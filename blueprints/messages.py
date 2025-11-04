"""
PSU Connect - InMail Direct Messaging System
LinkedIn-style messaging with monthly credit system
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import DirectMessage, UserMessageCredits
from models import User
from sqlalchemy import or_, desc, func
from datetime import datetime, timedelta

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')


def get_or_create_credits(user_id):
    """Get or create message credits for user"""
    credits = UserMessageCredits.query.filter_by(user_id=user_id).first()
    
    if not credits:
        # New user - give 5 free credits
        credits = UserMessageCredits(
            user_id=user_id,
            free_credits=5,
            premium_credits=0,
            last_refill=datetime.utcnow()
        )
        db.session.add(credits)
        db.session.commit()
    else:
        # Check if monthly refill is due
        if credits.last_refill < datetime.utcnow() - timedelta(days=30):
            credits.refill_credits()
            db.session.commit()
    
    return credits


@messages_bp.route('/')
@messages_bp.route('/inbox')
@login_required
def inbox():
    """View inbox"""
    # Get all conversations (grouped by other user)
    # Get messages where user is sender or recipient
    messages = DirectMessage.query.filter(
        or_(
            DirectMessage.sender_id == current_user.id,
            DirectMessage.recipient_id == current_user.id
        )
    ).order_by(desc(DirectMessage.created_at)).all()
    
    # Group by conversation partner
    conversations = {}
    for msg in messages:
        partner_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        
        if partner_id not in conversations:
            conversations[partner_id] = {
                'partner': User.query.get(partner_id),
                'last_message': msg,
                'unread_count': 0,
                'messages': []
            }
        
        conversations[partner_id]['messages'].append(msg)
        
        # Count unread
        if msg.recipient_id == current_user.id and not msg.read_at:
            conversations[partner_id]['unread_count'] += 1
    
    # Sort by last message time
    conversations = dict(sorted(
        conversations.items(),
        key=lambda x: x[1]['last_message'].created_at,
        reverse=True
    ))
    
    # Get user's credits
    credits = get_or_create_credits(current_user.id)
    
    return render_template('messages/inbox.html',
                         conversations=conversations,
                         credits=credits)


@messages_bp.route('/conversation/<int:user_id>')
@login_required
def conversation(user_id):
    """View conversation with specific user"""
    other_user = User.query.get_or_404(user_id)
    
    # Get all messages between users
    messages = DirectMessage.query.filter(
        or_(
            (DirectMessage.sender_id == current_user.id) & (DirectMessage.recipient_id == user_id),
            (DirectMessage.sender_id == user_id) & (DirectMessage.recipient_id == current_user.id)
        )
    ).order_by(DirectMessage.created_at).all()
    
    # Mark received messages as read
    for msg in messages:
        if msg.recipient_id == current_user.id and not msg.read_at:
            msg.read_at = datetime.utcnow()
    db.session.commit()
    
    # Get user's credits
    credits = get_or_create_credits(current_user.id)
    
    return render_template('messages/conversation.html',
                         other_user=other_user,
                         messages=messages,
                         credits=credits)


@messages_bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    """Compose new message"""
    if request.method == 'POST':
        data = request.json
        
        recipient_id = data.get('recipient_id', type=int)
        content = data.get('content', '').strip()
        
        if not recipient_id or not content:
            return jsonify({'error': 'Recipient and message required'}), 400
        
        # Verify recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            return jsonify({'error': 'Recipient not found'}), 404
        
        # Check if already have conversation (no credit needed)
        existing_conversation = DirectMessage.query.filter(
            or_(
                (DirectMessage.sender_id == current_user.id) & (DirectMessage.recipient_id == recipient_id),
                (DirectMessage.sender_id == recipient_id) & (DirectMessage.recipient_id == current_user.id)
            )
        ).first()
        
        needs_credit = existing_conversation is None
        
        # Check credits if starting new conversation
        if needs_credit:
            credits = get_or_create_credits(current_user.id)
            
            if credits.total_credits == 0:
                return jsonify({
                    'error': 'No message credits available',
                    'needs_premium': True
                }), 403
            
            # Deduct credit
            if credits.free_credits > 0:
                credits.free_credits -= 1
            else:
                credits.premium_credits -= 1
            
            credits.used_this_month += 1
        
        # Create message
        message = DirectMessage(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content,
            used_credit=needs_credit
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Send push notification
        from blueprints.push_notifications import notify_new_message
        notify_new_message(recipient_id, current_user.full_name, content[:100])
        
        return jsonify({
            'success': True,
            'message_id': message.id,
            'credit_used': needs_credit
        })
    
    # GET - show compose form
    # Get suggested recipients (connections, alumni in same field, etc.)
    suggested = User.query.filter(
        User.id != current_user.id
    ).limit(10).all()
    
    credits = get_or_create_credits(current_user.id)
    
    return render_template('messages/compose.html',
                         suggested=suggested,
                         credits=credits)


@messages_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send message in existing conversation"""
    data = request.json
    
    recipient_id = data.get('recipient_id', type=int)
    content = data.get('content', '').strip()
    
    if not recipient_id or not content:
        return jsonify({'error': 'Recipient and message required'}), 400
    
    # Verify recipient exists
    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404
    
    # No credit needed for existing conversations
    message = DirectMessage(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content,
        used_credit=False
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Send push notification
    from blueprints.push_notifications import notify_new_message
    notify_new_message(recipient_id, current_user.full_name, content[:100])
    
    return jsonify({
        'success': True,
        'message_id': message.id
    })


@messages_bp.route('/mark-read/<int:message_id>', methods=['POST'])
@login_required
def mark_read(message_id):
    """Mark message as read"""
    message = DirectMessage.query.get_or_404(message_id)
    
    # Verify recipient
    if message.recipient_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    message.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})


@messages_bp.route('/delete/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete message (soft delete)"""
    message = DirectMessage.query.get_or_404(message_id)
    
    # Only sender or recipient can delete
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    # Soft delete
    if message.sender_id == current_user.id:
        message.deleted_by_sender = True
    else:
        message.deleted_by_recipient = True
    
    # If both deleted, hard delete
    if message.deleted_by_sender and message.deleted_by_recipient:
        db.session.delete(message)
    
    db.session.commit()
    
    return jsonify({'success': True})


@messages_bp.route('/credits')
@login_required
def view_credits():
    """View message credits status"""
    credits = get_or_create_credits(current_user.id)
    
    return render_template('messages/credits.html', credits=credits)


@messages_bp.route('/credits/purchase', methods=['POST'])
@login_required
def purchase_credits():
    """Purchase additional message credits"""
    data = request.json
    amount = data.get('amount', type=int)
    
    # Credit packages
    packages = {
        10: 2.99,   # $2.99 for 10 credits
        25: 5.99,   # $5.99 for 25 credits
        50: 9.99,   # $9.99 for 50 credits
        100: 15.99  # $15.99 for 100 credits
    }
    
    if amount not in packages:
        return jsonify({'error': 'Invalid package'}), 400
    
    # TODO: Integrate with payment processor (Stripe)
    # For now, just add credits (simulation)
    
    credits = get_or_create_credits(current_user.id)
    credits.premium_credits += amount
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_total': credits.total_credits
    })


@messages_bp.route('/templates')
@login_required
def message_templates():
    """View message templates for common scenarios"""
    templates = [
        {
            'name': 'Job Inquiry',
            'subject': 'Question about [Position]',
            'body': 'Hi [Name],\n\nI saw your post about [position] and I\'m very interested. I have experience in [your skills] and would love to learn more.\n\nWould you be available for a brief chat?\n\nBest regards,\n[Your Name]'
        },
        {
            'name': 'Networking',
            'subject': 'Fellow PSU [Major] Graduate',
            'body': 'Hi [Name],\n\nI\'m a [your major] student at PSU and I noticed we share similar career interests. I\'d love to connect and learn from your experience.\n\nWould you be open to a quick virtual coffee chat?\n\nThanks,\n[Your Name]'
        },
        {
            'name': 'Mentorship Request',
            'subject': 'Mentorship Opportunity',
            'body': 'Hi [Name],\n\nI\'m impressed by your career path in [field]. As a PSU student pursuing [major], I\'m seeking guidance from experienced professionals.\n\nWould you consider being a mentor? I\'m happy to work around your schedule.\n\nBest,\n[Your Name]'
        },
        {
            'name': 'Thank You',
            'subject': 'Thank You',
            'body': 'Hi [Name],\n\nThank you for taking the time to [action]. I really appreciate your insights about [topic].\n\nI\'ve already started applying your advice and it\'s been very helpful.\n\nBest regards,\n[Your Name]'
        }
    ]
    
    return render_template('messages/templates.html', templates=templates)


@messages_bp.route('/search')
@login_required
def search_messages():
    """Search messages"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('messages.inbox'))
    
    messages = DirectMessage.query.filter(
        or_(
            DirectMessage.sender_id == current_user.id,
            DirectMessage.recipient_id == current_user.id
        ),
        DirectMessage.content.ilike(f'%{query}%')
    ).order_by(desc(DirectMessage.created_at)).limit(50).all()
    
    return render_template('messages/search_results.html',
                         query=query,
                         messages=messages)


@messages_bp.route('/unread-count')
@login_required
def unread_count():
    """Get unread message count (for navbar badge)"""
    count = DirectMessage.query.filter_by(
        recipient_id=current_user.id,
        read_at=None
    ).count()
    
    return jsonify({'count': count})
