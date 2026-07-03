"""
Training Calendar Web App
- Reads trainings from the shared SQLite database
- Pushes real-time updates to the browser via Server-Sent Events (SSE)
"""

import sqlite3
import json
import os
import time
import queue
import threading
from datetime import datetime
from flask import Flask, Response, render_template_string, g

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "/data/trainings.db")

# Each SSE client gets a Queue in this list
_clients: list[queue.Queue] = []
_clients_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db:
        db.close()


def fetch_trainings():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT * FROM trainings ORDER BY from_date ASC"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# SSE broadcaster - background thread watches DB for changes
# ---------------------------------------------------------------------------

def _broadcast(data: str):
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(data)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _clients.remove(q)


def _db_watcher():
    """Poll the DB every 2 seconds and broadcast changes."""
    last_snapshot = None
    while True:
        try:
            trainings = fetch_trainings()
            snapshot = json.dumps(trainings, sort_keys=True)
            if snapshot != last_snapshot:
                last_snapshot = snapshot
                _broadcast(snapshot)
        except Exception:
            pass
        time.sleep(2)


watcher_thread = threading.Thread(target=_db_watcher, daemon=True)
watcher_thread.start()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/stream")
def stream():
    """SSE endpoint - each browser tab gets its own queue."""
    client_queue: queue.Queue = queue.Queue(maxsize=10)
    with _clients_lock:
        _clients.append(client_queue)

    def event_generator():
        try:
            # Send current data immediately on connect
            try:
                trainings = fetch_trainings()
                yield f"data: {json.dumps(trainings)}\n\n"
            except Exception:
                yield "data: []\n\n"

            while True:
                try:
                    data = client_queue.get(timeout=30)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    # Send a heartbeat comment to keep the connection alive
                    yield ": heartbeat\n\n"
        finally:
            with _clients_lock:
                if client_queue in _clients:
                    _clients.remove(client_queue)

    return Response(
        event_generator(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/trainings")
def api_trainings():
    return json.dumps(fetch_trainings()), 200, {"Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TekTutor Training Calendar</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      min-height: 100vh;
    }

    header {
      background: #1a1f2e;
      border-bottom: 2px solid #e53e3e;
      padding: 16px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    header h1 {
      font-size: 1.5rem;
      font-weight: 700;
      color: #fff;
    }

    header h1 span { color: #e53e3e; }

    #status-dot {
      width: 10px; height: 10px;
      border-radius: 50%;
      background: #48bb78;
      display: inline-block;
      margin-right: 8px;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0.4; }
    }

    #status-bar {
      font-size: 0.8rem;
      color: #718096;
      display: flex;
      align-items: center;
    }

    main { padding: 32px; }

    #summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }

    .stat-card {
      background: #1a1f2e;
      border-radius: 8px;
      padding: 20px;
      border-left: 4px solid #e53e3e;
      text-align: center;
    }

    .stat-card .number { font-size: 2rem; font-weight: 700; color: #e53e3e; }
    .stat-card .label  { font-size: 0.8rem; color: #718096; margin-top: 4px; }

    table {
      width: 100%;
      border-collapse: collapse;
      background: #1a1f2e;
      border-radius: 8px;
      overflow: hidden;
    }

    thead { background: #e53e3e; }
    thead th {
      padding: 14px 16px;
      text-align: left;
      font-size: 0.85rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #fff;
    }

    tbody tr {
      border-bottom: 1px solid #2d3748;
      transition: background 0.15s;
    }
    tbody tr:hover { background: #2d3748; }
    tbody tr.new-row { animation: flashRow 1.5s ease; }

    @keyframes flashRow {
      0%   { background: #276749; }
      100% { background: transparent; }
    }

    td {
      padding: 14px 16px;
      font-size: 0.9rem;
      color: #cbd5e0;
    }

    td:first-child { font-weight: 600; color: #e2e8f0; }

    .badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .badge-online    { background: #2b6cb0; color: #bee3f8; }
    .badge-classroom { background: #276749; color: #c6f6d5; }

    .badge-upcoming { background: #744210; color: #fefcbf; }
    .badge-active   { background: #276749; color: #c6f6d5; }
    .badge-past     { background: #2d3748; color: #718096; }

    #empty-state {
      text-align: center;
      padding: 60px;
      color: #4a5568;
    }

    #empty-state p { margin-top: 8px; font-size: 0.85rem; }

    #last-updated {
      text-align: right;
      font-size: 0.75rem;
      color: #4a5568;
      margin-top: 16px;
    }
  </style>
</head>
<body>

<header>
  <h1><span>TekTutor</span> Training Calendar</h1>
  <div id="status-bar">
    <span id="status-dot"></span>
    <span id="status-text">Connecting...</span>
  </div>
</header>

<main>
  <div id="summary">
    <div class="stat-card">
      <div class="number" id="stat-total">0</div>
      <div class="label">Total Trainings</div>
    </div>
    <div class="stat-card">
      <div class="number" id="stat-online">0</div>
      <div class="label">Online</div>
    </div>
    <div class="stat-card">
      <div class="number" id="stat-classroom">0</div>
      <div class="label">Classroom</div>
    </div>
    <div class="stat-card">
      <div class="number" id="stat-active">0</div>
      <div class="label">Active Now</div>
    </div>
  </div>

  <table id="calendar-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Training Name</th>
        <th>Duration (days)</th>
        <th>From</th>
        <th>To</th>
        <th>Mode</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody id="calendar-body">
    </tbody>
  </table>

  <div id="empty-state" style="display:none">
    <strong>No trainings scheduled yet.</strong>
    <p>Create a Training custom resource in OpenShift to add one.</p>
  </div>

  <div id="last-updated"></div>
</main>

<script>
  let knownIds = new Set();

  function getStatus(fromDate, toDate) {
    const today = new Date();
    const from  = new Date(fromDate);
    const to    = new Date(toDate);
    if (today < from) return { label: "Upcoming", cls: "badge-upcoming" };
    if (today > to)   return { label: "Past",     cls: "badge-past" };
    return { label: "Active", cls: "badge-active" };
  }

  function render(trainings) {
    const tbody  = document.getElementById("calendar-body");
    const empty  = document.getElementById("empty-state");
    const table  = document.getElementById("calendar-table");

    // Stats
    const online    = trainings.filter(t => t.mode === "Online").length;
    const classroom = trainings.filter(t => t.mode === "Classroom").length;
    const today     = new Date();
    const active    = trainings.filter(t => {
      return new Date(t.from_date) <= today && new Date(t.to_date) >= today;
    }).length;

    document.getElementById("stat-total").textContent     = trainings.length;
    document.getElementById("stat-online").textContent    = online;
    document.getElementById("stat-classroom").textContent = classroom;
    document.getElementById("stat-active").textContent    = active;

    if (trainings.length === 0) {
      table.style.display = "none";
      empty.style.display = "block";
    } else {
      table.style.display = "table";
      empty.style.display = "none";
    }

    tbody.innerHTML = "";
    trainings.forEach((t, idx) => {
      const isNew = !knownIds.has(t.id);
      const status = getStatus(t.from_date, t.to_date);
      const modeCls = t.mode === "Online" ? "badge-online" : "badge-classroom";

      const tr = document.createElement("tr");
      if (isNew && knownIds.size > 0) tr.classList.add("new-row");

      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td>${t.training_name}</td>
        <td>${t.duration}</td>
        <td>${t.from_date}</td>
        <td>${t.to_date}</td>
        <td><span class="badge ${modeCls}">${t.mode}</span></td>
        <td><span class="badge ${status.cls}">${status.label}</span></td>
      `;
      tbody.appendChild(tr);
    });

    knownIds = new Set(trainings.map(t => t.id));

    const now = new Date().toLocaleTimeString();
    document.getElementById("last-updated").textContent = `Last updated: ${now}`;
  }

  // SSE connection
  function connect() {
    const es = new EventSource("/stream");

    es.onopen = () => {
      document.getElementById("status-text").textContent = "Live";
      document.getElementById("status-dot").style.background = "#48bb78";
    };

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);
      render(data);
    };

    es.onerror = () => {
      document.getElementById("status-text").textContent = "Reconnecting...";
      document.getElementById("status-dot").style.background = "#e53e3e";
      es.close();
      setTimeout(connect, 3000);
    };
  }

  connect();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
