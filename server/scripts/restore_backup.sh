#!/bin/bash

# PostgreSQL Database Restore Script
# This script restores a database from a pg_dump backup
# Usage: ./restore_backup.sh <backup_file.sql.gz>

set -e  # Exit on any error

# Configuration - Update these variables for your environment
DATABASE_URL="${DATABASE_URL:-postgresql://user:password@localhost:5432/feedback_db}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/feedback-agent}"

# Logging
LOG_FILE="${LOG_FILE:-/var/log/feedback-agent/restore.log}"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [RESTORE] $*" | tee -a "$LOG_FILE"
}

error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" >&2 | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $*" >&2 | tee -a "$LOG_FILE"
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS] [BACKUP_FILE]"
    echo ""
    echo "Restore a PostgreSQL database from backup"
    echo ""
    echo "OPTIONS:"
    echo "  -f, --file BACKUP_FILE    Specify backup file path"
    echo "  -l, --list                List available backup files"
    echo "  -c, --confirm             Skip confirmation prompt"
    echo "  -h, --help                Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 -l                                    # List available backups"
    echo "  $0 feedback_backup_20241107_020000.sql.gz  # Restore specific backup"
    echo "  $0 -f /path/to/backup.sql.gz -c          # Restore without confirmation"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  DATABASE_URL    Database connection string"
    echo "  BACKUP_DIR      Directory containing backup files (default: $BACKUP_DIR)"
}

# Function to list available backups
list_backups() {
    echo "Available backup files in $BACKUP_DIR:"
    echo "----------------------------------------"

    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "Backup directory does not exist: $BACKUP_DIR"
    fi

    # List backup files with size and date
    find "$BACKUP_DIR" -name "feedback_backup_*.sql.gz" -type f -printf "%P %s %T@\n" | \
    sort -k3 -n | \
    while read -r filename size timestamp; do
        date_str=$(date -d "@$timestamp" "+%Y-%m-%d %H:%M:%S")
        size_mb=$(echo "scale=2; $size/1024/1024" | bc 2>/dev/null || echo "$size")
        printf "  %-40s %8s MB  %s\n" "$filename" "$size_mb" "$date_str"
    done

    if [[ $(find "$BACKUP_DIR" -name "feedback_backup_*.sql.gz" -type f | wc -l) -eq 0 ]]; then
        echo "  No backup files found."
    fi
}

# Parse command line arguments
SKIP_CONFIRMATION=false
LIST_BACKUPS=false
BACKUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        -l|--list)
            LIST_BACKUPS=true
            shift
            ;;
        -c|--confirm)
            SKIP_CONFIRMATION=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            error "Unknown option: $1"
            ;;
        *)
            # If no -f flag and argument doesn't start with -, treat as backup file
            if [[ -z "$BACKUP_FILE" && ! "$1" =~ ^- ]]; then
                BACKUP_FILE="$1"
            else
                error "Unexpected argument: $1"
            fi
            shift
            ;;
    esac
done

# Handle list command
if [[ "$LIST_BACKUPS" == true ]]; then
    list_backups
    exit 0
fi

# Validate backup file
if [[ -z "$BACKUP_FILE" ]]; then
    error "No backup file specified. Use -l to list available backups or -f to specify a file."
fi

# If backup file doesn't contain path, prepend backup directory
if [[ "$BACKUP_FILE" != /* ]]; then
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    error "Backup file does not exist: $BACKUP_FILE"
fi

log "Starting database restore"
log "Backup file: $BACKUP_FILE"

# Extract database connection details from DATABASE_URL
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    error "Invalid DATABASE_URL format. Expected: postgresql://user:password@host:port/database"
fi

# Show warning and confirmation
warning "⚠️  WARNING: This will OVERWRITE the existing database!"
warning "Database: $DB_HOST:$DB_PORT/$DB_NAME"
warning "Backup file: $BACKUP_FILE"
echo ""

if [[ "$SKIP_CONFIRMATION" != true ]]; then
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log "Restore cancelled by user"
        exit 0
    fi
fi

# Set PGPASSWORD environment variable
export PGPASSWORD="$DB_PASSWORD"

log "Connecting to database: $DB_HOST:$DB_PORT/$DB_NAME as user: $DB_USER"

# Terminate active connections to the database (except our own)
log "Terminating active connections to database..."
psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="postgres" \
    --no-password \
    --command="
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
    " >/dev/null 2>&1 || warning "Could not terminate active connections (this may be normal)"

# Drop and recreate the database
log "Recreating database..."
psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="postgres" \
    --no-password \
    --command="DROP DATABASE IF EXISTS $DB_NAME;" >/dev/null

psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="postgres" \
    --no-password \
    --command="CREATE DATABASE $DB_NAME;" >/dev/null

# Restore from backup
log "Restoring database from backup..."
if pg_restore \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --no-password \
    --verbose \
    --clean \
    --if-exists \
    --create \
    "$BACKUP_FILE"; then

    log "Database restore completed successfully"

    # Run any post-restore operations (migrations, etc.)
    log "Running post-restore operations..."
    # Add any additional commands here if needed

else
    error "Database restore failed"
fi

# Unset password for security
unset PGPASSWORD

log "Database restore process completed successfully"

# Optional: Send notification
# curl -X POST -H 'Content-type: application/json' \
#      --data "{\"text\":\"Database restore completed from: $(basename "$BACKUP_FILE")\"}" \
#      YOUR_SLACK_WEBHOOK_URL

exit 0
