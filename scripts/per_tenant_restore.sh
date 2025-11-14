#!/bin/bash

# Same PATH as all backup scripts
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/sasiabburi/E--Commerce/venv/bin

# Load environment variables
if [ -f /Users/sasiabburi/E--Commerce/.env ]; then
    source /Users/sasiabburi/E--Commerce/.env
else
    echo "❌ ERROR: .env not found!"
    exit 1
fi

echo "🏗 Tenant Schema Restore Tool (Daily Backup)"
echo "---------------------------------------------"

# Ask for tenant
read -p "Enter tenant schema name to restore (e.g., tenant1_schema): " TENANT
TENANT=$(echo "$TENANT" | xargs)  # trim spaces

# Ask for date
read -p "Enter backup date (YYYY-MM-DD): " DATE
DATE=$(echo "$DATE" | xargs)

BACKUP_FILE="/Users/sasiabburi/E--Commerce/backups/tenants/daily/${DATE}/${TENANT}.dump"

# Validate backup file
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found:"
    echo "   $BACKUP_FILE"
    exit 1
fi

echo ""
echo "⚠️  WARNING: This will DELETE and RECREATE schema: '$TENANT'"
read -p "Type CONFIRM to continue: " CONFIRM

if [ "$CONFIRM" != "CONFIRM" ]; then
    echo "❌ Cancelled."
    exit 1
fi
echo ""

echo "🗑 Dropping old schema '$TENANT'..."
psql "host=$DB_HOST port=$DB_PORT user=$DB_USER password=$DB_PASSWORD dbname=$DB_NAME sslmode=$DB_SSLMODE" \
    -c "DROP SCHEMA IF EXISTS \"$TENANT\" CASCADE;" || { echo "❌ Failed to drop schema"; exit 1; }

echo "🆕 Recreating schema '$TENANT'..."
psql "host=$DB_HOST port=$DB_PORT user=$DB_USER password=$DB_PASSWORD dbname=$DB_NAME sslmode=$DB_SSLMODE" \
    -c "CREATE SCHEMA \"$TENANT\";" || { echo "❌ Failed to create schema"; exit 1; }

echo "🔄 Restoring tenant '$TENANT' from backup..."
pg_restore \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --schema="$TENANT" \
  --clean --if-exists \
  --no-owner \
  --verbose \
  "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Tenant schema '$TENANT' restored successfully!"
else
    echo "❌ Tenant restore failed. Check DB logs or dump integrity."
fi