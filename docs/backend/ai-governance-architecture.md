# Enterprise AI Governance, Provider Management & Safety Firewall

## 1. Architectural Overview

CampusOS implements an ambient, enterprise-grade AI governance and predictive intelligence engine strictly adhering to the architectural maxim:

> **"One Campus. One System. One Source of Truth."**

AI within CampusOS does not act as an unconstrained agent with direct database or execution privileges. Rather, it operates behind strict server-side **Policy Boundaries**, **Attribute/Permission-Based Access Controls (PBAC)**, and **Multi-Tenant Boundary Isolation**.

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                        CAMPUSOS CLIENT (Web / Mobile)                     │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ Authenticated HTTP / TLS
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                   FASTAPI ROUTER (/api/v1/intelligence)                  │
│       PBAC Verification: require_permission(INTELLIGENCE_...)             │
│       Tenant Context Resolution: Current Tenant Isolation Guard          │
└──────────────────┬─────────────────────────────────────┬──────────────────┘
                   │                                     │
                   ▼                                     ▼
┌──────────────────────────────────────┐  ┌─────────────────────────────────┐
│          PROMPTGUARD FIREWALL        │  │      AI GOVERNANCE SERVICE      │
│  - Zero-Trust Adversarial Detection  │  │  - Permitted/Prohibited Check   │
│  - System Prompt Leakage Defense     │  │  - Budget & Token Telemetry     │
│  - PII Masking (Phone, Aadhaar, SSN) │  │  - Human Review Requirement     │
└──────────────────┬───────────────────┘  └────────────────┬────────────────┘
                   │                                       │
                   ▼                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    GOVERNED SERVICE & INFERENCE LAYER                     │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌─────────────────┐  │
│  │  NL Analytics Service │ │ Student Support Pred. │ │ Recommendation  │  │
│  │ (Step 28 Metric Reg.) │ │ (Risk Indicator Eng.) │ │ & Anomaly Engine│  │
│  └───────────────────────┘ └───────────────────────┘ └─────────────────┘  │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     AI PROVIDER MANAGER ABSTRACTION                       │
│  - Active Provider Dispatch (Mock / OpenAI / Anthropic / Gemini)          │
│  - Exponential Backoff & Circuit Breaker                                  │
│  - Graceful Degradation (Non-AI ERP operations unaffected)                │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Provider-Agnostic AI Integration

The `AIProviderManager` (`app/domains/intelligence/ai/provider_manager.py`) decouples CampusOS from specific foundation model vendors:

1. **Supported Providers**:
   - `mock`: Deterministic rule-based simulated LLM for unit tests and offline/air-gapped environments.
   - `openai`: OpenAI GPT-4o / GPT-4o-mini (configured via `OPENAI_API_KEY`, `OPENAI_MODEL`).
   - `anthropic`: Anthropic Claude 3.5 Sonnet (configured via `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`).
   - `gemini`: Google Gemini 1.5 Pro / Flash (configured via `GEMINI_API_KEY`, `GEMINI_MODEL`).

2. **Configuration & Security**:
   - Zero hardcoded credentials; loaded strictly through environment variables.
   - When credentials for a requested commercial provider are missing, the status is explicitly reported as `UNAVAILABLE` or `DISABLED` without crashing existing ERP functions.
   - Never leaks provider secrets or stack traces in API responses.

---

## 3. Zero-Trust Safety Firewall (`PromptGuard`)

Every input inquiry and retrieved document passes through `PromptGuard` (`app/domains/intelligence/governance/safety.py`):

1. **Adversarial Pattern Interception**:
   - Detects jailbreak attempts ("ignore previous instructions", "DAN mode", "developer mode").
   - Blocks prompt extraction attacks ("reveal your system prompt", "print initial instructions", "reveal secrets").
   - Intercepts malicious SQL injection (`DROP TABLE`, `UNION SELECT`, `ALTER TABLE`, `exec`).
   - Blocks Cross-Site Scripting (`<script>` payloads).
2. **Automated PII Masking**:
   - National Identification numbers (e.g., Aadhaar 12-digit grouped sequences: `\b\d{4}\s\d{4}\s\d{4}\b`) masked as `[NATIONAL_ID_REDACTED]`.
   - Contact numbers (International and local 10-digit formats) masked as `[PHONE_REDACTED]`.
   - Applied *before* context injection into prompts or analytics logs.

---

## 4. Policy Management & Prohibited Use Cases

The `AIGovernanceService` (`app/domains/intelligence/governance/policy_service.py`) guarantees that AI is used only for assistive analysis, strictly banning consequential autonomous decisions:

### Non-Negotiable Prohibited Use Cases
- `AUTOMATED_GRADING`: AI may not assign conclusive student grades or marks.
- `AUTOMATED_DISCIPLINE`: AI may not issue disciplinary actions, suspensions, or expulsions.
- `RAW_SQL_EXECUTION`: AI may never execute arbitrary SQL or uncompiled database statements.
- `AUTOMATED_ADMISSION_REJECTION`: AI may not reject applicant admission files autonomously.
- `AUTOMATED_SCHOLARSHIP_TERMINATION`: AI may not revoke student financial concessions without human senate review.

### Human-in-the-Loop Safeguards
All predictions and recommendations maintain `human_review_required = True`. Consequential actions require an authorized administrator or advisor to review evidence, input decision rationale, and trigger actions through standard domain APIs.
