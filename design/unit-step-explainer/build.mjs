// Make an offline single-file version. No bundler, server, or network involved.
import {readFile,writeFile,rename,mkdir} from 'node:fs/promises';
const here=new URL('./',import.meta.url);
const html=await readFile(new URL('index.html',here),'utf8');
const model=(await readFile(new URL('model.mjs',here),'utf8')).replace(/^export /gm,'');
const app=(await readFile(new URL('app.mjs',here),'utf8')).replace(/^import .*?;\n/,'');
const marker='<script type="module" src="app.mjs"></script>';
if(html.split(marker).length!==2 || /<\/script/i.test(model+app))throw Error('Unexpected bundle inputs');
const result=html.replace(marker,`<script type="module">\n${model}\n${app}\n</script>`);
const output=new URL('standalone.html',here),temp=new URL('standalone.html.tmp',here);
await writeFile(temp,result);await rename(temp,output);
const publicRoot=new URL('public/',here);
await mkdir(publicRoot,{recursive:true});
const publicTemp=new URL('index.html.tmp',publicRoot);
await writeFile(publicTemp,result);await rename(publicTemp,new URL('index.html',publicRoot));
console.log('Built offline standalone.html and managed LAN public/index.html (build only; no server started)');
