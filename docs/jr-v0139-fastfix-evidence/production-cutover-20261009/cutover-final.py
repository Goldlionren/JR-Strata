import datetime,hashlib,json,pathlib,re,shutil,socket,subprocess,sys,time,urllib.request
R=pathlib.Path('/data/strata-lab/JR-Strata-SYCL-v0139-FastFix')
E=R/'logs/fastfix-production/cutover-03';assert not E.exists();E.mkdir(parents=True)
RC='jr-strata-sycl-rc1.service';NEW='jr-strata-sycl-fastfix.service'
EXPECTED='8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e'
IMAGE='sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44'
start=json.loads((R/'logs/fastfix-production/cutover-01/cutover.json').read_text())['start_epoch'];results={};stopped=True;started=False
def save(n,x):(E/n).write_text(x if isinstance(x,str) else json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def say(x):print(f'{time.time()-start:.1f}s {x}',flush=True)
def cmd(*args,timeout=20,check=True):return subprocess.run(args,text=True,capture_output=True,check=check,timeout=timeout)
def digest(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def api(ep):
 with urllib.request.urlopen('http://127.0.0.1:18083/'+ep,timeout=10) as f:return json.load(f)
def props(unit):
 return dict(line.split('=',1) for line in cmd('systemctl','--user','show',unit,'-p','ActiveState','-p','SubState','-p','MainPID','-p','UnitFileState','-p','NRestarts','-p','Conflicts').stdout.splitlines())
def health(pre=False):
 p=cmd('journalctl','-k','--since',f'@{start-(900 if pre else 0):.0f}','--no-pager','-o','short-iso-precise')
 save('kernel-preflight.txt' if pre else 'kernel.txt',p.stdout)
 assert not re.search('permission|not seeing messages',p.stderr,re.I)
 assert not re.search(r'(?:xe.*(?:fault|reset|wedged|CAT error|Timedout)|GPU.*(?:HANG|reset|fault))',p.stdout,re.I),'GPU fault/reset; assess hardware, no fallback'
 g=json.loads(cmd('xpu-smi','discovery','-d','0000:07:00.0','-j').stdout)
 assert g['device_state']=='normal' and g['pci_bdf_address']=='0000:07:00.0' and g['pci_device_id']=='0xe211'
 return g
def request(name,body):
 req=urllib.request.Request('http://127.0.0.1:18083/v1/chat/completions',json.dumps(body).encode(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as f:row=json.load(f)
 save(name+'.json',row)
 assert not row.get('error')
 content=row['choices'][0]['message'].get('content','');assert content and not re.search(r'!{5,}|\ufffd',content)
 return row
try:
 save('cutover.json',{'start_epoch':start,'start_iso':datetime.datetime.now().astimezone().isoformat(),'authorization':'Final operator production migration; RC1 deprecated, no automatic fallback','validated_head':'c6a8a55dbd2989dd51f5355e9a83eb76198fe832','candidate_sha256':EXPECTED})
 assert cmd('git','-C',str(R),'rev-parse','HEAD').stdout.strip()=='c6a8a55dbd2989dd51f5355e9a83eb76198fe832'
 oldmanifest=json.loads((R/'tools/fastfix/mirror-repair-candidate.json').read_text())
 manifest=json.loads((R/'deploy/fastfix/manifest.json').read_text())
 for m in [oldmanifest,manifest]:
  for p,h in m['files'].items():assert digest(R/p)==h,p
 assert digest(R/'dist/jr-b60-sycl-v0139-fastfix-adaptive-mirror/strata')==EXPECTED
 assert cmd('docker','image','inspect',IMAGE,'--format','{{.Id}}').stdout.strip()==IMAGE
 before=props(RC);save('rc1-before.json',before);assert before['ActiveState']=='inactive' and before['UnitFileState']=='disabled'
 rcserver=int(before['MainPID'])
 rcengine=0
 protected={str(p):digest(p) for p in [pathlib.Path('/home/james/.config/systemd/user/jr-strata-sycl-rc1.service'),pathlib.Path('/data/strata-lab/JR-Strata-SYCL-v0.1.40.3/strata-swift-iq3_xxs-b60-32k.json'),pathlib.Path('/data/strata-lab/JR-Strata-SYCL-v0.1.40.3/dist/jr-b60-sycl-v0.1.40.3-rc1/strata'),pathlib.Path('/data/strata-lab/Strata/data/expert-profile.bin')]}
 assert digest('/data/strata-lab/JR-Strata-SYCL-v0.1.40.3/dist/jr-b60-sycl-v0.1.40.3-rc1/strata')=='cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028'
 save('protected-before.json',protected);save('gpu-before.json',health(True))
 installed=pathlib.Path('/home/james/.config/systemd/user')/NEW
 assert installed.is_file() and not installed.is_symlink() and digest(installed)==digest(R/'deploy/fastfix'/NEW),'Unexpected changed FastFix unit'
 assert digest(installed)==digest(R/'deploy/fastfix'/NEW)
 cmd('systemctl','--user','daemon-reload')
 say('Continuing same authorized cutover: RC1 already inactive/disabled, no restart or GPU test yet')
 assert props(RC)['ActiveState']=='inactive' and props(RC)['UnitFileState']=='disabled'
 g=health();available=int(re.search(r'^MemAvailable:\s+(\d+)',pathlib.Path('/proc/meminfo').read_text(),re.M)[1])
 save('unloaded-resources.json',{'gpu':g,'host_available_kib':available})
 assert int(g['memory_free_size_byte'])>=22*1024**3 and available>=32*1024**2,'Resource conflict: no unrelated process termination'
 with socket.socket() as s:
  s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',18083))
 say('RC1 inactive/disabled; B60 released/healthy; starting permanent FastFix at18083')
 p=cmd('systemctl','--user','start',NEW,timeout=300);started=True;save('service-start.txt',p.stdout+p.stderr)
 status=props(NEW);save('fastfix-active.json',status);assert status['ActiveState']=='active' and status['SubState']=='running'
 ready=json.loads((R/'logs/fastfix-production/ready.json').read_text());save('ready.json',ready);assert ready['binary_sha256']==EXPECTED
 save('models.json',api('v1/models'));save('metrics-before-smoke.json',api('metrics'));save('status.json',api('status'))
 say(f'FastFix loaded: engine PID{ready["engine_pid"]},10831 GPU/13745 mirror, headroom{ready["engine"]["vram_free_mib"]}MiB')
 bodies={
  'english':{'model':'swift-1.5-iq3_xxs','messages':[{'role':'user','content':'In two sentences, explain why salt water freezes below zero Celsius.'}],'max_tokens':64,'temperature':0,'seed':42,'chat_template_kwargs':{'enable_thinking':False}},
  'chinese':{'model':'swift-1.5-iq3_xxs','messages':[{'role':'user','content':'請用兩句繁體中文解釋：為甚麼海水的冰點低於攝氏零度？'}],'max_tokens':64,'temperature':0,'seed':42,'chat_template_kwargs':{'enable_thinking':False}},
  'math':{'model':'swift-1.5-iq3_xxs','messages':[{'role':'user','content':'What is 6 times 7? Reply only with the number.'}],'max_tokens':16,'temperature':0,'seed':42,'chat_template_kwargs':{'enable_thinking':False}}}
 rows={n:request(n,b) for n,b in bodies.items()}
 assert rows['math']['choices'][0]['message']['content'].strip()=='42'
 assert sum(row['timings']['draft_n'] for row in rows.values())>0,'No drafting observed'
 m=api('metrics');save('metrics-final.json',m)
 record=json.loads((R/'logs/fastfix-production/current.json').read_text())
 with pathlib.Path(record['engine_log']).open('rb') as f:
  f.seek(record['engine_log_start']);log=f.read().decode('utf-8','replace')
 assert not re.search(r'holes=[1-9]|invalid=[1-9]|missing=[1-9]|readiness.*(?:timeout|expired)|device wait expired|FASTFIX_UNSAFE_TEARDOWN|terminate called',log,re.I)
 generations=re.findall(r'APLAN_RESIDENCY upload=(\d+) generation=(\d+) adapt_every=4 adapt_swaps=96 holes=0',log)
 swaps=re.findall(r'^APLAN_EXCHANGE ',log,re.M);assert generations and swaps,'Adaptive ON did not actually execute in smoke'
 save('adaptive-smoke.json',{'pair_exchanges':len(swaps),'committed_generations':len(generations),'holes':0,'mtp_suffix_proposed':sum(x['timings']['draft_n'] for x in rows.values()),'mtp_suffix_accepted':sum(x['timings']['draft_n_accepted'] for x in rows.values())})
 web={}
 with urllib.request.urlopen('http://127.0.0.1:18083/',timeout=10) as f:html=f.read().decode();web['root_status']=f.status
 assert all('tab-btn-'+name in html for name in ['chat','monitor','about'])
 for path in sorted(set(re.findall(r'(?:src|href)=["\'](web/[^"\'#]+)',html))):
  with urllib.request.urlopen('http://127.0.0.1:18083/'+path,timeout=10) as f:content=f.read();web[path]={'status':f.status,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
  assert content and hashlib.sha256(content).hexdigest()==digest(R/'serve'/path),path
 save('native-ui-assets.json',web)
 save('running-container.json',json.loads(cmd('docker','inspect','jr-strata-fastfix-engine').stdout))
 save('runtime-maps.txt',cmd('docker','exec','jr-strata-fastfix-engine','cat','/proc/1/maps').stdout)
 health()
 cmd('systemctl','--user','enable',NEW)
 final=props(NEW);rc=props(RC);assert final['ActiveState']=='active' and final['UnitFileState']=='enabled' and rc['ActiveState']=='inactive' and rc['UnitFileState']=='disabled'
 assert RC in final['Conflicts']
 linger=cmd('loginctl','show-user','james','-p','Linger','--value').stdout.strip();assert linger=='yes'
 assert (pathlib.Path('/home/james/.config/systemd/user/default.target.wants')/NEW).resolve()==installed
 assert {p:digest(p) for p in protected}==protected,'Protected historical files changed'
 assert digest(installed)==digest(R/'deploy/fastfix'/NEW)
 result={'status':'PASS','fastfix':final,'rc1':rc,'server_pid':int(final['MainPID']),'engine_pid':ready['engine_pid'],'binary_sha256':EXPECTED,
         'context':131072,'gpu_experts':10831,'gpu_cache_mib':17990,'mirror_experts':13745,'loaded_headroom_mib':ready['engine']['vram_free_mib'],
         'adaptive_pair_exchanges_smoke':len(swaps),'adaptive_generations_smoke':len(generations),'gpu_faults_resets':0,
         'native_ui':'http://127.0.0.1:18083/','linger':linger,'boot_autostart':'enabled default.target symlink and existing Linger=yes; reboot not performed',
         'rc1_artifacts_unchanged':True,'no_rc1_fallback':True,'elapsed_s':time.time()-start}
 save('result.json',result);say('PASS: FastFix ACTIVE/ENABLED; RC1 INACTIVE/DISABLED; APIs/native assets/drafting/adaptive swaps/health PASS')
except Exception as exc:
 save('incident.json',{'error':repr(exc),'elapsed_s':time.time()-start,'rc1_stopped':stopped,'fastfix_started':started,'policy':'No RC1 restart/fallback; preserve diagnostics and assess FastFix/hardware'})
 say('BLOCKER: '+repr(exc)+'; RC1 will not be restored automatically')
 if stopped:
  try:
   cmd('systemctl','--user','disable',NEW)
   cmd('systemctl','--user','stop',NEW,timeout=190)
   save('failed-fastfix-journal.txt',cmd('journalctl','--user','-u',NEW,'--since',f'@{start:.0f}','--no-pager').stdout)
   save('failed-kernel.txt',cmd('journalctl','-k','--since',f'@{start:.0f}','--no-pager','-o','short-iso-precise').stdout)
  except Exception as cleanup:
   save('unsafe-cleanup.json',{'error':repr(cleanup),'note':'No force-kill issued; inspect surviving engine/hardware before any restart'})
 raise
