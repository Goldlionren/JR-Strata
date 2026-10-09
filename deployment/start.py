#!/usr/bin/env python3
"""Host-side portable packaging gate, then unchanged native Intel server."""
import fcntl,hashlib,json,os,re,socket,subprocess,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parent
sys.path.insert(0,str(D/'lib'))
import kit
FAULT=r'(?:xe.*(?:fault|reset|wedged|CAT error|Timedout)|GPU.*(?:HANG|reset|fault))'
ENGINE_ERROR=r'FASTFIX_UNSAFE_TEARDOWN|readiness.*(?:timeout|expired)|device wait expired|invalid draft|uncovered expert|mirror.*(?:ownership|coverage).*fail|terminate called|UR_RESULT_ERROR_'
def command(*a):return kit.run(*a,timeout=20).stdout
def health(since):
 p=kit.run('journalctl','-k','--since',f'@{since:.0f}','--no-pager','-o','short-iso-precise',timeout=15)
 kit.require(not re.search('permission|not seeing messages',p.stderr,re.I),'Kernel diagnostics inaccessible; arrange read-only journal access')
 kit.require(not re.search(FAULT,p.stdout,re.I),'GPU fault/reset: assess hardware; no automatic fallback')
 return p.stdout
def image_identity(ref):
 m=kit.read(D/'docker/runtime-manifest.json');x=json.loads(command('docker','image','inspect',ref))[0]
 kit.require(x['Architecture']=='amd64' and x['Os']=='linux' and x['RootFS']['Layers']==m['rootfs_diff_ids'] and x['Config']['Env']==m['base_environment'] and x['Id'] in (m['image_id'],m['oci_config_digest']),'Frozen Docker content mismatch')
 return x['Id']
def main():
 kit.verify_installed(R);s=kit.read(D/'settings.json');state=R/'logs';lock=open(state/'service.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.set_inheritable(lock.fileno(),True)
 prior=kit.read(state/'current.json') if (state/'current.json').exists() else None
 if prior:
  log=state/'engine.log'
  if log.exists():
   with log.open('rb') as f:f.seek(prior['log_offset']);text=f.read().decode('utf8','replace')
   kit.require(not re.search(ENGINE_ERROR,text,re.I),'Prior safety incident; operator assessment required before restart')
 health(min(time.time()-900,prior['epoch']) if prior else time.time()-900)
 pci,nodes=kit.gpu_identity(s['gpu_pci']);kit.require(nodes==s['device_nodes'],'GPU device mappings changed; explicit reinstall/review required')
 g=json.loads(command('xpu-smi','discovery','-d',pci,'-j'))
 kit.require(g.get('pci_bdf_address')==pci and g.get('pci_device_id')=='0xe211' and g.get('pci_vendor_id')=='0x8086' and g.get('device_state')=='normal','B60 identity/health changed')
 avail=int(re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M)[1])
 kit.require(int(g['memory_free_size_byte'])>=22*1024**3 and avail>=32*1024**2,'Insufficient resources; never terminate another workload to make room')
 # Practical operator-controlled resource policy: no claim of complete process enumeration.
 names=command('docker','ps','-a','--format','{{.Names}}').splitlines();kit.require(s['container_name'] not in names,'Existing owned engine container; assess, do not kill')
 rc=subprocess.run(['systemctl','--user','is-active','jr-strata-sycl-rc1.service'],capture_output=True,text=True,timeout=10)
 kit.require(rc.stdout.strip() not in ('active','activating','deactivating'),'RC1 is still active/releasing GPU')
 image=image_identity(kit.read(D/'docker/runtime-manifest.json')['local_alias'])
 with socket.socket() as sock:sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sock.bind(('127.0.0.1',s['port']))
 log=state/'engine.log';record={'epoch':time.time(),'server_pid':os.getpid(),'image':image,'log_offset':log.stat().st_size if log.exists() else 0}
 (state/'current.json').write_text(json.dumps(record,indent=2)+'\n')
 env=os.environ.copy();env.update(FASTFIX_PACKAGED='1',FASTFIX_P0='1',FASTFIX_APLAN_DIAG='1',FASTFIX_NO_DRAFT='0',FASTFIX_NO_HOST='0',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
 os.chdir(R/'app');os.execve(sys.executable,[sys.executable,'-B',str(D/'server-entry.py'),'--engine','strata','--config',str(D/'runtime.json'),'--host','127.0.0.1','--port',str(s['port'])],env)
if __name__=='__main__':
 try:main()
 except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:print('FastFix REFUSED: '+str(e),file=sys.stderr);sys.exit(78)
