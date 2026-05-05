// ═══════════════════════════════════════════
// DATA & STATE
// ═══════════════════════════════════════════

const AGENTS = [
  { id:1, name:'CIPHER-X', emoji:'🤖', rarity:'legendary', level:12, dps:480, status:'deployed', desc:'Tier-5 breach agent. Specializes in layered encryption dismantling.' },
  { id:2, name:'PHANTOM', emoji:'🔮', rarity:'epic', level:9, dps:320, status:'deployed', desc:'Stealth infiltration unit. Low detection profile.' },
  { id:3, name:'NULL-9', emoji:'⚙️', rarity:'rare', level:7, dps:320, status:'standby', desc:'Multi-vector support unit.' },
  { id:4, name:'IRON VEIL', emoji:'🛡️', rarity:'rare', level:11, dps:180, status:'deployed', desc:'Defense anchor with reflect mechanics.' },
  { id:5, name:'SPECTER', emoji:'👁️', rarity:'common', level:5, dps:140, status:'standby', desc:'Early-game recon unit.' },
  { id:6, name:'AXIOM', emoji:'⚡', rarity:'epic', level:8, dps:410, status:'deployed', desc:'High burst attacker. Volatile cooldown.' },
  { id:7, name:'PRISM', emoji:'🔷', rarity:'common', level:3, dps:90, status:'standby', desc:'Utility agent. Buff stacking specialist.' },
  { id:8, name:'VERTEX', emoji:'🌀', rarity:'rare', level:6, dps:210, status:'standby', desc:'Crowd control and disruption.' },
];

const MODULES = [
  { id:1, icon:'⚡', name:'VOLTCORE', rarity:'epic', slot:'attack', stat:'+340 ATK', equipped:true },
  { id:2, icon:'🛡️', name:'IRONPLATE', rarity:'rare', slot:'defense', stat:'+180 DEF', equipped:true },
  { id:3, icon:'💉', name:'REGEN CELL', rarity:'common', slot:'support', stat:'+120 HP/s', equipped:false },
  { id:4, icon:'🎯', name:'SCOPE MK2', rarity:'rare', slot:'attack', stat:'+12% CRIT', equipped:false },
  { id:5, icon:'🔥', name:'PYREX', rarity:'legendary', slot:'attack', stat:'+580 DPS', equipped:true },
  { id:6, icon:'🧊', name:'CRYO LOCK', rarity:'epic', slot:'defense', stat:'-22% DMG RCV', equipped:false },
  { id:7, icon:'📡', name:'SIGNAL AMP', rarity:'common', slot:'support', stat:'+8% XP', equipped:false },
  { id:8, icon:'⚙️', name:'SYN CORE', rarity:'rare', slot:'support', stat:'+200 HP', equipped:true },
  { id:9, icon:'🌀', name:'VORTEX', rarity:'epic', slot:'attack', stat:'+280 ATK', equipped:false },
  { id:10, icon:'🔮', name:'ETHER NODE', rarity:'rare', slot:'support', stat:'+15% DPS', equipped:false },
  { id:11, icon:'🗡️', name:'EDGE PROC', rarity:'common', slot:'attack', stat:'+60 ATK', equipped:false },
  { id:12, icon:'🔒', name:'BULWARK', rarity:'legendary', slot:'defense', stat:'+420 DEF', equipped:false },
];

const EVENTS = [
  { type:'TARGET PURGED', detail:'Node CIPHER-04 eliminated · +340 XP', color:'var(--red)', time:'0s ago' },
  { type:'MODULE FOUND', detail:'VOLTCORE [EPIC] dropped from cache', color:'var(--purple)', time:'12s ago' },
  { type:'RANK UPDATED', detail:'WRAITH-II → WRAITH-III achieved', color:'var(--amber)', time:'1m ago' },
  { type:'AGENT DEPLOYED', detail:'AXIOM deployed to NEXUS-7', color:'var(--green)', time:'3m ago' },
  { type:'AUTO BREACH', detail:'AUTO cycle completed · +820 CR', color:'var(--blue)', time:'5m ago' },
];

const MILESTONES = [
  { name:'FIRST PURGE', desc:'Complete first target', prog:'1/1', pct:100, done:true, icon:'🎯' },
  { name:'SQUAD ONLINE', desc:'Deploy 5 agents simultaneously', prog:'5/5', pct:100, done:true, icon:'◈' },
  { name:'DEEP SECTOR', desc:'Reach Sector 10', prog:'7/10', pct:70, done:false, icon:'⬡' },
  { name:'MODULE MASTER', desc:'Equip 6 modules at once', prog:'4/6', pct:66, done:false, icon:'◫' },
  { name:'WRAITH ASCENSION', desc:'Reach rank WRAITH-V', prog:'3/5', pct:60, done:false, icon:'◉' },
];

const UNLOCKS = [
  { name:'SLOT 7 AGENT', req:'RANK WRAITH-IV', locked:false, color:'var(--green)' },
  { name:'EPIC POOL', req:'RANK WRAITH-IV', locked:false, color:'var(--purple)' },
  { name:'SECTOR 8 ACCESS', req:'RANK WRAITH-V', locked:true, color:'var(--amber)' },
  { name:'RECOMPILE BOOST', req:'MODULE MASTER', locked:true, color:'var(--blue)' },
];

const INV_ITEMS = [
  { emoji:'💊', name:'Nanohealer', qty:4, rarity:'common', effect:'+500 HP instant' },
  { emoji:'⚡', name:'Surge Token', qty:2, rarity:'rare', effect:'+50% ATK · 30s' },
  { emoji:'🔑', name:'Sector Key', qty:1, rarity:'epic', effect:'Unlocks locked sector' },
  { emoji:'🎲', name:'Shard Booster', qty:5, rarity:'common', effect:'+20% SH gain · 1h' },
  { emoji:'📦', name:'Module Crate', qty:2, rarity:'rare', effect:'Contains 1-3 modules' },
];

// ═══════════════════════════════════════════
// RENDER FUNCTIONS
// ═══════════════════════════════════════════

function rarityClass(r) {
  return { common:'rarity-common', rare:'rarity-rare', epic:'rarity-epic', legendary:'rarity-legendary' }[r] || 'rarity-common';
}
function rarityBadge(r) {
  const m = { common:'badge-muted', rare:'badge-blue', epic:'badge-purple', legendary:'badge-amber' };
  return `<span class="badge ${m[r]||'badge-muted'}">${r.toUpperCase()}</span>`;
}

function renderAgents() {
  const g = document.getElementById('agents-grid');
  if (!g) return;
  g.innerHTML = AGENTS.map(a => `
    <div class="agent-card ${a.status==='deployed'?'deployed':''}" onclick="openModal('agent', ${a.id})">
      <div class="agent-lvl">LVL ${a.level}</div>
      <div class="agent-avatar">
        ${a.emoji}
        ${a.status==='deployed'?'<div class="active-badge">ON</div>':''}
      </div>
      <div class="agent-name">${a.name}</div>
      <div class="agent-rarity ${rarityClass(a.rarity)}">${a.rarity.toUpperCase()}</div>
      <div class="agent-stats">
        <span class="agent-stat"><strong>${a.dps}</strong> DPS</span>
      </div>
      <div class="agent-btns">
        <button class="btn ${a.status==='deployed'?'btn-red':'btn-green'} btn-sm" onclick="event.stopPropagation();toggleDeploy(${a.id})">${a.status==='deployed'?'RECALL':'DEPLOY'}</button>
        <button class="btn btn-amber btn-sm" onclick="event.stopPropagation();openModal('upgrade-agent',${a.id})">UP</button>
        <button class="btn btn-muted btn-sm" onclick="event.stopPropagation();openModal('agent',${a.id})">...</button>
      </div>
    </div>
  `).join('');
}

let currentModuleFilter = 'all';

function renderModules(filter='all') {
  currentModuleFilter = filter;
  const g = document.getElementById('modules-grid');
  if (!g) return;
  let mods = MODULES;
  if(filter==='common'||filter==='rare'||filter==='epic'||filter==='legendary') mods = MODULES.filter(m=>m.rarity===filter);
  if(filter==='attack'||filter==='defense'||filter==='support') mods = MODULES.filter(m=>m.slot===filter);
  g.innerHTML = mods.map(m => `
    <div class="module-card ${m.equipped?'equipped':''}" onclick="openModal('module',${m.id})">
      <div class="module-icon">${m.icon}</div>
      <div class="module-name">${m.name}</div>
      <div class="module-rarity ${rarityClass(m.rarity)}">${m.rarity.toUpperCase()}</div>
      <div class="module-stat">${m.stat}</div>
      <div class="module-slot">${m.slot.toUpperCase()} SLOT</div>
      <div class="module-btns">
        <button class="btn ${m.equipped?'btn-red':'btn-blue'} btn-sm" onclick="event.stopPropagation();toggleEquip(${m.id})">${m.equipped?'REMOVE':'INSTALL'}</button>
        <button class="btn btn-amber btn-sm" onclick="event.stopPropagation();openModal('enhance-module',${m.id})">⚡</button>
      </div>
    </div>
  `).join('');
}

function renderEvents() {
  const s = document.getElementById('event-stream');
  if (!s) return;
  s.innerHTML = EVENTS.map(e => `
    <div class="event-card">
      <div class="event-dot" style="background:${e.color}"></div>
      <div class="event-body">
        <div class="event-type" style="color:${e.color}">${e.type}</div>
        <div class="event-detail">${e.detail}</div>
      </div>
      <div class="event-time">${e.time}</div>
    </div>
  `).join('');
}

function renderMilestones() {
  const m = document.getElementById('milestones');
  if (!m) return;
  m.innerHTML = MILESTONES.map(ms => `
    <div class="milestone ${ms.done?'done':''}">
      <div class="milestone-icon">${ms.icon}</div>
      <div class="milestone-info">
        <div class="milestone-name">${ms.name}</div>
        <div class="milestone-prog">${ms.desc} · ${ms.prog}</div>
        <div class="bar-track" style="height:4px">
          <div class="bar-fill ${ms.done?'bar-green':'bar-amber'}" style="width:${ms.pct}%"></div>
        </div>
      </div>
      <div class="milestone-check">${ms.done?'✅':'⬜'}</div>
    </div>
  `).join('');
}

function renderUnlocks() {
  const g = document.getElementById('unlock-grid');
  if (!g) return;
  g.innerHTML = UNLOCKS.map(u => `
    <div class="unlock-card ${u.locked?'locked':''}" onclick="openModal('unlock','${u.name}')">
      <div class="unlock-name">${u.name}</div>
      <div class="unlock-req">${u.req}</div>
      <div class="unlock-status" style="color:${u.locked?'var(--muted)':u.color}">${u.locked?'🔒 LOCKED':'✓ UNLOCKED'}</div>
    </div>
  `).join('');
}

function renderInventory() {
  const l = document.getElementById('inv-list');
  if (!l) return;
  l.innerHTML = INV_ITEMS.map(it => `
    <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;background:var(--panel2);border:1px solid var(--border);border-radius:8px;cursor:pointer;transition:border-color .15s" onmouseover="this.style.borderColor='var(--border2)'" onmouseout="this.style.borderColor='var(--border)'" onclick="openModal('use-item-detail','${it.name}')">
      <span style="font-size:22px">${it.emoji}</span>
      <div style="flex:1">
        <div style="font-weight:700;font-size:14px">${it.name}</div>
        <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--muted)">${it.effect}</div>
      </div>
      <div style="text-align:right">
        <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:var(--text)">×${it.qty}</div>
        <div class="badge badge-${it.rarity==='common'?'muted':it.rarity==='rare'?'blue':'purple'}" style="margin-top:2px">${it.rarity.toUpperCase()}</div>
      </div>
    </div>
  `).join('');
}

// ═══════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════

function switchPage(name) {
  // Update halaman
  document.querySelectorAll('.page').forEach(p => {
    p.classList.remove('active');
    if (name === 'ai-console') {
      p.style.display = 'none';
    }
  });
  
  const activePage = document.getElementById('page-'+name);
  if (activePage) {
    if (name === 'ai-console') {
      activePage.style.display = 'flex';
      activePage.style.flexDirection = 'column';
      activePage.style.height = '100%';
      initAIConsole();
    } else {
      activePage.style.display = '';
      activePage.classList.add('active');
    }
  }

  // Update navigasi
  document.querySelectorAll('.nav-item, .bnav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll(`[data-page="${name}"]`).forEach(n => n.classList.add('active'));
  
  document.getElementById('content').scrollTop = 0;
  
  // TG Back Button
  if (name !== 'dashboard') {
    TG.backBtn(() => { switchPage('dashboard'); TG.hideBack(); });
  } else {
    TG.hideBack();
  }
  
  // TG Main Button
  if (name === 'dashboard') {
    TG.mainBtn('ENHANCE SYSTEM', () => openModal('enhance'));
  } else {
    TG.hideMainBtn();
  }
}

document.querySelectorAll('.nav-item, .bnav-item').forEach(item => {
  item.addEventListener('click', () => switchPage(item.dataset.page));
});

// ═══════════════════════════════════════════
// MODULE FILTERS
// ═══════════════════════════════════════════

document.querySelectorAll('#module-filters .filter-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('#module-filters .filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    renderModules(chip.dataset.filter);
  });
});

// ═══════════════════════════════════════════
// MODALS
// ═══════════════════════════════════════════

const MODAL_CONTENT = {
  enhance: {
    title: '⚡ ENHANCE SYSTEM',
    body: () => `
      <div class="effect-preview">
        <div class="effect-row">
          <span class="effect-label">ATK</span>
          <span class="effect-val">2,840<span class="effect-arrow">→</span><span class="effect-new">3,420</span></span>
        </div>
        <div class="effect-row">
          <span class="effect-label">DPS</span>
          <span class="effect-val">1,120<span class="effect-arrow">→</span><span class="effect-new">1,344</span></span>
        </div>
        <div class="effect-row">
          <span class="effect-label">CRIT</span>
          <span class="effect-val">28%<span class="effect-arrow">→</span><span class="effect-new">31%</span></span>
        </div>
      </div>
      <div class="cost-row">
        <span class="cost-label">COST</span>
        <span class="cost-val">1,200 CR + 80 SH</span>
      </div>
      <button class="btn btn-green btn-full" onclick="confirmAction('enhance')">CONFIRM ENHANCE</button>
    `
  },
  deploy: {
    title: '▶ DEPLOY AGENTS',
    body: () => `
      <div style="font-size:13px;color:var(--muted);margin-bottom:14px;font-family:'JetBrains Mono',monospace">Select agents to deploy to NEXUS-7</div>
      ${AGENTS.filter(a=>a.status==='standby').slice(0,3).map(a=>`
        <div style="display:flex;align-items:center;justify-content:space-between;padding:9px 12px;background:var(--panel2);border:1px solid var(--border);border-radius:8px;margin-bottom:6px">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:20px">${a.emoji}</span>
            <div>
              <div style="font-weight:700;font-size:13px">${a.name}</div>
              <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--muted)">DPS ${a.dps} · LVL ${a.level}</div>
            </div>
          </div>
          <button class="btn btn-green btn-sm" onclick="closeModal()">DEPLOY</button>
        </div>
      `).join('')}
      <div style="margin-top:12px">
        <button class="btn btn-muted btn-full" onclick="closeModal()">CANCEL</button>
      </div>
    `
  },
  checkpoint: {
    title: '⊠ SAVE CHECKPOINT',
    body: () => `
      <div style="font-size:13px;color:var(--muted);margin-bottom:14px;font-family:'JetBrains Mono',monospace">
        Save current run state to on-chain checkpoint.<br>Gas: ~0.0002 ETH (BASE L2)
      </div>
      <div class="effect-preview">
        <div class="effect-row"><span class="effect-label">SECTOR</span><span class="effect-val" style="color:var(--text)">NEXUS-7 / GRID ALPHA</span></div>
        <div class="effect-row"><span class="effect-label">AGENTS</span><span class="effect-val" style="color:var(--text)">5 ACTIVE</span></div>
        <div class="effect-row"><span class="effect-label">PROGRESS</span><span class="effect-val" style="color:var(--amber)">82% XP TO RANK</span></div>
      </div>
      <div style="height:10px"></div>
      <button class="btn btn-amber btn-full" onclick="confirmAction('checkpoint')">⊠ SAVE TO CHAIN</button>
      <button class="btn btn-muted btn-full" style="margin-top:6px" onclick="closeModal()">CANCEL</button>
    `
  },
  recruit: {
    title: '+ RECRUIT AGENT',
    body: () => `
      <div style="font-size:13px;color:var(--muted);margin-bottom:14px;font-family:'JetBrains Mono',monospace">Pull from agent pool</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px">
        <div style="background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center;cursor:pointer" onclick="confirmAction('recruit-standard')">
          <div style="font-size:28px;margin-bottom:6px">📦</div>
          <div style="font-weight:700;font-size:13px">STANDARD</div>
          <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--muted);margin:4px 0">Common · Rare</div>
          <div style="color:var(--amber);font-family:'JetBrains Mono',monospace;font-weight:700">400 CR</div>
        </div>
        <div style="background:var(--purple-dim);border:1px solid rgba(188,140,255,0.3);border-radius:10px;padding:14px;text-align:center;cursor:pointer" onclick="confirmAction('recruit-premium')">
          <div style="font-size:28px;margin-bottom:6px">💎</div>
          <div style="font-weight:700;font-size:13px">PREMIUM</div>
          <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--muted);margin:4px 0">Epic · Legendary</div>
          <div style="color:var(--purple);font-family:'JetBrains Mono',monospace;font-weight:700">120 SH</div>
        </div>
      </div>
    `
  },
  'boost-recompile': {
    title: '⚡ BOOST RECOMPILE',
    body: () => `
      <div class="effect-preview">
        <div class="effect-row"><span class="effect-label">CURRENT ETA</span><span class="effect-val" style="color:var(--red)">2h 14m</span></div>
        <div class="effect-row"><span class="effect-label">AFTER BOOST</span><span class="effect-val effect-new">48m</span></div>
        <div class="effect-row"><span class="effect-label">TIME SAVED</span><span class="effect-val effect-new">1h 26m</span></div>
      </div>
      <div class="cost-row"><span class="cost-label">COST</span><span class="cost-val">200 SH</span></div>
      <button class="btn btn-amber btn-full" onclick="confirmAction('boost')">APPLY BOOST</button>
    `
  },
  notif: {
    title: '🔔 NOTIFICATIONS',
    body: () => `
      <div style="display:flex;flex-direction:column;gap:6px">
        <div style="padding:10px 12px;background:var(--red-dim);border:1px solid rgba(255,123,114,0.25);border-radius:8px">
          <div style="font-weight:700;font-size:13px;color:var(--red)">⚠ INTEGRITY LOW</div>
          <div style="font-size:12px;color:var(--muted);margin-top:2px">Target integrity at 34% — breach imminent</div>
        </div>
        <div style="padding:10px 12px;background:var(--amber-dim);border:1px solid rgba(227,179,65,0.25);border-radius:8px">
          <div style="font-weight:700;font-size:13px;color:var(--amber)">↑ RANK CLOSE</div>
          <div style="font-size:12px;color:var(--muted);margin-top:2px">5,200 XP to WRAITH-IV</div>
        </div>
        <div style="padding:10px 12px;background:var(--green-dim);border:1px solid rgba(126,231,135,0.25);border-radius:8px">
          <div style="font-weight:700;font-size:13px;color:var(--green)">✓ MODULE DROPPED</div>
          <div style="font-size:12px;color:var(--muted);margin-top:2px">VOLTCORE [EPIC] in inventory</div>
        </div>
      </div>
    `
  }
};

function openModal(type, id) {
  const overlay = document.getElementById('modal');
  const title = document.getElementById('modal-title');
  const body = document.getElementById('modal-body');

  if(type === 'agent' && id) {
    const a = AGENTS.find(x=>x.id===id);
    title.textContent = a.name;
    body.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
        <div style="font-size:40px;width:54px;height:54px;background:var(--panel2);border:1px solid var(--border);border-radius:12px;display:flex;align-items:center;justify-content:center">${a.emoji}</div>
        <div>
          <div>${rarityBadge(a.rarity)} <span class="badge badge-muted">LVL ${a.level}</span></div>
          <div style="font-size:12px;color:var(--muted);font-family:'JetBrains Mono',monospace;margin-top:4px">${a.desc}</div>
        </div>
      </div>
      <div class="effect-preview">
        <div class="effect-row"><span class="effect-label">DPS</span><span class="effect-val" style="color:var(--green)">${a.dps}</span></div>
        <div class="effect-row"><span class="effect-label">STATUS</span><span class="effect-val" style="color:${a.status==='deployed'?'var(--green)':'var(--amber)'}">${a.status.toUpperCase()}</span></div>
      </div>
      <div style="display:flex;gap:6px;margin-top:14px">
        <button class="btn ${a.status==='deployed'?'btn-red':'btn-green'}" style="flex:1" onclick="toggleDeploy(${a.id});closeModal()">${a.status==='deployed'?'RECALL':'DEPLOY'}</button>
        <button class="btn btn-amber" onclick="openModal('upgrade-agent',${a.id})">UPGRADE</button>
      </div>
    `;
  } else if(type === 'upgrade-agent' && id) {
    const a = AGENTS.find(x=>x.id===id);
    title.textContent = '↑ UPGRADE · '+a.name;
    body.innerHTML = `
      <div class="effect-preview">
        <div class="effect-row"><span class="effect-label">LEVEL</span><span class="effect-val">${a.level}<span class="effect-arrow">→</span><span class="effect-new">${a.level+1}</span></span></div>
        <div class="effect-row"><span class="effect-label">DPS</span><span class="effect-val">${a.dps}<span class="effect-arrow">→</span><span class="effect-new">${Math.round(a.dps*1.15)}</span></span></div>
      </div>
      <div class="cost-row"><span class="cost-label">COST</span><span class="cost-val">${a.level*80} CR + ${a.level*5} SH</span></div>
      <button class="btn btn-amber btn-full" onclick="confirmAction('upgrade')">CONFIRM UPGRADE</button>
    `;
  } else if(type === 'module' && id) {
    const m = MODULES.find(x=>x.id===id);
    title.textContent = m.name;
    body.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
        <div style="font-size:32px;width:48px;height:48px;background:var(--panel2);border:1px solid var(--border);border-radius:10px;display:flex;align-items:center;justify-content:center">${m.icon}</div>
        <div>
          <div>${rarityBadge(m.rarity)}</div>
          <div style="font-size:12px;font-family:'JetBrains Mono',monospace;color:var(--muted);margin-top:4px">${m.slot.toUpperCase()} SLOT</div>
        </div>
      </div>
      <div class="effect-preview">
        <div class="effect-row"><span class="effect-label">BONUS</span><span class="effect-val effect-new">${m.stat}</span></div>
        <div class="effect-row"><span class="effect-label">STATE</span><span class="effect-val" style="color:${m.equipped?'var(--blue)':'var(--muted)'}">${m.equipped?'EQUIPPED':'UNEQUIPPED'}</span></div>
      </div>
      <div style="display:flex;gap:6px;margin-top:14px">
        <button class="btn ${m.equipped?'btn-red':'btn-blue'}" style="flex:1" onclick="toggleEquip(${m.id});closeModal()">${m.equipped?'REMOVE':'INSTALL'}</button>
        <button class="btn btn-amber" onclick="openModal('enhance-module',${m.id})">⚡ ENHANCE</button>
      </div>
    `;
  } else if(type === 'enhance-module' && id) {
    const m = MODULES.find(x=>x.id===id);
    title.textContent = '⚡ ENHANCE · '+m.name;
    const cur = parseInt(m.stat.replace(/[^0-9]/g,''))||0;
    body.innerHTML = `
      <div class="effect-preview">
        <div class="effect-row"><span class="effect-label">STAT</span><span class="effect-val">${m.stat}<span class="effect-arrow">→</span><span class="effect-new">${m.stat.replace(cur, Math.round(cur*1.2))}</span></span></div>
      </div>
      <div class="cost-row"><span class="cost-label">COST</span><span class="cost-val">300 CR + 20 SH</span></div>
      <button class="btn btn-amber btn-full" onclick="confirmAction('enhance-module')">CONFIRM</button>
    `;
  } else if(type === 'use-item') {
    title.textContent = 'USE ITEM';
    body.innerHTML = `
      ${INV_ITEMS.filter(i=>i.qty>0).map(it=>`
        <div style="display:flex;align-items:center;justify-content:space-between;padding:9px 12px;background:var(--panel2);border:1px solid var(--border);border-radius:8px;margin-bottom:6px">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:20px">${it.emoji}</span>
            <div>
              <div style="font-weight:700;font-size:13px">${it.name} ×${it.qty}</div>
              <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--muted)">${it.effect}</div>
            </div>
          </div>
          <button class="btn btn-green btn-sm" onclick="confirmAction('use-item')">USE</button>
        </div>
      `).join('')}
    `;
  } else if(MODAL_CONTENT[type]) {
    const mc = MODAL_CONTENT[type];
    title.textContent = mc.title;
    body.innerHTML = mc.body();
  } else {
    title.textContent = type.toUpperCase();
    body.innerHTML = `<div class="empty-hint">No content for: ${type}</div>`;
  }

  overlay.classList.add('open');
}

function closeModal() {
  document.getElementById('modal').classList.remove('open');
}

function closeModalOutside(e) {
  if(e.target === document.getElementById('modal')) closeModal();
}

function confirmAction(type) {
  const body = document.getElementById('modal-body');
  body.innerHTML = `
    <div style="text-align:center;padding:20px 0">
      <div style="font-size:36px;margin-bottom:12px">✅</div>
      <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:16px;color:var(--green)">ACTION CONFIRMED</div>
      <div style="font-size:12px;font-family:'JetBrains Mono',monospace;color:var(--muted);margin-top:6px">${type.toUpperCase()} · processing...</div>
    </div>
  `;
  setTimeout(closeModal, 1400);
}

// ═══════════════════════════════════════════
// INTERACTIONS
// ═══════════════════════════════════════════

let autoActive = false;
let autoTimer;

function toggleAuto() {
  autoActive = !autoActive;
  const btn = document.getElementById('auto-btn');
  if (!btn) return;
  if(autoActive) {
    btn.classList.add('auto-active');
    btn.textContent = '⟳ AUTO ON';
    tickCredits();
  } else {
    btn.classList.remove('auto-active');
    btn.textContent = '⟳ AUTO';
    clearInterval(autoTimer);
  }
}

function tickCredits() {
  if (autoTimer) clearInterval(autoTimer);
  autoTimer = setInterval(() => {
    const el = document.getElementById('cr-val');
    if(!el) return;
    const cur = parseInt(el.textContent.replace(/,/g,''));
    const next = cur + Math.floor(Math.random()*40+10);
    el.textContent = next.toLocaleString();
    el.classList.add('tick');
    setTimeout(()=>el.classList.remove('tick'), 150);
  }, 2000);
}

function toggleDeploy(id) {
  const a = AGENTS.find(x=>x.id===id);
  if(!a) return;
  a.status = a.status==='deployed' ? 'standby' : 'deployed';
  renderAgents();
}

function toggleEquip(id) {
  const m = MODULES.find(x=>x.id===id);
  if(!m) return;
  m.equipped = !m.equipped;
  renderModules(currentModuleFilter);
}

function toggleSetting(row) {
  const toggle = row.querySelector('.toggle');
  if(toggle) toggle.classList.toggle('on');
}

// ═══════════════════════════════════════════
// LIVE TICKERS (Integrity, Events, Shards)
// ═══════════════════════════════════════════

let integrity = 34;
let direction = -1;
setInterval(() => {
  integrity = Math.max(0, Math.min(100, integrity + direction * (Math.random()*1.5)));
  if(integrity <= 5) direction = 1;
  if(integrity >= 98) direction = -1;
  const bar = document.getElementById('integrity-bar');
  const pct = document.querySelector('.integrity-label .pct');
  if(bar) bar.style.width = integrity.toFixed(0)+'%';
  if(pct) pct.textContent = integrity.toFixed(0)+'%';
}, 1200);

const liveEvents = [
  { type:'DPS TICK', detail:'Auto cycle · +120 ATK hit registered', color:'var(--blue)' },
  { type:'MODULE PROC', detail:'VOLTCORE passive triggered', color:'var(--purple)' },
  { type:'SHARD GAIN', detail:'+12 SH from sector drop', color:'var(--amber)' },
  { type:'CRIT HIT', detail:'CIPHER-X CRIT x3.2 · 1,536 DMG', color:'var(--red)' },
  { type:'XP GAINED', detail:'+280 XP · active sector bonus', color:'var(--green)' },
];

setInterval(() => {
  const idx = Math.floor(Math.random() * liveEvents.length);
  const e = liveEvents[idx];
  EVENTS.unshift({ ...e, time: '0s ago' });
  EVENTS.forEach((ev,i) => { if(i>0) ev.time = (i*8)+'s ago'; });
  if(EVENTS.length > 6) EVENTS.pop();
  renderEvents();
}, 4000);

setInterval(() => {
  const el = document.getElementById('sh-val');
  if(!el || !autoActive) return;
  const cur = parseInt(el.textContent.replace(/,/g,''));
  el.textContent = cur + Math.floor(Math.random()*3+1);
}, 3000);

// ═══════════════════════════════════════════
// API DAEMON (Game Sync)
// ═══════════════════════════════════════════

let previousState = {};

async function fetchState() {
  try {
    const res = await fetch('/api/state');
    const data = await res.json();
    updateDashboardFromGame(data);
    updateAgentsFromGame(data.player.agents);
    previousState = data.player;
  } catch(e) {
    console.error('fetchState error:', e);
  }
}

function updateDashboardFromGame(data) {
  document.getElementById('sector-name').textContent = data.stage;
  document.getElementById('entity-name').textContent = data.enemy.name;
  
  const hpPct = data.enemy.hp / data.enemy.max_hp * 100;
  const bar = document.getElementById('integrity-bar');
  const pct = document.querySelector('.integrity-label .pct');
  if(bar) bar.style.width = hpPct + '%';
  if(pct) pct.textContent = Math.round(hpPct) + '%';
  
  document.getElementById('target-gold').textContent = data.enemy.reward_gold;
  document.getElementById('target-exp').textContent = data.enemy.reward_exp;

  // Update topbar values
  const crVal = document.getElementById('cr-val');
  const shVal = document.getElementById('sh-val');
  if (crVal) crVal.textContent = data.player.gold.toLocaleString();
  if (shVal) shVal.textContent = data.player.shards || 0;
  
  // Update stat cards
  document.getElementById('stat-atk').textContent = data.player.atk;
  document.getElementById('stat-def').textContent = data.player.defense;
  document.getElementById('stat-hp').textContent = data.player.hp + '/' + data.player.max_hp;
  document.getElementById('stat-crit').textContent = (data.player.crit_rate * 100).toFixed(1) + '%';
}

function updateAgentsFromGame(agents) {
  // Update the UI with real game agent data
  if (!agents || !agents.length) return;
  // Map real data to AGENTS array format
  agents.forEach((a, idx) => {
    const id = idx + 1;
    const existing = AGENTS.find(x => x.id === id);
    if (existing) {
      existing.name = a.name;
      existing.level = a.level;
      existing.dps = a.dps;
      existing.status = a.deployed ? 'deployed' : 'standby';
      existing.rarity = a.tier || 'common';
      existing.emoji = existing.emoji || '🤖'; // keep emoji if exists
    } else {
      AGENTS.push({
        id,
        name: a.name,
        emoji: '🤖',
        rarity: a.tier || 'common',
        level: a.level,
        dps: a.dps,
        status: a.deployed ? 'deployed' : 'standby',
        desc: ''
      });
    }
  });
  renderAgents();
}

// ═══════════════════════════════════════════
// TELEGRAM WEBAPP LAYER
// ═══════════════════════════════════════════

const TG = (() => {
  const twa = window.Telegram?.WebApp;

  if (twa) {
    twa.ready();
    twa.expand();
    const tc = twa.themeParams;
    if (tc?.bg_color) {
      document.documentElement.style.setProperty('--bg', tc.bg_color || '#0D1117');
    }
    console.log('[TG] WebApp initialized. Platform:', twa.platform);
  } else {
    console.log('[TG] Running outside Telegram — mock mode.');
  }

  function haptic(type = 'light') {
    if (twa?.HapticFeedback) {
      if (type === 'impact')     twa.HapticFeedback.impactOccurred('light');
      else if (type === 'heavy') twa.HapticFeedback.impactOccurred('heavy');
      else if (type === 'error') twa.HapticFeedback.notificationOccurred('error');
      else if (type === 'success') twa.HapticFeedback.notificationOccurred('success');
      else                       twa.HapticFeedback.selectionChanged();
    }
  }

  function mainBtn(text, cb, color = '#7EE787', textColor = '#000000') {
    if (twa?.MainButton) {
      twa.MainButton.setParams({ text, color, text_color: textColor });
      twa.MainButton.show();
      twa.MainButton.onClick(cb);
    } else {
      const btn = document.getElementById('tg-main-btn');
      if (btn) {
        btn.textContent = text;
        btn.classList.add('visible');
        btn._cb = cb;
      }
    }
  }

  function hideMainBtn() {
    if (twa?.MainButton) {
      twa.MainButton.hide();
    } else {
      const btn = document.getElementById('tg-main-btn');
      if (btn) btn.classList.remove('visible');
    }
  }

  function backBtn(cb) {
    if (twa?.BackButton) {
      twa.BackButton.show();
      twa.BackButton.onClick(cb);
    }
  }

  function hideBack() {
    if (twa?.BackButton) twa.BackButton.hide();
  }

  function alert(msg) {
    if (twa) twa.showAlert(msg);
    else window.alert(msg);
  }

  function confirm(msg, cb) {
    if (twa) twa.showConfirm(msg, ok => { if (ok) cb(); });
    else { if (window.confirm(msg)) cb(); }
  }

  function close() {
    if (twa) twa.close();
  }

  const user = twa?.initDataUnsafe?.user;
  const username = user?.username || user?.first_name || 'OPERATOR';

  return { haptic, mainBtn, hideMainBtn, backBtn, hideBack, alert, confirm, close, username, raw: twa };
})();

function tgMainAction() {
  const btn = document.getElementById('tg-main-btn');
  if (btn && btn._cb) btn._cb();
}

// Wrap all .btn clicks with haptic
document.addEventListener('click', e => {
  if (e.target.closest('.btn, .qprompt, .filter-chip, .nav-item, .bnav-item')) {
    TG.haptic('light');
  }
  if (e.target.closest('.btn-red')) {
    TG.haptic('heavy');
  }
});

// ═══════════════════════════════════════════
// AI CONSOLE — STREAMING ENGINE
// ═══════════════════════════════════════════

let isStreaming = false;
let lastAITarget = null;

const AI_RESPONSES = {
  'analyze sector': [
    { type:'text', content:'Scanning NEXUS-7 / GRID ALPHA...' },
    { type:'pause', ms:600 },
    { type:'text', content:'\n\nSector threat profile:' },
    { type:'code', content:'TARGET   : CIPHER SYNDICATE NODE\nINTEGRITY: 34% ↓ declining\nTHREAT   : CRITICAL\nWINDOW   : ~14m before respawn' },
    { type:'pause', ms:400 },
    { type:'text', content:'\n\nRecommendation: deploy ' },
    { type:'highlight', content:'AXIOM', color:'var(--amber)' },
    { type:'text', content:' immediately. Current DPS ' },
    { type:'stat', content:'1,120', label:'DPS' },
    { type:'text', content:' is insufficient for sub-10m clear. You need ≥1,400 DPS to guarantee breach before respawn window closes.' },
  ],
  'optimize agents': [
    { type:'text', content:'Running agent efficiency matrix...' },
    { type:'pause', ms:800 },
    { type:'text', content:'\n\nCurrent formation score: ' },
    { type:'highlight', content:'61 / 100', color:'var(--amber)' },
    { type:'text', content:'\n\nIssues detected:\n\n' },
    { type:'text', content:'① ' },
    { type:'highlight', content:'NULL-9', color:'var(--blue)' },
    { type:'text', content:' on standby — DPS gap at 320. Bring online.\n\n② ' },
    { type:'highlight', content:'PHANTOM', color:'var(--purple)' },
    { type:'text', content:' crit synergy with SCOPE MK2 unequipped — install it for +12% crit.\n\n③ ' },
    { type:'highlight', content:'VERTEX', color:'var(--muted)' },
    { type:'text', content:' underleveled at LVL 6. Upgrade to 8 before next sector.' },
  ],
  'check integrity': [
    { type:'text', content:'Pulling live telemetry...' },
    { type:'pause', ms:500 },
    { type:'code', content:`SECTOR  : NEXUS-7 ALPHA\nINTEGRITY: ${Math.round(integrity)}% ↓\nETA PURGE: ~${Math.round((integrity/2.4))}m at current DPS\nAGENTS   : 5 active / 8 slots` },
    { type:'pause', ms:300 },
    { type:'text', content:'\n\n' },
    { type:'highlight', content:integrity < 40 ? '⚠ CRITICAL — breach imminent.' : '✓ Stable — no immediate action.', color: integrity < 40 ? 'var(--red)' : 'var(--green)' },
    { type:'text', content:' Enable AUTO mode to maintain pressure passively.' },
  ],
  'drop prediction': [
    { type:'text', content:'Calculating drop probability for this sector...' },
    { type:'pause', ms:900 },
    { type:'text', content:'\n\nDrop table (NEXUS-7):' },
    { type:'code', content:'VOLTCORE [EPIC]    — 4.2%\nBULWARK [LEGEND]   — 0.8%\nSURGE TOKEN        — 18.5%\nRANK SHARD ×5      — 12.1%\nMODULE CRATE       — 9.4%' },
    { type:'pause', ms:400 },
    { type:'text', content:'\n\nWith ' },
    { type:'stat', content:'3x', label:'BOOST' },
    { type:'text', content:' active, effective EPIC drop becomes ~12.6%. Recommend activating boost before next purge.' },
  ],
  'rank roadmap': [
    { type:'text', content:'Projecting rank trajectory...' },
    { type:'pause', ms:700 },
    { type:'text', content:'\n\nCurrent: ' },
    { type:'highlight', content:'WRAITH-III', color:'var(--amber)' },
    { type:'text', content:' · 82% to next\n\nMilestone gaps:\n\n' },
    { type:'code', content:'WRAITH-IV  → 5,200 XP  (≈2.1h AUTO)\nWRAITH-V   → 28,000 XP (≈11.4h)\nSHADOW-I   → 95,000 XP (≈38.8h)' },
    { type:'pause', ms:400 },
    { type:'text', content:'\n\nFastest path: keep AUTO on, equip ' },
    { type:'highlight', content:'SIGNAL AMP', color:'var(--blue)' },
    { type:'text', content:' (+8% XP) and clear 3 sectors per session.' },
  ],
  'module audit': [
    { type:'text', content:'Running module slot audit...' },
    { type:'pause', ms:600 },
    { type:'text', content:'\n\nEquipped: 4/6 slots\n' },
    { type:'code', content:'[1] VOLTCORE   +340 ATK  ✓\n[2] IRONPLATE  +180 DEF  ✓\n[3] PYREX      +580 DPS  ✓\n[4] SYN CORE   +200 HP   ✓\n[5] —          empty     ⚠\n[6] —          empty     ⚠' },
    { type:'pause', ms:300 },
    { type:'text', content:'\n\nSlot 5 recommendation: ' },
    { type:'highlight', content:'SCOPE MK2', color:'var(--blue)' },
    { type:'text', content:' (+12% CRIT).\nSlot 6 recommendation: ' },
    { type:'highlight', content:'BULWARK', color:'var(--amber)' },
    { type:'text', content:' (+420 DEF) if owned.' },
  ],
  'default': [
    { type:'text', content:'Processing query...' },
    { type:'pause', ms:700 },
    { type:'text', content:'\n\nI can help you with:\n\n• Sector analysis & breach timing\n• Agent formation optimization\n• Module slot efficiency\n• XP & rank roadmap\n• Drop rate predictions\n\nUse the quick prompts below or ask anything.' },
  ],
};

function getResponse(query) {
  const q = query.toLowerCase().trim();
  for (const key of Object.keys(AI_RESPONSES)) {
    if (key !== 'default' && q.includes(key)) return AI_RESPONSES[key];
  }
  if (q.includes('sector') || q.includes('nexus') || q.includes('breach')) return AI_RESPONSES['analyze sector'];
  if (q.includes('agent') || q.includes('deploy') || q.includes('squad')) return AI_RESPONSES['optimize agents'];
  if (q.includes('integr') || q.includes('health') || q.includes('hp')) return AI_RESPONSES['check integrity'];
  if (q.includes('drop') || q.includes('loot') || q.includes('farm')) return AI_RESPONSES['drop prediction'];
  if (q.includes('rank') || q.includes('xp') || q.includes('level') || q.includes('progress')) return AI_RESPONSES['rank roadmap'];
  if (q.includes('module') || q.includes('equip') || q.includes('slot')) return AI_RESPONSES['module audit'];
  return AI_RESPONSES['default'];
}

function nowTime() {
  const d = new Date();
  return d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0');
}

function appendMsg(role, html) {
  const feed = document.getElementById('chat-messages');
  if (!feed) return;
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  const avatarIcon = role === 'ai' ? '🧠' : '⬡';
  div.innerHTML = `
    <div class="msg-avatar">${avatarIcon}</div>
    <div>
      <div class="msg-bubble">${html}</div>
      <span class="msg-time">${nowTime()}</span>
    </div>
  `;
  feed.appendChild(div);
  feed.scrollTop = feed.scrollHeight;
}

function showTyping() {
  const feed = document.getElementById('chat-messages');
  if (!feed) return;
  const div = document.createElement('div');
  div.className = 'msg ai';
  div.id = 'typing-indicator';
  div.innerHTML = `
    <div class="msg-avatar">🧠</div>
    <div class="typing-dots">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  feed.appendChild(div);
  feed.scrollTop = feed.scrollHeight;
}

function removeTyping() {
  const t = document.getElementById('typing-indicator');
  if (t) t.remove();
}

async function streamResponse(tokens) {
  const feed = document.getElementById('chat-messages');
  if (!feed) return;

  const div = document.createElement('div');
  div.className = 'msg ai';
  div.innerHTML = `
    <div class="msg-avatar">🧠</div>
    <div>
      <div class="msg-bubble" id="stream-bubble"></div>
      <span class="msg-time">${nowTime()}</span>
    </div>
  `;
  feed.appendChild(div);
  feed.scrollTop = feed.scrollHeight;

  const bubble = document.getElementById('stream-bubble');
  if (!bubble) return;
  
  const cursor = document.createElement('span');
  cursor.className = 'stream-cursor';
  bubble.appendChild(cursor);

  for (const token of tokens) {
    if (!bubble) break;

    if (token.type === 'pause') {
      await sleep(token.ms);
      continue;
    }

    if (token.type === 'code') {
      const block = document.createElement('code');
      block.className = 'chat-code';
      bubble.insertBefore(block, cursor);
      await typeChars(block, token.content, 12);
      feed.scrollTop = feed.scrollHeight;
      continue;
    }

    if (token.type === 'highlight') {
      const span = document.createElement('span');
      span.style.color = token.color || 'var(--green)';
      span.style.fontWeight = '700';
      bubble.insertBefore(span, cursor);
      await typeChars(span, token.content, 22);
      feed.scrollTop = feed.scrollHeight;
      continue;
    }

    if (token.type === 'stat') {
      const span = document.createElement('span');
      span.className = 'chat-stat';
      span.innerHTML = `<span style="color:var(--green);font-weight:700">${token.content}</span><span style="color:var(--muted)">${token.label}</span>`;
      bubble.insertBefore(span, cursor);
      await sleep(80);
      feed.scrollTop = feed.scrollHeight;
      continue;
    }

    if (token.type === 'text') {
      await typeTextNode(bubble, cursor, token.content, 18);
      feed.scrollTop = feed.scrollHeight;
      continue;
    }
  }

  if (cursor.parentNode) cursor.remove();
  bubble.id = '';

  feed.scrollTop = feed.scrollHeight;
}

async function typeChars(container, text, speed) {
  for (const ch of text) {
    container.appendChild(document.createTextNode(ch));
    if (speed > 0) await sleep(speed + Math.random() * 8);
  }
}

async function typeTextNode(bubble, cursor, text, speed) {
  for (const ch of text) {
    if (ch === '\n') {
      bubble.insertBefore(document.createElement('br'), cursor);
    } else {
      bubble.insertBefore(document.createTextNode(ch), cursor);
    }
    if (speed > 0) await sleep(speed + Math.random() * 12);
  }
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function sendPrompt(query) {
  if (isStreaming || !query) return;
  isStreaming = true;
  TG.haptic('light');

  const sendBtn = document.getElementById('chat-send');
  const input = document.getElementById('chat-input');
  if (sendBtn) sendBtn.classList.add('disabled');

  appendMsg('user', query.replace(/</g,'&lt;'));
  if (input) { input.value = ''; autoResize(input); }

  const statusLine = document.getElementById('ai-status-line');
  if (statusLine) statusLine.textContent = 'PROCESSING QUERY...';

  await sleep(300);
  showTyping();
  await sleep(600 + Math.random() * 800);
  removeTyping();

  const tokens = getResponse(query);
  await streamResponse(tokens);

  isStreaming = false;
  if (sendBtn) sendBtn.classList.remove('disabled');
  if (statusLine) statusLine.textContent = 'SYSTEMS ONLINE · MONITORING';
  TG.haptic('success');
}

async function submitChat() {
  const input = document.getElementById('chat-input');
  const query = input?.value.trim();
  if (!query || isStreaming) return;
  await sendPrompt(query);
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    submitChat();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 80) + 'px';
}

function initAIConsole() {
  const feed = document.getElementById('chat-messages');
  if (!feed || feed.children.length > 0) return;

  setTimeout(async () => {
    const tokens = [
      { type:'text', content:`NEXUS-AI online. Welcome back, ${TG.username.toUpperCase()}.` },
      { type:'pause', ms:400 },
      { type:'text', content:'\n\nI have access to your sector telemetry, agent status, and module configuration. Use the prompts below or ask me anything.' },
    ];
    await streamResponse(tokens);
  }, 400);
}

// ═══════════════════════════════════════════
// STARTUP
// ═══════════════════════════════════════════

window.addEventListener('load', () => {
  renderAgents();
  renderModules();
  renderEvents();
  renderMilestones();
  renderUnlocks();
  renderInventory();
  
  fetchState();
  setInterval(fetchState, 5000);
  
  // Init AI Console if currently active
  if (document.getElementById('page-ai-console')?.style.display === 'flex') {
    initAIConsole();
  }
});