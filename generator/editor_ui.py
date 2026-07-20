from __future__ import annotations

EDITOR_UI_VERSION = "1.2"

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
#job-panel { display: flex; align-items: center; gap: 7px; min-width: 260px; }
#job-panel[hidden] { display: none; }
#job-panel progress { width: 120px; accent-color: var(--accent); }
#job-message { max-width: 210px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #cbd5e1; font-size: .82rem; }
#job-cancel { padding: 5px 8px; }
#drop-zone { position: fixed; z-index: 20; inset: 74px 18px auto 18px; border: 2px dashed #4b5563; background: rgba(17,24,39,.94); padding: 14px; text-align: center; border-radius: 10px; color: var(--muted); transition: .15s ease; }
#drop-zone.dragging { border-color: var(--accent); color: #dbeafe; background: rgba(30,64,175,.35); }
#drop-zone[hidden] { display: none; }
#analysis-panel{position:fixed;z-index:30;inset:78px 8vw 6vh;background:#0f172a;border:1px solid var(--border);border-radius:14px;padding:22px;overflow:auto;box-shadow:0 20px 60px #000b}#analysis-panel[hidden]{display:none}.analysis-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.analysis-card{background:#111827;border:1px solid #334155;border-radius:10px;padding:14px}.analysis-card h3{margin-top:0}.analysis-list{max-height:220px;overflow:auto}.analysis-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:18px}.category-bar{display:flex;justify-content:space-between;border-bottom:1px solid #263244;padding:5px 0}
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
#graph .node.multi-selected rect { stroke: #34d399; stroke-width: 3; }
#graph .node.link-source rect { stroke: var(--accent-2); stroke-dasharray: 6 4; }
#graph .node.review rect { stroke: #f59e0b; }
#graph .chapter-label { fill: #94a3b8; font-size: 14px; font-weight: 700; }
.toolbar { position: absolute; z-index: 4; top: 10px; left: 10px; right: 10px; display: flex; gap: 8px; align-items: center; pointer-events: none; }
.toolbar > * { pointer-events: auto; }
.toolbar input, .toolbar select { background: rgba(17,24,39,.94); color: inherit; border: 1px solid var(--border); border-radius: 6px; padding: 8px; }
.toolbar input { min-width: 220px; }
.toolbar .spacer { flex: 1; }
#zoom-label, #selection-label { color: var(--muted); background: rgba(17,24,39,.8); padding: 6px 8px; border-radius: 6px; }
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
.reward-row{display:grid;grid-template-columns:90px minmax(120px,1fr) 70px minmax(120px,1fr) auto;gap:6px;margin:6px 0}.reward-row input,.reward-row select{min-width:0}</style>
</head>
<body>
<header>
<strong>FTB Quest Maker</strong>
<button id="import-button">Import modpack</button>
<input id="file-input" type="file" accept=".mrpack,.zip,.ftbqproj" hidden>
<button onclick="undo()">Undo</button><button onclick="redo()">Redo</button>
<button id="snapshot-button" onclick="createSnapshot()">Snapshot</button><button id="recover-button" onclick="recoverLatest()">Recover latest</button>
<button onclick="saveModel()">Save model</button><button id="bundle-button" onclick="saveBundle()">Save project bundle</button><button id="install-button" onclick="installQuestbook()">Install to instance</button><button onclick="exportQuestbook()">Export FTB Quests</button>
<span id="status">Loading…</span>
<div id="job-panel" hidden><progress id="job-progress" max="100" value="0"></progress><span id="job-message"></span><button id="job-cancel">Cancel</button></div>
</header>
<div id="drop-zone">
  <strong>Drop a modpack archive or portable .ftbqproj project here</strong>
  <div class="import-options">
    <label>Target quests <input id="target-quests" type="number" min="1" placeholder="Auto" size="7"></label>
    <label>Chapter size <input id="chapter-size" type="number" min="1" value="40" size="5"></label>
    <label>Description <select id="description-style"><option>guided</option><option>concise</option><option>detailed</option></select></label>
    <label>Rewards <select id="reward-policy"><option>unassigned</option><option>none</option><option>conservative</option><option>balanced</option><option>generous</option></select></label>
  </div>
</div>
<section id="analysis-panel" hidden>
  <h2>Modpack analysis</h2><p id="analysis-summary" class="meta"></p>
  <div class="analysis-grid">
    <div class="analysis-card"><h3>Pack</h3><div id="analysis-pack"></div></div>
    <div class="analysis-card"><h3>Gameplay mix</h3><div id="analysis-categories"></div></div>
    <div class="analysis-card"><h3>Major content mods</h3><div id="analysis-mods" class="analysis-list"></div></div>
    <div class="analysis-card"><h3>Generation plan</h3><label>Quest density<select id="analysis-density"><option value="compact">Compact</option><option value="standard" selected>Standard</option><option value="large">Large</option><option value="completionist">Completionist</option></select></label><label>Lore style<select id="analysis-lore"><option value="concise">Minimal</option><option value="guided" selected>Guided</option><option value="detailed">Detailed</option></select></label><label>Rewards<select id="analysis-rewards"><option value="unassigned">Decide later</option><option value="conservative">Conservative</option><option value="balanced">Balanced</option><option value="generous">Generous</option></select></label><div id="analysis-estimate" class="meta"></div></div>
  </div>
  <div id="analysis-warnings" class="meta"></div>
  <div class="analysis-actions"><button id="analysis-cancel">Cancel</button><button id="analysis-generate">Generate quest book</button></div>
</section>
<main>
<aside id="navigator"><h3>Chapters</h3><div id="chapters"></div></aside>
<section id="canvas-wrap">
  <div class="toolbar">
    <input id="search" type="search" placeholder="Search quests…">
    <select id="chapter-filter"><option value="">All chapters</option></select>
    <button id="link-button" title="Choose prerequisite, then dependent quest">Link prerequisite</button>
    <button id="auto-layout-button">Auto layout</button>
    <select id="bulk-chapter"><option value="">Move selected…</option></select>
    <button id="bulk-review-button">Flag review</button>
    <button id="bulk-clear-review-button">Clear review</button>
    <button id="fit-button">Fit graph</button>
    <span class="spacer"></span><span id="selection-label">0 selected</span><span id="zoom-label">100%</span>
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
    <label>Reward mode</label><select id="reward-decision"><option value="unassigned">Unassigned</option><option value="none">No reward</option><option value="rewarded">Custom rewards</option></select>
    <label>Rewards</label><div id="reward-list"></div><button id="add-reward" type="button">Add reward</button>
    <div class="meta">Reward types may be item, xp, command, or loot. Item IDs use namespace:path.</div>
    <button onclick="saveQuest()">Apply quest changes</button>
  </div>
  <pre id="error"></pre>
</aside>
</main>
<script>
const api = '/api/v1'; const importEndpoint = '/api/v1/import-job';
let doc = null, selected = null, selectedChapter = '', linkSource = null;
let selectedQuests = new Set();
let activeJob = null; let analyzedPack = null;
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
function sleep(milliseconds) { return new Promise(resolve => setTimeout(resolve, milliseconds)); }
function renderJob(job) {
  const panel = document.getElementById('job-panel');
  panel.hidden = false;
  document.getElementById('job-progress').value = job.progress || 0;
  document.getElementById('job-message').textContent = `${job.stage}: ${job.message}`;
  document.getElementById('job-cancel').disabled = !job.cancellable;
}
async function monitorJob(jobId) {
  activeJob = jobId;
  while (activeJob === jobId) {
    const job = await request(`/jobs/${jobId}`);
    renderJob(job);
    if (job.state === 'completed') {
      activeJob = null;
      document.getElementById('job-panel').hidden = true;
      selected = null; selectedChapter = ''; linkSource = null; selectedQuests.clear();
      await refresh(); fitGraph(); document.getElementById('drop-zone').hidden = true;
      return job;
    }
    if (job.state === 'failed') { activeJob = null; throw new Error(job.error || 'Generation failed'); }
    if (job.state === 'cancelled') { activeJob = null; throw new Error('Generation cancelled'); }
    await sleep(180);
  }
}
async function cancelActiveJob() {
  if (!activeJob) return;
  try { await request(`/jobs/${activeJob}/cancel`, {method:'POST', body:'{}'}); }
  catch (error) { showError(error); }
}
async function importFile(file) {
  if (!file) return;
  const lower = file.name.toLowerCase();
  const isBundle = lower.endsWith('.ftbqproj');
  if (!isBundle && !lower.endsWith('.zip') && !lower.endsWith('.mrpack')) throw new Error('Choose a .zip, .mrpack, or .ftbqproj file.');
  if (activeJob) throw new Error('A modpack generation job is already running.');
  const drop = document.getElementById('drop-zone');
  drop.hidden = false; drop.classList.add('dragging');
  document.getElementById('status').textContent = `Uploading ${file.name}…`;
  const endpoint = isBundle ? `${api}/project-bundle-import` : `${api}/analyze`;
  const response = await fetch(endpoint, {method:'POST',headers:{'Content-Type':'application/octet-stream','X-File-Name':encodeURIComponent(file.name)},body:file});
  const result = await response.json(); drop.classList.remove('dragging');
  if (!response.ok) throw new Error(result.error || 'Import failed'); showError();
  if (isBundle) { selected=null;selectedChapter='';linkSource=null;selectedQuests.clear();await refresh();fitGraph();drop.hidden=true; }
  else { analyzedPack=result; renderAnalysis(result.profile); }
}

function densityTarget(base, density){const factors={compact:.55,standard:1,large:1.35,completionist:1.7};return Math.max(10,Math.round(base*(factors[density]||1)));}
function renderAnalysis(profile){
  const panel=document.getElementById('analysis-panel'); const pack=profile.pack||{}; const summary=profile.summary||{}; const mods=profile.mods||[];
  document.getElementById('analysis-summary').textContent=`${summary.mods||0} mods detected · ${summary.content_mods||0} gameplay/content mods · analyzed without launching Minecraft`;
  document.getElementById('analysis-pack').innerHTML=`<strong>${pack.name||'Unknown modpack'}</strong><p>Minecraft ${pack.minecraft||'unknown'}<br>${pack.loader||'Unknown loader'} ${pack.loader_version||''}</p>`;
  const counts=summary.category_counts||{}; document.getElementById('analysis-categories').innerHTML=Object.entries(counts).filter(([k])=>k!=='library').map(([k,v])=>`<div class="category-bar"><span>${k}</span><strong>${v}</strong></div>`).join('')||'<span class="meta">No gameplay categories detected.</span>';
  document.getElementById('analysis-mods').innerHTML=mods.filter(m=>!m.library).sort((a,b)=>b.quest_weight-a.quest_weight).slice(0,30).map(m=>`<div><strong>${m.display_name}</strong> <span class="badge">${m.category}</span>${m.resolved?'':' <span class="badge">generic</span>'}</div>`).join('');
  document.getElementById('analysis-warnings').textContent=(profile.warnings||[]).map(x=>`Warning: ${x}`).join('\n'); updateAnalysisEstimate(); panel.hidden=false;
}
function updateAnalysisEstimate(){if(!analyzedPack)return;const base=analyzedPack.profile.summary.recommended_quests.target||25;const density=document.getElementById('analysis-density').value;const target=densityTarget(base,density);document.getElementById('analysis-estimate').textContent=`Estimated ${target} quests across about ${Math.max(1,Math.ceil(target/40))} chapters.`;}
async function generateAnalyzedPack(){
  if(!analyzedPack)return; const density=document.getElementById('analysis-density').value; const base=analyzedPack.profile.summary.recommended_quests.target||25; const target=densityTarget(base,density);
  const result=await request('/generate-job',{method:'POST',body:JSON.stringify({path:analyzedPack.path,target_quests:target,chapter_size:40,description_style:document.getElementById('analysis-lore').value,reward_policy:document.getElementById('analysis-rewards').value})});
  document.getElementById('analysis-panel').hidden=true; await monitorJob(result.id); analyzedPack=null;
}

async function refresh() {
  try {
    doc = await request('/document');
    const status = await request('/status');
    renderNavigator(); renderGraph(); renderInspector();
    const recovery = status.recovery || {};
    const autosave = recovery.autosave_available ? ` · autosaved r${recovery.autosave.revision}` : '';
    document.getElementById('status').textContent = `${status.quests} quests · ${status.dependency_edges} links · revision ${status.revision}${status.has_unsaved_changes ? ' · unsaved' : ''}${autosave}`;
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
  const bulkChapter = document.getElementById('bulk-chapter'); const oldBulk = bulkChapter.value; bulkChapter.innerHTML = '<option value="">Move selected…</option>';
  for (const chapter of doc.chapters) {
    const option = document.createElement('option'); option.value = chapter.id; option.textContent = chapter.title; filter.appendChild(option);
    const bulkOption = document.createElement('option'); bulkOption.value = chapter.id; bulkOption.textContent = `Move to ${chapter.title}`; bulkChapter.appendChild(bulkOption);
    const chapterButton = document.createElement('button'); chapterButton.className = `chapter${selectedChapter === chapter.id ? ' selected' : ''}`; chapterButton.textContent = chapter.title;
    chapterButton.onclick = () => { selectedChapter = selectedChapter === chapter.id ? '' : chapter.id; filter.value = selectedChapter; renderNavigator(); renderGraph(); };
    root.appendChild(chapterButton);
    const list = document.createElement('div'); list.className = 'quest-list';
    for (const quest of doc.quests.filter(item => item.chapter_id === chapter.id).sort((a,b)=>a.order-b.order)) {
      const button = document.createElement('button'); button.textContent = quest.title; button.onclick = event => selectQuest(quest.id, event.ctrlKey || event.metaKey || event.shiftKey); list.appendChild(button);
    }
    root.appendChild(list);
  }
  filter.value = old || selectedChapter; bulkChapter.value = oldBulk;
  updateSelectionLabel();
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
    const group = svg('g', {class:`node${quest.id===selected?' selected':''}${selectedQuests.has(quest.id)?' multi-selected':''}${quest.id===linkSource?' link-source':''}${quest.review_required?' review':''}`, transform:`translate(${point.x},${point.y})`, 'data-id':quest.id, tabindex:'0'});
    group.appendChild(svg('rect',{width:NODE_W,height:NODE_H}));
    const title = svg('text',{x:12,y:25}); title.textContent = quest.title.length > 24 ? quest.title.slice(0,23)+'…' : quest.title; group.appendChild(title);
    const sub = svg('text',{class:'sub',x:12,y:47}); sub.textContent = `${quest.objective.type}: ${quest.objective.id}`.slice(0,34); group.appendChild(sub);
    group.addEventListener('pointerdown', event => startNodeDrag(event, quest));
    group.addEventListener('click', event => { if (!dragging || !dragging.moved) handleNodeClick(quest.id, event); event.stopPropagation(); });
    nodeRoot.appendChild(group);
  }
  document.getElementById('empty').hidden = quests.length > 0;
  applyViewport();
}
function handleNodeClick(id, event) {
  if (document.getElementById('link-button').classList.contains('active')) {
    if (!linkSource) { linkSource = id; renderGraph(); return; }
    if (linkSource === id) { linkSource = null; renderGraph(); return; }
    createDependency(linkSource, id); linkSource = null; return;
  }
  selectQuest(id, event.ctrlKey || event.metaKey || event.shiftKey);
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
function updateSelectionLabel(){ document.getElementById('selection-label').textContent=`${selectedQuests.size} selected`; }
function selectQuest(id, additive=false) {
  if (additive) {
    if (selectedQuests.has(id)) selectedQuests.delete(id); else selectedQuests.add(id);
  } else {
    selectedQuests.clear(); selectedQuests.add(id);
  }
  selected=id; updateSelectionLabel(); renderGraph(); renderInspector();
}
function selectedQuestIds(){ return [...selectedQuests].filter(id=>doc && doc.quests.some(q=>q.id===id)).sort(); }
async function runBatch(operations){
  if(!operations.length) throw new Error('Select at least one quest.');
  const result=await request('/batch-operations',{method:'POST',body:JSON.stringify({operations})});
  await refresh(); return result;
}
async function setSelectedReview(value){
  try { const operations=selectedQuestIds().map(id=>({action:'update_quest',target_id:id,values:{review_required:value}})); await runBatch(operations); showError(); } catch(error){showError(error);}
}
async function moveSelectedToChapter(chapterId){
  if(!chapterId) return;
  try {
    const ids=selectedQuestIds(); if(!ids.length) throw new Error('Select at least one quest.');
    const existing=doc.quests.filter(q=>q.chapter_id===chapterId && !selectedQuests.has(q.id));
    let nextOrder=existing.reduce((value,q)=>Math.max(value,q.order+1),0);
    const operations=ids.map((id,index)=>{const q=doc.quests.find(item=>item.id===id);return {action:'move_quest',target_id:id,values:{chapter_id:chapterId,order:nextOrder+index,x:q.position.x,y:q.position.y}};});
    await runBatch(operations); document.getElementById('bulk-chapter').value=''; showError();
  } catch(error){showError(error);}
}
async function autoLayout(){
  try { await request('/auto-layout',{method:'POST',body:JSON.stringify({chapter_id:selectedChapter||null})}); showError(); await refresh(); fitGraph(); } catch(error){showError(error);}
}
function rewardRow(reward={type:'item',id:'',count:1,reason:''}) {
  const row=document.createElement('div'); row.className='reward-row';
  row.innerHTML='<select class="reward-type"><option>item</option><option>xp</option><option>command</option><option>loot</option></select><input class="reward-id" placeholder="minecraft:diamond"><input class="reward-count" type="number" min="1" value="1"><input class="reward-reason" placeholder="Why this reward?"><button type="button" class="reward-remove">Remove</button>';
  row.querySelector('.reward-type').value=reward.type||'item'; row.querySelector('.reward-id').value=reward.id||''; row.querySelector('.reward-count').value=reward.count||1; row.querySelector('.reward-reason').value=reward.reason||'';
  row.querySelector('.reward-remove').onclick=()=>row.remove(); return row;
}
function addReward(reward){document.getElementById('reward-list').appendChild(rewardRow(reward));}
function readRewards(){return [...document.querySelectorAll('.reward-row')].map(row=>({type:row.querySelector('.reward-type').value,id:row.querySelector('.reward-id').value.trim(),count:Number(row.querySelector('.reward-count').value||1),reason:row.querySelector('.reward-reason').value.trim()})).filter(item=>item.id);}
function renderInspector() {
  const quest = doc && doc.quests.find(item=>item.id===selected); const editor=document.getElementById('editor');
  if(!quest){editor.hidden=true;document.getElementById('quest-title').textContent='Select a quest';return;}
  editor.hidden=false; document.getElementById('quest-title').textContent=quest.title; document.getElementById('title').value=quest.title; document.getElementById('description').value=quest.description; document.getElementById('review-required').checked=quest.review_required;
  document.getElementById('reward-decision').value=quest.reward_decision||'unassigned'; const list=document.getElementById('reward-list'); list.innerHTML=''; (quest.rewards||[]).forEach(addReward);
  document.getElementById('quest-meta').textContent=`${quest.objective.type} · ${quest.reward_decision}
${quest.objective.id}
Position ${quest.position.x}, ${quest.position.y}`;
}
async function saveQuest(){try{const rewardDecision=document.getElementById('reward-decision').value;const rewards=rewardDecision==='rewarded'?readRewards():[];await request('/operations',{method:'POST',body:JSON.stringify({action:'update_quest',target_id:selected,values:{title:document.getElementById('title').value,description:document.getElementById('description').value,review_required:document.getElementById('review-required').checked,reward_decision:rewardDecision,rewards}})});showError();await refresh();}catch(error){showError(error);}}
async function createDependency(prerequisite, dependent){try{await request('/operations',{method:'POST',body:JSON.stringify({action:'set_dependency',target_id:dependent,values:{prerequisite_id:prerequisite,enabled:true}})});showError();await refresh();}catch(error){showError(error);}}
async function undo(){try{await request('/undo',{method:'POST',body:'{}'});showError();await refresh();}catch(error){showError(error);}}
async function redo(){try{await request('/redo',{method:'POST',body:'{}'});showError();await refresh();}catch(error){showError(error);}}
async function createSnapshot(){try{const result=await request('/snapshot',{method:'POST',body:JSON.stringify({reason:'manual browser checkpoint'})});showError(`Snapshot saved: ${result.snapshot.path}`);await refresh();}catch(error){showError(error);}}
async function recoverLatest(){try{const recovery=await request('/recovery');if(!recovery.autosave_available)throw new Error('No autosave recovery document is available.');if(!confirm(`Restore autosave revision ${recovery.autosave.revision}? Current unsaved state will be checkpointed first.`))return;await request('/recover',{method:'POST',body:'{}'});showError('Recovered latest autosave.');selected=null;selectedQuests.clear();await refresh();fitGraph();}catch(error){showError(error);}}
async function saveModel(){try{await request('/save',{method:'POST',body:JSON.stringify({path:'quest-editor-model.json'})});showError();await refresh();}catch(error){showError(error);}}
async function saveBundle(){try{const result=await request('/bundle',{method:'POST',body:JSON.stringify({destination:'project.ftbqproj'})});showError(`Saved portable project bundle to ${result.destination}`);}catch(error){showError(error);}}
async function installQuestbook(){
  try {
    const discovery = await request('/instances');
    const instances = discovery.instances || [];
    if (!instances.length) throw new Error('No supported Minecraft instances were discovered. Use the desktop launcher to add a custom instance folder.');
    const choices = instances.map((item,index)=>`${index+1}. ${item.name} [${item.launcher}] · ${item.minecraft_version||'unknown'} · ${item.game_directory}`).join('\n');
    const selected = window.prompt(`Choose the discovered instance number:\n\n${choices}`, '1');
    if (!selected) return;
    const index = Number(selected) - 1;
    if (!Number.isInteger(index) || !instances[index]) throw new Error('Choose a valid instance number.');
    const result=await request('/install',{method:'POST',body:JSON.stringify({instance:instances[index].game_directory,backup:true})});
    showError(`Installed ${result.installed_files} files to ${result.destination}${result.backup ? ` · backup: ${result.backup}` : ''}`);
  } catch(error){showError(error);}
}
async function exportQuestbook(){try{const result=await request('/export',{method:'POST',body:JSON.stringify({destination:'generated/ftbquests'})});showError(`Exported ${result.summary.quests} quests to ${result.destination}`);}catch(error){showError(error);}}

const graph=document.getElementById('graph');
graph.addEventListener('pointermove', movePointer); graph.addEventListener('pointerup', endPointer); graph.addEventListener('pointercancel', endPointer);
graph.addEventListener('pointerdown', event=>{if(event.target===graph || event.target.id==='viewport'){panning={x:event.clientX,y:event.clientY};}});
graph.addEventListener('wheel', event=>{event.preventDefault();zoom=Math.max(.35,Math.min(2.5,zoom*(event.deltaY<0?1.1:.9)));applyViewport();},{passive:false});
document.getElementById('search').addEventListener('input',renderGraph); document.getElementById('chapter-filter').addEventListener('change',event=>{selectedChapter=event.target.value;renderGraph();});
document.getElementById('fit-button').onclick=fitGraph;
document.getElementById('auto-layout-button').onclick=autoLayout;
document.getElementById('bulk-review-button').onclick=()=>setSelectedReview(true);
document.getElementById('bulk-clear-review-button').onclick=()=>setSelectedReview(false);
document.getElementById('bulk-chapter').addEventListener('change',event=>moveSelectedToChapter(event.target.value));
document.getElementById('link-button').onclick=event=>{event.currentTarget.classList.toggle('active');linkSource=null;renderGraph();};
document.getElementById('import-button').onclick=()=>document.getElementById('file-input').click();
document.getElementById('job-cancel').onclick=cancelActiveJob;
document.getElementById('add-reward').onclick=()=>addReward();
document.getElementById('analysis-density').addEventListener('change',updateAnalysisEstimate);
document.getElementById('analysis-cancel').onclick=()=>{document.getElementById('analysis-panel').hidden=true;analyzedPack=null;};
document.getElementById('analysis-generate').onclick=()=>generateAnalyzedPack().catch(showError);
document.getElementById('file-input').addEventListener('change',event=>importFile(event.target.files[0]).catch(showError));
const drop=document.getElementById('drop-zone');
for(const name of ['dragenter','dragover']) drop.addEventListener(name,event=>{event.preventDefault();drop.classList.add('dragging');});
for(const name of ['dragleave','drop']) drop.addEventListener(name,event=>{event.preventDefault();drop.classList.remove('dragging');});
drop.addEventListener('drop',event=>importFile(event.dataTransfer.files[0]).catch(showError));
refresh().then(()=>{if(doc && doc.quests.length) drop.hidden=true;fitGraph();});
</script>
</body></html>'''
