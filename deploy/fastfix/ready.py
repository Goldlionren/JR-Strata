#!/usr/bin/env python3
"""Bounded production readiness gate; no inference and no engine replacement."""
import json,re,sys,time,urllib.error,urllib.request
from pathlib import Path
import start as S
server_pid=int(sys.argv[1]);deadline=time.monotonic()+240
while time.monotonic()<deadline:
    if not Path(f'/proc/{server_pid}').exists():raise SystemExit('Native server exited before readiness')
    try:
        with urllib.request.urlopen('http://127.0.0.1:18083/metrics',timeout=2) as f:m=json.load(f)
        with urllib.request.urlopen('http://127.0.0.1:18083/v1/models',timeout=2) as f:models=json.load(f)
        break
    except urllib.error.URLError:time.sleep(.5)
else:raise SystemExit('FastFix startup exceeded240s')
e=m['engine'];expected={'expert_slots':10831,'expert_cache_mib':17990,'max_context':131072,'kv':'int8','kv_resident':32768,'spec':6,'mtp_max':4}
if any(e.get(k)!=v for k,v in expected.items()) or e['vram_free_mib']<512:raise SystemExit('Loaded residency/KV/MTP/headroom mismatch')
if models['data'][0]['meta']['n_ctx']!=131072:raise SystemExit('Wrong API context')
record=json.loads((S.STATE/'current.json').read_text())
with Path(record['engine_log']).open('rb') as f:
    f.seek(record['engine_log_start']);log=f.read().decode('utf-8','replace')
if re.findall(r'(\d+) of (\d+) experts missing from VRAM mirrored',log)!=[('13745','13745')]:raise SystemExit('Incomplete Host Mirror')
if 'GPU 0: Intel(R) Arc(TM) Pro B60 Graphics' not in log:raise SystemExit('Wrong LevelZero device')
if re.search(S.ENGINE_FAILURE,log,re.I):raise SystemExit('Unsafe startup log')
actual=S.command('docker','exec',S.NAME,'sha256sum','/proc/1/exe').stdout.split()[0]
if actual!=S.SHA:raise SystemExit('Running Docker ELF hash mismatch')
container=json.loads(S.command('docker','inspect',S.NAME).stdout)[0]
if container['Image']!=S.IMAGE:raise SystemExit('Docker runtime image changed')
S.health(record['start_epoch'])
result={'server_pid':server_pid,'engine_pid':container['State']['Pid'],'binary_sha256':actual,'docker_image':container['Image'],
        'engine':e,'mirror_experts':13745,'mirror_expected':13745,'adaptive_every':4,'adaptive_swaps':96,'ready_epoch':time.time()}
(S.STATE/'ready.json').write_text(json.dumps(result,indent=2)+'\n')
print('FastFix ready:128K,10831 GPU/13745 mirror, headroom '+str(e['vram_free_mib'])+'MiB, frozen running ELF',flush=True)
