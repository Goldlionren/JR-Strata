#!/usr/bin/env python3
import importlib.util,io,json,sys,tarfile,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'lib'));import kit
spec=importlib.util.spec_from_file_location('load_runtime',Path(__file__).parent/'load-runtime.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
class Packaging(unittest.TestCase):
 def test_fixed_profile(self):
  cfg,s,u=kit.generated(Path('/opt/frozen kit'),Path('/assets models'),18087,'0000:03:00.0',['/dev/dri/renderD129'],'jr-strata-sycl-test.service')
  a=cfg['args'];self.assertEqual(a[a.index('--expert-cache')+1],'8098');self.assertEqual(a[a.index('--spec')+1],'4');self.assertEqual(a[a.index('--prefill')+1],'4096');self.assertIn('/assets/models/',a[a.index('--native')+1]);self.assertNotIn('/data/strata-lab',json.dumps((cfg,s,u)));self.assertIn('WorkingDirectory=/opt/frozen kit/app',u);self.assertIn('SendSIGKILL=no',u);self.assertIn('KillMode=process',u);self.assertNotIn('ExecStop=',u)
 def test_port_unit_rejected(self):
  for port,unit in [(80,'jr-strata-sycl-test.service'),(18087,'../../bad')]:
   with self.assertRaises(ValueError):kit.generated(Path('/x'),Path('/y'),port,'x',[],unit)
 def test_idempotent_generation(self):
  a=(Path('/x'),Path('/y'),18087,'0000:03:00.0',['/dev/dri/card2','/dev/dri/renderD129'],'jr-strata-sycl-test.service');self.assertEqual(kit.generated(*a),kit.generated(*a))
 def test_systemd_escape(self):self.assertEqual(kit.systemd_quote('/x/%/a"b'),'"/x/%%/a\\"b"')
 def test_gpu_selection(self):
  with tempfile.TemporaryDirectory() as d:
   sysroot=Path(d);dev=sysroot/'bus/pci/devices/0000:03:00.0';dev.mkdir(parents=True);(dev/'vendor').write_text('0x8086');(dev/'device').write_text('0xe211');(sysroot/'drivers/xe').mkdir(parents=True);(dev/'driver').symlink_to(sysroot/'drivers/xe');node=sysroot/'class/drm/renderD129';node.mkdir(parents=True);(node/'device').symlink_to(dev)
   self.assertEqual(kit.gpu_identity(sysroot=sysroot),('0000:03:00.0',['/dev/dri/renderD129']))
   with self.assertRaises(ValueError):kit.gpu_identity('0000:07:00.0',sysroot)
 def test_tar_rejects_parent(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.tgz'
   with tarfile.open(p,'w:gz') as t:m=tarfile.TarInfo('../escape');m.size=1;t.addfile(m,io.BytesIO(b'x'))
   with self.assertRaises(ValueError):kit.safe_extract(p,Path(d)/'out')
 def test_transport_only_relabel(self):
  src=io.BytesIO();out=io.BytesIO();blob=b'original runtime bytes'
  with tarfile.open(fileobj=src,mode='w') as t:
   for name,data in [('manifest.json',json.dumps([{'RepoTags':['original:latest']}]).encode()),('index.json',json.dumps({'manifests':[{'digest':'sha256:unchanged'}]}).encode()),('blobs/sha256/test',blob)]:
    m=tarfile.TarInfo(name);m.size=len(data);t.addfile(m,io.BytesIO(data))
  src.seek(0);loader.rewrite_stream(src,out,'separate:prod');out.seek(0)
  with tarfile.open(fileobj=out) as t:self.assertEqual(t.extractfile('blobs/sha256/test').read(),blob);self.assertEqual(json.load(t.extractfile('manifest.json'))[0]['RepoTags'],['separate:prod']);self.assertEqual(json.load(t.extractfile('index.json'))['manifests'][0]['digest'],'sha256:unchanged')
 def test_failure_lifecycle(self):
  u=(kit.D/'systemd/jr-strata-sycl-fastfix.service').read_text();self.assertIn('RestartPreventExitStatus=78 86',u);self.assertIn('StartLimitBurst=3',u)
 def test_frozen_identity(self):
  m=kit.read(kit.D/'manifests/production-lock.json');self.assertNotEqual(m['deployment_commit'],m['engine_source_commit']);self.assertEqual(m['engine_sha256'],'8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e')
if __name__=='__main__':unittest.main()
