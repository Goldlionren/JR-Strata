#!/usr/bin/env python3
import json,os,shlex,sys
from pathlib import Path
import start as S
if os.environ.get('FASTFIX_PACKAGED')!='1':raise SystemExit('Use the dedicated systemd service')
s=S.kit.read(S.D/'settings.json');m=S.kit.read(S.D/'docker/runtime-manifest.json');stamp=S.kit.read(S.R/'logs/current.json')['epoch']
S.kit.verify_installed(S.R);S.health(stamp);image=S.image_identity(m['local_alias'])
a=['docker','run','--rm','-i','--name',s['container_name'],'--oom-score-adj','1000','--stop-timeout','90','--no-healthcheck','--restart','no']
for device in s['device_nodes']:a+=['--device',device]
a+=['-v',s['install_dir']+':/release:ro','-v',s['data_dir']+':/assets:ro']
for k,v in s['environment'].items():a+=['-e',k+'='+v]
a += [image,'exec '+shlex.join(['/release/bin/strata',*sys.argv[1:]])]
os.execvp('docker',a)
