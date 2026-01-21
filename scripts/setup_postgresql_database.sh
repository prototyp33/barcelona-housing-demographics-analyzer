#!/bin/bash
# Setup PostgreSQL database for Barcelona Housing migration

set -e

echo "=========================================="
echo "PostgreSQL Database Setup"
echo "=========================================="

# Get PostgreSQL version
PSQL_VERSION=$(psql --version | awk '{print $3}')
echo "✅ PostgreSQL version: $PSQL_VERSION"

# Database name
DB_NAME="barcelona_housing"

# Check if database already exists
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "⚠️  Database '$DB_NAME' already exists"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Dropping existing database..."
        dropdb "$DB_NAME" || true
    else
        echo "Using existing database"
        exit 0
    fi
fi

# Create database
echo "Creating database '$DB_NAME'..."
createdb "$DB_NAME"

# Enable PostGIS extension (for geospatial data) - Optional
echo "Enabling PostGIS extension (optional)..."
if psql -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2>/dev/null; then
    echo "✅ PostGIS extension enabled"
else
    echo "⚠️  PostGIS not available (optional - can install later with: brew install postgis)"
    echo "   Database will work without PostGIS for basic queries"
fi

# Verify setup
echo ""
echo "✅ Database setup complete!"
echo ""
echo "Database details:"
echo "  Name: $DB_NAME"
echo "  Host: localhost"
echo "  Port: 5432"
echo ""
echo "Next steps:"
echo "  1. Update .env file with your PostgreSQL credentials"
echo "  2. Run: python scripts/migrate_sqlite_to_postgresql.py"
echo ""
