#!/bin/bash

# Weekly full backup - upload directly to Supabase Storage
set -e

# Correct PATH for pg_dump, psql, python
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

# Load environment variables
if [ -f /Users/sasiabburi/E--Commerce/.env ]; then
  source /Users/sasiabburi/E--Commerce/.env
fi

DATE=$(date +%Y-%m-%d)

echo "🚀 Starting WEEKLY full backup for $DB_NAME on $DATE"

# Query only tenant schemas (exclude PostgreSQL internal schemas)
TENANT_SCHEMAS=$(psql "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
  -t -c "SELECT schema_name 
         FROM information_schema.schemata 
         WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog')
           AND schema_name NOT LIKE 'pg_%'
           AND schema_name NOT LIKE 'pg_toast%'
           AND schema_name NOT LIKE 'pg_temp_%';")

for schema in $TENANT_SCHEMAS; do

  schema=$(echo "$schema" | xargs)   # trim whitespace
  echo "📦 Weekly backup: $schema"

  # Pipe pg_dump → python upload
  pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
      -n "$schema" -Fc \
  | /Users/sasiabburi/E--Commerce/venv/bin/python3 \
        /Users/sasiabburi/E--Commerce/backups/utils/upload_to_supabase.py "$schema-weekly" "$DATE" "weekly"

  echo "✅ Uploaded: $schema-weekly.dump → Supabase Storage"

done

echo "🎉 WEEKLY full backups completed & uploaded successfully!"