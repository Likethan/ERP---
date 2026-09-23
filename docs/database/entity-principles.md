# CampusOS — Database Entity Principles

## 1. Single Source of Truth for Core Entities

The core architectural invariant of CampusOS is: **No entity is duplicated across modules.**

```text
                             ┌───────────────────┐
                             │    people_users   │
                             └─────────▲─────────┘
                                       │ 1:1
                             ┌─────────┴─────────┐
                             │  people_students  │
                             └─────────┬─────────┘
                                       │
        ┌──────────────┬───────────────┼───────────────┬──────────────┐
        ▼              ▼               ▼               ▼              ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│  attendance  ││ examination  ││   finance    ││  placement   ││  documents   │
│  _records    ││  _marks      ││  _invoices   ││_applications ││  _student    │
└──────────────┘└──────────────┘└──────────────┘└──────────────┘└──────────────┘
```

- If Attendance needs to record presence for a student, it stores `student_id: UUID` pointing to `people_students.id`.
- If Finance generates a tuition invoice, it binds `student_id: UUID` to the invoice.
- If Placement records an application to Google or Microsoft, it binds `student_id: UUID`.
- If the student's name, email, or guardian contact updates, it is updated **in exactly one place** (`people_users` / `people_students`), reflecting immediately across all modules.

---

## 2. Standardized Base Entity Fields

All persistent tables inherit from a standardized base model:

```python
class Base(DeclarativeBase):
    pass

class BaseModel(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

class TenantScopedModel(BaseModel):
    __abstract__ = True

    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
```

### Key Conventions:

1. **Primary Keys**: Always `UUIDv4` to prevent ID enumeration attacks and enable distributed entity generation.
2. **Timestamps**: Stored in `TIMESTAMPTZ` (UTC). Timezone conversion occurs on presentation to clients based on institutional configuration.
3. **Soft Deletion (`deleted_at`)**: Financial records, marks, and attendance records are never hard deleted; audit integrity is strictly preserved.
4. **Naming Conventions**: Snake_case table names prefixed with domain identifier (e.g., `people_students`, `academics_courses`, `finance_invoices`).
