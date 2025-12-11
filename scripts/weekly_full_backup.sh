#!/bin/bash

set -e

# Correct PATH for pg_dump, python
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

# Load environment variables from .env
export $(grep -v '^#' /Users/sasiabburi/E--Commerce/.env | xargs)

DATE=$(date +%Y-%m-%d_%H-%M)
DB_NAME=$DB_NAME

echo "🚀 Starting WEEKLY full backup for $DB_NAME on $DATE"

# Temporary dump location
DUMP_FILE="/tmp/weekly_${DATE}.dump"

# Run pg_dump
pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
    -Fc -f "$DUMP_FILE"

echo "📦 Weekly backup dump created → $DUMP_FILE"

# Upload to Supabase through Python (pipe dump file)
cat "$DUMP_FILE" | /Users/sasiabburi/E--Commerce/venv/bin/python3 \
    /Users/sasiabburi/E--Commerce/backups/utils/upload_to_supabase.py \
    "$DB_NAME" "$DATE" "weekly"

echo "🎉 WEEKLY BACKUP COMPLETED"