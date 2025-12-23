"""Initial migration - Create tables for categories, products, and stock

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-23 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('nom', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('date_creation', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('date_modification', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('sku', sa.String(50), unique=True, nullable=False),
        sa.Column('nom', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('categorie_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('prix_ht', sa.Numeric(10, 2), nullable=False),
        sa.Column('taux_tva', sa.Numeric(4, 2), nullable=False, server_default='20.0'),
        sa.Column('prix_ttc', sa.Numeric(10, 2), nullable=False),
        sa.Column('unite_mesure', sa.String(20), nullable=False, server_default='g'),
        sa.Column('poids_unitaire', sa.Numeric(8, 3), nullable=True),
        sa.Column('fournisseur', sa.String(100), nullable=True),
        sa.Column('origine', sa.String(100), nullable=True),
        sa.Column('notes_qualite', sa.Text(), nullable=True),
        sa.Column('date_creation', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('date_modification', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('statut', sa.String(20), nullable=False, server_default='actif'),
    )
    
    # Create stock table
    op.create_table(
        'stock',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('produit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('quantite', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('seuil_alerte', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('emplacement', sa.String(100), nullable=True),
        sa.Column('date_derniere_modification', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for better query performance
    op.create_index('ix_categories_code', 'categories', ['code'], unique=False)
    op.create_index('ix_products_sku', 'products', ['sku'], unique=False)
    op.create_index('ix_products_categorie_id', 'products', ['categorie_id'], unique=False)
    op.create_index('ix_stock_produit_id', 'stock', ['produit_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('stock')
    op.drop_table('products')
    op.drop_table('categories')
