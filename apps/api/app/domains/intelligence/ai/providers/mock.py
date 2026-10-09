"""Deterministic Mock LLM Provider for CampusOS Intelligence.

Used in development and automated testing to produce structured institutional
AI responses based on facts retrieved from authoritative ERP tools.
"""

from typing import Any

from app.domains.intelligence.ai.provider import LLMResponse


class MockLLMProvider:
    """Deterministic, permission-grounded mock provider."""

    async def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> LLMResponse:
        """Formulate multi-block structured response grounded exclusively in supplied tool facts."""
        latest_query = messages[-1].get("content", "") if messages else ""
        tool_results = context.get("tool_results", {})
        query_lower = latest_query.lower()

        blocks: list[dict[str, Any]] = []
        actions: list[dict[str, Any]] = []
        explanation_text = ""

        # Case 1: Attendance below threshold query
        if "attendance" in query_lower and (
            "below" in query_lower or "shortage" in query_lower or "75" in query_lower
        ):
            att_data = tool_results.get("attendance.get_students_below_threshold", {})
            students = att_data.get("students", [])
            count = att_data.get("count_below_threshold", len(students))
            threshold = att_data.get("threshold", 75.0)

            explanation_text = (
                f"Authoritative attendance records identify {count} students currently below the "
                f"mandatory institutional threshold of {threshold}%. Immediate student advising and "
                "attendance shortage notifications are recommended."
            )

            blocks.append(
                {
                    "type": "METRIC",
                    "title": "Students Below Attendance Threshold",
                    "metrics": [
                        {
                            "label": f"Attendance < {threshold}%",
                            "value": count,
                            "change": "+2 vs prior month",
                            "trend": "down",
                            "unit": "Students",
                        },
                        {
                            "label": "Institutional Minimum",
                            "value": f"{threshold}%",
                            "trend": "neutral",
                        },
                    ],
                }
            )

            if students:
                table_rows = []
                for s in students:
                    table_rows.append(
                        [
                            s.get("student_name", "Student"),
                            s.get("roll_number", "REG-01"),
                            f"{s.get('attendance_percentage', 0.0)}%",
                            f"{s.get('attended_sessions', 0)} / {s.get('total_sessions', 0)}",
                            s.get("program", "Computer Science"),
                        ]
                    )
                blocks.append(
                    {
                        "type": "TABLE",
                        "title": "At-Risk Attendance Roster",
                        "table": {
                            "headers": [
                                "Student Name",
                                "Roll Number",
                                "Attendance %",
                                "Sessions Attended",
                                "Program",
                            ],
                            "rows": table_rows,
                        },
                    }
                )

            blocks.append(
                {
                    "type": "WARNING",
                    "title": "Examination Ineligibility Advisory",
                    "content": f"Under Regulation 7.2, students with attendance below {threshold}% cannot sit for end-semester assessments without formal medical/extenuating condonation.",
                }
            )

            actions.append({"label": "View Attendance Dashboard", "href": "/attendance"})
            actions.append(
                {
                    "label": "Dispatch Shortage Notices",
                    "href": "/attendance/alerts",
                    "variant": "secondary",
                }
            )

        # Case 2: Fee & Finance Queries
        elif "fee" in query_lower or "finance" in query_lower or "outstanding" in query_lower:
            fin_data = tool_results.get("finance.get_fee_summary") or tool_results.get(
                "finance.get_outstanding_summary", {}
            )
            total_out = fin_data.get("total_outstanding_inr") or fin_data.get(
                "outstanding_amount_inr", 2650000.0
            )
            rate = fin_data.get("collection_rate_percentage", 89.2)

            explanation_text = (
                f"Financial ledger analysis reports total outstanding student fee balance of "
                f"₹{total_out:,.2f} with an overall institutional collection rate of {rate}%."
            )

            blocks.append(
                {
                    "type": "METRIC",
                    "title": "Institutional Fee Standing",
                    "metrics": [
                        {
                            "label": "Total Outstanding Dues",
                            "value": f"₹{total_out:,.0f}",
                            "change": "-4.2% MoM",
                            "trend": "up",
                        },
                        {
                            "label": "Collection Efficiency",
                            "value": f"{rate}%",
                            "trend": "up",
                        },
                    ],
                }
            )

            blocks.append(
                {
                    "type": "INSIGHT",
                    "title": "Fee Collection Trajectory",
                    "content": "89.2% of academic tuition dues have been settled for the active academic year. Remaining balance is concentrated across final-year engineering tracks.",
                }
            )

            actions.append({"label": "Open Finance Console", "href": "/finance"})
            actions.append(
                {
                    "label": "Inspect Overdue Invoices",
                    "href": "/finance/invoices",
                    "variant": "secondary",
                }
            )

        # Case 3: Cross-domain Comparison (Attendance + Examination)
        elif "compare" in query_lower or (
            "attendance" in query_lower and ("exam" in query_lower or "performance" in query_lower)
        ):
            explanation_text = (
                "Cross-domain correlation between student attendance ledgers and examination outcome "
                "registers reveals a direct positive correlation between lecture attendance and pass rates in the CSE department."
            )

            blocks.append(
                {
                    "type": "TABLE",
                    "title": "Attendance vs Academic Outcome Correlation",
                    "table": {
                        "headers": [
                            "Department",
                            "Average Attendance",
                            "Pass Rate",
                            "Distinction Rate",
                            "Academic Standing",
                        ],
                        "rows": [
                            ["Computer Science & Engineering", "86.4%", "92.1%", "28.4%", "TIER_1"],
                            ["Information Technology", "84.2%", "89.5%", "24.0%", "TIER_1"],
                            ["Electronics & Communication", "81.8%", "85.2%", "18.5%", "TIER_2"],
                        ],
                    },
                }
            )

            blocks.append(
                {
                    "type": "CHART",
                    "title": "Academic Standing Distribution",
                    "chart": {
                        "type": "bar",
                        "labels": ["CSE", "IT", "ECE", "MECH"],
                        "datasets": [
                            {"name": "Pass Rate %", "data": [92.1, 89.5, 85.2, 79.4]},
                            {"name": "Attendance %", "data": [86.4, 84.2, 81.8, 77.2]},
                        ],
                    },
                }
            )

            blocks.append(
                {
                    "type": "RECOMMENDATION",
                    "title": "Targeted Academic Mentoring",
                    "content": "Students maintaining above 85% attendance achieved a 96% pass rate. Allocate peer tutors for course sections below 80% attendance.",
                }
            )

            actions.append({"label": "View Academics Report", "href": "/academics"})

        # Default Case: General Domain Answer
        else:
            explanation_text = (
                "Verified institutional data retrieved from CampusOS ERP registry. "
                "All figures reflect authoritative records from current operational ledgers."
            )
            blocks.append(
                {
                    "type": "TEXT",
                    "title": "Institutional Summary",
                    "content": explanation_text,
                }
            )

        return LLMResponse(
            content=explanation_text,
            structured_blocks=blocks,
            suggested_actions=actions,
            model="campusos-mock-v1",
            provider="mock",
            token_usage={"prompt_tokens": 145, "completion_tokens": 92, "total_tokens": 237},
            latency_ms=38,
        )
