"""Generate an offline, printable slide deck from reviewed JSON content."""

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "review-materials"
slides = json.loads((ROOT / "slides.json").read_text(encoding="utf-8"))
sections = []
for index, slide in enumerate(slides, 1):
    bullets = "".join(f"<li>{escape(item)}</li>" for item in slide["bullets"])
    sections.append(
        f'<section class="slide" aria-label="Slide {index}">'
        f'<p class="eyebrow">TEAM 9 · FINAL YEAR PROJECT · {index:02d}/{len(slides)}</p>'
        f'<h1>{escape(slide["title"])}</h1><p class="lead">{escape(slide["message"])}</p>'
        f"<ul>{bullets}</ul><aside><b>Speaker notes</b><p>{escape(slide['notes'])}</p></aside>"
        "<footer>0xMemory · Evidence, lifecycle, and current context</footer></section>"
    )
template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>0xMemory — Final Review</title>
<style>
*{box-sizing:border-box}body{margin:0;
background:#09151d;
color:#edf5f5;
font:20px/1.5 system-ui,sans-serif}
.slide{display:none;
min-height:100vh;
padding:6vh 8vw 9vh;
position:relative;
background:radial-gradient(ellipse at top right,#163c44,transparent 65%)}
.slide.active{display:block}.eyebrow{font-size:13px;
letter-spacing:2px;
color:#76d9bd}
h1{font-size:clamp(32px,4.5vw,66px);
line-height:1.1;
max-width:1100px;
margin:3vh 0}
.lead{font-size:clamp(22px,2.4vw,34px);
color:#b3dfd4;
max-width:1050px}
ul{max-width:1050px;
padding-left:24px}li{margin:12px 0}footer{font-size:12px;
color:#8dabae;
margin-top:36px}
aside{display:none;
background:#152c35;
border-left:4px solid #76d9bd;
padding:16px;
font-size:16px}
body.notes aside{display:block}nav{position:fixed;
bottom:14px;
right:20px;
display:flex;
gap:10px}
button{border:1px solid #6aa899;
background:#17332d;
color:white;
padding:10px 18px;
border-radius:6px;
cursor:pointer}
@media print{@page{size:A4 landscape;
margin:10mm}body{background:white;
color:#132b32;
font-size:16px}
.slide,.slide.active{display:block;
min-height:185mm;
height:auto;
padding:6mm;
break-after:page;
background:white}
.slide:last-of-type{break-after:auto}h1{font-size:34px}.lead{font-size:23px;
color:#235d50}.eyebrow{color:#235d50}
aside,body.notes aside,nav{display:none}li{margin:8px 0}footer{color:#555}}
</style>
</head>
<body>CONTENT<nav>
<button id="prev">Previous</button>
<button id="notes">Notes</button>
<button id="next">Next</button>
</nav>
<script>const slides=[...document.querySelectorAll('.slide')];
let current=0;

function show(i){current=Math.max(0,Math.min(slides.length-1,i));
slides.forEach((s,n)=>s.classList.toggle('active',n===current));
location.hash=String(current+1)}
document.querySelector('#prev').onclick=()=>show(current-1);
document.querySelector('#next').onclick=()=>show(current+1);

document.querySelector('#notes').onclick=()=>document.body.classList.toggle('notes');

document.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();
show(current+1)}if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();
show(current-1)}if(e.key.toLowerCase()==='n')document.body.classList.toggle('notes')});

show((Number(location.hash.slice(1))||1)-1);
</script>
</body>
</html>"""
(ROOT / "PRESENTATION.html").write_text(
    template.replace("CONTENT", "\n".join(sections)), encoding="utf-8"
)
print(f"Built {len(slides)} slides: {ROOT / 'PRESENTATION.html'}")
