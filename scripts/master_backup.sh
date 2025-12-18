#!/bin/bash

set -e

# Correct PATH for pg_dump, psql, python
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

# Load environment variables
export $(grep -v '^#' /Users/sasiabburi/E--Commerce/.env | xargs)

DATE=$(date +%Y-%m-%d)

echo "🚀 Starting MASTER DB BACKUP for database: $DB_NAME"

DUMP_FILE="/tmp/master_${DATE}.dump"

# Create full DB dump
pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
    -Fc -f "$DUMP_FILE"

echo "📦 Master DB dump created at: $DUMP_FILE"

# Upload to Supabase using Python (PIPE the dump file into python)
cat "$DUMP_FILE" | /Users/sasiabburi/E--Commerce/venv/bin/python3 \
    /Users/sasiabburi/E--Commerce/backups/utils/upload_to_supabase.py \
    "master" "$DATE" "master"

echo "🎉 MASTER DB BACKUP COMPLETED"
