#!/usr/bin/env python3
"""One bounded operator-authorized FastFix acceptance and verified RC1 restoration."""
import argparse,hashlib,json,os,re,socket,subprocess,sys,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'tools/fastfix'
RC='jr-strata-sycl-rc1.service';UNIT='jr-strata-fastfix-test.service';NAME='jr-strata-fastfix-engine'
IMAGE='sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44'
FROZEN='cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028'
RCBIN=Path('/data/strata-lab/JR-Strata-SYCL-v0.1.40.3/dist/jr-b60-sycl-v0.1.40.3-rc1/strata')
TESTS=['fastfix_memory_safety','kv_q8_parity','kv_stream_parity','iq_multi_parity','native_grouped_parity','quantize_act_parity','fastfix_ple_staging','fastfix_handoff']
def cmd(*args,timeout=20,check=True):return subprocess.run(args,text=True,capture_output=True,timeout=timeout,check=check)
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def api(port,path):return json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}{path}',timeout=8))
def state(unit):return cmd('systemctl','--user','show',unit,'-p','ActiveState','--value').stdout.strip()
def gpu():return json.loads(cmd('xpu-smi','discovery','-d','0000:07:00.0','-j').stdout)
def children(pid):
 result=[]
 for p in Path(f'/proc/{pid}/task/{pid}/children').read_text().split():
  result.append(int(p));result+=children(p)
 return result
p=argparse.ArgumentParser();p.add_argument('--execute-authorized',action='store_true');p.add_argument('--out',required=True);p.add_argument('--resume-start',type=Path);a=p.parse_args()
if not a.execute_authorized:
 print(json.dumps({'tests':TESTS,'arms':['historical spec4 auto cache','device-only spec4 same slots','MTP-off same slots'],'port':18086,'max_minutes':60,'admission_cutoff_minutes':45,'cleanup_minutes':50,'recovery_reserve_minutes':10},indent=2));sys.exit(0)
E=Path(a.out).resolve();E.mkdir(parents=True,exist_ok=False);start=json.loads(a.resume_start.read_text())['start_epoch'] if a.resume_start else time.time();deadline=time.monotonic()+(start+3600-time.time());stopped=False;exp_started=False
if time.time()>start+2700:raise SystemExit('original admission deadline expired')
(E/'cutover.json').write_text(json.dumps({'start_epoch':start,'deadline_epoch':start+3600,'authorization':'operator final execute-all instruction; isolated FastFix only'},indent=2))
def save(name,data): (E/name).write_text(data if isinstance(data,str) else json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def health():
 k=cmd('journalctl','-k','--since',f'@{start-900:.0f}','--no-pager');save('kernel.txt',k.stdout)
 if re.search('permission|not seeing messages',k.stderr,re.I):raise RuntimeError('kernel journal inaccessible')
 if re.search(r'(?:xe.*(?:fault|reset|wedged|CAT error|Timedout)|GPU.*(?:HANG|reset|fault))',k.stdout,re.I):raise RuntimeError('SERIOUS GPU FAULT; assess hardware before restoration')
 x=gpu()
 if x['pci_bdf_address']!='0000:07:00.0' or x['pci_device_id']!='0xe211' or x['device_state']!='normal':raise RuntimeError('wrong/unhealthy B60')
 return x

def free_check():
 x=health();m=int(re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M)[1]);save('resources-latest.json',{'gpu':x,'host_available_kib':m})
 if int(x['memory_free_size_byte'])<22*1024**3 or m<50*1024**2:raise RuntimeError('resource conflict: need22GiB free B60 and50GiB host')

def containers():return cmd('docker','ps','-a','--format','{{.Names}}').stdout.splitlines()
def admission(seconds):
 if time.monotonic()+seconds>deadline-900:raise RuntimeError('experiment admission deadline: restore now')
def wait_api(port,secs):
 end=min(time.monotonic()+secs,deadline-600 if port==18086 else deadline-20)
 while time.monotonic()<end:
  health()
  try:
   x=api(port,'/v1/models')
   if x.get('data'):return x
  except (OSError,ValueError):pass
  time.sleep(3)
 raise RuntimeError(f'API startup timeout port{port}')
def stop_exp():
 global exp_started
 if exp_started:
  z=cmd('systemctl','--user','stop',UNIT,timeout=105,check=False);save('experimental-stop.txt',z.stdout+z.stderr)
  save('experimental-journal.txt',cmd('journalctl','--user','-u',UNIT,'--since',f'@{start:.0f}','--no-pager').stdout)
  if z.returncode:raise RuntimeError('unsafe experimental teardown')
 if any(n==NAME or n.startswith('jr-fastfix-probe-') for n in containers()):raise RuntimeError('surviving experimental container; assess before restoration')
 if cmd('ss','-H','-ltn','sport = :18086').stdout.strip():raise RuntimeError('experimental listener survived shutdown')
 exp_started=False;free_check()
def arm(name,slots=None,no_host=False,spec=4):
 global exp_started
 admission(700)
 c=json.loads((D/'runtime.json').read_text());args=c['args']
 if slots:args[args.index('--expert-cache')+1]=str(slots)
 args[args.index('--spec')+1]=str(spec)
 c['log']=str(E/(name+'-engine.log'));path=E/(name+'-runtime.json');save(path.name,c)
 run=['systemd-run','--user','--unit',UNIT,'--collect','--service-type=exec','-p','Restart=no','-p','KillMode=process','-p','KillSignal=SIGTERM','-p','SendSIGKILL=no','-p','TimeoutStopSec=90','--setenv=PYTHONDONTWRITEBYTECODE=1','--setenv=PYTHONUNBUFFERED=1',f'--setenv=FASTFIX_NO_HOST={1 if no_host else 0}',f'--working-directory={R}','/data/strata-lab/Strata/.venv/bin/python','-B',str(R/'sycl/serve/server_intel.py'),'--engine','strata','--config',str(path),'--host','127.0.0.1','--port','18086']
 save(name+'-launch.json',run);cmd(*run);exp_started=True
 save(name+'-models.json',wait_api(18086,300));m=api(18086,'/metrics');save(name+'-metrics-start.json',m)
 log=Path(c['log']).read_text();matches=re.findall(r'(\d+) of (\d+) experts missing from VRAM mirrored',log)
 if not matches or any(x!=y for x,y in matches):raise RuntimeError('incomplete Host Mirror')
 actual=m['engine']['expert_slots'];
 if slots and actual!=slots:raise RuntimeError('cache budget changed')
 save(name+'-container.json',json.loads(cmd('docker','inspect',NAME).stdout))
 # Validate running ELF hash inside the unchanged runtime image, plus actual loaded libraries.
 actual_sha=cmd('docker','exec',NAME,'sha256sum','/proc/1/exe').stdout.split()[0]
 if actual_sha!=sha(R/'build-fastfix/strata'):raise RuntimeError('running experimental binary mismatch')
 save(name+'-maps.txt',cmd('docker','exec',NAME,'cat','/proc/1/maps').stdout)
 return actual

def suite(name,which):
 admission(650 if which=='sustained' else 500)
 env=dict(os.environ,FASTFIX_EVIDENCE=str(E),FASTFIX_ARM=name,PYTHONDONTWRITEBYTECODE='1')
 with (E/(name+'-'+which+'.log')).open('w') as f:
  z=subprocess.run([sys.executable,'-B',str(D/'acceptance.py'),which],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=700 if which=='sustained' else 520)
 if z.returncode:raise RuntimeError(name+' '+which+' failed; preserve evidence, stop comparisons')
 if which=='functional':
  z=cmd(sys.executable,'-B',str(D/'quality.py'),str(E/(name+'-'+which)));save(name+'-quality.txt',z.stdout)
 health()
try:
 # Frozen files and own service ancestry only; no global ownership census or sudo dependency.
 if state(RC)!='active' or sha(RCBIN)!=FROZEN:raise RuntimeError('RC1 state/binary mismatch')
 spid=int(cmd('systemctl','--user','show',RC,'-p','MainPID','--value').stdout);pids=children(spid)
 engines=[pid for pid in pids if Path(f'/proc/{pid}/exe').exists() and sha(f'/proc/{pid}/exe')==FROZEN]
 if len(engines)!=1:raise RuntimeError('running RC1 identity unverified')
 save('rc1-before.json',{'server_pid':spid,'engine_pids':engines,'hash':FROZEN,'enabled':cmd('systemctl','--user','is-enabled',RC).stdout.strip()})
 protected=[RCBIN,Path('/data/strata-lab/JR-Strata-SYCL-v0.1.40.3/strata-swift-iq3_xxs-b60-32k.json'),Path('/home/james/.config/systemd/user')/RC,Path('/data/strata-lab/Strata/data/expert-profile.bin')]
 before_hash={str(f):sha(f) for f in protected};save('protected-before.json',before_hash)
 frozen=json.loads((D/'frozen.json').read_text())
 for f,h in frozen.items():
  if sha(R/f)!=h:raise RuntimeError('experimental identity mismatch: '+f)
 if json.loads(cmd('docker','image','inspect',IMAGE).stdout)[0]['Id']!=IMAGE:raise RuntimeError('Docker identity mismatch')
 with socket.socket() as s:s.bind(('127.0.0.1',18086))
 if NAME in containers():raise RuntimeError('existing experimental container')
 x=health();save('gpu-before.json',x)
 n=None
 for i in range(2):
  m=api(18083,'/metrics');s=api(18083,'/status');save(f'rc1-idle-{i}.json',{'metrics':m,'status':s})
  if s['busy'] or s['queued'] or m['live']['state']!='idle' or m['live']['queued']:raise RuntimeError('RC1 not idle')
  count=m['totals']['requests']
  if n is not None and count!=n:raise RuntimeError('new production request during preflight')
  n=count
  if i==0:time.sleep(3)
 save('rc1-stop.txt',cmd('systemctl','--user','stop',RC,timeout=105).stdout);stopped=True
 if state(RC)!='inactive' or any(Path(f'/proc/{pid}').exists() for pid in [spid,*engines]):raise RuntimeError('RC1 teardown incomplete')
 free_check()
 selection=cmd('docker','run','--rm','--device','/dev/dri','-e','ONEAPI_DEVICE_SELECTOR=level_zero:0',IMAGE,'sycl-ls --verbose',timeout=30).stdout
 save('docker-device.txt',selection)
 if 'Arc(TM) Pro B60' not in selection or '57873' not in selection:raise RuntimeError('container selector not verified as B60 e211')
 for i,test in enumerate(TESTS):
  admission(180);name=f'jr-fastfix-probe-{i}'
  arg=[] if test in ('iq_multi_parity','native_grouped_parity','fastfix_memory_safety','fastfix_handoff') else ['--selftest']
  if test=='fastfix_ple_staging':arg=['/tmp/fastfix-ple.gguf']
  command='timeout --signal=TERM 150 /work/JR-Strata-SYCL-v0139-FastFix/build-fastfix/'+test+' '+' '.join(arg)
  z=cmd('docker','run','--rm','--name',name,'--device','/dev/dri','-v','/data/strata-lab:/work:ro','-e','ONEAPI_DEVICE_SELECTOR=level_zero:0','-e','STRATA_ARENA_ALIAS_CHECK=1','-e','SYCL_CACHE_PERSISTENT=0',IMAGE,command,timeout=175,check=False)
  save(test+'.log',z.stdout+z.stderr);health()
  print(test,z.returncode,flush=True)
  if z.returncode:raise RuntimeError('GPU safety failed: '+test)
 free_check();slots=arm('historical');suite('historical','functional');suite('historical','sustained');stop_exp()
 slots=arm('device-only',slots,no_host=True);suite('device-only','functional');stop_exp()
 arm('mtp-off',slots,spec=0);suite('mtp-off','functional');stop_exp()
 save('experiments.json',{'status':'completed','slots':slots})
except Exception as ex:
 save('blocker.json',{'error':str(ex),'elapsed_s':time.time()-start});print('STOP:',str(ex),flush=True)
finally:
 if stopped:
  try:
   stop_exp();health()
   if sha(RCBIN)!=FROZEN:raise RuntimeError('RC1 disk hash changed')
   cmd('systemctl','--user','start',RC,timeout=150);models=wait_api(18083,300)
   spid=int(cmd('systemctl','--user','show',RC,'-p','MainPID','--value').stdout);eps=[p for p in children(spid) if Path(f'/proc/{p}/exe').exists() and sha(f'/proc/{p}/exe')==FROZEN]
   if len(eps)!=1 or state(RC)!='active':raise RuntimeError('restored running identity mismatch')
   req=urllib.request.Request('http://127.0.0.1:18083/v1/chat/completions',json.dumps({'model':'swift-1.5-iq3_xxs','messages':[{'role':'user','content':'Reply with one sentence: what is 2 plus 2?'}],'temperature':0,'max_tokens':32,'chat_template_kwargs':{'enable_thinking':False}}).encode(),{'Content-Type':'application/json'})
   response=json.load(urllib.request.urlopen(req,timeout=90));save('rc1-smoke.json',response)
   if '4' not in response['choices'][0]['message']['content'] and 'four' not in response['choices'][0]['message']['content'].lower():raise RuntimeError('RC1 restoration smoke incorrect')
   m=api(18083,'/metrics');save('rc1-restored-metrics.json',m);save('rc1-restored-status.json',api(18083,'/status'));save('rc1-restored-models.json',models)
   if m['engine']['max_context']!=32768:raise RuntimeError('RC1 context changed')
   after={str(f):sha(f) for f in protected};save('protected-after.json',after)
   if before_hash!=after:raise RuntimeError('protected file changed')
   health();save('rc1-watch.json',cmd('/home/james/.local/bin/jr-sycl-watch','--json',timeout=30).stdout)
   save('restoration.json',{'status':'PASS','engine_pids':eps,'sha256':FROZEN,'elapsed_s':time.time()-start,'enabled':cmd('systemctl','--user','is-enabled',RC).stdout.strip()});print('RC1 RESTORED',eps,flush=True)
  except Exception as ex:
   save('RESTORATION-INCIDENT.json',{'error':str(ex),'elapsed_s':time.time()-start});print('INCIDENT: restoration not verified:',ex,flush=True)
 save('elapsed.json',{'seconds':time.time()-start,'within60minutes':time.time()-start<=3600})
