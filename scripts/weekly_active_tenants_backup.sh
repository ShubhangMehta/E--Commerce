#!/bin/bash

set -e

echo "🚀 Starting WEEKLY tenant backup job"

PROJECT_DIR="/Users/sasiabburi/E--Commerce"
VENV_DIR="$PROJECT_DIR/venv"
ENV_FILE="$PROJECT_DIR/.env"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$VENV_DIR/bin"

# Load env
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
else
  echo "❌ .env file not found!"
  exit 1
fi

source "$VENV_DIR/bin/activate"
cd "$PROJECT_DIR"

python manage.py backup_weekly

echo "🎉 WEEKLY tenant backup job finished"