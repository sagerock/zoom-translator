"""Single-page web UI served as an HTML string constant.

Exports:
  HTML_PAGE   – management UI (admin starts/stops bots)
  LISTEN_PAGE – listener page (attendees hear translated audio)
"""

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
  button.copy-link {
    background: #6c757d; color: #fff; border: none; padding: .35rem .8rem;
    border-radius: 4px; font-size: .8rem; cursor: pointer; margin-right: .4rem;
  }
  button.copy-link:hover { background: #5a6268; }
  button.copy-link.copied { background: #2ecc71; }
  .listen-url {
    font-size: .75rem; color: #4361ee; font-family: monospace;
    word-break: break-all; margin-top: .3rem;
  }
  .dl-links { margin-top: .3rem; }
  .dl-links a {
    font-size: .75rem; color: #6c757d; margin-right: .8rem;
    text-decoration: none;
  }
  .dl-links a:hover { color: #4361ee; text-decoration: underline; }
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

  <div class="card">
    <label>Recordings</label>
    <div id="rec-list"><div class="empty">No recordings yet</div></div>
  </div>
</div>

<script>
(function() {
  const startBtn  = document.getElementById("start-btn");
  const urlInput  = document.getElementById("meeting-url");
  const sourceSel = document.getElementById("source-lang");
  const botList   = document.getElementById("bot-list");
  const recList   = document.getElementById("rec-list");
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

  function listenUrl(lang) {
    return location.protocol + "//" + location.host + "/listen?lang=" + lang;
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
      var url = listenUrl(b.target_lang);
      var recBase = "/recordings/" + b.bot_id + "/";
      var dlHtml = "";
      if (b.clip_count > 0) {
        dlHtml = '<div class="dl-links">' +
          '<a href="' + recBase + 'full_audio.mp3" download>Audio MP3</a>' +
          '<a href="' + recBase + 'subtitles.srt" download>Subtitles SRT</a>' +
          '<a href="' + recBase + 'transcript.jsonl" download>Transcript</a>' +
          '(' + b.clip_count + ' clips)' +
        '</div>';
      }
      html += '<div class="bot-row">' +
        '<div class="bot-info">' +
          '<span class="status-dot ' + b.status + '"></span>' +
          '<strong>' + b.source_lang.toUpperCase() + ' &rarr; ' + b.target_lang.toUpperCase() + '</strong> ' +
          '<span class="bot-id">' + shortId + '</span> ' +
          '<span>' + b.status + '</span>' +
          '<div class="listen-url">' + url + '</div>' +
          dlHtml +
        '</div>' +
        '<div>' +
          '<button class="copy-link" data-url="' + url + '">Copy Link</button>' +
          '<button class="stop" data-id="' + b.bot_id + '">Stop</button>' +
        '</div>' +
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

    var copyBtns = botList.querySelectorAll("button.copy-link");
    for (var k = 0; k < copyBtns.length; k++) {
      copyBtns[k].addEventListener("click", function() {
        var btn = this;
        navigator.clipboard.writeText(btn.getAttribute("data-url")).then(function() {
          btn.textContent = "Copied!";
          btn.classList.add("copied");
          setTimeout(function() { btn.textContent = "Copy Link"; btn.classList.remove("copied"); }, 2000);
        });
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

  function formatDuration(sec) {
    if (!sec) return "";
    var m = Math.floor(sec / 60);
    var s = Math.round(sec % 60);
    return m > 0 ? m + "m " + s + "s" : s + "s";
  }

  function loadRecordings() {
    fetch("/api/recordings").then(function(r) { return r.json(); }).then(function(recs) {
      if (!recs || recs.length === 0) {
        recList.innerHTML = '<div class="empty">No recordings yet</div>';
        return;
      }
      var html = "";
      for (var i = 0; i < recs.length; i++) {
        var r = recs[i];
        var base = "/recordings/" + r.bot_id + "/";
        var shortId = r.bot_id.substring(0, 8);
        var info = r.clips + " clips";
        if (r.duration) info += " &middot; " + formatDuration(r.duration);
        html += '<div class="bot-row">' +
          '<div class="bot-info">' +
            '<strong>' + shortId + '</strong> ' +
            '<span style="color:#888">' + info + '</span>' +
            '<div class="dl-links">' +
              '<a href="' + base + 'full_audio.mp3" download>Audio MP3</a>' +
              '<a href="' + base + 'subtitles.srt" download>Subtitles SRT</a>' +
              '<a href="' + base + 'transcript.jsonl" download>Transcript</a>' +
            '</div>' +
          '</div>' +
        '</div>';
      }
      recList.innerHTML = html;
    }).catch(function() {});
  }

  connect();
  loadRecordings();
  setInterval(loadRecordings, 15000);
})();
</script>
</body>
</html>
"""


LISTEN_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Translation Listener</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f5; color: #333;
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh;
  }
  .container { text-align: center; max-width: 400px; padding: 2rem; }
  h1 { font-size: 1.4rem; margin-bottom: .5rem; color: #1a1a2e; }
  .lang { font-size: 1.1rem; color: #4361ee; margin-bottom: 1.5rem; }
  .status-badge {
    display: inline-block; padding: .35rem 1rem; border-radius: 20px;
    font-size: .85rem; font-weight: 600; margin-bottom: 1.5rem;
  }
  .status-badge.connected { background: #d4edda; color: #155724; }
  .status-badge.disconnected { background: #f8d7da; color: #721c24; }
  .status-badge.connecting { background: #fff3cd; color: #856404; }
  .activity {
    font-size: .95rem; color: #666; min-height: 1.5rem;
  }
  .activity.playing { color: #2ecc71; font-weight: 600; }
  .subtitle {
    font-size: 1.15rem; font-weight: 600; color: #1a1a2e;
    margin-bottom: .4rem; min-height: 1.5rem;
  }
  .original {
    font-size: .85rem; color: #888; font-style: italic;
    margin-bottom: 1.2rem; min-height: 1.2rem;
  }
  .clip-count {
    font-size: .8rem; color: #999; margin-top: 1rem;
  }
  .start-btn {
    background: #4361ee; color: #fff; border: none; padding: .8rem 2rem;
    border-radius: 8px; font-size: 1.1rem; cursor: pointer; font-weight: 600;
    margin-bottom: 1.5rem;
  }
  .start-btn:hover { background: #3a56d4; }
  .hidden { display: none; }
</style>
</head>
<body>
<div class="container">
  <h1>Translation Listener</h1>
  <div class="lang" id="lang-label"></div>
  <button class="start-btn" id="start-btn">Start Listening</button>
  <div class="hidden" id="live-area">
    <div class="status-badge connecting" id="status">Connecting...</div>
    <div class="subtitle" id="subtitle"></div>
    <div class="original" id="original"></div>
    <div class="activity" id="activity">Waiting for translation...</div>
    <div class="clip-count" id="clip-count"></div>
  </div>
</div>

<script>
(function() {
  var LANG_NAMES = {
    en: "English", es: "Spanish", fr: "French",
    de: "German", pt: "Portuguese", ja: "Japanese", zh: "Chinese"
  };

  var params = new URLSearchParams(location.search);
  var lang = params.get("lang") || "";
  var langLabel = document.getElementById("lang-label");
  var startBtn = document.getElementById("start-btn");
  var liveArea = document.getElementById("live-area");
  var statusEl = document.getElementById("status");
  var subtitleEl = document.getElementById("subtitle");
  var originalEl = document.getElementById("original");
  var activityEl = document.getElementById("activity");
  var clipCountEl = document.getElementById("clip-count");

  langLabel.textContent = LANG_NAMES[lang] || lang.toUpperCase();

  if (!lang) {
    startBtn.classList.add("hidden");
    liveArea.classList.remove("hidden");
    statusEl.textContent = "Error";
    statusEl.className = "status-badge disconnected";
    activityEl.textContent = "Missing ?lang= parameter in URL";
    return;
  }

  var queue = [];
  var playing = false;
  var clipsPlayed = 0;

  function playNext() {
    if (queue.length === 0) {
      playing = false;
      activityEl.textContent = "Waiting for translation...";
      activityEl.className = "activity";
      return;
    }
    playing = true;
    activityEl.textContent = "Playing...";
    activityEl.className = "activity playing";

    var item = queue.shift();
    subtitleEl.textContent = item.translated;
    originalEl.textContent = item.original;

    var audio = new Audio("data:audio/mp3;base64," + item.mp3);
    audio.onended = function() {
      clipsPlayed++;
      clipCountEl.textContent = clipsPlayed + " clip" + (clipsPlayed === 1 ? "" : "s") + " played";
      playNext();
    };
    audio.onerror = function() {
      playNext();
    };
    audio.play().catch(function() {
      playNext();
    });
  }

  function enqueue(item) {
    queue.push(item);
    if (!playing) playNext();
  }

  var ws = null;
  var reconnectTimer = null;

  function wsUrl() {
    var proto = location.protocol === "https:" ? "wss:" : "ws:";
    return proto + "//" + location.host + "/listen?lang=" + encodeURIComponent(lang);
  }

  function connect() {
    if (ws && ws.readyState <= 1) return;
    ws = new WebSocket(wsUrl());

    ws.onopen = function() {
      statusEl.textContent = "Connected";
      statusEl.className = "status-badge connected";
    };

    ws.onclose = function() {
      statusEl.textContent = "Disconnected";
      statusEl.className = "status-badge disconnected";
      reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = function() { ws.close(); };

    ws.onmessage = function(ev) {
      var msg;
      try { msg = JSON.parse(ev.data); } catch(e) { return; }
      if (msg.type === "audio" && msg.mp3) {
        enqueue({mp3: msg.mp3, translated: msg.translated || "", original: msg.original || ""});
      }
    };
  }

  startBtn.addEventListener("click", function() {
    startBtn.classList.add("hidden");
    liveArea.classList.remove("hidden");
    connect();
  });
})();
</script>
</body>
</html>
"""
