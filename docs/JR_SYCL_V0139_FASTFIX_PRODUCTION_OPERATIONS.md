# FastFix production operations

Production service: **`jr-strata-sycl-fastfix.service`**. Native Chat, Monitor and About: **http://127.0.0.1:18083/**. OpenAI API base: **http://127.0.0.1:18083/v1**. It stays running; no automatic trial timeout. RC1 is deprecated, disabled and not an automatic recovery target.

## Read-only health and monitoring

```bash
systemctl --user status jr-strata-sycl-fastfix.service
curl --fail --max-time 10 http://127.0.0.1:18083/v1/models
curl --fail --max-time 10 http://127.0.0.1:18083/status
curl --fail --max-time 10 http://127.0.0.1:18083/metrics
journalctl --user -u jr-strata-sycl-fastfix.service -n 80 --no-pager
```

Use the existing native Monitor tab for request/throughput/MTP/hardware data. Metrics absent from the native server remain N/A; no custom monitor was built. The old `jr-sycl-watch` is RC1-specific and is not the status command for FastFix. `/health`, `/config` and `/settings` also support native Chat/About behavior.

The API reports131072 configured context; this deployment did not repeat a genuine128K prompt test. The prior25.3tok/s result belongs to the qualified2048-token garden workload; short-request speeds can be lower. Aggregate draft counters include MTP and suffix, not MTP-only acceptance.

## Brief API check

This supported request field disables thinking for a concise answer without changing engine defaults:

```bash
curl --fail --max-time 60 http://127.0.0.1:18083/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary '{"model":"swift-1.5-iq3_xxs","messages":[{"role":"user","content":"What is 6 times 7? Reply only with the number."}],"max_tokens":16,"temperature":0,"seed":42,"chat_template_kwargs":{"enable_thinking":false}}'
```

Expected answer42. A top-level `thinking:false` is not the supported control in this server. A response using its entire budget on reasoning is length-capped, not evidence of GPU corruption. Native Chat provides its own thinking toggle. Keep inference arguments/MTP/ranking unchanged.

## Graceful lifecycle

```bash
systemctl --user stop jr-strata-sycl-fastfix.service
# Verify native "stopped", no owned engine/container, released GPU and no new fault before starting again.
systemctl --user start jr-strata-sycl-fastfix.service
systemctl --user is-active jr-strata-sycl-fastfix.service
systemctl --user is-enabled jr-strata-sycl-fastfix.service
```

An intentional stop preserves ENABLED for the next boot. To leave it offline across boots, explicitly `systemctl --user disable jr-strata-sycl-fastfix.service`. Do not terminate Docker processes, issue kill9/pkill or start another heavy inference engine while FastFix owns the B60. Do not run old experimental maintenance controllers against production.

After a fault, corrupted output, Ring timeout, uncovered expert or unsafe shutdown: stop admitting requests, preserve `logs/fastfix-production/`, native journal, `journalctl -k` and current engine/container identity; request only graceful stop. Assess GPU health/resource release before any restart. A surviving engine or unresolved queue is an unsafe state. Do not manually clear a refusal merely to resume inference. Investigate/repair FastFix; temporary unavailability is preferable to bypassing safety. **Do not automatically re-enable or start RC1.** Changing the archived-production decision requires a separate explicit operator decision.

Startup refusal lists its cause: artifact/config hash mismatch, wrong/missing B60, unexpected owner/container, memory shortfall, port listener, unresolved engine error or kernel fault. Correct that cause without changing drivers, model/ranking or safety thresholds. Linux TIME_WAIT alone is accepted using the unchanged native server's SO_REUSEADDR behavior; real listeners still block.

Production files: `deploy/fastfix/{runtime.json,manifest.json,start.py,engine-wrapper.py,ready.py,jr-strata-sycl-fastfix.service}`. Frozen ELF: `dist/jr-b60-sycl-v0139-fastfix-adaptive-mirror/strata`. Do not rebuild/replace it under the same identity. Any future candidate needs separate validation; existing RC1 artifacts remain historical only.

## Installation reproduction

This cutover is already installed and active. These commands describe the installed lifecycle, not a request to redo it:

```bash
cd /data/strata-lab/JR-Strata-SYCL-v0139-FastFix
PYTHONDONTWRITEBYTECODE=1 python3 -B deploy/fastfix/cpu_test.py
systemd-analyze --user verify deploy/fastfix/jr-strata-sycl-fastfix.service
# Compare existing units and identities; refuse an unexpected file before installation.
install -m 0644 deploy/fastfix/jr-strata-sycl-fastfix.service ~/.config/systemd/user/jr-strata-sycl-fastfix.service
systemctl --user daemon-reload
systemctl --user stop jr-strata-sycl-rc1.service
systemctl --user disable jr-strata-sycl-rc1.service
# Confirm prior engine exited, B60 healthy/free and no active/queued request before a real cutover.
systemctl --user start jr-strata-sycl-fastfix.service
# Verify model, actual ELF SHA, mirror/residency, native UI/API, faults and brief generation.
systemctl --user enable jr-strata-sycl-fastfix.service
```

The manifest verifies original files as well as the production copy. If restoring this checkout from source, recover the already-validated ELF with the exact recorded hash; never silently rebuild. Existing Docker and user Linger policies are already enabled. Do not change host policy or perform a reboot merely to repeat this deployment.
