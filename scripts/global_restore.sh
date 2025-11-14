#!/bin/bash

# Load environment variables
source /Users/sasiabburi/E--Commerce/.env

echo "🌍 Starting full database restore process..."

# Ask user for backup date
read -p "Enter backup date (YYYY-MM-DD): " BACKUP_DATE

BACKUP_FILE="/Users/sasiabburi/E--Commerce/backups/global/weekly/full_backup_${BACKUP_DATE}.dump"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "🔄 Restoring full database from $BACKUP_FILE ..."

# Drop and recreate the target database before restore
psql "host=$DB_HOST port=$DB_PORT user=$DB_USER password=$DB_PASSWORD dbname=postgres sslmode=$DB_SSLMODE" -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql "host=$DB_HOST port=$DB_PORT user=$DB_USER password=$DB_PASSWORD dbname=postgres sslmode=$DB_SSLMODE" -c "CREATE DATABASE $DB_NAME;"

# Restore the full dump into the new database
pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -Fc -v "$BACKUP_FILE" --no-owner --clean --if-exists

if [ $? -eq 0 ]; then
  echo "✅ Global database restore completed successfully!"
else
  echo "❌ Restore failed. Please check connection or dump integrity."
fi