// ═══════════════════════════════════════════
// XUMOTION — Systems Console Dashboard
// Real-time, event-driven, zero mock data
// ═══════════════════════════════════════════

// --- CONFIG ---
const WS_URL = `ws://${location.hostname}:8081`;
const STATE_INTERVAL = 2000;   // polling state tiap 2 detik
const BUFFER_INTERVAL = 2500;  // agregasi event tiap 2.5 detik
const TYPE_SPEED = 18;         // ms per karakter

// --- GLOBAL STATE ---
let eventBuffer = [];          // buffer untuk event masuk
let typingQueue = [];          // antrian pesan yang akan diketik
let isTyping = false;           // lock agar tidak ada dua typing bersamaan
let previousState = {};

// --- DOM REFS ---
const $crVal         = document.getElementById('cr-val');
const $shVal         = document.getElementById('sh-val');
const $sectorName    = document.getElementById('sector-name');
const $entityName    = document.getElementById('entity-name');
const $integrityPct  = document.querySelector('.integrity-label .pct');
const $integrityBar  = document.getElementById('integrity-bar');
const $targetGold    = document.getElementById('target-gold');
const $targetExp     = document.getElementById('target-exp');
const $statAtk       = document.getElementById('stat-atk');
const $statDps       = document.getElementById('stat-dps');
const $statDef       = document.getElementById('stat-def');
const $statCrit      = document.getElementById('stat-crit');
const $statHp        = document.getElementById('stat-hp');
const $statAgents    = document.getElementById('stat-agents');
const $agentsGrid    = document.getElementById('agents-grid');
const $modulesGrid   = document.getElementById('modules-grid');
const $eventStream   = document.getElementById('event-stream');
const $deployedCount = document.getElementById('deployed-count');
const $ownedModules  = document.getElementById('owned-modules');
const $agentsMiniList= document.getElementById('agents-mini-list');
const $autoBtn       = document.getElementById('auto-btn');
const $expFill       = document.getElementById('exp-fill');
const $expLabel      = document.querySelector('.exp-label strong');
const $rankDisplay   = document.querySelector('.rank-display');
const $milestones    = document.getElementById('milestones');
const $unlockGrid    = document.getElementById('unlock-grid');
const $invList       = document.getElementById('inv-list');

// --- UI UTILS ---
function showToast(text, type = 'info') {
  // Sederhana: tampilkan notifikasi kecil di atas
  const toast = document.createElement('div');
  toast.className = `notification toast-${type}`;
  toast.textContent = text;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// --- TYPING EFFECT ENGINE ---
async function typeText(element, text, speed = TYPE_SPEED) {
  for (const char of text) {
    element.appendChild(document.createTextNode(char));
    await new Promise(r => setTimeout(r, speed + Math.random() * 10));
  }
}

async function processTypingQueue() {
  if (isTyping || typingQueue.length === 0) return;
  isTyping = true;
  
  const message = typingQueue.shift();
  const entryDiv = document.createElement('div');
  entryDiv.className = 'event-card';
  
  // time
  const timeSpan = document.createElement('span');
  timeSpan.className = 'event-time';
  timeSpan.textContent = new Date().toLocaleTimeString();
  entryDiv.appendChild(timeSpan);
  
  // body
  const bodyDiv = document.createElement('div');
  bodyDiv.className = 'event-body';
  entryDiv.appendChild(bodyDiv);
  
  // dot indicator
  const dot = document.createElement('div');
  dot.className = 'event-dot';
  dot.style.background = 'var(--green)';
  entryDiv.appendChild(dot);
  
  // type detail
  const detailDiv = document.createElement('div');
  detailDiv.className = 'event-detail';
  bodyDiv.appendChild(detailDiv);
  
  // insert to feed
  const feed = document.getElementById('event-stream');
  if (feed) {
    feed.insertBefore(entryDiv, feed.firstChild);
    // max 30 entries
    while (feed.children.length > 30) feed.lastChild.remove();
  }
  
  // animate typing
  const cursorSpan = document.createElement('span');
  cursorSpan.className = 'stream-cursor';
  entryDiv.appendChild(cursorSpan);
  
  await typeText(detailDiv, message);
  
  // remove cursor
  if (cursorSpan.parentNode) cursorSpan.remove();
  
  isTyping = false;
  // process next after a short pause
  setTimeout(processTypingQueue, 400);
}

function addToTypingQueue(message) {
  typingQueue.push(message);
  processTypingQueue();
}

// --- WEBSOCKET EVENT HANDLER ---
function connectWebSocket() {
  const ws = new WebSocket(WS_URL);
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      eventBuffer.push(data);
    } catch (e) {
      console.error('WS parse error:', e);
    }
  };
  
  ws.onclose = () => {
    // reconnect after 5 detik
    setTimeout(connectWebSocket, 5000);
  };
  
  ws.onerror = (err) => {
    console.error('WebSocket error:', err);
    ws.close();
  };
}

// Agregasi buffer
function processEventBuffer() {
  if (eventBuffer.length === 0) return;
  
  const aggregated = new Map();
  
  for (const ev of eventBuffer) {
    const key = `${ev.type}|${ev.message}`;
    if (aggregated.has(key)) {
      aggregated.get(key).count++;
    } else {
      aggregated.set(key, { ...ev, count: 1 });
    }
  }
  
  // clear buffer
  eventBuffer = [];
  
  // add to typing queue
  for (const [, aggr] of aggregated) {
    let msg = aggr.message;
    if (aggr.count > 1) {
      msg += ` (x${aggr.count})`;
    }
    addToTypingQueue(msg);
  }
}

// --- DATA FETCHING ---
async function fetchState() {
  try {
    const res = await fetch('/api/state');
    if (!res.ok) throw new Error('Network response was not ok');
    const data = await res.json();
    updateDashboardFromGame(data);
    updateAgentsFromGame(data.player.agents);
    updateModulesFromGame(data.player.inventory || []);
    updateProgressionFromGame(data.player);
    previousState = data.player;
  } catch (e) {
    console.error('fetchState error:', e);
  }
}

// --- UPDATE DASHBOARD UI ---
function updateDashboardFromGame(data) {
  // topbar
  if ($crVal) $crVal.textContent = data.player.gold.toLocaleString();
  if ($shVal) $shVal.textContent = (data.player.core_points || 0).toLocaleString();
  
  // sector
  if ($sectorName) $sectorName.textContent = `SECTOR ${data.stage}`;
  if ($entityName) $entityName.textContent = data.enemy.name;
  
  // integrity
  const hpPct = data.enemy.hp / data.enemy.max_hp * 100;
  if ($integrityPct) $integrityPct.textContent = Math.round(hpPct) + '%';
  if ($integrityBar) $integrityBar.style.width = hpPct + '%';
  
  if ($targetGold) $targetGold.textContent = data.enemy.reward_gold;
  if ($targetExp) $targetExp.textContent = data.enemy.reward_exp;
  
  // stats grid
  if ($statAtk) $statAtk.textContent = data.player.atk;
  if ($statDps) $statDps.textContent = data.player.dps;
  if ($statDef) $statDef.textContent = data.player.defense;
  if ($statCrit) $statCrit.textContent = (data.player.crit_rate * 100).toFixed(1) + '%';
  if ($statHp) $statHp.textContent = `${data.player.hp}/${data.player.max_hp}`;
  if ($statAgents) $statAgents.textContent = `${data.player.agents?.filter(a => a.deployed).length || 0} / ${data.player.max_agent_slots || 0}`;
  
  // auto button state
  if ($autoBtn) {
    if (data.player.auto_enhance) {
      $autoBtn.classList.add('auto-active');
      $autoBtn.textContent = '⟳ AUTO ON';
    } else {
      $autoBtn.classList.remove('auto-active');
      $autoBtn.textContent = '⟳ AUTO';
    }
  }
}

function updateAgentsFromGame(agents) {
  if (!$agentsGrid) return;
  if (!agents || agents.length === 0) {
    $agentsGrid.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted)">No agents deployed.</div>';
    if ($deployedCount) $deployedCount.textContent = '0 DEPLOYED';
    return;
  }
  
  const deployed = agents.filter(a => a.deployed).length;
  const totalSlots = previousState?.max_agent_slots || 2;
  if ($deployedCount) $deployedCount.textContent = `${deployed} / ${totalSlots} DEPLOYED`;
  
  $agentsGrid.innerHTML = agents.map(a => `
    <div class="agent-card ${a.deployed ? 'deployed' : ''}">
      <div class="agent-lvl">LVL ${a.level}</div>
      <div class="agent-avatar">
        🤖
        ${a.deployed ? '<div class="active-badge">ON</div>' : ''}
      </div>
      <div class="agent-name">${a.name}</div>
      <div class="agent-rarity ${a.tier}">${a.tier?.toUpperCase()}</div>
      <div class="agent-stats">
        <span class="agent-stat"><strong>${a.dps}</strong> DPS</span>
      </div>
      <div class="agent-btns">
        <button class="btn ${a.deployed ? 'btn-red' : 'btn-green'} btn-sm" 
                onclick="sendCommand('${a.deployed ? 'undeploy ' + a.id : 'deploy ' + a.id}')">
          ${a.deployed ? 'RECALL' : 'DEPLOY'}
        </button>
        <button class="btn btn-amber btn-sm" onclick="sendCommand('ea ${a.id}')">UP</button>
      </div>
    </div>
  `).join('');
  
  // mini agents list di dashboard
  if ($agentsMiniList && agents.length > 0) {
    $agentsMiniList.innerHTML = agents.filter(a => a.deployed).slice(0, 4).map(a => `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:5px 8px;background:var(--panel2);border:1px solid var(--border);border-radius:6px;">
        <span>🤖 ${a.name}</span>
        <span style="font-family:monospace;font-size:12px;color:var(--green)">DPS ${a.dps}</span>
      </div>
    `).join('') || '<div style="font-size:12px;color:var(--muted)">No active agents</div>';
  }
}

function updateModulesFromGame(inventory) {
  if (!$modulesGrid) return;
  if (!inventory || inventory.length === 0) {
    $modulesGrid.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted)">Module bay empty.</div>';
    if ($ownedModules) $ownedModules.textContent = '0 OWNED';
    return;
  }
  
  if ($ownedModules) $ownedModules.textContent = `${inventory.length} OWNED`;
  
  // filter hanya modul terpasang atau semua? Tampilkan semua.
  $modulesGrid.innerHTML = inventory.map(mod => `
    <div class="module-card ${mod.installed ? 'equipped' : ''}">
      <div class="module-icon">⚙️</div>
      <div class="module-name">${mod.name}</div>
      <div class="module-rarity ${mod.rarity}">${mod.rarity.toUpperCase()}</div>
      <div class="module-stat">
        ${mod.atk_bonus ? `ATK+${mod.atk_bonus} ` : ''}
        ${mod.def_bonus ? `DEF+${mod.def_bonus} ` : ''}
        ${mod.hp_bonus ? `HP+${mod.hp_bonus} ` : ''}
        ${mod.crit_rate_bonus ? `CRIT+${(mod.crit_rate_bonus*100).toFixed(1)}%` : ''}
      </div>
      <div class="module-slot">${mod.slot} SLOT</div>
      <div class="module-btns">
        <button class="btn ${mod.installed ? 'btn-red' : 'btn-blue'} btn-sm" 
                onclick="sendCommand('${mod.installed ? 'uninstall ' + mod.slot : 'install ' + (inventory.indexOf(mod)+1)}')">
          ${mod.installed ? 'REMOVE' : 'INSTALL'}
        </button>
      </div>
    </div>
  `).join('');
}

function updateProgressionFromGame(player) {
  if ($rankDisplay) $rankDisplay.textContent = `RANK ${player.level}`;
  if ($expFill) {
    // perkiraan exp needed (ambil dari constants atau dari API jika ada)
    const expNeed = player.exp + 1; // Fallback, seharusnya dari server
    const pct = Math.min(100, (player.exp / expNeed) * 100);
    $expFill.style.width = pct + '%';
  }
  if ($expLabel) $expLabel.textContent = player.exp.toLocaleString();
}

// --- COMMANDS ---
async function sendCommand(cmd) {
  try {
    const res = await fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: cmd })
    });
    if (!res.ok) throw new Error('Command failed');
    const data = await res.json();
    showToast(data.response || 'Done', 'success');
    // Refresh state immediately
    fetchState();
  } catch (e) {
    console.error('sendCommand error:', e);
    showToast('Command failed. Check console.', 'error');
  }
}

// --- NAVIGATION (preserve existing tab system) ---
function switchPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const page = document.getElementById(`page-${name}`);
  if (page) page.classList.add('active');
  
  document.querySelectorAll('.nav-item, .bnav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll(`[data-page="${name}"]`).forEach(n => n.classList.add('active'));
}

// Attach nav handlers
document.querySelectorAll('.nav-item, .bnav-item').forEach(item => {
  item.addEventListener('click', () => switchPage(item.dataset.page));
});

// Auto-enhance toggle
function toggleAuto() {
  sendCommand('auto');
}

// --- INIT ---
window.addEventListener('load', () => {
  connectWebSocket();
  setInterval(processEventBuffer, BUFFER_INTERVAL);
  setInterval(fetchState, STATE_INTERVAL);
  fetchState(); // initial load
  
  // Handle modals (simplified) – we rely on toasts and direct commands,
  // but keep modal system if needed for complex interactions.
  // For now, we'll intercept clicks on elements with data-command
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-command]');
    if (btn) {
      e.preventDefault();
      sendCommand(btn.dataset.command);
    }
  });
});
