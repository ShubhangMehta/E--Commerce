#!/bin/bash

# Load environment variables
source /Users/sasiabburi/E--Commerce/.env

# Ask for tenant name and date
read -p "Enter tenant schema name to restore (e.g., Tenant1_schema): " TENANT
read -p "Enter backup date (YYYY-MM-DD): " DATE

# Backup path
BACKUP_FILE="/Users/sasiabburi/E--Commerce/backups/tenants/daily/${DATE}/${TENANT}.dump"

# Check if file exists
if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "🔄 Restoring tenant '$TENANT' from $BACKUP_FILE..."

# Restore the schema using pg_restore
pg_restore \
  --host=$DB_HOST \
  --port=$DB_PORT \
  --username=$DB_USER \
  --dbname=$DB_NAME \
  --no-password \
  --schema=$TENANT \
  --clean --if-exists \
  --no-owner \
  --verbose \
  "$BACKUP_FILE"

echo "✅ Tenant '$TENANT' restored successfully!"