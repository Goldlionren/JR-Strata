#!/usr/bin/env bash
set -euo pipefail
# Removes only this kit's registered user-unit. Retains installation, models and runtime.
root=${1:?Usage: uninstall.sh INSTALL_DIR}
exec python3 -B - "$root" <<'EOF'
import json,pathlib,subprocess,sys
r=pathlib.Path(sys.argv[1]).expanduser().resolve();s=json.loads((r/'deployment/settings.json').read_text())
u=pathlib.Path.home()/'.config/systemd/user'/s['unit']
if not u.exists():print('No installed unit; files retained');raise SystemExit
if str(r/'deployment/start.py').replace('%','%%') not in u.read_text():raise SystemExit('Conflicting unit; refuse removal')
subprocess.run(['systemctl','--user','stop',s['unit']],check=True,timeout=200)
st=subprocess.run(['systemctl','--user','show',s['unit'],'-p','ActiveState','--value'],check=True,capture_output=True,text=True).stdout.strip()
if st!='inactive':raise SystemExit('Teardown unresolved; do not disable/delete')
subprocess.run(['systemctl','--user','disable',s['unit']],check=True);u.unlink();subprocess.run(['systemctl','--user','daemon-reload'],check=True)
print('Own unit removed. Installation, external assets and Docker image retained.')
EOF
