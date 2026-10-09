# FastFix adaptive GGUF mirror and host payload repair

Offline work starts at `48a0fefe682a7c5aeea78a23a4a6fda6867751ea` on `jr-b60-sycl-v0.1.39-fastfix`. Production RC1 remains running. This is a source repair and CPU validation, **not GPU acceptance or a production release**.

## Confirmed defect and causal limit

Startup `generate.cpp` mirrors only the initial GPU-cache complement. The old adaptive path overwrote the victim's GPU slot, changed its residency to -1, admitted the incoming expert, and uploaded residency without updating GGUF mirror pointers. `resident_stage_swaps()` maintains only `FileExpertSource`, not `GgufExpertSource`. An initially GPU-only victim therefore becomes unavailable to the device plan, despite complete initial coverage. The source defect is reproduced deterministically; the exact failed expert was absent from the archived ring33/ring47 traces, so neither historical timeout is conclusively attributed to this defect.

A second independent defect is confirmed: GPU device-plan skips allow `seq` to run ahead of the host, but the old x/IDs/weights addresses were reused for every layer. `seq >= want` means the requested layer has published; it does not mean the shared payload still belongs to that layer. Delayed CPU consumption can interpret newer IDs/activation under the older layer number, changing host fallback, plans and adaptive usage. This is possible even without a GPU memory fault. The archived layer29/seq33 and layer31/seq47 gaps establish exposure, not the exact numerical damage in those runs.

## Storage ownership and lifetime

| Storage | Owner / lifetime | Reader and reuse boundary |
|---|---|---|
| Main GPU expert slots | `ExpertCache`, unchanged contiguous sized arena and slot offsets; startup10831 experts/17.57GiB target | Verifier graph and prompt path. Adaptation starts after `ver.run()` completes compute, copy and host pool; prompt loans must already be restored. Same-layer slot ownership also updates through `cache.replace()` after copies. |
| GGUF pinned slots | `GgufExpertSource::blocks_`, original chunked USM host allocations,13745 complement experts/22.40GiB target | CPU pool and graph pointers. Allocation addresses do not move; only logical ownership changes at exchange commit. No reader is admitted while an exchange is pending. |
| Exact mirror aliases | `mirror_ptr_[layer*512+expert]` in source; device table base fixed for captured graphs | `device_alias()` now returns nullptr for an unmirrored expert, rather than another expert's sentinel. `pcie_layer()` separately preserves layer capability. |
| Exchange scratch | One source-owned pinned allocation of2329600 bytes, allocated on first swap | Three ordered copies per expert on the existing in-order adaptive queue. Next exchange reuses scratch only after the preceding host-slot copy. Freed only after tracked queues drain. |
| GGUF fallback ring | Original512 ordinary host buffers and shard FDs, unchanged | Unmirrored experts still read GGUF; queued prompt refills retain existing256-copy drains. No new permanent all-expert mirror. |
| Verifier plan / CPU outputs | Existing two group plan regions and per-group ymiss | Fallback A/B/M dependencies retained. Device-plan skip does not consume obsolete host plans; a true fallback cannot advance to the next publication before its current dependencies. |
| Verifier x/IDs/weights | Verifier-owned uncached mapped memory, now `[stage_layer][max_t][N or K]` | Each layer writes once per window; split groups use disjoint row slices. Host lag is harmless for storage ownership. Whole-window compute/copy/host completion gates reuse. Failed window remains poisoned. |
| MTP expert weights | Drafter's separate `experts_` device allocation | Adaptation does not touch it. Verifier commit graph updates recurrent/KV/history state, not main expert weights; this existing overlap is retained. |

Source anchors: `sycl/src/program/generate.cpp:3789` (initial mirror/table),`:4696` (publication helpers),`:5810` (serving apply),`:5893` (serving transaction), CLI corresponding transaction near`:8000`; `sycl/src/core/gguf_expert_source.cpp:330` (copies),`:366` (completion/ownership); `sycl/src/core/expert_source.cpp:2077` (host plan); `sycl/src/core/verify.cpp:374`,`:912`,`:1452` (snapshots); `sycl/src/kernels/cuda/verify_kernels.dp.cpp:932` (device plan, unchanged). Line numbers refer to engine source revision in the candidate manifest.

## Swap protocol and publication invariants

`d2eb7f9` introduces the exchange; `6397c24` independently repairs payload lifetime. `be3105e` adds the actual-source GPU probe, error propagation and opt-in ownership evidence.

```mermaid
sequenceDiagram
    participant V as Verifier / host pool
    participant A as Adaptive in-order copy queue
    participant H as GGUF source / host metadata
    participant D as Device metadata
    V->>A: Previous expert readers complete; select unchanged4/96 policy
    H->>H: Validate same-layer incoming pinned / outgoing GPU / unique slots / generation
    A->>A: D2H outgoing GPU slot → one scratch
    A->>A: H2D incoming pinned slot → outgoing GPU slot
    A->>A: Ordered host-USM copy scratch → incoming pinned slot
    Note over A: Repeat; no scratch reuse before preceding copy completes
    A->>H: Final event wait_and_throw + asynchronous error propagation
    H->>H: Transfer host slot to outgoing; incoming→GPU; update cache ownership
    H->>D: Upload mirror table; wait_and_throw
    H->>D: Upload residency; wait_and_throw
    D->>V: Admit next graph only after both uploads complete
```

Host and GPU table writes need not be simultaneous: no graph/pool reader exists during their uncommitted interval. They describe the same committed generation when the next graph is admitted. CPU mirror getters reject an active transaction; generation, exact host address, residency, duplicate expert/slot and same-layer ownership are checked before mutation. Every batch is validated before any metadata changes. Copies are completed before admission even if the old optional `STRATA_ADAPT_NOWAIT=1` is supplied, because overwriting main slots while permitting another graph is unsafe.

The admitted expert's pinned slot becomes the victim's pinned slot. Its old GPU bytes are saved before GPU overwrite; incoming host bytes remain intact until H2D finishes. This preserves exactly one backing location per expert without a second17.57GiB mirror. Full initial coverage therefore remains full after every validated exchange. Partial mirror configurations keep disk fallback, and only swap candidates with an exchangeable pinned slot are selected. GGUF adaptation on peer/layer-split GPUs is explicitly rejected; this repair is for the existing single B60, not an unverified multi-device transaction.

`APLAN_EXCHANGE` records expert IDs/slot/host owner only after copy completion and CPU commit. `APLAN_MIRROR phase=mirror_uploaded` is the first device-table phase, not permission to run. Serving `APLAN_RESIDENCY` follows both uploads and includes generation/coverage. Captured graphs retain table addresses and read newly committed values; no recapture is needed for each swap.

Failed submissions/completions never resume Decode. Adaptive worker exceptions and publication failures use the existing bounded device-drain guard; unproven quiescence exits86 without freeing application buffers. Source destruction drains tracked queues before freeing pinned blocks/scratch. Successful Decode windows gain no global queue drain, sleep or extended Ring timeout.

## Payload lifetime repair

Graph publication and CPU consumption use the same `verify_payload::row(l,lb,max_t,tb)` offset. `seq >= want` is retained. Each stage allocates only its own layers, and max_t stride remains fixed across T1/4/6. `h_plan_`, `h_ymiss_`, A/B/M flags, native expert arithmetic and device-plan fast path are unchanged.

CPU tests deliberately publish every GPU layer before serving older CPU layers and demonstrate that the old reused region returns the wrong reference data while the new snapshots return exact x/IDs/weights. Mixed fallback/skip scheduling and multiple windows are covered. Existing queue completion, joined CPU pool callbacks and sticky failed-window state prevent cross-window reuse; the fix adds no per-layer acknowledgement or global synchronization.

## Offline validation and limitations

| Gate | Result | Evidence |
|---|---|---|
| Mirror ownership and copy ordering | PASS, CPU |16 cases;1000 simulated batches/3000 pair exchanges; independent byte patterns, ownership transfer, duplicate/stale rejection, generation checks, delayed copies and failed cleanup |
| Host payload lifetime | PASS, CPU |6 cases;300 changing windows, T1/4/6, MTP on/off grouping, archived lag shapes, stale windows, split-stage offsets and timeout lifetime |
| ASan + UBSan | PASS, CPU |Both new suites plus existing lifecycle and A-plan state suites; address/undefined checks, leak detection, halt-on-error; no sanitizer diagnostics |
| Existing PLE / lifecycle / A-plan | PASS, CPU |90 Direct/mmap independent PLE windows;90/110-byte Reader tests;11 lifecycle and16 A-plan fault cases; output and source dependency checks |
| Maintenance / output / new plan | PASS, CPU |10 restoration-controller tests, fenced/unfenced Python checks,7 new admission/fixture/dry-run tests |
| Old frozen adaptive-control identity guard | Expected rejection |6/7 old tests pass; old artifact identity assertion fails after intentional source/build changes. Historical manifests/hashes are retained, not rewritten to pass. |
| New Docker build | See candidate manifest |Frozen image/compiler; no GPU devices mapped. Initial compile-scope and standalone-probe declaration/type errors corrected, failure logs retained. |
| Actual B60 exchange, payload coherency, inference | BLOCKED |Not executed; fresh narrow maintenance authorization required |
| Historical timeout eliminated /25–30tok/s | BLOCKED |No repaired-engine GPU inference or performance measurement |
| Production protected | PASS |Read-only frozen hash, active/enabled service,32K model/status; no stop/restart or generation |

Raw CPU evidence: `docs/jr-v0139-fastfix-evidence/mirror-repair-offline/`. Build logs including failed attempts: `logs/fastfix/mirror-repair-offline/`. New identity/plan: `tools/fastfix/mirror-repair-candidate.json` and `docs/JR_SYCL_V0139_FASTFIX_MIRROR_GPU_PLAN.md`.

## Expected cost, without performance claims

For the actual48-layer,2560-width model, max_t6 and K10, payload allocation rises from61920 to2972160 bytes: **+2910240 bytes (2.775MiB)** pinned host memory. One max expert scratch adds2329600 bytes (2.222MiB). Persistent CPU mirror publication staging adds196608 bytes (0.188MiB), plus small bounded batch bookkeeping. Total principal new host storage is about5.185MiB; no expert-cache VRAM or permanent mirror budget increase.

Each swap adds a victim D2H and one ordered host-USM copy to the old incoming H2D. At96 largest blobs, each phase is at most223641600 logical bytes; actual selected layer sizes/counts can be smaller. **Logical copy bytes are not measured physical PCIe traffic**, especially for host-to-host USM copies. The event wait gates a true weight dependency and may partly overlap existing drafting/commit. Transfer latency and sustained Decode cost remain unmeasured. Payload writes copy the same bytes as before into different destinations; no additional per-layer kernel or wait is introduced.

Do not deploy this candidate or claim the archived27.9tok/s belongs to it. The next test runs Adaptive ON, verifies real exchanged bytes and captured ownership first, then passes beyond1186 tokens with normal teardown and RC1 restoration. A clean run is evidence for further validation, not general reliability.

## Frozen offline build identity

Engine source: `be3105e7f66ef4f9668ef129a1938800954b1b3b`. Build PASS. Experimental ELF SHA256: `8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e`. Actual-GGUF/captured-payload probe SHA256: `a8e764fd2ee893bc6eb6d327f8eb2edb8e930a292df825153284c9d3afc3eae8`. Neither executable has been GPU-run. The previous tested diagnostic ELF remains preserved under `dist/aplan-control-window-01/strata`.

Final read-only production check:2026-10-09T12:01:58+11:00; server984699, engine985485, RC1 active/enabled, frozen hash matched, native models/status/metrics available and32768 context. PCI vendor/device8086:e211 verified. No matching GPU fault/reset/hang lines in the recorded kernel journal since11:05; no inference or production lifecycle action occurred. Evidence:`rc1-readonly-final.json` and `kernel-journal-readonly.log`.
