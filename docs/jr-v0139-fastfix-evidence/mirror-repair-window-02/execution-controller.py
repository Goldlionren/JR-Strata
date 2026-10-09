#!/usr/bin/env python3
# Ephemeral execution of the operator-approved, frozen mirror GPU plan. No source/config edits.
import datetime,hashlib,json,os,re,shlex,socket,subprocess,sys,threading,time,urllib.request
from pathlib import Path
R=Path('/data/strata-lab/JR-Strata-SYCL-v0139-FastFix');D=R/'tools/fastfix';E=R/'logs/fastfix/mirror-repair-window-02'
RC='jr-strata-sycl-rc1.service';UNIT='jr-strata-fastfix-mirror-test.service';NAME='jr-strata-fastfix-engine'
IMAGE='sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44'
FROZEN='cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028';EXPECTED='8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e'
RCBIN=Path('/data/strata-lab/JR-Strata-SYCL-v0.1.40.3/dist/jr-b60-sycl-v0.1.40.3-rc1/strata')
start=None;mono=None;stopped=False;exp=False;unsafe=False;results={};protected={};spid=0;engines=[];test_process=None

def save(n,x):(E/n).write_text(x if isinstance(x,str) else json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def say(x):print(f'{time.monotonic()-mono:.1f}s {x}',flush=True)
def cmd(*a,timeout=15,check=True):return subprocess.run(a,cwd=R,text=True,capture_output=True,timeout=timeout,check=check)
def digest(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def api(port,path,timeout=8):return json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}{path}',timeout=timeout))
def state(u):return cmd('systemctl','--user','show',u,'-p','ActiveState','--value').stdout.strip()
def containers():return cmd('docker','ps','-a','--format','{{.Names}}').stdout.splitlines()
def children(pid):
 out=[]
 for p in Path(f'/proc/{pid}/task/{pid}/children').read_text().split():out.append(int(p));out+=children(p)
 return out
FAULT=r'(?:xe.*(?:fault|reset|wedged|CAT error|Timedout)|GPU.*(?:HANG|reset|fault))'
def health(pre=False):
 global unsafe
 z=cmd('journalctl','-k','--since',f'@{start-(900 if pre else 0):.0f}','--no-pager','-o','short-iso-precise')
 save('kernel-preflight.txt' if pre else 'kernel.txt',z.stdout)
 if re.search('permission|not seeing messages',z.stderr,re.I):raise RuntimeError('kernel diagnostics inaccessible')
 if re.search(FAULT,z.stdout,re.I):unsafe=True;raise RuntimeError('SERIOUS GPU FAULT/reset; restoration suspended pending assessment')
 z=cmd('xpu-smi','discovery','-d','0000:07:00.0','-j');g=json.loads(z.stdout)
 if g['pci_bdf_address']!='0000:07:00.0' or g['pci_device_id']!='0xe211' or g['device_state']!='normal':unsafe=True;raise RuntimeError('B60 identity or hardware health failed')
 return g

def mem():
 m=dict((k,int(v)) for k,v in re.findall(r'^(\w+):\s+(\d+) kB',Path('/proc/meminfo').read_text(),re.M))
 v=Path('/proc/vmstat').read_text();return {'host_available_kib':m['MemAvailable'],'swap_used_kib':m['SwapTotal']-m['SwapFree'],**{k:int(re.search('^'+k+r'\s+(\d+)',v,re.M)[1]) for k in ['pswpin','pswpout']}}
def free_check():
 g=health();m=mem();save('resources-free.json',{'gpu':g,**m})
 if int(g['memory_free_size_byte'])<22*1024**3 or m['host_available_kib']<32*1024**2:raise RuntimeError('prepared resource gate BLOCKED: require22GiB B60 free /32GiB MemAvailable')
 before=mem();time.sleep(1);after=mem()
 if any(after[k]!=before[k] for k in ['pswpin','pswpout']):raise RuntimeError('active swapping at resource gate')

def admit(seconds):
 if time.monotonic()-mono+seconds+90>900:raise RuntimeError('deadline admission denied; recover RC1 now')
def lifecycle(a,u,timeout):
 p=subprocess.Popen(['systemctl','--user',a,u],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:o,e=p.communicate(timeout=timeout)
 except subprocess.TimeoutExpired:raise RuntimeError('systemd '+a+' timeout; no force-kill sent')
 save(a+'-'+u+'.txt',o+e)
 if p.returncode:raise RuntimeError('systemd '+a+' failed: '+e)

def stop_exp():
 global exp,unsafe
 if exp:
  lifecycle('stop',UNIT,90)
  j=cmd('journalctl','--user','-u',UNIT,'--since',f'@{start:.0f}','--no-pager').stdout;save('server-journal.txt',j)
  if re.search('FASTFIX_UNSAFE_TEARDOWN|status=86|core.dump|terminate called',j):unsafe=True;raise RuntimeError('unsafe experimental service teardown')
  if state(UNIT) not in ('inactive','failed',''):raise RuntimeError('experimental service survives')
 if any(n in containers() for n in [NAME,'jr-fastfix-mirror-safety','jr-fastfix-mirror-handoff','jr-fastfix-mirror-probe']):unsafe=True;raise RuntimeError('surviving experimental container; do not restore')
 if cmd('ss','-H','-ltn','sport = :18086').stdout.strip():unsafe=True;raise RuntimeError('experimental listener survives')
 log=E/'engine.log'
 if log.exists() and re.search('FASTFIX_UNSAFE_TEARDOWN|terminate called',log.read_text()):unsafe=True;raise RuntimeError('unsafe engine exit')
 exp=False;g=health();m=mem();save('resources-recovery.json',{'gpu':g,**m})
 if int(g['memory_free_size_byte'])<22*1024**3 or m['host_available_kib']<40*1024**2:raise RuntimeError('RC1 original recovery resource gate not met')
 results['experimental_teardown']='PASS' if (E/'launch.json').exists() else 'NOT STARTED; resources released';say('experimental process absence and RC1 recovery resource gate PASS')

def gpu_test(test,bound,args=(),name='jr-fastfix-mirror-safety'):
 global test_process,unsafe
 admit(bound);health()
 command='exec '+shlex.join(['/work/JR-Strata-SYCL-v0139-FastFix/build-fastfix/'+test,*args])
 a=['docker','run','--rm','--name',name,'--device','/dev/dri','-e','ONEAPI_DEVICE_SELECTOR=level_zero:0','-e','SYCL_CACHE_PERSISTENT=0','-e','STRATA_ARENA_ALIAS_CHECK=1','-e','STRATA_HOST_UNCACHED=1','-e','STRATA_APLAN_DIAG=1','-v','/data/strata-lab:/work:ro',IMAGE,command]
 save(test+'-command.json',a);t=time.monotonic()
 with (E/(test+'.log')).open('w') as f:
  test_process=subprocess.Popen(a,cwd=R,stdout=f,stderr=subprocess.STDOUT)
  try:rc=test_process.wait(timeout=bound)
  except subprocess.TimeoutExpired:unsafe=True;raise RuntimeError(test+' bounded probe hung; left unsignalled for assessment')
 test_process=None;health();text=(E/(test+'.log')).read_text()
 if re.search('FASTFIX_UNSAFE_TEARDOWN',text):unsafe=True;raise RuntimeError(test+' unsafe cleanup')
 results[test]={'status':'PASS' if rc==0 else 'FAIL','exit_code':rc,'duration_s':time.monotonic()-t};save('stages.json',results);say(test+' '+results[test]['status'])
 if rc:raise RuntimeError(test+' failed; no inference admitted')

SNAP=r'''import json,re,time
from pathlib import Path
p=Path('/proc/1');x={'epoch':time.time(),'io':{k:int(v) for k,v in (l.split(':') for l in (p/'io').read_text().splitlines())}}
s=(p/'stat').read_text().split(') ',1)[1].split();x.update(majflt=int(s[9]),minflt=int(s[7]))
for key in ('VmRSS','VmHWM','VmSwap'):
 m=re.search('^'+key+r':\s+(\d+)',(p/'status').read_text(),re.M);x[key+'_kib']=int(m[1]) if m else None
seen=set()
for f in (p/'fdinfo').iterdir():
 try:s=f.read_text()
 except FileNotFoundError:continue
 if '0000:07:00.0' not in s:continue
 z=re.search(r'drm-client-id:\s+(\d+)',s)
 if not z or z[1] in seen:continue
 seen.add(z[1])
 for key,tag in [('vram_kib','drm-total-vram0'),('gtt_kib','drm-total-gtt')]:
  z=re.search(tag+r':\s+(\d+)',s)
  if z:x[key]=x.get(key,0)+int(z[1])
print(json.dumps(x))'''
def snapshot():
 x=json.loads(cmd('docker','exec',NAME,'python3','-c',SNAP,timeout=8).stdout);x.update(mem());return x

def wait_api(port,seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  health()
  try:
   x=api(port,'/v1/models',timeout=3)
   if x.get('data'):return x
  except (OSError,ValueError):pass
  time.sleep(2)
 raise RuntimeError(f'API startup timeout:{port}')

def request(name,body,bound):
 admit(bound);health();t=time.monotonic();row={'name':name,'request':body,'before':snapshot(),'ttft_s':None};text=[];reason=[];samples=[];issues=[];done=threading.Event();error=None
 def monitor():
  while not done.is_set():
   try:
    health();x=snapshot();samples.append(x)
    if x['host_available_kib']<4*1024**2:raise RuntimeError('host RAM headroom below4GiB')
    log=(E/'engine.log').read_text()
    if re.search(r'holes=[1-9]|FASTFIX_UNSAFE_TEARDOWN|readiness timeout|expert readiness device wait expired|GGUF adaptive exchange.*failed',log):raise RuntimeError('engine readiness/coverage/ownership failure')
   except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:issues.append(str(e));return
   done.wait(2)
 th=threading.Thread(target=monitor,daemon=True);th.start()
 try:
  req=urllib.request.Request('http://127.0.0.1:18086/v1/chat/completions',json.dumps(body).encode(),{'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=20) as f,(E/(name+'.sse')).open('wb') as rawout:
   for raw in f:
    rawout.write(raw);rawout.flush()
    if issues:raise RuntimeError(issues[0])
    if time.monotonic()-t>bound:raise TimeoutError('request bound reached')
    if not raw.startswith(b'data: '):continue
    if raw.strip()==b'data: [DONE]':break
    d=json.loads(raw[6:])
    if d.get('error'):raise RuntimeError(str(d['error']))
    for c in d.get('choices',[]):
     delta=c.get('delta',{});v=delta.get('content') or '';r=delta.get('reasoning_content') or ''
     if (v or r) and row['ttft_s'] is None:row['ttft_s']=time.monotonic()-t
     text.append(v);reason.append(r)
     if c.get('finish_reason'):row['finish_reason']=c['finish_reason']
    for k in ['usage','timings']:
     if d.get(k):row[k]=d[k]
    full=''.join(text)
    if '!!!!!' in full or '\ufffd' in full or re.search(r'(.{40,200}?)\1{4}',full,re.S):raise RuntimeError('output corruption/repetition')
  if not ''.join(text) or not row.get('usage'):raise RuntimeError('empty output/missing accepted token counts')
  health()
 except (OSError,ValueError,RuntimeError) as e:error=str(e)
 finally:
  done.set();th.join(timeout=12);row.update(content=''.join(text),reasoning=''.join(reason),elapsed_s=time.monotonic()-t,error=error,samples=samples)
  try:row['after']=snapshot();row['metrics']=api(18086,'/metrics')
  except (OSError,ValueError,subprocess.SubprocessError) as e:row['after_error']=str(e)
  save(name+'.json',row)
 say(name+' '+('FAIL '+error if error else 'completed '+str(row.get('usage'))))
 if error:raise RuntimeError(name+': '+error)
 return row

# Original clock begins now; no later phase resets it.
E.mkdir(parents=True,exist_ok=False);start=time.time();mono=time.monotonic();save('cutover.json',{'start_epoch':start,'start_iso':datetime.datetime.now().astimezone().isoformat(),'deadline_epoch':start+1200,'experiment_teardown_epoch':start+900,'authorization':'user-approved20-minute Adaptive Mirror GPU validation retry at11e46f7 with explicitly approved22GiB unloaded/512MiB loaded gates','engine_sha256':EXPECTED})
try:
 if cmd('git','rev-parse','HEAD').stdout.strip()!='11e46f7f53d5cc45883fe6e6eac0f510c6f1df35' or cmd('git','status','--short').stdout.strip():raise RuntimeError('prepared HEAD/state changed')
 z=cmd(sys.executable,'-B',str(D/'mirror-repair-plan.py'),'--verify',timeout=60);save('identity-verification.json',z.stdout)
 if digest(R/'build-fastfix/strata')!=EXPECTED or digest(RCBIN)!=FROZEN:raise RuntimeError('binary mismatch')
 if cmd('docker','image','inspect',IMAGE,'--format','{{.Id}}').stdout.strip()!=IMAGE:raise RuntimeError('runtime image mismatch')
 if state(RC)!='active':raise RuntimeError('unexpected production service state')
 spid=int(cmd('systemctl','--user','show',RC,'-p','MainPID','--value').stdout);pids=children(spid);engines=[p for p in pids if Path(f'/proc/{p}/exe').exists() and digest(f'/proc/{p}/exe')==FROZEN]
 if len(engines)!=1:raise RuntimeError('running RC1 executable identity unverified')
 for p in [RCBIN,Path('/data/strata-lab/JR-Strata-SYCL-v0.1.40.3/strata-swift-iq3_xxs-b60-32k.json'),Path('/home/james/.config/systemd/user')/RC,Path('/data/strata-lab/Strata/data/expert-profile.bin')]:protected[str(p)]=digest(p)
 save('protected-before.json',protected);save('rc1-before.json',{'server_pid':spid,'engine_pids':engines,'sha256':FROZEN,'service':cmd('systemctl','--user','show',RC,'-p','ActiveState','-p','SubState','-p','UnitFileState').stdout,'watch':json.loads(cmd('/home/james/.local/bin/jr-sycl-watch','--json').stdout)})
 with socket.socket() as s:s.bind(('127.0.0.1',18086))
 if any(n in containers() for n in [NAME,'jr-fastfix-mirror-safety','jr-fastfix-mirror-handoff','jr-fastfix-mirror-probe']):raise RuntimeError('existing experiment/resource conflict')
 if cmd('systemctl','--user','show',UNIT,'-p','MainPID','--value',check=False).stdout.strip() not in ('','0'):raise RuntimeError('existing experimental service')
 save('gpu-before.json',health(pre=True));count=None
 for i in range(2):
  m=api(18083,'/metrics');s=api(18083,'/status');save(f'rc1-idle-{i}.json',{'metrics':m,'status':s})
  if s['busy'] or s['queued'] or m['live']['state']!='idle' or m['live']['queued']:raise RuntimeError('RC1 busy; no cutover')
  if count is not None and m['totals']['requests']!=count:raise RuntimeError('new production request during preflight')
  count=m['totals']['requests']
  if i==0:time.sleep(2)
 stopped=True;lifecycle('stop',RC,90)
 save('rc1-stop-journal.txt',cmd('journalctl','--user','-u',RC,'--since',f'@{start:.0f}','--no-pager').stdout)
 if state(RC)!='inactive' or any(Path(f'/proc/{p}').exists() for p in [spid,*engines]):raise RuntimeError('RC1 server/engine still alive')
 free_check();say('RC1 graceful stop and B60 resource gate PASS')
 z=cmd('docker','run','--rm','--device','/dev/dri','-e','ONEAPI_DEVICE_SELECTOR=level_zero:0',IMAGE,'sycl-ls --verbose',timeout=20);save('docker-device.txt',z.stdout+z.stderr)
 if 'Arc(TM) Pro B60' not in z.stdout or '57873' not in z.stdout:raise RuntimeError('container B60 selector unverified')
 teststart=time.monotonic()
 for test in ['fastfix_memory_safety','kv_q8_parity','kv_stream_parity','iq_multi_parity','native_grouped_parity','quantize_act_parity','fastfix_ple_staging']:
  remaining=120-(time.monotonic()-teststart)
  if remaining<=0:raise RuntimeError('seven-test stage deadline')
  args=('/tmp/fastfix-ple-mirror.gguf',) if test=='fastfix_ple_staging' else ('--selftest',) if test in ['kv_q8_parity','kv_stream_parity','quantize_act_parity'] else ()
  gpu_test(test,remaining,args)
 gpu_test('fastfix_handoff',30,name='jr-fastfix-mirror-handoff')
 gpu_test('fastfix_adaptive_mirror',120,('/work/data/packs/swift-iq3_xxs','/work/data/models/swift-IQ3_XXS/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf'),name='jr-fastfix-mirror-probe')
 config=json.loads((D/'mirror-repair-runtime.json').read_text());config['log']=str(E/'engine.log');save('runtime.json',config)
 admit(120);health();a=['systemd-run','--user','--unit',UNIT,'--collect','--service-type=exec','-p','Restart=no','-p','KillMode=process','-p','KillSignal=SIGTERM','-p','SendSIGKILL=no','-p','TimeoutStopSec=90','--setenv=PYTHONDONTWRITEBYTECODE=1','--setenv=PYTHONUNBUFFERED=1','--setenv=FASTFIX_P0=1','--setenv=FASTFIX_APLAN_DIAG=1','--setenv=FASTFIX_NO_DRAFT=0','--setenv=FASTFIX_NO_HOST=0',f'--working-directory={R}','/data/strata-lab/Strata/.venv/bin/python','-B',str(R/'sycl/serve/server_intel.py'),'--engine','strata','--config',str(E/'runtime.json'),'--host','127.0.0.1','--port','18086'];save('launch.json',a);cmd(*a);exp=True
 save('experimental-models.json',wait_api(18086,120));m=api(18086,'/metrics');save('metrics-start.json',m);log=(E/'engine.log').read_text();e=m['engine']
 expected={'expert_slots':10831,'expert_cache_mib':17990,'max_context':131072,'kv':'int8','kv_resident':32768,'spec':6,'mtp_max':4}
 if any(e.get(k)!=v for k,v in expected.items()) or float(e['pcie_frac'])!=0.25 or float(e['spec_min_p'])!=0.5:raise RuntimeError('loaded residency/cache/MTP/context mismatch')
 save('loaded-headroom.json',{'vram_free_mib':e['vram_free_mib'],'required_mib':512,'expert_slots':e['expert_slots'],'expert_cache_mib':e['expert_cache_mib']})
 if e['vram_free_mib']<512:raise RuntimeError('loaded VRAM headroom below512MiB')
 if re.findall(r'(\d+) of (\d+) experts missing from VRAM mirrored',log)!=[('13745','13745')]:raise RuntimeError('full mirror coverage mismatch')
 if cmd('docker','exec',NAME,'sha256sum','/proc/1/exe').stdout.split()[0]!=EXPECTED:raise RuntimeError('running experimental ELF mismatch')
 save('experimental-maps.txt',cmd('docker','exec',NAME,'cat','/proc/1/maps').stdout);save('experimental-container.json',json.loads(cmd('docker','inspect',NAME).stdout));say('Adaptive ON original residency/MTP/runtime startup PASS')
 row=request('long-response',json.loads((D/'mirror-repair-request.json').read_text()),240)
 if row['usage']['completion_tokens']!=2048:raise RuntimeError('2048 actual outputs incomplete; correctness trigger coverage BLOCKED')
 log=(E/'engine.log').read_text();swaps=re.findall(r'APLAN_EXCHANGE generation=(\d+)',log);results['long_generation']={'status':'PASS','usage':row['usage'],'timings':row.get('timings'),'swaps':len(swaps),'generations':len(set(swaps))}
 if not swaps:raise RuntimeError('Adaptive ON had no committed swaps; trigger coverage BLOCKED')
 for name,prompt in [('english','Explain why seawater freezes below zero Celsius in two concise sentences.'),('chinese','请用两句简洁的中文解释为什么盐水的冰点低于纯水。'),('math','A rectangle has perimeter 30 and length 9. Give its width and area with a brief calculation. Keep the answer concise.')]:
  if time.monotonic()-mono+30+90>900:results[name]='BLOCKED deadline';continue
  body={'model':'swift-1.5-iq3_xxs','messages':[{'role':'user','content':prompt}],'temperature':0,'seed':42,'max_tokens':64,'chat_template_kwargs':{'enable_thinking':False},'stream':True,'stream_options':{'include_usage':True}};request(name,body,30);results[name]='completed; semantic review pending'
 save('metrics-final.json',api(18086,'/metrics'));stop_exp()
except Exception as e:
 save('first-failure.json',{'error':str(e),'elapsed_s':time.monotonic()-mono,'unsafe':unsafe,'stage_results':results});say('STOP: '+str(e));results['validation']='FAIL/BLOCKED: '+str(e)
finally:
 try:
  if stopped:
   if unsafe:raise RuntimeError('unsafe hardware/teardown condition; automatic restoration suspended')
   stop_exp();health()
   lifecycle('start',RC,35);save('rc1-models.json',wait_api(18083,min(150,max(5,1200-(time.monotonic()-mono)-35))))
   newpid=int(cmd('systemctl','--user','show',RC,'-p','MainPID','--value').stdout);neweng=[p for p in children(newpid) if Path(f'/proc/{p}/exe').exists() and digest(f'/proc/{p}/exe')==FROZEN]
   if len(neweng)!=1 or api(18083,'/v1/models')['data'][0]['meta']['n_ctx']!=32768:raise RuntimeError('RC1 restored identity/context failure')
   smoke={'model':'swift-1.5-iq3_xxs','messages':[{'role':'user','content':'What is 6 times 7? Answer briefly.'}],'max_tokens':32,'temperature':0,'chat_template_kwargs':{'enable_thinking':False}}
   req=urllib.request.Request('http://127.0.0.1:18083/v1/chat/completions',json.dumps(smoke).encode(),{'Content-Type':'application/json'});x=json.load(urllib.request.urlopen(req,timeout=35));save('rc1-smoke.json',x)
   if '42' not in x['choices'][0]['message']['content'] or '!!!!!' in x['choices'][0]['message']['content']:raise RuntimeError('RC1 smoke failed')
   for path in ['/status','/metrics']:save('rc1-'+path[1:]+'.json',api(18083,path))
   with urllib.request.urlopen('http://127.0.0.1:18083/',timeout=8) as f:save('rc1-ui-status.json',{'http_status':f.status,'bytes':len(f.read())})
   save('rc1-watch.json',json.loads(cmd('/home/james/.local/bin/jr-sycl-watch','--json').stdout));health()
   if {p:digest(p) for p in protected}!=protected:raise RuntimeError('protected config/ranking/binary/unit changed')
   save('rc1-restored.json',{'server_pid':newpid,'engine_pids':neweng,'sha256':FROZEN,'state':state(RC),'enabled':cmd('systemctl','--user','is-enabled',RC).stdout.strip(),'elapsed_s':time.monotonic()-mono,'protected_hashes_unchanged':True});results['RC1_restoration']='PASS';say('RC1 restored: hash/API generation/native monitoring/kernel PASS')
  else:results['RC1_restoration']='UNCHANGED; never stopped'
 except Exception as e:
  results['RC1_restoration']='BLOCKED: '+str(e);save('restoration-incident.json',{'error':str(e),'unsafe':unsafe,'elapsed_s':time.monotonic()-mono});say('INCIDENT: '+str(e))
 save('result.json',{'stages':results,'elapsed_s':time.monotonic()-mono,'start_epoch':start,'deadline_epoch':start+1200,'unsafe':unsafe});say('WINDOW CLOSED')
