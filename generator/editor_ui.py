from __future__ import annotations

EDITOR_UI_VERSION = "1.0"

EDITOR_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FTB Quest Maker</title>
<style>
:root {
  color-scheme: dark;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  --panel: #111827;
  --panel-2: #1f2937;
  --border: #374151;
  --muted: #9ca3af;
  --accent: #60a5fa;
  --accent-2: #a78bfa;
  --danger: #f87171;
}
* { box-sizing: border-box; }
body { margin: 0; background: #070b14; color: #e5e7eb; overflow: hidden; }
button, input, textarea, select { font: inherit; }
button { padding: 8px 12px; border: 1px solid var(--border); border-radius: 7px; cursor: pointer; background: #273449; color: inherit; }
button:hover { border-color: var(--accent); }
button.active { background: #1d4ed8; border-color: #93c5fd; }
header { height: 62px; padding: 10px 16px; background: var(--panel-2); display: flex; gap: 8px; align-items: center; border-bottom: 1px solid var(--border); }
header strong { margin-right: 8px; }
#status { margin-left: auto; color: var(--muted); font-size: .9rem; }
#drop-zone { position: fixed; z-index: 20; inset: 74px 18px auto 18px; border: 2px dashed #4b5563; background: rgba(17,24,39,.94); padding: 14px; text-align: center; border-radius: 10px; color: var(--muted); transition: .15s ease; }
#drop-zone.dragging { border-color: var(--accent); color: #dbeafe; background: rgba(30,64,175,.35); }
#drop-zone[hidden] { display: none; }
main { display: grid; grid-template-columns: 250px minmax(0,1fr) 330px; height: calc(100vh - 62px); }
aside { background: var(--panel); overflow: auto; }
#navigator { border-right: 1px solid var(--border); padding: 14px; }
#inspector { border-left: 1px solid var(--border); padding: 16px; }
#canvas-wrap { position: relative; min-width: 0; overflow: hidden; background: radial-gradient(circle at 1px 1px, #253047 1px, transparent 1px); background-size: 24px 24px; }
#graph { width: 100%; height: 100%; touch-action: none; user-select: none; }
#graph .edge { stroke: #64748b; stroke-width: 2; fill: none; marker-end: url(#arrow); }
#graph .node rect { fill: #1f2937; stroke: #64748b; stroke-width: 2; rx: 9; }
#graph .node text { fill: #e5e7eb; pointer-events: none; font-size: 13px; }
#graph .node .sub { fill: #9ca3af; font-size: 10px; }
#graph .node.selected rect { stroke: var(--accent); stroke-width: 3; }
#graph .node.link-source rect { stroke: var(--accent-2); stroke-dasharray: 6 4; }
#graph .node.review rect { stroke: #f59e0b; }
#graph .chapter-label { fill: #94a3b8; font-size: 14px; font-weight: 700; }
.toolbar { position: absolute; z-index: 4; top: 10px; left: 10px; right: 10px; display: flex; gap: 8px; align-items: center; pointer-events: none; }
.toolbar > * { pointer-events: auto; }
.toolbar input, .toolbar select { background: rgba(17,24,39,.94); color: inherit; border: 1px solid var(--border); border-radius: 6px; padding: 8px; }
.toolbar input { min-width: 220px; }
.toolbar .spacer { flex: 1; }
#zoom-label { color: var(--muted); background: rgba(17,24,39,.8); padding: 6px 8px; border-radius: 6px; }
.chapter { width: 100%; text-align: left; margin: 3px 0; background: transparent; }
.chapter.selected { background: #1e3a5f; }
.quest-list { margin: 8px 0 18px; }
.quest-list button { width: 100%; text-align: left; margin: 3px 0; background: #202b3d; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
label { display: block; margin: 12px 0 5px; color: #cbd5e1; font-size: .88rem; }
input, textarea, select { width: 100%; padding: 8px; background: #0b1220; color: inherit; border: 1px solid #4b5563; border-radius: 6px; }
textarea { min-height: 150px; resize: vertical; }
.meta { color: var(--muted); font-size: .82rem; line-height: 1.5; word-break: break-word; }
#error { white-space: pre-wrap; color: var(--danger); min-height: 36px; }
#empty { color: var(--muted); padding: 24px; text-align: center; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 999px; background: #273449; color: #cbd5e1; font-size: .75rem; margin-right: 4px; }
.import-options { display: flex; gap: 8px; justify-content: center; margin-top: 10px; flex-wrap: wrap; }
.import-options label { margin: 0; display: flex; align-items: center; gap: 5px; }
.import-options input, .import-options select { width: auto; }
@media (max-width: 1050px) { main { grid-template-columns: 210px minmax(0,1fr); } #inspector { position: fixed; right: 0; top: 62px; bottom: 0; width: 330px; z-index: 8; box-shadow: -8px 0 20px #0008; } }
</style>
</head>
<body>
<header>
<strong>FTB Quest Maker</strong>
<button id="import-button">Import modpack</button>
<input id="file-input" type="file" accept=".mrpack,.zip" hidden>
<button onclick="undo()">Undo</button><button onclick="redo()">Redo</button>
<button onclick="saveModel()">Save model</button><button onclick="exportQuestbook()">Export FTB Quests</button>
<span id="status">Loading…</span>
</header>
<div id="drop-zone">
  <strong>Drop a CurseForge ZIP, Modrinth .mrpack, Prism export, or server pack here</strong>
  <div class="import-options">
    <label>Target quests <input id="target-quests" type="number" min="1" placeholder="Auto" size="7"></label>
    <label>Chapter size <input id="chapter-size" type="number" min="1" value="40" size="5"></label>
    <label>Description <select id="description-style"><option>guided</option><option>concise</option><option>detailed</option></select></label>
    <label>Rewards <select id="reward-policy"><option>unassigned</option><option>none</option><option>conservative</option><option>balanced</option><option>generous</option></select></label>
  </div>
</div>
<main>
<aside id="navigator"><h3>Chapters</h3><div id="chapters"></div></aside>
<section id="canvas-wrap">
  <div class="toolbar">
    <input id="search" type="search" placeholder="Search quests…">
    <select id="chapter-filter"><option value="">All chapters</option></select>
    <button id="link-button" title="Choose prerequisite, then dependent quest">Link prerequisite</button>
    <button id="fit-button">Fit graph</button>
    <span class="spacer"></span><span id="zoom-label">100%</span>
  </div>
  <svg id="graph" aria-label="Interactive quest dependency graph">
    <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#64748b"></path></marker></defs>
    <g id="viewport"><g id="edges"></g><g id="nodes"></g></g>
  </svg>
  <div id="empty" hidden>No quests match the current filter.</div>
</section>
<aside id="inspector">
  <h2 id="quest-title">Select a quest</h2>
  <div id="editor" hidden>
    <div id="quest-meta" class="meta"></div>
    <label>Title</label><input id="title">
    <label>Description</label><textarea id="description"></textarea>
    <label><input id="review-required" type="checkbox" style="width:auto"> Requires manual review</label>
    <button onclick="saveQuest()">Apply quest changes</button>
  </div>
  <pre id="error"></pre>
</aside>
</main>
<script>
const api = '/api/v1'; const importEndpoint = '/api/v1/import';
let doc = null, selected = null, selectedChapter = '', linkSource = null;
let zoom = 1, panX = 0, panY = 0, dragging = null, panning = null;
const NODE_W = 180, NODE_H = 72, GRID_X = 210, GRID_Y = 105, CHAPTER_GAP = 170;

async function request(path, options={}) {
  const response = await fetch(api + path, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}
function showError(error) { document.getElementById('error').textContent = error ? String(error) : ''; }
function importOptions() {
  const target = document.getElementById('target-quests').value;
  const params = new URLSearchParams({
    chapter_size: document.getElementById('chapter-size').value || '40',
    description_style: document.getElementById('description-style').value,
    reward_policy: document.getElementById('reward-policy').value,
  });
  if (target) params.set('target_quests', target);
  return params;
}
async function importFile(file) {
  if (!file) return;
  const lower = file.name.toLowerCase();
  if (!lower.endsWith('.zip') && !lower.endsWith('.mrpack')) throw new Error('Choose a .zip or .mrpack modpack export.');
  const drop = document.getElementById('drop-zone');
  drop.hidden = false; drop.classList.add('dragging');
  document.getElementById('status').textContent = `Importing ${file.name}…`;
  const response = await fetch(`${importEndpoint}?${importOptions()}`, {
    method: 'POST',
    headers: {'Content-Type':'application/octet-stream', 'X-File-Name': encodeURIComponent(file.name)},
    body: file,
  });
  const data = await response.json();
  drop.classList.remove('dragging');
  if (!response.ok) throw new Error(data.error || 'Import failed');
  selected = null; selectedChapter = ''; linkSource = null;
  await refresh();
  fitGraph();
  drop.hidden = true;
}
async function refresh() {
  try {
    doc = await request('/document');
    const status = await request('/status');
    renderNavigator(); renderGraph(); renderInspector();
    document.getElementById('status').textContent = `${status.quests} quests · ${status.dependency_edges} links · revision ${status.revision}${status.has_unsaved_changes ? ' · unsaved' : ''}`;
  } catch (error) { showError(error); }
}
function visibleQuests() {
  if (!doc) return [];
  const query = document.getElementById('search').value.trim().toLowerCase();
  const chapter = document.getElementById('chapter-filter').value || selectedChapter;
  return doc.quests.filter(q => (!chapter || q.chapter_id === chapter) && (!query || `${q.title} ${q.description} ${q.objective.id}`.toLowerCase().includes(query)));
}
function renderNavigator() {
  const root = document.getElementById('chapters'); root.innerHTML = '';
  const filter = document.getElementById('chapter-filter'); const old = filter.value; filter.innerHTML = '<option value="">All chapters</option>';
  for (const chapter of doc.chapters) {
    const option = document.createElement('option'); option.value = chapter.id; option.textContent = chapter.title; filter.appendChild(option);
    const chapterButton = document.createElement('button'); chapterButton.className = `chapter${selectedChapter === chapter.id ? ' selected' : ''}`; chapterButton.textContent = chapter.title;
    chapterButton.onclick = () => { selectedChapter = selectedChapter === chapter.id ? '' : chapter.id; filter.value = selectedChapter; renderNavigator(); renderGraph(); };
    root.appendChild(chapterButton);
    const list = document.createElement('div'); list.className = 'quest-list';
    for (const quest of doc.quests.filter(item => item.chapter_id === chapter.id).sort((a,b)=>a.order-b.order)) {
      const button = document.createElement('button'); button.textContent = quest.title; button.onclick = () => selectQuest(quest.id); list.appendChild(button);
    }
    root.appendChild(list);
  }
  filter.value = old || selectedChapter;
}
function graphPoint(quest) {
  const chapterIndex = Math.max(0, doc.chapters.findIndex(c => c.id === quest.chapter_id));
  return {x: 80 + quest.position.x * GRID_X, y: 110 + quest.position.y * GRID_Y + chapterIndex * CHAPTER_GAP};
}
function svg(tag, attrs={}) { const element = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const [key,value] of Object.entries(attrs)) element.setAttribute(key, value); return element; }
function renderGraph() {
  if (!doc) return;
  const quests = visibleQuests(); const visible = new Set(quests.map(q=>q.id));
  const edgeRoot = document.getElementById('edges'); const nodeRoot = document.getElementById('nodes'); edgeRoot.innerHTML = ''; nodeRoot.innerHTML = '';
  for (const edge of doc.edges) {
    if (!visible.has(edge.from) || !visible.has(edge.to)) continue;
    const from = doc.quests.find(q=>q.id===edge.from), to = doc.quests.find(q=>q.id===edge.to); if (!from || !to) continue;
    const a = graphPoint(from), b = graphPoint(to);
    const curve = svg('path', {class:'edge', d:`M ${a.x+NODE_W} ${a.y+NODE_H/2} C ${a.x+NODE_W+70} ${a.y+NODE_H/2}, ${b.x-70} ${b.y+NODE_H/2}, ${b.x} ${b.y+NODE_H/2}`});
    edgeRoot.appendChild(curve);
  }
  const chapterLabels = new Set();
  for (const quest of quests) {
    const point = graphPoint(quest), chapter = doc.chapters.find(c=>c.id===quest.chapter_id);
    if (chapter && !chapterLabels.has(chapter.id)) { const label = svg('text',{class:'chapter-label',x:30,y:point.y-28}); label.textContent=chapter.title; nodeRoot.appendChild(label); chapterLabels.add(chapter.id); }
    const group = svg('g', {class:`node${quest.id===selected?' selected':''}${quest.id===linkSource?' link-source':''}${quest.review_required?' review':''}`, transform:`translate(${point.x},${point.y})`, 'data-id':quest.id, tabindex:'0'});
    group.appendChild(svg('rect',{width:NODE_W,height:NODE_H}));
    const title = svg('text',{x:12,y:25}); title.textContent = quest.title.length > 24 ? quest.title.slice(0,23)+'…' : quest.title; group.appendChild(title);
    const sub = svg('text',{class:'sub',x:12,y:47}); sub.textContent = `${quest.objective.type}: ${quest.objective.id}`.slice(0,34); group.appendChild(sub);
    group.addEventListener('pointerdown', event => startNodeDrag(event, quest));
    group.addEventListener('click', event => { if (!dragging || !dragging.moved) handleNodeClick(quest.id); event.stopPropagation(); });
    nodeRoot.appendChild(group);
  }
  document.getElementById('empty').hidden = quests.length > 0;
  applyViewport();
}
function handleNodeClick(id) {
  if (document.getElementById('link-button').classList.contains('active')) {
    if (!linkSource) { linkSource = id; renderGraph(); return; }
    if (linkSource === id) { linkSource = null; renderGraph(); return; }
    createDependency(linkSource, id); linkSource = null; return;
  }
  selectQuest(id);
}
function startNodeDrag(event, quest) {
  if (event.button !== 0) return;
  const point = graphPoint(quest); dragging = {id:quest.id, startX:event.clientX, startY:event.clientY, x:point.x, y:point.y, moved:false};
  event.currentTarget.setPointerCapture(event.pointerId);
}
function movePointer(event) {
  if (dragging) {
    const dx=(event.clientX-dragging.startX)/zoom, dy=(event.clientY-dragging.startY)/zoom; dragging.moved = Math.abs(dx)+Math.abs(dy)>4;
    const node=document.querySelector(`.node[data-id="${CSS.escape(dragging.id)}"]`); if(node) node.setAttribute('transform',`translate(${dragging.x+dx},${dragging.y+dy})`);
  } else if (panning) { panX += event.clientX-panning.x; panY += event.clientY-panning.y; panning={x:event.clientX,y:event.clientY}; applyViewport(); }
}
async function endPointer(event) {
  if (dragging) {
    const state=dragging; dragging=null; if (!state.moved) return;
    const quest=doc.quests.find(q=>q.id===state.id); const chapterIndex=Math.max(0,doc.chapters.findIndex(c=>c.id===quest.chapter_id));
    const x=Math.round(((state.x+(event.clientX-state.startX)/zoom)-80)/GRID_X);
    const y=Math.round(((state.y+(event.clientY-state.startY)/zoom)-110-chapterIndex*CHAPTER_GAP)/GRID_Y);
    try { await request('/operations',{method:'POST',body:JSON.stringify({action:'move_quest',target_id:quest.id,values:{chapter_id:quest.chapter_id,order:quest.order,x,y}})}); showError(); await refresh(); } catch(error){showError(error); await refresh();}
  }
  panning=null;
}
function applyViewport(){ document.getElementById('viewport').setAttribute('transform',`translate(${panX},${panY}) scale(${zoom})`); document.getElementById('zoom-label').textContent=`${Math.round(zoom*100)}%`; }
function fitGraph(){ zoom=1; panX=0; panY=0; applyViewport(); }
function selectQuest(id) { selected=id; renderGraph(); renderInspector(); }
function renderInspector() {
  const quest = doc && doc.quests.find(item=>item.id===selected); const editor=document.getElementById('editor');
  if(!quest){editor.hidden=true;document.getElementById('quest-title').textContent='Select a quest';return;}
  editor.hidden=false; document.getElementById('quest-title').textContent=quest.title; document.getElementById('title').value=quest.title; document.getElementById('description').value=quest.description; document.getElementById('review-required').checked=quest.review_required;
  document.getElementById('quest-meta').textContent=`${quest.objective.type} · ${quest.reward_decision}\n${quest.objective.id}\nPosition ${quest.position.x}, ${quest.position.y}`;
}
async function saveQuest(){try{await request('/operations',{method:'POST',body:JSON.stringify({action:'update_quest',target_id:selected,values:{title:document.getElementById('title').value,description:document.getElementById('description').value,review_required:document.getElementById('review-required').checked}})});showError();await refresh();}catch(error){showError(error);}}
async function createDependency(prerequisite, dependent){try{await request('/operations',{method:'POST',body:JSON.stringify({action:'set_dependency',target_id:dependent,values:{prerequisite_id:prerequisite,enabled:true}})});showError();await refresh();}catch(error){showError(error);}}
async function undo(){try{await request('/undo',{method:'POST',body:'{}'});showError();await refresh();}catch(error){showError(error);}}
async function redo(){try{await request('/redo',{method:'POST',body:'{}'});showError();await refresh();}catch(error){showError(error);}}
async function saveModel(){try{await request('/save',{method:'POST',body:JSON.stringify({path:'quest-editor-model.json'})});showError();await refresh();}catch(error){showError(error);}}
async function exportQuestbook(){try{const result=await request('/export',{method:'POST',body:JSON.stringify({destination:'generated/ftbquests'})});showError(`Exported ${result.summary.quests} quests to ${result.destination}`);}catch(error){showError(error);}}

const graph=document.getElementById('graph');
graph.addEventListener('pointermove', movePointer); graph.addEventListener('pointerup', endPointer); graph.addEventListener('pointercancel', endPointer);
graph.addEventListener('pointerdown', event=>{if(event.target===graph || event.target.id==='viewport'){panning={x:event.clientX,y:event.clientY};}});
graph.addEventListener('wheel', event=>{event.preventDefault();zoom=Math.max(.35,Math.min(2.5,zoom*(event.deltaY<0?1.1:.9)));applyViewport();},{passive:false});
document.getElementById('search').addEventListener('input',renderGraph); document.getElementById('chapter-filter').addEventListener('change',event=>{selectedChapter=event.target.value;renderGraph();});
document.getElementById('fit-button').onclick=fitGraph;
document.getElementById('link-button').onclick=event=>{event.currentTarget.classList.toggle('active');linkSource=null;renderGraph();};
document.getElementById('import-button').onclick=()=>document.getElementById('file-input').click();
document.getElementById('file-input').addEventListener('change',event=>importFile(event.target.files[0]).catch(showError));
const drop=document.getElementById('drop-zone');
for(const name of ['dragenter','dragover']) drop.addEventListener(name,event=>{event.preventDefault();drop.classList.add('dragging');});
for(const name of ['dragleave','drop']) drop.addEventListener(name,event=>{event.preventDefault();drop.classList.remove('dragging');});
drop.addEventListener('drop',event=>importFile(event.dataTransfer.files[0]).catch(showError));
refresh().then(()=>{if(doc && doc.quests.length) drop.hidden=true;fitGraph();});
</script>
</body></html>'''
