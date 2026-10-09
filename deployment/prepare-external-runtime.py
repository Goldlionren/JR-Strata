#!/usr/bin/env python3
"""Split an operator-provided licensed exact archive, never download or replace a Docker image."""
import argparse,hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D/'lib'));import kit
p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--artifact-dir',required=True);a=p.parse_args()
m=kit.read(D/'docker/archive-parts.json');src=Path(a.archive);dest=Path(a.artifact_dir)
kit.require(kit.digest(src)==m['archive_sha256'],'External runtime archive mismatch');dest.mkdir(parents=True,exist_ok=True)
with src.open('rb') as f:
 for e in m['parts']:
  q=dest/e['name']
  if q.exists():
   kit.require(q.stat().st_size==e['bytes'] and kit.digest(q)==e['sha256'],'Existing conflicting archive part')
   f.seek(e['bytes'],1);continue
  tmp=q.with_suffix(q.suffix+'.partial');kit.require(not tmp.exists(),'Unexpected partial archive; inspect before replacement');h=hashlib.sha256();left=e['bytes']
  with tmp.open('xb') as o:
   while left:
    b=f.read(min(left,8*1024**2));kit.require(bool(b),'Truncated external archive');o.write(b);h.update(b);left-=len(b)
  kit.require(h.hexdigest()==e['sha256'],'Runtime part mismatch');tmp.rename(q)
 kit.require(not f.read(1),'Trailing archive bytes')
print('PASS exact licensed external runtime parts; Docker unchanged')
