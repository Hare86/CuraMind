"""Add user fields (username, salutation, is_approved, pending_role_name) and new roles

Revision ID: 002_add_user_fields_and_roles
Revises: 001_initial_schema
Create Date: 2026-03-06
"""
from alembic import op
import sqlalchemy as sa

revision = "002_add_user_fields_and_roles"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column("users", sa.Column("username", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("salutation", sa.String(16), nullable=True))
    op.add_column("users", sa.Column("is_approved", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("users", sa.Column("pending_role_name", sa.String(64), nullable=True))

    # Add unique index on username
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # Mark existing users as approved (they were created before this migration)
    op.execute("UPDATE users SET is_approved = true")

    # Seed new roles
    op.execute("""
        INSERT INTO roles (id, name, description, permissions) VALUES
        (gen_random_uuid(), 'psychologist', 'Licensed psychologist access', '{"query": true, "upload": true, "edit_articles": true}'),
        (gen_random_uuid(), 'rehab_staff', 'Rehabilitation staff access', '{"query": true, "upload": true, "edit_articles": true}'),
        (gen_random_uuid(), 'hospital_admin', 'Hospital administrator access', '{"query": true, "upload": true, "edit_articles": true, "manage_kb": true}')
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "pending_role_name")
    op.drop_column("users", "is_approved")
    op.drop_column("users", "salutation")
    op.drop_column("users", "username")
