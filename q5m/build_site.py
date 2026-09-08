#!/usr/bin/env python3
"""Build the full Erdős static site for optional external review."""
from __future__ import annotations
import hashlib, json, os, shutil, stat, tempfile
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parent.parent
OUTPUT=ROOT/'build/q5m-site'
ALLOWED={'.html','.js','.css','.svg','.jpg','.png','.webp','.pdf','.txt','.xml','.json'}
SOURCE_FETCH="""fetch('gaussian_walk_demo.py', {cache: 'no-store'})
    .then(response => {
      if (!response.ok) throw new Error(`source request failed: ${response.status}`);
      return response.text();
    })"""

def regular(path:Path)->bytes:
 if path.is_symlink():raise ValueError(f'symlink refused: {path.relative_to(ROOT)}')
 info=path.stat()
 if not stat.S_ISREG(info.st_mode) or info.st_size>32*1024*1024:raise ValueError('unsafe site input')
 return path.read_bytes()

def build()->dict:
 outputs={};total=0
 for source,prefix in ((ROOT/'viz',PurePosixPath()),(ROOT/'results',PurePosixPath('family'))):
  if source.is_symlink() or not source.is_dir():raise ValueError('site source missing')
  for path in sorted(source.rglob('*')):
   if path.is_dir() and not path.is_symlink():continue
   relative=PurePosixPath(path.relative_to(source).as_posix())
   if any(part.startswith('.') for part in relative.parts):raise ValueError('hidden site input refused')
   if path.suffix not in ALLOWED:
    if path==ROOT/'viz/gaussian_walk_demo.py':continue
    if path.suffix=='.py':continue
    raise ValueError(f'unsupported site input: {path.relative_to(ROOT)}')
   data=regular(path);total+=len(data);outputs[str(prefix/relative)]=data
 if len(outputs)>256 or total>128*1024*1024:raise ValueError('site exceeds build bound')
 source=regular(ROOT/'viz/gaussian_walk_demo.py');demo=outputs['demo.html'].decode()
 if demo.count(SOURCE_FETCH)!=1:raise ValueError('demo loader changed')
 module=('// Generated from viz/gaussian_walk_demo.py for static review.\nexport default '
         +json.dumps(source.decode(),ensure_ascii=True)+';\n').encode()
 outputs['demo-source.js']=module
 outputs['demo.html']=demo.replace(SOURCE_FETCH,"import('./demo-source.js').then(module => module.default)").encode()
 fingerprint=hashlib.sha256(b''.join(name.encode()+b'\0'+outputs[name] for name in sorted(outputs))).hexdigest()
 outputs['preview-build.json']=(json.dumps({'version':1,'fingerprint':fingerprint,'files':len(outputs)},sort_keys=True)+'\n').encode()
 OUTPUT.parent.mkdir(parents=True,exist_ok=True)
 if OUTPUT.exists():
  meta=json.loads((OUTPUT/'preview-build.json').read_text())
  if meta.get('fingerprint')==fingerprint:return {'ok':True,'output':str(OUTPUT),'fingerprint':fingerprint,'reused':True}
  retained=ROOT/'build/q5m-site-retained'/meta['fingerprint'];retained.parent.mkdir(parents=True,exist_ok=True)
  if retained.exists():raise ValueError('retained output collision')
  OUTPUT.rename(retained)
 with tempfile.TemporaryDirectory(prefix='.q5m-site-',dir=OUTPUT.parent) as temporary:
  stage=Path(temporary)/'site';stage.mkdir()
  for name,data in outputs.items():
   target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  os.rename(stage,OUTPUT)
 return {'ok':True,'output':str(OUTPUT),'fingerprint':fingerprint,'reused':False}

if __name__=='__main__':print(json.dumps(build(),sort_keys=True))
