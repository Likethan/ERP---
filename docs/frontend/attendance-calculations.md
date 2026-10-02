# CampusOS — Attendance Calculations Engine & Policy Formulas

## 1. Overview

All attendance calculations within CampusOS are centralized in a single standardized frontend computation service:

```text
apps/web/src/services/attendance-calculator.ts
```

This guarantees consistent calculations across the Operations Hub, Student 360°, Course Summaries, Reports, and Warning Banners, preventing discrepancies across UI views. In future releases, this mathematical contract will be identically enforced by the backend FastAPI service.

---

## 2. Core Mathematical Formulations

### 2.1 Attendance Percentage Formula

$$\text{Effective Attended Sessions} = P + (L \times w) + E$$

Where:
- $P$ = Total count of `PRESENT` marks
- $L$ = Total count of `LATE` marks
- $w$ = Late weighting coefficient (default = $0.5$ or $50\%$)
- $E$ = Total count of `EXCUSED` marks (included when policy condonation applies)
- $N$ = Total sessions conducted ($N = P + A + L + E$)

$$\text{Attendance Percentage} = \begin{cases} 0.0 & \text{if } N = 0 \\ \min\left(100.0, \, \text{round}\left(\frac{\text{Effective Attended}}{N} \times 100, \, 1\right)\right) & \text{if } N > 0 \end{cases}$$

### 2.2 Late Arrival Penalty Handling
Institutions can configure late weight handling via policy:
- **Strict Mode** ($w = 0.0$): Late students receive zero session credit.
- **Pro-rated Mode** ($w = 0.5$): Late students receive half credit ($0.5$).
- **Forgiving Mode** ($w = 1.0$): Late students receive full session credit.

### 2.3 Excused Leave Exemption
When `includeLeavesInCalculations: true`:
- Approved medical and official duty sessions count toward effective attendance.
When `includeLeavesInCalculations: false`:
- Excused sessions are subtracted from the denominator $N$, ensuring the student is evaluated strictly against class periods they were eligible to attend.

---

## 3. Attendance Risk Categorization

Students are grouped into three operational health bands:

| Status Band | Criteria | UI Indicator | Academic Action |
| :--- | :--- | :--- | :--- |
| **HEALTHY** | $\text{Attendance} \ge \text{Warning Threshold}$ (e.g. $\ge 80\%$) | Green Badge | Eligible for examinations; good standing. |
| **WARNING** | $\text{Critical Threshold} \le \text{Attendance} < \text{Warning Threshold}$ ($65\% - 79.9\%$) | Amber Badge | Warning notice triggered to student & proctor; remediation recommended. |
| **CRITICAL** | $\text{Attendance} < \text{Critical Threshold}$ ($< 65\%$) | Red Badge | Barred from semester examinations without formal Academic Council condonation. |

---

## 4. Recovery Projection Formula (Sessions Needed)

When a student falls below the minimum required threshold $T$ (e.g. $75\%$), the calculator estimates the minimum number of consecutive upcoming sessions $S$ they must attend to restore their standing:

$$\frac{P_{\text{eff}} + S}{N + S} \ge T$$

Solving for $S$:

$$P_{\text{eff}} + S \ge T \times (N + S)$$
$$S \times (1 - T) \ge (T \times N) - P_{\text{eff}}$$
$$S = \left\lceil \frac{T \times N - P_{\text{eff}}}{1 - T} \right\rceil$$

### Example Calculation:
- Current total sessions conducted: $N = 42$
- Current attended sessions: $P_{\text{eff}} = 25$
- Current percentage: $59.5\%$ (Critical)
- Target minimum threshold: $T = 0.75$ (75%)

$$S = \left\lceil \frac{0.75 \times 42 - 25}{1 - 0.75} \right\rceil = \left\lceil \frac{31.5 - 25}{0.25} \right\rceil = \left\lceil \frac{6.5}{0.25} \right\rceil = 26$$

The student must attend **26 consecutive sessions** without absence to reach the 75% examination threshold.
