"""Concurrency-Safe Numbering Sequence Generator and Format Engine for CampusOS (Step 23)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import NotFoundException
from app.models.configuration import NumberingResetFrequency, NumberingSequence
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import (
    NumberingSequenceCreate,
    NumberingSequenceUpdate,
    SequenceGenerateResponse,
)


class SequenceService:
    """Provides atomic, concurrency-safe unique sequence identifier generation."""

    @classmethod
    async def get_sequence(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        sequence_key: str,
    ) -> NumberingSequence:
        repo = ConfigurationRepository(db)
        seq = await repo.get_sequence(tenant_id, sequence_key)
        if not seq:
            raise NotFoundException("NumberingSequence", sequence_key)
        return seq

    @classmethod
    async def list_sequences(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[NumberingSequence]:
        repo = ConfigurationRepository(db)
        return await repo.list_sequences(tenant_id)

    @classmethod
    async def create_sequence(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: NumberingSequenceCreate,
    ) -> NumberingSequence:
        repo = ConfigurationRepository(db)
        seq = NumberingSequence(
            tenant_id=tenant_id,
            sequence_key=dto.sequence_key,
            name=dto.name,
            description=dto.description,
            prefix=dto.prefix,
            suffix=dto.suffix,
            pattern=dto.pattern,
            padding=dto.padding,
            current_val=dto.current_val,
            step=dto.step,
            reset_frequency=dto.reset_frequency,
            is_active=True,
        )
        return await repo.create_sequence(seq)

    @classmethod
    async def update_sequence(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        sequence_key: str,
        dto: NumberingSequenceUpdate,
        actor_id: UUID | None = None,
    ) -> NumberingSequence:
        repo = ConfigurationRepository(db)
        seq = await repo.get_sequence(tenant_id, sequence_key)
        if not seq:
            raise NotFoundException("NumberingSequence", sequence_key)

        if dto.name is not None:
            seq.name = dto.name
        if dto.description is not None:
            seq.description = dto.description
        if dto.prefix is not None:
            seq.prefix = dto.prefix
        if dto.suffix is not None:
            seq.suffix = dto.suffix
        if dto.pattern is not None:
            seq.pattern = dto.pattern
        if dto.padding is not None:
            seq.padding = dto.padding
        if dto.step is not None:
            seq.step = dto.step
        if dto.reset_frequency is not None:
            seq.reset_frequency = dto.reset_frequency
        if dto.is_active is not None:
            seq.is_active = dto.is_active

        await db.flush()

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.SEQUENCE_UPDATED,
            entity_type="numbering_sequence",
            entity_id=seq.id,
            user_id=actor_id,
            new_values_json={"pattern": seq.pattern, "prefix": seq.prefix, "padding": seq.padding},
            business_context=f"Numbering sequence '{sequence_key}' pattern updated.",
        )
        db.add(audit)
        await db.flush()

        return seq

    @classmethod
    async def generate_next_sequence_number(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        sequence_key: str,
        context_date: datetime | None = None,
    ) -> SequenceGenerateResponse:
        """Atomically generate the next sequential identifier under row-level database locking."""
        repo = ConfigurationRepository(db)
        # Lock row via SELECT ... FOR UPDATE to guarantee concurrency safety
        seq = await repo.get_sequence(tenant_id, sequence_key, for_update=True)
        if not seq:
            raise NotFoundException("NumberingSequence", sequence_key)

        now = context_date or datetime.now(UTC)
        current_year = now.year
        current_month = now.month

        # Handle periodic reset rules
        if seq.reset_frequency == NumberingResetFrequency.YEARLY:
            if seq.last_reset_year is None or seq.last_reset_year != current_year:
                seq.current_val = 0
                seq.last_reset_year = current_year
                seq.last_reset_at = now
        elif seq.reset_frequency == NumberingResetFrequency.MONTHLY:
            if (
                seq.last_reset_month is None
                or seq.last_reset_month != current_month
                or seq.last_reset_year is None
                or seq.last_reset_year != current_year
            ):
                seq.current_val = 0
                seq.last_reset_month = current_month
                seq.last_reset_year = current_year
                seq.last_reset_at = now

        # Atomic increment
        seq.current_val += seq.step
        await db.flush()

        # Format according to configured pattern template
        seq_str = str(seq.current_val).zfill(seq.padding)
        pattern = seq.pattern
        formatted = (
            pattern.replace("{PREFIX}", seq.prefix)
            .replace("{SUFFIX}", seq.suffix or "")
            .replace("{YYYY}", str(current_year))
            .replace("{YEAR}", str(current_year))
            .replace("{YY}", now.strftime("%y"))
            .replace("{MM}", now.strftime("%m"))
            .replace("{SEQ}", seq_str)
        )

        return SequenceGenerateResponse(
            sequence_key=seq.sequence_key,
            generated_number=formatted,
            current_val=seq.current_val,
        )
