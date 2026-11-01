#!/usr/bin/env node

/**
 * CampusOS Unified Dev Orchestrator
 * Runs Backend API (:8000) and Frontend Web (:3000) together in a single terminal.
 * Handles process lifecycle, output prefixing, space-safe paths, and graceful multi-process termination.
 */

import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";

const rootDir = process.cwd();
const isWin = process.platform === "win32";

// 1. Resolve Python Binary
const winVenv = path.join(
  rootDir,
  "apps",
  "api",
  ".venv",
  "Scripts",
  "python.exe",
);
const unixVenv = path.join(rootDir, "apps", "api", ".venv", "bin", "python");

let pythonBin = isWin ? winVenv : unixVenv;
if (!fs.existsSync(pythonBin)) {
  console.log(
    "\x1b[33m[SETUP] apps/api/.venv not found; falling back to system python...\x1b[0m",
  );
  pythonBin = isWin ? "python.exe" : "python3";
}

console.log(
  "\x1b[36m====================================================\x1b[0m",
);
console.log(
  "\x1b[36m   CampusOS — Unified Full-Stack Dev Server        \x1b[0m",
);
console.log(
  "\x1b[36m====================================================\x1b[0m",
);
console.log(
  "  \x1b[32m• Backend API:\x1b[0m  http://127.0.0.1:8000  (Docs: http://127.0.0.1:8000/docs)",
);
console.log("  \x1b[35m• Frontend Web:\x1b[0m http://localhost:3000");
console.log(
  "  \x1b[90mPress Ctrl+C to terminate both servers together.\x1b[0m\n",
);

function pipeWithPrefix(stream, prefix, colorCode) {
  if (!stream) return;
  const rl = readline.createInterface({ input: stream });
  rl.on("line", (line) => {
    if (!line.trim()) return;
    console.log(`${colorCode}${prefix}\x1b[0m ${line}`);
  });
}

// 2. Spawn Backend API (:8000)
const apiProcess = spawn(
  pythonBin,
  [
    "-m",
    "uvicorn",
    "app.main:app",
    "--reload",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
  ],
  {
    cwd: path.join(rootDir, "apps", "api"),
    shell: false,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1",
    },
  },
);

pipeWithPrefix(apiProcess.stdout, "[API]", "\x1b[36m");
pipeWithPrefix(apiProcess.stderr, "[API]", "\x1b[36m");

// 3. Spawn Frontend Next.js (:3000) via cmd.exe on Windows for safe .cmd invocation
const webProcess = isWin
  ? spawn("cmd.exe", ["/d", "/s", "/c", "npm run dev"], {
      cwd: path.join(rootDir, "apps", "web"),
      windowsVerbatimArguments: true,
      env: {
        ...process.env,
        NODE_OPTIONS: "--max-old-space-size=4096",
        PORT: "3000",
      },
    })
  : spawn("npm", ["run", "dev"], {
      cwd: path.join(rootDir, "apps", "web"),
      env: {
        ...process.env,
        NODE_OPTIONS: "--max-old-space-size=4096",
        PORT: "3000",
      },
    });

pipeWithPrefix(webProcess.stdout, "[WEB]", "\x1b[35m");
pipeWithPrefix(webProcess.stderr, "[WEB]", "\x1b[35m");

// 4. Clean Unified Termination
let shuttingDown = false;

function cleanExit(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log(
    "\n\x1b[33m[SHUTDOWN] Stopping CampusOS Backend and Frontend servers...\x1b[0m",
  );

  const killTree = (proc) => {
    if (!proc || !proc.pid) return;
    try {
      if (isWin) {
        spawn("taskkill", ["/pid", proc.pid.toString(), "/T", "/F"], {
          stdio: "ignore",
        });
      } else {
        process.kill(-proc.pid, "SIGKILL");
      }
    } catch {
      // Process already exited
    }
  };

  killTree(apiProcess);
  killTree(webProcess);

  setTimeout(() => {
    console.log("\x1b[32m[SHUTDOWN] Both servers stopped cleanly.\x1b[0m");
    process.exit(code);
  }, 500);
}

process.on("SIGINT", () => cleanExit(0));
process.on("SIGTERM", () => cleanExit(0));
process.on("exit", () => cleanExit(0));

apiProcess.on("exit", (code) => {
  if (!shuttingDown) {
    console.log(`\x1b[31m[API] Process exited with code ${code}\x1b[0m`);
    cleanExit(code || 1);
  }
});

webProcess.on("exit", (code) => {
  if (!shuttingDown) {
    console.log(`\x1b[31m[WEB] Process exited with code ${code}\x1b[0m`);
    cleanExit(code || 1);
  }
});
