# 🔄 Backup & Export Guide

This guide covers the nightly PostgreSQL backup system and CSV export functionality for the Feedback Analysis Agent.

## 📦 Nightly Database Backup

The system includes automated nightly backups using `pg_dump` with compression and retention policies.

### 🚀 Setup Nightly Backups

#### 1. Configure Environment Variables

Set these environment variables in your deployment:

```bash
# Backup configuration
BACKUP_DIR=/var/backups/feedback-agent          # Where to store backups
DATABASE_URL=postgresql://user:password@host:5432/db  # Database connection
RETENTION_DAYS=30                               # How long to keep backups
COMPRESSION_LEVEL=6                             # gzip compression (1-9)
LOG_FILE=/var/log/feedback-agent/backup.log     # Backup log location
```

#### 2. Create Backup Directory

```bash
sudo mkdir -p /var/backups/feedback-agent
sudo chown -R your-app-user:your-app-user /var/backups/feedback-agent

# Create log directory
sudo mkdir -p /var/log/feedback-agent
sudo chown -R your-app-user:your-app-user /var/log/feedback-agent
```

#### 3. Schedule Nightly Backups

Add to crontab (`crontab -e`):

```bash
# Run backup at 2:00 AM daily
0 2 * * * /path/to/server/scripts/nightly_backup.sh
```

For Docker deployments, mount the backup directory:

```yaml
volumes:
  - ./backups:/var/backups/feedback-agent
  - ./logs:/var/log/feedback-agent
```

### 📋 Backup Script Features

- **Compressed backups**: Uses `pg_dump --compress` for smaller file sizes
- **Automatic retention**: Removes backups older than `RETENTION_DAYS`
- **Integrity verification**: Tests backup files after creation
- **Comprehensive logging**: Logs all operations with timestamps
- **Error handling**: Exits on failures with clear error messages

### 📊 Backup File Format

```
feedback_backup_20241107_020000.sql.gz
               └─┬────┘ └─┬──┘ └┬┘
                 │        │    │
                 │        │    └── Compression (.gz)
                 │        └── Time (HHMMSS)
                 └── Date (YYYYMMDD)
```

## 🔄 Database Restore

### 🚨 Important Safety Notes

- **Always backup current database** before restore
- **Restore operations are destructive** - they overwrite existing data
- **Test restores** on staging environments first
- **Verify backup integrity** before production restores

### 📋 Restore Steps

#### Method 1: Using the Restore Script (Recommended)

```bash
cd server/scripts

# List available backups
./restore_backup.sh --list

# Restore from latest backup (interactive)
./restore_backup.sh feedback_backup_20241107_020000.sql.gz

# Restore without confirmation prompt
./restore_backup.sh -f feedback_backup_20241107_020000.sql.gz --confirm
```

#### Method 2: Manual Restore

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@host:5432/db"
export PGPASSWORD="your-password"

# Extract connection details
DB_HOST="your-host"
DB_PORT="5432"
DB_USER="your-user"
DB_NAME="your-database"

# Terminate active connections
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
"

# Drop and recreate database
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

# Restore from backup
pg_restore \
    --host=$DB_HOST \
    --port=$DB_PORT \
    --username=$DB_USER \
    --dbname=$DB_NAME \
    --verbose \
    --clean \
    --if-exists \
    /path/to/backup/feedback_backup_20241107_020000.sql.gz

# Run migrations if needed
cd server
alembic upgrade head
```

### 🔍 Post-Restore Verification

```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM feedback;"

# Verify data integrity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM topic;"

# Run application health checks
curl http://your-app/health

# Test API endpoints
curl http://your-app/api/feedback?page=1&page_size=1
```

## 📊 CSV Export API

The system provides streaming CSV export endpoints for data analysis and backup purposes.

### 🚀 Available Export Endpoints

#### 1. Feedback Export
```http
GET /api/export.csv?[filters]
```

**Query Parameters:**
- `source` (string): Filter by feedback source
- `customer_id` (string): Filter by customer ID
- `start_date` (YYYY-MM-DD): Filter by creation date (start)
- `end_date` (YYYY-MM-DD): Filter by creation date (end)
- `sentiment_min` (0.0-1.0): Minimum sentiment score
- `sentiment_max` (0.0-1.0): Maximum sentiment score

**Example:**
```bash
# Export all feedback
curl -o feedback.csv "http://your-app/api/export.csv"

# Export feedback from specific source and date range
curl -o filtered_feedback.csv "http://your-app/api/export.csv?source=website&start_date=2024-01-01&end_date=2024-12-31"

# Export feedback with sentiment filter
curl -o positive_feedback.csv "http://your-app/api/export.csv?sentiment_min=0.7"
```

#### 2. Topics Export
```http
GET /api/export/topics.csv?min_feedback_count=1
```

**Query Parameters:**
- `min_feedback_count` (integer): Minimum feedback count for topics (default: 1)

**Example:**
```bash
# Export all topics with at least 5 feedback items
curl -o topics.csv "http://your-app/api/export/topics.csv?min_feedback_count=5"
```

#### 3. Analytics Export
```http
GET /api/export/analytics.csv?[date_filters]
```

**Query Parameters:**
- `start_date` (YYYY-MM-DD): Start date for analytics
- `end_date` (YYYY-MM-DD): End date for analytics

**Example:**
```bash
# Export analytics for current month
curl -o analytics.csv "http://your-app/api/export/analytics.csv?start_date=2024-11-01"
```

### 📋 CSV Format Specifications

#### Feedback Export Columns
```csv
id,text,source,customer_id,sentiment_score,created_at,updated_at,primary_topic,topic_keywords
```

#### Topics Export Columns
```csv
id,label,keywords,created_at,updated_at,feedback_count,avg_sentiment
```

#### Analytics Export Columns
```csv
date,total_feedback,positive_feedback,negative_feedback,neutral_feedback,avg_sentiment,unique_customers,top_sources
```

### ⚡ Streaming Performance

- **Memory efficient**: Data is streamed directly to response, not loaded into memory
- **Large dataset support**: Can handle millions of rows without memory issues
- **Gzip compression**: Automatic compression for faster downloads
- **Proper headers**: `Content-Disposition: attachment` for automatic download

### 🔧 API Usage Examples

#### Python Client
```python
import requests

# Export feedback with filters
params = {
    'source': 'website',
    'start_date': '2024-01-01',
    'sentiment_min': 0.5
}

response = requests.get('http://your-app/api/export.csv', params=params)
with open('feedback_export.csv', 'wb') as f:
    f.write(response.content)
```

#### JavaScript Client
```javascript
// Using fetch API
const exportData = async (endpoint, filename) => {
    const response = await fetch(endpoint);
    const blob = await response.blob();

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
};

// Usage
exportData('/api/export.csv?source=website', 'website_feedback.csv');
```

### 📊 Export Monitoring

All export operations are logged and monitored:

```bash
# Check application logs for export activity
tail -f /var/log/feedback-agent/app.log | grep export

# Monitor export performance metrics
curl http://your-app/metrics | grep export
```

## 🔧 Troubleshooting

### Backup Issues

**"pg_dump: could not connect to database"**
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Verify pg_dump is installed
which pg_dump
```

**"No space left on device"**
```bash
# Check disk space
df -h $BACKUP_DIR

# Clean old backups manually
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Export Issues

**"Export failed: database connection error"**
```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM feedback;"

# Verify API is running
curl http://your-app/health
```

**"Memory error on large exports"**
- Exports are streamed, so this shouldn't happen
- Check for database connection leaks
- Verify the streaming implementation isn't being bypassed

### Restore Issues

**"pg_restore: [archiver] input file does not appear to be a valid archive"**
```bash
# Check if backup file is corrupted
file /path/to/backup.sql.gz

# Verify backup with pg_restore --list
pg_restore --list /path/to/backup.sql.gz
```

**"database 'X' does not exist"**
```bash
# Create database manually before restore
createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
```

## 📈 Automation Examples

### Docker Compose with Backups

```yaml
version: '3.8'
services:
  backup:
    image: postgres:15-alpine
    volumes:
      - ./backups:/backups
      - ./scripts:/scripts
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/feedback_db
    command: sh -c "chmod +x /scripts/nightly_backup.sh && /scripts/nightly_backup.sh"
    depends_on:
      - postgres
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nightly-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command: ["/scripts/nightly_backup.sh"]
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: database-url
            volumeMounts:
            - name: backup-scripts
              mountPath: /scripts
            - name: backups
              mountPath: /var/backups/feedback-agent
          volumes:
          - name: backup-scripts
            configMap:
              name: backup-scripts
          - name: backups
            persistentVolumeClaim:
              claimName: backup-pvc
```

## 🔐 Security Considerations

- **Backup encryption**: Consider encrypting backups at rest
- **Access control**: Restrict access to backup files and scripts
- **Network security**: Use SSL/TLS for database connections
- **Credential management**: Use secret management for database passwords
- **Audit logging**: All backup and export operations are logged

## 📞 Support

For issues with backup/restore operations:
1. Check the log files in `/var/log/feedback-agent/`
2. Verify environment variables are set correctly
3. Test database connectivity manually
4. Review the troubleshooting section above
