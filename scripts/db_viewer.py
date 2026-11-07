"""CampusOS Interactive Database Web Visualizer.

Runs on http://localhost:5434
Provides an interactive web dashboard to browse tables, inspect rows, view students,
and run SQL queries directly on the PostgreSQL database.
"""

import os
import sys
import webbrowser
from pathlib import Path

workspace_root = Path(__file__).resolve().parent.parent
api_dir = workspace_root / "apps" / "api"
sys.path.insert(0, str(api_dir))
os.chdir(api_dir)

import uvicorn
from app.core.database import AsyncSessionLocal
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import text

app = FastAPI(title="CampusOS Database Visualizer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CampusOS — Database Visualizer</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#fefce8',
              100: '#fef9c3',
              400: '#facc15',
              500: '#eab308',
              600: '#ca8a04',
            }
          }
        }
      }
    }
  </script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    /* Custom scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #eab308; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans">

  <!-- Top Navbar -->
  <header class="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
    <div class="flex items-center space-x-3">
      <div class="w-9 h-9 rounded-lg bg-brand-500 text-slate-950 font-black flex items-center justify-center text-lg shadow-lg shadow-brand-500/20">
        <i class="fa-solid fa-database"></i>
      </div>
      <div>
        <h1 class="font-bold text-base tracking-wide flex items-center gap-2">
          CampusOS <span class="text-brand-400 font-semibold text-xs px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">Database Explorer</span>
        </h1>
        <p class="text-xs text-slate-400">PostgreSQL 16 @ 127.0.0.1:5433 / <span class="text-slate-300 font-mono">campusos_db</span></p>
      </div>
    </div>

    <!-- Quick Navigation Links -->
    <div class="flex items-center space-x-2">
      <button onclick="switchTab('students')" id="btn-students" class="tab-btn px-3 py-1.5 rounded-md text-xs font-medium bg-brand-500 text-slate-950 hover:bg-brand-400 transition-all">
        <i class="fa-solid fa-user-graduate mr-1.5"></i> Students Roster
      </button>
      <button onclick="switchTab('tables')" id="btn-tables" class="tab-btn px-3 py-1.5 rounded-md text-xs font-medium bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-all">
        <i class="fa-solid fa-table-list mr-1.5"></i> All Tables (<span id="total-tables-badge">...</span>)
      </button>
      <button onclick="switchTab('sql')" id="btn-sql" class="tab-btn px-3 py-1.5 rounded-md text-xs font-medium bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-all">
        <i class="fa-solid fa-terminal mr-1.5"></i> SQL Console
      </button>
      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 ml-2">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span> Connected
      </span>
    </div>
  </header>

  <!-- Main Body Layout -->
  <div class="flex-1 flex overflow-hidden">
    
    <!-- Left Sidebar: Tables List -->
    <aside class="w-72 bg-slate-900/60 border-r border-slate-800 flex flex-col shrink-0">
      <div class="p-3 border-b border-slate-800">
        <div class="relative">
          <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-500 text-xs"></i>
          <input type="text" id="tableSearch" onkeyup="filterTableList()" placeholder="Filter 600+ tables..."
            class="w-full bg-slate-950 text-xs border border-slate-700 rounded-md pl-8 pr-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500">
        </div>
      </div>

      <div class="px-3 py-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex justify-between items-center">
        <span>Database Tables</span>
        <span id="filtered-count" class="text-slate-500"></span>
      </div>

      <div id="tableList" class="flex-1 overflow-y-auto px-2 space-y-0.5 text-xs">
        <div class="p-4 text-center text-slate-500">Loading tables...</div>
      </div>
    </aside>

    <!-- Right Workspace Area -->
    <main class="flex-1 flex flex-col overflow-hidden bg-slate-950 p-5">

      <!-- VIEW 1: Students Roster -->
      <section id="view-students" class="view-panel flex-1 flex flex-col overflow-hidden">
        <div class="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h2 class="text-lg font-bold text-slate-100 flex items-center gap-2">
              <i class="fa-solid fa-user-graduate text-brand-400"></i> Registered Student Records
            </h2>
            <p class="text-xs text-slate-400">Live student cohort queried from <span class="font-mono text-brand-300">people_students</span> joined with <span class="font-mono text-brand-300">people_users</span></p>
          </div>
          <div class="flex items-center gap-3">
            <span id="students-count" class="text-xs bg-brand-500/10 text-brand-400 px-3 py-1 rounded-full border border-brand-500/20 font-semibold">12 Students Enrolled</span>
            <button onclick="loadStudents()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded border border-slate-700 flex items-center gap-1.5">
              <i class="fa-solid fa-rotate"></i> Refresh
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-auto mt-4 rounded-lg border border-slate-800 bg-slate-900/30">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="bg-slate-900 text-slate-400 font-semibold sticky top-0 border-b border-slate-800">
              <tr>
                <th class="py-2.5 px-4">Roll Number</th>
                <th class="py-2.5 px-4">Student Name</th>
                <th class="py-2.5 px-4">Email</th>
                <th class="py-2.5 px-4">DOB</th>
                <th class="py-2.5 px-4">Gender</th>
                <th class="py-2.5 px-4">Blood Group</th>
                <th class="py-2.5 px-4">Program / Batch</th>
                <th class="py-2.5 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody id="students-tbody" class="divide-y divide-slate-800/60 font-mono">
              <tr><td colspan="8" class="text-center py-8 text-slate-500">Loading student records...</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- VIEW 2: Dynamic Table Data Browser -->
      <section id="view-tables" class="view-panel hidden flex-1 flex flex-col overflow-hidden">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h2 id="current-table-title" class="text-lg font-bold text-slate-100 flex items-center gap-2">
              <i class="fa-solid fa-table text-brand-400"></i> <span id="current-table-name">Select a table</span>
            </h2>
            <p id="current-table-meta" class="text-xs text-slate-400">Click a table on the left to browse rows</p>
          </div>
          <div class="flex items-center gap-2">
            <input type="text" id="rowSearchInput" onkeyup="filterRows()" placeholder="Search in table rows..."
              class="bg-slate-900 text-xs border border-slate-700 rounded px-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500">
            <button onclick="refreshCurrentTable()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded border border-slate-700">
              <i class="fa-solid fa-rotate"></i>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-auto mt-4 rounded-lg border border-slate-800 bg-slate-900/30" id="tableDataContainer">
          <div class="p-12 text-center text-slate-500">Select any table from the left panel to inspect its records.</div>
        </div>
      </section>

      <!-- VIEW 3: SQL Runner -->
      <section id="view-sql" class="view-panel hidden flex-1 flex flex-col overflow-hidden">
        <div class="pb-3 border-b border-slate-800 flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold text-slate-100 flex items-center gap-2">
              <i class="fa-solid fa-terminal text-brand-400"></i> Interactive SQL Console
            </h2>
            <p class="text-xs text-slate-400">Execute custom queries on <span class="font-mono text-brand-300">campusos_db</span> (Port 5433)</p>
          </div>
          <div class="flex gap-2">
            <button onclick="setQuery('SELECT count(*) FROM information_schema.tables WHERE table_schema=\\'public\\';')" class="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded border border-slate-700">Count Tables</button>
            <button onclick="setQuery('SELECT email, first_name, last_name, status FROM people_users LIMIT 15;')" class="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded border border-slate-700">Sample Users</button>
            <button onclick="setQuery('SELECT roll_number, admission_number, status, date_of_birth FROM people_students;')" class="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded border border-slate-700">All Students</button>
          </div>
        </div>

        <div class="mt-4 flex flex-col gap-3">
          <div class="relative">
            <textarea id="sqlInput" rows="4"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs font-mono text-brand-200 focus:outline-none focus:border-brand-500"
              placeholder="Enter your SQL query, e.g. SELECT * FROM people_users LIMIT 20;"></textarea>
            <button onclick="runQuery()" class="absolute bottom-3 right-3 bg-brand-500 hover:bg-brand-400 text-slate-950 font-bold text-xs px-4 py-1.5 rounded shadow-lg shadow-brand-500/20 transition-all flex items-center gap-1.5">
              <i class="fa-solid fa-play"></i> Execute
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-auto mt-3 rounded-lg border border-slate-800 bg-slate-900/30" id="sqlResultsContainer">
          <div class="p-8 text-center text-slate-500 text-xs">Run a query above to visualize rows.</div>
        </div>
      </section>

    </main>
  </div>

  <script>
    let allTables = [];
    let currentTable = null;
    let currentTableRows = [];

    // Switch Tabs
    function switchTab(tab) {
      document.querySelectorAll('.view-panel').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('bg-brand-500', 'text-slate-950');
        btn.classList.add('bg-slate-800', 'text-slate-300');
      });

      document.getElementById('view-' + tab).classList.remove('hidden');
      const activeBtn = document.getElementById('btn-' + tab);
      activeBtn.classList.remove('bg-slate-800', 'text-slate-300');
      activeBtn.classList.add('bg-brand-500', 'text-slate-950');

      if (tab === 'students') loadStudents();
    }

    // Load tables list
    async function loadTables() {
      try {
        const res = await fetch('/api/tables');
        allTables = await res.json();
        document.getElementById('total-tables-badge').innerText = allTables.length;
        renderTableList(allTables);
      } catch (err) {
        console.error('Error loading tables:', err);
      }
    }

    function renderTableList(tables) {
      const listEl = document.getElementById('tableList');
      document.getElementById('filtered-count').innerText = `${tables.length}`;
      listEl.innerHTML = '';
      tables.forEach(t => {
        const item = document.createElement('button');
        item.className = 'w-full text-left px-2.5 py-1.5 rounded flex items-center justify-between hover:bg-slate-800 text-slate-300 hover:text-brand-300 transition-colors group';
        item.onclick = () => viewTable(t.name);
        item.innerHTML = `
          <span class="truncate flex items-center gap-1.5">
            <i class="fa-regular fa-table text-slate-500 group-hover:text-brand-400 text-[10px]"></i>
            <span class="font-mono text-[11px]">${t.name}</span>
          </span>
          <span class="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded font-mono">${t.rows ?? ''}</span>
        `;
        listEl.appendChild(item);
      });
    }

    function filterTableList() {
      const q = document.getElementById('tableSearch').value.toLowerCase();
      const filtered = allTables.filter(t => t.name.toLowerCase().includes(q));
      renderTableList(filtered);
    }

    // Load Students Roster View
    async function loadStudents() {
      const tbody = document.getElementById('students-tbody');
      tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-slate-500">Loading student records...</td></tr>';
      try {
        const res = await fetch('/api/students-overview');
        const students = await res.json();
        document.getElementById('students-count').innerText = `${students.length} Students Enrolled`;
        tbody.innerHTML = '';
        if (students.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-slate-500">No students found.</td></tr>';
          return;
        }
        students.forEach(s => {
          const tr = document.createElement('tr');
          tr.className = 'hover:bg-slate-800/40 transition-colors';
          tr.innerHTML = `
            <td class="py-2.5 px-4 font-bold text-brand-400">${s.roll_number}</td>
            <td class="py-2.5 px-4 text-slate-100 font-sans font-medium">${s.first_name} ${s.last_name}</td>
            <td class="py-2.5 px-4 text-slate-400">${s.email}</td>
            <td class="py-2.5 px-4">${s.dob}</td>
            <td class="py-2.5 px-4"><span class="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">${s.gender}</span></td>
            <td class="py-2.5 px-4 font-semibold text-rose-300">${s.blood_group || '-'}</td>
            <td class="py-2.5 px-4 text-slate-400 text-[11px] font-sans">${s.program_code || 'BTECH-CSE'} / ${s.batch_name || '2024-2028'}</td>
            <td class="py-2.5 px-4 text-center">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ACTIVE
              </span>
            </td>
          `;
          tbody.appendChild(tr);
        });
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-rose-400 font-sans">Error loading students: ${err.message}</td></tr>`;
      }
    }

    // Inspect individual table
    async function viewTable(tableName) {
      currentTable = tableName;
      switchTab('tables');
      document.getElementById('current-table-name').innerText = tableName;
      document.getElementById('current-table-meta').innerText = 'Fetching rows...';
      const container = document.getElementById('tableDataContainer');
      container.innerHTML = '<div class="p-8 text-center text-slate-500 text-xs">Loading records...</div>';

      try {
        const res = await fetch(`/api/table/${tableName}?limit=100`);
        const data = await res.json();
        currentTableRows = data.rows;
        document.getElementById('current-table-meta').innerText = `Showing ${data.rows.length} row(s) | Table: ${tableName}`;
        renderGrid(container, data.columns, data.rows);
      } catch (err) {
        container.innerHTML = `<div class="p-8 text-center text-rose-400 text-xs">Failed to load table: ${err.message}</div>`;
      }
    }

    function refreshCurrentTable() {
      if (currentTable) viewTable(currentTable);
    }

    // Helper: Render data grid
    function renderGrid(container, columns, rows) {
      if (!rows || rows.length === 0) {
        container.innerHTML = '<div class="p-12 text-center text-slate-500 text-xs">Table is empty (0 records).</div>';
        return;
      }
      let html = '<table class="w-full text-left text-xs text-slate-300 font-mono">';
      html += '<thead class="bg-slate-900 text-slate-400 font-semibold sticky top-0 border-b border-slate-800"><tr>';
      columns.forEach(col => {
        html += `<th class="py-2.5 px-4 whitespace-nowrap">${col}</th>`;
      });
      html += '</tr></thead><tbody class="divide-y divide-slate-800/60">';

      rows.forEach(r => {
        html += '<tr class="hover:bg-slate-800/40 transition-colors">';
        columns.forEach(col => {
          let val = r[col];
          if (val === null || val === undefined) {
            val = '<span class="text-slate-600 italic">null</span>';
          } else if (typeof val === 'boolean') {
            val = val ? '<span class="text-emerald-400">true</span>' : '<span class="text-rose-400">false</span>';
          } else if (typeof val === 'object') {
            val = JSON.stringify(val);
          }
          html += `<td class="py-2 px-4 whitespace-nowrap max-w-xs truncate">${val}</td>`;
        });
        html += '</tr>';
      });
      html += '</tbody></table>';
      container.innerHTML = html;
    }

    function filterRows() {
      const q = document.getElementById('rowSearchInput').value.toLowerCase();
      const container = document.getElementById('tableDataContainer');
      if (!currentTableRows.length) return;
      const columns = Object.keys(currentTableRows[0]);
      const filtered = currentTableRows.filter(row => {
        return Object.values(row).some(v => String(v).toLowerCase().includes(q));
      });
      renderGrid(container, columns, filtered);
    }

    // SQL Runner
    function setQuery(sql) {
      document.getElementById('sqlInput').value = sql;
      runQuery();
    }

    async function runQuery() {
      const query = document.getElementById('sqlInput').value.trim();
      if (!query) return;
      const container = document.getElementById('sqlResultsContainer');
      container.innerHTML = '<div class="p-8 text-center text-slate-500 text-xs">Executing SQL query...</div>';

      try {
        const res = await fetch('/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        });
        const data = await res.json();
        if (data.error) {
          container.innerHTML = `<div class="p-6 text-rose-400 text-xs bg-rose-500/10 border border-rose-500/20 rounded m-4 font-mono">${data.error}</div>`;
          return;
        }
        renderGrid(container, data.columns, data.rows);
      } catch (err) {
        container.innerHTML = `<div class="p-6 text-rose-400 text-xs m-4">Error: ${err.message}</div>`;
      }
    }

    // Init on load
    window.onload = () => {
      loadTables();
      loadStudents();
    };
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTML_CONTENT


@app.get("/api/tables")
async def list_tables():
    async with AsyncSessionLocal() as session:
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        res = await session.execute(query)
        table_names = [row[0] for row in res.fetchall()]

        # Return table list
        return [{"name": name} for name in table_names]


@app.get("/api/students-overview")
async def get_students_overview():
    async with AsyncSessionLocal() as session:
        query = text("""
            SELECT 
                sp.roll_number,
                u.first_name,
                u.last_name,
                u.email,
                sp.date_of_birth as dob,
                sp.gender,
                sp.blood_group,
                p.code as program_code,
                b.name as batch_name,
                sp.status
            FROM people_students sp
            JOIN people_users u ON sp.user_id = u.id
            LEFT JOIN core_programs p ON sp.program_id = p.id
            LEFT JOIN core_batches b ON sp.batch_id = b.id
            ORDER BY sp.roll_number;
        """)
        res = await session.execute(query)
        rows = [dict(row._mapping) for row in res.fetchall()]
        for r in rows:
            if r.get("dob"):
                r["dob"] = str(r["dob"])
        return rows


@app.get("/api/table/{table_name}")
async def get_table_data(table_name: str, limit: int = Query(100, le=500)):
    # Validate table_name contains safe chars only
    if not table_name.isidentifier():
        raise HTTPException(status_code=400, detail="Invalid table name")

    async with AsyncSessionLocal() as session:
        # Fetch columns
        col_res = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :tname 
            ORDER BY ordinal_position;
        """), {"tname": table_name})
        columns = [row[0] for row in col_res.fetchall()]

        # Fetch rows
        query_res = await session.execute(text(f'SELECT * FROM "{table_name}" LIMIT :lim;'), {"lim": limit})
        raw_rows = [dict(row._mapping) for row in query_res.fetchall()]

        # Convert datetimes / UUIDs to strings
        safe_rows = []
        for row in raw_rows:
            clean = {}
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    clean[k] = v.isoformat()
                elif isinstance(v, (str, int, float, bool, type(None))):
                    clean[k] = v
                else:
                    clean[k] = str(v)
            safe_rows.append(clean)

        return {"columns": columns, "rows": safe_rows}


@app.post("/api/query")
async def execute_query(req: QueryRequest):
    sql = req.query.strip()
    if not sql:
        return {"error": "Empty query provided"}

    # Basic safety check (read-only)
    forbidden = ["drop ", "truncate ", "delete from", "update ", "alter ", "create "]
    for word in forbidden:
        if word in sql.lower():
            return {"error": f"Security restriction: {word.strip().upper()} queries are not permitted in this visualizer console."}

    async with AsyncSessionLocal() as session:
        try:
            res = await session.execute(text(sql))
            if not res.returns_rows:
                return {"columns": [], "rows": []}

            columns = list(res.keys())
            raw_rows = [dict(row._mapping) for row in res.fetchall()]

            safe_rows = []
            for row in raw_rows:
                clean = {}
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        clean[k] = v.isoformat()
                    elif isinstance(v, (str, int, float, bool, type(None))):
                        clean[k] = v
                    else:
                        clean[k] = str(v)
                safe_rows.append(clean)

            return {"columns": columns, "rows": safe_rows}
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)}


def open_browser(port: int):
    import time

    time.sleep(1.0)
    try:
        webbrowser.open(f"http://localhost:{port}")
    except OSError:
        pass


def main():
    port = 5434
    print("=" * 70)
    print(" CampusOS Database Web Visualizer")
    print(f" URL: http://localhost:{port}")
    print("=" * 70)
    import threading
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()

