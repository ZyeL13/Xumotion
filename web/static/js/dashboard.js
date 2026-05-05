let currentTab = 'dashboard';

// Fetch state and render
async function fetchState() {
  try {
    const res = await fetch('/api/state');
    const data = await res.json();
    updateDashboard(data);
    updateAgents(data.player.agents, data.player.max_agent_slots, data.player.deployed_count);
    updateModules(data.player.inventory_count);
    updateProgression(data.player);
  } catch (e) {
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

  document.getElementById('credits-value').textContent = data.player.gold.toLocaleString();
  document.getElementById('shards-value').textContent = data.player.shards || 0;

  document.getElementById('stat-atk').textContent = data.player.atk;
  document.getElementById('stat-def').textContent = data.player.defense;
  document.getElementById('stat-hp').textContent = data.player.hp + '/' + data.player.max_hp;
  document.getElementById('stat-crit').textContent = (data.player.crit_rate * 100).toFixed(1) + '%';
}

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
          ? `<button class="btn-outline sm" onclick="sendCommand('undeploy ${a.id}')">UNDEPLOY</button>`
          : `<button class="btn-success sm" onclick="sendCommand('deploy ${a.id}')" ${deployedCount >= maxSlots ? 'disabled' : ''}>DEPLOY</button>`
        }
        <button class="btn-outline sm" onclick="sendCommand('ea ${a.id}')">UPGRADE</button>
      </div>
    </div>
  `).join('');
}

function updateModules(count) {
  document.getElementById('modules-count').textContent = count + ' modules in bay';
  // Detail module bisa ditambahkan nanti
}

function updateProgression(player) {
  document.getElementById('rank-value').textContent = player.level;
  const expPct = player.exp / (player.exp + 100) * 100; // perkiraan, butuh exp_needed dari API
  document.getElementById('exp-fill').style.width = Math.min(expPct, 100) + '%';
  document.getElementById('exp-text').textContent = player.exp + ' EXP';
}

async function sendCommand(cmd) {
  await fetch('/api/command', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: cmd})
  });
  fetchState();
}

// Tab switching
document.querySelectorAll('#bottom-nav .nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#bottom-nav .nav-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentTab = btn.dataset.tab;
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById('tab-' + currentTab).classList.remove('hidden');
  });
});

// Event feed via WebSocket
const ws = new WebSocket('ws://' + location.hostname + ':8081');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const feed = document.getElementById('event-list');
  const entry = document.createElement('div');
  entry.className = 'event-item';
  const time = new Date(data.timestamp * 1000).toLocaleTimeString();
  entry.innerHTML = `<span>${data.message}</span><span class="time">${time}</span>`;
  feed.prepend(entry);
  if (feed.children.length > 20) feed.removeChild(feed.lastChild);
  
  // dot notification
  document.getElementById('event-dot').classList.remove('hidden');
  setTimeout(() => document.getElementById('event-dot').classList.add('hidden'), 3000);
};

// Initial load
fetchState();
setInterval(fetchState, 3000);
