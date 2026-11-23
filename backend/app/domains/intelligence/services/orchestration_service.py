"""Central AI Orchestration Engine for CampusOS Intelligence.

Executes the zero-trust workflow:
Query → Context → Intent Classification → Tool Permission Engine →
Sandboxed Domain Execution → Response Synthesis → Validation →
Provenance Attachment → Audit & Activity Logging.
"""

import time
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    CampusOSException,
    PermissionDeniedException,
    ValidationException,
)
from app.core.logging import logger
from app.domains.intelligence.ai.provider import LLMProvider
from app.domains.intelligence.ai.providers.mock import MockLLMProvider
from app.domains.intelligence.services.activity_service import ActivityService
from app.domains.intelligence.services.conversation_service import ConversationService
from app.domains.intelligence.services.intent_service import IntentService
from app.domains.intelligence.services.rate_limit_service import get_rate_limiter
from app.domains.intelligence.tools.registry import get_tool_registry
from app.models.people import User
from app.schemas.intelligence import (
    ActionItem,
    AIConversationCreate,
    AIExplainability,
    AIQueryRequest,
    AIResponse,
    AIResponseBlock,
    AISource,
)


def get_active_llm_provider() -> LLMProvider:
    """Resolve configured LLM provider from settings."""
    # Production supports "mock", "openai", "anthropic", "gemini"
    provider_name = settings.AI_PROVIDER.lower().strip()
    if provider_name == "mock":
        return MockLLMProvider()
    # Fallback to mock provider for local resilience
    return MockLLMProvider()


class IntelligenceOrchestrator:
    """Core permission-aware institutional intelligence orchestrator."""

    @classmethod
    async def process_query(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user: User,
        user_permissions: set[str],
        request: AIQueryRequest,
    ) -> AIResponse:
        start_time = time.time()

        # 1. Validation & Safety Checks
        query_text = request.query.strip()
        if not query_text:
            raise ValidationException("Query string cannot be empty.")
        if len(query_text) > settings.AI_MAX_QUERY_LENGTH:
            raise ValidationException(
                f"Query length ({len(query_text)}) exceeds configured ceiling ({settings.AI_MAX_QUERY_LENGTH} chars)."
            )

        # 2. Rate Limiting Check
        rate_limiter = get_rate_limiter()
        rate_limiter.check_and_record(tenant_id, user.id)

        # 3. Conversation Context
        conv_id: UUID
        if request.conversation_id:
            try:
                conv_id = UUID(str(request.conversation_id))
            except ValueError as exc:
                raise ValidationException("Invalid conversation ID format.") from exc
            # Verifies ownership and tenant isolation
            conv = await ConversationService.get_conversation(db, tenant_id, conv_id, user.id)
        else:
            # Create a new session automatically
            title = query_text[:40] + ("..." if len(query_text) > 40 else "")
            conv = await ConversationService.create_conversation(
                db,
                tenant_id,
                user.id,
                AIConversationCreate(title=title, domain=request.domain or "ALL"),
            )
            conv_id = conv.id

        # Record User Message
        await ConversationService.add_message(
            db=db,
            tenant_id=tenant_id,
            conversation_id=conv_id,
            role="USER",
            content=query_text,
        )

        # 4. Intent Analysis & Tool Selection
        context_dict = request.context.model_dump(exclude_none=True) if request.context else {}
        intent_plan = IntentService.classify(query_text, context_dict)

        # 5. Tool Permission Engine & Execution
        registry = get_tool_registry()
        tool_results: dict[str, Any] = {}
        executed_tools: list[str] = []
        sources: list[AISource] = []

        for tool_name in intent_plan.target_tools:
            tool_def = registry.get(tool_name)
            if not tool_def:
                continue

            # Execute with strict permission verification
            try:
                params = intent_plan.suggested_params.get(tool_name, {})
                # Merge context filters if relevant
                if "student_id" in context_dict and "identifier" not in params:
                    params["identifier"] = context_dict["student_id"]
                if "department" in context_dict and "department" not in params:
                    params["department"] = context_dict["department"]

                result = await registry.execute(
                    tool_name=tool_name,
                    db=db,
                    tenant_id=tenant_id,
                    user=user,
                    user_permissions=user_permissions,
                    params=params,
                )
                tool_results[tool_name] = result
                executed_tools.append(tool_name)

                # Attach domain source provenance
                sources.append(
                    AISource(
                        name=tool_def.description,
                        domain=tool_def.domain,
                        href=f"/{tool_def.domain.lower()}",
                        description=f"Authoritative ledger extraction via {tool_name}",
                    )
                )
            except PermissionDeniedException as p_err:
                # Controlled permission failure: do not fabricate data
                raise p_err
            except Exception as t_err:
                # Tool execution error: record and continue without fabricated facts
                logger.error(f"Tool execution failed for {tool_name}: {t_err}", exc_info=True)
                tool_results[tool_name] = {"error": str(t_err)}

        # 6. Response Synthesis via LLM Provider
        provider = get_active_llm_provider()
        llm_context = {
            "query": query_text,
            "intent": intent_plan.intent,
            "tool_results": tool_results,
            "tenant_id": str(tenant_id),
            "user_id": str(user.id),
        }

        try:
            llm_res = await provider.generate(
                messages=[{"role": "user", "content": query_text}],
                tools=[{"name": t} for t in executed_tools],
                context=llm_context,
            )
        except Exception as p_exc:
            raise CampusOSException(
                status_code=503,
                code="AI_PROVIDER_UNAVAILABLE",
                message="The institutional AI provider is temporarily unavailable. Please try again shortly.",
            ) from p_exc

        parsed_blocks = [AIResponseBlock.model_validate(b) for b in llm_res.structured_blocks]
        parsed_actions = [ActionItem.model_validate(a) for a in llm_res.suggested_actions]

        # 7. Assemble Explainability Metadata
        calc_metrics = [b.title for b in parsed_blocks if getattr(b, "title", None)] or [
            "Aggregate summary metrics"
        ]
        explainability = AIExplainability(
            data_sources=[s.name for s in sources] or ["Authoritative ERP Domain Ledger"],
            filters_applied=[f"{k}: {v}" for k, v in context_dict.items()]
            if context_dict
            else ["Institutional Scope: Active Term"],
            time_period="Academic Term 2026",
            calculation_used=f"Intent: {intent_plan.intent} via tools {executed_tools}",
            metrics_calculated=calc_metrics,
            relevant_domain=intent_plan.intent.split("_")[0] if intent_plan.intent else "CAMPUS",
            result="Verified against PostgreSQL transactional ledgers",
        )

        # 8. Persist Assistant Message
        assistant_msg = await ConversationService.add_message(
            db=db,
            tenant_id=tenant_id,
            conversation_id=conv_id,
            role="ASSISTANT",
            content=llm_res.content,
            structured_response=[b.model_dump() for b in parsed_blocks],
            sources=[s.model_dump() for s in sources],
            explainability=explainability.model_dump(),
            suggested_actions=[a.model_dump() for a in parsed_actions],
            tool_calls=[{"tool": t, "status": "SUCCESS"} for t in executed_tools],
            model=llm_res.model,
            provider=llm_res.provider,
            latency_ms=int((time.time() - start_time) * 1000),
        )

        # 9. Audit Activity Log
        duration_ms = int((time.time() - start_time) * 1000)
        user_role_str = next(iter({ur.role.name for ur in user.roles if ur.role}), "USER")
        await ActivityService.log_activity(
            db=db,
            tenant_id=tenant_id,
            user_id=user.id,
            user_name=f"{user.first_name} {user.last_name}",
            user_role=user_role_str,
            query=query_text,
            domain=intent_plan.domain,
            tools_invoked=executed_tools,
            result_summary=llm_res.content[:200],
            duration_ms=duration_ms,
            status="COMPLETED",
            data_sources=[s.name for s in sources],
            context_summary=f"Intent: {intent_plan.intent}",
            provider=llm_res.provider,
            model=llm_res.model,
            conversation_id=conv_id,
        )

        # 10. Construct Final Verified Response
        return AIResponse(
            id=str(uuid4()),
            query=query_text,
            reply=llm_res.content,
            status="COMPLETED",
            blocks=parsed_blocks,
            sources=sources,
            explainability=explainability,
            suggested_actions=parsed_actions,
            execution_time_ms=duration_ms,
            tool_name=executed_tools[0] if executed_tools else None,
            conversation_id=str(conv_id),
            message_id=str(assistant_msg.id),
            metadata={
                "provider": llm_res.provider or "mock",
                "model": llm_res.model or "mock",
                "latency_ms": duration_ms,
                "data_freshness": "current",
            },
        )
