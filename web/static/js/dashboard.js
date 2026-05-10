// ═══════════════════════════════════════════
// XUMOTION — Idle Agent Dashboard v2
// ═══════════════════════════════════════════

// --- CONFIG ---
const STATE_INTERVAL = 2000;
let currentUser = 0;
let gameState = null;
let mergeSlots = [null, null, null];
let eventQueue = [];

function getUserId() {
  try {
    if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
      return window.Telegram.WebApp.initDataUnsafe.user.id;
    }
  } catch(e) {}
  const params = new URLSearchParams(location.search);
  return parseInt(params.get('user_id')) || 0;
}

// --- DOM REFS ---
const $ = (id) => document.getElementById(id);

// --- API ---
async function fetchState() {
  try {
    const res = await fetch(`/api/v1/state?user_id=${currentUser}`);
    if (!res.ok) throw new Error('Status ' + res.status);
    gameState = await res.json();
    updateAllUI();
  } catch(e) {
    console.error('fetchState:', e);
  }
}

async function sendAction(action, params = {}) {
  try {
    const res = await fetch(`/api/v1/action?user_id=${currentUser}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action, params})
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      if (data.state) { gameState = data.state; updateAllUI(); }
    } else {
      showToast(data.message || 'Failed', 'error');
    }
  } catch(e) {
    console.error('sendAction:', e);
    showToast('Network error', 'error');
  }
}

function showToast(msg, type='') {
  const t = document.createElement('div');
  t.className = 'toast' + (type ? ' toast-'+type : '');
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// --- UPDATE ALL ---
function updateAllUI() {
  const p = gameState?.player;
  const e = gameState?.enemy;
  const s = gameState?.sector;
  if (!p || !e || !s) return;

  // Top bar
  const input = $('input-val'), output = $('output-val'), shards = $('shards-val');
  if (input) input.textContent = (p.input_credits||0).toLocaleString();
  if (output) output.textContent = (p.gold||0).toLocaleString();
  if (shards) shards.textContent = (p.core_points||0).toLocaleString();

  // Pause indicator
  const dot = $('pause-dot'), txt = $('pause-text'), ind = $('pause-indicator');
  if (p.paused) {
    if (dot) dot.textContent = '⏸';
    if (txt) txt.textContent = 'PAUSED';
    if (ind) ind.classList.add('paused');
  } else {
    if (dot) dot.textContent = '●';
    if (txt) txt.textContent = 'LIVE';
    if (ind) ind.classList.remove('paused');
  }

  // Enemy
  const zone = $('zone-name'), ename = $('enemy-name'), badge = $('enemy-badge');
  const hpPctEl = $('hp-pct'), hpBar = $('hp-bar');
  const bossTimer = $('boss-timer'), bossVal = $('boss-timer-val');
  const btnBoss = $('btn-start-boss');

  if (zone) zone.textContent = `SECTOR ${s.sector} · ${s.substage}/10 — ${s.zone}`;
  if (ename) ename.textContent = e.name;
  if (badge) {
    badge.textContent = e.is_boss ? 'BOSS' : 'NORMAL';
    badge.className = 'enemy-badge' + (e.is_boss ? ' boss' : '');
  }

  // Update reward display
  const rewOutput = document.getElementById('reward-output');
  const rewExp = document.getElementById('reward-exp');
  if (rewOutput) rewOutput.textContent = (e.reward_gold || 0).toLocaleString();
  if (rewExp) rewExp.textContent = (e.reward_exp || 0).toLocaleString();

  const hpPct = Math.max(0, (e.hp / e.max_hp) * 100);
  if (hpPctEl) hpPctEl.textContent = Math.round(hpPct) + '%';
  if (hpBar) {
    hpBar.style.width = hpPct + '%';
    hpBar.className = 'bar-fill ' + (hpPct < 25 ? 'bar-red' : hpPct < 60 ? 'bar-amber' : 'bar-green');
  }

  if (bossTimer && bossVal) {
    if (e.is_boss && e.boss_timer > 0) {
      bossTimer.classList.remove('hidden');
      bossVal.textContent = Math.ceil(e.boss_timer) + 's';
    } else {
      bossTimer.classList.add('hidden');
    }
  }

  if (btnBoss) {
    if (s.substage === 10) {
      btnBoss.classList.remove('hidden');
      btnBoss.textContent = s.boss_active ? 'BOSS IN PROGRESS...' : 'START DEBUG SESSION';
      btnBoss.className = 'btn btn-red btn-full';
    } else {
      btnBoss.classList.add('hidden');
    }
  }

  // Stats cards
  const atk = $('stat-atk'), dps = $('stat-dps'), def = $('stat-def');
  const crit = $('stat-crit'), hp = $('stat-hp'), rank = $('stat-rank'), barExp = $('exp-mini-bar');
  if (atk) atk.textContent = p.atk;
  if (dps) dps.textContent = p.dps;
  if (def) def.textContent = p.defense;
  if (crit) crit.textContent = (p.crit_rate*100).toFixed(1) + '%';
  if (hp) hp.textContent = `${p.hp}/${p.max_hp}`;
  if (rank) rank.textContent = p.level;
  if (barExp && p.exp_needed > 0) {
    barExp.style.width = Math.min(100, (p.exp/p.exp_needed)*100) + '%';
  }

  // Agents
  const aGrid = $('agents-grid'), aCount = $('agent-count');
  const agents = gameState.agents || [];
  if (aCount) aCount.textContent = `${p.deployed_count} / ${p.max_agent_slots}`;
  if (aGrid) {
    if (agents.length === 0) {
      aGrid.innerHTML = '<div class="empty-state">No workers deployed.</div>';
    } else {
      aGrid.innerHTML = agents.map(a => `
        <div class="agent-card ${a.deployed?'deployed':''}" data-agent-id="${a.id}" onclick="selectMergeSlot('${a.id}')">
          <div class="agent-header">
            <div class="agent-name">${a.name}</div>
            <div class="agent-tier tier-${a.tier}">${a.tier.toUpperCase()}</div>
          </div>
          <div class="agent-stats-row"><span>Lv.${a.level}</span><span>DPS ${a.dps}</span></div>
          <div class="agent-actions">
            <button class="btn btn-sm ${a.deployed?'btn-red':'btn-green'}" onclick="event.stopPropagation();sendAction('${a.deployed?'undeploy_agent':'deploy_agent'}',{agent_id:'${a.id}'})">${a.deployed?'RECALL':'DEPLOY'}</button>
            <button class="btn btn-amber btn-sm" onclick="event.stopPropagation();sendAction('enhance_agent',{agent_id:'${a.id}'})">UP</button>
          </div>
        </div>`).join('');
    }
  }

  // Modules
  const mGrid = $('modules-grid'), mCount = $('module-count');
  const slotInj = $('slot-injector'), slotBar = $('slot-barrier'), slotCac = $('slot-cache');
  const modules = gameState.modules || [];
  if (mCount) mCount.textContent = modules.length;

  const installed = modules.filter(m => m.installed);
  const slotMap = {};
  installed.forEach(m => { slotMap[m.slot] = m; });

  [['injector',slotInj],['barrier',slotBar],['cache',slotCac]].forEach(([s,el]) => {
    if (!el) return;
    const mod = slotMap[s];
    el.textContent = mod ? mod.name : 'EMPTY';
    el.style.color = mod ? 'var(--text)' : 'var(--muted)';
  });

  if (mGrid) {
    if (modules.length === 0) {
      mGrid.innerHTML = '<div class="empty-state">Module bay empty.</div>';
    } else {
      mGrid.innerHTML = modules.map((m,i) => `
        <div class="module-card ${m.installed?'installed':''}">
          <div class="module-name">${m.name}</div>
          <div class="module-rarity rarity-${m.rarity}">${m.rarity.toUpperCase()}</div>
          <div class="module-stats">${[m.atk_bonus&&'ATK+'+m.atk_bonus,m.def_bonus&&'DEF+'+m.def_bonus,m.hp_bonus&&'HP+'+m.hp_bonus,m.crit_rate_bonus&&'CRIT+'+(m.crit_rate_bonus*100).toFixed(1)+'%'].filter(Boolean).join(' ')||'No bonus'}</div>
          <div class="module-slot-tag">${m.slot.toUpperCase()}</div>
          <div class="module-actions">
            <button class="btn btn-sm ${m.installed?'btn-red':'btn-blue'}" onclick="sendAction('${m.installed?'uninstall_module':'install_module'}',{${m.installed?`slot:'${m.slot}'`:`index:${i}`}})">${m.installed?'REMOVE':'INSTALL'}</button>
          </div>
        </div>`).join('');
    }
  }

  // Lab toggles
  if ($('toggle-auto')) $('toggle-auto').classList.toggle('on', p.auto_enhance);
  if ($('toggle-pause')) $('toggle-pause').classList.toggle('on', p.paused);

  // Daily
  const dailyStatus = $('daily-status'), btnDaily = $('btn-daily');
  if (dailyStatus && btnDaily) {
    const now = Date.now()/1000;
    const last = p.last_daily_claim || 0;
    const remaining = 86400 - (now - last);
    if (remaining <= 0) {
      dailyStatus.innerHTML = '<span style="color:var(--green)">● Ready to claim</span>';
      btnDaily.disabled = false;
    } else {
      const h = Math.floor(remaining/3600), m = Math.floor((remaining%3600)/60);
      dailyStatus.innerHTML = `<span style="color:var(--muted)">Next in ${h}h ${m}m</span>`;
      btnDaily.disabled = true;
    }
  }

  // Prestige
  ['prestige-sector','prestige-req','prestige-core','prestige-gain'].forEach(id => {
    const el = $(id); if (!el) return;
    if (id === 'prestige-sector') el.textContent = s.sector;
    if (id === 'prestige-req') el.textContent = '40';
    if (id === 'prestige-core') el.textContent = p.core_points;
    if (id === 'prestige-gain') el.textContent = '+' + Math.floor(s.sector*0.5);
  });
  const btnPrestige = $('btn-prestige');
  if (btnPrestige) {
    const can = s.sector >= 40;
    btnPrestige.disabled = !can;
    btnPrestige.textContent = can ? 'RECOMPILE' : 'NEED SECTOR 40';
  }

  // Merge UI
  document.querySelectorAll('.merge-slot').forEach((el,i) => {
    const aid = mergeSlots[i];
    if (aid && agents.length) {
      const agent = agents.find(a => a.id === aid);
      if (agent) { el.textContent = agent.name; el.classList.add('filled'); }
      else { mergeSlots[i] = null; el.textContent = `Slot ${i+1}`; el.classList.remove('filled'); }
    }
  });
  const btnMerge = $('btn-merge');
  if (btnMerge) btnMerge.disabled = mergeSlots.filter(s=>s!==null).length !== 3;

  // Event stream
  const stream = $('event-stream');
  if (stream && eventQueue.length > 0) {
    stream.innerHTML = eventQueue.slice(0,20).map(e => `<div class="event-entry">${e}</div>`).join('');
  }

  // Achievements
  const ach = $('ach-list');
  if (ach) {
    const items = [
      ['First Purge', (s.kills_in_stage||0)>=1],
      ['Entity Hunter', (s.kills_in_stage||0)>=50],
      ['Sector Cleaner', (s.kills_in_stage||0)>=100],
      ['Operator Lv.5', p.level>=5],
      ['Maintainer Lv.10', p.level>=10],
      ['Architect Lv.25', p.level>=25],
      ['Relay Access (S10)', s.sector>=10],
      ['Core Network (S25)', s.sector>=25],
      ['Buffer Full (1K)', p.gold>=1000],
      ['Cache Overflow (10K)', p.gold>=10000],
    ];
    ach.innerHTML = items.map(([name,done]) => `
      <div class="ach-entry ${done?'completed':'locked'}">
        <span class="ach-icon">${done?'✅':'🔒'}</span>
        <span class="ach-name ${done?'':'locked'}">${name}</span>
      </div>`).join('');
  }
}

// --- ACTIONS ---
function startBoss() { sendAction('start_boss'); }
function claimDaily() { sendAction('claim_daily'); }
function toggleAuto() { sendAction('toggle_auto'); }
function togglePause() { sendAction('toggle_pause'); }
function recompile() { sendAction('recompile'); }
function autoInstall() { sendAction('install_module', {index:''}); }
function openEnhance(stat) {
  const map = {atk:'atk',def:'defense',hp:'max_hp',crit:'crit_rate'};
  const labels = {atk:'PROCESSING',defense:'STABILITY',max_hp:'INTEGRITY',crit_rate:'OPTIMIZATION'};
  const key = map[stat];
  if (!key) return;
  const p = gameState?.player;
  if (!p) return;
  let val = p[key];
  if (key === 'crit_rate') val = (val*100).toFixed(1)+'%';
  showModal(`UPGRADE ${labels[key]}`, `
    <div style="text-align:center;margin-bottom:12px;">
      <div style="font-size:28px;font-weight:700;color:#fff;">${val}</div>
    </div>
    <button class="btn btn-green btn-full" onclick="sendAction('enhance',{stat:'${key}'});closeModal()">ENHANCE</button>
  `);
}
function selectMergeSlot(agentId) {
  const idx = mergeSlots.findIndex(s => s === null);
  if (idx === -1) { mergeSlots = [agentId, null, null]; }
  else if (!mergeSlots.includes(agentId)) mergeSlots[idx] = agentId;
  updateAllUI();
}
function executeMerge() {
  const filled = mergeSlots.filter(s => s !== null);
  if (filled.length !== 3) { showToast('Select 3 workers','error'); return; }
  sendAction('merge_agents', {ids: filled.join(' ')});
  mergeSlots = [null,null,null];
}
function openRecruitModal() {
  showModal('RECRUIT','<div style="color:var(--muted);text-align:center;padding:12px;">Use Deploy on available workers.</div><button class="btn btn-muted btn-full" onclick="closeModal()">CLOSE</button>');
}
function addEvent(msg) {
  const time = new Date().toLocaleTimeString();
  eventQueue.unshift(`<span style="color:var(--muted)">${time}</span> ${msg}`);
  if (eventQueue.length > 50) eventQueue.pop();
}

// ─── TYPING LOG ENGINE ───────────────────────
let logBuffer = [];
let isTyping = false;
const TYPE_SPEED = 18; // ms per character

function addEvent(msg) {
  logBuffer.push(msg);
  if (logBuffer.length > 100) logBuffer.shift();
}

function flushLogBuffer() {
  if (logBuffer.length === 0) return;
  
  const messages = [...logBuffer];
  logBuffer = [];
  
  // Process sequentially with typing effect
  typeMessages(messages, 0);
}

async function typeMessages(messages, index) {
  if (index >= messages.length || !$('event-stream')) return;
  
  const msg = messages[index];
  const entry = document.createElement('div');
  entry.className = 'event-entry typing';
  
  const timeSpan = document.createElement('span');
  timeSpan.style.cssText = 'color:var(--muted);margin-right:8px;';
  timeSpan.textContent = new Date().toLocaleTimeString();
  entry.appendChild(timeSpan);
  
  const textSpan = document.createElement('span');
  entry.appendChild(textSpan);
  
  const stream = $('event-stream');
  // Remove placeholder
  const placeholder = stream.querySelector('.event-placeholder');
  if (placeholder) placeholder.remove();
  
  stream.insertBefore(entry, stream.firstChild);
  
  // Type character by character
  for (let i = 0; i < msg.length; i++) {
    textSpan.textContent += msg[i];
    await new Promise(r => setTimeout(r, TYPE_SPEED + Math.random() * 8));
  }
  
  // Remove cursor class
  entry.classList.remove('typing');
  
  // Keep max 30 entries
  while (stream.children.length > 30) {
    stream.lastChild?.remove();
  }
  
  // Next message with small delay
  await new Promise(r => setTimeout(r, 400));
  typeMessages(messages, index + 1);
}

// Flush buffer every 5 seconds
setInterval(flushLogBuffer, 5000);

// --- MODALS ---
function showModal(title, html) {
  const t = $('modal-title'), b = $('modal-body'), o = $('modal-overlay');
  if (t) t.textContent = title;
  if (b) b.innerHTML = html;
  if (o) o.classList.add('open');
}
function closeModal() { const o = $('modal-overlay'); if (o) o.classList.remove('open'); }
function closeModalOutside(e) { if (e.target === $('modal-overlay')) closeModal(); }

// --- TABS ---
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const tab = document.getElementById('tab-'+name);
  if (tab) tab.classList.add('active');
  const nav = document.querySelector(`.nav-item[data-tab="${name}"]`);
  if (nav) nav.classList.add('active');
}

// --- WEBSOCKET ---
function connectWS() {
  try {
    const ws = new WebSocket(`ws://${location.hostname}:8081`);
    ws.onmessage = e => {
      try { const d = JSON.parse(e.data); addEvent(d.message); updateAllUI(); } catch(ex) {}
    };
    ws.onclose = () => setTimeout(connectWS, 5000);
  } catch(e) {}
}

// --- INIT ---
window.addEventListener('load', () => {
  currentUser = getUserId();
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => switchTab(item.dataset.tab));
  });
  document.querySelectorAll('.merge-slot').forEach((el,i) => {
    el.addEventListener('click', () => { mergeSlots[i] = null; updateAllUI(); });
  });
  fetchState();
  setInterval(fetchState, STATE_INTERVAL);
  connectWS();
});
