#!/usr/bin/env python3
"""CPU-only artifact/admission plan. Never executes GPU work or production lifecycle actions."""
import argparse, hashlib, json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
TOTAL=1200
EXPERIMENT_END=900
TEARDOWN=90
STAGES=[('seven existing safety tests',120),('existing captured readiness probe',30),
        ('actual GGUF mirror/captured payload probe',120),('Adaptive ON startup',120),
        ('one2048-token Adaptive ON generation',240),('three subsequent short requests',90),
        ('graceful experimental cleanup',90)]
def admit(elapsed, work_bound):
    return elapsed >= 0 and work_bound >= 0 and elapsed+work_bound+TEARDOWN <= EXPERIMENT_END

def plan():
    return {'maximum_seconds':TOTAL,'experimental_cleanup_deadline_seconds':EXPERIMENT_END,
            'restoration_reserve_seconds':TOTAL-EXPERIMENT_END,
            'stages':[{'name':n,'bound_seconds':s} for n,s in STAGES],
            'stage_bounds_total_seconds':sum(s for _,s in STAGES),
            'adaptive':'ON: existing4/96 policy, original ranking/cache/model/MTP unchanged',
            'gpu_execution':False,'production_lifecycle_actions':False,
            'authorization':'PENDING: no old approval is reused'}

def verify():
    with (R/'tools/fastfix/mirror-repair-candidate.json').open() as f:m=json.load(f)
    for path,expect in m['files'].items():
        with (R/path).open('rb') as f:got=hashlib.file_digest(f,'sha256').hexdigest()
        if got!=expect:raise SystemExit('BLOCKED identity mismatch: '+path)
    return len(m['files'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    result=plan()
    if a.verify:result['verified_files']=verify()
    print(json.dumps(result,indent=2))
