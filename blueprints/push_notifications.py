"""
PSU Connect - Push Notifications System
Web push notifications for job matches, messages, achievements
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import PushSubscription, NotificationPreference
from pywebpush import webpush, WebPushException
import json
import os

push_bp = Blueprint('push', __name__, url_prefix='/push')

# VAPID keys for web push (generate with: vapid.py --gen)
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', 'YOUR_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', 'YOUR_PRIVATE_KEY')
VAPID_CLAIMS = {"sub": "mailto:support@psuconnect.com"}


@push_bp.route('/vapid-public-key')
def get_vapid_public_key():
    """Get VAPID public key for browser subscription"""
    return jsonify({'publicKey': VAPID_PUBLIC_KEY})


@push_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Subscribe to push notifications"""
    data = request.json
    
    subscription = PushSubscription(
        user_id=current_user.id,
        endpoint=data['endpoint'],
        p256dh_key=data['keys']['p256dh'],
        auth_key=data['keys']['auth'],
        user_agent=request.user_agent.string[:512],
        is_active=True
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({'success': True, 'subscription_id': subscription.id})


@push_bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Unsubscribe from push notifications"""
    data = request.json
    endpoint = data.get('endpoint')
    
    if endpoint:
        PushSubscription.query.filter_by(
            user_id=current_user.id,
            endpoint=endpoint
        ).delete()
    else:
        # Unsubscribe all
        PushSubscription.query.filter_by(
            user_id=current_user.id
        ).delete()
    
    db.session.commit()
    
    return jsonify({'success': True})


@push_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def notification_preferences():
    """Get/update notification preferences"""
    prefs = NotificationPreference.query.filter_by(
        user_id=current_user.id
    ).first()
    
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.session.add(prefs)
        db.session.commit()
    
    if request.method == 'POST':
        data = request.json
        
        # Update preferences
        prefs.job_matches = data.get('job_matches', True)
        prefs.new_messages = data.get('new_messages', True)
        prefs.application_updates = data.get('application_updates', True)
        prefs.connection_requests = data.get('connection_requests', True)
        prefs.forum_replies = data.get('forum_replies', True)
        prefs.achievement_unlocked = data.get('achievement_unlocked', True)
        prefs.event_reminders = data.get('event_reminders', True)
        prefs.weekly_digest = data.get('weekly_digest', True)
        
        db.session.commit()
        
        return jsonify({'success': True})
    
    # GET - return current preferences
    return jsonify({
        'job_matches': prefs.job_matches,
        'new_messages': prefs.new_messages,
        'application_updates': prefs.application_updates,
        'connection_requests': prefs.connection_requests,
        'forum_replies': prefs.forum_replies,
        'achievement_unlocked': prefs.achievement_unlocked,
        'event_reminders': prefs.event_reminders,
        'weekly_digest': prefs.weekly_digest
    })


def send_push_notification(user_id, title, body, data=None, icon=None):
    """Send push notification to user's subscriptions"""
    # Check user preferences
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if not prefs:
        return  # No preferences = notifications disabled
    
    # Get active subscriptions
    subscriptions = PushSubscription.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()
    
    if not subscriptions:
        return  # No subscriptions
    
    # Prepare notification payload
    notification = {
        'title': title,
        'body': body,
        'icon': icon or '/static/img/psu-logo.png',
        'badge': '/static/img/psu-badge.png',
        'data': data or {},
        'requireInteraction': False
    }
    
    # Send to all subscriptions
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {
                        'p256dh': sub.p256dh_key,
                        'auth': sub.auth_key
                    }
                },
                data=json.dumps(notification),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            
            # Update last used
            sub.last_used = db.func.now()
            
        except WebPushException as e:
            print(f"Push notification failed: {e}")
            
            # If subscription expired/invalid, deactivate it
            if e.response and e.response.status_code in [404, 410]:
                sub.is_active = False
    
    db.session.commit()


def notify_job_match(user_id, job_title, job_company, job_id):
    """Notify user of new job match"""
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and not prefs.job_matches:
        return
    
    send_push_notification(
        user_id=user_id,
        title=f"New Job Match: {job_title}",
        body=f"{job_company} - Check it out now!",
        data={'url': f'/jobs/{job_id}', 'type': 'job_match'},
        icon='/static/img/icons/briefcase.png'
    )


def notify_new_message(user_id, sender_name, message_preview):
    """Notify user of new message"""
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and not prefs.new_messages:
        return
    
    send_push_notification(
        user_id=user_id,
        title=f"Message from {sender_name}",
        body=message_preview[:100],
        data={'url': '/messages', 'type': 'new_message'},
        icon='/static/img/icons/message.png'
    )


def notify_application_update(user_id, job_title, status):
    """Notify user of application status update"""
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and not prefs.application_updates:
        return
    
    status_text = {
        'viewed': 'Your application was viewed',
        'interview': 'Interview request',
        'offer': 'Job offer received',
        'rejected': 'Application status updated'
    }.get(status, 'Application updated')
    
    send_push_notification(
        user_id=user_id,
        title=f"{job_title}",
        body=status_text,
        data={'url': '/applications', 'type': 'application_update'},
        icon='/static/img/icons/document.png'
    )


def notify_achievement_unlocked(user_id, badge_name, badge_description):
    """Notify user of achievement/badge earned"""
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and not prefs.achievement_unlocked:
        return
    
    send_push_notification(
        user_id=user_id,
        title=f"🏆 Achievement Unlocked: {badge_name}",
        body=badge_description,
        data={'url': '/gamification/badges', 'type': 'achievement'},
        icon='/static/img/icons/trophy.png'
    )


def notify_connection_request(user_id, requester_name):
    """Notify user of new connection request"""
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and not prefs.connection_requests:
        return
    
    send_push_notification(
        user_id=user_id,
        title="New Connection Request",
        body=f"{requester_name} wants to connect",
        data={'url': '/connections', 'type': 'connection_request'},
        icon='/static/img/icons/users.png'
    )


def notify_forum_reply(user_id, topic_title, replier_name):
    """Notify user of reply to their forum post"""
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and not prefs.forum_replies:
        return
    
    send_push_notification(
        user_id=user_id,
        title="New Reply",
        body=f"{replier_name} replied to: {topic_title[:50]}",
        data={'url': '/forums', 'type': 'forum_reply'},
        icon='/static/img/icons/comment.png'
    )


def notify_event_reminder(user_id, event_name, start_time):
    """Notify user of upcoming event"""
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and not prefs.event_reminders:
        return
    
    send_push_notification(
        user_id=user_id,
        title=f"Event Starting Soon: {event_name}",
        body=f"Starts at {start_time.strftime('%I:%M %p')}",
        data={'url': '/events', 'type': 'event_reminder'},
        icon='/static/img/icons/calendar.png'
    )


@push_bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """Send test notification"""
    send_push_notification(
        user_id=current_user.id,
        title="Test Notification",
        body="Push notifications are working! 🎉",
        data={'url': '/', 'type': 'test'}
    )
    
    return jsonify({'success': True})
