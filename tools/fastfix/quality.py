"""Bounded checks of the four fixed functional tasks; natural-language review still required."""
import ast,json,re,sys
from pathlib import Path
for p in sorted(Path(sys.argv[1]).glob('*.json')):
 d=json.loads(p.read_text());s=d['content'];name=d['case'];assert not d['error'],d['error']
 if name=='python':
  m=re.search(r'```(?:python)?\s*\n(.*?)```',s,re.S);code=m[1] if m else s
  tree=ast.parse(code)
  forbidden=(ast.Import,ast.ImportFrom,ast.Attribute,ast.While,ast.For,ast.AsyncFor,ast.With,ast.ClassDef,ast.Lambda)
  assert not any(isinstance(n,forbidden) for n in ast.walk(tree)),'unexpected code outside fixed pure-function task'
  assert all(isinstance(n.func,ast.Name) and n.func.id in {'triangular','range'} for n in ast.walk(tree) if isinstance(n,ast.Call))
  ns={'__builtins__':{}};exec(compile(tree,'<model answer>','exec'),ns)
  assert all(ns['triangular'](n)==n*(n+1)//2 for n in (0,1,2,10,100)), 'Python numeric oracle'
 elif name=='math':assert re.search(r'\b6\b',s) and re.search(r'\b54\b',s),'width6/area54 missing'
 elif name=='english':assert 'salt' in s.lower() and any(x in s.lower() for x in ('freez','freez','ice')),'salinity explanation missing'
 elif name=='chinese':assert '盐' in s and any(x in s for x in ('冰','冻')),'Chinese salinity explanation missing'
 print(name,'PASS automated checks; natural-language semantics reviewed separately')
