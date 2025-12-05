#!/bin/bash

# Correct PATH for pg_dump, psql, python
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

export SUPABASE_URL
export SUPABASE_KEY
# Load environment variables
source /Users/sasiabburi/E--Commerce/.env

DATE=$(date +%Y-%m-%d)

echo "🚀 Starting tenant backups for $DB_NAME on $DATE"

# Loop through all tenant schemas except system ones
TENANT_SCHEMAS=$(psql "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
  -t -c "SELECT schema_name FROM information_schema.schemata 
         WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog');")

for schema in $TENANT_SCHEMAS; do

  schema=$(echo $schema | xargs)  # Trim spaces
  echo "📦 Backing up tenant schema: $schema"

  # Run pg_dump and PIPE output directly to Python uploader
  pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
      -n "$schema" -Fc \
  | /Users/sasiabburi/E--Commerce/venv/bin/python3 \
        /Users/sasiabburi/E--Commerce/backups/utils/upload_to_supabase.py "$schema" "$DATE" "daily"

  echo "✅ Uploaded: $schema.dump → Supabase Storage"

done

echo "🎉 All tenant backups completed & uploaded successfully!"