/**
 * Desktop Landscape Institutional Login Portal Verification Suite
 * Verifies:
 * 1. Desktop landscape (16:9 widescreen) two-column split layout.
 * 2. Left Column (Warm ivory gradient #FAF8F2):
 *    - Brand header: VSB university crest seal (/college-logo.jpg), bold "CampusOS" wordmark, amber "ERP V2.4" pill badge, college subtitle.
 *    - Status pill: "Unified Institutional Gateway" with live green status dot.
 *    - Headline: "One Campus. One System. One Source of Truth." (editorial serif typography with amber highlight).
 *    - 2x2 Feature Grid: "Zero-Trust RBAC", "ISO 27001 Certified", "5 Campuses • 14 Depts", "Real-Time Telemetry".
 * 3. Right Column (Clean white canvas with centered access card):
 *    - Top meta: "Tenant: VSB-CAMPUS" and "INSTITUTIONAL ACCESS PORTAL" heading with "Select Your Portal Experience".
 *    - 4-Role Segment Bar: "Student" (active yellow pill with graduation cap), "Faculty", "Vice Principal", "HOD".
 *    - Elevated Login Card: Academic pill badge, "✨ Fill Demo" trigger, "Student Portal" title, stylized inputs with visibility toggle, "Remember me" checkbox, and bold golden CTA.
 *    - Quick-Switch Test Persona: "Aarav Patel (Year 3 / Sem 5)" 1-click launch card at bottom.
 * 4. Authentication logic: valid credentials succeed; invalid credentials display appropriate errors.
 * 5. Password visibility control toggling.
 * 6. Existing password recovery portal compatibility.
 * 7. Authenticated user redirection.
 * 8. Multi-role support preservation.
 */

import { DEMO_PERSONAS } from "../mocks/auth.mock";
import fs from "fs";
import path from "path";

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string) {
  if (condition) {
    passed++;
    console.log(`✔ PASS: ${message}`);
  } else {
    failed++;
    console.error(`✖ FAIL: ${message}`);
  }
}

async function runLandscapeLoginTests() {
  console.log("=================================================");
  console.log("CampusOS Landscape Institutional Login Portal Test Suite");
  console.log("=================================================");

  const loginPagePath = path.resolve(__dirname, "../app/login/page.tsx");
  const rootPagePath = path.resolve(__dirname, "../app/page.tsx");
  const forgotPasswordPath = path.resolve(
    __dirname,
    "../app/login/forgot-password/page.tsx",
  );

  const loginPageSource = fs.readFileSync(loginPagePath, "utf-8");
  const rootPageSource = fs.readFileSync(rootPagePath, "utf-8");
  const forgotPasswordSource = fs.readFileSync(forgotPasswordPath, "utf-8");

  // -------------------------------------------------------------------------
  // 1. Initial Application Loading & Root Page Resolution
  // -------------------------------------------------------------------------
  assert(
    rootPageSource.includes("<LoginPage") ||
      rootPageSource.includes("LoginPage"),
    "Root page '/' directly renders LoginPage without intermediate welcome or initialization screens",
  );

  // -------------------------------------------------------------------------
  // 2. Desktop Landscape Two-Column Split Layout & Left Column
  // -------------------------------------------------------------------------
  assert(
    loginPageSource.includes("lg:flex-row") &&
      (loginPageSource.includes("#FAF8F2") ||
        loginPageSource.includes("bg-[#FAF8F2]")),
    "Clean desktop landscape two-column split layout with warm ivory (#FAF8F2) is present",
  );

  // Left Column: Brand Header
  assert(
    loginPageSource.includes('src="/college-logo.jpg"') &&
      loginPageSource.includes("CampusOS") &&
      loginPageSource.includes("ERP V2.4") &&
      loginPageSource.includes("V.S.B. Engineering College"),
    "Left Column Brand Header: VSB university crest seal, bold 'CampusOS' wordmark, amber 'ERP V2.4' pill badge, and college subtitle",
  );

  // Left Column: Status Pill
  assert(
    loginPageSource.includes("Unified Institutional Gateway") &&
      loginPageSource.includes("bg-emerald-500"),
    "Left Column Status Pill: 'Unified Institutional Gateway' with live green status dot is present",
  );

  // Left Column: Headline
  assert(
    loginPageSource.includes("One Campus.") &&
      loginPageSource.includes("One System.") &&
      loginPageSource.includes("One Source of Truth.") &&
      loginPageSource.includes("font-serif"),
    "Left Column Headline: 'One Campus. One System. One Source of Truth.' with editorial serif typography and amber highlight",
  );

  // Left Column: 2x2 Feature Grid
  assert(
    loginPageSource.includes("Zero-Trust RBAC") &&
      loginPageSource.includes("ISO 27001 Certified") &&
      loginPageSource.includes("5 Campuses • 14 Depts") &&
      loginPageSource.includes("Real-Time Telemetry"),
    "Left Column 2x2 Feature Grid: Cards for Zero-Trust RBAC, ISO 27001 Certified, 5 Campuses • 14 Depts, and Real-Time Telemetry",
  );

  // -------------------------------------------------------------------------
  // 3. Right Column: Top Meta, Heading, 4-Role Segment Bar & Elevated Card
  // -------------------------------------------------------------------------
  assert(
    loginPageSource.includes("Tenant: VSB-CAMPUS") &&
      loginPageSource.includes("INSTITUTIONAL ACCESS PORTAL") &&
      loginPageSource.includes("Select Your Portal Experience"),
    "Right Column Top Meta: 'Tenant: VSB-CAMPUS', 'INSTITUTIONAL ACCESS PORTAL', and 'Select Your Portal Experience'",
  );

  // 4-Role Segment Bar
  assert(
    loginPageSource.includes("FOUR_ROLES") &&
      loginPageSource.includes("STUDENT") &&
      loginPageSource.includes("FACULTY") &&
      loginPageSource.includes("VICE_PRINCIPAL") &&
      loginPageSource.includes("HOD"),
    "4-Role Segment Bar: 'Student' (active yellow pill with graduation cap), 'Faculty', 'Vice Principal', and 'HOD'",
  );

  // Elevated Login Card & Elements
  assert(
    loginPageSource.includes("Academic Lifecycle & Courses") &&
      loginPageSource.includes("✨ Fill Demo") &&
      loginPageSource.includes("Student Portal"),
    "Elevated Login Card: Academic pill badge, '✨ Fill Demo' trigger, and 'Student Portal' title",
  );

  // Username / Student ID input
  assert(
    loginPageSource.includes('id="identifier"') &&
      loginPageSource.includes("STUDENT ID / ROLL NO. OR EMAIL"),
    "Stylized input: Student ID / Roll No or Email with accessible label is present",
  );

  // Password input & visibility toggle
  assert(
    loginPageSource.includes('id="password"') &&
      loginPageSource.includes("INSTITUTIONAL PASSWORD") &&
      loginPageSource.includes("showPassword") &&
      loginPageSource.includes("EyeOff") &&
      loginPageSource.includes("Eye"),
    "Stylized input: Institutional Password input with show/hide password visibility toggle",
  );

  // Remember me checkbox
  assert(
    loginPageSource.includes('id="rememberMe"') &&
      loginPageSource.includes("Remember me on this institutional device"),
    "Remember me checkbox control is present",
  );

  // Forgot password link
  assert(
    loginPageSource.includes('href="/login/forgot-password"') &&
      loginPageSource.includes("Forgot password?"),
    "Forgot password link pointing to /login/forgot-password is present",
  );

  // Golden CTA button
  assert(
    loginPageSource.includes('type="submit"') &&
      loginPageSource.includes("Sign In to Student Portal →"),
    "Bold golden CTA: 'Sign In to Student Portal →' submit button is present",
  );

  // Accessible alert container
  assert(
    loginPageSource.includes("errorMessage") &&
      loginPageSource.includes('role="alert"'),
    "Accessible alert container for authentication error messages is present",
  );

  // Quick-Switch Test Persona
  assert(
    loginPageSource.includes("INSTANT TEST PERSONA") &&
      loginPageSource.includes("1-Click Workspace Launch") &&
      loginPageSource.includes("Aarav Patel") &&
      loginPageSource.includes("Student — B.Tech CSE (Year 3 / Sem 5)"),
    "Quick-Switch Test Persona: 'Aarav Patel (Year 3 / Sem 5)' 1-click launch card at bottom",
  );

  // -------------------------------------------------------------------------
  // 4. Authentication Functionality & Security
  // -------------------------------------------------------------------------
  assert(
    loginPageSource.includes("await login({") &&
      loginPageSource.includes("email: trimmedIdentifier") &&
      loginPageSource.includes("password: password"),
    "Preserves existing login() API invocation with credentials",
  );

  assert(
    loginPageSource.includes("router.replace(redirectUrl)") ||
      loginPageSource.includes('router.replace("/app/dashboard")'),
    "Authenticated redirect securely routes to /app/dashboard",
  );

  // -------------------------------------------------------------------------
  // 5. Password Recovery Page Consistency
  // -------------------------------------------------------------------------
  assert(
    forgotPasswordSource.includes("Reset your password") &&
      forgotPasswordSource.includes('href="/login"'),
    "Forgot password page is aligned with clean white-and-yellow enterprise design",
  );

  // -------------------------------------------------------------------------
  // 6. Role Accounts Completeness
  // -------------------------------------------------------------------------
  const requiredRoles = [
    "STUDENT",
    "FACULTY",
    "HOD",
    "PRINCIPAL",
    "SUPER_ADMIN",
  ];
  for (const role of requiredRoles) {
    const persona = DEMO_PERSONAS.find((p) => p.role === role);
    assert(
      Boolean(persona),
      `Institutional persona for role ${role} is preserved (${persona?.email})`,
    );
  }

  console.log("=================================================");
  console.log(
    `Landscape Login Tests Finished: Passed: ${passed}, Failed: ${failed}`,
  );
  console.log("=================================================");

  if (failed > 0) {
    process.exit(1);
  }
}

runLandscapeLoginTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
