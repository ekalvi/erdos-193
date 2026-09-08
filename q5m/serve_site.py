#!/usr/bin/env python3
"""Serve the full production-shaped Erdős site for LAN development."""
from __future__ import annotations
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote,urlsplit
import mimetypes,os,stat

ROOT=Path(__file__).resolve().parent.parent
ALLOWED={'.html','.js','.css','.svg','.jpg','.png','.webp','.pdf','.txt','.xml','.json'}
class Handler(SimpleHTTPRequestHandler):
 def translate_path(self,path):
  parts=[p for p in unquote(urlsplit(path).path).split('/') if p]
  if any(p in {'.','..'} or p.startswith('.') for p in parts):return str(ROOT/'missing')
  base=ROOT/'results' if parts[:1]==['family'] else ROOT/'viz'
  if parts[:1]==['family']:parts=parts[1:]
  target=base
  for part in parts:
   target/=part
   if target.is_symlink():return str(ROOT/'missing')
  if not parts or target.is_dir():target/= 'index.html'
  if target==ROOT/'viz/gaussian_walk_demo.py':return str(target)
  if target.suffix not in ALLOWED:return str(ROOT/'missing')
  try:
   info=target.lstat()
   if not stat.S_ISREG(info.st_mode) or target.is_symlink():return str(ROOT/'missing')
  except OSError:return str(ROOT/'missing')
  return str(target)
 def list_directory(self,path):self.send_error(404);return None
 def end_headers(self):
  self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
 def log_message(self,format,*args):return

if __name__=='__main__':
 host=os.environ.get('HOST','0.0.0.0');port=int(os.environ.get('PORT','8080'))
 ThreadingHTTPServer((host,port),Handler).serve_forever()
