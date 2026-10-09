#!/usr/bin/env python3
import json,re,sys,time,urllib.request,urllib.error
import start as S
s=S.kit.read(S.D/'settings.json');pid=int(sys.argv[1]);deadline=time.monotonic()+240
while time.monotonic()<deadline:
 S.kit.require(S.Path(f'/proc/{pid}').exists(),'Server exited before readiness')
 try:
  with urllib.request.urlopen(f"http://127.0.0.1:{s['port']}/metrics",timeout=2) as f:m=json.load(f)
  with urllib.request.urlopen(f"http://127.0.0.1:{s['port']}/v1/models",timeout=2) as f:models=json.load(f)
  break
 except urllib.error.URLError:time.sleep(.5)
else:raise SystemExit('Startup exceeded240s; no force-kill')
lock=S.kit.read(S.D/'manifests/production-lock.json');e=m['engine']
S.kit.require(all(e.get(k)==v for k,v in lock['engine_info'].items()) and e['vram_free_mib']>=512,'Loaded expert/KV/MTP/headroom mismatch')
S.kit.require(models['data'][0]['meta']['n_ctx']==131072,'Wrong context')
record=S.kit.read(S.R/'logs/current.json')
with (S.R/'logs/engine.log').open('rb') as f:f.seek(record['log_offset']);log=f.read().decode('utf8','replace')
S.kit.require(re.findall(r'(\d+) of (\d+) experts missing from VRAM mirrored',log)==[('13745','13745')],'Incomplete Host Mirror')
S.kit.require('GPU 0: Intel(R) Arc(TM) Pro B60 Graphics' in log and not re.search(S.ENGINE_ERROR,log,re.I),'Wrong GPU or unsafe startup')
sha=S.command('docker','exec',s['container_name'],'sha256sum','/proc/1/exe').split()[0]
S.kit.require(sha==lock['engine_sha256'],'Running ELF changed');S.health(record['epoch'])
(S.R/'logs/ready.json').write_text(json.dumps({'server_pid':pid,'engine':e,'running_sha256':sha,'ready_epoch':time.time(),'mirror':13745},indent=2)+'\n')
print('Frozen FastFix READY; full mirror, MTP4, Adaptive4/96,128K, loaded headroom>=512MiB')
