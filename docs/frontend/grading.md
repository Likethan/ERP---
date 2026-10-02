# CampusOS Grading & Evaluation Calculation Engine

This document details the deterministic formulas and configuration rules governing multi-component scoring, percentage normalization, and UGC Choice Based Credit System (CBCS) 10-point letter grade assignment.

Implementation: `apps/web/src/services/grading-calculator.ts`

---

## 1. Multi-Component Assessment Weighting

Each assessment can be divided into weighted sub-components:

$$\text{Component Weighted Score} = \left( \frac{\text{Marks Obtained}}{\text{Component Max Marks}} \right) \times \text{Component Weightage}$$

### Example: CS301 Internal Assessment Scheme
| Component | Max Marks | Passing Marks | Weightage (%) | Student Raw Score | Weighted Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Assignment 1 (Graph Algorithms) | 20 | 8 | 10% | 18 | 9.0 |
| Quiz 1 (AVL Trees) | 20 | 8 | 10% | 16 | 8.0 |
| Midterm Test (Theory) | 60 | 24 | 20% | 52 | 17.33 |
| **Total Scheme** | **100** | **40** | **40%** | **86** | **34.33** |

Weightage validation enforces that the sum of sub-component weightages equals the assessment scheme total.

---

## 2. UGC CBCS 10-Point Letter Grading Scale

CampusOS implements the standard University Grants Commission (UGC) 10-point scale:

| Letter Grade | Grade Point (GP) | Percentage Range (%) | Classification | Qualifying Status |
| :---: | :---: | :---: | :--- | :---: |
| **O / A+** | 10.0 | 90.0 – 100.0 | Outstanding | PASS |
| **A** | 9.0 | 80.0 – 89.9 | Excellent | PASS |
| **B+** | 8.0 | 70.0 – 79.9 | Very Good | PASS |
| **B** | 7.0 | 60.0 – 69.9 | Good | PASS |
| **C** | 6.0 | 50.0 – 59.9 | Above Average | PASS |
| **D** | 5.0 | 40.0 – 49.9 | Pass | PASS |
| **E** | 4.0 | 35.0 – 39.9 | Marginal / Conditional Pass | PASS |
| **F** | 0.0 | 0.0 – 34.9 | Fail | FAIL |

---

## 3. Disciplinary & Non-Numeric Status Overrides

Regardless of computed percentages, non-numeric candidate states take precedence:

- `isAbsent == true` $\rightarrow$ Result status: **`ABSENT`**, Grade Point: `0.0`, Grade: `F`
- `isMalpractice == true` $\rightarrow$ Result status: **`WITHHELD`**, Grade Point: `0.0`, Grade: `F`
- `isWithheld == true` $\rightarrow$ Result status: **`WITHHELD`**, pending Disciplinary Hearing
- `isIncomplete == true` $\rightarrow$ Result status: **`INCOMPLETE`**, candidate has pending lab/viva components

---

## 4. Semester Grade Point Average (SGPA) Foundation

For a candidate enrolled in $N$ courses:

$$\text{SGPA} = \frac{\sum_{i=1}^{N} \left( \text{Course Credits}_i \times \text{Grade Point}_i \right)}{\sum_{i=1}^{N} \text{Course Credits}_i}$$

This formula is isolated in `grading-calculator.ts` and will seamlessly transition to backend calculation when FastAPI endpoints are activated.
