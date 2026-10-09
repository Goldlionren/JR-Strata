#!/usr/bin/env python3
"""Frozen FastFix startup, resource/incident gates; exec the unchanged native server."""
import datetime,fcntl,hashlib,json,os,re,socket,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
D=R/'deploy/fastfix'
STATE=R/'logs/fastfix-production'
IMAGE='sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44'
SHA='8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e'
BINARY=R/'dist/jr-b60-sycl-v0139-fastfix-adaptive-mirror/strata'
NAME='jr-strata-fastfix-engine'
FAULT=r'(?:xe.*(?:fault|reset|wedged|CAT error|Timedout)|GPU.*(?:HANG|reset|fault))'
ENGINE_FAILURE=r'FASTFIX_UNSAFE_TEARDOWN|readiness.*(?:timeout|expired)|device wait expired|invalid draft|uncovered expert|mirror.*(?:ownership|coverage).*fail|terminate called|UR_RESULT_ERROR_'
def command(*args,timeout=15):
    return subprocess.run(args,text=True,capture_output=True,check=True,timeout=timeout)
def digest(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify_identity():
    m=json.loads((D/'manifest.json').read_text())
    for path,sha in m['files'].items():
        if digest(R/path)!=sha:raise ValueError('Frozen identity mismatch: '+path)
    if command('docker','image','inspect',IMAGE,'--format','{{.Id}}').stdout.strip()!=IMAGE:
        raise ValueError('Historical Docker image ID mismatch')
def health(since):
    p=command('journalctl','-k','--since',f'@{since:.0f}','--no-pager','-o','short-iso-precise')
    if re.search('permission|not seeing messages',p.stderr,re.I):raise ValueError('Kernel fault diagnostics inaccessible')
    if re.search(FAULT,p.stdout,re.I):raise ValueError('GPU fault/reset: hardware assessment required; no automatic restart/fallback')
    g=json.loads(command('xpu-smi','discovery','-d','0000:07:00.0','-j').stdout)
    if g.get('pci_bdf_address')!='0000:07:00.0' or g.get('pci_device_id')!='0xe211' or g.get('pci_vendor_id')!='0x8086' or g.get('device_state')!='normal':
        raise ValueError('B60 identity/state mismatch')
    return g
def prior_incident_guard():
    path=STATE/'current.json'
    previous=json.loads(path.read_text()) if path.exists() else None
    if previous:
        log=Path(previous['engine_log'])
        if log.exists():
            with log.open('rb') as f:
                f.seek(previous['engine_log_start']);text=f.read().decode('utf-8','replace')
            if re.search(ENGINE_FAILURE,text,re.I):raise ValueError('Prior engine safety error: assess/repair before restart; evidence retained')
    return previous
def exclude_other_engine():
    active=command('systemctl','--user','show','jr-strata-sycl-rc1.service','-p','ActiveState','--value').stdout.strip()
    if active in ('active','activating','deactivating'):raise ValueError('RC1 still owns/is releasing GPU; refuse concurrent engines')
    names=command('docker','ps','-a','--format','{{.Names}}').stdout.splitlines()
    if NAME in names or any(n.startswith('jr-fastfix-mirror-') for n in names):raise ValueError('Existing owned FastFix container/probe; assess, do not terminate it here')
def main():
    STATE.mkdir(parents=True,exist_ok=True)
    lock=open(STATE/'production.lock','a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.set_inheritable(lock.fileno(),True)
    # Keep this file descriptor alive in the native server through exec.
    verify_identity();exclude_other_engine();previous=prior_incident_guard()
    since=min(time.time()-900,previous['start_epoch']) if previous else time.time()-900
    g=health(since)
    pci=Path('/sys/bus/pci/devices/0000:07:00.0')
    if (pci/'vendor').read_text().strip()!='0x8086' or (pci/'device').read_text().strip()!='0xe211':raise ValueError('PCI device changed')
    available=int(re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M)[1])
    if int(g['memory_free_size_byte'])<22*1024**3 or available<32*1024**2:raise ValueError('Insufficient resources: need22GiB unloaded B60 /32GiB MemAvailable; do not stop unrelated workloads')
    with socket.socket() as s:s.bind(('127.0.0.1',18083))
    cfg=json.loads((D/'runtime.json').read_text());log=Path(cfg['log'])
    record={'start_epoch':time.time(),'started_at':datetime.datetime.now().astimezone().isoformat(),'server_pid':os.getpid(),
            'binary':str(BINARY),'binary_sha256':SHA,'docker_image':IMAGE,'config':str(D/'runtime.json'),
            'engine_log':str(log),'engine_log_start':log.stat().st_size if log.exists() else 0,
            'host_available_kib':available,'gpu_free_bytes':int(g['memory_free_size_byte']),
            'validated_checkout':'c6a8a55dbd2989dd51f5355e9a83eb76198fe832','engine_source':'be3105e7f66ef4f9668ef129a1938800954b1b3b'}
    (STATE/'current.json').write_text(json.dumps(record,indent=2)+'\n')
    with (STATE/'starts.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
    env=os.environ.copy();env.update(FASTFIX_PRODUCTION='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',FASTFIX_P0='1',FASTFIX_APLAN_DIAG='1',FASTFIX_NO_DRAFT='0',FASTFIX_NO_HOST='0')
    os.chdir(R)
    print('FastFix frozen production: Adaptive4/96, MTP4,128K INT8/32K resident, localhost18083',flush=True)
    os.execve(sys.executable,[sys.executable,'-B',str(R/'sycl/serve/server_intel.py'),'--engine','strata','--config',str(D/'runtime.json'),'--host','127.0.0.1','--port','18083'],env)
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:
        print('FastFix startup REFUSED: '+str(exc),file=sys.stderr,flush=True);sys.exit(78)
