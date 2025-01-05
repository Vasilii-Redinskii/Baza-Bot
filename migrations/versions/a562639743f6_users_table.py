"""users table

Revision ID: a562639743f6
Revises: 
Create Date: 2025-01-05 12:59:35.007732

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a562639743f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('local_dict', sa.PickleType(), nullable=True),
    sa.Column('step_list', sa.PickleType(), nullable=True),
    sa.Column('main_list', sa.PickleType(), nullable=True),
    sa.Column('menu_list', sa.PickleType(), nullable=True),
    sa.Column('merge_list', sa.PickleType(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    # ### end Alembic commands ###
