async function fetchState() {
    const res = await fetch('/api/state');
    const data = await res.json();
    document.getElementById('stage').textContent = data.stage;
    document.getElementById('rank').textContent = data.player.level;
    document.getElementById('entity-name').textContent = data.enemy.name;
    document.getElementById('entity-rarity').textContent = data.enemy.rarity;
    // ... update semua metric
    const hpPct = data.enemy.hp / data.enemy.max_hp * 100;
    document.getElementById('integrity-fill').style.width = hpPct + '%';
    document.getElementById('integrity-text').textContent = `${data.enemy.hp}/${data.enemy.max_hp}`;
}

async function sendCommand(cmd) {
    await fetch('/api/command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: cmd})
    });
    fetchState();
}

setInterval(fetchState, 2000);
fetchState();
