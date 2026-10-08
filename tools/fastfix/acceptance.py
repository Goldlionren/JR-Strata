#!/usr/bin/env python3
"""One bounded historical functional/sustained sequence. Does not manage services."""
import argparse,json,re,subprocess,threading,time,urllib.request
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[2];E=Path(os.environ['FASTFIX_EVIDENCE']);NAME='jr-strata-fastfix-engine'
PROBE=r"""import json,re,time
from pathlib import Path
p=Path('/proc/1');x={'epoch':time.time(),'io':{k:int(v) for k,v in (l.split(':') for l in (p/'io').read_text().splitlines())}}
st=(p/'stat').read_text().split(') ',1)[1].split();x.update(majflt=int(st[9]),minflt=int(st[7]))
for key in ('VmRSS','VmHWM','VmSwap'):
 m=re.search('^'+key+r':\s+(\d+)',(p/'status').read_text(),re.M);x[key+'_kib']=int(m[1]) if m else None
seen=set()
for f in (p/'fdinfo').iterdir():
 try:s=f.read_text()
 except FileNotFoundError:continue
 if '0000:07:00.0' not in s:continue
 m=re.search(r'drm-client-id:\s+(\d+)',s)
 if not m or m[1] in seen:continue
 seen.add(m[1])
 for key,tag in [('vram_kib','drm-total-vram0'),('gtt_kib','drm-total-gtt')]:
  z=re.search(tag+r':\s+(\d+)',s)
  if z:x[key]=x.get(key,0)+int(z[1])
print(json.dumps(x))"""
def snapshot():
 p=subprocess.run(['docker','exec',NAME,'python3','-c',PROBE],capture_output=True,text=True,check=True,timeout=8);x=json.loads(p.stdout)
 m=Path('/proc/meminfo').read_text();x['host_available_kib']=int(re.search(r'^MemAvailable:\s+(\d+)',m,re.M)[1]);v=Path('/proc/vmstat').read_text()
 for k in ('pswpin','pswpout'):x[k]=int(re.search('^'+k+r'\s+(\d+)',v,re.M)[1])
 
 try:x['device_stats']=json.loads(subprocess.run(['xpu-smi','stats','-d','0000:07:00.0','-j'],capture_output=True,text=True,check=True,timeout=5).stdout)
 except (OSError,ValueError,subprocess.SubprocessError):x['device_stats']='N/A'
 return x

def health():
 t=json.loads((E/'cutover.json').read_text())['start_epoch'];p=subprocess.run(['journalctl','-k','--since',f'@{t:.0f}','--no-pager'],capture_output=True,text=True,check=True,timeout=8);(E/'kernel-acceptance.txt').write_text(p.stdout)
 if re.search('permission|not seeing messages',p.stderr,re.I):raise RuntimeError('kernel journal inaccessible')
 if re.search(r'(?:xe.*(?:fault|reset|wedged|CAT error|Timedout)|GPU.*(?:HANG|reset|fault))',p.stdout,re.I):raise RuntimeError('SERIOUS GPU FAULT; halt and assess before restart')

p=argparse.ArgumentParser();p.add_argument('suite',choices=['functional','sustained']);a=p.parse_args()
work=[('english','Explain why seawater freezes below zero Celsius in two concise sentences.',128),('chinese','请用两句简洁的中文解释为什么盐水的冰点低于纯水。',128),('python','Return only Python code defining triangular(n) for nonnegative integers, and assertions for n=0,1,10. Use a closed-form formula.',192),('math','A rectangle has perimeter 30 and length 9. Give its width and area with a brief calculation. Keep the answer under 80 words.',192)]
if a.suite=='sustained':
 work=[('sustained','Write a practical field manual for volunteers starting a community vegetable garden. Cover site assessment, soil preparation, irrigation, crop rotation, pest management, shared responsibilities, seasonal scheduling, record keeping and troubleshooting. Include concrete examples and explain tradeoffs. Aim for at least 3000 words; continue until the manual is detailed and useful.',2048)]
out=E/(os.environ.get('FASTFIX_ARM','historical')+'-'+a.suite);out.mkdir(exist_ok=False)
for i,(name,prompt,cap) in enumerate(work):
 health();before=snapshot();samples=[];stop=threading.Event();issues=[]
 def sample():
  while not stop.is_set():
   try:
    x=snapshot();samples.append(x);health()
    if x['host_available_kib']<4*1024**2:raise RuntimeError('RAM headroom below4GiB')
   except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:issues.append(str(e));return
   stop.wait(2)
 thread=threading.Thread(target=sample);thread.start();start=time.monotonic();row={'case':name,'prompt':prompt,'max_tokens':cap,'before':before,'ttft_s':None};text=[];reason=[];err=None
 body={'model':'swift-1.5-iq3_xxs','messages':[{'role':'user','content':prompt}],'temperature':0,'seed':42,'max_tokens':cap,'chat_template_kwargs':{'enable_thinking':False},'stream':True,'stream_options':{'include_usage':True}}
 row['request']=body
 try:
  req=urllib.request.Request('http://127.0.0.1:18086/v1/chat/completions',json.dumps(body).encode(),{'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=90) as f:
   for raw in f:
    if issues:raise RuntimeError(issues[0])
    if time.monotonic()-start>(600 if cap>=2000 else 120):raise TimeoutError('request deadline')
    if not raw.startswith(b'data: '):continue
    if raw.strip()==b'data: [DONE]':break
    d=json.loads(raw[6:])
    if d.get('error'):raise RuntimeError(str(d['error']))
    for c in d.get('choices',[]):
     delta=c.get('delta',{});x=delta.get('content') or '';y=delta.get('reasoning_content') or ''
     if (x or y) and row['ttft_s'] is None:row['ttft_s']=time.monotonic()-start
     text.append(x);reason.append(y)
     if c.get('finish_reason'):row['finish_reason']=c['finish_reason']
    for k in ('usage','timings'):
     if d.get(k):row[k]=d[k]
    full=''.join(text)
    if '!!!!!' in full or '\ufffd' in full:raise RuntimeError('confirmed punctuation/invalid-token corruption')
  if not row.get('usage') or not ''.join(text):raise RuntimeError('empty response/missing usage')
  health()
 except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as ex:err=str(ex)
 finally:
  stop.set();thread.join(timeout=20);row.update(content=''.join(text),reasoning=''.join(reason),elapsed_s=time.monotonic()-start,error=err,samples=samples)
  try:row['after']=snapshot();row['native_metrics']=json.load(urllib.request.urlopen('http://127.0.0.1:18086/metrics',timeout=5))
  except (OSError,ValueError,subprocess.SubprocessError) as ex:row['after_error']=str(ex)
  (out/f'{i:02d}-{name}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:row.get(k) for k in ('case','usage','timings','error','content')},ensure_ascii=False),flush=True)
 if err:raise SystemExit(1)
