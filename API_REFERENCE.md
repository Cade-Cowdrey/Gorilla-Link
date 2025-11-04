# API Quick Reference Guide

## Base URL
```
https://pittstate-connect.onrender.com/api/v1
```

## Authentication

### Headers Required
```http
Authorization: Bearer <jwt_token>
X-API-Key: <api_key>  # For programmatic access
```

---

## Feature Flags & A/B Testing

### Check Feature Availability
```bash
GET /feature-flags/check/ai_assistant
```
**Response**:
```json
{"flag": "ai_assistant", "enabled": true}
```

### Get All User Flags
```bash
GET /feature-flags
```
**Response**:
```json
{
  "user_id": 123,
  "flags": {
    "ai_assistant": true,
    "scholarships_v2": true,
    "alumni_portal": false
  }
}
```

### Create Feature Flag (Admin)
```bash
POST /feature-flags
Content-Type: application/json

{
  "name": "beta_feature",
  "description": "New experimental feature",
  "enabled": true,
  "rollout_percentage": 25.0,
  "target_roles": ["student", "alumni"]
}
```

### Update Feature Flag (Admin)
```bash
PUT /feature-flags/beta_feature
Content-Type: application/json

{
  "enabled": true,
  "rollout_percentage": 50.0
}
```

### Get A/B Test Variant
```bash
GET /ab-tests/1/variant
```
**Response**:
```json
{"test_id": 1, "variant": "B"}
```

### Create A/B Test (Admin)
```bash
POST /ab-tests
Content-Type: application/json

{
  "name": "Homepage Redesign",
  "description": "Test new homepage layout",
  "variant_a": {"layout": "classic", "color": "blue"},
  "variant_b": {"layout": "modern", "color": "green"},
  "traffic_split": 0.5
}
```

### Start A/B Test (Admin)
```bash
POST /ab-tests/1/start
```

### Stop A/B Test (Admin)
```bash
POST /ab-tests/1/stop
Content-Type: application/json

{"winner": "B"}
```

### Get A/B Test Results (Admin)
```bash
GET /ab-tests/1/results
```
**Response**:
```json
{
  "test_id": 1,
  "name": "Homepage Redesign",
  "status": "completed",
  "total_participants": 1250,
  "variant_a": {"participants": 625, "percentage": 50.0},
  "variant_b": {"participants": 625, "percentage": 50.0},
  "winner": "B"
}
```

---

## Data Governance

### Get Data Lineage (Admin)
```bash
GET /governance/lineage/ScholarshipApplication/456
```
**Response**:
```json
{
  "entity_type": "ScholarshipApplication",
  "entity_id": 456,
  "lineage_chain": [
    {
      "entity_type": "ScholarshipApplication",
      "entity_id": 456,
      "source_type": "User",
      "source_id": 123,
      "transformation": "ai_matching_v2",
      "created_at": "2025-10-15T10:30:00Z"
    }
  ]
}
```

### Get Lineage Graph (Admin)
```bash
GET /governance/lineage-graph/ScholarshipApplication/456
```
**Response**:
```json
{
  "nodes": [
    {"id": "User:123", "type": "User", "entity_id": 123},
    {"id": "ScholarshipApplication:456", "type": "ScholarshipApplication", "entity_id": 456}
  ],
  "edges": [
    {"from": "User:123", "to": "ScholarshipApplication:456", "transformation": "ai_matching_v2"}
  ]
}
```

### Report Bias Metrics (Admin)
```bash
POST /governance/bias
Content-Type: application/json

{
  "model_name": "scholarship_success_predictor",
  "prediction_type": "success",
  "demographic_group": "underrepresented_minority",
  "true_positives": 85,
  "false_positives": 10,
  "true_negatives": 90,
  "false_negatives": 15
}
```
**Response**:
```json
{
  "model": "scholarship_success_predictor",
  "demographic_group": "underrepresented_minority",
  "metrics": {
    "accuracy": 0.875,
    "precision": 0.8947,
    "recall": 0.85,
    "f1_score": 0.8718,
    "false_positive_rate": 0.10
  }
}
```

### Compare Bias Across Groups (Admin)
```bash
GET /governance/bias/scholarship_success_predictor
```
**Response**:
```json
{
  "model": "scholarship_success_predictor",
  "groups": {
    "majority": {"avg_accuracy": 0.90, "avg_recall": 0.88},
    "underrepresented_minority": {"avg_accuracy": 0.87, "avg_recall": 0.85}
  },
  "disparate_impact": {
    "underrepresented_minority_vs_majority": {
      "ratio": 0.966,
      "passes_80_rule": true
    }
  },
  "fairness_assessment": "fair"
}
```

### Set Retention Policy (Admin)
```bash
POST /governance/retention
Content-Type: application/json

{
  "entity_type": "PageView",
  "retention_days": 90,
  "deletion_method": "hard",
  "legal_basis": "FERPA_compliance"
}
```

### Check Expired Records (Admin)
```bash
GET /governance/retention/PageView/check
```
**Response**:
```json
{
  "entity_type": "PageView",
  "expired_count": 1234,
  "records": [
    {"id": 1, "created": "2025-07-01T12:00:00Z", "age_days": 124},
    {"id": 2, "created": "2025-07-02T14:30:00Z", "age_days": 123}
  ]
}
```

### Run Data Quality Checks (Admin)
```bash
GET /governance/quality/User
```
**Response**:
```json
{
  "entity_type": "User",
  "checks": [
    {"check": "missing_email", "status": "pass", "count": 0},
    {"check": "duplicate_email", "status": "fail", "count": 3},
    {"check": "invalid_phone", "status": "pass", "count": 0}
  ],
  "overall_status": "fail"
}
```

---

## Notification Hub

### Get User Preferences
```bash
GET /notifications/preferences
```
**Response**:
```json
{
  "user_id": 123,
  "preferences": {
    "scholarship_deadline": {
      "in_app": true,
      "email": true,
      "sms": true,
      "push": true
    },
    "new_post": {
      "in_app": true,
      "email": false,
      "push": true
    }
  },
  "has_push_tokens": true
}
```

### Update Preferences
```bash
PUT /notifications/preferences
Content-Type: application/json

{
  "preferences": {
    "scholarship_deadline": {
      "in_app": true,
      "email": true,
      "sms": true,
      "push": true
    },
    "new_post": {
      "in_app": true,
      "email": false,
      "push": false
    }
  }
}
```

### Enable Channel for All Types
```bash
POST /notifications/channel/email/enable
```
**Response**:
```json
{"message": "Channel email enabled"}
```

### Disable Channel for All Types
```bash
POST /notifications/channel/sms/disable
```
**Response**:
```json
{"message": "Channel sms disabled"}
```

### List User Notifications
```bash
GET /notifications/list?unread_only=true&limit=20
```
**Response**:
```json
{
  "notifications": [
    {
      "id": 1,
      "message": "New scholarship match: Engineering Excellence Award",
      "category": "scholarship_matched",
      "link": "/scholarships/123",
      "is_read": false,
      "created_at": "2025-11-02T10:30:00Z"
    }
  ],
  "unread_count": 5
}
```

### Mark Notification as Read
```bash
POST /notifications/1/read
```

### Mark All as Read
```bash
POST /notifications/read-all
```

### Send Notification (Admin)
```bash
POST /notifications/send
Content-Type: application/json

{
  "user_id": 123,
  "notification_type": "scholarship_deadline",
  "title": "Deadline Approaching",
  "message": "Your scholarship application is due in 3 days",
  "data": {"scholarship_id": 456},
  "link": "/scholarships/456"
}
```
**Response**:
```json
{
  "success": true,
  "user_id": 123,
  "type": "scholarship_deadline",
  "priority": "critical",
  "channels": ["in_app", "email", "sms", "push"],
  "results": {
    "in_app": true,
    "email": true,
    "sms": true,
    "push": true
  }
}
```

### Send Bulk Notification (Admin)
```bash
POST /notifications/send-bulk
Content-Type: application/json

{
  "user_ids": [123, 456, 789],
  "notification_type": "system_maintenance",
  "title": "Scheduled Maintenance",
  "message": "PittState Connect will be down tonight from 12-2am",
  "link": "/system/status"
}
```
**Response**:
```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "errors": []
}
```

### Get Notification Stats (Admin)
```bash
GET /notifications/stats?days=7
```
**Response**:
```json
{
  "period_days": 7,
  "total_sent": 1250,
  "by_category": {
    "scholarship_deadline": 300,
    "new_post": 450,
    "new_message": 200,
    "event_reminder": 300
  },
  "read_count": 875,
  "unread_count": 375,
  "read_rate": 70.0
}
```

---

## Rate Limits

| Endpoint Category | Limit | Time Window |
|------------------|-------|-------------|
| Feature Flags - Check | No limit | - |
| Feature Flags - Create/Update | 10-20/hour | 1 hour |
| Feature Flags - Delete | 5/hour | 1 hour |
| A/B Tests - Create | 5/hour | 1 hour |
| Data Governance - Read | No limit | - |
| Data Governance - Write | 10-100/hour | 1 hour |
| Notifications - Preferences | 20/hour | 1 hour |
| Notifications - Send (Admin) | 30/hour | 1 hour |
| Notifications - Bulk Send | 10/hour | 1 hour |

---

## Error Responses

### 400 Bad Request
```json
{"error": "Invalid request data"}
```

### 401 Unauthorized
```json
{"error": "Authentication required"}
```

### 403 Forbidden
```json
{"error": "Admin access required"}
```

### 404 Not Found
```json
{"error": "Resource not found"}
```

### 429 Too Many Requests
```json
{"error": "Rate limit exceeded", "message": "Too many requests"}
```

### 500 Internal Server Error
```json
{"error": "Internal server error"}
```

---

## Code Examples

### Python
```python
import requests

BASE_URL = "https://pittstate-connect.onrender.com/api/v1"
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}

# Check feature flag
response = requests.get(
    f"{BASE_URL}/feature-flags/check/ai_assistant",
    headers=headers
)
data = response.json()
print(f"AI Assistant enabled: {data['enabled']}")

# Send notification
notification = {
    "user_id": 123,
    "notification_type": "new_message",
    "title": "New Message",
    "message": "You have a new message from John Doe"
}
response = requests.post(
    f"{BASE_URL}/notifications/send",
    headers=headers,
    json=notification
)
```

### JavaScript (Fetch)
```javascript
const BASE_URL = 'https://pittstate-connect.onrender.com/api/v1';
const headers = {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
};

// Check feature flag
const checkFeature = async (flagName) => {
  const response = await fetch(`${BASE_URL}/feature-flags/check/${flagName}`, {
    headers
  });
  const data = await response.json();
  return data.enabled;
};

// Update notification preferences
const updatePreferences = async (preferences) => {
  const response = await fetch(`${BASE_URL}/notifications/preferences`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ preferences })
  });
  return response.json();
};
```

### cURL
```bash
# Check feature flag
curl -X GET "https://pittstate-connect.onrender.com/api/v1/feature-flags/check/ai_assistant" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Update notification preferences
curl -X PUT "https://pittstate-connect.onrender.com/api/v1/notifications/preferences" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "scholarship_deadline": {
        "in_app": true,
        "email": true,
        "sms": true
      }
    }
  }'
```

---

## Webhook Events (Future)

Coming soon: Webhook notifications for:
- Feature flag changes
- A/B test completions
- Bias detection alerts
- Data quality failures
- Retention policy executions

---

*Last Updated: November 2, 2025*
