"""Add loans tables and enhanced model fields

Revision ID: add_loans_enhanced
Revises: 7e0ea2c13577
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_loans_enhanced'
down_revision = '7e0ea2c13577'
branch_labels = None
depends_on = None


def upgrade():
    # === CREATE LOANS TABLE ===
    op.create_table('loans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('lender_name', sa.String(length=200), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('received_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), server_default='0.00'),
        sa.Column('remaining_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('is_paid', sa.Boolean(), server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # === CREATE LOAN_PAYMENTS TABLE ===
    op.create_table('loan_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # === ADD NEW COLUMNS TO EXISTING TABLES ===

    # Add contract_type to employees (SQLite-compatible: use batch)
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contract_type', sa.String(length=20), server_default='full-time'))

    # Add phase to projects (if not exists)
    try:
        with op.batch_alter_table('projects', schema=None) as batch_op:
            batch_op.add_column(sa.Column('phase', sa.String(length=20), server_default='building'))
    except Exception:
        pass  # Column may already exist

    # Add owner_capital to projects (if not exists)
    try:
        with op.batch_alter_table('projects', schema=None) as batch_op:
            batch_op.add_column(sa.Column('owner_capital', sa.Numeric(precision=15, scale=2), server_default='0.00'))
    except Exception:
        pass  # Column may already exist

    # Add phase to expense_transactions (if not exists)
    try:
        with op.batch_alter_table('expense_transactions', schema=None) as batch_op:
            batch_op.add_column(sa.Column('phase', sa.String(length=20), server_default='operating'))
    except Exception:
        pass  # Column may already exist

    # Add is_direct_cost to expense_transactions (if not exists)
    try:
        with op.batch_alter_table('expense_transactions', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_direct_cost', sa.Boolean(), server_default='0'))
    except Exception:
        pass  # Column may already exist


def downgrade():
    # Drop new tables
    op.drop_table('loan_payments')
    op.drop_table('loans')

    # Remove added columns
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.drop_column('contract_type')

    # Note: Not dropping phase, owner_capital, is_direct_cost as they may have existed before
