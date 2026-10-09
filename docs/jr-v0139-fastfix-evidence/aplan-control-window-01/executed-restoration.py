import hashlib,json,re,subprocess,time,urllib.request
from pathlib import Path
R=Path('/data/strata-lab/JR-Strata-SYCL-v0139-FastFix');E=R/'logs/fastfix/aplan-control-window-01';clock=json.loads((E/'cutover.json').read_text())
def run(*args,timeout=15):return subprocess.check_output(args,text=True,timeout=timeout).strip()
def save(name,x):(E/name).write_text(x if isinstance(x,str) else json.dumps(x,indent=2)+'\n')
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def api(path,port=18083):
 with urllib.request.urlopen(f'http://127.0.0.1:{port}/'+path,timeout=5) as f:return json.load(f)
def kernel(name):
 p=subprocess.run(['journalctl','-k','--since',f'@{clock["start_epoch"]:.0f}','--no-pager','-o','short-iso-precise'],capture_output=True,text=True,check=True,timeout=10);save(name,p.stdout)
 if re.search('permission|not seeing messages',p.stderr,re.I):raise RuntimeError('kernel inaccessible')
 if re.search(r'(?:xe.*(?:fault|reset|wedged|CAT error|Timedout)|GPU.*(?:HANG|reset|fault))',p.stdout,re.I):raise RuntimeError('SERIOUS GPU FAULT: no automatic restart; assess hardware')
 return p.stdout
assert time.monotonic()<clock['deadline_monotonic']-120,'insufficient recovery budget'
assert not run('ss','-H','-ltn','sport = :18086'),'experimental port survived'
containers=run('docker','ps','-a','--format','{{.Names}}');assert 'jr-strata-fastfix-engine' not in containers.splitlines() and 'jr-fastfix-aplan-probe' not in containers.splitlines(),containers
inspection=json.loads((E/'static-container.json').read_text())[0];epid=int(inspection['State']['Pid']);assert not Path(f'/proc/{epid}').exists(),epid
log=(E/'static-engine.log').read_text();assert not re.search(r'FASTFIX_UNSAFE_TEARDOWN|terminate called|UR_RESULT_ERROR',log),'unsafe teardown marker'
stop=json.loads((E/'static-teardown.json').read_text());assert stop['returncode']==0
kernel('kernel-before-restoration.txt')
x=json.loads(run('xpu-smi','discovery','-d','0000:07:00.0','-j'));save('b60-before-restoration.json',x);assert x['device_state']=='normal' and x['pci_device_id']=='0xe211' and int(x['memory_free_size_byte'])>22*1024**3,x
save('health-assessment.json',{'elapsed':time.monotonic()-clock['start_monotonic'],'experimental_engine_pid_gone':epid,'experimental_port_free':True,'experimental_containers_gone':True,'unsafe_marker':False,'new_gpu_faults':False,'b60_normal':True,'free_gpu_bytes':x['memory_free_size_byte'],'restoration_safe':True})
expected='cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028';rc='jr-strata-sycl-rc1.service';rcbin=Path('/data/strata-lab/JR-Strata-SYCL-v0.1.40.3/dist/jr-b60-sycl-v0.1.40.3-rc1/strata');assert sha(rcbin)==expected
before=json.loads((E/'protected-before.json').read_text());assert all(sha(path)==h for path,h in before.items()),'protected file mismatch'
print('Health assessment PASS; restoring unchanged RC1, elapsed',time.monotonic()-clock['start_monotonic'],flush=True)
subprocess.run(['systemctl','--user','start',rc],check=True,timeout=30)
t=time.monotonic()
while True:
 kernel('kernel-restoration.txt')
 try:
  models=api('v1/models')
  if models.get('data'):break
 except OSError:pass
 if time.monotonic()-t>180 or time.monotonic()>clock['deadline_monotonic']-60:raise RuntimeError('RC1 restoration startup deadline')
 time.sleep(2)
assert models['data'][0]['meta']['n_ctx']==32768;save('rc1-models-restored.json',models)
pid=int(run('systemctl','--user','show',rc,'-p','MainPID','--value'))
def kids(p):
 result=[]
 for v in Path(f'/proc/{p}/task/{p}/children').read_text().split():result+=[int(v)]+kids(int(v))
 return result
eng=[]
for p in kids(pid):
 try:
  if sha(f'/proc/{p}/exe')==expected:eng.append(p)
 except FileNotFoundError:pass
assert len(eng)==1,eng
m=api('metrics');assert m['engine']['expert_slots']==9248;save('rc1-metrics-restored-before-smoke.json',m);save('rc1-status-restored.json',api('status'))
body={'model':models['data'][0]['id'],'messages':[{'role':'user','content':'What is 2 plus 2? Answer in one short sentence.'}],'temperature':0,'max_tokens':32,'chat_template_kwargs':{'enable_thinking':False},'stream':False}
req=urllib.request.Request('http://127.0.0.1:18083/v1/chat/completions',json.dumps(body).encode(),{'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=60) as f:answer=json.load(f)
save('rc1-smoke.json',answer);text=answer['choices'][0]['message']['content'];assert text and ('4' in text or 'four' in text.lower()) and '!!!!!' not in text,text
save('rc1-monitor.json',json.loads(run('/home/james/.local/bin/jr-sycl-watch','--json')))
save('rc1-metrics-restored.json',api('metrics'))
with urllib.request.urlopen('http://127.0.0.1:18083/',timeout=5) as f:save('rc1-web-ui.html',f.read().decode())
kernel('kernel-final.txt');after={path:sha(path) for path in before};assert after==before;save('protected-after.json',after)
report={'status':'PASS','server_pid':pid,'engine_pid':eng[0],'running_sha256':expected,'context':32768,'expert_slots':9248,'active':run('systemctl','--user','is-active',rc),'enabled':run('systemctl','--user','is-enabled',rc),'elapsed':time.monotonic()-clock['start_monotonic'],'window_deadline_met':time.monotonic()<clock['deadline_monotonic'],'experimental_engine_gone':True,'gpu_faults':False,'smoke':text}
assert report['active']=='active';save('restoration.json',report);print(json.dumps(report,indent=2),flush=True)
