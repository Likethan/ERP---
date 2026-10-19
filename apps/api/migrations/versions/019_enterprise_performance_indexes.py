"""Enterprise Performance Engineering, Index Optimization & Scalability Migration (Step 32).

Revision ID: 019_enterprise_performance_indexes
Revises: 018_enterprise_reliability_disaster_recovery
Create Date: 2026-10-15 15:00:00.000000

Adds evidence-based composite indexes across high-traffic multi-tenant tables:
- Student Directory: program, batch, status, and roll number search
- Attendance Sessions & Records: chronological attendance logging and percentage calculation
- Examination Marks: assessment mark retrieval and transcript assembly
- Finance Invoices & Payments: student balance lookups, dues tracking, payment histories
- Campus Notifications: user inbox badge and unread feed optimization
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "019_enterprise_performance_indexes"
down_revision = "018_enterprise_reliability_disaster_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Student Directory Performance Indexes
    op.create_index(
        "idx_perf_students_tenant_prog_status",
        "people_students",
        ["tenant_id", "program_id", "status"],
    )
    op.create_index(
        "idx_perf_students_tenant_batch",
        "people_students",
        ["tenant_id", "batch_id"],
    )
    op.create_index(
        "idx_perf_students_tenant_roll",
        "people_students",
        ["tenant_id", "roll_number"],
    )
    op.create_index(
        "idx_perf_students_tenant_created",
        "people_students",
        ["tenant_id", "status", "created_at"],
    )

    # 2. Attendance Logging & Aggregation Performance Indexes
    op.create_index(
        "idx_perf_att_session_search",
        "attendance_sessions",
        ["tenant_id", "session_date", "status"],
    )
    op.create_index(
        "idx_perf_att_rec_student_date",
        "attendance_records",
        ["tenant_id", "student_id", "created_at"],
    )

    # 3. Examination Student Marks Performance Indexes
    op.create_index(
        "idx_perf_marks_tenant_assess_status",
        "examination_student_marks",
        ["tenant_id", "assessment_id", "status"],
    )

    # 4. Finance Invoices & Payments Performance Indexes
    op.create_index(
        "idx_perf_invoices_tenant_student_status",
        "finance_invoices",
        ["tenant_id", "student_id", "status"],
    )
    op.create_index(
        "idx_perf_invoices_tenant_due",
        "finance_invoices",
        ["tenant_id", "status", "due_date"],
    )
    op.create_index(
        "idx_perf_payments_tenant_student_date",
        "finance_payments",
        ["tenant_id", "student_id", "payment_date"],
    )
    op.create_index(
        "idx_perf_payments_tenant_status_date",
        "finance_payments",
        ["tenant_id", "status", "payment_date"],
    )

    # 5. User Notification Inbox & Badging Performance Indexes
    op.create_index(
        "idx_perf_notif_tenant_recipient_unread",
        "campus_notifications",
        ["tenant_id", "recipient_user_id", "is_read", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_perf_notif_tenant_recipient_unread", table_name="campus_notifications")
    op.drop_index("idx_perf_payments_tenant_status_date", table_name="finance_payments")
    op.drop_index("idx_perf_payments_tenant_student_date", table_name="finance_payments")
    op.drop_index("idx_perf_invoices_tenant_due", table_name="finance_invoices")
    op.drop_index("idx_perf_invoices_tenant_student_status", table_name="finance_invoices")
    op.drop_index("idx_perf_marks_tenant_assess_status", table_name="examination_student_marks")
    op.drop_index("idx_perf_att_rec_student_date", table_name="attendance_records")
    op.drop_index("idx_perf_att_session_search", table_name="attendance_sessions")
    op.drop_index("idx_perf_students_tenant_created", table_name="people_students")
    op.drop_index("idx_perf_students_tenant_roll", table_name="people_students")
    op.drop_index("idx_perf_students_tenant_batch", table_name="people_students")
    op.drop_index("idx_perf_students_tenant_prog_status", table_name="people_students")
