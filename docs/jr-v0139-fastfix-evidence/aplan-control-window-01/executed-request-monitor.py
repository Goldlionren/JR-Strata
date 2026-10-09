import ast,json,re,subprocess,sys,time,urllib.request
from pathlib import Path
R=Path('/data/strata-lab/JR-Strata-SYCL-v0139-FastFix');E=R/'logs/fastfix/aplan-control-window-01';arm=sys.argv[1];assert arm in ('static','adaptive')
clock=json.loads((E/'cutover.json').read_text());end=clock['start_monotonic']+600
src=ast.parse((R/'tools/fastfix/p0-acceptance.py').read_text());PROBE=next(ast.literal_eval(n.value) for n in src.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PROBE' for x in n.targets))
def api(path):
 with urllib.request.urlopen('http://127.0.0.1:18086/'+path,timeout=3) as f:return json.load(f)
def snapshot():
 p=subprocess.run(['docker','exec','jr-strata-fastfix-engine','python3','-c',PROBE],capture_output=True,text=True,timeout=5,check=True);x=json.loads(p.stdout)
 mem=Path('/proc/meminfo').read_text();x['host_available_kib']=int(re.search(r'^MemAvailable:\s+(\d+)',mem,re.M)[1]);v=Path('/proc/vmstat').read_text()
 for k in ('pswpin','pswpout'):x[k]=int(re.search('^'+k+r'\s+(\d+)',v,re.M)[1])
 x['native_metrics']=api('metrics');return x
start=time.monotonic();row={'arm':arm,'start_epoch':time.time(),'elapsed_window_start':start-clock['start_monotonic'],'samples':[],'ttft_s':None,'error':None}
row['before']=snapshot();f=(E/f'{arm}-response.sse').open('w');cmd=['curl','--fail','--no-buffer','--max-time','180','http://127.0.0.1:18086/v1/chat/completions','-H','Content-Type: application/json','--data-binary','@'+str(R/'tools/fastfix/aplan-request.json')];p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
seen=0;chunks=[];reason=[];next_sample=0;next_print=0;failure=None
try:
 while True:
  now=time.monotonic();sse=(E/f'{arm}-response.sse').read_text()
  lines=sse.splitlines();complete_lines=lines if sse.endswith('\n') else lines[:-1]
  for line in complete_lines[seen:]:
   if not line.startswith('data: ') or line=='data: [DONE]':continue
   x=json.loads(line[6:])
   if x.get('error'):raise RuntimeError('API error: '+str(x['error']))
   for c in x.get('choices',[]):
    a=c.get('delta',{}).get('content') or '';b=c.get('delta',{}).get('reasoning_content') or ''
    chunks.append(a);reason.append(b)
    if (a or b) and row['ttft_s'] is None:row['ttft_s']=now-start
    if c.get('finish_reason'):row['finish_reason']=c['finish_reason']
   for k in ('usage','timings'):
    if x.get(k):row[k]=x[k]
  seen=len(complete_lines)
  text=''.join(chunks)
  if '!!!!!' in text or '\ufffd' in text or re.search(r'(.{40,200}?)\1{4}',text,re.S):raise RuntimeError('output corruption')
  log=(E/f'{arm}-engine.log').read_text()
  if re.search(r'readiness timeout|expert readiness device wait expired|FASTFIX_UNSAFE_TEARDOWN|UR_RESULT_ERROR|terminate called',log):raise RuntimeError('engine readiness/lifecycle error')
  hole=re.search(r'APLAN_RESIDENCY[^\n]*holes=([1-9]\d*)[^\n]*',log)
  bad=re.search(r'APLAN ring=[^\n]*(?:invalid|missing)=([1-9]\d*)[^\n]*',log)
  if hole or bad:raise RuntimeError('UNCOVERED/INVALID EXPERT: '+(hole or bad)[0])
  if now>=next_sample:
   k=subprocess.run(['journalctl','-k','--since',f'@{clock["start_epoch"]:.0f}','--no-pager','-o','short-iso-precise'],capture_output=True,text=True,timeout=5,check=True);(E/'kernel-request.txt').write_text(k.stdout)
   if re.search(r'(?:xe.*(?:fault|reset|wedged|CAT error|Timedout)|GPU.*(?:HANG|reset|fault))',k.stdout,re.I):raise RuntimeError('SERIOUS GPU FAULT')
   x=snapshot();row['samples'].append(x)
   if x['host_available_kib']<4*1024**2:raise RuntimeError('host RAM headroom below4GiB')
   next_sample=now+2
   if now>=next_print:
    print(json.dumps({'arm':arm,'request_s':round(now-start,1),'window_s':round(now-clock['start_monotonic'],1),'live':x['native_metrics'].get('live'),'sample_count':len(row['samples'])}),flush=True);next_print=now+15
  if p.poll() is not None:
   if p.returncode:raise RuntimeError('curl exit '+str(p.returncode))
   if '[DONE]' in sse:break
   raise RuntimeError('stream ended without DONE')
  if now-start>185 or now+90>end:raise RuntimeError('request/cleanup deadline')
  time.sleep(.2)
 if not row.get('usage') or row['usage'].get('completion_tokens')!=1536:raise RuntimeError('target actual token coverage incomplete')
 if not ''.join(chunks):raise RuntimeError('empty output')
 row['verdict']='PASS'
except Exception as ex:
 failure=str(ex);row['error']=failure;row['verdict']='FAIL';print('STOP',arm,failure,flush=True)
finally:
 row['content']=''.join(chunks);row['reasoning']=''.join(reason);row['elapsed_s']=time.monotonic()-start
 try:row['after']=snapshot()
 except Exception as ex:row['after_error']=str(ex)
 (E/f'{arm}-result.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:row.get(k) for k in ('arm','verdict','usage','timings','ttft_s','elapsed_s','error')},ensure_ascii=False),flush=True)
 # Native server-directed graceful shutdown, also on first failure. No engine signals.
 stop_start=time.monotonic();z=subprocess.run(['systemctl','--user','stop','jr-strata-fastfix-aplan-test.service'],capture_output=True,text=True,timeout=95)
 (E/f'{arm}-stop.txt').write_text(z.stdout+z.stderr)
 if p.poll() is None:
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5) # owned HTTP client only, after server stop
 f.close()
 (E/f'{arm}-journal.txt').write_text(subprocess.check_output(['journalctl','--user','-u','jr-strata-fastfix-aplan-test.service','--since',f'@{clock["start_epoch"]:.0f}','--no-pager','-o','short-iso-precise'],text=True,timeout=8))
 (E/f'{arm}-teardown.json').write_text(json.dumps({'returncode':z.returncode,'seconds':time.monotonic()-stop_start,'elapsed':time.monotonic()-clock['start_monotonic']},indent=2)+'\n')
 print('SERVER STOP return',z.returncode,'elapsed',time.monotonic()-clock['start_monotonic'],flush=True)
 if z.returncode:raise RuntimeError('unsafe service stop')
if failure:sys.exit(1)
