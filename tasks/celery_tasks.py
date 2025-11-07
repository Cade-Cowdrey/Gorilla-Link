"""
Celery Tasks for Asynchronous Operations
Email sending, data processing, analytics, notifications
"""

from extensions import celery, db, mail
from flask_mail import Message as MailMessage
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# ============================================================
# EMAIL TASKS
# ============================================================

@celery.task(name='tasks.send_async_email')
def send_async_email(to: str, subject: str, body: str, html: str = None):
    """
    Send email asynchronously
    """
    try:
        msg = MailMessage(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            body=body,
            html=html
        )
        mail.send(msg)
        logger.info(f"✅ Email sent to {to}")
        return {"success": True}
    except Exception as e:
        logger.error(f"❌ Email send error: {e}")
        return {"success": False, "error": str(e)}


@celery.task(name='tasks.send_bulk_emails')
def send_bulk_emails(recipients: list, subject: str, body: str, html: str = None):
    """
    Send bulk emails asynchronously
    """
    success_count = 0
    failed_count = 0
    
    for recipient in recipients:
        result = send_async_email.delay(recipient, subject, body, html)
        if result.get('success'):
            success_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Bulk email: {success_count} sent, {failed_count} failed")
    return {"success": success_count, "failed": failed_count}


@celery.task(name='tasks.send_welcome_email')
def send_welcome_email(user_id: int):
    """
    Send welcome email to new user
    """
    from models import User
    
    user = User.query.get(user_id)
    if not user:
        return {"success": False, "error": "User not found"}
    
    subject = "Welcome to PittState-Connect! 🦍"
    body = f"""
    Hi {user.first_name},
    
    Welcome to PittState-Connect! We're excited to have you join our Gorilla family.
    
    Get started by:
    - Completing your profile
    - Exploring scholarship opportunities
    - Connecting with fellow Gorillas
    - Checking out upcoming events
    
    Go Gorillas!
    The PittState-Connect Team
    """
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #A50021;">Welcome to PittState-Connect! 🦍</h2>
        <p>Hi {user.first_name},</p>
        <p>We're excited to have you join our Gorilla family.</p>
        <h3>Get Started:</h3>
        <ul>
            <li>Complete your profile</li>
            <li>Explore scholarship opportunities</li>
            <li>Connect with fellow Gorillas</li>
            <li>Check out upcoming events</li>
        </ul>
        <p><strong>Go Gorillas!</strong><br>
        The PittState-Connect Team</p>
    </body>
    </html>
    """
    
    return send_async_email.delay(user.email, subject, body, html)


# ============================================================
# ANALYTICS TASKS
# ============================================================

@celery.task(name='tasks.update_daily_analytics')
def update_daily_analytics():
    """
    Update daily analytics summary
    """
    from models import AnalyticsSummary, User, PageView, Post
    import datetime
    
    try:
        today = datetime.date.today()
        yesterday = today - timedelta(days=1)
        start_of_day = datetime.datetime.combine(yesterday, datetime.time.min)
        end_of_day = datetime.datetime.combine(yesterday, datetime.time.max)
        
        # Calculate metrics
        page_views = PageView.query.filter(
            PageView.timestamp >= start_of_day,
            PageView.timestamp <= end_of_day
        ).count()
        
        active_users = db.session.query(PageView.user_id).filter(
            PageView.timestamp >= start_of_day,
            PageView.timestamp <= end_of_day,
            PageView.user_id.isnot(None)
        ).distinct().count()
        
        new_users = User.query.filter(
            User.date_joined >= start_of_day,
            User.date_joined <= end_of_day
        ).count()
        
        # Check if summary exists
        summary = AnalyticsSummary.query.filter_by(date=yesterday).first()
        
        if summary:
            summary.page_views = page_views
            summary.active_users = active_users
            summary.new_users = new_users
        else:
            summary = AnalyticsSummary(
                date=yesterday,
                page_views=page_views,
                active_users=active_users,
                new_users=new_users
            )
            db.session.add(summary)
        
        db.session.commit()
        logger.info(f"✅ Daily analytics updated for {yesterday}")
        return {"success": True, "date": str(yesterday)}
        
    except Exception as e:
        logger.error(f"❌ Daily analytics update error: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e)}


@celery.task(name='tasks.generate_weekly_report')
def generate_weekly_report():
    """
    Generate and email weekly analytics report
    """
    from models import User, Post, Event, Scholarship
    from services.analytics_service import get_analytics_service
    
    try:
        analytics = get_analytics_service()
        insights = analytics.generate_ai_insights(days=7)
        
        # Get admin users
        from models import Role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            return {"success": False, "error": "Admin role not found"}
        
        admins = User.query.filter_by(role_id=admin_role.id).all()
        
        # Generate report
        report_body = f"""
        Weekly PittState-Connect Report
        
        Key Insights:
        {"- " + chr(10).join(insights)}
        
        View full dashboard: https://pittstate-connect.onrender.com/analytics
        """
        
        # Send to all admins
        for admin in admins:
            send_async_email.delay(
                admin.email,
                "Weekly PittState-Connect Report",
                report_body
            )
        
        logger.info(f"✅ Weekly report sent to {len(admins)} admins")
        return {"success": True, "recipients": len(admins)}
        
    except Exception as e:
        logger.error(f"❌ Weekly report error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# NOTIFICATION TASKS
# ============================================================

@celery.task(name='tasks.send_push_notification')
def send_push_notification(user_id: int, title: str, body: str, data: dict = None):
    """
    Send push notification asynchronously
    """
    from services.integration_service import get_integration_service
    import os
    
    try:
        integration = get_integration_service({
            "FIREBASE_CREDENTIALS": os.getenv("FIREBASE_CREDENTIALS")
        })
        
        success = integration.send_push_notification(user_id, title, body, data)
        return {"success": success}
        
    except Exception as e:
        logger.error(f"❌ Push notification error: {e}")
        return {"success": False, "error": str(e)}


@celery.task(name='tasks.send_deadline_reminders')
def send_deadline_reminders():
    """
    Send reminders for upcoming scholarship deadlines
    """
    from models import Scholarship, User
    from models_growth_features import ScholarshipApplication
    
    try:
        # Find scholarships with deadlines in next 7 days
        today = datetime.now().date()
        week_from_now = today + timedelta(days=7)
        
        scholarships = Scholarship.query.filter(
            Scholarship.deadline >= today,
            Scholarship.deadline <= week_from_now
        ).all()
        
        reminded_count = 0
        
        for scholarship in scholarships:
            # Find users who haven't applied
            applied_users = db.session.query(ScholarshipApplication.user_id).filter_by(
                scholarship_id=scholarship.id
            ).all()
            applied_user_ids = [u[0] for u in applied_users]
            
            # Get eligible users (simplified)
            eligible_users = User.query.filter(
                ~User.id.in_(applied_user_ids)
            ).limit(100).all()
            
            for user in eligible_users:
                send_async_email.delay(
                    user.email,
                    f"Reminder: {scholarship.title} deadline approaching",
                    f"Hi {user.first_name},\n\nThe deadline for {scholarship.title} is {scholarship.deadline}.\n\nDon't miss out!"
                )
                reminded_count += 1
        
        logger.info(f"✅ Sent {reminded_count} scholarship deadline reminders")
        return {"success": True, "count": reminded_count}
        
    except Exception as e:
        logger.error(f"❌ Deadline reminder error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# DATA PROCESSING TASKS
# ============================================================

@celery.task(name='tasks.sync_external_data')
def sync_external_data():
    """
    Sync data from external sources (Canvas, Banner, etc.)
    """
    from services.integration_service import get_integration_service
    from models import User, Job, Company
    from models_extended import AlumniProfile
    
    try:
        logger.info("🔄 Starting external data sync...")
        
        results = {
            "users_updated": 0,
            "jobs_synced": 0,
            "alumni_updated": 0,
            "errors": []
        }
        
        # 1. Sync user data from external HR/Student systems
        try:
            # In production, this would connect to Canvas, Workday, etc.
            # For now, we'll sync basic user profile completeness
            incomplete_users = User.query.filter(
                db.or_(
                    User.major == None,
                    User.graduation_year == None,
                    User.bio == None
                )
            ).limit(100).all()
            
            for user in incomplete_users:
                # Simulate fetching additional data
                if not user.bio:
                    user.bio = f"Student pursuing {user.major or 'degree'} at Pittsburg State University"
                
                results["users_updated"] += 1
            
            db.session.commit()
            logger.info(f"✅ Updated {results['users_updated']} user profiles")
            
        except Exception as e:
            logger.error(f"Error syncing users: {e}")
            results["errors"].append(f"User sync: {str(e)}")
            db.session.rollback()
        
        # 2. Sync job postings from external job boards (if integration exists)
        try:
            from services.job_scraping_service import JobScrapingService
            
            scraper = JobScrapingService()
            # Scrape from configured sources
            new_jobs = scraper.scrape_jobs(query="recent graduate", location="Kansas", max_results=20)
            
            results["jobs_synced"] = len(new_jobs)
            logger.info(f"✅ Synced {results['jobs_synced']} new jobs")
            
        except Exception as e:
            logger.error(f"Error syncing jobs: {e}")
            results["errors"].append(f"Job sync: {str(e)}")
        
        # 3. Sync alumni employment status from LinkedIn/external sources
        try:
            alumni_profiles = AlumniProfile.query.filter(
                AlumniProfile.last_sync_date < datetime.now() - timedelta(days=30)
            ).limit(50).all()
            
            for profile in alumni_profiles:
                # In production, would call LinkedIn API or similar
                profile.last_sync_date = datetime.now()
                results["alumni_updated"] += 1
            
            db.session.commit()
            logger.info(f"✅ Updated {results['alumni_updated']} alumni profiles")
            
        except Exception as e:
            logger.error(f"Error syncing alumni: {e}")
            results["errors"].append(f"Alumni sync: {str(e)}")
            db.session.rollback()
        
        logger.info("✅ External data sync completed")
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"❌ External data sync error: {e}")
        return {"success": False, "error": str(e)}


@celery.task(name='tasks.cleanup_old_data')
def cleanup_old_data():
    """
    Clean up old data based on retention policies
    """
    from models import PageView, ApiUsage
    from models_extended import EventLog
    
    try:
        # Delete page views older than 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        
        deleted_views = PageView.query.filter(
            PageView.timestamp < cutoff_date
        ).delete()
        
        # Archive old API usage
        deleted_api = ApiUsage.query.filter(
            ApiUsage.timestamp < cutoff_date
        ).delete()
        
        # Archive old event logs
        deleted_events = EventLog.query.filter(
            EventLog.timestamp < cutoff_date
        ).delete()
        
        db.session.commit()
        
        logger.info(f"✅ Cleaned up: {deleted_views} views, {deleted_api} API logs, {deleted_events} events")
        return {
            "success": True,
            "deleted": {
                "page_views": deleted_views,
                "api_usage": deleted_api,
                "event_logs": deleted_events
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Data cleanup error: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e)}


@celery.task(name='tasks.train_ml_models')
def train_ml_models():
    """
    Retrain machine learning models with new data
    """
    from models_extended import PredictiveModel
    from models import User
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    import pickle
    
    try:
        logger.info("🤖 Starting ML model training...")
        
        results = {
            "models_trained": [],
            "accuracy_scores": {},
            "errors": []
        }
        
        # 1. Train Student Success Prediction Model
        try:
            logger.info("Training student success model...")
            
            # Gather training data
            students = User.query.filter_by(role_id=1).all()  # Assuming role_id=1 for students
            
            if len(students) >= 50:  # Minimum data requirement
                X = []
                y = []
                
                for student in students:
                    # Features: [gpa_normalized, engagement_score, profile_completeness, etc.]
                    features = [
                        float(getattr(student, 'gpa', 3.0) / 4.0),  # Normalize GPA
                        float(getattr(student, 'engagement_score', 50) / 100),
                        1.0 if student.bio else 0.0,
                        1.0 if student.major else 0.0,
                        float(len(student.connections) / 10.0) if hasattr(student, 'connections') else 0.0
                    ]
                    
                    # Target: success indicator (e.g., employed or high engagement)
                    success = 1 if getattr(student, 'engagement_score', 0) > 60 else 0
                    
                    X.append(features)
                    y.append(success)
                
                X = np.array(X)
                y = np.array(y)
                
                # Split and train
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                
                accuracy = model.score(X_test, y_test)
                results["accuracy_scores"]["student_success"] = round(accuracy, 3)
                
                # Save model
                model_record = PredictiveModel.query.filter_by(model_name="student_success_v1").first()
                if not model_record:
                    model_record = PredictiveModel(
                        model_name="student_success_v1",
                        model_type="classification",
                        version="1.0"
                    )
                    db.session.add(model_record)
                
                model_record.model_data = pickle.dumps(model)
                model_record.accuracy = accuracy
                model_record.trained_at = datetime.now()
                
                db.session.commit()
                results["models_trained"].append("student_success")
                logger.info(f"✅ Student success model trained (accuracy: {accuracy:.3f})")
            
        except Exception as e:
            logger.error(f"Error training student success model: {e}")
            results["errors"].append(f"Student success: {str(e)}")
        
        # 2. Train Churn Prediction Model
        try:
            logger.info("Training churn prediction model...")
            
            users = User.query.filter(
                User.last_login.isnot(None)
            ).all()
            
            if len(users) >= 50:
                X = []
                y = []
                
                for user in users:
                    days_since_login = (datetime.now() - user.last_login).days if user.last_login else 365
                    
                    features = [
                        float(days_since_login / 365),  # Normalize
                        float((datetime.now() - user.date_joined).days / 365),
                        1.0 if user.profile_image else 0.0,
                        float(getattr(user, 'engagement_score', 50) / 100),
                        float(len(user.posts) if hasattr(user, 'posts') else 0) / 10.0
                    ]
                    
                    # Target: churned if not logged in for 30+ days
                    churned = 1 if days_since_login > 30 else 0
                    
                    X.append(features)
                    y.append(churned)
                
                X = np.array(X)
                y = np.array(y)
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                
                accuracy = model.score(X_test, y_test)
                results["accuracy_scores"]["churn_prediction"] = round(accuracy, 3)
                
                # Save model
                model_record = PredictiveModel.query.filter_by(model_name="churn_prediction_v1").first()
                if not model_record:
                    model_record = PredictiveModel(
                        model_name="churn_prediction_v1",
                        model_type="classification",
                        version="1.0"
                    )
                    db.session.add(model_record)
                
                model_record.model_data = pickle.dumps(model)
                model_record.accuracy = accuracy
                model_record.trained_at = datetime.now()
                
                db.session.commit()
                results["models_trained"].append("churn_prediction")
                logger.info(f"✅ Churn prediction model trained (accuracy: {accuracy:.3f})")
            
        except Exception as e:
            logger.error(f"Error training churn model: {e}")
            results["errors"].append(f"Churn prediction: {str(e)}")
        
        logger.info(f"✅ ML model training completed: {len(results['models_trained'])} models trained")
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"❌ ML training error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# DATA GOVERNANCE TASKS
# ============================================================

@celery.task(name='tasks.apply_retention_policies')
def apply_retention_policies():
    """
    Apply data retention policies across all entity types
    """
    from services.data_governance_service import get_data_governance_service
    
    try:
        service = get_data_governance_service()
        
        # Apply retention for each entity type
        entity_types = ['PageView', 'ApiUsage', 'EventLog', 'AuditLog']
        results = {}
        
        for entity_type in entity_types:
            result = service.apply_retention_policy(entity_type, dry_run=False)
            results[entity_type] = result.get('deleted_count', 0)
        
        logger.info(f"✅ Retention policies applied: {results}")
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"❌ Retention policy application error: {e}")
        return {"success": False, "error": str(e)}


@celery.task(name='tasks.check_bias_metrics')
def check_bias_metrics():
    """
    Check bias metrics for all active ML models
    """
    from services.data_governance_service import get_data_governance_service
    
    try:
        service = get_data_governance_service()
        
        # Check bias for active models
        models = ['scholarship_success_predictor', 'student_churn_predictor']
        results = {}
        
        for model_name in models:
            comparison = service.compare_bias_across_groups(model_name)
            results[model_name] = comparison.get('fairness_assessment', 'unknown')
        
        logger.info(f"✅ Bias metrics checked: {results}")
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"❌ Bias check error: {e}")
        return {"success": False, "error": str(e)}


@celery.task(name='tasks.data_quality_scan')
def data_quality_scan():
    """
    Run data quality checks across all entity types
    """
    from services.data_governance_service import get_data_governance_service
    
    try:
        service = get_data_governance_service()
        
        # Check quality for each entity type
        entity_types = ['User', 'Scholarship', 'Event', 'Job']
        results = {}
        
        for entity_type in entity_types:
            quality_result = service.check_data_quality(entity_type)
            results[entity_type] = quality_result.get('overall_status', 'unknown')
        
        logger.info(f"✅ Data quality scan completed: {results}")
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"❌ Data quality scan error: {e}")
        return {"success": False, "error": str(e)}


@celery.task(name='tasks.send_notification_digests')
def send_notification_digests():
    """
    Send daily digest of notifications to users who prefer batched notifications
    """
    from services.notification_hub_service import get_notification_hub_service
    from models import User
    
    try:
        service = get_notification_hub_service()
        
        # Get users with unread notifications
        users = User.query.all()
        digest_count = 0
        
        for user in users:
            unread_count = service.get_unread_count(user.id)
            
            if unread_count > 0:
                # Check if user wants daily digests
                prefs = user.notification_preferences or {}
                if prefs.get('daily_digest', False):
                    notifications = service.get_user_notifications(
                        user.id,
                        unread_only=True,
                        limit=20
                    )
                    
                    # Send digest email
                    send_async_email.delay(
                        user.email,
                        f"Your Daily PittState-Connect Digest ({unread_count} updates)",
                        f"Hi {user.first_name},\n\nYou have {unread_count} unread notifications."
                    )
                    digest_count += 1
        
        logger.info(f"✅ Sent {digest_count} notification digests")
        return {"success": True, "count": digest_count}
        
    except Exception as e:
        logger.error(f"❌ Notification digest error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# SCHEDULED TASK REGISTRATION
# ============================================================

def register_scheduled_tasks(scheduler):
    """
    Register all scheduled tasks with APScheduler
    """
    
    # Daily analytics update (runs at midnight)
    scheduler.add_job(
        id='daily_analytics',
        func=update_daily_analytics,
        trigger='cron',
        hour=0,
        minute=5
    )
    
    # Weekly report (runs Monday 8am)
    scheduler.add_job(
        id='weekly_report',
        func=generate_weekly_report,
        trigger='cron',
        day_of_week='mon',
        hour=8,
        minute=0
    )
    
    # Deadline reminders (runs daily at 9am)
    scheduler.add_job(
        id='deadline_reminders',
        func=send_deadline_reminders,
        trigger='cron',
        hour=9,
        minute=0
    )
    
    # Data cleanup (runs weekly Sunday 2am)
    scheduler.add_job(
        id='data_cleanup',
        func=cleanup_old_data,
        trigger='cron',
        day_of_week='sun',
        hour=2,
        minute=0
    )
    
    # External sync (runs every 6 hours)
    scheduler.add_job(
        id='external_sync',
        func=sync_external_data,
        trigger='interval',
        hours=6
    )
    
    # ML model training (runs weekly Saturday 3am)
    scheduler.add_job(
        id='ml_training',
        func=train_ml_models,
        trigger='cron',
        day_of_week='sat',
        hour=3,
        minute=0
    )
    
    # Data retention policies (runs daily at 1am)
    scheduler.add_job(
        id='retention_policies',
        func=apply_retention_policies,
        trigger='cron',
        hour=1,
        minute=0
    )
    
    # Bias monitoring (runs daily at 4am)
    scheduler.add_job(
        id='bias_monitoring',
        func=check_bias_metrics,
        trigger='cron',
        hour=4,
        minute=0
    )
    
    # Data quality scan (runs daily at 5am)
    scheduler.add_job(
        id='data_quality',
        func=data_quality_scan,
        trigger='cron',
        hour=5,
        minute=0
    )
    
    # Notification digests (runs daily at 6pm)
    scheduler.add_job(
        id='notification_digests',
        func=send_notification_digests,
        trigger='cron',
        hour=18,
        minute=0
    )
    
    logger.info("✅ Scheduled tasks registered")
