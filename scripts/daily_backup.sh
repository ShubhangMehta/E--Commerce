#!/bin/bash

# absolute PATH so cron finds pg_dump/psql etc
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

# Load environment variables from .env file
source /Users/sasiabburi/E--Commerce/.env

DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/Users/sasiabburi/E--Commerce/backups/tenants/daily/$DATE"
mkdir -p "$BACKUP_DIR"

echo "Starting backup for $DB_NAME on $DATE"

# Loop through schemas except system schemas
for schema in $(psql "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
    -t -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog');")
do
  echo "Backing up tenant: $schema"
  pg_dump "host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=$DB_SSLMODE" \
    -n "$schema" -Fc > "$BACKUP_DIR/${schema}.dump"
done

# Delete backups older than 7 days
find /Users/sasiabburi/E--Commerce/backups/tenants/daily/* -mtime +7 -exec rm -rf {} \;

echo "Backup completed successfully at $BACKUP_DIR"