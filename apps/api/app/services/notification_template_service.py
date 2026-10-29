"""Enterprise Notification Message Template and Safe Rendering Service (Step 26).

Enforces:
- Strict variable schema validation against explicit template schemas.
- Safe token replacement without dynamic script evaluation (prevents eval / code injection).
- HTML escaping for HTML email rendering and plain-text fallback generation.
- Immutable active versions: publishing publishes a new version or creates a successor.
- Bounded template size limits (64KB) to prevent resource exhaustion.
- Bounded, predictable preview generation.
"""

import html
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.notification import (
    NotificationTemplate,
    NotificationTemplateVersion,
    TemplateStatus,
)
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationTemplateCreate,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)

MAX_TEMPLATE_SIZE_BYTES = 64 * 1024  # 64 Kilobytes
TOKEN_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


class NotificationTemplateService:
    """Safe, deterministic template authoring, versioning, and rendering service."""

    @classmethod
    def _extract_variable_tokens(cls, template_text: str) -> set[str]:
        """Extract all {{variable}} reference keys from template text."""
        return set(TOKEN_PATTERN.findall(template_text))

    @classmethod
    def _resolve_nested_value(cls, context: dict[str, Any], key_path: str) -> Any:
        """Resolve dotted variable paths like 'student.profile.roll_number' safely."""
        parts = key_path.split(".")
        current = context
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @classmethod
    def validate_template_size(cls, content: str, field_name: str = "template") -> None:
        """Ensure template size does not exceed bounded limit."""
        if len(content.encode("utf-8")) > MAX_TEMPLATE_SIZE_BYTES:
            raise ValidationException(
                f"The {field_name} content exceeds the maximum allowed size of 64KB."
            )

    @classmethod
    def validate_variables(
        cls, schema: dict[str, Any], context: dict[str, Any]
    ) -> list[str]:
        """Check for required variables defined in the schema that are missing from context."""
        missing = []
        for var_name, spec in schema.items():
            is_required = True
            if isinstance(spec, dict):
                is_required = spec.get("required", True)
            val = cls._resolve_nested_value(context, var_name)
            if is_required and val is None:
                missing.append(var_name)
        return missing

    @classmethod
    def render_text(cls, template_text: str, context: dict[str, Any]) -> str:
        """Safely render plain text with {{token}} substitution."""
        if not template_text:
            return ""
        cls.validate_template_size(template_text)

        def replace_token(match: re.Match) -> str:
            token = match.group(1).strip()
            val = cls._resolve_nested_value(context, token)
            return str(val) if val is not None else ""

        return TOKEN_PATTERN.sub(replace_token, template_text)

    @classmethod
    def render_html(cls, html_template: str, context: dict[str, Any]) -> str:
        """Safely render HTML template with automatic HTML escaping of interpolated values."""
        if not html_template:
            return ""
        cls.validate_template_size(html_template, field_name="HTML template")

        def replace_token_escaped(match: re.Match) -> str:
            token = match.group(1).strip()
            val = cls._resolve_nested_value(context, token)
            if val is None:
                return ""
            # Escape HTML characters: < > & " '
            return html.escape(str(val))

        return TOKEN_PATTERN.sub(replace_token_escaped, html_template)

    @classmethod
    def render(
        cls,
        subject_template: str | None,
        body_template: str,
        variables_schema: dict[str, Any],
        payload: dict[str, Any],
        is_html: bool = False,
    ) -> tuple[str | None, str]:
        """Validate variables and render subject and body templates."""
        missing = cls.validate_variables(variables_schema or {}, payload or {})
        if missing:
            raise ValidationException(
                f"Missing required variable(s) for template: {', '.join(missing)}"
            )

        rendered_subj = (
            cls.render_text(subject_template, payload) if subject_template else None
        )
        if is_html:
            rendered_body = cls.render_html(body_template, payload)
        else:
            rendered_body = cls.render_text(body_template, payload)

        return rendered_subj, rendered_body

    # -------------------------------------------------------------------------
    # CRUD & LIFECYCLE
    # -------------------------------------------------------------------------
    @classmethod
    async def create_template(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: NotificationTemplateCreate,
        actor_id: UUID | None = None,
    ) -> NotificationTemplate:
        repo = NotificationRepository(db)

        # Check existing key
        existing = await repo.get_template_by_key_and_channel(
            tenant_id, dto.template_key, dto.channel
        )
        if existing:
            raise ValidationException(
                f"Template with key '{dto.template_key}' already exists for channel '{dto.channel}'."
            )

        cls.validate_template_size(dto.body_template, "body_template")
        if dto.body_html_template:
            cls.validate_template_size(dto.body_html_template, "body_html_template")

        template = NotificationTemplate(
            id=uuid4(),
            tenant_id=tenant_id,
            template_key=dto.template_key.upper(),
            name=dto.name,
            description=dto.description,
            channel=dto.channel.upper(),
            category=dto.category.upper(),
            current_version=1,
            status=TemplateStatus.ACTIVE,
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        created_tmpl = await repo.create_template(template)

        # Initial active version
        version = NotificationTemplateVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            template_id=created_tmpl.id,
            version=1,
            status=TemplateStatus.ACTIVE,
            locale="en",
            subject=dto.subject,
            body_template=dto.body_template,
            body_html_template=dto.body_html_template,
            variable_schema_json=dto.variable_schema or {},
            sample_context_json=dto.sample_context,
            published_at=datetime.now(UTC),
            published_by_id=actor_id,
            change_summary="Initial template creation",
        )
        await repo.create_template_version(version)
        await db.commit()

        # Re-fetch with loaded versions
        return await repo.get_template_by_id(tenant_id, created_tmpl.id)  # type: ignore

    @classmethod
    async def get_template(
        cls, db: AsyncSession, tenant_id: UUID, template_id: UUID
    ) -> NotificationTemplate:
        repo = NotificationRepository(db)
        tmpl = await repo.get_template_by_id(tenant_id, template_id)
        if not tmpl:
            raise NotFoundException("NotificationTemplate", template_id)
        return tmpl

    @classmethod
    async def list_templates(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        channel: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[NotificationTemplate]:
        repo = NotificationRepository(db)
        return await repo.list_templates(
            tenant_id, channel=channel, category=category, status=status
        )

    @classmethod
    async def publish_version(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        template_id: UUID,
        subject: str | None = None,
        body_template: str | None = None,
        body_html_template: str | None = None,
        variable_schema: dict[str, Any] | None = None,
        change_summary: str | None = None,
        locale: str = "en",
        actor_id: UUID | None = None,
    ) -> NotificationTemplateVersion:
        """Publish a new immutable version for an existing template."""
        repo = NotificationRepository(db)
        template = await repo.get_template_by_id(tenant_id, template_id)
        if not template:
            raise NotFoundException("NotificationTemplate", template_id)

        # Get latest version to increment
        latest_version = template.current_version
        active_ver = await repo.get_active_version_for_template(tenant_id, template_id, locale)

        # Fallback to existing active version fields if not provided
        sub = subject if subject is not None else (active_ver.subject if active_ver else None)
        body = body_template if body_template is not None else (active_ver.body_template if active_ver else "")
        body_html = body_html_template if body_html_template is not None else (active_ver.body_html_template if active_ver else None)
        v_schema = variable_schema if variable_schema is not None else (active_ver.variable_schema_json if active_ver else {})

        cls.validate_template_size(body, "body_template")
        if body_html:
            cls.validate_template_size(body_html, "body_html_template")

        new_version_num = latest_version + 1

        # Mark previous active version as DEPRECATED or INACTIVE
        if active_ver:
            active_ver.status = TemplateStatus.DEPRECATED

        new_version = NotificationTemplateVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            template_id=template_id,
            version=new_version_num,
            status=TemplateStatus.ACTIVE,
            locale=locale,
            subject=sub,
            body_template=body,
            body_html_template=body_html,
            variable_schema_json=v_schema,
            published_at=datetime.now(UTC),
            published_by_id=actor_id,
            change_summary=change_summary or f"Published version {new_version_num}",
        )
        await repo.create_template_version(new_version)

        template.current_version = new_version_num
        template.updated_at = datetime.now(UTC)
        await db.commit()
        return new_version

    @classmethod
    async def preview_template(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        template_id: UUID,
        payload: TemplatePreviewRequest,
    ) -> TemplatePreviewResponse:
        """Preview rendering for an existing template using provided sample context."""
        repo = NotificationRepository(db)
        template = await repo.get_template_by_id(tenant_id, template_id)
        if not template:
            raise NotFoundException("NotificationTemplate", template_id)

        active_ver = await repo.get_active_version_for_template(
            tenant_id, template_id, payload.locale
        )
        if not active_ver:
            raise ValidationException(
                f"No active template version found for locale '{payload.locale}'."
            )

        missing = cls.validate_variables(
            active_ver.variable_schema_json or {}, payload.context
        )

        rendered_subject = (
            cls.render_text(active_ver.subject, payload.context)
            if active_ver.subject
            else None
        )
        rendered_body = cls.render_text(active_ver.body_template, payload.context)
        rendered_html = (
            cls.render_html(active_ver.body_html_template, payload.context)
            if active_ver.body_html_template
            else None
        )

        return TemplatePreviewResponse(
            template_key=template.template_key,
            channel=template.channel,
            version=active_ver.version,
            rendered_subject=rendered_subject,
            rendered_body=rendered_body,
            rendered_body_html=rendered_html,
            missing_variables=missing,
            is_valid=len(missing) == 0,
        )
