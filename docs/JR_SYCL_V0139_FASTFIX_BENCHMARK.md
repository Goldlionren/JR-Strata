# FastFix validation

CPU: PLE Reader selftests pass for90/110-byte rows. Independent PLE test passes90 windows, T=1/4/6, three request histories, changing/repeated rows, Direct/mmap, delayed I/O and failed gather before submission. Completed MTP output bounds and actual source ordering checks pass. Evidence `logs/fastfix/cpu-N1P0h5/`. Initial test compile missing `<initializer_list>` was corrected; no GPU was used.

| Criterion | Status | Evidence |
|---|---|---|
| CPU PLE numerical reference | PASS |90 windows plus history oracle|
| CPU MTP output validation | PASS |bounds, NaN/Inf, source wait ordering|
| GPU PLE graph visibility | BLOCKED |not executed yet|
| Queue/expert readiness | BLOCKED |GPU handoff test pending|
| MTP on/off correctness | BLOCKED |pending inference|
| Allocation integrity | BLOCKED |GPU tests pending|
|2048+ generated tokens | BLOCKED |pending inference|
|≥20 tok/s | BLOCKED |no FastFix measurement|
|GPU fault-free acceptance | BLOCKED |pending GPU tests|
|RC1 restoration | BLOCKED |maintenance not started; RC1 unchanged|

Historical28.7tok/s/1036 tokens had confirmed corruption.33.5tok/s/2932 tokens lacks full qualification. Do not compute a correctness-equivalent regression or improvement against those values.
