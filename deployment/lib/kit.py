#!/usr/bin/env python3
"""Portable packaging only. No engine builds, GPU tests, process census or driver changes."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys,tarfile,tempfile,venv
from pathlib import Path
D=Path(__file__).resolve().parents[1]
SOURCE=D.parent
TAG='jr-b60-sycl-fastfix-prod-20261009'
def read(p):return json.loads(Path(p).read_text())
def digest(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*a,**kw):return subprocess.run(a,check=True,text=True,capture_output=True,timeout=kw.pop('timeout',120),**kw)
def require(ok,msg):
 if not ok:raise ValueError(msg)
def asset_check(data,report=None):
 expected=read(D/'manifests/assets.json');cached=read(report)['files'] if report else None
 for name,x in expected.items():
  p=data/name;require(p.is_file(),'Missing external asset: '+str(p));st=p.stat()
  require(st.st_size==x['bytes'],'Asset size mismatch: '+name)
  if cached:
   c=cached.get(name,{})
   require(c.get('sha256')==x['sha256'] and all(c.get(k)==v for k,v in {'bytes':st.st_size,'inode':st.st_ino,'mtime_ns':st.st_mtime_ns}.items()),'Reused-asset fingerprint changed: '+name)
  else:require(digest(p)==x['sha256'],'Asset SHA256 mismatch: '+name)
 return {'files':len(expected),'mode':'operator-supplied prior full SHA256 report + unchanged inode/size/mtime' if cached else 'full SHA256'}
def safe_extract(archive,destination):
 with tarfile.open(archive,'r:gz') as t:
  for m in t.getmembers():
   require(not (m.issym() or m.islnk() or m.isdev()),'Unsafe archive member type')
   q=(destination/m.name).resolve()
   require(q.is_relative_to(destination.resolve()),'Archive path traversal')
  t.extractall(destination,filter='data')
def verify_payload(path):
 sums=D/'manifests/artifacts.sha256'
 require(sums.exists(),'Missing release artifact manifest')
 for line in sums.read_text().splitlines():
  sha,name=line.split(None,1);p=path/name.strip()
  require(p.is_file() and digest(p)==sha,'Release checksum mismatch: '+name)
def gpu_identity(pci=None,sysroot=Path('/sys')):
 devices=sysroot/'bus/pci/devices'
 matches=[p.name for p in devices.iterdir() if (p/'vendor').exists() and (p/'device').exists() and (p/'vendor').read_text().strip()=='0x8086' and (p/'device').read_text().strip()=='0xe211']
 require(pci in matches if pci else len(matches)==1,'Select one B60 explicitly with --gpu-pci; no BDF is assumed')
 pci=pci or matches[0];dev=devices/pci
 require((dev/'driver').resolve().name=='xe','B60 must use xe driver')
 nodes=[]
 for node in (sysroot/'class/drm').glob('*'):
  if re.fullmatch(r'(card|renderD)\d+',node.name) and (node/'device').resolve()==dev.resolve():nodes.append('/dev/dri/'+node.name)
 require(any('renderD' in n for n in nodes),'No matching B60 render node')
 return pci,sorted(nodes)
def systemd_quote(value):return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'
def generated(root,data,port,pci,nodes,unit):
 require(1024<=port<=65535,'Port must be1024..65535');require(re.fullmatch(r'jr-strata-sycl-[a-z0-9-]+\.service',unit),'Invalid dedicated service name')
 for p in (root,data):require(not any(c in str(p) for c in '\n\r\0:'),'Paths contain unsupported control/colon characters')
 config=json.loads((D/'config/fastfix-production.json').read_text().replace('@INSTALL_DIR@',str(root).replace('\\','\\\\').replace('"','\\"')).replace('@DATA_DIR@',str(data).replace('\\','\\\\').replace('"','\\"')))
 config['port']=port
 env={line.split('=',1)[0]:line.split('=',1)[1] for line in (D/'config/fastfix.env.example').read_text().splitlines() if line and not line.startswith('#')}
 settings={'release':TAG,'install_dir':str(root),'data_dir':str(data),'port':port,'gpu_pci':pci,'device_nodes':nodes,'unit':unit,'container_name':unit[:-8]+'-engine','environment':env}
 template=(D/'systemd/jr-strata-sycl-fastfix.service').read_text()
 service=template.replace('@PYTHON@',systemd_quote(root/'venv/bin/python')).replace('@START@',systemd_quote(root/'deployment/start.py')).replace('@READY@',systemd_quote(root/'deployment/ready.py')).replace('@WORKDIR@',str(root/'app').replace('%','%%'))
 return config,settings,service
def do_install(a):
 root=Path(a.install_dir).expanduser().resolve();data=Path(a.data_dir).expanduser().resolve();payload=Path(a.artifact_dir).resolve()
 require(sys.version_info[:2]==(3,12),'Use Python3.12 for the frozen linux/amd64 wheels')
 verify_payload(payload)
 check=asset_check(data,a.asset_report)
 pci,nodes=gpu_identity(a.gpu_pci)
 config,settings,service=generated(root,data,a.port,pci,nodes,a.unit_name)
 if root.exists():
  require((root/'deployment/settings.json').is_file(),'Unexpected install directory; refuse overwrite')
  require(read(root/'deployment/settings.json')==settings,'Existing installation settings differ; no overwrite')
  verify_installed(root,quiet=True)
 unitfile=Path.home()/'.config/systemd/user'/a.unit_name
 require(not unitfile.exists() or unitfile.read_text()==service,'Conflicting user unit; refuse replacement')
 plan={'dry_run':a.dry_run,'asset_verification':check,'settings':settings,'config':config,'unit':service,'will_start':False,'will_enable':False}
 print(json.dumps(plan,indent=2))
 if a.dry_run:return
 if not root.exists():
  root.parent.mkdir(parents=True,exist_ok=True)
  staging=Path(tempfile.mkdtemp(prefix='.jr-fastfix-',dir=root.parent))
  try:
   safe_extract(payload/'prebuilt-production.tar.gz',staging)
   shutil.copytree(D,staging/'deployment',ignore=shutil.ignore_patterns('__pycache__'))
   for path in ('serve','sycl/serve'):
    shutil.copytree(SOURCE/path,staging/'app'/path,ignore=shutil.ignore_patterns('__pycache__'))
   (staging/'app/tools').mkdir(parents=True);shutil.copy2(SOURCE/'tools/strata_tokenizer.py',staging/'app/tools/strata_tokenizer.py')
   shutil.copy2(SOURCE/'LICENSE',staging/'LICENSE');shutil.copytree(D/'assets',staging/'assets')
   require(digest(staging/'bin/strata')==read(D/'manifests/production-lock.json')['engine_sha256'],'Prebuilt ELF mismatch')
   (staging/'logs').mkdir();(staging/'deployment/settings.json').write_text(json.dumps(settings,indent=2)+'\n')
   (staging/'deployment/runtime.json').write_text(json.dumps(config,indent=2)+'\n')
   os.rename(staging,root)
  except BaseException:
   shutil.rmtree(staging);raise
 # A copied/moved venv has stale script shebangs. Create it at the final path.
 venv.EnvBuilder(with_pip=True).create(root/'venv')
 run(str(root/'venv/bin/python'),'-m','pip','install','--no-index','--find-links',str(root/'wheelhouse'),'--require-hashes','-r',str(root/'deployment/requirements-hashed.lock'),timeout=300)
 files={str(p.relative_to(root)):digest(p) for base in ['bin','app','deployment','assets'] for p in (root/base).rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name!='installed-files.json'}
 (root/'deployment/installed-files.json').write_text(json.dumps(files,indent=2)+'\n')
 if not a.no_systemd:
  unitfile.parent.mkdir(parents=True,exist_ok=True);unitfile.write_text(service);run('systemctl','--user','daemon-reload')
 print('Installed; NOT enabled or started. Load verified runtime, review prerequisites, then explicitly enable/start on the new host.')
def verify_installed(root,quiet=False):
 require(digest(root/'bin/strata')==read(D/'manifests/production-lock.json')['engine_sha256'],'Installed engine hash changed')
 for f,h in read(root/'deployment/installed-files.json').items():require(digest(root/f)==h,'Installed file changed: '+f)
 if not quiet:print('PASS installed ELF, native frontend, settings and launchers')
def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
 i=sub.add_parser('install');i.add_argument('--install-dir',default='~/.local/share/jr-strata-sycl');i.add_argument('--data-dir',required=True);i.add_argument('--artifact-dir',required=True);i.add_argument('--port',type=int,default=18083);i.add_argument('--gpu-pci');i.add_argument('--unit-name',default='jr-strata-sycl-fastfix.service');i.add_argument('--dry-run',action='store_true');i.add_argument('--no-systemd',action='store_true');i.add_argument('--asset-report',help='Explicitly reuse a trusted local full-hash report if physical file fingerprints are unchanged')
 v=sub.add_parser('verify');v.add_argument('--install-dir',required=True);v.add_argument('--data-dir');v.add_argument('--asset-report')
 a=p.parse_args()
 if a.action=='install':do_install(a)
 else:
  verify_installed(Path(a.install_dir).expanduser().resolve())
  if a.data_dir:print(json.dumps(asset_check(Path(a.data_dir).resolve(),a.asset_report)))
if __name__=='__main__':
 try:main()
 except (OSError,ValueError,subprocess.SubprocessError) as e:print('REFUSED: '+str(e),file=sys.stderr);sys.exit(78)
