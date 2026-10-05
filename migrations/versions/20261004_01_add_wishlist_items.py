"""add wishlist items

Revision ID: 20261004_01
Revises: e559bbb96325
Create Date: 2026-10-04 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "20261004_01"
down_revision = "e559bbb96325"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "wishlist_items",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_wishlist_items_user_product"),
    )
    with op.batch_alter_table("wishlist_items", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_wishlist_items_product_id"), ["product_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_wishlist_items_user_id"), ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("wishlist_items", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_wishlist_items_user_id"))
        batch_op.drop_index(batch_op.f("ix_wishlist_items_product_id"))

    op.drop_table("wishlist_items")
