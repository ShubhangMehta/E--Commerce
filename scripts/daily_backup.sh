#!/bin/bash

# Correct PATH for pg_dump, psql, python
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

# Load environment variables from .env
export $(grep -v '^#' /Users/sasiabburi/E--Commerce/.env | xargs)

DATE=$(date +%Y-%m-%d)

echo "🚀 Starting DAILY tenant backups for $DB_NAME on $DATE"

# Fetch tenant schemas (exclude all system schemas)
TENANT_SCHEMAS=$(psql "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
  -t -c "SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT LIKE 'pg_%'
        AND schema_name NOT IN ('public', 'information_schema')
        AND schema_name NOT LIKE 'auth%'
        AND schema_name NOT Like 'graph%'
        AND schema_name NOT LIKE 'extensions%'
        AND schema_name NOT LIKE 'storage%'
        AND schema_name NOT LIKE 'vault%'
        ORDER BY schema_name;")

for schema in $TENANT_SCHEMAS; do

  schema=$(echo $schema | xargs)  # Trim whitespace

  echo "📦 Dumping tenant schema: $schema"

  # Dump ONLY this schema & pipe to Python uploader
  pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
      -n "$schema" -Fc \
  | /Users/sasiabburi/E--Commerce/venv/bin/python3 \
        /Users/sasiabburi/E--Commerce/backups/utils/upload_to_supabase.py \
        "$schema" "$DATE" "daily"

  echo "✅ Uploaded: $schema.dump → backups/tenants/daily/$DATE/"
done

echo "🎉 All tenant DAILY backups completed successfully!"

echo "📧 Sending backup status emails..."

source /Users/sasiabburi/E--Commerce/venv/bin/activate
cd /Users/sasiabburi/E--Commerce

python manage.py send_backup_status_email --type=daily --date="$DATE"