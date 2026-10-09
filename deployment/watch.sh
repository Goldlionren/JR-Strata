#!/usr/bin/env bash
set -euo pipefail
root=${1:?Usage: watch.sh INSTALL_DIR}
exec python3 -B - "$root" <<'EOF'
import json,pathlib,subprocess,sys,urllib.request
r=pathlib.Path(sys.argv[1]).expanduser();s=json.loads((r/'deployment/settings.json').read_text())
print(subprocess.run(['systemctl','--user','status',s['unit'],'--no-pager'],text=True,capture_output=True).stdout)
for endpoint in ['status','metrics']:
 try:
  with urllib.request.urlopen(f"http://127.0.0.1:{s['port']}/{endpoint}",timeout=3) as f: print(endpoint,json.dumps(json.load(f),ensure_ascii=False))
 except OSError as e: print(endpoint,'N/A',e)
print(pathlib.Path('/proc/meminfo').read_text())
p=subprocess.run(['journalctl','-k','--since','-15min','--no-pager'],text=True,capture_output=True)
import re
print('Recent GPU faults:', '\n'.join(x for x in p.stdout.splitlines() if re.search(r'xe.*(fault|reset|wedged)|GPU.*(HANG|fault|reset)',x,re.I)) or ('N/A' if p.returncode or p.stderr else 'none in accessible interval'))
EOF
