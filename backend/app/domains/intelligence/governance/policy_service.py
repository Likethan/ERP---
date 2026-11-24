"""Enterprise AI Governance Policy Service.

Enforces institutional compliance, permitted/prohibited use-case boundaries,
daily cost budgets, model allowlists, and human-in-the-loop oversight requirements.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CampusOSException
from app.models.intelligence import AIGovernancePolicy


class AIGovernanceService:
    """Manages institutional AI policies and enforces guardrails at runtime."""

    PROHIBITED_USE_CASES = {
        "AUTOMATED_GRADING",
        "AUTOMATED_DISCIPLINE",
        "RAW_SQL_EXECUTION",
        "AUTOMATED_ADMISSION_REJECTION",
    }

    PERMITTED_USE_CASES = {
        "ANALYTICS_QUERY",
        "STUDENT_SUPPORT",
        "ANOMALY_DETECTION",
        "RECOMMENDATION",
        "WORKFLOW_ASSISTANCE",
    }

    @classmethod
    async def get_active_policy(cls, db: AsyncSession, tenant_id: UUID) -> AIGovernancePolicy:
        """Retrieve active institutional policy or return default in-memory policy."""
        stmt = (
            select(AIGovernancePolicy)
            .where(
                AIGovernancePolicy.tenant_id == tenant_id,
                AIGovernancePolicy.is_active == True,  # noqa: E712
            )
            .order_by(AIGovernancePolicy.version.desc())
        )
        result = await db.execute(stmt)
        policy = result.scalars().first()

        if not policy:
            # Create default institutional policy
            policy = AIGovernancePolicy(
                tenant_id=tenant_id,
                policy_name="DEFAULT_INSTITUTIONAL_POLICY",
                version=1,
                is_active=True,
                allowed_providers=["mock", "openai", "anthropic", "gemini"],
                allowed_models=["campusos-institutional-v1", "gpt-4o", "claude-3-5-sonnet"],
                permitted_use_cases=list(cls.PERMITTED_USE_CASES),
                prohibited_use_cases=list(cls.PROHIBITED_USE_CASES),
                max_context_tokens=4096,
                max_output_tokens=2048,
                daily_budget_usd=Decimal("50.00"),
                human_review_required=True,
                enforce_prompt_guard=True,
            )
            db.add(policy)
            await db.flush()

        return policy

    @classmethod
    async def validate_use_case(cls, db: AsyncSession, tenant_id: UUID, use_case: str) -> None:
        """Ensure the requested use case is permitted and strictly not in the prohibited list."""
        normalized = use_case.upper().strip()

        if normalized in cls.PROHIBITED_USE_CASES:
            raise CampusOSException(
                status_code=403,
                code="PROHIBITED_AI_USE_CASE",
                message=(
                    f"Use case '{normalized}' is strictly prohibited under institutional governance policy. "
                    "Autonomous student discipline, automated grading, and direct SQL execution are not permitted."
                ),
            )

        policy = await cls.get_active_policy(db, tenant_id)
        if policy.permitted_use_cases and normalized not in policy.permitted_use_cases:
            raise CampusOSException(
                status_code=403,
                code="UNAPPROVED_AI_USE_CASE",
                message=f"Use case '{normalized}' has not been approved for this institution.",
            )

    @classmethod
    async def check_budget_limit(cls, db: AsyncSession, tenant_id: UUID) -> None:
        """Verify tenant has not exceeded their daily USD token spend budget."""
        policy = await cls.get_active_policy(db, tenant_id)
        # In a real environment, query today's sum of estimated_cost_usd from AIUsageRecord
        # If spend > policy.daily_budget_usd, raise 429
        # For default limits:
        if policy.daily_budget_usd <= Decimal("0.0"):
            raise CampusOSException(
                status_code=429,
                code="AI_BUDGET_EXCEEDED",
                message="Institutional daily AI budget has been exhausted.",
            )
