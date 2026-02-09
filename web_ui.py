"""Single-page web UI served as an HTML string constant."""

HTML_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zoom Translator</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f5; color: #333; padding: 2rem;
  }
  .container { max-width: 640px; margin: 0 auto; }
  h1 { font-size: 1.5rem; margin-bottom: 1.5rem; color: #1a1a2e; }
  .card {
    background: #fff; border-radius: 8px; padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.1); margin-bottom: 1.5rem;
  }
  label { display: block; font-weight: 600; margin-bottom: .4rem; font-size: .9rem; }
  input[type="text"], select {
    width: 100%; padding: .6rem .8rem; border: 1px solid #ddd;
    border-radius: 6px; font-size: .95rem; margin-bottom: 1rem;
  }
  input[type="text"]:focus, select:focus {
    outline: none; border-color: #4361ee;
  }
  .checkboxes { margin-bottom: 1rem; }
  .checkboxes label {
    display: inline-flex; align-items: center; font-weight: 400;
    margin-right: 1.5rem; cursor: pointer;
  }
  .checkboxes input { margin-right: .4rem; width: 16px; height: 16px; }
  button.primary {
    background: #4361ee; color: #fff; border: none; padding: .7rem 1.5rem;
    border-radius: 6px; font-size: .95rem; cursor: pointer; font-weight: 600;
  }
  button.primary:hover { background: #3a56d4; }
  button.primary:disabled { background: #aab; cursor: not-allowed; }
  button.stop {
    background: #e74c3c; color: #fff; border: none; padding: .35rem .8rem;
    border-radius: 4px; font-size: .8rem; cursor: pointer;
  }
  button.stop:hover { background: #c0392b; }
  .status-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    margin-right: .4rem;
  }
  .status-dot.in_call { background: #2ecc71; }
  .status-dot.starting { background: #f39c12; }
  .status-dot.stopped { background: #95a5a6; }
  .bot-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: .6rem 0; border-bottom: 1px solid #eee;
  }
  .bot-row:last-child { border-bottom: none; }
  .bot-info { font-size: .9rem; }
  .bot-id { color: #888; font-family: monospace; font-size: .8rem; }
  .empty { color: #999; font-size: .9rem; padding: .5rem 0; }
  #conn-status {
    font-size: .75rem; padding: .25rem .6rem; border-radius: 12px;
    display: inline-block; margin-bottom: 1rem;
  }
  #conn-status.connected { background: #d4edda; color: #155724; }
  #conn-status.disconnected { background: #f8d7da; color: #721c24; }
  .error-toast {
    background: #f8d7da; color: #721c24; padding: .6rem 1rem;
    border-radius: 6px; margin-bottom: .8rem; font-size: .85rem;
  }
</style>
</head>
<body>
<div class="container">
  <h1>Zoom Translator</h1>
  <div id="conn-status" class="disconnected">Disconnected</div>
  <div id="errors"></div>

  <div class="card">
    <label for="meeting-url">Zoom Meeting Link</label>
    <input type="text" id="meeting-url" placeholder="https://zoom.us/j/123456789?pwd=...">

    <label for="source-lang">Source Language</label>
    <select id="source-lang">
      <option value="en">English</option>
      <option value="de">German</option>
      <option value="es">Spanish</option>
      <option value="fr">French</option>
      <option value="pt">Portuguese</option>
    </select>

    <label>Target Languages</label>
    <div class="checkboxes">
      <label><input type="checkbox" name="target" value="es"> Spanish</label>
      <label><input type="checkbox" name="target" value="pt"> Portuguese</label>
      <label><input type="checkbox" name="target" value="en"> English</label>
      <label><input type="checkbox" name="target" value="de"> German</label>
      <label><input type="checkbox" name="target" value="fr"> French</label>
    </div>

    <button class="primary" id="start-btn" disabled>Start Translation</button>
  </div>

  <div class="card">
    <label>Active Bots</label>
    <div id="bot-list"><div class="empty">No active bots</div></div>
  </div>
</div>

<script>
(function() {
  const startBtn  = document.getElementById("start-btn");
  const urlInput  = document.getElementById("meeting-url");
  const sourceSel = document.getElementById("source-lang");
  const botList   = document.getElementById("bot-list");
  const connEl    = document.getElementById("conn-status");
  const errorsEl  = document.getElementById("errors");

  let ws = null;
  let reconnectTimer = null;

  function wsUrl() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    return proto + "//" + location.host + "/mgmt";
  }

  function connect() {
    if (ws && ws.readyState <= 1) return;
    ws = new WebSocket(wsUrl());

    ws.onopen = function() {
      connEl.textContent = "Connected";
      connEl.className = "connected";
      startBtn.disabled = false;
    };

    ws.onclose = function() {
      connEl.textContent = "Disconnected";
      connEl.className = "disconnected";
      startBtn.disabled = true;
      reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = function() { ws.close(); };

    ws.onmessage = function(ev) {
      var msg;
      try { msg = JSON.parse(ev.data); } catch(e) { return; }

      if (msg.type === "status") {
        renderBots(msg.bots);
      } else if (msg.type === "error") {
        showError(msg.message);
      }
    };
  }

  function showError(text) {
    var div = document.createElement("div");
    div.className = "error-toast";
    div.textContent = text;
    errorsEl.appendChild(div);
    setTimeout(function() { div.remove(); }, 6000);
  }

  function renderBots(bots) {
    if (!bots || bots.length === 0) {
      botList.innerHTML = '<div class="empty">No active bots</div>';
      return;
    }
    var html = "";
    for (var i = 0; i < bots.length; i++) {
      var b = bots[i];
      var shortId = b.bot_id.substring(0, 8);
      html += '<div class="bot-row">' +
        '<div class="bot-info">' +
          '<span class="status-dot ' + b.status + '"></span>' +
          '<strong>' + b.source_lang.toUpperCase() + ' &rarr; ' + b.target_lang.toUpperCase() + '</strong> ' +
          '<span class="bot-id">' + shortId + '</span> ' +
          '<span>' + b.status + '</span>' +
        '</div>' +
        '<button class="stop" data-id="' + b.bot_id + '">Stop</button>' +
      '</div>';
    }
    botList.innerHTML = html;

    var stopBtns = botList.querySelectorAll("button.stop");
    for (var j = 0; j < stopBtns.length; j++) {
      stopBtns[j].addEventListener("click", function() {
        var botId = this.getAttribute("data-id");
        ws.send(JSON.stringify({ action: "stop", bot_id: botId }));
      });
    }
  }

  startBtn.addEventListener("click", function() {
    var meetingUrl = urlInput.value.trim();
    if (!meetingUrl) { showError("Enter a Zoom meeting link"); return; }

    var checks = document.querySelectorAll('input[name="target"]:checked');
    var targets = [];
    for (var i = 0; i < checks.length; i++) targets.push(checks[i].value);
    if (targets.length === 0) { showError("Select at least one target language"); return; }

    ws.send(JSON.stringify({
      action: "start",
      meeting_url: meetingUrl,
      source_lang: sourceSel.value,
      target_langs: targets
    }));
  });

  connect();
})();
</script>
</body>
</html>
"""
