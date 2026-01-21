#!/bin/bash
# Script to run duplicate investigation queries against the database

DB_PATH="data/processed/database.db"

if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at $DB_PATH"
    exit 1
fi

echo "🔍 Investigating duplicates in fact_precios..."
echo "================================================"
echo ""

# Run investigation query
sqlite3 "$DB_PATH" < scripts/investigate_fact_precios_duplicates.sql > /tmp/duplicate_investigation.txt

echo "✅ Investigation complete. Results saved to /tmp/duplicate_investigation.txt"
echo ""
echo "📊 Summary:"
echo "-----------"
head -20 /tmp/duplicate_investigation.txt

echo ""
echo "💡 To view full results:"
echo "   cat /tmp/duplicate_investigation.txt"
echo ""
echo "💡 To view in a pager:"
echo "   less /tmp/duplicate_investigation.txt"
