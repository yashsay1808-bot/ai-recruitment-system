"""Initial schema migration: jobs, resumes, screening_sessions, screening_results, audit_logs.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-24 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=255), server_default="Engineering", nullable=False),
        sa.Column("min_experience", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("preferred_skills", sa.JSON(), nullable=False),
        sa.Column("preferred_degrees", sa.JSON(), nullable=False),
        sa.Column("description_text", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_jobs_id"), "jobs", ["id"], unique=False)
    op.create_index(op.f("ix_jobs_title"), "jobs", ["title"], unique=False)

    # 2. resumes table
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_text", sa.Text(), server_default="", nullable=False),
        sa.Column("parsed_data", sa.JSON(), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_resumes_id"), "resumes", ["id"], unique=False)
    op.create_index(op.f("ix_resumes_file_hash"), "resumes", ["file_hash"], unique=True)

    # 3. screening_sessions table
    op.create_table(
        "screening_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("session_name", sa.String(length=255), nullable=False),
        sa.Column("recruiter_email", sa.String(length=255), server_default="recruiter@enterprise.com", nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_screening_sessions_id"), "screening_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_screening_sessions_job_id"), "screening_sessions", ["job_id"], unique=False)

    # 4. screening_results table
    op.create_table(
        "screening_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=True),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("overall_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("rank", sa.Integer(), server_default="1", nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.Column("gap_results", sa.JSON(), nullable=False),
        sa.Column("candidate_data", sa.JSON(), nullable=False),
        sa.Column("rubric_scores", sa.JSON(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=True),
        sa.Column("decision_timestamp", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_screening_results_id"), "screening_results", ["id"], unique=False)
    op.create_index(op.f("ix_screening_results_session_id"), "screening_results", ["session_id"], unique=False)
    op.create_index(op.f("ix_screening_results_resume_id"), "screening_results", ["resume_id"], unique=False)

    # 5. audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor", sa.String(length=255), server_default="system", nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("screening_results")
    op.drop_table("screening_sessions")
    op.drop_table("resumes")
    op.drop_table("jobs")
