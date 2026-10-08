import json,subprocess,tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'python.json'
 for fenced in (False,True):
  s='def triangular(n):\n    return n*(n+1)//2\nassert triangular(10)==55\n'
  p.write_text(json.dumps({'case':'python','content':'```python\n'+s+'```' if fenced else s,'error':None}))
  subprocess.run(['python3','-B','tools/fastfix/quality.py',d],check=True)
 p.write_text(json.dumps({'case':'python','content':'def triangular(n):\n return 0','error':None}))
 assert subprocess.run(['python3','-B','tools/fastfix/quality.py',d],capture_output=True).returncode!=0
print('PASS: fenced/unfenced code and wrong formula rejected')
