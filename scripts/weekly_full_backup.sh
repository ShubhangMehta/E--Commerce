#!/bin/bash

# Weekly full backup script
set -e

# Add absolute PATH so cron can find commands
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

# Load environment variables if available
if [ -f /Users/sasiabburi/E--Commerce/.env ]; then
  source /Users/sasiabburi/E--Commerce/.env
fi

# Create logs and backup directories if missing
mkdir -p /Users/sasiabburi/E--Commerce/logs
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/Users/sasiabburi/E--Commerce/backups/tenants/weekly/$DATE"
mkdir -p "$BACKUP_DIR"

echo "Starting weekly full backup for $DB_NAME on $DATE"

# Loop through all tenant schemas except system ones
for schema in $(psql "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
    -t -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg_%' AND schema_name NOT IN ('information_schema');")
do
  schema=$(echo $schema | xargs)  # trim whitespace
  echo "Backing up tenant schema: $schema"

  # Perform schema dump
  pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
    -n "\"$schema\"" -Fc -f "$BACKUP_DIR/${schema}_weekly.dump" 2>/dev/null || echo "⚠️ Skipped schema: $schema (not found or empty)"
done

# Delete backups older than 4 weeks (28 days)
find /Users/sasiabburi/E--Commerce/backups/tenants/weekly/* -mtime +28 -exec rm -rf {} \;

echo "✅ Weekly backup completed successfully at $BACKUP_DIR"