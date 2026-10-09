#!/usr/bin/env python3
"""Exact OCI blobs; change only Docker-save transport tag annotations before loading."""
import argparse,hashlib,io,json,subprocess,sys,tarfile
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D/'lib'));import kit
def rewrite_stream(source,output,alias):
 with tarfile.open(fileobj=source,mode='r|') as tin,tarfile.open(fileobj=output,mode='w|') as tout:
  for member in tin:
   kit.require(not member.issym() and not member.islnk() and '..' not in Path(member.name).parts and not Path(member.name).is_absolute(),'Unsafe runtime tar member')
   f=tin.extractfile(member) if member.isfile() else None
   if member.name.lstrip('./') in ('manifest.json','index.json'):
    data=json.load(f)
    if isinstance(data,list):
     for item in data:item['RepoTags']=[alias]
    else:
     for descriptor in data['manifests']:
      descriptor.setdefault('annotations',{}).update({'io.containerd.image.name':'docker.io/library/'+alias,'org.opencontainers.image.ref.name':alias.split(':')[1]})
    b=json.dumps(data).encode();member.size=len(b);f=io.BytesIO(b)
   tout.addfile(member,f)
def main():
 p=argparse.ArgumentParser();p.add_argument('--artifact-dir',required=True);p.add_argument('--verify-only',action='store_true');a=p.parse_args();root=Path(a.artifact_dir)
 m=kit.read(D/'docker/runtime-manifest.json');parts=kit.read(D/'docker/archive-parts.json');h=hashlib.sha256()
 for entry in parts['parts']:
  part=root/entry['name'];ph=hashlib.sha256()
  with part.open('rb') as f:
   while b:=f.read(8*1024**2):h.update(b);ph.update(b)
  kit.require(ph.hexdigest()==entry['sha256'] and part.stat().st_size==entry['bytes'],'Runtime part checksum failed')
 kit.require(h.hexdigest()==parts['archive_sha256'],'Runtime archive checksum failed')
 if a.verify_only:print('PASS exact archive and all parts; no Docker mutation');return
 # Refuse overwriting a differently identified existing alias; do not touch the old tag.
 found=subprocess.run(['docker','image','inspect',m['local_alias']],text=True,capture_output=True,timeout=20)
 if found.returncode==0:
  x=json.loads(found.stdout)[0]
  kit.require(x['Id'] in (m['image_id'],m['oci_config_digest']) and x['RootFS']['Layers']==m['rootfs_diff_ids'],'Conflicting restored tag')
  print('Verified runtime alias already installed; unchanged');return
 kit.require('No such image' in found.stderr,'Docker inspect failed; cannot assume alias is absent')
 # Concatenated parts stream into zstd without constructing a second huge archive.
 decoder=subprocess.Popen(['zstd','-dc'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
 loader=subprocess.Popen(['docker','load'],stdin=subprocess.PIPE)
 import threading
 errors=[]
 def feed():
  try:
   for entry in parts['parts']:
    with (root/entry['name']).open('rb') as f:
     while b:=f.read(4*1024**2):decoder.stdin.write(b)
   decoder.stdin.close()
  except BaseException as e:errors.append(e)
 worker=threading.Thread(target=feed);worker.start()
 try:rewrite_stream(decoder.stdout,loader.stdin,m['local_alias'])
 finally:loader.stdin.close()
 worker.join();kit.require(not errors and decoder.wait()==0 and loader.wait()==0,'Runtime load failed')
 x=json.loads(kit.run('docker','image','inspect',m['local_alias']).stdout)[0]
 kit.require(x['Id'] in (m['image_id'],m['oci_config_digest']) and x['RootFS']['Layers']==m['rootfs_diff_ids'] and x['Architecture']=='amd64' and x['Config']['Env']==m['base_environment'],'Loaded runtime content mismatch')
 print('Loaded exact production OCI content under distinct alias: '+x['Id'])
if __name__=='__main__':
 try:main()
 except (OSError,ValueError,subprocess.SubprocessError) as e:print('REFUSED: '+str(e),file=sys.stderr);sys.exit(78)
