"""
PSU Connect - Live Events System
Virtual career fairs, webinars, and live Q&A sessions
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User
from models_growth_features import LiveEvent, EventAttendee, EventMessage
from datetime import datetime, timedelta
from sqlalchemy import desc, or_
import json

events_bp = Blueprint('events', __name__, url_prefix='/events')


@events_bp.route('/')
def index():
    """Events listing"""
    # Get upcoming events
    upcoming = LiveEvent.query.filter(
        LiveEvent.start_time > datetime.utcnow(),
        LiveEvent.is_public == True
    ).order_by(LiveEvent.start_time).all()
    
    # Get past events with recordings
    past = LiveEvent.query.filter(
        LiveEvent.end_time < datetime.utcnow(),
        LiveEvent.recording_url != None
    ).order_by(desc(LiveEvent.start_time)).limit(10).all()
    
    return render_template('events/index.html',
                         upcoming=upcoming,
                         past=past)


@events_bp.route('/event/<int:event_id>')
def view_event(event_id):
    """View event details"""
    event = LiveEvent.query.get_or_404(event_id)
    
    # Check if user is registered
    is_registered = False
    if current_user.is_authenticated:
        is_registered = EventAttendee.query.filter_by(
            event_id=event_id,
            user_id=current_user.id
        ).first() is not None
    
    # Get attendee count
    attendee_count = EventAttendee.query.filter_by(event_id=event_id).count()
    
    # Check if event is live
    now = datetime.utcnow()
    is_live = event.start_time <= now <= event.end_time
    
    return render_template('events/event_detail.html',
                         event=event,
                         is_registered=is_registered,
                         attendee_count=attendee_count,
                         is_live=is_live)


@events_bp.route('/event/<int:event_id>/register', methods=['POST'])
@login_required
def register(event_id):
    """Register for an event"""
    event = LiveEvent.query.get_or_404(event_id)
    
    # Check if already registered
    existing = EventAttendee.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        return jsonify({'error': 'Already registered'}), 400
    
    # Check capacity
    if event.max_attendees:
        current_count = EventAttendee.query.filter_by(event_id=event_id).count()
        if current_count >= event.max_attendees:
            return jsonify({'error': 'Event is full'}), 400
    
    # Register
    attendee = EventAttendee(
        event_id=event_id,
        user_id=current_user.id
    )
    db.session.add(attendee)
    db.session.commit()
    
    # Send confirmation notification
    from blueprints.push_notifications import notify_event_reminder
    notify_event_reminder(current_user.id, event.title, event.start_time)
    
    # Award points
    from blueprints.gamification import award_points
    award_points(current_user.id, 10, 'event_registered')
    
    return jsonify({'success': True})


@events_bp.route('/event/<int:event_id>/unregister', methods=['POST'])
@login_required
def unregister(event_id):
    """Unregister from event"""
    EventAttendee.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).delete()
    
    db.session.commit()
    
    return jsonify({'success': True})


@events_bp.route('/event/<int:event_id>/live')
@login_required
def live_event(event_id):
    """Live event room"""
    event = LiveEvent.query.get_or_404(event_id)
    
    # Check if registered
    attendee = EventAttendee.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()
    
    if not attendee:
        return redirect(url_for('events.view_event', event_id=event_id))
    
    # Mark as attended
    attendee.attended = True
    db.session.commit()
    
    # Get chat messages
    messages = EventMessage.query.filter_by(
        event_id=event_id
    ).order_by(EventMessage.created_at).all()
    
    # Get Q&A questions
    questions = EventMessage.query.filter_by(
        event_id=event_id,
        is_question=True
    ).order_by(EventMessage.created_at).all()
    
    return render_template('events/live_room.html',
                         event=event,
                         messages=messages,
                         questions=questions)


@events_bp.route('/event/<int:event_id>/chat', methods=['POST'])
@login_required
def send_chat(event_id):
    """Send chat message in live event"""
    data = request.json
    message_text = data.get('message', '').strip()
    is_question = data.get('is_question', False)
    
    if not message_text:
        return jsonify({'error': 'Message required'}), 400
    
    # Check if registered
    attendee = EventAttendee.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()
    
    if not attendee:
        return jsonify({'error': 'Must be registered'}), 403
    
    # Create message
    message = EventMessage(
        event_id=event_id,
        user_id=current_user.id,
        message=message_text,
        is_question=is_question
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message_id': message.id,
        'user_name': current_user.full_name,
        'timestamp': message.created_at.isoformat()
    })


@events_bp.route('/event/<int:event_id>/question/<int:question_id>/answer', methods=['POST'])
@login_required
def answer_question(event_id, question_id):
    """Mark question as answered (host only)"""
    event = LiveEvent.query.get_or_404(event_id)
    
    # Check if host
    if event.host_id != current_user.id:
        return jsonify({'error': 'Only host can answer questions'}), 403
    
    question = EventMessage.query.get_or_404(question_id)
    question.is_answered = True
    
    db.session.commit()
    
    return jsonify({'success': True})


@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():
    """Create new event"""
    if request.method == 'POST':
        data = request.form
        
        event = LiveEvent(
            title=data.get('title'),
            description=data.get('description'),
            event_type=data.get('event_type'),
            host_id=current_user.id,
            start_time=datetime.fromisoformat(data.get('start_time')),
            end_time=datetime.fromisoformat(data.get('end_time')),
            meeting_link=data.get('meeting_link'),
            max_attendees=data.get('max_attendees', type=int),
            is_public=data.get('is_public') == 'on'
        )
        
        db.session.add(event)
        db.session.commit()
        
        return redirect(url_for('events.view_event', event_id=event.id))
    
    return render_template('events/create.html')


@events_bp.route('/my-events')
@login_required
def my_events():
    """User's registered events"""
    registered = EventAttendee.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(EventAttendee.registered_at)).all()
    
    return render_template('events/my_events.html',
                         registered=registered)


@events_bp.route('/api/upcoming')
def api_upcoming():
    """API endpoint for upcoming events"""
    limit = request.args.get('limit', 5, type=int)
    
    events = LiveEvent.query.filter(
        LiveEvent.start_time > datetime.utcnow(),
        LiveEvent.is_public == True
    ).order_by(LiveEvent.start_time).limit(limit).all()
    
    return jsonify({
        'events': [{
            'id': e.id,
            'title': e.title,
            'type': e.event_type,
            'start_time': e.start_time.isoformat(),
            'attendee_count': EventAttendee.query.filter_by(event_id=e.id).count()
        } for e in events]
    })
