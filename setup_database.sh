#!/bin/bash
# Database setup script for Fund Reconciliation System

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Fund Reconciliation v2.0 - Database Setup                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic not found. Installing dependencies..."
    pip install -r requirements-local.txt
fi

# Set database URL if not set
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="sqlite:///./fund_reconciliation.db"
    echo "📌 Using default SQLite database: $DATABASE_URL"
fi

# Create alembic version table and apply migrations
echo ""
echo "🔄 Applying database migrations..."

# Check if alembic.ini exists
if [ ! -f "alembic.ini" ]; then
    echo "⚠️  alembic.ini not found. Creating from template..."
fi

# Apply migrations
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully!"
else
    echo "❌ Database migration failed"
    exit 1
fi

# Show database info
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Database Setup Complete!                                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Database: $DATABASE_URL"
echo ""
echo "Tables created:"
echo "  ✓ funds              - Master fund data"
echo "  ✓ reference_prices   - Benchmark prices"
echo "  ✓ fund_positions     - Position data from CSVs"
echo "  ✓ reconciled_prices  - Reconciliation results"
echo "  ✓ monthly_returns    - Monthly performance data"
echo ""
echo "To use the database:"
echo "  1. Set DATABASE_URL environment variable (optional)"
echo "  2. Run: python main.py --api"
echo "  3. Or: python main.py (for E2E mode)"
echo ""
