let currentTab = 'dashboard';
let clickCooldown = false;

const state = {
  credits: 0,
  shards: 0,
  atk: 0,
  def: 0,
  hp: 0,
  maxHp: 0,
  crit: 0,
};

// Operation stream helpers
function addOpLog(message, type = 'info') {
  const stream = document.getElementById('operation-stream');
  if (!stream) return;
  const entry = document.createElement('div');
  entry.className = `log-entry log-${type}`;
  const now = new Date();
  const time = now.toLocaleTimeString();
  entry.innerHTML = `<span>${message}</span><span class="time">${time}</span>`;
  stream.appendChild(entry);
  stream.scrollTop = stream.scrollHeight;
  // keep only last 30 entries
  while (stream.children.length > 30) stream.firstChild.remove();
}

function showNotification(text) {
  const el = document.createElement('div');
  el.className = 'notification';
  el.textContent = text;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

function showStatus(message, loading = false) {
  const bar = document.getElementById('status-bar');
  if (!bar) return;
  bar.classList.remove('hidden');
  bar.innerHTML = loading 
    ? `<span class="dots"></span> ${message}`
    : message;
  if (!loading) {
    setTimeout(() => bar.classList.add('hidden'), 2000);
  }
}

function hideStatus() {
  const bar = document.getElementById('status-bar');
  if (bar) bar.classList.add('hidden');
}

// Simulasi pemrosesan bertahap
async function simulateProcessing(steps, finalMessage) {
  for (let i = 0; i < steps.length; i++) {
    addOpLog(steps[i], 'info');
    showStatus(steps[i], true);
    await new Promise(r => setTimeout(r, 400 + Math.random() * 700));
  }
  hideStatus();
  if (finalMessage) {
    addOpLog(finalMessage, 'success');
    showNotification(finalMessage);
  }
}

// Mengirim perintah dengan feedback
async function sendCommand(cmd, buttonElement = null) {
  if (clickCooldown) return;
  clickCooldown = true;
  
  // Pressed state pada tombol
  if (buttonElement) {
    buttonElement.classList.add('btn-pressed');
    buttonElement.classList.add('btn-loading');
  }
  
  // Deretan log simulasi (bisa disesuaikan per command)
  const stepsMap = {
    'enhance': ['INITIALIZING MODULE...', 'VALIDATING RESOURCES...', 'APPLYING ENHANCEMENT...'],
    'deploy': ['INITIALIZING AGENT DEPLOYMENT...', 'ALLOCATING SLOTS...', 'DEPLOYING AGENT...'],
    'install': ['SCANNING MODULE BAY...', 'REBALANCING SLOTS...', 'INSTALLING OPTIMAL MODULES...'],
    'checkpoint': ['SYNCING CHECKPOINT...', 'WRITING TO ARCHIVE...', 'CHECKPOINT SAVED'],
    'recompile': ['PREPARING RECOMPILE...', 'RESETTING SYSTEMS...', 'APPLYING CORE MULTIPLIERS...'],
    'auto': ['TOGGLING AUTO-ENHANCE...'],
    'cycle': ['CLAIMING CYCLE DEPOSIT...'],
    'restore': ['RESTORING OPERATOR...'],
    'merge': ['INITIATING AGENT MERGE...', 'VALIDATING TIERS...', 'EXECUTING MERGE...'],
    'undeploy': ['RECALLING AGENT...', 'FREEING SLOT...'],
  };
  
  const commandBase = cmd.split(' ')[0];
  const steps = stepsMap[commandBase] || [`PROCESSING: ${cmd.toUpperCase()}...`];
  const finalMsg = `${cmd.toUpperCase()} COMPLETE`;
  
  await simulateProcessing(steps, finalMsg);
  
  // Kirim ke server
  try {
    await fetch('/api/command', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: cmd})
    });
  } catch(e) {
    addOpLog('COMMAND FAILED: network error', 'error');
  }
  
  // Refresh state
  fetchState();
  
  // Reset button
  if (buttonElement) {
    buttonElement.classList.remove('btn-loading', 'btn-pressed');
  }
  clickCooldown = false;
}

// Fungsi fetchState diperbaharui dengan animasi angka
let previousState = {};
async function fetchState() {
  try {
    const res = await fetch('/api/state');
    const data = await res.json();
    updateDashboard(data);
    updateAgents(data.player.agents, data.player.max_agent_slots, data.player.deployed_count);
    updateModules(data.player.inventory_count);
    updateProgression(data.player);
    previousState = data.player;
  } catch(e) {
    console.error(e);
  }
}

function updateDashboard(data) {
  document.getElementById('sector-name').textContent = data.stage;
  document.getElementById('entity-name').textContent = data.enemy.name;
  const hpPct = data.enemy.hp / data.enemy.max_hp * 100;
  document.getElementById('integrity-pct').textContent = Math.round(hpPct) + '%';
  document.getElementById('integrity-fill').style.width = hpPct + '%';
  document.getElementById('target-gold').textContent = data.enemy.reward_gold;
  document.getElementById('target-exp').textContent = data.enemy.reward_exp;

  animateValue('credits-value', previousState.gold || 0, data.player.gold);
  animateValue('shards-value', previousState.shards || 0, data.player.shards);
  
  document.getElementById('stat-atk').textContent = data.player.atk;
  document.getElementById('stat-def').textContent = data.player.defense;
  document.getElementById('stat-hp').textContent = data.player.hp + '/' + data.player.max_hp;
  document.getElementById('stat-crit').textContent = (data.player.crit_rate * 100).toFixed(1) + '%';
}

function animateValue(elementId, start, end) {
  const el = document.getElementById(elementId);
  if (!el || start === end) return;
  const duration = 500;
  const step = (end - start) / (duration / 16);
  let current = start;
  el.classList.add('counter-animate');
  const timer = setInterval(() => {
    current += step;
    if ((step > 0 && current >= end) || (step < 0 && current <= end)) {
      clearInterval(timer);
      current = end;
    }
    el.textContent = Math.round(current).toLocaleString();
  }, 16);
}

// Update agents dengan tombol yang melekatkan handler sendCommand
function updateAgents(agents, maxSlots, deployedCount) {
  const container = document.getElementById('agents-list');
  container.innerHTML = agents.map(a => `
    <div class="agent-card">
      <div class="agent-header">
        <div>
          <div class="agent-name">${a.name}</div>
          <div class="agent-tier">${a.tier.toUpperCase()} · Lvl ${a.level}</div>
        </div>
        <div class="agent-dps">DPS ${a.dps}</div>
      </div>
      <div class="agent-actions">
        ${a.deployed 
          ? `<button class="btn-outline sm undeploy-btn" data-agent="${a.id}">UNDEPLOY</button>`
          : `<button class="btn-success sm deploy-btn" data-agent="${a.id}" ${deployedCount >= maxSlots ? 'disabled' : ''}>DEPLOY</button>`
        }
        <button class="btn-outline sm ea-btn" data-agent="${a.id}">UPGRADE</button>
      </div>
    </div>
  `).join('');

  // Attach event listeners to agent action buttons
  document.querySelectorAll('.undeploy-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      sendCommand('undeploy ' + this.dataset.agent, this);
    });
  });
  document.querySelectorAll('.deploy-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      sendCommand('deploy ' + this.dataset.agent, this);
    });
  });
  document.querySelectorAll('.ea-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      sendCommand('ea ' + this.dataset.agent, this);
    });
  });
}

// Attach global click handlers for dashboard action buttons
function attachGlobalHandlers() {
  document.querySelectorAll('[data-command]').forEach(btn => {
    btn.addEventListener('click', function(e) {
      const cmd = this.dataset.command;
      sendCommand(cmd, this);
    });
  });
}

// Pastikan tombol2 di dashboard punya data-command (harus ditambahkan di HTML nanti)
// Untuk sekarang, kita panggil attachGlobalHandlers setiap kali fetchState selesai
// dan pastikan tombol di dashboard sudah memiliki atribut data-command.
// Di HTML, beri atribut: data-command="enhance atk" dll.

// Panggil attach di awal
window.addEventListener('load', () => {
  attachGlobalHandlers();
  fetchState();
  setInterval(fetchState, 5000);
});

// Override onClick di HTML? Lebih baik kita gunakan event delegation untuk tombol dashboard
document.addEventListener('click', function(e) {
  const btn = e.target.closest('button[data-command]');
  if (btn) {
    e.preventDefault();
    const cmd = btn.dataset.command;
    sendCommand(cmd, btn);
  }
});
