#!/bin/bash

# Set PATH same as backup scripts
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

# Load environment variables
if [ -f /Users/sasiabburi/E--Commerce/.env ]; then
    source /Users/sasiabburi/E--Commerce/.env
else
    echo "❌ ERROR: .env file not found!"
    exit 1
fi

echo "🌍 Starting FULL GLOBAL DATABASE RESTORE PROCESS..."
echo "⚠️ WARNING: This action will DELETE & RECREATE the entire database: $DB_NAME"
echo ""

# Ask user for confirmation
read -p "Type 'CONFIRM' to continue: " CONFIRM_INPUT

if [ "$CONFIRM_INPUT" != "CONFIRM" ]; then
    echo "❌ Restore cancelled."
    exit 1
fi

echo ""

# Ask user for backup date
read -p "Enter backup date (YYYY-MM-DD): " BACKUP_DATE

BACKUP_FILE="/Users/sasiabburi/E--Commerce/backups/global/weekly/full_backup_${BACKUP_DATE}.dump"

# Validate backup file
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found at:"
    echo "   $BACKUP_FILE"
    exit 1
fi

echo "🔄 Restoring full database from:"
echo "   $BACKUP_FILE"
echo ""

# Drop DB safely
echo "🗑 Dropping database $DB_NAME ..."
psql "host=$DB_HOST port=$DB_PORT user=$DB_USER password=$DB_PASSWORD dbname=postgres sslmode=$DB_SSLMODE" \
    -c "DROP DATABASE IF EXISTS \"$DB_NAME\";" || { echo "❌ Failed to drop DB"; exit 1; }

# Recreate DB
echo "🆕 Creating new database $DB_NAME ..."
psql "host=$DB_HOST port=$DB_PORT user=$DB_USER password=$DB_PASSWORD dbname=postgres sslmode=$DB_SSLMODE" \
    -c "CREATE DATABASE \"$DB_NAME\";" || { echo "❌ Failed to create DB"; exit 1; }

# Restore
echo "📦 Running pg_restore..."
pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -Fc -v "$BACKUP_FILE" \
    --no-owner --clean --if-exists

if [ $? -eq 0 ]; then
    echo "✅ FULL GLOBAL DATABASE RESTORE COMPLETED SUCCESSFULLY!"
else
    echo "❌ Restore failed. Please verify DB permissions or dump integrity."
fi