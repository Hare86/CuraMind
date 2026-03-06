"""Initial schema — all tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-03-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # roles
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.String(256)),
        sa.Column("permissions", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # permissions
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("resource", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(256), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("full_name", sa.String(256)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # knowledge_bases
    op.create_table(
        "knowledge_bases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(128)),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("qdrant_collection", sa.String(256), nullable=False, unique=True),
        sa.Column("document_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("file_type", sa.String(32)),
        sa.Column("file_size_bytes", sa.Integer),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True),
        sa.Column("error_message", sa.Text),
        sa.Column("page_count", sa.Integer),
        sa.Column("chunk_count", sa.Integer),
        sa.Column("doc_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )

    # document_chunks
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doc_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("qdrant_point_id", postgresql.UUID(as_uuid=True)),
        sa.Column("page_number", sa.Integer),
        sa.Column("chunk_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("token_count", sa.Integer),
        sa.Column("chunk_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # research_articles
    op.create_table(
        "research_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("url", sa.Text, nullable=False, unique=True),
        sa.Column("source", sa.String(64)),
        sa.Column("authors", sa.Text),
        sa.Column("abstract", sa.Text),
        sa.Column("summary", sa.Text),
        sa.Column("status", sa.String(32), nullable=False,
                  server_default="pending_review", index=True),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True)),
        sa.Column("article_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("scraped_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # source_submissions
    op.create_table(
        "source_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("submission_type", sa.String(32)),
        sa.Column("url", sa.Text),
        sa.Column("file_path", sa.Text),
        sa.Column("title", sa.Text),
        sa.Column("summary", sa.Text),
        sa.Column("status", sa.String(32), nullable=False,
                  server_default="pending_review", index=True),
        sa.Column("admin_notes", sa.Text),
        sa.Column("target_kb_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    )

    # notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("notification_type", sa.String(64)),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # feedback
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("response_text", sa.Text, nullable=False),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True)),
        sa.Column("rating", sa.String(32), nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("query_mode", sa.String(64)),
        sa.Column("retrieval_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Seed default roles
    op.execute("""
        INSERT INTO roles (id, name, description, permissions) VALUES
        (gen_random_uuid(), 'admin', 'Full platform access', '{"all": true}'),
        (gen_random_uuid(), 'researcher', 'Research access and KB management', '{"query": true, "upload": true, "research": true}'),
        (gen_random_uuid(), 'doctor', 'Clinical professional access', '{"query": true, "upload": true}'),
        (gen_random_uuid(), 'student', 'Basic query access', '{"query": true}')
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("notifications")
    op.drop_table("source_submissions")
    op.drop_table("research_articles")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("knowledge_bases")
    op.drop_table("users")
    op.drop_table("permissions")
    op.drop_table("roles")
