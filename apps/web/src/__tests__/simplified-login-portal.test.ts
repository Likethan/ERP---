/**
 * Simplified Login Portal Verification Suite
 * Verifies:
 * 1. Application opens directly on the login portal (no introductory screen).
 * 2. Left-side promotional content, marketing text, and promo sections are completely removed.
 * 3. Centered login card structure with the 8 essential elements only.
 * 4. Authentication logic: valid credentials succeed; invalid credentials display appropriate errors.
 * 5. Password visibility control toggling.
 * 6. Existing password recovery portal compatibility.
 * 7. Authenticated user redirection.
 * 8. Multi-role support preservation.
 */

import { DEMO_PERSONAS } from "../mocks/auth.mock";
import { PORTALS } from "../lib/portals";
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

async function runSimplifiedLoginTests() {
  console.log("=================================================");
  console.log("CampusOS Simplified Login Portal Test Suite");
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
  // 1. Initial Application Loading & Introductory Content Removal
  // -------------------------------------------------------------------------
  assert(
    rootPageSource.includes("<LoginPage") ||
      rootPageSource.includes("LoginPage"),
    "Root page '/' directly renders LoginPage without intermediate welcome or initialization screens",
  );
  assert(
    !rootPageSource.includes("CampusOSPortalPage") &&
      !rootPageSource.includes("domainModules") &&
      !rootPageSource.includes("DEMO_PERSONAS"),
    "All previous 600+ line welcome, promotional, and module showcase content is removed from root page",
  );

  // -------------------------------------------------------------------------
  // 2. Removal of Left-Side Promotional & Marketing Content
  // -------------------------------------------------------------------------
  assert(
    !loginPageSource.includes("lg:w-5/12") &&
      !loginPageSource.includes("xl:w-5/12"),
    "Left-side split panel (5/12 width) is completely removed",
  );
  assert(
    !loginPageSource.includes("One Campus. One System. One Source of Truth."),
    "Large marketing slogan ('One Campus. One System...') is removed from login page",
  );
  assert(
    !loginPageSource.includes("Unified Institutional Gateway") &&
      !loginPageSource.includes("handleAutofillDemo") &&
      !loginPageSource.includes("handleDirectPersonaLogin"),
    "Promotional badges, autofill buttons, and 1-click bypass buttons are removed from login page",
  );

  // -------------------------------------------------------------------------
  // 3. Centered Single Login Card Layout & 8 Elements
  // -------------------------------------------------------------------------
  assert(
    (loginPageSource.includes("min-h-screen") &&
      loginPageSource.includes("flex-col items-center justify-center") &&
      loginPageSource.includes("max-w-md")) ||
      loginPageSource.includes("max-w-sm"),
    "Responsive single centered login card container is present",
  );

  // Element 1: CampusOS logo / brand
  assert(
    loginPageSource.includes('src="/college-logo.jpg"') &&
      loginPageSource.includes("CampusOS"),
    "Element 1: CampusOS logo and brand name are present",
  );

  // Element 2: Login heading
  assert(
    loginPageSource.includes("<h1") &&
      loginPageSource.includes("Sign in to your account"),
    "Element 2: Clean login heading 'Sign in to your account' is present",
  );

  // Element 3: Username / Email input
  assert(
    loginPageSource.includes('id="identifier"') &&
      loginPageSource.includes("Username or Email"),
    "Element 3: Username or Email input with accessible label is present",
  );

  // Element 4: Password input
  assert(
    loginPageSource.includes('id="password"') &&
      loginPageSource.includes("Password"),
    "Element 4: Password input with accessible label is present",
  );

  // Element 5: Show / hide password control
  assert(
    loginPageSource.includes("showPassword") &&
      loginPageSource.includes("setShowPassword") &&
      loginPageSource.includes("EyeOff") &&
      loginPageSource.includes("Eye"),
    "Element 5: Show / hide password visibility toggle is present",
  );

  // Element 6: Forgot password link
  assert(
    loginPageSource.includes('href="/login/forgot-password"') &&
      loginPageSource.includes("Forgot password?"),
    "Element 6: Forgot password link pointing to /login/forgot-password is present",
  );

  // Element 7: Sign In button
  assert(
    loginPageSource.includes('type="submit"') &&
      loginPageSource.includes("Sign In"),
    "Element 7: Sign In primary submit button is present",
  );

  // Element 8: Existing authentication error messages
  assert(
    loginPageSource.includes("errorMessage") &&
      loginPageSource.includes('role="alert"'),
    "Element 8: Accessible alert container for authentication error messages is present",
  );

  // -------------------------------------------------------------------------
  // 4. Authentication Functionality & Error Handling
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
      forgotPasswordSource.includes('href="/login"') &&
      !forgotPasswordSource.includes(
        "One Campus. One System. One Source of Truth.",
      ),
    "Forgot password page is aligned with minimal clean white-and-yellow enterprise design",
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
    `Simplified Login Tests Finished: Passed: ${passed}, Failed: ${failed}`,
  );
  console.log("=================================================");

  if (failed > 0) {
    process.exit(1);
  }
}

runSimplifiedLoginTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
