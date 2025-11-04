# Developer Integration Guide

## How to Use the New Production Services

This guide shows you how to integrate Feature Flags, Data Governance, and Notification Hub into your code.

---

## Feature Flags

### Basic Usage - Check if Feature is Enabled

```python
from services.feature_flag_service import get_feature_flag_service
from flask_login import current_user

@app.route('/scholarships')
@login_required
def scholarships():
    service = get_feature_flag_service()
    
    # Check if new scholarship UI is enabled
    role = current_user.role.name if current_user.role else None
    show_v2 = service.is_enabled('scholarships_v2', current_user.id, role)
    
    if show_v2:
        return render_template('scholarships_v2.html')
    else:
        return render_template('scholarships.html')
```

### Gradual Rollout Pattern

```python
# Enable for 10% of users
service.create_flag(
    name='new_dashboard',
    description='New analytics dashboard',
    enabled=True,
    rollout_percentage=10.0  # Start small
)

# After testing, increase to 50%
service.update_flag('new_dashboard', rollout_percentage=50.0)

# After validation, go to 100%
service.update_flag('new_dashboard', rollout_percentage=100.0)
```

### Role-Based Features

```python
# Enable only for alumni
service.create_flag(
    name='alumni_portal',
    description='Alumni engagement portal',
    enabled=True,
    rollout_percentage=100.0,
    target_roles=['alumni']
)

# Check in route
if service.is_enabled('alumni_portal', current_user.id, 'alumni'):
    # Show alumni features
```

### A/B Testing UI Components

```python
@app.route('/homepage')
def homepage():
    service = get_feature_flag_service()
    
    # Get variant for this user
    variant = service.get_ab_variant(test_id=1, user_id=current_user.id)
    
    if variant == 'A':
        layout = 'classic'
    elif variant == 'B':
        layout = 'modern'
    else:
        layout = 'classic'  # Fallback
    
    return render_template('homepage.html', layout=layout)
```

### Template Usage (Jinja2)

```jinja
{# In your template #}
{% if current_user.is_authenticated %}
  {% set ff_service = get_feature_flag_service() %}
  {% set show_ai = ff_service.is_enabled('ai_assistant', current_user.id) %}
  
  {% if show_ai %}
    <div class="ai-assistant">
      <button onclick="openGorillaChatGPT()">
        <i class="fas fa-robot"></i> Ask GorillaGPT
      </button>
    </div>
  {% endif %}
{% endif %}
```

---

## Data Governance

### Track Data Lineage

```python
from services.data_governance_service import get_data_governance_service

@app.route('/scholarships/<int:scholarship_id>/apply', methods=['POST'])
@login_required
def apply_scholarship(scholarship_id):
    # Create application
    application = ScholarshipApplication(
        user_id=current_user.id,
        scholarship_id=scholarship_id,
        essay_text=request.form['essay'],
        ai_match_score=0.85
    )
    db.session.add(application)
    db.session.commit()
    
    # Track lineage
    service = get_data_governance_service()
    service.track_lineage(
        entity_type='ScholarshipApplication',
        entity_id=application.id,
        source_type='User',
        source_id=current_user.id,
        transformation='ai_matching_v2',
        metadata={
            'match_score': 0.85,
            'algorithm_version': '2.1.0',
            'timestamp': datetime.utcnow().isoformat()
        }
    )
    
    return redirect('/scholarships/applications')
```

### Monitor ML Bias

```python
from services.data_governance_service import get_data_governance_service
from services.ai_service import get_ai_service

def evaluate_model_fairness():
    """Run after training ML model"""
    ai_service = get_ai_service()
    governance = get_data_governance_service()
    
    # Get predictions for different demographic groups
    groups = ['majority', 'underrepresented_minority', 'international']
    
    for group in groups:
        # Get test data for this group
        users = User.query.filter_by(demographic_group=group).all()
        
        # Calculate confusion matrix
        tp = fp = tn = fn = 0
        for user in users:
            prediction = ai_service.predict_user_success(user.id)
            actual = user.graduated  # Ground truth
            
            if prediction and actual:
                tp += 1
            elif prediction and not actual:
                fp += 1
            elif not prediction and not actual:
                tn += 1
            else:
                fn += 1
        
        # Report metrics
        result = governance.detect_bias(
            model_name='student_success_predictor',
            prediction_type='graduation',
            demographic_group=group,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn
        )
        
        print(f"{group}: {result['metrics']}")
    
    # Check fairness
    comparison = governance.compare_bias_across_groups('student_success_predictor')
    if comparison['fairness_assessment'] == 'potential_bias_detected':
        # Alert admins
        send_admin_alert('ML Bias Detected', comparison)
```

### Implement Retention Policies

```python
from services.data_governance_service import get_data_governance_service

def setup_retention_policies():
    """Call during app initialization"""
    service = get_data_governance_service()
    
    # Set policies
    policies = [
        ('PageView', 90, 'hard', 'Analytics retention'),
        ('ApiUsage', 90, 'hard', 'API log retention'),
        ('AuditLog', 2555, 'soft', 'FERPA - 7 years'),  # 7 years
        ('EventLog', 365, 'hard', 'System log retention'),
    ]
    
    for entity_type, days, method, basis in policies:
        service.set_retention_policy(
            entity_type=entity_type,
            retention_days=days,
            deletion_method=method,
            legal_basis=basis
        )
```

### Data Quality Checks

```python
from services.data_governance_service import get_data_governance_service

@app.cli.command('check-data-quality')
def check_data_quality_cli():
    """CLI command: flask check-data-quality"""
    service = get_data_governance_service()
    
    entity_types = ['User', 'Scholarship', 'Event', 'Job']
    
    for entity_type in entity_types:
        result = service.check_data_quality(entity_type)
        
        print(f"\n{entity_type} Quality Check:")
        print(f"Overall Status: {result['overall_status']}")
        
        for check in result['checks']:
            status_icon = '✅' if check['status'] == 'pass' else '❌'
            print(f"  {status_icon} {check['check']}: {check['count']} issues")
```

---

## Notification Hub

### Send Notifications

```python
from services.notification_hub_service import get_notification_hub_service

@app.route('/scholarships/<int:scholarship_id>/apply', methods=['POST'])
@login_required
def apply_scholarship(scholarship_id):
    # Create application
    application = ScholarshipApplication(...)
    db.session.add(application)
    db.session.commit()
    
    # Send confirmation notification
    service = get_notification_hub_service()
    service.send(
        user_id=current_user.id,
        notification_type='application_submitted',
        title='Application Submitted',
        message=f'Your application for {scholarship.title} has been received',
        data={'scholarship_id': scholarship_id},
        link=f'/scholarships/{scholarship_id}'
    )
    
    return jsonify({'success': True})
```

### Bulk Notifications

```python
from services.notification_hub_service import get_notification_hub_service

def notify_scholarship_deadline(scholarship_id):
    """Send deadline reminder to all eligible students"""
    service = get_notification_hub_service()
    scholarship = Scholarship.query.get(scholarship_id)
    
    # Get eligible students who haven't applied
    eligible_users = User.query.filter_by(role='student').all()
    applied_ids = [app.user_id for app in scholarship.applications]
    
    eligible_ids = [u.id for u in eligible_users if u.id not in applied_ids]
    
    # Send bulk notification
    result = service.send_bulk(
        user_ids=eligible_ids,
        notification_type='scholarship_deadline',
        title='Scholarship Deadline Approaching',
        message=f'{scholarship.title} is due in 3 days!',
        data={'scholarship_id': scholarship_id},
        link=f'/scholarships/{scholarship_id}'
    )
    
    print(f"Sent {result['successful']}/{result['total']} notifications")
```

### Role-Based Notifications

```python
from services.notification_hub_service import get_notification_hub_service

@app.route('/admin/announcements', methods=['POST'])
@admin_required
def create_announcement():
    """Admin creates announcement for specific role"""
    service = get_notification_hub_service()
    
    # Send to all students
    result = service.send_to_role(
        role='student',
        notification_type='announcement',
        title=request.form['title'],
        message=request.form['message'],
        link=request.form.get('link')
    )
    
    flash(f"Announcement sent to {result['successful']} students")
    return redirect('/admin/announcements')
```

### Department Notifications

```python
from services.notification_hub_service import get_notification_hub_service

def notify_department_event(department_id, event_id):
    """Notify all users in a department about new event"""
    service = get_notification_hub_service()
    event = Event.query.get(event_id)
    
    result = service.send_to_department(
        department_id=department_id,
        notification_type='new_event',
        title='New Department Event',
        message=f'{event.title} - {event.start_time.strftime("%b %d")}',
        data={'event_id': event_id},
        link=f'/events/{event_id}'
    )
    
    return result
```

### Smart Notification Routing

The system automatically routes notifications through appropriate channels:

```python
# This notification will automatically go through:
# - In-app notification
# - Email
# - SMS (if user has phone)
# - Push notification (if user has device tokens)

service.send(
    user_id=user_id,
    notification_type='scholarship_deadline',  # Critical type
    title='Urgent: Scholarship Deadline',
    message='Application due tomorrow!'
)

# This will only go through in-app and push:
service.send(
    user_id=user_id,
    notification_type='new_post',  # Low priority type
    title='New Post',
    message='Someone you follow posted'
)
```

### Check User Preferences

```python
from services.notification_hub_service import get_notification_hub_service

@app.route('/profile/notifications')
@login_required
def notification_settings():
    service = get_notification_hub_service()
    
    # Get current preferences
    preferences = service.get_preferences(current_user.id)
    
    return render_template(
        'profile/notification_settings.html',
        preferences=preferences
    )
```

---

## Integration Patterns

### Pattern 1: Feature Flag + Notification

```python
@app.route('/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    ff_service = get_feature_flag_service()
    notif_service = get_notification_hub_service()
    
    # Check if AI assistant is enabled
    if not ff_service.is_enabled('ai_assistant', current_user.id):
        return jsonify({'error': 'Feature not available'}), 403
    
    # Process AI chat
    ai_service = get_ai_service()
    response = ai_service.chat(
        user_id=current_user.id,
        message=request.json['message']
    )
    
    # Track usage for A/B test
    variant = ff_service.get_ab_variant(test_id=2, user_id=current_user.id)
    
    # Send notification if AI provides important info
    if response.get('confidence', 0) > 0.9:
        notif_service.send(
            user_id=current_user.id,
            notification_type='ai_insight',
            title='Important AI Insight',
            message=response['summary']
        )
    
    return jsonify(response)
```

### Pattern 2: Data Governance + Analytics

```python
from services.data_governance_service import get_data_governance_service
from services.analytics_service import get_analytics_service

@app.route('/admin/fairness-report')
@admin_required
def fairness_report():
    governance = get_data_governance_service()
    analytics = get_analytics_service()
    
    # Check bias across all models
    models = ['scholarship_predictor', 'churn_predictor', 'success_predictor']
    
    fairness_data = {}
    for model in models:
        comparison = governance.compare_bias_across_groups(model)
        fairness_data[model] = {
            'status': comparison['fairness_assessment'],
            'details': comparison['disparate_impact']
        }
    
    # Generate dashboard
    dashboard = analytics.get_admin_dashboard(days=30)
    
    return render_template(
        'admin/fairness_report.html',
        fairness=fairness_data,
        dashboard=dashboard
    )
```

### Pattern 3: All Three Services Together

```python
@app.route('/scholarships/recommend', methods=['POST'])
@login_required
def recommend_scholarships():
    """Smart scholarship recommendation with all safeguards"""
    ff_service = get_feature_flag_service()
    governance = get_data_governance_service()
    notif_service = get_notification_hub_service()
    ai_service = get_ai_service()
    
    # 1. Check if feature is enabled
    if not ff_service.is_enabled('smart_matching', current_user.id):
        # Fallback to basic matching
        scholarships = Scholarship.query.filter_by(major=current_user.major).all()
        return jsonify({'scholarships': [s.to_dict() for s in scholarships]})
    
    # 2. Get AI recommendations
    recommendations = ai_service.smart_match_scholarships(
        user_profile={
            'gpa': current_user.gpa,
            'major': current_user.major,
            'interests': current_user.interests
        },
        scholarships=Scholarship.query.filter_by(active=True).all()
    )
    
    # 3. Track lineage for each recommendation
    for rec in recommendations:
        governance.track_lineage(
            entity_type='ScholarshipRecommendation',
            entity_id=rec['scholarship_id'],
            source_type='User',
            source_id=current_user.id,
            transformation='ai_smart_match_v3',
            metadata={
                'match_score': rec['match_score'],
                'model_version': '3.2.1'
            }
        )
    
    # 4. Check if we should notify about top matches
    top_matches = [r for r in recommendations if r['match_score'] > 0.9]
    if top_matches:
        notif_service.send(
            user_id=current_user.id,
            notification_type='scholarship_matched',
            title='High-Match Scholarships Found!',
            message=f'We found {len(top_matches)} scholarships that match your profile',
            data={'count': len(top_matches)},
            link='/scholarships/matches'
        )
    
    return jsonify({'recommendations': recommendations})
```

---

## Best Practices

### 1. Always Check Feature Flags for New Features

```python
# ❌ BAD: Directly show feature
@app.route('/new-feature')
def new_feature():
    return render_template('new_feature.html')

# ✅ GOOD: Check feature flag
@app.route('/new-feature')
@login_required
def new_feature():
    if not get_feature_flag_service().is_enabled('new_feature', current_user.id):
        abort(404)
    return render_template('new_feature.html')
```

### 2. Track Data Transformations

```python
# ❌ BAD: No lineage tracking
def process_data(user_data):
    result = ml_model.predict(user_data)
    return result

# ✅ GOOD: Track lineage
def process_data(user_id, user_data):
    result = ml_model.predict(user_data)
    
    get_data_governance_service().track_lineage(
        entity_type='Prediction',
        entity_id=result.id,
        source_type='User',
        source_id=user_id,
        transformation='ml_model_v2',
        metadata={'confidence': result.confidence}
    )
    
    return result
```

### 3. Respect User Notification Preferences

```python
# ❌ BAD: Force email notification
send_email(user.email, subject, body)

# ✅ GOOD: Use notification hub
get_notification_hub_service().send(
    user_id=user.id,
    notification_type='announcement',
    title=subject,
    message=body
)
# System automatically checks user preferences and routes accordingly
```

### 4. Monitor Bias Regularly

```python
# Set up weekly bias check
@app.cli.command('check-bias')
def check_bias_cli():
    """flask check-bias"""
    governance = get_data_governance_service()
    
    for model in ['scholarship_predictor', 'churn_predictor']:
        comparison = governance.compare_bias_across_groups(model)
        
        if comparison['fairness_assessment'] != 'fair':
            # Alert admins
            send_admin_alert(
                f'Bias Detected in {model}',
                comparison
            )
```

---

## Testing

### Testing with Feature Flags

```python
def test_scholarship_page_v2():
    # Enable feature for test
    service = get_feature_flag_service()
    service.create_flag(
        name='scholarships_v2',
        description='Test flag',
        enabled=True,
        rollout_percentage=100.0
    )
    
    # Test
    response = client.get('/scholarships')
    assert b'Version 2' in response.data
    
    # Cleanup
    service.delete_flag('scholarships_v2')
```

### Testing Notifications

```python
def test_scholarship_application_notification():
    # Apply to scholarship
    response = client.post('/scholarships/1/apply', data={
        'essay': 'Test essay'
    })
    
    # Check notification was created
    service = get_notification_hub_service()
    notifications = service.get_user_notifications(user_id=1)
    
    assert len(notifications) > 0
    assert notifications[0]['category'] == 'application_submitted'
```

---

*Happy coding! 🦍*
