// Flow beach atmosphere. Settings match the approved standalone preview.
'use strict';
(async()=>{
const canvas=document.getElementById('sand-atmosphere'),video=document.getElementById('sand-beach-video');
const toggle=document.getElementById('atmosphere-toggle');
const settings=Object.freeze({letterSize:4,brightness:1.2,threshold:.42,glow:1.5,waveSpeed:.55});
const controls={size:{value:settings.letterSize},light:{value:settings.brightness},threshold:{value:settings.threshold},glow:{value:settings.glow},speed:{value:settings.waveSpeed}};
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
// Multiply the scene's own colored light near the pointer; no overlay is added.
const finePointer=matchMedia('(pointer:fine)');
let pointerX=-1,pointerY=-1,pointerActive=0;
function hidePointerGlow(){pointerActive=0;}
addEventListener('pointermove',event=>{
  if(reduced.matches||!finePointer.matches||event.pointerType==='touch')return;
  pointerX=event.clientX/innerWidth;pointerY=event.clientY/innerHeight;pointerActive=1;
},{passive:true});
document.documentElement.addEventListener('pointerleave',hidePointerGlow);
addEventListener('blur',hidePointerGlow);reduced.addEventListener('change',hidePointerGlow);
const paletteKey='sandtris-palette-time';
let savedPaletteTime=0;
try{savedPaletteTime=Number(sessionStorage.getItem(paletteKey))||0;}catch(_){}
let playing=!reduced.matches,ready=false,text='',cols=1,rows=1,frame=0,last=0,paletteTime=savedPaletteTime,paletteLast=0;
const gl=canvas.getContext('webgl',{alpha:false,antialias:false,preserveDrawingBuffer:false});
function fail(message){console.warn('Beach background:',message);canvas.hidden=true;if(toggle){toggle.disabled=true;toggle.textContent='Background unavailable';}}
if(!gl){fail('Text rendering is unavailable in this browser.');return;}
const vs=`attribute vec2 position;varying vec2 uv;void main(){uv=vec2((position.x+1.)*.5,(1.-position.y)*.5);gl_Position=vec4(position,0.,1.);}`;
const fs=`precision highp float;
varying vec2 uv;uniform sampler2D scene;uniform sampler2D letters;uniform sampler2D glowLetters;uniform vec2 grid;uniform vec2 viewport;uniform vec2 videoSize;uniform float brightness;uniform float glow;uniform float threshold;uniform float sceneTarget;uniform vec3 colorA;uniform vec3 colorB;uniform vec2 pointer;uniform float pointerActive;
vec2 sourceUV(vec2 p){
// Match object-fit: cover, keeping the supplied landscape video undistorted.
float va=viewport.x/viewport.y;float sa=videoSize.x/videoSize.y;
vec2 scale=va>sa?vec2(1.,sa/va):vec2(va/sa,1.);
if(sceneTarget>0.){
  // Place the moon and its reflection in the clear space beside the right board.
  // Crop only as much as needed to keep the entire viewport inside the video.
  float moonX=.61;
  float available=min(moonX/sceneTarget,(1.-moonX)/(1.-sceneTarget));
  scale/=max(1.,scale.x/available);
  return vec2(moonX+(p.x-sceneTarget)*scale.x,.23+(p.y-.23)*scale.y);
}
return (p-.5)*scale+.5;
}
vec3 grade(vec2 p){
vec3 c=texture2D(scene,sourceUV(p)).rgb;
float y=dot(c,vec3(.2126,.7152,.0722));
// Preserve the restored exposure and luminous range; replace only the source hue.
float l=pow(max(y,0.),.9)*brightness*1.3;
vec3 tint=mix(colorA,colorB,smoothstep(threshold-.16,threshold+.16,y));
// Match the source luminance so applying the palette does not flatten its light.
vec3 graded=tint/max(dot(tint,vec3(.2126,.7152,.0722)),.001)*l;
return mix(graded,vec3(l),smoothstep(.35,.85,y)*.42);
}

void main(){
vec2 center=(floor(uv*grid)+.5)/grid;
vec3 c=grade(center);
float ink=texture2D(letters,uv).r;
vec3 color=c*ink;
// A continuously blurred glyph atlas gives soft light without offset letter copies.
vec2 d=vec2(2.5)/viewport;
vec3 halo=vec3(0.);float totalWeight=0.;
for(int x=-1;x<=1;x++){for(int y=-1;y<=1;y++){
vec2 offset=vec2(float(x),float(y));
float weight=exp(-dot(offset,offset)*.5);
vec2 sampleUV=uv+offset*d;
vec2 sampleCenter=(floor(sampleUV*grid)+.5)/grid;
float softStroke=texture2D(glowLetters,sampleUV).r;
vec3 light=max(grade(sampleCenter)-vec3(.43),vec3(0.));
halo+=light*softStroke*weight;totalWeight+=weight;
}}
// Compensate for the letter texture's typical coverage while keeping a smooth fade.
halo*=28./totalWeight;
color+=halo*(glow*.075);
float vignette=1.-.24*pow(length((uv-.5)*vec2(1.,.8)),1.5);
vec2 pointerDistance=(uv-pointer)*viewport;
float localLight=exp(-dot(pointerDistance,pointerDistance)/(2.*95.*95.))*pointerActive;
gl_FragColor=vec4(color*vignette*(1.+localLight*.65),1.);
}`;
function shader(type,source){let s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
try{
const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vs));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);const pos=gl.getAttribLocation(program,'position');gl.enableVertexAttribArray(pos);gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);
const loc=Object.fromEntries(['scene','letters','glowLetters','grid','viewport','videoSize','brightness','glow','threshold','sceneTarget','colorA','colorB','pointer','pointerActive'].map(n=>[n,gl.getUniformLocation(program,n)]));
function texture(unit){gl.activeTexture(gl.TEXTURE0+unit);const t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);return t;}
const scene=texture(0),letters=texture(1),glowLetters=texture(2);gl.uniform1i(loc.scene,0);gl.uniform1i(loc.letters,1);gl.uniform1i(loc.glowLetters,2);
function resize(){const dpr=Math.min(devicePixelRatio||1,1.5);canvas.width=Math.round(innerWidth*dpr);canvas.height=Math.round(innerHeight*dpr);gl.viewport(0,0,canvas.width,canvas.height);
 const fontSize=+controls.size.value;cols=Math.ceil(innerWidth/(fontSize*.6));rows=Math.ceil(innerHeight/(fontSize*1.15));
 const mask=document.createElement('canvas');mask.width=canvas.width;mask.height=canvas.height;const ctx=mask.getContext('2d');ctx.scale(dpr,dpr);ctx.fillStyle='#000';ctx.fillRect(0,0,innerWidth,innerHeight);ctx.fillStyle='#fff';ctx.font=`500 ${fontSize}px Menlo,Consolas,monospace`;ctx.textBaseline='middle';
 // Explicit cells keep every word stable when only the footage changes.
 const cellCount=cols*rows;
 // Explicitly tile from the start until every cell in the canvas has text.
 const sourceText=text.trim()+' ';
 const repeatedText=sourceText.repeat(Math.ceil(cellCount/sourceText.length)).slice(0,cellCount);
 canvas.dataset.textCells=String(cellCount);
 canvas.dataset.textRepeats=String(Math.ceil(cellCount/sourceText.length));
 const ch=innerHeight/rows;
 // Draw complete rows. Hundreds of thousands of individual glyph draws can leave
 // missing raster regions on large/high-density canvases even with a full string.
 for(let row=0;row<rows;row++){
   const line=repeatedText.slice(row*cols,(row+1)*cols);
   const width=ctx.measureText(line).width;
   ctx.save();
   if(width>0)ctx.scale(innerWidth/width,1);
   ctx.fillText(line,0,row*ch+ch*.48);
   ctx.restore();
 }
 gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,letters);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,mask);// Blur the static letter mask once per resize, rather than resampling sharp copies.
 const softMask=document.createElement('canvas');softMask.width=mask.width;softMask.height=mask.height;
 const soft=softMask.getContext('2d');soft.filter=`blur(${Math.max(1.8,fontSize*.28)*dpr}px)`;soft.drawImage(mask,0,0);
 gl.activeTexture(gl.TEXTURE2);gl.bindTexture(gl.TEXTURE_2D,glowLetters);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,softMask);
 gl.uniform2f(loc.grid,cols,rows);gl.uniform2f(loc.viewport,innerWidth,innerHeight);
 // Keep the original centered beach composition consistent on every page.
 const target=-1;
 gl.uniform1f(loc.sceneTarget,target);canvas.dataset.sceneTarget=String(target);
 draw();}
function hsl(h,s,l){h=((h%360)+360)%360/360;const a=s*Math.min(l,1-l);return [0,8,4].map(n=>{const k=(n+h*12)%12;return l-a*Math.max(-1,Math.min(k-3,9-k,1));});}
function palette(){const hue=265+paletteTime*.85;gl.uniform3fv(loc.colorA,hsl(hue,.72,.66));gl.uniform3fv(loc.colorB,hsl(hue+150,.72,.66));const root=document.documentElement;root.style.setProperty('--ai',`hsl(${hue} 72% 77%)`);root.style.setProperty('--you',`hsl(${hue+150} 72% 77%)`);}
function draw(){if(!ready||gl.isContextLost())return;gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,scene);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,video);gl.uniform2f(loc.videoSize,video.videoWidth,video.videoHeight);gl.uniform1f(loc.brightness,+controls.light.value);gl.uniform1f(loc.glow,+controls.glow.value);gl.uniform1f(loc.threshold,+controls.threshold.value);gl.uniform2f(loc.pointer,pointerX,pointerY);gl.uniform1f(loc.pointerActive,pointerActive);palette();gl.drawArrays(gl.TRIANGLES,0,6);canvas.dataset.ready='true';}
function savePalette(){try{sessionStorage.setItem(paletteKey,String(paletteTime));}catch(_){}}
function tick(now){frame=0;if(!playing||document.hidden)return;if(paletteLast)paletteTime+=Math.min((now-paletteLast)/1000,.1);paletteLast=now;if(now-last>1000/24){draw();last=now;}frame=requestAnimationFrame(tick);}
function sync(){
  paletteLast=0;
  if(toggle){toggle.textContent=playing?'Still background':'Animate background';toggle.setAttribute('aria-pressed',String(!playing));}
  cancelAnimationFrame(frame);frame=0;
  if(playing&&!document.hidden){
    video.play().then(()=>{if(!frame)frame=requestAnimationFrame(tick);})
      .catch(()=>{playing=false;video.pause();sync();});
  }else video.pause();
}
text=await fetch('/beach-assets/sandtris-readme.txt').then(r=>{if(!r.ok)throw Error('README text could not load.');return r.text();});
if(!text.trim())throw Error('README text is empty.');
await new Promise((resolve,reject)=>{if(video.error)return reject(Error('Beach footage could not load.'));if(video.readyState>=2)return resolve();video.addEventListener('loadeddata',resolve,{once:true});video.addEventListener('error',()=>reject(Error('Beach footage could not load.')),{once:true});});
ready=true;video.playbackRate=+controls.speed.value;resize();sync();
if(toggle)toggle.addEventListener('click',()=>{playing=!playing;sync();});
addEventListener('resize',resize);addEventListener('pagehide',savePalette);
const canvasResizeObserver=new ResizeObserver(resize);canvasResizeObserver.observe(canvas);video.addEventListener('seeked',draw);document.addEventListener('visibilitychange',sync);reduced.addEventListener('change',e=>{playing=!e.matches;sync();});canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();playing=false;sync();fail('The graphics context stopped. Reload to restore the text rendering.');});
window.sandBeachBackground={settings,get playing(){return playing;},get letters(){return cols*rows;},get hue(){return (265+paletteTime*.85)%360;},draw};
}catch(e){fail(e.message);}
})();
