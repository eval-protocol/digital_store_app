#!/bin/bash
set -euo pipefail

echo "Loading Chinook schema into 'chinook' database..."
# Filter out database-level commands from the upstream script
sed '/^\s*DROP DATABASE IF EXISTS/Id;/^\s*CREATE DATABASE/Id' /chinook.sql > /tmp/chinook_nodb.sql
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d chinook -f /tmp/chinook_nodb.sql
echo "Chinook schema loaded."

