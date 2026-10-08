#!/usr/bin/env python3
"""Historical Docker launch strategy, with a unique container and no force-removal."""
import json,os,shlex,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
image='sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44'
name='jr-strata-fastfix-engine'
if name in subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines():raise SystemExit('REFUSED existing FastFix container')
if subprocess.check_output(['systemctl','--user','show','jr-strata-sycl-rc1.service','-p','ActiveState','--value'],text=True).strip()=='active':raise SystemExit('REFUSED RC1 active')
args=['docker','run','--rm','-i','--name',name,'--device','/dev/dri','--oom-score-adj','1000','--stop-timeout','90','--no-healthcheck','-v','/data/strata-lab:/work:ro']
for v in ['ONEAPI_DEVICE_SELECTOR=level_zero:0','SYCL_CACHE_PERSISTENT=0','STRATA_VERIFY_DEVICE_PLAN=1','STRATA_STAGER_THREADS=12','STRATA_ARENA_ALIAS_CHECK=1','STRATA_HOST_UNCACHED=1']:
 args+=['-e',v]
if os.environ.get('FASTFIX_NO_HOST')=='1':args+=['-e','STRATA_VERIFY_NO_HOST=1']
binary='/work/JR-Strata-SYCL-v0139-FastFix/build-fastfix/strata'
args += [image,'exec '+shlex.join([binary,*sys.argv[1:]])]
os.execvp('docker',args)
