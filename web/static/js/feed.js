const ws = new WebSocket('ws://' + location.hostname + ':8081');
const feed = document.getElementById('event-feed');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const entry = document.createElement('div');
    entry.className = 'event-entry';
    const time = new Date(data.timestamp * 1000).toLocaleTimeString();
    entry.innerHTML = `<span class="time">[${time}]</span> ${data.message}`;
    feed.prepend(entry);
    if (feed.children.length > 50) feed.removeChild(feed.lastChild);
};
