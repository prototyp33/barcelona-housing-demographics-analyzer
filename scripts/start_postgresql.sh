#!/bin/bash
# Start PostgreSQL service

echo "Starting PostgreSQL..."

# Try to start via Homebrew
if command -v brew &> /dev/null; then
    echo "Starting PostgreSQL via Homebrew..."
    brew services start postgresql@16 || brew services start postgresql
    sleep 2
    
    # Check if it's running
    if brew services list | grep -q "postgresql.*started"; then
        echo "✅ PostgreSQL started successfully"
        exit 0
    fi
fi

# Alternative: Try to start directly
echo "Attempting to start PostgreSQL directly..."
pg_ctl -D /opt/homebrew/var/postgresql@16 start 2>/dev/null || \
pg_ctl -D /usr/local/var/postgresql@16 start 2>/dev/null || \
pg_ctl -D ~/Library/Application\ Support/Postgres/var-16 start 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL started successfully"
else
    echo "❌ Could not start PostgreSQL automatically"
    echo ""
    echo "Please start PostgreSQL manually:"
    echo "  brew services start postgresql@16"
    echo "  or"
    echo "  pg_ctl -D /opt/homebrew/var/postgresql@16 start"
fi
