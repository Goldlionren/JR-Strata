# Frozen production operations

Native Chat/Monitor/About: http://127.0.0.1:18083/ ; OpenAI API:http://127.0.0.1:18083/v1.
Use the configured port on another installation. No unauthenticated network exposure is supported by this kit.

```bash
systemctl --user status jr-strata-sycl-fastfix.service --no-pager
./deployment/healthcheck.sh 18083
./deployment/watch.sh "$HOME/.local/share/jr-strata-sycl"
journalctl --user -u jr-strata-sycl-fastfix.service -n 100 --no-pager
# Graceful SIGTERM to native server, Server QUIT, SYCL queue drain:
systemctl --user stop jr-strata-sycl-fastfix.service
# After confirmed process/container exit and GPU-health assessment:
systemctl --user start jr-strata-sycl-fastfix.service
```

systemd bounded retry3 starts/600s,30s delay; safety refusal78/86 prevents automatic restart. KillModeprocess,
SendSIGKILLno and180s stop timeout preserve validated shutdown. There is no broad kill and no Docker restart loop.
Do not free/kill unresolved GPU users to hide an unsafe teardown; preserve logs and assess device health first.

Native Monitor uses existing metrics. The portable wrapper selects the requested PCI card's sysfs telemetry and deliberately
shows N/A for privileged global-sampler counters that cannot be attributed to that device; it installs no privileged
helper. Additional read-only XPU-SMI/resource diagnostics can be used where accessible. Request counts/timings are engine
statistics, not invented measurements. Native frontend and Intel server source are unmodified.

Keep config/runtime.json, rankings, binary, Docker content and Python pins frozen. Do not use the web configuration editor
to alter engine settings in this immutable deployment. install-file verification refuses changed runtime/launch files.
RC1 is deprecated/inactive/disabled; no automatic fallback or competing autostart is configured.
