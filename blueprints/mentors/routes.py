# File: blueprints/mentors/routes.py
from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from utils.analytics_util import track_page_view
from services.live_chat_service import LiveChatService
from models import User, db
from models_extended import Message
from datetime import datetime
from sqlalchemy import or_, and_
from . import bp

@bp.get("/health")
def health():
    return jsonify(status="ok", section="mentors")

@bp.get("/")
@login_required
def index():
    """Mentor discovery and matchmaking"""
    track_page_view("mentors")
    
    # Get available mentors (alumni and faculty)
    mentors = User.query.filter(
        User.role_id.in_([
            db.session.query(db.text("id")).select_from(db.text("roles")).filter(
                db.text("name").in_(['alumni', 'faculty'])
            )
        ]),
        User.is_active == True
    ).limit(20).all()
    
    # Get user's active conversations
    conversations = Message.query.filter(
        or_(
            Message.sender_id == current_user.id,
            Message.recipient_id == current_user.id
        )
    ).order_by(Message.created_at.desc()).limit(10).all()
    
    # Group by thread
    threads = {}
    for msg in conversations:
        if msg.thread_id not in threads:
            other_user_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
            other_user = User.query.get(other_user_id)
            threads[msg.thread_id] = {
                'thread_id': msg.thread_id,
                'other_user': other_user,
                'last_message': msg,
                'unread_count': Message.query.filter(
                    Message.thread_id == msg.thread_id,
                    Message.recipient_id == current_user.id,
                    Message.is_read == False
                ).count()
            }
    
    return render_template('mentors/index.html', 
                         mentors=mentors, 
                         threads=list(threads.values()))


@bp.get("/chat/<int:mentor_id>")
@login_required
def chat(mentor_id):
    """Real-time chat interface with mentor"""
    track_page_view("mentor_chat")
    
    mentor = User.query.get_or_404(mentor_id)
    
    # Generate or get thread ID
    thread_id = f"chat_{min(current_user.id, mentor_id)}_{max(current_user.id, mentor_id)}"
    
    # Get message history
    messages = Message.query.filter_by(thread_id=thread_id).order_by(
        Message.created_at.asc()
    ).limit(100).all()
    
    # Mark messages as read
    unread_messages = Message.query.filter(
        Message.thread_id == thread_id,
        Message.recipient_id == current_user.id,
        Message.is_read == False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
        msg.read_at = datetime.utcnow()
    
    db.session.commit()
    
    return render_template('mentors/chat.html',
                         mentor=mentor,
                         messages=messages,
                         thread_id=thread_id)


@bp.post("/chat/send")
@login_required
def send_message():
    """Send a message"""
    data = request.get_json()
    
    recipient_id = data.get('recipient_id')
    message_body = data.get('message')
    thread_id = data.get('thread_id')
    
    if not recipient_id or not message_body:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    try:
        # Create message
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            body=message_body,
            thread_id=thread_id,
            is_read=False,
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Emit via WebSocket for real-time delivery
        from extensions import socketio
        socketio.emit('new_message', {
            'message_id': message.id,
            'sender_id': current_user.id,
            'sender_name': current_user.full_name,
            'sender_avatar': current_user.profile_image_url,
            'recipient_id': recipient_id,
            'body': message_body,
            'thread_id': thread_id,
            'timestamp': message.created_at.isoformat()
        }, room=f"user_{recipient_id}")
        
        return jsonify({
            'success': True,
            'message_id': message.id,
            'timestamp': message.created_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.get("/chat/messages/<thread_id>")
@login_required
def get_messages(thread_id):
    """Get message history (AJAX endpoint)"""
    
    # Verify user is part of thread
    sample_message = Message.query.filter_by(thread_id=thread_id).first()
    if not sample_message:
        return jsonify({'success': False, 'error': 'Thread not found'}), 404
    
    if current_user.id not in [sample_message.sender_id, sample_message.recipient_id]:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    # Get messages
    messages = Message.query.filter_by(thread_id=thread_id).order_by(
        Message.created_at.asc()
    ).all()
    
    result = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        result.append({
            'message_id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': sender.full_name if sender else 'Unknown',
            'sender_avatar': sender.profile_image_url if sender else None,
            'body': msg.body,
            'is_read': msg.is_read,
            'read_at': msg.read_at.isoformat() if msg.read_at else None,
            'timestamp': msg.created_at.isoformat()
        })
    
    return jsonify({'success': True, 'messages': result})


@bp.post("/chat/mark-read/<int:message_id>")
@login_required
def mark_read(message_id):
    """Mark message as read"""
    message = Message.query.get_or_404(message_id)
    
    if message.recipient_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    message.is_read = True
    message.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})


@bp.get("/chat/online-status/<int:user_id>")
@login_required
def online_status(user_id):
    """Check if user is online"""
    is_online = user_id in LiveChatService.online_users
    
    user = User.query.get(user_id)
    last_seen = None
    if user and hasattr(user, 'last_login'):
        last_seen = user.last_login.isoformat() if user.last_login else None
    
    return jsonify({
        'user_id': user_id,
        'is_online': is_online,
        'last_seen': last_seen
    })
