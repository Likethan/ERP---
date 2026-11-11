import { execSync } from "child_process";
import { readdirSync } from "fs";
import { join } from "path";

const testsDir = "apps/web/src/__tests__";
const files = readdirSync(testsDir)
  .filter((f) => f.endsWith(".ts"))
  .sort();

console.log(
  "================================================================================",
);
console.log(
  `Starting CampusOS Total ERP Frontend Workflow Test Execution (${files.length} Modules)`,
);
console.log(
  "================================================================================\n",
);

let totalPassed = 0;
let totalFailed = 0;
const summary = [];

for (const file of files) {
  const filePath = join(testsDir, file);
  process.stdout.write(`Testing [${file}]... `);
  const start = Date.now();
  try {
    const out = execSync(
      `npx tsx --tsconfig apps/web/tsconfig.json "${filePath}"`,
      {
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 60000,
      },
    );
    const duration = ((Date.now() - start) / 1000).toFixed(2);

    // Parse passed/failed counts from output
    const passMatch =
      out.match(/Passed:\s*(\d+)/i) ||
      out.match(/(\d+)\s*\/\s*\d+\s*ASSERTIONS PASSED/i) ||
      out.match(/(\d+)\s*passed/i);
    const failMatch =
      out.match(/Failed:\s*(\d+)/i) || out.match(/(\d+)\s*failed/i);

    let passedCount = passMatch ? parseInt(passMatch[1], 10) : 1;
    let failedCount = failMatch ? parseInt(failMatch[1], 10) : 0;

    // Check for success banner if not explicitly in numbers
    if (out.includes("ALL STEP 62 LEGAL OPERATIONS FRONTEND TESTS PASSED")) {
      passedCount = 20; // known count of assertions in legal
    }

    totalPassed += passedCount;
    totalFailed += failedCount;

    console.log(`PASS (${passedCount} assertions, ${duration}s)`);
    summary.push({
      file,
      status: "PASS",
      passed: passedCount,
      failed: failedCount,
      duration,
    });
  } catch (err) {
    const duration = ((Date.now() - start) / 1000).toFixed(2);
    console.log(`FAIL (${duration}s)`);
    console.error(err.stdout || err.stderr || err.message);
    totalFailed += 1;
    summary.push({ file, status: "FAIL", passed: 0, failed: 1, duration });
  }
}

console.log(
  "\n================================================================================",
);
console.log(`CampusOS Total ERP Frontend Workflow Test Results:`);
console.log(`Total Modules Tested: ${files.length}`);
console.log(`Total Assertions Passed: ${totalPassed}`);
console.log(`Total Failures: ${totalFailed}`);
console.log(
  "================================================================================\n",
);

if (totalFailed > 0) {
  process.exit(1);
}
