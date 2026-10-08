# FastFix A-plan readiness: offline reconstruction

Starting revision: `106c00c818efcde18211b42cd0bce90762ed5c54`. This investigation runs no GPU work and makes no RC1 lifecycle changes. The new build is an **opt-in diagnostic candidate, not a timeout fix or a release**. Artifact identities and CPU results are in `tools/fastfix/aplan-candidate.json`.

## Findings and causal limits

**A source-level coverage hole is confirmed:** startup builds the pinned mirror only for experts initially absent from VRAM; the serving loop nevertheless enables adaptive swaps by default (every 4 windows, up to 96 swaps). Swapping out an initially resident expert changes its residency to -1 but does not add that expert to the static mirror table. A later route to it must fall back to a host plan. Complete mirror coverage at startup is therefore not evidence of complete coverage throughout Decode.

The exact archived Docker command has no `--adapt-every` or `--adapt-swaps` override. The startup text `PROFILE ... no eviction` describes initial cache policy; it does **not** disable the separate serving-loop adaptive tier. The existing `FileExpertSource` exchange helper does not exchange the `GgufExpertSource` mirror. This explains a concrete way for `skip=0` to occur after a fully covered startup, without any DMA failure or device cache fault. **The failed expert ID was not recorded, so attributing ring47 specifically to this hole remains a hypothesis.** No ranking, adaptive policy or residency setting is changed to hide it.

| Question | Evidence-based conclusion |
|---|---|
| A-plan producer | CPU `expert_pool_dispatch_multi` fills mapped plan metadata and calls `Verifier::publish_plan`; `_mm_sfence` precedes `A=cur_layer+1`. |
| Consumer | GPU A wait, then guarded host-plan copy in the verifier command graph. A current device-plan `skip==ring` bypasses host metadata. |
| `observed=40` | Value returned by the GPU's final A readiness load for expected47, **not** layer40's event, a token count, or a DMA byte count. |
| Plan vs DMA publication | A authorizes metadata only. B separately authorizes staged weights. In the tested automatic/kernel PCIe mode (2), there is no per-plan copy-queue DMA: B is immediate, then graph `fetch_blobs` copies from pinned weights before compute. |
| First recorded loss of lockstep | At host layer29/expected ring30, `seq=33,A=B=M=29`; by host layer31 completion, `seq=47,A=B=32`. GPU advancement is legal for a covered device plan, but host payload buffers are reused. |
| Permanently stalled graph | Not supported by this run: GPU reached seq48 and `wait_and_throw` returned; compute and copy queues drained before rejection. A temporary stall cannot be timed from this trace. |
| Consumer visibility failure | Not established. The host was demonstrably behind; its eventual A=48 does not prove that A=47 existed before the failing wait expired. |
| Producer failure | The host eventually published through48. Delay before the needed publication is evidenced; its exact cause (CPU scheduling, obsolete payload, expert reads/computation) is not timed separately in the old trace. |
| Missing mirror/device plan | Source permits coverage loss after adaptive eviction. Exact failed routing/residency values remain unrecorded. |
| Memory fault | No new kernel fault/reset in the latest run. This does not prove every weight or plan pointer remained numerically valid. |

## Producer/consumer state diagram

```mermaid
sequenceDiagram
    participant G as Verifier graph / in-order compute queue
    participant H as Host layer loop / expert pool
    participant C as In-order copy queue (DMA mode only)
    G->>G: Route IDs; build plan from device residency + static mirror table
    alt All routes covered
        G->>G: Write device plan; device fence; publish skip=ring
    else Invalid ID or uncovered expert
        G->>G: skip=0; require host plan
    end
    G->>H: Publish x/IDs/weights; system fence; advance seq
    H->>H: Observe seq>=want; fill mapped plan
    H->>G: sfence; publish A=want (metadata)
    alt skip==ring
        G->>G: Keep device plan; bypass A/B/M
    else Host plan required
        G->>G: Wait A; reject on timeout; copy plan
        alt PCIe mode0 DMA
            H->>C: Submit copies
            C->>G: After copies, immutable callback publishes B=want
        else Mode2 used in archived run
            H->>G: Publish B=want without copy-queue DMA
            G->>G: After B, fetch_blobs kernel then expert compute
        end
        H->>H: Finish CPU expert outputs
        H->>G: Publish M=want
        G->>G: After M, consume CPU outputs and combine
    end
    G->>H: End graph; existing compute wait_and_throw
    H->>H: Existing copy wait_and_throw; reject any latched failure
    H->>H: Only completed successful windows may commit/reuse
```

A separate between-window path matters: serving adaptation overwrites a victim cache slot, marks its old expert nonresident, waits for its transfer event before admitting the new expert, and uploads `host_res` to `d_res`. **It does not update the startup mirror table.** The upload may be perfectly ordered and still publish an uncovered expert.

## Precise source map (diagnostic revision)

- `sycl/src/program/generate.cpp:519,542`: defaults `adapt_every=4`, `adapt_swaps=96`; `:5737` enables usage; `:5841` selects swaps; `:5921` evicts victim; `:5809` commits the FileExpertSource exchange and then uploads new residency. The Gguf source uses its own mirror, not those FileExpertSource buffers.
- `sycl/src/program/generate.cpp:3788–3827`: mirror covers initial cache misses; builds/upload `mirror_table_d` once. `:5410` registers that table before graph capture.
- `sycl/src/core/gguf_expert_source.cpp:286`: `pinned()` checks the immutable per-expert mirror pointer. `device_alias()` may return a layer sentinel for an unmirrored expert, so coverage must test `pinned()`; a non-null alias alone is insufficient.
- `sycl/src/core/expert_source.cpp:2077–2193`: host plan construction, metadata fence, A publication and fetch dispatch. The Gguf source inherits the no-op `begin_layer`; its actual unmirrored weight reads happen in `blob`, including CPU expert work. Do not attribute this run's delay to FileExpertSource's `begin_layer` implementation.
- `sycl/src/core/verify.cpp:903`: device plan precedes doorbell; `:950–1005`: A/B/M consumers; `:1297`: window staging/reset/submission; `:1439`: host layer service; `:1710`: B publication; `:1753`: A publication.
- `sycl/src/kernels/cuda/elementwise.dp.cpp:566`: one workgroup writes mapped x/IDs/weights, fences/barriers, then advances seq.
- `sycl/src/kernels/cuda/verify_kernels.dp.cpp:932`: device plan rejects invalid IDs, `n>64`, or any `res<0 && mirror==0`; success publishes skip after device plan writes. `:1081`: bounded readiness polling and first-failure latch; `:1104`: guarded pointer-bearing plan copy.
- `sycl/include/strata/sycl_doorbell.hpp:30`: uncached L1/L3 read hint and acquire system fence; `:56`: unchanged20,000 bound.
- `sycl/include/strata/sycl_queue.hpp:65`: `zeMemAllocHost(BIAS_UNCACHED)`, with an unlogged fallback to ordinary host USM in the old binary. The new opt-in startup line reports which path actually allocated A/B/M/seq/plan/diagnostics.

## Two failures, without conflating them

Older run (`logs/fastfix/window-01-resume`): readiness timeout ring33 at00:41:19, then the first journal CCS reset/page-fault report at00:41:20. Ring33 means zero-based layer32 for G=1/lb=0. The old latch could be overwritten and did not identify its channel, T, position or observed word. It cannot prove A was the first channel or that the fault began after the timeout; timestamps are second resolution. Prior lifetime repairs remain intact.

Latest run (`docs/jr-v0139-fastfix-evidence/p0-window-01/mtp-on-engine.log`): error at08:50:06, window896/T1/position1264, ring47/layer46/group0/observed40/skip0 after1,186 emitted tokens. This was an MTP-enabled run, **but the failing verifier window had T=1**. Zero new page faults/resets, completed compute/copy waits, and clean assessed teardown are recorded.

Host trace for zero-based window895, microseconds before `SYNCED`:

| Event | us before SYNCED | GPU seq | A |
|---|---:|---:|---:|
| Served layer28 | 58,258.2 | 29 | 29 |
| Host begins layer29 | 54,542.4 | 33 | 29 |
| Served layer31 | 44,533.8 | 47 | 32 |
| Served layer39 | 18,975.9 | 47 | 40 |
| Served layer40 | 12,463.9 | 47 | 41 |
| Served layer46 | 2,682.7 | 47 | 47 |
| Served layer47 | 2,078.8 | 48 | 48 |
| SYNCED | 0 | 48 | 48 |

This is consistent with A=40 being a real, late producer frontier; there is no contemporaneous evidence of A=47 failing visibility. GPU timeout timestamps are unavailable. The old line “the GPU never started it” was false as an inference: SYCL `gpu_stamp_kernel` writes zero because `%globaltimer` has no implemented equivalent. That message is corrected.

The host loop tests `seq>=want`, while x/IDs/weights and plan buffers are per-group, not per-layer. When the GPU bypasses waits and advances, a lagging host may work from a newer layer's overwritten payload under an older layer number. The source permits this and the trace proves lag; it does not preserve the bytes actually read. This can amplify catch-up work. Do not “repair” the incident solely by raising the wait bound or skipping arbitrary host layers.

## Reuse, MTP and upstream comparison

`skip` is reused per group; `resident_plan` runs before its consumer in the same in-order graph and writes the current ring or zero. Readiness words reset between completed windows. Error poisons the verifier; compute/copy and other tracked work must quiesce before any memory owner is released. The immutable DMA callback and pending-commit safety fixes remain unchanged. No saved event status proves a prematurely completed event in this run.

T=1 selected by MTP probability/first-window policy uses the same T=1 verifier graph as the no-draft control. MTP affects preceding draft/commit work and route histories, but no alternate A-plan dependency is selected simply because MTP is enabled. `MtpDrafter::draft` already waits before host token/probability consumption. The passing512-token controls cannot rule out later coverage loss.

Compared against **exact tag v0.1.40.3, commit `d5ea7133741e67743c0e886bb426c0ce8d69cf6c`**, not current main or JR RC1 modifications:

- Uncached L1/L3 doorbell loads, system fences and Level Zero uncached host allocation are already present in this FastFix base. Both have ordinary-USM allocation fallback. Reapplying these mechanisms is not a causal fix.
- Upstream uses a configurable spin bound; its BMG default remains20,000. The larger A-series wait is not a B60 fix and is not ported.
- Upstream A publication also precedes weight copies, and B remains the separate readiness dependency. FastFix retains its stronger immutable callback capture and guarded rejected-plan consumption.
- Upstream has newer all-resident/always-publish paths and pipelined-stage fencing. Replacing the verifier with those paths would violate the surgical scope and does not establish this incident's cause.
- Upstream also builds the Gguf mirror table at startup and has an adaptive tier. No verified single upstream doorbell patch repairs the static-mirror/adaptive-victim coverage invariant automatically.

## Smallest useful diagnostic change

`STRATA_APLAN_DIAG=1` is off by default. It records, in existing captured nodes:

1. Per-ring generation, actual planner entry, local route hash, invalid/missing counts, first rejected expert/slot, device residency/mirror-table addresses, shared rejection flag and intended skip publication.
2. Each A/B/M wait's entry/exit, skip, before/after readiness values and bounded spin count; plan-copy decision (reject/device/host).
3. Host pool begin, A publication, fetch submission and pool-return timestamps/seq values. Mode0 callbacks retain existing queued/published tracing.
4. After adaptive admission, CPU residency hash and count of nonresident experts lacking a pinned mirror. This counts holes without changing placement, allocation or I/O policy.

Only the first completed window and a failed readiness window dump per-ring device records, after existing compute **and** copy waits. Each of96 maximum ring slots uses168 bytes (16,128 bytes total mapped diagnostic storage); host observations are separate. No new graph nodes, per-window queue drains, barriers, higher timeout or expert compute changes. Observations are not readiness inputs. Destruction retains the safe drain-before-free path. An unquiesced GPU never authorizes reading/freeing these records.

The opt-in route inspection and extra uncached reads can change timing. Even diagnostics-off is a rebuilt kernel binary, not a claim of identical performance. A nonreproduction with diagnostics is inconclusive. GPU durations, physical PCIe traffic and the exact stalled instruction remain N/A. The shared rejection flag has multiple non-atomic same-value writers on rejection; its consistency is recorded, not assumed to explain this incident.

## Offline validation and decision

15 deterministic CPU state/fault cases pass, including a successful adaptive swap that creates a static-mirror coverage hole; delayed producer vs injected stale consumer with the same timeout; invalid routes; skip mismatch; missing node progress; DMA-after-A; stale generation;1,000 consecutive windows with MTP on/off policy; sticky first failure; failed-queue lifetime retention. ASan/UBSan pass. Existing90 PLE oracle windows,11 lifecycle cases, parser/output checks and10 maintenance-gate tests pass.

A compiled captured-graph probe now checks four changing covered/missing/invalid route generations. **It has not run on the GPU.** CPU observations do not certify hardware coherency. An initial CPU test syntax error was fixed; the initial log is retained alongside final PASS evidence.

| Gate | Status |
|---|---|
| Handshake/source reconstruction and archived command verification | PASS |
| Static mirror coverage hole after eligible adaptive eviction | PASS: source and deterministic CPU counterexample |
| Exact failed expert / causal chain for ring47 | BLOCKED: old telemetry absent |
| CPU regression and sanitizer checks | PASS |
| Isolated new build | See frozen candidate manifest |
| GPU diagnostic probe / reproduction / timeout eliminated | BLOCKED: not executed; new authorization required |
| Production acceptance / performance preservation | BLOCKED |
| RC1 preserved | PASS: read-only active/hash verification; no lifecycle actions |

No speculative synchronization fix is claimed. The next narrow test must establish whether the actual failing ring routes an uncovered expert, a valid plan's skip is lost, or a node does not progress. Only then select the corrective change; the historical performance target does not justify disabling a safety gate.

## Frozen offline diagnostic build

Engine source commit: `ee3ab2dba75a9597d5ad2c76e8d8e5fb5f764907`. Build: **PASS**, CPU-only historical Docker build.

Experimental ELF: `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix/build-fastfix/strata`

SHA256: `6b00ee839b6cf342fc85bdefa504e17fa80cc3fd94f766611e3707bf1120d6fe`

Captured handoff probe SHA256: `3237f2ced414e38d1695631b121dd6dcb54b30fd7a361da615f647323a1de4fa`. It is compiled, not GPU-tested.

Rebuild with `bash tools/fastfix/build.sh`; CPU checks with `bash tools/fastfix/cpu-tests.sh` and `python3 -B tools/fastfix/p0-harness-tests.py`. The manifest freezes the experimental binary, probe, profile, request, launcher and changed engine sources. Do not reuse an older maintenance manifest.

Final read-only RC1 check: 2026-10-09 09:22 AEDT, service active/enabled, server198898, engine199664, frozen SHA256 and32768 context, native status reachable, no kernel fault lines since08:52:18. No production lifecycle action or inference request was made. Evidence: `docs/jr-v0139-fastfix-evidence/aplan-offline/`.
