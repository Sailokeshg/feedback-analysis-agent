#!/bin/bash

# Nightly PostgreSQL Database Backup Script
# This script creates compressed backups of the feedback database
# Run this via cron: 0 2 * * * /path/to/nightly_backup.sh

set -e  # Exit on any error

# Configuration - Update these variables for your environment
BACKUP_DIR="${BACKUP_DIR:-/var/backups/feedback-agent}"
DATABASE_URL="${DATABASE_URL:-postgresql://user:password@localhost:5432/feedback_db}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"  # gzip compression level (1-9)

# Logging
LOG_FILE="${LOG_FILE:-/var/log/feedback-agent/backup.log}"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [BACKUP] $*" | tee -a "$LOG_FILE"
}

error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" >&2 | tee -a "$LOG_FILE"
    exit 1
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR" || error "Failed to create backup directory: $BACKUP_DIR"

# Generate timestamp for backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="feedback_backup_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

log "Starting nightly database backup"
log "Backup directory: $BACKUP_DIR"
log "Backup file: $BACKUP_FILENAME"

# Extract database connection details from DATABASE_URL
# Expected format: postgresql://user:password@host:port/database
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    error "Invalid DATABASE_URL format. Expected: postgresql://user:password@host:port/database"
fi

# Set PGPASSWORD environment variable for pg_dump
export PGPASSWORD="$DB_PASSWORD"

log "Connecting to database: $DB_HOST:$DB_PORT/$DB_NAME as user: $DB_USER"

# Perform the backup using pg_dump with gzip compression
if pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --no-password \
    --format=custom \
    --compress="$COMPRESSION_LEVEL" \
    --file="$BACKUP_PATH" \
    --verbose; then

    # Get backup file size
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    log "Backup completed successfully. Size: $BACKUP_SIZE"

    # Verify backup integrity
    log "Verifying backup integrity..."
    if pg_restore --list "$BACKUP_PATH" > /dev/null 2>&1; then
        log "Backup integrity check passed"
    else
        error "Backup integrity check failed - backup may be corrupted"
    fi

else
    error "Database backup failed"
fi

# Clean up old backups (keep only last RETENTION_DAYS days)
log "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "feedback_backup_*.sql.gz" -type f -mtime +"$RETENTION_DAYS" -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "feedback_backup_*.sql.gz" -type f | wc -l)
log "Cleanup completed. $BACKUP_COUNT backup(s) remaining."

# Unset password for security
unset PGPASSWORD

log "Nightly backup process completed successfully"

# Optional: Send notification (uncomment and configure as needed)
# curl -X POST -H 'Content-type: application/json' \
#      --data "{\"text\":\"Database backup completed: $BACKUP_FILENAME ($BACKUP_SIZE)\"}" \
#      YOUR_SLACK_WEBHOOK_URL

exit 0
