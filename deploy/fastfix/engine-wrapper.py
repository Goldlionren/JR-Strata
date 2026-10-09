#!/usr/bin/env python3
"""Exact validated Docker inference launch, pinned to a frozen production ELF."""
import os,shlex,sys,time
import start as S
if os.environ.get('FASTFIX_PRODUCTION')!='1':raise SystemExit('REFUSED: use the production service')
try:
    S.exclude_other_engine();S.prior_incident_guard()
    current=S.STATE/'current.json'
    import json
    stamp=json.loads(current.read_text())['start_epoch']
    S.health(stamp)
    if S.digest(S.BINARY)!=S.SHA:raise ValueError('Frozen production ELF hash mismatch')
except (OSError,ValueError,KeyError,S.subprocess.SubprocessError) as exc:
    print('FastFix engine REFUSED: '+str(exc),file=sys.stderr);sys.exit(78)
args=['docker','run','--rm','-i','--name',S.NAME,'--device','/dev/dri','--oom-score-adj','1000','--stop-timeout','90','--no-healthcheck','-v','/data/strata-lab:/work:ro']
for v in ['ONEAPI_DEVICE_SELECTOR=level_zero:0','SYCL_CACHE_PERSISTENT=0','STRATA_VERIFY_DEVICE_PLAN=1','STRATA_STAGER_THREADS=12','STRATA_ARENA_ALIAS_CHECK=1','STRATA_HOST_UNCACHED=1','STRATA_DECODE_TIMING=1','STRATA_VERIFY_TRACE=1','STRATA_APLAN_DIAG=1']:
    args+=['-e',v]
binary='/work/JR-Strata-SYCL-v0139-FastFix/dist/jr-b60-sycl-v0139-fastfix-adaptive-mirror/strata'
args += [S.IMAGE,'exec '+shlex.join([binary,*sys.argv[1:]])]
os.execvp('docker',args)
