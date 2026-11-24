"""Repository for Enterprise Administration, Configuration & Policy Management (Step 23)."""

from uuid import UUID

from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import (
    ConfigurationDefinition,
    ConfigurationDependency,
    ConfigurationPolicy,
    ConfigurationPolicyVersion,
    ConfigurationValue,
    ConfigurationVersion,
    FeatureFlag,
    ModuleConfiguration,
    NumberingSequence,
)


class ConfigurationRepository:
    """Encapsulates transactional database persistence for system configuration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------------------------------
    # 1. Definitions
    # -------------------------------------------------------------------------

    async def get_definition_by_key(self, key: str) -> ConfigurationDefinition | None:
        stmt = select(ConfigurationDefinition).where(ConfigurationDefinition.key == key)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_definition_by_id(self, id: UUID) -> ConfigurationDefinition | None:
        stmt = select(ConfigurationDefinition).where(ConfigurationDefinition.id == id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_definitions(
        self,
        category: str | None = None,
        module: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ConfigurationDefinition], int]:
        filters = []
        if category:
            filters.append(ConfigurationDefinition.category == category)
        if module:
            filters.append(ConfigurationDefinition.module == module)
        if is_active is not None:
            filters.append(ConfigurationDefinition.is_active == is_active)

        count_stmt = select(func.count()).select_from(ConfigurationDefinition)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = select(ConfigurationDefinition)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = (
            stmt.order_by(ConfigurationDefinition.category, ConfigurationDefinition.key)
            .offset(offset)
            .limit(limit)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        return items, total

    async def create_definition(
        self, definition: ConfigurationDefinition
    ) -> ConfigurationDefinition:
        self.db.add(definition)
        await self.db.flush()
        return definition

    # -------------------------------------------------------------------------
    # 2. Values
    # -------------------------------------------------------------------------

    async def get_value_by_id(self, id: UUID) -> ConfigurationValue | None:
        stmt = select(ConfigurationValue).where(ConfigurationValue.id == id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_value(
        self,
        definition_id: UUID,
        tenant_id: UUID | None,
        scope_type: str,
        campus_id: UUID | None = None,
    ) -> ConfigurationValue | None:
        stmt = select(ConfigurationValue).where(
            ConfigurationValue.configuration_definition_id == definition_id,
            ConfigurationValue.scope_type == scope_type,
        )
        if tenant_id is not None:
            stmt = stmt.where(ConfigurationValue.tenant_id == tenant_id)
        else:
            stmt = stmt.where(ConfigurationValue.tenant_id.is_(None))

        if campus_id is not None:
            stmt = stmt.where(ConfigurationValue.campus_id == campus_id)
        else:
            stmt = stmt.where(ConfigurationValue.campus_id.is_(None))

        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_values_for_tenant(
        self,
        tenant_id: UUID,
        campus_id: UUID | None = None,
    ) -> list[ConfigurationValue]:
        stmt = select(ConfigurationValue).where(
            or_(
                ConfigurationValue.tenant_id == tenant_id,
                ConfigurationValue.tenant_id.is_(None),  # Platform defaults
            )
        )
        if campus_id is not None:
            stmt = stmt.where(
                or_(
                    ConfigurationValue.campus_id == campus_id,
                    ConfigurationValue.campus_id.is_(None),
                )
            )
        else:
            stmt = stmt.where(ConfigurationValue.campus_id.is_(None))

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_raw_values_for_definition(
        self,
        definition_id: UUID,
        tenant_id: UUID | None = None,
    ) -> list[ConfigurationValue]:
        stmt = select(ConfigurationValue).where(
            ConfigurationValue.configuration_definition_id == definition_id
        )
        if tenant_id is not None:
            stmt = stmt.where(
                or_(
                    ConfigurationValue.tenant_id == tenant_id,
                    ConfigurationValue.tenant_id.is_(None),
                )
            )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def delete_value(self, value_id: UUID) -> bool:
        stmt = delete(ConfigurationValue).where(ConfigurationValue.id == value_id)
        res = await self.db.execute(stmt)
        rowcount = int(getattr(res, "rowcount", 0) or 0)
        return rowcount > 0

    # -------------------------------------------------------------------------
    # 3. Versions
    # -------------------------------------------------------------------------

    async def create_version(self, version: ConfigurationVersion) -> ConfigurationVersion:
        self.db.add(version)
        await self.db.flush()
        return version

    async def list_versions(
        self,
        definition_id: UUID | None = None,
        tenant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConfigurationVersion]:
        stmt = select(ConfigurationVersion)
        filters = []
        if definition_id is not None:
            filters.append(ConfigurationVersion.configuration_definition_id == definition_id)
        if tenant_id is not None:
            filters.append(
                or_(
                    ConfigurationVersion.tenant_id == tenant_id,
                    ConfigurationVersion.tenant_id.is_(None),
                )
            )
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(desc(ConfigurationVersion.created_at)).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_version(self, id: UUID) -> ConfigurationVersion | None:
        stmt = select(ConfigurationVersion).where(ConfigurationVersion.id == id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_version_by_number(
        self,
        definition_id: UUID,
        version_number: int,
        tenant_id: UUID | None = None,
    ) -> ConfigurationVersion | None:
        stmt = select(ConfigurationVersion).where(
            ConfigurationVersion.configuration_definition_id == definition_id,
            ConfigurationVersion.version_number == version_number,
        )
        if tenant_id is not None:
            stmt = stmt.where(
                or_(
                    ConfigurationVersion.tenant_id == tenant_id,
                    ConfigurationVersion.tenant_id.is_(None),
                )
            )
        stmt = stmt.order_by(desc(ConfigurationVersion.created_at)).limit(1)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    # -------------------------------------------------------------------------
    # 4. Policies
    # -------------------------------------------------------------------------

    async def get_policy(
        self,
        policy_key: str,
        tenant_id: UUID | None = None,
        campus_id: UUID | None = None,
    ) -> ConfigurationPolicy | None:
        stmt = select(ConfigurationPolicy).where(ConfigurationPolicy.policy_key == policy_key)
        if tenant_id is not None:
            stmt = stmt.where(
                or_(
                    ConfigurationPolicy.tenant_id == tenant_id,
                    ConfigurationPolicy.tenant_id.is_(None),
                )
            )
        if campus_id is not None:
            stmt = stmt.where(
                or_(
                    ConfigurationPolicy.campus_id == campus_id,
                    ConfigurationPolicy.campus_id.is_(None),
                )
            )
        stmt = stmt.order_by(desc(ConfigurationPolicy.priority)).limit(1)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_policies(
        self,
        tenant_id: UUID | None = None,
        module: str | None = None,
        status: str | None = None,
    ) -> list[ConfigurationPolicy]:
        stmt = select(ConfigurationPolicy)
        filters = []
        if tenant_id is not None:
            filters.append(
                or_(
                    ConfigurationPolicy.tenant_id == tenant_id,
                    ConfigurationPolicy.tenant_id.is_(None),
                )
            )
        if module:
            filters.append(ConfigurationPolicy.module == module)
        if status:
            filters.append(ConfigurationPolicy.status == status)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(ConfigurationPolicy.module, desc(ConfigurationPolicy.priority))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_policy(self, policy: ConfigurationPolicy) -> ConfigurationPolicy:
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def create_policy_version(
        self, policy_version: ConfigurationPolicyVersion
    ) -> ConfigurationPolicyVersion:
        self.db.add(policy_version)
        await self.db.flush()
        return policy_version

    # -------------------------------------------------------------------------
    # 5. Feature Flags
    # -------------------------------------------------------------------------

    async def get_feature_flag(self, key: str, tenant_id: UUID | None = None) -> FeatureFlag | None:
        stmt = select(FeatureFlag).where(FeatureFlag.key == key)
        if tenant_id is not None:
            stmt = stmt.where(
                or_(
                    FeatureFlag.tenant_id == tenant_id,
                    FeatureFlag.tenant_id.is_(None),
                )
            )
            # Prioritize tenant override over platform global
            stmt = stmt.order_by(desc(FeatureFlag.tenant_id.isnot(None))).limit(1)
        else:
            stmt = stmt.limit(1)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_feature_flags(
        self, tenant_id: UUID | None = None, module: str | None = None
    ) -> list[FeatureFlag]:
        stmt = select(FeatureFlag)
        filters = []
        if tenant_id is not None:
            filters.append(
                or_(
                    FeatureFlag.tenant_id == tenant_id,
                    FeatureFlag.tenant_id.is_(None),
                )
            )
        if module:
            filters.append(FeatureFlag.module == module)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(FeatureFlag.module, FeatureFlag.key)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_feature_flag(self, flag: FeatureFlag) -> FeatureFlag:
        self.db.add(flag)
        await self.db.flush()
        return flag

    # -------------------------------------------------------------------------
    # 6. Module Configurations
    # -------------------------------------------------------------------------

    async def get_module_config(self, tenant_id: UUID, module: str) -> ModuleConfiguration | None:
        stmt = select(ModuleConfiguration).where(
            ModuleConfiguration.tenant_id == tenant_id,
            ModuleConfiguration.module == module,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_module_configs(self, tenant_id: UUID) -> list[ModuleConfiguration]:
        stmt = select(ModuleConfiguration).where(ModuleConfiguration.tenant_id == tenant_id)
        stmt = stmt.order_by(ModuleConfiguration.module)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def upsert_module_config(self, module_cfg: ModuleConfiguration) -> ModuleConfiguration:
        self.db.add(module_cfg)
        await self.db.flush()
        return module_cfg

    # -------------------------------------------------------------------------
    # 7. Numbering Sequences
    # -------------------------------------------------------------------------

    async def get_sequence(
        self, tenant_id: UUID, sequence_key: str, for_update: bool = False
    ) -> NumberingSequence | None:
        stmt = select(NumberingSequence).where(
            NumberingSequence.tenant_id == tenant_id,
            NumberingSequence.sequence_key == sequence_key,
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_sequences(self, tenant_id: UUID) -> list[NumberingSequence]:
        stmt = select(NumberingSequence).where(NumberingSequence.tenant_id == tenant_id)
        stmt = stmt.order_by(NumberingSequence.sequence_key)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_sequence(self, seq: NumberingSequence) -> NumberingSequence:
        self.db.add(seq)
        await self.db.flush()
        return seq

    # -------------------------------------------------------------------------
    # 8. Dependencies
    # -------------------------------------------------------------------------

    async def list_dependencies(
        self, key: str | None = None, module: str | None = None
    ) -> list[ConfigurationDependency]:
        stmt = select(ConfigurationDependency)
        filters = []
        if key:
            filters.append(ConfigurationDependency.configuration_key == key)
        if module:
            filters.append(ConfigurationDependency.consumer_module == module)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(ConfigurationDependency.configuration_key)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_dependency(self, dep: ConfigurationDependency) -> ConfigurationDependency:
        self.db.add(dep)
        await self.db.flush()
        return dep
