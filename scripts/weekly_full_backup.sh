#!/bin/bash
set -e

PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

# SAFE env loading
set -a
source /Users/sasiabburi/E--Commerce/.env
set +a

DATE=$(date +%Y-%m-%d)

echo "🚀 Starting WEEKLY FULL backup for $DB_NAME on $DATE"

DUMP_FILE="/tmp/${DB_NAME}_weekly_${DATE}.dump"

pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
  -Fc \
  -f "$DUMP_FILE"

echo "📦 Full database dump created → $DUMP_FILE"

cat "$DUMP_FILE" | /Users/sasiabburi/E--Commerce/venv/bin/python3 \
  /Users/sasiabburi/E--Commerce/backups/utils/upload_to_supabase.py \
  "$DB_NAME" "$DATE" "weekly"

rm -f "$DUMP_FILE"

echo "🎉 WEEKLY FULL BACKUP COMPLETED"