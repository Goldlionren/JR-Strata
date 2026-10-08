#!/usr/bin/env python3
"""CPU-only plan/identity check. This tool never manages services or executes GPU work."""
import argparse,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
TOTAL=900
EXPERIMENT_END=600
STARTUP=120
REQUEST=180
TEARDOWN=90
ARM_BOUND=STARTUP+REQUEST+TEARDOWN
def admit_arm(elapsed):
    return elapsed>=0 and elapsed+ARM_BOUND<=EXPERIMENT_END

def plan():
    return {'maximum_seconds':TOTAL,'experimental_cleanup_deadline_seconds':EXPERIMENT_END,
            'restoration_reserve_seconds':TOTAL-EXPERIMENT_END,'probe_bound_seconds':60,
            'arm_bound_seconds':ARM_BOUND,'last_arm_admission_seconds':EXPERIMENT_END-ARM_BOUND,
            'order':['prepared captured-plan probe','static: --adapt-swaps 0, one1536-token request',
                     'optional adaptive: unchanged defaults, same request, only after clean static teardown and deadline admission'],
            'binary_sha256':'6b00ee839b6cf342fc85bdefa504e17fa80cc3fd94f766611e3707bf1120d6fe',
            'gpu_execution':False,'production_lifecycle_actions':False}

def verify():
    p=R/'tools/fastfix/adaptive-control-frozen.json'
    with p.open() as f:m=json.load(f)
    for path,h in m['files'].items():
        with (R/path).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=h:raise SystemExit('BLOCKED identity mismatch: '+path)
    return len(m['files'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    result=plan()
    if a.verify:result['verified_files']=verify()
    print(json.dumps(result,indent=2))
