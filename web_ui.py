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
<title>SageRock AI</title>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:         #1a1e23;
    --bg-card:    #20262d;
    --bg-input:   #161b21;
    --border:     #2e3740;
    --border-warm:#3a3228;
    --sage:       #6B8F71;
    --sage-light: #7fa885;
    --sage-dark:  #546e5a;
    --stone:      #C4A882;
    --stone-dark: #a8906c;
    --cream:      #F5F0E8;
    --cream-dim:  #c8c2b8;
    --muted:      #7a8390;
    --danger:     #c0645a;
    --danger-dim: #a05550;
    --success:    #6B8F71;
    --shadow:     0 4px 24px rgba(0,0,0,.35);
    --shadow-sm:  0 2px 8px rgba(0,0,0,.25);
    --radius:     10px;
    --radius-sm:  6px;
  }

  html { scroll-behavior: smooth; }

  body {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    background: var(--bg);
    color: var(--cream);
    min-height: 100vh;
    line-height: 1.6;
  }

  /* ── Login Screen ─────────────────────────────────────────────────── */
  #login-screen {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background:
      radial-gradient(ellipse 80% 60% at 30% 20%, rgba(107,143,113,.12) 0%, transparent 60%),
      radial-gradient(ellipse 60% 50% at 70% 80%, rgba(196,168,130,.08) 0%, transparent 60%),
      var(--bg);
    animation: fadeIn .6s ease both;
  }

  .login-card {
    width: 100%;
    max-width: 380px;
    background: var(--bg-card);
    border: 1px solid var(--border-warm);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: var(--shadow), 0 0 0 1px rgba(196,168,130,.06);
  }

  .brand {
    text-align: center;
    margin-bottom: 2rem;
    letter-spacing: -.01em;
  }

  .brand-sage {
    font-family: "DM Serif Display", Georgia, serif;
    font-style: italic;
    font-size: 2.2rem;
    color: var(--cream);
  }

  .brand-rock {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    font-weight: 700;
    font-size: 2.2rem;
    color: var(--cream);
    letter-spacing: -.03em;
  }

  .brand-ai {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    font-weight: 600;
    font-size: 2.2rem;
    color: var(--sage);
  }

  .brand-tagline {
    display: block;
    font-size: .72rem;
    font-weight: 500;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--stone);
    margin-top: .3rem;
  }

  /* ── Brand inline (top bar) ─────────────────────────────────────── */
  .brand-inline .brand-sage { font-size: 1.3rem; }
  .brand-inline .brand-rock { font-size: 1.3rem; }
  .brand-inline .brand-ai   { font-size: 1.3rem; }

  /* ── Form Elements ─────────────────────────────────────────────── */
  label {
    display: block;
    font-weight: 600;
    font-size: .78rem;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: .45rem;
  }

  input[type="text"],
  input[type="email"],
  input[type="password"],
  select {
    width: 100%;
    padding: .65rem .9rem;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: inherit;
    font-size: .92rem;
    color: var(--cream);
    margin-bottom: 1rem;
    transition: border-color .2s, box-shadow .2s;
  }

  input[type="text"]:focus,
  input[type="email"]:focus,
  input[type="password"]:focus,
  select:focus {
    outline: none;
    border-color: var(--sage);
    box-shadow: 0 0 0 3px rgba(107,143,113,.18);
  }

  select option { background: var(--bg-card); }

  /* ── Buttons ─────────────────────────────────────────────────────── */
  button.primary {
    background: var(--sage);
    color: #fff;
    border: none;
    padding: .72rem 1.6rem;
    border-radius: var(--radius-sm);
    font-family: inherit;
    font-size: .92rem;
    font-weight: 600;
    cursor: pointer;
    transition: background .2s, transform .1s, box-shadow .2s;
    box-shadow: 0 2px 8px rgba(107,143,113,.3);
  }

  button.primary:hover {
    background: var(--sage-light);
    box-shadow: 0 4px 16px rgba(107,143,113,.35);
  }

  button.primary:active { transform: translateY(1px); }

  button.primary:disabled {
    background: var(--border);
    color: var(--muted);
    cursor: not-allowed;
    box-shadow: none;
  }

  button.secondary {
    background: transparent;
    color: var(--stone);
    border: 1px solid var(--stone-dark);
    padding: .72rem 1.6rem;
    border-radius: var(--radius-sm);
    font-family: inherit;
    font-size: .92rem;
    font-weight: 600;
    cursor: pointer;
    transition: background .2s, color .2s;
  }

  button.secondary:hover {
    background: rgba(196,168,130,.1);
    color: var(--cream);
  }

  button.stop {
    background: transparent;
    color: var(--danger);
    border: 1px solid rgba(192,100,90,.4);
    padding: .3rem .75rem;
    border-radius: 20px;
    font-family: inherit;
    font-size: .75rem;
    font-weight: 600;
    cursor: pointer;
    letter-spacing: .04em;
    transition: background .2s, color .2s;
  }

  button.stop:hover {
    background: rgba(192,100,90,.12);
    color: #e87068;
  }

  button.copy-link {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    padding: .3rem .75rem;
    border-radius: 20px;
    font-family: inherit;
    font-size: .75rem;
    font-weight: 500;
    cursor: pointer;
    margin-right: .4rem;
    transition: background .2s, color .2s, border-color .2s;
  }

  button.copy-link:hover {
    border-color: var(--sage-dark);
    color: var(--sage-light);
  }

  button.copy-link.copied {
    border-color: var(--sage);
    color: var(--sage-light);
    background: rgba(107,143,113,.1);
  }

  button.logout {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: .3rem .8rem;
    border-radius: 20px;
    font-family: inherit;
    font-size: .75rem;
    font-weight: 500;
    cursor: pointer;
    transition: border-color .2s, color .2s;
  }

  button.logout:hover {
    border-color: var(--stone-dark);
    color: var(--stone);
  }

  /* ── Cards ───────────────────────────────────────────────────────── */
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.6rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-sm);
    animation: slideUp .4s ease both;
  }

  .card-title {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 1rem;
    font-weight: 400;
    color: var(--cream-dim);
    letter-spacing: .01em;
    margin-bottom: 1.1rem;
    display: flex;
    align-items: center;
    gap: .5rem;
  }

  .card-title::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--border);
    margin-left: .25rem;
  }

  /* ── Main layout ─────────────────────────────────────────────────── */
  #main-app { display: none; }

  .app-header {
    position: sticky;
    top: 0;
    z-index: 10;
    background: rgba(26,30,35,.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: .85rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: .8rem;
  }

  .user-email {
    font-size: .78rem;
    color: var(--muted);
    font-weight: 500;
  }

  .container {
    max-width: 680px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }

  /* ── Connection status pill ──────────────────────────────────────── */
  #conn-status {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .05em;
    text-transform: uppercase;
    padding: .3rem .75rem;
    border-radius: 20px;
    margin-bottom: 1.25rem;
    transition: background .3s, color .3s;
  }

  #conn-status::before {
    content: "";
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  #conn-status.connected {
    background: rgba(107,143,113,.15);
    color: var(--sage-light);
    border: 1px solid rgba(107,143,113,.3);
  }

  #conn-status.connected::before { background: var(--sage-light); box-shadow: 0 0 6px var(--sage); }

  #conn-status.disconnected {
    background: rgba(192,100,90,.1);
    color: #c07070;
    border: 1px solid rgba(192,100,90,.25);
  }

  #conn-status.disconnected::before { background: var(--danger); }

  /* ── Mode segmented control ──────────────────────────────────────── */
  .mode-toggle {
    display: inline-flex;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 3px;
    margin-bottom: 1.2rem;
    gap: 2px;
  }

  .mode-toggle input[type="radio"] { display: none; }

  .mode-toggle label {
    display: inline-block;
    padding: .45rem 1.1rem;
    border-radius: 6px;
    font-size: .82rem;
    font-weight: 600;
    letter-spacing: .04em;
    text-transform: uppercase;
    color: var(--muted);
    cursor: pointer;
    margin-bottom: 0;
    transition: background .2s, color .2s;
    white-space: nowrap;
  }

  .mode-toggle input[type="radio"]:checked + label {
    background: var(--sage-dark);
    color: var(--cream);
    box-shadow: 0 1px 4px rgba(0,0,0,.3);
  }

  /* ── Checkboxes ──────────────────────────────────────────────────── */
  .checkboxes {
    display: flex;
    flex-wrap: wrap;
    gap: .4rem;
    margin-bottom: 1rem;
  }

  .checkboxes label {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    font-weight: 500;
    font-size: .82rem;
    letter-spacing: .02em;
    text-transform: none;
    color: var(--cream-dim);
    cursor: pointer;
    padding: .35rem .8rem;
    border: 1px solid var(--border);
    border-radius: 20px;
    transition: border-color .2s, color .2s, background .2s;
    margin-bottom: 0;
  }

  .checkboxes label:has(input:checked) {
    border-color: var(--sage-dark);
    color: var(--sage-light);
    background: rgba(107,143,113,.1);
  }

  .checkboxes input[type="checkbox"],
  .checkboxes input[type="radio"] {
    width: 14px;
    height: 14px;
    margin: 0;
    padding: 0;
    accent-color: var(--sage);
    flex-shrink: 0;
  }

  /* ── Bot/recording rows ──────────────────────────────────────────── */
  .bot-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: .75rem;
    padding: .85rem 0;
    border-bottom: 1px solid var(--border);
  }

  .bot-row:last-child { border-bottom: none; }

  .bot-info { font-size: .88rem; flex: 1; min-width: 0; }

  .bot-id {
    color: var(--muted);
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: .75rem;
  }

  .empty {
    color: var(--muted);
    font-size: .88rem;
    padding: .5rem 0;
    font-style: italic;
  }

  /* ── Status dot ──────────────────────────────────────────────────── */
  .status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: .4rem;
    vertical-align: middle;
  }

  .status-dot.in_call  { background: var(--sage-light); box-shadow: 0 0 5px var(--sage); }
  .status-dot.starting { background: var(--stone); box-shadow: 0 0 5px var(--stone-dark); }
  .status-dot.stopped  { background: var(--border); }

  /* ── Listen URL ──────────────────────────────────────────────────── */
  .listen-url {
    font-size: .72rem;
    color: var(--sage);
    font-family: "SF Mono", "Fira Code", monospace;
    word-break: break-all;
    margin-top: .3rem;
    opacity: .8;
  }

  /* ── Download links ──────────────────────────────────────────────── */
  .dl-links { margin-top: .4rem; display: flex; flex-wrap: wrap; gap: .1rem; }

  .dl-links a {
    font-size: .75rem;
    color: var(--muted);
    text-decoration: none;
    padding: .2rem .55rem;
    border-radius: 4px;
    transition: color .2s, background .2s;
    font-weight: 500;
  }

  .dl-links a:hover {
    color: var(--stone);
    background: rgba(196,168,130,.08);
    text-decoration: none;
  }

  .dl-links a + a::before {
    content: "·";
    color: var(--border);
    margin-right: .1rem;
  }

  /* ── Error toast ─────────────────────────────────────────────────── */
  .error-toast {
    background: rgba(192,100,90,.12);
    border: 1px solid rgba(192,100,90,.3);
    color: #e08080;
    padding: .6rem 1rem;
    border-radius: var(--radius-sm);
    margin-bottom: .8rem;
    font-size: .85rem;
    animation: slideUp .2s ease;
  }

  /* ── Auth error ──────────────────────────────────────────────────── */
  .auth-error {
    background: rgba(192,100,90,.12);
    border: 1px solid rgba(192,100,90,.25);
    color: #e08080;
    padding: .5rem .85rem;
    border-radius: var(--radius-sm);
    margin-bottom: .9rem;
    font-size: .84rem;
    display: none;
  }

  /* ── Auth buttons ────────────────────────────────────────────────── */
  .auth-buttons { display: flex; gap: .8rem; margin-top: .25rem; }
  .auth-buttons button { flex: 1; }

  /* ── Forgot link ─────────────────────────────────────────────────── */
  .forgot-wrap {
    text-align: center;
    margin-top: 1rem;
  }

  .forgot-wrap a {
    font-size: .8rem;
    color: var(--muted);
    text-decoration: none;
    transition: color .2s;
  }

  .forgot-wrap a:hover { color: var(--stone); }

  #reset-msg {
    text-align: center;
    font-size: .82rem;
    color: var(--sage-light);
    margin-top: .6rem;
    display: none;
  }

  /* ── Admin section ───────────────────────────────────────────────── */
  .admin-card-dashboard { border-color: rgba(107,143,113,.3); }
  .admin-card-users     { border-color: rgba(196,168,130,.25); }
  .admin-card-sessions  { border-color: rgba(192,100,90,.25); }

  .admin-title-dashboard { color: var(--sage-light); }
  .admin-title-users     { color: var(--stone); }
  .admin-title-sessions  { color: #c07070; }

  .admin-add-row {
    display: flex;
    gap: .6rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .admin-add-row input {
    flex: 1;
    min-width: 140px;
    margin-bottom: 0;
  }

  /* ── Dashboard stats grid ────────────────────────────────────────── */
  .stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
    gap: .75rem;
    margin: .5rem 0 1rem;
  }

  .stat-tile {
    text-align: center;
    padding: .9rem .6rem;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
  }

  .stat-value {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 1.7rem;
    line-height: 1;
    margin-bottom: .25rem;
  }

  .stat-label {
    font-size: .68rem;
    font-weight: 600;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .stat-sage    { color: var(--sage-light); }
  .stat-stone   { color: var(--stone); }
  .stat-cream   { color: var(--cream-dim); }
  .stat-danger  { color: #c07070; }
  .stat-purple  { color: #9b84c2; }

  /* ── Dashboard service line ──────────────────────────────────────── */
  .service-line {
    font-size: .78rem;
    color: var(--muted);
    line-height: 1.7;
    margin-top: .4rem;
    display: flex;
    flex-wrap: wrap;
    gap: .3rem .6rem;
  }

  .service-line span { white-space: nowrap; }

  /* ── Dashboard user table ────────────────────────────────────────── */
  .dash-table {
    width: 100%;
    margin-top: 1rem;
    font-size: .8rem;
    border-collapse: collapse;
  }

  .dash-table th {
    text-align: left;
    padding: .4rem .5rem;
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
  }

  .dash-table th:not(:first-child) { text-align: right; }

  .dash-table td {
    padding: .45rem .5rem;
    border-bottom: 1px solid rgba(46,55,64,.5);
    color: var(--cream-dim);
  }

  .dash-table td:not(:first-child) { text-align: right; }

  .dash-table tr:last-child td { border-bottom: none; }

  /* ── User management table ───────────────────────────────────────── */
  .user-table {
    width: 100%;
    border-collapse: collapse;
    font-size: .85rem;
  }

  .user-table th {
    text-align: left;
    padding: .4rem .4rem;
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
  }

  .user-table td {
    padding: .55rem .4rem;
    border-bottom: 1px solid rgba(46,55,64,.5);
    color: var(--cream-dim);
  }

  .user-table tr:last-child td { border-bottom: none; }

  /* ── Animations ──────────────────────────────────────────────────── */
  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .card:nth-child(1) { animation-delay: .05s; }
  .card:nth-child(2) { animation-delay: .10s; }
  .card:nth-child(3) { animation-delay: .15s; }
  .card:nth-child(4) { animation-delay: .20s; }

  /* ── Cost/revenue inline ─────────────────────────────────────────── */
  .cost-green   { color: var(--sage-light); }
  .cost-blue    { color: #6aacdb; }
  .cost-purple  { color: #9b84c2; }
  .owner-tag    { color: var(--danger); font-size: .72rem; }

  /* ── Start button full-width ─────────────────────────────────────── */
  #start-btn { width: 100%; margin-top: .25rem; }
</style>
</head>
<body>

<!-- Login Screen -->
<div id="login-screen">
  <div class="login-card">
    <div class="brand">
      <img src="data:image/png;base64,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" alt="SageRock AI" style="height:48px;">
      <span class="brand-tagline">Meeting Intelligence</span>
    </div>
    <div class="auth-error" id="auth-error"></div>
    <label for="auth-email">Email</label>
    <input type="email" id="auth-email" placeholder="you@example.com">
    <label for="auth-password">Password</label>
    <input type="password" id="auth-password" placeholder="Password">
    <div class="auth-buttons">
      <button class="primary" id="signin-btn">Sign In</button>
    </div>
    <div class="forgot-wrap">
      <a href="#" id="forgot-link">Forgot password?</a>
    </div>
    <div id="reset-msg"></div>
  </div>
</div>

<!-- Main App (hidden until authenticated) -->
<div id="main-app">
  <header class="app-header">
    <div class="brand brand-inline">
      <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAV4AAABaCAYAAADwzT64AAABS2lUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzggNzkuMTU5ODI0LCAyMDE2LzA5LzE0LTAxOjA5OjAxICAgICAgICAiPgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIi8+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgo8P3hwYWNrZXQgZW5kPSJyIj8+IEmuOgAAIABJREFUeJztvXmwJNV95/s55+RS2117oxskGmiEQCbcNNsgISHkZiwkS29GM932eIRkhAQzenJ4iYmACL959iyKoCde+MmWR3qNBcgSRpi2nkeIFthgCbTR0CwSAglBi2ZtaPr2XWrNysyTZ/7IzLp169btW3fv252fiIy6S1Wekycrv/nL3/md3w8yMjIyMjIyMjIyTmRE+oMxZiX7AcBvX3t5MTL+eUqpc9yctcW27c1B0DjNGLPBoNcYY/qBvJQSKWVDSlnWzcZRrfVhrfVrxpiXlFIHHMf5peM4P9/9hUdqK31MGRkZK4cQYvY3rQArLrzX/p8fvExKeZmUXAJsi4x/dhiGBKFHGIbk83bcUWkQQrS2Vr+DJkopLMtCSkkURfi+j+/7LwR+9GQY8pilco/c9Tf7H1mRA8zIyFgxMuFt499du+3SXM65ynXdD2jVuMIYI42Ju2KitEsSgHq90SG2BmMmt4FiiSiK0LqJ1prIBMn7Y6F2HIcoiqIg0A97jeC7xogH9nztl48u28FmZGSsGCe98H72Dz9UqDcqHzUEH7Ft+8O2rQaUUpS9kUREk64YiZQSIRRCCCzLbu0jfl+EMYYoil/ztoPWmjD0iKIIhMayLGxboZSiUqngui6um0dg4fvhhN/Ue6Mo+rYQ9j1/s3tffUkPPCMjY8U4aYX3kzdcUjKEOyDaYVnW1bZto5QiikBrTV0fRkqJUgopbIRQRFqidUSkJa7rTrFwEVGy5/g1qKnk8wKpDEIYDAFRpDHG0NdXRGtNEGh83yeKIpR0cBwHxyncNzo6usd1Cnu++v89Wl2SAcjIyFgxTkrh/e1PbNvR15//eGSCjxqjSSbFEj9sSBAEDG5QiatAE2lBFAHGAgQCe4roGmNavl4pQUoJfq7lWkBoIMIQtCzjRqOW+IAdbNtGCEGkBUEQEIYwODiI1wju8RrhHXfevn/Pog9CRkbGinFSCe/v/YfLLrIsPhXq5rXKMrkp/zQSsCBxLQRyPBkcmbxBxsIq4skyEIRhSBBotI7F23EcXDe2nCsjmlwuR6h9hNCU+vL4QZ1arZpYy7qjdxKMav2Wy9vU63WksD3X6b+9XvNv++ruHz2+aIORkZGxYpw0wnvNp999Q6Ho3GBMcEG9UcHNqalv6BBebZWTf8ikD5PCK4QgDDX5fB6QaK1RSqG1ptGoEYYhxsvT19eHjgKCoEGh6CKkxvMaGGOw7Y72O4RXyIhGo4GSDq7TT6MePFWv6d3//12P716UAcnIyFgxTnjh/fhntm4xxvy+41ifC8NQGqNxXbftHXLqayK8whFEUURkwqQPOnYdJC6FMIgYGlpL0wsol2tI4WAiRRiG5HJFVERs+VbHaXgV+vsL9A8UQYSEYZNQ+0m7UUc/YsIwJPANUkryuRJSWjTqfhQE5q+kcL74t7ftO7CggcnIyFgxTmjhveYz2650c84fl0ql3/J9j7GxMYQwDA0N4Xle8q7uwusUnVj8wiZRFCFEFLsYROyjxUiKxX7GRieYmKiyZngDp2w4jU2bNrF581lYJhbu0bEjvPzKr3j99ZepVMeRKiKfdzCkrobuwiuEIPDjKAnbypHLFbCUSxAYvEZ4b3mi8eff/Mb+7817cDIyMlaME1Z4P/MHW3cGQXCjMWabZbkopTCRInUZaN3pYw2n/FbsX4fv+3jNGjpqIpVOfLtREoHgEviSek0zPLiRiy96H79+/iWceca5DA8MowM/njQj5JXXX+QHP3yQRx/7EaPjb6AUWI6O2xQRoNuiImKUiOOAg7BBEAQoJbHtOIQtDEMcO/9kvaZ33XnbU3fPa4AyMjJWjBNSeK/5zCXXufnmnyilzgjDEM+LFy/k3BJCKHzfx7Ksjk9NFd7BNZtoNBrUG5WW8MbhZiFaa2wrz8S4x+DABt77nu28/4qreduGLUDsxlCA1/TIuQoIaQTjPP2zJ3no+//IY489wuBwnmMJr9G5xMKO24ui+EYRiz8UC/0EvjxYr4Wf//pXfnzrnAcpIyNjxThehbdTFXtm5yfPu6GvL/+n1Vp5Y7FYxHFygKLpafymRimJFHYymQYQL26YFMBYgC3LQcoASMU/Ir4fRBgTRzIo6fDOc87nve+5mrdteBfgokNo1GGgAH7NxatC/wDkrUEu3XYa9YrNgV8eIQrrIJsgAmIBnup6EFjoMEIqheMoEAFRFCBkiGVZeM0xlCycYdniv/3utZdad97+aDbplpGRsSDk7G+ZzjWfueS6vr6+PwU2lkolwjCkXC7j+z6u61IoFHAcp4u126UDUs54VzLGEAQB+Xyed7zjHWw+dTMAjUaEUlAqgTHQ3w+DgxBF0GjEIr5161Y+9KEPzdp+HDEBzWaTZrOJ7/uxBV6v02jEy5UbjQaWZW1cs2bNn37iut+4rrdRysjIyOjOnIX3P/zxhTsLpfBP6t6RjdIKCI2FsPLY+SLKddAyxIuqNE2FQNTQqpFsTbQM0QK0UGhcNC5epcHmU09Hhg4qLFJyhqmNBSidp2ANQrPIKYPn8OtnX4ViGGVcbGFQIkCIJi2jWhD7dJUNkcXQwClcfvnlbNg4yETlVVDjFPoiDB5KKYiKEBWpNusYS2Dl8qDyGNGH5azDsjdgGCbQRUJj42mfeji+MbRG/2TndefvXIJzkZGRcZIwJ+G95vrzr/Q870YhxBn9/f2LEvtbr9dxHIdSqYTW8TJfx3ESf2tEGIb09fVRLBaB2MJN/a9CxCvdPC9EaxACZNsROY7D0NAQUsrWJF+a40FK2VP/43wRFrZtY9s2+Xz+DNu2b7zuD9995YIPPiMj46SkZ+H9+Kcv3GJZ1h+HYbTN90Ncp0ik5+WpmEK5XMZ1XdasHSIyIVobXNcm1E0QmlDXGV7bx8BQvADOGFBKADYCBwxJFEWMEGCIN0vZbFi/EaXslqinr1LRFmo2M0KIOFIjcXskGc+2eZ73xzuvO3/LggcgIyPjpKNn5TTG/H5fX99v2bbd8ocuxoyh7/sIIVi/fj1KKTzPw7bjHA3pKrVSqYSjnCTOd6pVKyW4rkC1LVDTmtbn+/r6sCyrZemmr0KInize1DqOooharYbnxa6KXC73W5Zl/f6CByAjI+Okoyfh/eQNl9yQy6vPRRG4TgElHRr1CCnyC+6AkIZ6o8qGDRsYHh7G87x4ybCKsGxANgl1DYMHookQxOZslGwmEeLUzAUsC6QQKEu2bhBSWMSRYjLOYGY0k4sqZiaKIizLwnEcpJTxMmVjUrfD5675zCU3LHgQMjIyTipmFd7fu+F9FxUKhRu01nJ8PE5ok8/nW4/gC8VxHN566y3WrVvH5s2b4+XDUdTat23bjI2NMVYea1nYUYdexhZu/HO7Ee55HocOHQLAsqxWrodUQKWc/b6TJubJ5/MUi0Vc122vciELhcINv33NpRcteCAyMjJOGmZVHjcXfcrgXxBFYRJXazCRhaVclHQW3AHLNhw69BpDg2s45x3nYikXrWNR930f25YcPvIiR46+gsADERGGk0IbBLHFK2Ri8Ari90R1Xn75IC+9/CLGCGzbRWszKby6iVS9Ta7F2dECpJStELkwjBdcGFG5wClUPrXggcjIyDhpOKbwXvPpf7EDuDb1u/b19aG1ptlsHjP+di4IIRgbG6NQKLBp06aWfxcgCAIsy2J8fJyJiYnWZ6JoUnjjvLzpviat4bGxMQ4ePMhbb72FMabl5037HfuLZ++/lBLP86hUKnie1/qcUgrHcfA8j4GBgWt/91MX7FjwYGRkZJwUzCi813zmkpK0mh8Po1pOWXHlhyCIowBSEWs0GgvuQLHoUizl2LdvP+edez7vvuxKKhMaSxaxVI41a9ZQqY7w05/toxGOAlVyBZAKEOCHDZAQEVKpTaCsAKjzwq9+yr3f+SbFYg7XdWk2fWTyIT/wcBzZcmukoWWpVVsqlbBtm2q1ita6FVKWWsvpJF0URdhORNMv50r96uM7P/HrpQUPSEZGxgnPjMIrpdwBfHSpOxAlJmq1WsXB4dxzz2VgYIBKpUIul+PNN99Ea83TTz/NQw891Pqc5xm0jleepVEWfX19ABx48QCPPfYYo6Ojs7avlJoyYeb7PiMjI/i+z/r16ykUCuRyORzHQSk1rdKxbdt4nocx5qOFQiGzejMyMmalq/Be99n3FSzb7Jgy629k8nYJaZkdMXsc7GxEJgQiJsYrQJ6t57+XM0//dYJmDh3YFItFSqUSR0Ze4dH9/8xzv9pPxCjSLqOsBlDGdWvk803gKL848APuvf8OnnthP8Nr8nGehvbEPEa2HUs06atNwsby+TyFQgFjDOVyuSW8tm23JuNSV0hcgkgRBCFahxRLzo7fu+E9hQUPSkZGxglNV+GdmJj4qG3bVy9XJ6IoauXtHSgOsHXrVjZu3Mjo6GgrikApxWuvvca3vvUt9j26j2aziTaaht8giALGymM89MOHuPvuu9m3bx9jY2M9tV2pVCgWiwwNDbWs3SAI6O/vZ/369QAt10K6mi6NA06jI2zbTqMfrq7Vakv+lJCRkbG66ZrFRsjgI0LEZXjiwpMwqdGJ9diydhc2wSYERKaJMYJ601BwS5z/rss4fPgNvvm/XsbzAly3gG1HTEy8zv4nRxk5+gbP/Hx/HN6Vg1q9zOuvv85LLx9gYmIMyxE4jsQPx2Jf8JQGo+SY4uPZuHEj1WqVw4fjasfr1q1rLeZoNBpMTEy0RDdddpy6GaSUeA1DsTBMvV4nCJq4eT4C3LWgQcnIyDihmWbx/u61l15aLBY/nMa8LgfpBJfneQQ64NSNp3LRRRexZcsWqtVqK25YSsng4CCHDh3innvu4Tvf+Q579+7l29/+Nvv376dWq1EqlVo+2f7+/lnbrtfrLat327ZtXHbZZaxbt47x8XFeffVVGo1G3K8gaFm7KekS5LR6cRAEFIvFD//OJy+5dCnHqxttfuftwM1MLilJt8eBG4Ghdj/1QrZkf53tLOb+d8zQhgHuBm5c5L7Ptp25yPu+eSHH0KXd7Unbo13aemAJzv+xzs9u4PrFPD+zvP+BLmN73DJNeIXUV5VKpQHfD7EsJy4MaVRcqsck1YBFBMKPtwWSTq4ZI8DYCJMDXM48411c/cH/A9fpY2xslEp1lELRZnhNnqE1OQaGbNy8JtDj5Aqa9afk2XBKP25eU6uPUq4eoRmUkzy8ybmY4t+NGR8fZ9u2bezcuZPzzjuPQ4cO8ZOf/ITDhw+3ojdgMmdDOsGW9t22ijQ9g6Vy6TLlASH9qxY8MHPEGDNkjLmbyQuskwuJv4yjxphu/58PF3b52/aF7tQYc6Yx5gFicZ3pAtoB3GxiVuuk5o1MHsO8z0ly7h8gPvc3A0Nd3pbekEeNMdfPt62kvTONMY9z7PNzPbDbGPMrY0y378miYYzZztTv3RiwaynbXCjThVeID7ium5TBWXqLNxW2dGluukAh7+R573vfy4UXXojvxwJfKBQ4dOgQ1WqV9evXI2Vcpift79jYGM1mk/7+fgqFArVabdb2d+zYwW/+5m+Sz+d5+OGHeeihh/B9n6GhoVZSHCllS3RT4TXGYIzBdV3q9Xor1CwJP/vA0o3YjDxALEa9cPMiiW+3C2pBF5kxZoj4WOYi4HevYvFNuTkRzzmRjNfjzG28ds/3/Ledn17P85nAA8aYM+fTXo90HsseYvE9bpkivNf94XsuKwyKKyYaI6i8xovKSR5djZbEmwCN1cqni3EWtEWRwbKS7GGEYCRGS4j6ybGFnR/5M37jPZ9Fhpt587WQUnGIUqlApXoEHdUIzTiBLqNNFSPq6KhO0y8TBHHOh0K+hN801CqaelUxNmIIGv2855KP8fk/+wrbr3ofP//FT7jr777GyNFDnL55I1KFjI0fJpeXKEsjZIChiY4ahLpOZDwQPkIGSbXjHDpqEmoPrzlBocQVf3DTlZct43m8kekXwi5gJzAM3AQ80fmZhVwMyQXY7fMLvcBu7rKPPcBNIn7U2El8PC92vGd30qd5I2ans8157Tvp/01MF4ft8xDEGceL+NxfRffxunmelmi39m5h+vlpZ4juT2ELJvkOd950jmtrFzom17TWlxlC2euqrsUitXbbMSaeeNu0aRPbt2/Hchs88dQPePPwSwgh6O/vj+N96/XEz5P6XiczkEWR4IUXXmDN8CYGBgYY6N/Atgsu5r2Xb6e/b5g333yTPXfdxvPPP8/hw4cpFovkcjmEENi2jWVZhGE4vcMdGGNAkFjCYIyRWuvLgEcWf7S60vnouFMIsaft913AruTxML3Yhogt5Pl+SWeysObtakguos5j2SWEaF3I6XEZY/YQW3qp2KbHc8t8218uhBC7AIwxtzDderyRHs/JDON1U7r/hAeBB5O2HmeqaN5ILJQ9kdzYej0/TxAfW8r1xpibhBCLbYl2CvqDTL/JHHdMUTtjzCVpXKvtqEVJdD4bQkRo7ZPLS4QMQYQIaaFDklSPks1vP4d/+7FBNm08jcef2MehQ4eoVCq8OlJhw6nDhGGI7wWEIUQ6rvVmWRZSOmw7/xLe+c53suXsszj11FM5fePbAPj+voe46667eKv8AkEQUCgUKBaLSCl7TpIOkxOD8bGIlhvC9/1LlmjIOrmQqRfTEx2i285NTL0YFiK8M1m2Q8aYC4UQnRZ2L3S6C8baL+p2hBAvJmLSfuFtZxUIb4oQYswY03lO5jJ+08aLGY4/aesWpvpkdxhjhuYghp2iO6MvVQjxYCK+7TeV62d6/3yY4cazKs5/S3h3fmpbsVhyt4U6maknFt7lsHuFEK1KESlRFAvv+HiZwcE8pXyJ7R/YztnvOIOXXnqJ5557jgMHDjBePdjKn1AsFhgaXMcpG05l48aNDAys4Zx3vJOBgQGG+2LD6GjlCPfffz8//OH3OXToEEMbS63lwFEUEQRBa5lwL9YukMT1xj+3LT/e9qn/eEXxti8/PLujeWF0CuCMF1FyMYwxaSVeOMcLr532C6p9n2mf5iO8nY++D87y/k7LZkkncZaCLucE4htIL+M3bbxmOZfdxnM7sWuiF+baXqfwLsgV1IVOa/dFej+WFaUlvFLK85RSZxsUQRC0Jo+W2uMQRRGu67Jp08Yk2U0AWK0kOAOtkLAikiJnnDbMGaddzMUX1CmXyzT162itCQPAuOTcIn2ltfT3DWLbNpEJkcIADQ69dZB/evBbfO/h+2l4ZU4/cy3lRgWtNb7vEwRxoUzLshBCTLFmj4WJ/Qudx3V2FAbnAfsXZ6RmZK5f5geZainN5cJrp92l8GDye0vQ57nPzpvIbI+Mnf9fygmcpaRTeHulUwiPOV5CiCe6PMnNZcw625vthr1kN8YZ3B6rwtqFNuG1LOuc5LU1O9+L6CwUrTXFYpG3ve1tcYkdYis7FXwhIAwj/KAe1z2z4kiLUrFEqVgiQCCRKFzABVTyGvddCgloXnjxBe7/x2/xk6cfwRhDX18fY2NjiLZkOUqplm83FePZxiCtTpFa3VIm7oZIIIQ4h6UX3s4v/2xf7vaLYV7+sOQRr10oniC+gNO25+vnneuFfaLwIlMFsFcR7vlpp+M97fufi+DP9ca4lHRze6w+4ZVSbgmCADcnEzEJ4wmvJXbz6sCllH87p248CylcgsDgWJPCG89bSfK5AYQArQ2NRgMTxUUxjRjCSAnKQkk3Dtc1ECUWu2XBz597mr33fZNHHn2QZjDOKZv6yBcsjIhQTr5l4aeJcNJVar1MMLYLbyzScfgZSiGMWo6abJ1f/iFjzI5j+Hkf5Nh+4F7oZmk92Pb3VffIv8J0it+sArqACI6FCO9xQXLsnW6GW1hFN+qW8BpjNge+j5uLk8HoMKk1tvA8OMckdTUM9g9ijCDUGqypFq9KUkDGv8e+3JYkiqQIJnFy8kjHNw5lxZbnm4cPcf/99/PjH/+Y/sE+Nq/bwOj4q7z11ij9/f3xxJzvT0l8k7ocbNuetf/t4pzuQ0qJQEEkNy9weHqhm9Wx2xjzRLfwJyHEbH7TXujmi51iDc11gm0+oW3JsSxf+M3SMR8XybIK5hLH4c6V65l+/KvG2oU24XVd9zT8sLU81s25sdXXPZ1Dz8S5cJv4vt+axEotzHw+T63s8i8/8O9RDINwsXJ2rKKCrpfUlCd/A03PxnXBRBBFPo4LEFCtjyGtgP/7v36WyDQYWmuIqDA6fhQpDf39JaSEUMeWbju9CG5K6pKRKv2MiSfljAA4bS5jNU/GiP2p7X7bIeBxY8xV84wumI0pE2vJjHmnoPc6QXRSk8TSdorIcR8OtVLMYO3uYZWNWUvGjDEbIE11KNvXQC+ItGpDoVBo5bu1LItcLkelUuGss85iaGj6zbuzrtpMuG5yIDK2NOuNOgC1Wo077rhjWjax9NjSjGNLzIalbiChW4hOKr4LXsLbhXbhTcX1RJnoWm52d/nbYjyVrDhCiF0dC1AWYyn9Dla5tQtThXcNTApvujx2oRhjWonGUzFPJ/A8z+PiC67mlHVbgAJRlFiNAgwhoY7aLN9o+tZ+XxAgVYARFSZqL/P4T7/DP333DiJ5GKxRUONI1UTKxGltHCK9MGu+B9YsdQMJTzB9tVDKAwtdm99OFwvtCYjjRJlq4WZ+3mNgjLmxY0FLyi1LsMjgRKLT2n1ikdxny0pLeKMo6m+3CherpprjOBhjWmV0crkcjUaDWq3Ghg0b2Lp1K2vWxPrUHjerVG8LOKIo3prNJlJIirkijz76KPfdd18cTrayFu/s6dEWiWS10kziO++1+V04VghT+88XLnQJ73JjZqabVbqgfRMvZOg2lsf9cteVIjEgui1XXnW0e0zzqUW6mMuFoyhqCaBIMnyNjIygtebyyy/n9LdvibOgITFGk1qzSmmUpYnz/4ZMWrppt9MKlyFGeLhuBDR4+dBzfP+H/8jBl55n/YahtuxkbRU0jD25LS35pW6gnVnE9+bFEBCmf/GfmOFnyKzeufAEcNVC8kGcBMyUdW/V0RLeTtFNF1AslGaziW3bFAoFhBA0m00sy+LMM8/kiiuuoFQqtdrrjJmNY3BnOYDEigUYr4yzd+9efvWrXzE4OIjnedMs3E4L+EQjEd+Z1t9fP58MWB1M8Rl3TN4t+UoyE6cZPBZL4dNeavYIIS7KRHdWus0b7FhtT1YwVXgb7bkGFutRPF1Ca9t2qyjl1q1b+eAHP8ipw6eSWrIGH8s2xCvXOrf0BpBUjmhLdxxRQ+ARRFV+8MOHePzxxzBG0N83SKXsIUUejAvGJtKKSNvxfoxCiiW3eBdehnkeJDG6V9E9rnG7ifP2zpduE2spnb62VWWNTE9G1uKGxdw302+Mq/FmcbyQJkdaVbQLb7n9H4slvPl8vEAhCAKq1SrGGC6++GIu33Y5mjhIOF2sIJLZMh1ptNFEzN5+vR5HMRw8eJB9+/bheR7FYhHP81o5clfQ4i3P/palIZlwuIruYTY7jDFzztBvpqcRnCK8yaRQu9ivKuFdRjpvUENdxjajO3uY7gdftMnj5aKlPIrgKKGHV63QX8ijPR9HOKhIooyMXyOJihTK0NpEaFCRwBYRtgywZBUlKihRwZJVpKljYWiUm6wpbebDH/gkV1x0DYqzUfqdky4GozBGYpBIaSOFgyC2TkMd4gdNtA5oRTMkm3E8Asa577t/z8FDP8Pp03hmlPygQKs6PmVCWSWyPHB8cHwiyyOUDXwWIX+N8OM+RW68pb5jEYKaOLrwBhbQtdgNcBXd42lvnMdjeef7u4l6u6icudiPgUKIszqsx1U3o90lAgQyq7dXbmL6hNqFrLLxawlvEASH263DXlMjtoeftVuQ7VEE5XKZfD7P+9//fj70oQ8xNBBfi5bqLZzLUlYrcU1nnwpWgV8c+AWvvvpqWxkhE0c5rLwP9/BKdyDxG84kvnOdbDvWxFpKpxivqgtiGVnVbpleMMZsT8Lm0m2hluktQogXk+905/itKndDS5n8pn5NqTi5jNYGKS2MaX/UT2NnTfvHkMqgI59ms0kYGIQpoEQJYUpEQYlDr1UZ6j+dD1zxr/jwB3ewZuB0II/ftJmsYExSx629vdSsVYBCChchFFqLjsUVPj/60Q946eUX25YZi9ZCjSkREEuJMMnYJMT13V5b+oZnJ7Gwurkdzpyj1dspDg90CZPqnHnOFlJ0p/OmtSoniWYhrfOXbgsVx/aInU6rt9vCiuOWliKFYfhSaqGmy2B7jWpoj4gQQqC1ptFoUC6Xede73sXHPvYxduzYwfDAMABBEGDbcxdD08qFMPm30dooP/3pT6nVariuO6WaxWKGxc2Tl1a6AymJ+HaLduhJeBNRmI9VttSW3Kq52DqYKTduxgy0LyxJJpDb5xO6pYk8bmlJmBTOARNJBGll3SgupyPa42fbSCr2GqOxLInjOGgtqJR9fM9msP80tpxxER//nc/x3nd/hIK9Ac8XVGtNLMtBSGj6AQgdb90qRJvY+o7bAhNNXdShtebpp59i5OibFAo53JxNFIU4jo1tucRO4KSysLGSLa00PEMyiLliZrKoLTDugYU3MCtDxP7a3bMF+yc+386sZL1e7PMV0J72v4BQqlUpvImILMTdsKyr247TULdVO8nWUgzXdX8ZhmHL0p1L3bV2CzcMQ0499VSuvvpqPve5z3Hu2efSV+gDIOfkKBVLiVXcW5xwe2SFMSDlZJ+q1SpPPvkkAH19fa2+pws1lmFl2mz8chna2EH8GJd+6WZ7tO98xO1VuDpF4aaZYq862pjLjP18xGRVCm9Ct8RCPbGAZcVzTkF5HNNpRHQrfHlc0hLefG7w52HAC1JagJieCL3Th5kQmZAgbKKU4vS3n8n7r9jORz+ygyuv+CCb1r2dEPC1jyEAmkAVX7+FkUfJ5eqAn2zNti1ZqSYiLGtqrG0qu81mg7Hxtzjw4rO4OQshQ5qb6pYwAAAP30lEQVTNBkIawlDHoWNakvqIp4RCLGomQcnUHBKAUWDUC0TFny9iQzMx10UL880YNpdqB51t9OrnnVOincT9cSIJ71yXWU/LxdzDZxYivHM9r0sq8qt5kq01u/Xlv9hb+/h1lz4JnA20WbzHtkrDMEQpxaZNm3j3ZVdyxft+g6I1jAZeeu0lpHSoVT1GR0ep1+s4jsOaNWsYHh6mUCgw0Lf2mPufqQvNZpNKpcLY2BiFQgHfbwKgLEkQBCiV+oRXzM/75K1ffmCp661BFwvWHDsX7nyFai7C2+1m0Evi9Rc72pntJrIqrJuZEHEpns7E5HOplJxW/kiZ7UbVbTznEo7XeX7mKrxLkSb0FqZ+D64nnoQ7ri35KfFcYSAec+zcb49NTNDXVyAIgjiCwJjWWyfdA7F1t2XLFn7t136NC7ZeTLHQz7PPPsszz/yCV15+jWrV4+jRNJQ1TPy54eTPwL+48N9w7rnncv755zLUl54ni7SMTxBobEuhNXheQKnPRkdN+vpzPPLod7FsTahrWHac6zd1j8STbKqtFlpijbYiJxbHDWGMSNqCRqNBLlfAsizqNfPYojQwO2lMaGc115lWW/USEjaFxApr/9zYMYQd5h9S9gRTLZbZinGuauFN6FYDby7CO+Wzcxyv2c5jJ519ne38zKkm3HwQQuwxxnSWTlrUasZLwZRZIcdxHvF9P8rn863ohFwuh5SxFen7Pkop1qxZw5YtW9i6dSvbt2/Htm327t3Lrl27+MIXvsC9997Ls88+yxtvvDFrB/bv38/tt9/Ol770JZ746eR3wGAIwqDl7pASXDd2OxhjKJfLHDp0aFqOifT/y0nadpruMgiCKJfLPbKMXei8UK/vZt2Y7gUCe7F4elk40c58XQ3dBKdrVrXk+FbNZMoxWMhCis7x6pYkHJjx3M+1/FO3SIKZ2tvB9ErUS7XYZdr3f4naWTSmWLxf+8r3H/n3n7rk4aE1xStD3UBrHftNhUU+b+M4BfL5PMViEduOY37/9o5vUK1WqdUaYBSFQoF16wexLAtjDJ5XjXcugtjaFQGQWr5QHn0DrTU/feZ1xsqv8uaRX3Hl+6+iYK3Dtlx05KN1nO08LgwRolRIuXqEN488j1RhLHzCYIxN7JdQSfRCmwCnupz+SSyOxSuQCAGGJpYtEcLgecHDd972z8stvDcyVeAeN8bcRCySqWXUmVbvRSFEL9bVnKxkIcSLHY/Qs7k/0s+NGWN2MfVivtHEZWeeYPKx8kziCUWYXihytdF1+XAvlmiP43VhsnWe+zHmaBW2tde+3LzVnhBiV5vgdgryrgVMCM7Gno4+nUn8fT9uS71PWzpWr9e/u2Zd7sooiFrJcmzbIucWcJw4w1ilUmFkZIQgCKhUxnAch7Vr12JbOYwxBIGhXq+jtca2k2TqQkxupK+wZs0a8vk8leooL7zwAkePjjIxXuOD//LfMNy/MYkrhigySQVfEAjq9XqcfcydNNpjSzfelsvoTaMnImNQSqU13L67PK1PYSfwAFP9asfKxzBTXG835vPI2OkP7LUU0C7ii6ZdJHYwGb3RyU3J3xcsvmb2R6WzFjusKvHzdt485lI2aVfy/vaxPtZ4pdw0n2PpENcp7R0j/8eLLGHe3ORG31n+6rgW3mkBqFJaDwSBnkgT15RKJWw7djWUy2WOjowyenSM8kSFei32abpuHiEUTd+jXJmgVh8HEVAo2iCaydaeZUy14mqNqHLk6EtoU2bjqf3UGke4595vsPe+u4EmggjLTlfIRfhhhYgGYxOvEeoaUhmkMqRWdJoIZ0r+XWQaaRD/vEjWbjxe8RBGURyL7Pv+hG3bC029OGfa8jL0KopzqcfW+fjby+fmFbbWtsqulzZuSgLpj8cY07kw39jq9vGai8js7PFJZyauone3QZpneKknuzqPv/PmfVwxTXi/eedPHg2CYK8xBsuy0Fq3/Lu+77fCzHK5HMVisVUpQut4ssx1XdykEFqj0Zi2qq1z832/VRo9l8tRKpWIoojnnnuOe++/Fz/wAbCsVOAimn6TN954o5WPIfWxphZ6ui0XWutWe1EU7f3G7T95dNkab0MI8YQQ4iziibVuF9YeYrE6q1fRNd2LMfby2XnnbEjW419EbJF3O45biC/m9FF5tQvvND/vXMLKhBBjQoidxII404x+eu5FcrOaN0l7V7W1141bgBvE8uUZ7nYDPm59va0ZqXahuvazF/6OUN43hIhn7AU2UioEdqvqcPp+N+cQhiFh6LeS66RWYC8CKGVc1TcyzaQwJrhOP649hKKfT3/qD3nXuduIK1QYjKjh+Ue5865bue8f/57hjfEyYa0FkRaYSCGEhUAhpuTbjRK/skleF8fqdUUf9XodaXnkcjnqtea/+/otP7trUXaekZGxII6DtAFd6ZoeTAhxD3CflPJqx3GItETriDAMiRLrLhVUP4grTKQl0hMf5xQLeDZGRkZABAwMDBBFcPToUYyuM1AyPP/882w+/RwcO4dt2wgklmXRbDZb4WPdohqWa7zTVX4qzsZ2n2VZ9yxPyxkZGauVrplqbvufj9crY7k9fcVTiKKIUNeIqGK5dSwnREchgjx9pXUIJyIUTepBjXpQwzdNjBUhXYF0BQH+MbcwhGJxgGKxnzA0RJFhYDDP4NomIneQf7jv8xx4dS+2HSSP9CV0cz0T5RH8oInfFISBwkSxpa0sg7JChPJAVtq2WuJrTvLnThmC9lwOTsfmJlv6e/K+5HOBLpMvgiVLVCesPbd/6an6Mpy3jIyMVcyMKcKGh4f3jIyM3NNsNvF9P7Z2k9VsruuilKLZbC55B6Mo4plnnqEZNJOJs7iMUKPR6MmaXo7+hWFIo9G4Z3h4+LidRc3IyDh+mFF4d//lA9Vaxdxhq0HPUkWUzBFphdYBlh3huBFmMUqKGRFvXbsmMUbw6GP7eOnlA0QmQMoIKSOazebiCG8rW1lK1LFpWnHH7Vvyf8fqw4T9nolyd/zF/7i3uvAOZWRknOgcMynuN+98ao/rurc7jtOycuNlxHHJ9jTv7ZJ2UEpeffVVnnnmmZbF3Wg0sG172VeodSOpjHH7nbfvy6zdjIyMnpg1G3mjqm6rV+VTUehiqTwAYdhEmwraVBaxK+nih/TX2BKNl+FGPPPsU0yUjwAB1doYxWKRIAgWod2OfLppJYxpFm5i+XbkDK5MyKcUQ7ctQkcyMjJOEmYV3lu//M+Pe563u9FoRFLK1lLgMAzxPG/JO6iUolQq8fLLL3Pw4EEgjiRIV4mtMJHnebtv3X3P4yvdkYyMjNVDT/V39nz96d1RmP8rHVhI4aIsgVQ6WY22GF3o1o3Ux2uwbEG1foSfPbsfX1foH3Sp1WoopRah/U5S325nRYypNeDi1XfuX/39nfvmWjAyIyPjJKfnwme2bX8xCIJ7oyhCKYVt28sSVZCuijPGcPDgQSqVCgW3QLVaXRYf8zG4F/jiSnYgIyNjddKz8H519w8O1CryzyNtP6lEgVrNI4ri1JFpgcl8Po9lWS0XQLFY7LEL7VUc0hprcW6FMPRRSrB2fZGXX32OXz7/NNAkX3BZnOrtx65I4TgOjYaPwMZSRcrjAX7DfXKo/+1//tUvProcNdUyMjJOMOYkXX/39Ue+p5TaFQTBwXS1Wro8OAzDVsRDnA4yrjqxUJRSrWgKIUSco0E3W3mCl5pyuUxfXx/NZpMgCNi0adNBrfWu//e//8P3lrzxjIyME5I5K9ftX953t++5n69XrDckfa3lw0EQ4HleK3l6av3OHUF7VjFlCZQlaPplLKfJgRefpVIboVQqzWPf3Uh8uGk0w5ToCkU+X6Je1Tj2AIrBN8ZG9Of/7rZH716kxjMyMk5C5mUyfv0rP77V9/3/UqvV3rAsC8dxWtEOaaYx13UpFAoL7mBb1i9c1+WVV15hZGSEvr6+Vj6IpST1ZUsp35iYmPgvf/uVB25d8kYzMjJOaOb9rH731362O2ja/1lrfTBOlm63Hv+bzSaNRqO3JcXpyrGWxZn+PfbxxpnHNFJpHFcwUT7CG2++TLGYJwwXI8NY50q1FAFGMjpSo6+09qDfcP7zN7+eRTBkZGQsnAU5Se/6m8du9TzvpnK5/GS9Xm9ZusCixdimtd8cx2n5j1955RXy+fyy+Hjz+fyTR44cuemOv/6nzNLNyMhYFBasXH/318/d3dfX9588z7vX9/1WPl4pZStV5EKw7Tg/hO0IPK+KUvD666/guu6i7H+apT0Fde+GDRv/0ze+8uPMp5uRkbFoLIrJePtfPPm9XC73R0EQ/GWz2YzSjGaL4YNNxVUphed5WJbF2NjYUscRR8BfAn/0//zZ/8qiFzIyMhaVrhUoFsI1n37PDVIFNziuuUBaAVpPppSMlxy7COw4/MyPsPJunMTcpFUrRGuSzkRxOSDLynHkyBH6SoNIKcnn82zZsoXXX3+dkaOdJeSnWq/KEm112NJ6m21xu7pOFEU4dhHbKlEpN57yGmb3nr99JPPnZmSsco7XChSL7iT9+ld+tDsMw+vr9fqXhRCeMaYV4WDbNr7vt3I8FIvFlt+2HaXUlPpr6d+EEK2VbGEY9uTjTeNvU/FNP+v7Ps1msxX21mw2vXK5/GUp5fWZ6GZkZCwli27xtvOJz1y2w7KjjyuLjwqpE9ELkpLxTpzQPKwkojpZNFMIgePkcByHSqVCPp+nPFEll8uhdbxKbvPmzdTrdd5487WpjZqpYpyKtTFMEfm0SKbSefymuEcK646vfeX7WWrHjIwTiOPV4l1S4QX45A0XlXTk7xBS73Bd9+p8PgdAo+FRr9exCwLLslDKblU0jpcgO61KE6VSiXrNw7ZtwjDO23DaaacBcOiNV6c22CG8YRgm+7dIi3dCfEKklPfVxoI969e9bc8Xdt2TJTHPyDjBOGmFN+Wzf/CvCyNHD3/UmOAj+Xz+w7m8M6CUYrzxSiupuhACHQUtcZRSEoY+xWKxVco9ikLCMGTt2rUUCgUOHTqUtNAmuCZdMRe7J5R0W2FpQRBORFG0Vyn1bUvl7rntL7+f1UjLyDhBOemFt51PfPp9lxr0VUqpD/hi5AohhJRSopRCqsnBipcix3kZ0lwNEOH7PqVSiaGhId58881kr92FN4oiIi2jMAwf1lp/N5fLP/D1L+1/dNkONiMjY8XIhHcG/uj/+reXeZ53WaNRuySKom1KybOVUkQmTHyyQTwpFzQQQmDbcViZbdusXbuWI0eOxqvcRDQpuPHrC6Ce9JvhY/l86ZFbv7j3kRU5wIyMjBUjE94e+MR/vKII5jwp5Tk6CraEYbg5l7NOk1Ju8IPGGqA/l3PynuchhGisW7eufPTo2FGMOoyIXsNYLwEHMNYvgZ9/9X8+VFvZI8rIyFhJjlfhzcjIyMjIyMjIyDix+d+YJdyfGn177gAAAABJRU5ErkJggg==" alt="SageRock AI" style="height:32px;">
    </div>
    <div class="user-info">
      <span class="user-email" id="user-email"></span>
      <button class="logout" id="logout-btn">Log out</button>
    </div>
  </header>

  <div class="container">
    <div id="conn-status" class="disconnected">Disconnected</div>
    <div id="errors"></div>

    <div class="card">
      <div class="card-title">Start a Session</div>

      <div class="mode-toggle">
        <input type="radio" name="bot-mode" id="mode-translate" value="translate" checked>
        <label for="mode-translate">Translation</label>
        <input type="radio" name="bot-mode" id="mode-notes" value="notes">
        <label for="mode-notes">Meeting Notes</label>
        <input type="radio" name="bot-mode" id="mode-both" value="both">
        <label for="mode-both">Both</label>
      </div>

      <label for="meeting-url">Meeting Link</label>
      <input type="text" id="meeting-url" placeholder="Zoom, Google Meet, or Teams link">

      <div id="translate-options">
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
      </div>

      <div id="notes-options" style="display:none;">
        <label for="notes-lang">Meeting Language</label>
        <select id="notes-lang">
          <option value="en">English</option>
          <option value="de">German</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="pt">Portuguese</option>
        </select>
      </div>

      <button class="primary" id="start-btn" disabled>Start Translation</button>
    </div>

    <div class="card">
      <div class="card-title">Active Bots</div>
      <div id="bot-list"><div class="empty">No active bots</div></div>
    </div>

    <div class="card">
      <div class="card-title">Recordings</div>
      <div id="usage-summary" style="display:none; margin-bottom:12px; padding:10px 14px; background:rgba(255,255,255,0.04); border-radius:8px; font-size:0.95em;">
        <span id="usage-total-mins" style="color:var(--cream);"></span>
        <span style="color:var(--muted);"> &middot; </span>
        <span id="usage-total-cost" style="color:var(--sage-light); font-weight:600;"></span>
        <span style="color:var(--muted); font-size:0.85em;"> @ $0.10/min</span>
      </div>
      <div id="rec-list"><div class="empty">No recordings yet</div></div>
    </div>

    <div id="admin-section" style="display:none;">
      <div class="card admin-card-dashboard">
        <div class="card-title admin-title-dashboard">Dashboard</div>
        <div id="admin-dashboard"><div class="empty">Loading...</div></div>
      </div>
      <div class="card admin-card-users">
        <div class="card-title admin-title-users">User Management</div>
        <div class="admin-add-row">
          <input type="email" id="new-user-email" placeholder="Email">
          <input type="password" id="new-user-pass" placeholder="Password (6+ chars)">
          <button class="primary" id="add-user-btn">Add User</button>
        </div>
        <div id="user-list"><div class="empty">Loading...</div></div>
      </div>
      <div class="card admin-card-sessions">
        <div class="card-title admin-title-sessions">All Sessions</div>
        <div id="admin-rec-list"><div class="empty">Loading...</div></div>
      </div>
    </div>
  </div>
</div>

<script>
(function() {
  // ── Supabase auth ──────────────────────────────────────────────────
  var sbUrl = "__SUPABASE_URL__";
  var sbKey = "__SUPABASE_ANON_KEY__";
  if (typeof supabase === "undefined") {
    document.getElementById("auth-error").textContent = "Error: Supabase JS failed to load";
    document.getElementById("auth-error").style.display = "block";
    return;
  }
  var sb = supabase.createClient(sbUrl, sbKey);
  var accessToken = null;

  var loginScreen = document.getElementById("login-screen");
  var mainApp     = document.getElementById("main-app");
  var authError   = document.getElementById("auth-error");
  var authEmail   = document.getElementById("auth-email");
  var authPass    = document.getElementById("auth-password");
  var signinBtn   = document.getElementById("signin-btn");
  var logoutBtn   = document.getElementById("logout-btn");
  var userEmailEl = document.getElementById("user-email");

  function showLogin() {
    loginScreen.style.display = "";
    mainApp.style.display = "none";
    accessToken = null;
    if (ws) ws.close();
  }

  function showApp(session) {
    accessToken = session.access_token;
    loginScreen.style.display = "none";
    mainApp.style.display = "block";
    userEmailEl.textContent = session.user.email || "";
    connect();
    loadRecordings();
  }

  function showAuthError(msg) {
    authError.textContent = msg;
    authError.style.display = "block";
    setTimeout(function() { authError.style.display = "none"; }, 6000);
  }

  // onAuthStateChange is the single source of truth for auth state.
  // It fires INITIAL_SESSION on load, SIGNED_IN after login/signup,
  // TOKEN_REFRESHED on refresh, and SIGNED_OUT on logout.
  sb.auth.onAuthStateChange(function(event, session) {
    if (event === "PASSWORD_RECOVERY") {
      var newPass = prompt("Enter your new password:");
      if (newPass) {
        sb.auth.updateUser({ password: newPass }).then(function(res) {
          if (res.error) { alert("Error: " + res.error.message); }
          else { alert("Password updated successfully!"); }
        });
      }
    }
    if (session && session.access_token) {
      var wasLoggedIn = !!accessToken;
      accessToken = session.access_token;
      if (!wasLoggedIn) {
        showApp(session);
      }
    } else if (event === "SIGNED_OUT" || event === "TOKEN_REFRESHED") {
      if (accessToken) {
        accessToken = null;
        showLogin();
      }
    }
  });

  signinBtn.addEventListener("click", function() {
    var email = authEmail.value.trim();
    var pass  = authPass.value;
    if (!email || !pass) { showAuthError("Enter email and password"); return; }
    sb.auth.signInWithPassword({email: email, password: pass}).then(function(res) {
      if (res.error) { showAuthError(res.error.message); }
      // showApp will be called by onAuthStateChange
    });
  });

  logoutBtn.addEventListener("click", function() {
    sb.auth.signOut().then(function() { showLogin(); });
  });

  // Allow Enter key to submit login
  authPass.addEventListener("keydown", function(e) {
    if (e.key === "Enter") signinBtn.click();
  });

  // Forgot password
  document.getElementById("forgot-link").addEventListener("click", function(e) {
    e.preventDefault();
    var email = authEmail.value.trim();
    if (!email) { showAuthError("Enter your email first"); return; }
    var resetMsg = document.getElementById("reset-msg");
    sb.auth.resetPasswordForEmail(email, { redirectTo: location.origin }).then(function(res) {
      if (res.error) { showAuthError(res.error.message); return; }
      resetMsg.textContent = "Password reset email sent! Check your inbox.";
      resetMsg.style.display = "block";
      authError.style.display = "none";
    });
  });

  // ── Management UI ──────────────────────────────────────────────────
  var startBtn  = document.getElementById("start-btn");
  var urlInput  = document.getElementById("meeting-url");
  var sourceSel = document.getElementById("source-lang");
  var botList   = document.getElementById("bot-list");
  var recList   = document.getElementById("rec-list");
  var connEl    = document.getElementById("conn-status");
  var errorsEl  = document.getElementById("errors");
  var translateOpts = document.getElementById("translate-options");
  var notesOpts = document.getElementById("notes-options");
  var notesLang = document.getElementById("notes-lang");

  // Mode toggle
  var modeRadios = document.querySelectorAll('input[name="bot-mode"]');
  function getMode() {
    for (var i = 0; i < modeRadios.length; i++) {
      if (modeRadios[i].checked) return modeRadios[i].value;
    }
    return "translate";
  }
  modeRadios.forEach(function(r) {
    r.addEventListener("change", function() {
      var m = getMode();
      translateOpts.style.display = (m === "translate" || m === "both") ? "" : "none";
      notesOpts.style.display = (m === "notes" || m === "both") ? "" : "none";
      startBtn.textContent = m === "notes" ? "Start Meeting Notes" : m === "both" ? "Start Session" : "Start Translation";
    });
  });

  var isAdmin = false;
  var adminSection = document.getElementById("admin-section");
  var adminRecList = document.getElementById("admin-rec-list");

  var ws = null;
  var reconnectTimer = null;

  function wsUrl() {
    var proto = location.protocol === "https:" ? "wss:" : "ws:";
    return proto + "//" + location.host + "/mgmt?token=" + encodeURIComponent(accessToken);
  }

  function connect() {
    if (!accessToken) return;
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
        if (msg.is_admin !== undefined) {
          isAdmin = msg.is_admin;
          if (isAdmin) {
            adminSection.style.display = "";
            loadDashboard();
            loadAdminSessions();
            loadUsers();
          }
        }
        renderBots(msg.bots);
      } else if (msg.type === "users") {
        renderUsers(msg.users);
      } else if (msg.type === "user_created") {
        loadUsers();
      } else if (msg.type === "user_deleted") {
        loadUsers();
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

  function authHeaders() {
    return { "Authorization": "Bearer " + accessToken };
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
      var ownerHtml = (isAdmin && b.user_id) ? ' <span class="owner-tag">user:' + b.user_id.substring(0,8) + '</span>' : '';
      var isNotes = b.mode === "notes";
      var isBoth = b.mode === "both";
      var url = isNotes ? "" : listenUrl(b.target_lang);
      var dlHtml = "";
      if (b.clip_count > 0 && !isNotes) {
        dlHtml = '<div class="dl-links">' +
          '<a href="#" data-mp3-bot="' + b.bot_id + '" onclick="downloadMp3(\\x27' + b.bot_id + '\\x27);return false;">Audio MP3</a>' +
          '<a href="#" onclick="downloadFile(\\x27' + b.bot_id + '\\x27,\\x27subtitles.srt\\x27);return false;">Subtitles SRT</a>' +
          '<a href="#" onclick="downloadFile(\\x27' + b.bot_id + '\\x27,\\x27transcript.jsonl\\x27);return false;">Transcript</a>' +
          '<a href="#" data-video-bot="' + b.bot_id + '" onclick="downloadVideo(\\x27' + b.bot_id + '\\x27);return false;">Dubbed Video</a>' +
          '<span style="color:var(--muted);font-size:.72rem;">(' + b.clip_count + ' clips)</span>' +
        '</div>';
      }
      var modeLabel = isNotes ? '<strong>MEETING NOTES</strong>' :
        isBoth ? '<strong>' + b.source_lang.toUpperCase() + ' &rarr; ' + b.target_lang.toUpperCase() + ' + NOTES</strong>' :
        '<strong>' + b.source_lang.toUpperCase() + ' &rarr; ' + b.target_lang.toUpperCase() + '</strong>';
      html += '<div class="bot-row">' +
        '<div class="bot-info">' +
          '<span class="status-dot ' + b.status + '"></span>' +
          modeLabel + ' ' +
          '<span class="bot-id">' + shortId + '</span> ' + ownerHtml +
          '<span style="color:var(--muted);font-size:.8rem;"> ' + b.status + '</span>' +
          (url ? '<div class="listen-url">' + url + '</div>' : '') +
          dlHtml +
        '</div>' +
        '<div style="display:flex;align-items:center;gap:.4rem;flex-shrink:0;">' +
          (url ? '<button class="copy-link" data-url="' + url + '">Copy Link</button>' : '') +
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
    var m = getMode();

    if (m === "notes") {
      ws.send(JSON.stringify({
        action: "start",
        mode: "notes",
        meeting_url: meetingUrl,
        source_lang: notesLang.value
      }));
    } else if (m === "both") {
      var checks2 = document.querySelectorAll('input[name="target"]:checked');
      var targets2 = [];
      for (var i = 0; i < checks2.length; i++) targets2.push(checks2[i].value);
      if (targets2.length === 0) { showError("Select at least one target language"); return; }
      ws.send(JSON.stringify({
        action: "start",
        mode: "both",
        meeting_url: meetingUrl,
        source_lang: sourceSel.value,
        target_langs: targets2
      }));
    } else {
      var checks = document.querySelectorAll('input[name="target"]:checked');
      var targets = [];
      for (var i = 0; i < checks.length; i++) targets.push(checks[i].value);
      if (targets.length === 0) { showError("Select at least one target language"); return; }
      ws.send(JSON.stringify({
        action: "start",
        mode: "translate",
        meeting_url: meetingUrl,
        source_lang: sourceSel.value,
        target_langs: targets
      }));
    }
  });

  function formatDuration(sec) {
    if (!sec) return "";
    var m = Math.floor(sec / 60);
    var s = Math.round(sec % 60);
    return m > 0 ? m + "m " + s + "s" : s + "s";
  }

  function loadRecordings() {
    if (!accessToken) return;
    fetch("/api/recordings", {headers: authHeaders()}).then(function(r) { return r.json(); }).then(function(recs) {
      if (!recs || recs.length === 0) {
        recList.innerHTML = '<div class="empty">No recordings yet</div>';
        return;
      }
      var RATE_PER_MIN = 0.10;
      var totalMins = 0;
      var html = "";
      for (var i = 0; i < recs.length; i++) {
        var r = recs[i];
        var shortId = r.bot_id.substring(0, 8);
        var isNotes = r.mode === "notes";
        var isBoth = r.mode === "both";
        var info = isNotes ? "" : r.clips + " clips";
        if (r.duration) {
          info += (info ? " &middot; " : "") + formatDuration(r.duration);
          totalMins += r.duration / 60;
        }
        var costHtml = "";
        if (r.duration) {
          var userCost = (r.duration / 60) * RATE_PER_MIN;
          costHtml = ' &middot; <span class="cost-green">$' + userCost.toFixed(2) + '</span>';
        }
        var linksHtml;
        if (isNotes) {
          linksHtml = '<div class="dl-links">' +
            '<a href="/meeting/' + r.bot_id + '" target="_blank">View Meeting Notes</a>' +
          '</div>';
        } else if (isBoth) {
          linksHtml = '<div class="dl-links">' +
            '<a href="/meeting/' + r.bot_id + '" target="_blank">View Meeting Notes</a>' +
            '<a href="#" data-mp3-bot="' + r.bot_id + '" onclick="downloadMp3(\\x27' + r.bot_id + '\\x27);return false;">Audio MP3</a>' +
            '<a href="#" onclick="downloadFile(\\x27' + r.bot_id + '\\x27,\\x27subtitles.srt\\x27);return false;">Subtitles SRT</a>' +
            '<a href="#" onclick="downloadFile(\\x27' + r.bot_id + '\\x27,\\x27transcript.jsonl\\x27);return false;">Transcript</a>' +
            '<a href="#" data-video-bot="' + r.bot_id + '" onclick="downloadVideo(\\x27' + r.bot_id + '\\x27);return false;">Dubbed Video</a>' +
          '</div>';
        } else {
          linksHtml = '<div class="dl-links">' +
            '<a href="#" data-mp3-bot="' + r.bot_id + '" onclick="downloadMp3(\\x27' + r.bot_id + '\\x27);return false;">Audio MP3</a>' +
            '<a href="#" onclick="downloadFile(\\x27' + r.bot_id + '\\x27,\\x27subtitles.srt\\x27);return false;">Subtitles SRT</a>' +
            '<a href="#" onclick="downloadFile(\\x27' + r.bot_id + '\\x27,\\x27transcript.jsonl\\x27);return false;">Transcript</a>' +
            '<a href="#" data-video-bot="' + r.bot_id + '" onclick="downloadVideo(\\x27' + r.bot_id + '\\x27);return false;">Dubbed Video</a>' +
          '</div>';
        }
        var label = isNotes ? "NOTES" : isBoth ? shortId + " + NOTES" : shortId;
        html += '<div class="bot-row">' +
          '<div class="bot-info">' +
            '<strong>' + label + '</strong> ' +
            '<span style="color:var(--muted)">' + info + costHtml + '</span>' +
            linksHtml +
          '</div>' +
        '</div>';
      }
      recList.innerHTML = html;
      var summaryEl = document.getElementById("usage-summary");
      if (totalMins > 0) {
        var totalCost = totalMins * RATE_PER_MIN;
        document.getElementById("usage-total-mins").textContent = Math.round(totalMins) + " minutes total";
        document.getElementById("usage-total-cost").textContent = "$" + totalCost.toFixed(2);
        summaryEl.style.display = "block";
      } else {
        summaryEl.style.display = "none";
      }
    }).catch(function() {});
  }

  var dashboardEl = document.getElementById("admin-dashboard");

  function loadDashboard() {
    if (!accessToken || !isAdmin) return;
    fetch("/api/admin/dashboard", {headers: authHeaders()}).then(function(r) { return r.json(); }).then(function(d) {
      var html = '<div class="stat-grid">';
      html += '<div class="stat-tile">' +
        '<div class="stat-value stat-cream">' + d.total_sessions + '</div>' +
        '<div class="stat-label">Sessions</div></div>';
      html += '<div class="stat-tile">' +
        '<div class="stat-value stat-cream">' + d.total_minutes + '</div>' +
        '<div class="stat-label">Minutes</div></div>';
      html += '<div class="stat-tile">' +
        '<div class="stat-value stat-danger">$' + d.total_api_cost.toFixed(2) + '</div>' +
        '<div class="stat-label">API Cost</div></div>';
      html += '<div class="stat-tile">' +
        '<div class="stat-value stat-sage">$' + d.total_revenue.toFixed(2) + '</div>' +
        '<div class="stat-label">Revenue</div></div>';
      html += '<div class="stat-tile">' +
        '<div class="stat-value stat-purple">$' + d.margin.toFixed(2) + '</div>' +
        '<div class="stat-label">Margin</div></div>';
      html += '</div>';
      // Service-level breakdown
      var services = [];
      if (d.recall_total_cost != null) {
        services.push('<span style="color:var(--stone);">Recall: $' + d.recall_total_cost.toFixed(2) +
          ' (' + d.recall_total_minutes + ' min, ' + d.recall_total_bots + ' bots)</span>');
      }
      if (d.deepgram_hours_this_month != null) {
        services.push('<span style="color:var(--cost-blue,#6aacdb);">Deepgram this month: $' + d.deepgram_cost_this_month.toFixed(2) +
          ' (' + d.deepgram_hours_this_month + ' hrs)</span>');
      }
      if (d.deepl_chars_used != null) {
        var pct = Math.round(d.deepl_chars_used / d.deepl_chars_limit * 100);
        var pctColor = pct > 80 ? 'var(--danger)' : 'var(--sage-light)';
        services.push('<span style="color:' + pctColor + ';">DeepL: ' +
          d.deepl_chars_used.toLocaleString() + ' / ' + d.deepl_chars_limit.toLocaleString() +
          ' chars (' + pct + '%)</span>');
      }
      if (services.length > 0) {
        html += '<div class="service-line">' + services.join('') + '</div>';
      }
      // Per-user breakdown table
      if (d.users && d.users.length > 0) {
        html += '<table class="dash-table">';
        html += '<tr>' +
          '<th>User</th>' +
          '<th>Sessions</th>' +
          '<th>Minutes</th>' +
          '<th>API Cost</th>' +
          '<th>Revenue</th>' +
          '<th>Margin</th></tr>';
        for (var i = 0; i < d.users.length; i++) {
          var u = d.users[i];
          var label = u.email || (u.user_id ? u.user_id.substring(0, 8) : "?");
          html += '<tr>' +
            '<td>' + label + '</td>' +
            '<td>' + u.sessions + '</td>' +
            '<td>' + u.minutes + '</td>' +
            '<td class="stat-danger">$' + u.api_cost.toFixed(2) + '</td>' +
            '<td class="stat-sage">$' + u.revenue.toFixed(2) + '</td>' +
            '<td class="stat-purple">$' + u.margin.toFixed(2) + '</td></tr>';
        }
        html += '</table>';
      }
      dashboardEl.innerHTML = html;
    }).catch(function() {});
  }

  function loadAdminSessions() {
    if (!accessToken || !isAdmin) return;
    fetch("/api/admin/sessions", {headers: authHeaders()}).then(function(r) { return r.json(); }).then(function(recs) {
      if (!recs || recs.length === 0) {
        adminRecList.innerHTML = '<div class="empty">No sessions found</div>';
        return;
      }
      var html = "";
      for (var i = 0; i < recs.length; i++) {
        var r = recs[i];
        var shortId = r.bot_id.substring(0, 8);
        var userId = r.email || (r.user_id ? r.user_id.substring(0, 8) : "?");
        var langInfo = (r.source_lang || "?").toUpperCase() + " &rarr; " + (r.target_lang || "?").toUpperCase();
        var info = r.clips + " clips";
        if (r.duration) info += " &middot; " + formatDuration(r.duration);
        if (r.api_cost != null && r.duration) {
          var rev = (r.duration / 60) * 0.10;
          info += ' &middot; <span class="cost-green">cost $' + r.api_cost.toFixed(2) + '</span>';
          info += ' &middot; <span class="cost-blue">rev $' + rev.toFixed(2) + '</span>';
          info += ' &middot; <span class="cost-purple">margin $' + (rev - r.api_cost).toFixed(2) + '</span>';
        }
        var dateStr = r.created_at ? new Date(r.created_at).toLocaleDateString() : "";
        html += '<div class="bot-row">' +
          '<div class="bot-info">' +
            '<strong>' + langInfo + '</strong> ' +
            '<span class="bot-id">' + shortId + '</span> ' +
            '<span class="owner-tag">user:' + userId + '</span>' +
            '<div style="color:var(--muted);font-size:.8rem;">' + info + (dateStr ? " &middot; " + dateStr : "") + '</div>' +
            '<div class="dl-links">' +
              '<a href="#" data-mp3-bot="' + r.bot_id + '" onclick="downloadMp3(\\x27' + r.bot_id + '\\x27);return false;">Audio MP3</a>' +
              '<a href="#" onclick="downloadFile(\\x27' + r.bot_id + '\\x27,\\x27subtitles.srt\\x27);return false;">Subtitles SRT</a>' +
              '<a href="#" onclick="downloadFile(\\x27' + r.bot_id + '\\x27,\\x27transcript.jsonl\\x27);return false;">Transcript</a>' +
              '<a href="#" data-video-bot="' + r.bot_id + '" onclick="downloadVideo(\\x27' + r.bot_id + '\\x27);return false;">Dubbed Video</a>' +
            '</div>' +
          '</div>' +
        '</div>';
      }
      adminRecList.innerHTML = html;
    }).catch(function() {});
  }

  // Download individual file via signed URL
  window.downloadFile = function(botId, filename) {
    fetch("/recordings/" + botId + "/" + filename, {headers: authHeaders()})
      .then(function(r) {
        if (r.redirected) {
          return fetch(r.url).then(function(r2) { return r2.blob(); });
        }
        return r.blob();
      })
      .then(function(blob) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = botId.substring(0, 8) + "_" + filename;
        a.click();
        URL.revokeObjectURL(a.href);
      })
      .catch(function() { showError("Failed to download " + filename); });
  };

  // Track resolved synced MP3 URLs and in-progress builds so periodic
  // DOM refreshes can restore the link state after innerHTML rebuild.
  var mp3Urls = {};      // botId -> signed URL
  var mp3Building = {};  // botId -> true

  function applyMp3State() {
    // Re-apply resolved/building state to freshly rendered links
    Object.keys(mp3Urls).forEach(function(botId) {
      var el = document.querySelector("[data-mp3-bot=\\x27" + botId + "\\x27]");
      if (el) {
        el.href = mp3Urls[botId];
        el.textContent = "Download MP3";
        el.style.fontWeight = "bold";
        el.target = "_blank";
        el.rel = "noopener";
        el.onclick = function(e) { /* allow default navigation */ };
      }
    });
    Object.keys(mp3Building).forEach(function(botId) {
      if (mp3Urls[botId]) return; // already resolved
      var el = document.querySelector("[data-mp3-bot=\\x27" + botId + "\\x27]");
      if (el) {
        el.textContent = "Building MP3...";
        el.style.color = "#0c5460";
        el.onclick = function(e) { e.preventDefault(); };
      }
    });
  }

  // Download timeline-synced MP3 (background build + polling)
  window.downloadMp3 = function(botId) {
    var shortId = botId.substring(0, 8);
    if (mp3Building[botId] || mp3Urls[botId]) return;
    mp3Building[botId] = true;

    var linkEl = document.querySelector("[data-mp3-bot=\\x27" + botId + "\\x27]");
    if (linkEl) {
      linkEl.textContent = "Building MP3...";
      linkEl.style.color = "#0c5460";
      linkEl.onclick = function(e) { e.preventDefault(); };
    }

    var attempts = 0;
    var maxAttempts = 60;
    function poll() {
      attempts++;
      fetch("/api/recordings/" + botId + "/audio", {headers: authHeaders(), redirect: "follow"})
        .then(function(r) {
          if (r.redirected) {
            mp3Urls[botId] = r.url;
            delete mp3Building[botId];
            applyMp3State();
            return;
          }
          if (r.status === 202) {
            if (attempts >= maxAttempts) {
              throw new Error("Timed out waiting for audio build");
            }
            setTimeout(poll, 5000);
            return;
          }
          throw new Error("Server error " + r.status);
        })
        .catch(function(err) {
          delete mp3Building[botId];
          showError("Failed to build audio for " + shortId + (err.message.includes("Timed out") ? " (timed out)" : ""));
          applyMp3State();
        });
    }
    poll();
  };

  // Download dubbed video (background build + polling)
  var videoUrls = {};
  var videoBuilding = {};

  function applyVideoState() {
    Object.keys(videoUrls).forEach(function(botId) {
      var el = document.querySelector("[data-video-bot=\\x27" + botId + "\\x27]");
      if (el) {
        el.href = videoUrls[botId];
        el.textContent = "Download Video";
        el.style.fontWeight = "bold";
        el.target = "_blank";
        el.rel = "noopener";
        el.onclick = function(e) { /* allow default navigation */ };
      }
    });
    Object.keys(videoBuilding).forEach(function(botId) {
      if (videoUrls[botId]) return;
      var el = document.querySelector("[data-video-bot=\\x27" + botId + "\\x27]");
      if (el) {
        el.textContent = "Building Video...";
        el.style.color = "#0c5460";
        el.onclick = function(e) { e.preventDefault(); };
      }
    });
  }

  window.downloadVideo = function(botId) {
    var shortId = botId.substring(0, 8);
    if (videoBuilding[botId] || videoUrls[botId]) return;
    videoBuilding[botId] = true;

    var linkEl = document.querySelector("[data-video-bot=\\x27" + botId + "\\x27]");
    if (linkEl) {
      linkEl.textContent = "Building Video...";
      linkEl.style.color = "#0c5460";
      linkEl.onclick = function(e) { e.preventDefault(); };
    }

    var attempts = 0;
    var maxAttempts = 60;
    function poll() {
      attempts++;
      fetch("/api/recordings/" + botId + "/video", {headers: authHeaders(), redirect: "follow"})
        .then(function(r) {
          if (r.redirected) {
            videoUrls[botId] = r.url;
            delete videoBuilding[botId];
            applyVideoState();
            return;
          }
          if (r.status === 202) {
            if (attempts >= maxAttempts) {
              throw new Error("Timed out waiting for video build");
            }
            setTimeout(poll, 10000);
            return;
          }
          throw new Error("Server error " + r.status);
        })
        .catch(function(err) {
          delete videoBuilding[botId];
          showError("Failed to build video for " + shortId + (err.message.includes("Timed out") ? " (timed out)" : ""));
          applyVideoState();
        });
    }
    poll();
  };

  // ── User Management (admin) ──────────────────────────────────────────
  var userListEl = document.getElementById("user-list");
  var addUserBtn = document.getElementById("add-user-btn");
  var newUserEmail = document.getElementById("new-user-email");
  var newUserPass = document.getElementById("new-user-pass");

  function loadUsers() {
    if (!ws || ws.readyState !== 1 || !isAdmin) return;
    ws.send(JSON.stringify({action: "list_users"}));
  }

  function renderUsers(users) {
    if (!users || users.length === 0) {
      userListEl.innerHTML = \x27<div class="empty">No users</div>\x27;
      return;
    }
    var html = \x27<table class="user-table">\x27;
    html += \x27<tr><th>Email</th><th>Created</th><th></th></tr>\x27;
    users.forEach(function(u) {
      var created = u.created_at ? new Date(u.created_at).toLocaleDateString() : "—";
      html += \x27<tr>\x27;
      html += \x27<td>\x27 + (u.email || "—") + \x27</td>\x27;
      html += \x27<td style="color:var(--muted)">\x27 + created + \x27</td>\x27;
      html += \x27<td style="text-align:right;"><button class="stop" style="border-radius:4px;" onclick="window._deleteUser(\x27 + "\x27" + u.id + "\x27" + \x27)">Delete</button></td>\x27;
      html += \x27</tr>\x27;
    });
    html += \x27</table>\x27;
    userListEl.innerHTML = html;
  }

  window._deleteUser = function(uid) {
    if (!confirm("Delete this user? They will no longer be able to sign in.")) return;
    if (ws && ws.readyState === 1) {
      ws.send(JSON.stringify({action: "delete_user", user_id: uid}));
    }
  };

  addUserBtn.addEventListener("click", function() {
    var email = newUserEmail.value.trim();
    var pass = newUserPass.value;
    if (!email || !pass) { showError("Enter email and password"); return; }
    if (pass.length < 6) { showError("Password must be at least 6 characters"); return; }
    if (ws && ws.readyState === 1) {
      ws.send(JSON.stringify({action: "create_user", email: email, password: pass}));
      newUserEmail.value = "";
      newUserPass.value = "";
    }
  });

  // Periodic refresh of recordings (restore link state after rebuild)
  setInterval(function() {
    loadRecordings();
    if (isAdmin) { loadDashboard(); loadAdminSessions(); }
    setTimeout(function() { applyMp3State(); applyVideoState(); }, 500);
  }, 15000);
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
<title>SageRock AI — Live Translation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #1a1e23;
    --bg-card:   #20262d;
    --border:    #2e3740;
    --sage:      #6B8F71;
    --sage-light:#7fa885;
    --stone:     #C4A882;
    --cream:     #F5F0E8;
    --cream-dim: #c8c2b8;
    --muted:     #7a8390;
    --danger:    #c0645a;
    --shadow:    0 8px 40px rgba(0,0,0,.4);
  }

  body {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    background:
      radial-gradient(ellipse 70% 50% at 50% 0%, rgba(107,143,113,.1) 0%, transparent 60%),
      var(--bg);
    color: var(--cream);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    animation: fadeIn .5s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: .4; }
  }

  @keyframes waveIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── Brand ─────────────────────────────────────────────────────── */
  .brand {
    text-align: center;
    margin-bottom: 2.5rem;
  }

  .brand-sage {
    font-family: "DM Serif Display", Georgia, serif;
    font-style: italic;
    font-size: 1.7rem;
    color: var(--cream);
  }

  .brand-rock {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    font-weight: 700;
    font-size: 1.7rem;
    color: var(--cream);
    letter-spacing: -.03em;
  }

  .brand-ai {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    font-weight: 600;
    font-size: 1.7rem;
    color: var(--sage);
  }

  .brand-tagline {
    display: block;
    font-size: .65rem;
    font-weight: 500;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--stone);
    margin-top: .2rem;
  }

  /* ── Card ───────────────────────────────────────────────────────── */
  .card {
    width: 100%;
    max-width: 420px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: var(--shadow);
    text-align: center;
  }

  /* ── Language label ─────────────────────────────────────────────── */
  .lang-label {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 1.4rem;
    color: var(--stone);
    margin-bottom: 1.8rem;
    letter-spacing: .01em;
  }

  /* ── Start button ───────────────────────────────────────────────── */
  .start-btn {
    background: var(--sage);
    color: #fff;
    border: none;
    padding: .85rem 2.5rem;
    border-radius: 50px;
    font-family: "Plus Jakarta Sans", inherit;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    letter-spacing: .03em;
    transition: background .2s, box-shadow .2s, transform .1s;
    box-shadow: 0 4px 20px rgba(107,143,113,.35);
    margin-bottom: 1.5rem;
  }

  .start-btn:hover {
    background: var(--sage-light);
    box-shadow: 0 6px 28px rgba(107,143,113,.45);
  }

  .start-btn:active { transform: scale(.97); }

  /* ── Status badge ───────────────────────────────────────────────── */
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    padding: .35rem 1rem;
    border-radius: 20px;
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    margin-bottom: 1.8rem;
    transition: background .3s, color .3s;
  }

  .status-badge::before {
    content: "";
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .status-badge.connected {
    background: rgba(107,143,113,.15);
    color: var(--sage-light);
    border: 1px solid rgba(107,143,113,.3);
  }

  .status-badge.connected::before {
    background: var(--sage-light);
    box-shadow: 0 0 6px var(--sage);
    animation: pulse 2s infinite;
  }

  .status-badge.disconnected {
    background: rgba(192,100,90,.1);
    color: #c07070;
    border: 1px solid rgba(192,100,90,.25);
  }

  .status-badge.disconnected::before { background: var(--danger); }

  .status-badge.connecting {
    background: rgba(196,168,130,.1);
    color: var(--stone);
    border: 1px solid rgba(196,168,130,.25);
  }

  .status-badge.connecting::before {
    background: var(--stone);
    animation: pulse 1s infinite;
  }

  /* ── Transcript area ─────────────────────────────────────────────── */
  .subtitle {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 1.25rem;
    font-weight: 400;
    color: var(--cream);
    margin-bottom: .4rem;
    min-height: 1.8rem;
    line-height: 1.4;
    animation: waveIn .3s ease;
  }

  .original {
    font-size: .83rem;
    color: var(--muted);
    font-style: italic;
    margin-bottom: 1.4rem;
    min-height: 1.2rem;
  }

  /* ── Activity indicator ─────────────────────────────────────────── */
  .activity {
    font-size: .82rem;
    color: var(--muted);
    min-height: 1.4rem;
    font-weight: 500;
    letter-spacing: .02em;
  }

  .activity.playing {
    color: var(--sage-light);
  }

  .activity.playing::before {
    content: "▶ ";
    font-size: .7rem;
  }

  /* ── Clip count ─────────────────────────────────────────────────── */
  .clip-count {
    font-size: .72rem;
    color: var(--muted);
    margin-top: 1.2rem;
    opacity: .7;
  }

  .hidden { display: none; }
</style>
</head>
<body>

<div class="brand">
  <img src="data:image/png;base64,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" alt="SageRock AI" style="height:56px;margin-bottom:8px;">
  <span class="brand-tagline">Live Translation</span>
</div>

<div class="card">
  <div class="lang-label" id="lang-label"></div>
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


MEETING_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SageRock AI — Meeting Notes</title>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #1a1e23;
    --bg-card:   #20262d;
    --bg-input:  #161b21;
    --border:    #2e3740;
    --sage:      #6B8F71;
    --sage-light:#7fa885;
    --sage-dark: #546e5a;
    --stone:     #C4A882;
    --stone-dark:#a8906c;
    --cream:     #F5F0E8;
    --cream-dim: #c8c2b8;
    --muted:     #7a8390;
    --danger:    #c0645a;
    --shadow:    0 4px 24px rgba(0,0,0,.35);
    --shadow-sm: 0 2px 8px rgba(0,0,0,.2);
    --radius:    10px;
    --radius-sm: 6px;
  }

  body {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    background: var(--bg);
    color: var(--cream);
    min-height: 100vh;
    line-height: 1.6;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── App header ──────────────────────────────────────────────────── */
  .app-header {
    position: sticky;
    top: 0;
    z-index: 10;
    background: rgba(26,30,35,.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: .85rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .brand-sage {
    font-family: "DM Serif Display", Georgia, serif;
    font-style: italic;
    font-size: 1.3rem;
    color: var(--cream);
  }

  .brand-rock {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    font-weight: 700;
    font-size: 1.3rem;
    color: var(--cream);
    letter-spacing: -.03em;
  }

  .brand-ai {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    font-weight: 600;
    font-size: 1.3rem;
    color: var(--sage);
  }

  .back-link {
    font-size: .82rem;
    color: var(--muted);
    text-decoration: none;
    font-weight: 500;
    transition: color .2s;
    display: flex;
    align-items: center;
    gap: .3rem;
  }

  .back-link:hover { color: var(--stone); text-decoration: none; }

  /* ── Container ───────────────────────────────────────────────────── */
  .container {
    max-width: 860px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }

  /* ── Page title ──────────────────────────────────────────────────── */
  .page-title {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 1.7rem;
    font-weight: 400;
    color: var(--cream);
    margin-bottom: .3rem;
    animation: slideUp .4s ease;
  }

  .meta {
    font-size: .8rem;
    color: var(--muted);
    margin-bottom: 1.75rem;
    font-weight: 500;
    animation: slideUp .4s ease .05s both;
  }

  /* ── Section cards ───────────────────────────────────────────────── */
  .section {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.6rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-sm);
    animation: slideUp .4s ease both;
  }

  .section:nth-child(1) { animation-delay: .08s; }
  .section:nth-child(2) { animation-delay: .14s; }
  .section:nth-child(3) { animation-delay: .20s; }

  .section h2 {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 1rem;
    font-weight: 400;
    color: var(--stone);
    margin-bottom: 1rem;
    letter-spacing: .01em;
    display: flex;
    align-items: center;
    gap: .5rem;
  }

  .section h2::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  /* ── Summary content (markdown) ──────────────────────────────────── */
  .summary-content { line-height: 1.7; color: var(--cream-dim); }
  .summary-content h1, .summary-content h2, .summary-content h3 {
    font-family: "DM Serif Display", Georgia, serif;
    font-weight: 400;
    color: var(--cream);
    margin-top: 1.2rem;
    margin-bottom: .5rem;
  }
  .summary-content h1 { font-size: 1.2rem; }
  .summary-content h2 { font-size: 1.05rem; }
  .summary-content h3 { font-size: .95rem; color: var(--stone); }
  .summary-content ul, .summary-content ol { padding-left: 1.4rem; margin: .6rem 0; }
  .summary-content li { margin-bottom: .3rem; }
  .summary-content strong { color: var(--cream); font-weight: 600; }
  .summary-content p { margin-bottom: .7rem; }

  /* ── Search box ──────────────────────────────────────────────────── */
  .search-box {
    width: 100%;
    padding: .6rem .9rem;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: inherit;
    color: var(--cream);
    font-size: .88rem;
    margin-bottom: .9rem;
    transition: border-color .2s, box-shadow .2s;
  }

  .search-box:focus {
    outline: none;
    border-color: var(--sage);
    box-shadow: 0 0 0 3px rgba(107,143,113,.15);
  }

  .search-box::placeholder { color: var(--muted); }

  /* ── Transcript ───────────────────────────────────────────────────── */
  .transcript {
    max-height: 480px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }

  .transcript::-webkit-scrollbar { width: 4px; }
  .transcript::-webkit-scrollbar-track { background: transparent; }
  .transcript::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .utterance {
    padding: .6rem 0;
    border-bottom: 1px solid rgba(46,55,64,.6);
    font-size: .84rem;
    line-height: 1.55;
    display: flex;
    gap: .5rem;
  }

  .utterance:last-child { border-bottom: none; }

  .utterance .time {
    color: var(--muted);
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: .72rem;
    flex-shrink: 0;
    padding-top: .1rem;
    opacity: .7;
  }

  .utterance .speaker {
    color: var(--sage-light);
    font-weight: 600;
    font-size: .8rem;
    flex-shrink: 0;
    padding-top: .05rem;
  }

  .utterance .text { color: var(--cream-dim); }

  /* ── Chat ────────────────────────────────────────────────────────── */
  .chat-messages {
    margin-bottom: 1rem;
    max-height: 320px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }

  .chat-messages::-webkit-scrollbar { width: 4px; }
  .chat-messages::-webkit-scrollbar-track { background: transparent; }
  .chat-messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .chat-msg {
    padding: .7rem 1rem;
    margin-bottom: .6rem;
    border-radius: var(--radius-sm);
    font-size: .85rem;
    line-height: 1.55;
    animation: slideUp .2s ease;
  }

  .chat-msg.user {
    background: rgba(107,143,113,.12);
    border: 1px solid rgba(107,143,113,.2);
    text-align: right;
    color: var(--cream-dim);
  }

  .chat-msg.assistant {
    background: var(--bg-input);
    border: 1px solid var(--border);
    color: var(--cream-dim);
  }

  .chat-msg.assistant p { margin-bottom: .5rem; }
  .chat-msg.assistant ul,
  .chat-msg.assistant ol { padding-left: 1.4rem; margin: .4rem 0; }

  .chat-box {
    display: flex;
    gap: .6rem;
  }

  .chat-input {
    flex: 1;
    padding: .65rem .9rem;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: inherit;
    color: var(--cream);
    font-size: .88rem;
    transition: border-color .2s, box-shadow .2s;
  }

  .chat-input:focus {
    outline: none;
    border-color: var(--sage);
    box-shadow: 0 0 0 3px rgba(107,143,113,.15);
  }

  .chat-input::placeholder { color: var(--muted); }

  .chat-send {
    padding: .65rem 1.3rem;
    background: var(--sage-dark);
    border: none;
    border-radius: var(--radius-sm);
    font-family: inherit;
    color: #fff;
    font-size: .88rem;
    font-weight: 600;
    cursor: pointer;
    transition: background .2s, box-shadow .2s;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(107,143,113,.25);
  }

  .chat-send:hover { background: var(--sage); box-shadow: 0 4px 14px rgba(107,143,113,.35); }
  .chat-send:disabled { opacity: .45; cursor: default; box-shadow: none; }

  /* ── Loading ─────────────────────────────────────────────────────── */
  .loading {
    color: var(--muted);
    font-style: italic;
    font-size: .88rem;
  }

  /* ── Auth / login screen ─────────────────────────────────────────── */
  #login-screen {
    min-height: 100vh;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background:
      radial-gradient(ellipse 80% 60% at 30% 20%, rgba(107,143,113,.1) 0%, transparent 60%),
      var(--bg);
  }

  #login-screen.visible {
    display: flex;
    animation: fadeIn .4s ease;
  }

  .login-card {
    width: 100%;
    max-width: 360px;
    background: var(--bg-card);
    border: 1px solid rgba(196,168,130,.2);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: var(--shadow);
  }

  .login-brand {
    text-align: center;
    margin-bottom: 1.75rem;
  }

  .login-brand .brand-sage { font-size: 2rem; }
  .login-brand .brand-rock { font-size: 2rem; }
  .login-brand .brand-ai   { font-size: 2rem; }

  .login-brand .brand-tagline {
    display: block;
    font-size: .65rem;
    font-weight: 500;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--stone);
    margin-top: .25rem;
  }

  .auth-field { margin-bottom: .9rem; }

  .auth-field label {
    display: block;
    font-size: .75rem;
    font-weight: 600;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: .4rem;
  }

  .auth-field input {
    width: 100%;
    padding: .65rem .9rem;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: inherit;
    color: var(--cream);
    font-size: .92rem;
    transition: border-color .2s, box-shadow .2s;
  }

  .auth-field input:focus {
    outline: none;
    border-color: var(--sage);
    box-shadow: 0 0 0 3px rgba(107,143,113,.15);
  }

  .auth-btn {
    width: 100%;
    padding: .75rem;
    background: var(--sage);
    border: none;
    border-radius: var(--radius-sm);
    font-family: inherit;
    color: #fff;
    font-size: .95rem;
    font-weight: 700;
    cursor: pointer;
    margin-top: .5rem;
    transition: background .2s, box-shadow .2s;
    box-shadow: 0 2px 8px rgba(107,143,113,.3);
  }

  .auth-btn:hover { background: var(--sage-light); }

  .auth-error {
    color: #e08080;
    font-size: .82rem;
    margin-top: .7rem;
    display: none;
    padding: .45rem .8rem;
    background: rgba(192,100,90,.1);
    border: 1px solid rgba(192,100,90,.25);
    border-radius: var(--radius-sm);
  }

  /* ── Links ───────────────────────────────────────────────────────── */
  a { color: var(--sage-light); text-decoration: none; }
  a:hover { color: var(--stone); text-decoration: underline; }
</style>
</head>
<body>

<div id="login-screen">
  <div class="login-card">
    <div class="login-brand">
      <img src="data:image/png;base64,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" alt="SageRock AI" style="height:40px;margin-bottom:12px;">
      <span class="brand-tagline">Meeting Intelligence</span>
    </div>
    <div class="auth-field">
      <label>Email</label>
      <input type="email" id="auth-email" placeholder="you@example.com">
    </div>
    <div class="auth-field">
      <label>Password</label>
      <input type="password" id="auth-password" placeholder="Password">
    </div>
    <button class="auth-btn" id="signin-btn">Sign In</button>
    <div class="auth-error" id="auth-error"></div>
  </div>
</div>

<div id="main-app" style="display:none;">
  <header class="app-header">
    <div>
      <img src="data:image/png;base64,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" alt="SageRock AI" style="height:32px;">
    </div>
    <a href="/" class="back-link">&larr; Dashboard</a>
  </header>

  <div class="container">
    <div class="page-title">Meeting Notes</div>
    <div class="meta" id="meeting-meta"></div>

    <div class="section" id="summary-section">
      <h2>Summary</h2>
      <div class="summary-content" id="summary-content"><span class="loading">Loading...</span></div>
    </div>

    <div class="section">
      <h2>Transcript</h2>
      <input type="text" class="search-box" id="transcript-search" placeholder="Search transcript...">
      <div class="transcript" id="transcript-content"><span class="loading">Loading...</span></div>
    </div>

    <div class="section">
      <h2>Ask a Question</h2>
      <div class="chat-messages" id="chat-messages"></div>
      <div class="chat-box">
        <input type="text" class="chat-input" id="chat-input" placeholder="Ask about this meeting...">
        <button class="chat-send" id="chat-send" disabled>Ask</button>
      </div>
    </div>
  </div>
</div>

<script>
(function() {
  var sbUrl = "__SUPABASE_URL__";
  var sbKey = "__SUPABASE_ANON_KEY__";
  var botId = "__BOT_ID__";

  if (typeof supabase === "undefined") {
    document.getElementById("auth-error").textContent = "Supabase JS failed to load";
    document.getElementById("auth-error").style.display = "block";
    return;
  }
  var sb = supabase.createClient(sbUrl, sbKey);
  var accessToken = null;
  var ws = null;
  var transcriptData = [];

  var loginScreen = document.getElementById("login-screen");
  var mainApp = document.getElementById("main-app");
  var authError = document.getElementById("auth-error");
  var signinBtn = document.getElementById("signin-btn");
  var summaryContent = document.getElementById("summary-content");
  var transcriptContent = document.getElementById("transcript-content");
  var searchBox = document.getElementById("transcript-search");
  var chatMessages = document.getElementById("chat-messages");
  var chatInput = document.getElementById("chat-input");
  var chatSend = document.getElementById("chat-send");
  var meetingMeta = document.getElementById("meeting-meta");

  function showLogin() {
    loginScreen.style.display = "";
    loginScreen.classList.add("visible");
    mainApp.style.display = "none";
  }
  function showApp() {
    loginScreen.style.display = "none";
    loginScreen.classList.remove("visible");
    mainApp.style.display = "block";
    loadMeeting();
    connectWs();
  }

  sb.auth.onAuthStateChange(function(event, session) {
    if (session && session.access_token) {
      accessToken = session.access_token;
      showApp();
    } else {
      accessToken = null;
      showLogin();
    }
  });

  signinBtn.addEventListener("click", function() {
    var email = document.getElementById("auth-email").value.trim();
    var pass = document.getElementById("auth-password").value;
    if (!email || !pass) { authError.textContent = "Enter email and password"; authError.style.display = "block"; return; }
    sb.auth.signInWithPassword({email: email, password: pass}).then(function(res) {
      if (res.error) { authError.textContent = res.error.message; authError.style.display = "block"; }
    });
  });

  document.getElementById("auth-password").addEventListener("keydown", function(e) {
    if (e.key === "Enter") signinBtn.click();
  });

  function connectWs() {
    if (ws) return;
    var proto = location.protocol === "https:" ? "wss:" : "ws:";
    var url = proto + "//" + location.host + "/mgmt?token=" + accessToken;
    ws = new WebSocket(url);
    ws.onmessage = function(e) {
      var msg = JSON.parse(e.data);
      if (msg.type === "answer") {
        if (msg.bot_id === botId) {
          addChatMessage("assistant", msg.answer);
          chatSend.disabled = false;
          chatSend.textContent = "Ask";
        }
      } else if (msg.type === "error") {
        addChatMessage("assistant", "Error: " + msg.message);
        chatSend.disabled = false;
        chatSend.textContent = "Ask";
      }
    };
    ws.onclose = function() { ws = null; setTimeout(connectWs, 3000); };
  }

  function loadMeeting() {
    fetch("/api/meeting/" + botId, { headers: { "Authorization": "Bearer " + accessToken } })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var date = data.created_at ? new Date(data.created_at).toLocaleString() : "";
        var dur = data.duration ? Math.round(data.duration / 60) + " min" : "";
        meetingMeta.textContent = [date, dur].filter(Boolean).join(" \xb7 ");

        if (data.summary) {
          if (typeof marked !== "undefined") {
            summaryContent.innerHTML = marked.parse(data.summary);
          } else {
            summaryContent.textContent = data.summary;
          }
        } else {
          summaryContent.innerHTML = '<span class="loading">No summary available yet.</span>';
        }

        transcriptData = data.transcript || [];
        renderTranscript(transcriptData);
      })
      .catch(function() {
        summaryContent.innerHTML = '<span class="loading">Failed to load meeting data.</span>';
      });
  }

  function renderTranscript(items) {
    if (!items || items.length === 0) {
      transcriptContent.innerHTML = '<span class="loading">No transcript available.</span>';
      return;
    }
    var html = "";
    for (var i = 0; i < items.length; i++) {
      var t = items[i];
      var elapsed = t.elapsed || 0;
      var mins = Math.floor(elapsed / 60);
      var secs = Math.floor(elapsed % 60);
      var ts = (mins < 10 ? "0" : "") + mins + ":" + (secs < 10 ? "0" : "") + secs;
      var speaker = t.speaker || t.participant_id || "Unknown";
      var text = t.text || t.original || "";
      html += '<div class="utterance">' +
        '<span class="time">' + ts + '</span>' +
        '<span class="speaker">' + speaker + '</span>' +
        '<span class="text">' + text + '</span>' +
      '</div>';
    }
    transcriptContent.innerHTML = html;
  }

  searchBox.addEventListener("input", function() {
    var q = searchBox.value.trim().toLowerCase();
    if (!q) { renderTranscript(transcriptData); return; }
    var filtered = transcriptData.filter(function(t) {
      var text = (t.text || t.original || "").toLowerCase();
      var speaker = (t.speaker || "").toLowerCase();
      return text.indexOf(q) !== -1 || speaker.indexOf(q) !== -1;
    });
    renderTranscript(filtered);
  });

  chatSend.addEventListener("click", function() {
    var q = chatInput.value.trim();
    if (!q || !ws || ws.readyState !== 1) return;
    addChatMessage("user", q);
    chatInput.value = "";
    chatSend.disabled = true;
    chatSend.textContent = "Thinking...";
    ws.send(JSON.stringify({ action: "ask", bot_id: botId, question: q }));
  });

  chatInput.addEventListener("keydown", function(e) {
    if (e.key === "Enter") chatSend.click();
  });

  var enableCheck = setInterval(function() {
    if (ws && ws.readyState === 1) {
      chatSend.disabled = false;
      clearInterval(enableCheck);
    }
  }, 200);

  function addChatMessage(role, text) {
    var div = document.createElement("div");
    div.className = "chat-msg " + role;
    if (role === "assistant" && typeof marked !== "undefined") {
      div.innerHTML = marked.parse(text);
    } else {
      div.textContent = text;
    }
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
})();
</script>
</body>
</html>
"""
