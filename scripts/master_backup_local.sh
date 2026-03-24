#!/bin/bash

set -e

# Correct PATH for pg_dump, psql
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

# Load environment variables
export $(grep -v '^#' /Users/sasiabburi/E--Commerce/.env | xargs)

DATE=$(date +%Y-%m-%d_%H-%M)

# Local folder to store backups
LOCAL_BACKUP_DIR="$HOME/E--Commerce/local_backups/master_backups_local"
mkdir -p "$LOCAL_BACKUP_DIR"

echo "🚀 Starting LOCAL MASTER DB BACKUP for database: $DB_NAME"

DUMP_FILE="$LOCAL_BACKUP_DIR/master_${DATE}.dump"

# Create full DB dump locally
pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
    -Fc -f "$DUMP_FILE"

echo "📦 Local Master DB dump created at: $DUMP_FILE"

echo "🎉 LOCAL MASTER DB BACKUP COMPLETED"