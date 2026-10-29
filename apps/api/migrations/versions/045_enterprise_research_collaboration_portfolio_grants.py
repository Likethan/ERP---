"""Enterprise Research Collaboration, Project Portfolio, Grants & Sponsored Research Management (Step 61).

Revision ID: 045_enterprise_research_collaboration_portfolio_grants
Revises: 044_enterprise_international_relations_global_mobility
Create Date: 2026-10-26 12:00:00.000000

Enhances research domain indexes for:
- Optimized full-text and title filtering on institutional research projects
- High-efficiency researcher workload and team assignment lookups
- Grant opportunity closing-date deadline sweep indexes
- Sponsor agreement and grant award organization queries
- Application-to-project relationship lookups
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "045_enterprise_research_collaboration_portfolio_grants"
down_revision = "044_enterprise_international_relations_global_mobility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Project Title & Search Optimization Index
    op.create_index(
        "ix_research_projects_tenant_title",
        "research_projects",
        ["tenant_id", "title"],
        unique=False,
        if_not_exists=True,
    )

    # 2. Researcher Active Workload & Portfolio Queries
    op.create_index(
        "ix_research_team_tenant_user_active",
        "research_team_members",
        ["tenant_id", "user_id", "is_active"],
        unique=False,
        if_not_exists=True,
    )

    # 3. Grant Opportunities Closing Date & Status Sweep Index
    op.create_index(
        "ix_research_opps_tenant_closing_status",
        "research_funding_opportunities",
        ["tenant_id", "status", "closing_date"],
        unique=False,
        if_not_exists=True,
    )

    # 4. Sponsored Agreements & Awards Funding Organization Query Index
    op.create_index(
        "ix_research_awards_tenant_funding_org",
        "research_grant_awards",
        ["tenant_id", "funding_organization"],
        unique=False,
        if_not_exists=True,
    )

    # 5. Grant Applications Project Reference Index
    op.create_index(
        "ix_research_grants_tenant_project",
        "research_grant_applications",
        ["tenant_id", "project_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_research_grants_tenant_project", table_name="research_grant_applications", if_exists=True)
    op.drop_index("ix_research_awards_tenant_funding_org", table_name="research_grant_awards", if_exists=True)
    op.drop_index("ix_research_opps_tenant_closing_status", table_name="research_funding_opportunities", if_exists=True)
    op.drop_index("ix_research_team_tenant_user_active", table_name="research_team_members", if_exists=True)
    op.drop_index("ix_research_projects_tenant_title", table_name="research_projects", if_exists=True)
