"""Update preserved review.html from the actual manufactured meshes."""
from pathlib import Path
import json,base64
root=Path(__file__).resolve().parent
meshdata=(root/'assembly-meshes.json').read_text()
art=base64.b64encode((root.parent/'docs/screen.png').read_bytes()).decode()
html='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fridge case review</title><style>
body{font-family:var(--font-sans,system-ui);color:var(--foreground,#ddd)}p{font-size:14px;line-height:1.5}button{background:var(--secondary,#333);color:var(--foreground,#ddd);border:1px solid var(--border,#777);border-radius:6px;padding:8px;margin:3px}label{display:inline-block;margin:7px;font-size:13px}input{accent-color:#888;vertical-align:middle}canvas{display:block;width:100%;height:460px;touch-action:none}.note{color:var(--muted-foreground,#aaa)}#error{color:var(--destructive,#b44)}
</style></head><body><p><b>Print model 04</b> · 126 × 82 × 36 mm · Three printed parts · No external openings</p><div><button onclick="preset('front')">Front</button><button onclick="preset('back')">Inside / back</button><button onclick="preset('side')">Side</button><button onclick="preset('iso')">3D</button></div><label>Separate cover <input id="explode" type="range" min="0" max="45" value="20" oninput="draw()"></label><label><input id="cover" type="checkbox" onchange="draw()">Back</label><label><input id="shell" type="checkbox" checked onchange="draw()">Shell</label><label><input id="carrier" type="checkbox" checked onchange="draw()">Carrier</label><label><input id="electronics" type="checkbox" checked onchange="draw()">Electronics + straps</label><canvas id="c" aria-label="Rotatable actual enclosure meshes with reference electronics"></canvas><p id="error"></p><p>Drag to rotate. White: front shell · Light gray: carrier and back · Dark gray: board/XIAO · Gray: battery · Black: straps, antenna and magnets.</p><p class="note">Shell, carrier and back are the actual exported mesh geometry. Electronics and straps are reference shapes. Straps thread through paired slots and fasten onto themselves. Removing the back leaves the strapped electronics on the carrier. First physical fit and library slicing remain to be checked.</p><script>
const data=__MESHES__;
const canvas=document.getElementById('c'),gl=canvas.getContext('webgl',{antialias:true,alpha:true});
let az=Math.PI,el=0,pointer=null,queued=false;
function draw(){if(!queued){queued=true;requestAnimationFrame(()=>{queued=false;render()})}}
function preset(p){[az,el]=p==='front'?[Math.PI,0]:p==='back'?[0,0]:p==='side'?[Math.PI/2,0]:[2.7,.3];if(p==='back')document.getElementById('cover').checked=false;draw()}
if(!gl){document.getElementById('error').textContent='This viewer needs WebGL. Open the file in a browser with hardware acceleration enabled.'}
const vertex=`attribute vec3 pos;attribute vec3 norm;attribute vec2 uv;uniform vec2 angle;uniform vec2 viewport;uniform float scale;uniform float offsetZ;varying vec3 normal;varying vec2 texUV;
vec3 rotate(vec3 p){float a=p.x*cos(angle.x)-p.z*sin(angle.x),b=p.x*sin(angle.x)+p.z*cos(angle.x);return vec3(a,p.y*cos(angle.y)-b*sin(angle.y),p.y*sin(angle.y)+b*cos(angle.y));}
void main(){vec3 q=rotate(pos+vec3(0.,0.,offsetZ)-vec3(63.,41.,22.));gl_Position=vec4(-q.x*scale*2./viewport.x,-q.y*scale*2./viewport.y,-q.z/250.,1.);normal=rotate(norm);texUV=uv;}`;
const fragment=`precision mediump float;uniform float gray;uniform bool textured;uniform sampler2D artwork;varying vec3 normal;varying vec2 texUV;
void main(){if(textured){gl_FragColor=texture2D(artwork,texUV);}else{float shade=.83+.17*max(0.,dot(normalize(normal),normalize(vec3(-.3,-.4,1.))));gl_FragColor=vec4(vec3(gray*shade),1.);}}`;
let program,texture,items=[];
function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
function add(name,vertices,faces,gray,group,textureFlag=false){let a=[];for(let f of faces){let p=f.map(i=>vertices[i]),u=p[1].map((v,i)=>v-p[0][i]),v=p[2].map((v,i)=>v-p[0][i]),n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],l=Math.hypot(...n)||1;n=n.map(v=>v/l);for(let j=0;j<3;j++){let t=textureFlag?[[0,0],[1,0],[1,1],[0,1]][f[j]]:[0,0];a.push(...p[j],...n,...t)}}const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(a),gl.STATIC_DRAW);items.push({name,b,count:a.length/8,gray,group,textured:textureFlag})}
function box(name,x,y,z,w,h,d,g,group='electronics'){let v=[[x,y,z],[x+w,y,z],[x+w,y+h,z],[x,y+h,z],[x,y,z+d],[x+w,y,z+d],[x+w,y+h,z+d],[x,y+h,z+d]],f=[];for(let q of [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]])f.push([q[0],q[1],q[2]],[q[0],q[2],q[3]]);add(name,v,f,g,group)}
function cylinder(name,x,y,z,r,h,g,group){let v=[],f=[],N=48;for(let k=0;k<2;k++)for(let i=0;i<N;i++)v.push([x+r*Math.cos(i*2*Math.PI/N),y+r*Math.sin(i*2*Math.PI/N),z+k*h]);v.push([x,y,z],[x,y,z+h]);for(let i=0;i<N;i++){let j=(i+1)%N;f.push([i,j,j+N],[i,j+N,i+N],[2*N,j,i],[2*N+1,i+N,j+N])}add(name,v,f,g,group)}
if(gl){try{program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);gl.enable(gl.DEPTH_TEST);
for(let part of data){const cfg={'01_front_shell':[.96,'shell'],'02_electronics_carrier':[.78,'carrier'],'03_back':[.9,'cover'],'screen':[.93,'electronics'],'driver_board':[.30,'electronics'],'XIAO':[.5,'electronics'],'USB':[.73,'electronics'],'battery':[.64,'electronics'],'antenna':[.12,'electronics']}[part.name];add(part.name,part.vertices,part.faces,...cfg)}
// Reference screen artwork at actual front surface, centered in aperture.
add('Artwork',[[16.6,13.16,2.39],[109.4,13.16,2.39],[109.4,68.84,2.39],[16.6,68.84,2.39]],[[0,2,1],[0,3,2]],1,'electronics',true);
// Shield/headers and hook-and-loop straps, NOT printed parts.
box('Shield',36,32,26.8,11,15,1,.72);
for(let y of [30.65,46.45])box('Header',33.3,y,14.2,20.9,2,11,.12);
box('Board strap top',39,23.8,27.9,6,32,1.1,.12);
for(let y of [23.8,55])box('Board strap side',39,y,5.7,6,1,22.3,.12);
box('Board strap under',39,23.8,5.7,6,32,1.1,.12);
box('Battery strap top',84,35,19.1,6,40,1.1,.12);
for(let y of [35,74.7])box('Battery strap side',84,y,5.7,6,1,14.5,.12);
box('Battery strap under',84,35,5.7,6,40,1.1,.12);
for(let x of [19,107])for(let y of [17,65])cylinder('Magnet',x,y,35.4,9.017,3.048,.25,'cover');
for(let x of [6,120])for(let y of [6,76])cylinder('Screw head',x,y,34.5,2.8,2.4,.45,'cover');
texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([255,255,255,255]));gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
const image=new Image();image.onload=()=>{gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);draw()};image.src='data:image/png;base64,__ART__';
}catch(e){document.getElementById('error').textContent=e.message;console.error(e)}}
function render(){if(!gl||!program)return;const width=canvas.clientWidth,height=460,dpr=window.devicePixelRatio||1;canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(program);gl.uniform2f(gl.getUniformLocation(program,'angle'),az,el);gl.uniform2f(gl.getUniformLocation(program,'viewport'),width,height);gl.uniform1f(gl.getUniformLocation(program,'scale'),Math.min(width/155,4.2));gl.uniform1i(gl.getUniformLocation(program,'artwork'),0);gl.bindTexture(gl.TEXTURE_2D,texture);
for(const i of items){if(!document.getElementById(i.group).checked)continue;gl.uniform1f(gl.getUniformLocation(program,'offsetZ'),i.group==='cover'?+document.getElementById('explode').value:0);gl.uniform1f(gl.getUniformLocation(program,'gray'),i.gray);gl.uniform1i(gl.getUniformLocation(program,'textured'),i.textured);gl.bindBuffer(gl.ARRAY_BUFFER,i.b);for(let [name,size,offset] of [['pos',3,0],['norm',3,12],['uv',2,24]]){let l=gl.getAttribLocation(program,name);gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,size,gl.FLOAT,false,32,offset)}gl.drawArrays(gl.TRIANGLES,0,i.count)}
}
canvas.onpointerdown=e=>{pointer=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!pointer)return;az+=(e.clientX-pointer[0])*.01;el+=(e.clientY-pointer[1])*.01;pointer=[e.clientX,e.clientY];draw()};canvas.onpointerup=canvas.onpointercancel=()=>pointer=null;window.onresize=draw;draw();
</script></body></html>'''
(root/'review.html').write_text(html.replace('__MESHES__',meshdata).replace('__ART__',art))
print('Updated review.html with exact printable meshes')
