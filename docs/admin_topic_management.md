# 🔧 Admin Topic Management

Advanced topic curation and feedback reassignment interface for administrators.

## 📋 Overview

The admin topic management interface allows administrators to:
- Edit topic labels and keywords
- Reassign misclassified feedback comments to correct topics
- View audit trails of all changes
- Refresh materialized views for immediate analytics updates

## 🚀 Accessing Admin Interface

### Login Process

1. Click "Admin Login" in the top navigation
2. Use one of these credentials:
   - **Admin**: `admin` / `admin123` (full access)
   - **Viewer**: `viewer` / `viewer123` (read-only)
3. Navigate to "Topic Management" in the admin navigation

### JWT Authentication

All admin API endpoints require JWT authentication. Include the token in requests:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Token Expiration**: 24 hours
**Refresh**: Re-login when token expires
**Security**: Tokens are validated on each request

### Interface Layout

The admin interface consists of two panels:

#### Left Panel: Topics List
- View all topics with their current labels and keywords
- Click "Edit" to modify topic labels and keywords
- Click "View Feedback" to see assigned feedback comments

#### Right Panel: Feedback Reassignment
- Shows feedback comments for the selected topic
- Click "Reassign" on any feedback to move it to a different topic
- Add optional reasons for reassignments

## 📝 Editing Topics

### Topic Label Updates

1. Click "Edit" next to any topic
2. Modify the topic label in the text field
3. Update keywords as a comma-separated list
4. Click "Save" to apply changes

**Example:**
```
Label: "Product Quality Issues"
Keywords: quality, defect, broken, poor, unsatisfactory
```

### Keyword Management

Keywords help the system classify new feedback:
- Add relevant terms that appear in feedback
- Remove outdated or irrelevant keywords
- Use synonyms and related terms

## 🔄 Reassigning Feedback

### Process

1. Select a topic from the left panel
2. Click "View Feedback" to load assigned comments
3. Find the misclassified feedback comment
4. Click "Reassign" next to the comment
5. Select the correct topic from the dropdown
6. Add an optional reason for the reassignment
7. Confirm the reassignment

### Reassignment Logic

- Feedback comments are linked to topics via NLP annotations
- Reassignment updates the `topic_id` in the annotation table
- All changes are logged in the audit trail
- Materialized views are automatically refreshed

## 📊 Data Updates

### Immediate Reflections

Changes are reflected immediately in:
- Topic labels and keywords in the interface
- Feedback-topic assignments
- Audit logs for compliance

### Analytics Updates

After any change:
1. Materialized views are refreshed automatically
2. Dashboard analytics update within seconds
3. Topic distribution charts reflect new assignments
4. Sentiment trends incorporate reassigned feedback

## 📋 Audit Trail

### Change Logging

All administrative actions are logged:
- Topic label/keyword updates
- Feedback reassignments
- User information and timestamps
- Optional reason fields

### Viewing Audit Logs

Access audit logs via:
- API: `GET /admin/topic-audit`
- Command line: Check application logs

### Audit Log Structure

```json
{
  "id": 123,
  "topic_id": 5,
  "action": "reassign_feedback",
  "old_label": "Feedback reassigned",
  "new_label": "From topic 3 (Quality) to topic 5 (Support) - Incorrect classification",
  "changed_by": "admin",
  "changed_at": "2024-11-07T14:30:00Z",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

## 🔧 API Endpoints

### Authentication

```http
POST /admin/login
# Admin login with JWT token
{
  "username": "admin",
  "password": "admin123"
}

POST /admin/viewer/login
# Viewer login (read-only access)
{
  "username": "viewer",
  "password": "viewer123"
}
```

### System Management

```http
GET /admin/stats
# Get comprehensive system statistics

GET /admin/health/database
# Check database connectivity and health

GET /admin/config
# Get system configuration (admin only)

POST /admin/maintenance/refresh-materialized-view
# Refresh database materialized views

POST /admin/cleanup/old-data
# Remove old feedback data
{
  "days_old": 365,
  "dry_run": true
}

GET /admin/logs/recent
# Get recent application logs

POST /admin/cache/clear
# Clear Redis cache
```

### Topics Management

```http
GET /admin/topics
# Returns all topics with labels and keywords

POST /admin/relabel-topic
# Update topic label and keywords
{
  "topic_id": 1,
  "new_label": "Updated Topic Label",
  "new_keywords": ["keyword1", "keyword2"]
}
```

### Feedback Reassignment

```http
GET /admin/topics/{topic_id}/feedback
# Get feedback assigned to a topic

POST /admin/reassign-feedback
# Reassign feedback to different topic
{
  "feedback_ids": ["uuid-string"],
  "target_topic_id": 2,
  "reason": "Incorrect classification"
}
```

### Audit Logs

```http
GET /admin/topic-audit
# Get recent audit logs (paginated)

GET /admin/topic-audit/{topic_id}
# Get audit history for specific topic
```

### Viewer Endpoints

```http
GET /admin/viewer/stats
# Get statistics for viewer dashboard

GET /admin/viewer/dashboard
# Get dashboard data for viewers

GET /admin/viewer/profile
# Get viewer profile information
```

## 🚨 Safety & Best Practices

### Before Making Changes

1. **Backup First**: Ensure database backups are current
2. **Test Environment**: Test changes in staging first
3. **Document Changes**: Always provide reasons for reassignments
4. **Review Impact**: Consider how changes affect analytics

### Change Guidelines

- **Topic Labels**: Keep them descriptive and consistent
- **Keywords**: Focus on terms that appear in actual feedback
- **Reassignments**: Only move feedback when clearly misclassified
- **Reasons**: Always document why feedback was reassigned

### Monitoring Changes

- Watch dashboard analytics after changes
- Monitor for unexpected shifts in topic distributions
- Review audit logs regularly for compliance

## 🔄 Automated Processes

### Materialized View Refresh

After any topic or feedback change:
```sql
REFRESH MATERIALIZED VIEW daily_feedback_aggregates;
```

This ensures:
- Dashboard data stays current
- Analytics reflect the latest changes
- Performance remains optimal

### Cache Invalidation

Changes trigger cache clearing for:
- Topic analytics data
- Feedback examples
- Dashboard summaries

## 📊 Analytics Impact

### Immediate Effects

- **Topic Distribution**: Pie charts update instantly
- **Sentiment Trends**: Lines adjust for reassigned feedback
- **Volume Metrics**: Counts reflect new assignments

### Long-term Effects

- **Model Training**: Improved topic classification accuracy
- **User Experience**: More accurate feedback categorization
- **Business Insights**: Better understanding of customer issues

## 🐛 Troubleshooting

### Common Issues

**"Failed to update topic"**
- Check user permissions
- Verify topic ID exists
- Ensure database connectivity

**"Reassignment failed"**
- Verify feedback ID format
- Check target topic exists
- Confirm admin authentication

**Changes not reflected**
- Wait a few seconds for cache refresh
- Check materialized view refresh logs
- Verify database transaction completion

### Recovery Procedures

**Undo Reassignment**
```bash
# Check audit logs for the change
GET /admin/topic-audit

# Manually reverse via API
POST /admin/reassign-feedback
{
  "feedback_id": "original-id",
  "new_topic_id": original_topic_id,
  "reason": "Reverting incorrect reassignment"
}
```

**Restore Topic Labels**
```bash
# Use audit history to find previous state
GET /admin/topic-audit/{topic_id}

# Restore via API
POST /admin/relabel-topic
{
  "topic_id": 1,
  "new_label": "Previous Label",
  "new_keywords": ["previous", "keywords"]
}
```

## 📈 Performance Considerations

### Database Impact

- Topic updates: Minimal impact
- Feedback reassignments: Low impact per operation
- Materialized view refresh: Moderate impact (runs in background)

### User Experience

- Changes appear instantly in the UI
- Analytics update within seconds
- No service downtime required

## 🔐 Security

### Access Control

- Admin authentication required for all operations
- Role-based permissions (admin vs viewer)
- Audit trail for compliance
- IP address and user agent logging

### Data Protection

- All changes are logged immutably
- Sensitive operations require explicit confirmation
- Database backups protect against accidental changes

## 📞 Support

For issues with topic management:

1. Check browser console for JavaScript errors
2. Verify admin authentication is active
3. Review server logs for API errors
4. Test API endpoints directly with curl
5. Check database connectivity and permissions

## 🎯 Best Practices Summary

- **Consistent Labeling**: Use clear, descriptive topic names
- **Keyword Relevance**: Focus on terms that appear in feedback
- **Reason Documentation**: Always explain reassignments
- **Regular Audits**: Review changes periodically
- **Test First**: Validate changes in staging environment
- **Monitor Impact**: Watch analytics after significant changes
