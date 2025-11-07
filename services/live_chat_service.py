"""
Live Chat Service for PittState Connect
Implements WebSocket-based real-time chat with AI fallback
Supports 1-on-1 chat, group chat, and counselor routing
"""

from flask_socketio import emit, join_room, leave_room, rooms
from extensions import db, socketio
from models import User
from datetime import datetime
import logging
import openai
import os

logger = logging.getLogger(__name__)

# Initialize OpenAI for AI chatbot
openai.api_key = os.getenv('OPENAI_API_KEY')


class LiveChatService:
    """Service for real-time chat functionality"""
    
    # Active chat rooms (in-memory for performance)
    active_rooms = {}
    online_users = set()
    
    @staticmethod
    def create_chat_room(room_type, participants, room_name=None):
        """
        Create a new chat room
        
        Args:
            room_type: 'direct', 'group', 'support'
            participants: List of user IDs
            room_name: Optional custom name
            
        Returns:
            dict: Room details
        """
        try:
            from models_extended import ChatRoom
            
            room_id = f"{room_type}_{int(datetime.now().timestamp())}"
            
            chat_room = ChatRoom(
                room_id=room_id,
                room_type=room_type,
                room_name=room_name or f"{room_type.capitalize()} Chat",
                created_at=datetime.now(),
                is_active=True
            )
            
            db.session.add(chat_room)
            db.session.flush()
            
            # Add participants
            from models_extended import ChatParticipant
            for user_id in participants:
                participant = ChatParticipant(
                    room_id=chat_room.id,
                    user_id=user_id,
                    joined_at=datetime.now()
                )
                db.session.add(participant)
            
            db.session.commit()
            
            # Add to active rooms
            LiveChatService.active_rooms[room_id] = {
                'participants': participants,
                'type': room_type,
                'created_at': datetime.now()
            }
            
            logger.info(f"✅ Created chat room: {room_id}")
            
            return {
                'room_id': room_id,
                'room_type': room_type,
                'room_name': chat_room.room_name,
                'participants': participants
            }
            
        except Exception as e:
            logger.error(f"Error creating chat room: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def send_message(room_id, user_id, message, message_type='text', metadata=None):
        """
        Send a message to a chat room
        
        Args:
            room_id: Room ID
            user_id: Sender user ID
            message: Message content
            message_type: text, image, file, system
            metadata: Additional data (file URL, etc.)
            
        Returns:
            dict: Message details
        """
        try:
            from models_growth_features import ChatMessage
            
            chat_message = ChatMessage(
                room_id=room_id,
                user_id=user_id,
                message=message,
                message_type=message_type,
                metadata=metadata,
                timestamp=datetime.now()
            )
            
            db.session.add(chat_message)
            db.session.commit()
            
            user = User.query.get(user_id)
            
            message_data = {
                'message_id': chat_message.id,
                'room_id': room_id,
                'user_id': user_id,
                'user_name': user.full_name if user else 'Unknown',
                'user_avatar': user.profile_image_url if user else None,
                'message': message,
                'message_type': message_type,
                'metadata': metadata,
                'timestamp': chat_message.timestamp.isoformat()
            }
            
            # Emit to room via WebSocket
            socketio.emit('new_message', message_data, room=room_id)
            
            logger.info(f"✅ Message sent in room {room_id} by user {user_id}")
            
            return message_data
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_room_messages(room_id, limit=50, before_id=None):
        """
        Get messages from a room (for history/pagination)
        
        Args:
            room_id: Room ID
            limit: Max messages to return
            before_id: Get messages before this message ID (pagination)
            
        Returns:
            list: Message list
        """
        try:
            from models_growth_features import ChatMessage
            
            query = ChatMessage.query.filter_by(room_id=room_id)
            
            if before_id:
                query = query.filter(ChatMessage.id < before_id)
            
            messages = query.order_by(ChatMessage.timestamp.desc()).limit(limit).all()
            
            result = []
            for msg in reversed(messages):
                user = User.query.get(msg.user_id)
                result.append({
                    'message_id': msg.id,
                    'user_id': msg.user_id,
                    'user_name': user.full_name if user else 'Unknown',
                    'user_avatar': user.profile_image_url if user else None,
                    'message': msg.message,
                    'message_type': msg.message_type,
                    'metadata': msg.metadata,
                    'timestamp': msg.timestamp.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting room messages: {str(e)}")
            return []
    
    @staticmethod
    def get_user_rooms(user_id):
        """
        Get all chat rooms for a user
        
        Args:
            user_id: User ID
            
        Returns:
            list: Room list with unread counts
        """
        try:
            from models_growth_features import ChatMessage
            from models_extended import ChatParticipant, ChatRoom
            
            # Get all rooms user is in
            participants = ChatParticipant.query.filter_by(user_id=user_id).all()
            
            rooms_data = []
            for participant in participants:
                room = ChatRoom.query.get(participant.room_id)
                if not room or not room.is_active:
                    continue
                
                # Get latest message
                latest_message = ChatMessage.query.filter_by(
                    room_id=room.room_id
                ).order_by(ChatMessage.timestamp.desc()).first()
                
                # Count unread messages
                unread_count = ChatMessage.query.filter(
                    ChatMessage.room_id == room.room_id,
                    ChatMessage.user_id != user_id,
                    ChatMessage.timestamp > participant.last_read_at if participant.last_read_at else room.created_at
                ).count()
                
                rooms_data.append({
                    'room_id': room.room_id,
                    'room_name': room.room_name,
                    'room_type': room.room_type,
                    'unread_count': unread_count,
                    'latest_message': latest_message.message if latest_message else None,
                    'latest_message_time': latest_message.timestamp.isoformat() if latest_message else None
                })
            
            return rooms_data
            
        except Exception as e:
            logger.error(f"Error getting user rooms: {str(e)}")
            return []
    
    @staticmethod
    def mark_room_as_read(room_id, user_id):
        """Mark all messages in room as read"""
        try:
            from models_extended import ChatParticipant
            
            participant = ChatParticipant.query.filter_by(
                room_id=room_id,
                user_id=user_id
            ).first()
            
            if participant:
                participant.last_read_at = datetime.now()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking room as read: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_ai_response(user_message, user_id=None):
        """
        Get AI chatbot response for support queries
        
        Args:
            user_message: User's question
            user_id: Optional user ID for personalization
            
        Returns:
            str: AI response
        """
        try:
            # Build context
            context = """You are a helpful assistant for PittState Connect, a university engagement platform.
            You can help with:
            - Finding jobs and internships
            - Scholarship information and deadlines
            - Campus events and activities
            - Alumni networking
            - Career advice
            - Platform navigation and features
            
            Provide concise, helpful responses. If you don't know something, suggest they contact support."""
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            logger.info(f"✅ AI response generated for query: {user_message[:50]}...")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again or contact support at support@pittstate.edu"
    
    @staticmethod
    def route_to_counselor(room_id, user_id, topic):
        """
        Route chat to available counselor
        
        Args:
            room_id: Current room ID
            user_id: User requesting counselor
            topic: Topic of inquiry
            
        Returns:
            dict: Routing result
        """
        try:
            from models_extended import ChatRoom, ChatParticipant
            
            # Find available counselors
            counselors = User.query.filter_by(role='counselor').filter_by(is_active=True).all()
            
            if not counselors:
                return {
                    'success': False,
                    'message': 'No counselors available. Please try again later or email support@pittstate.edu'
                }
            
            # Simple round-robin (could be enhanced with workload tracking)
            counselor = counselors[0]
            
            # Create new support room
            support_room = ChatRoom(
                room_id=f"support_{int(datetime.now().timestamp())}",
                room_type='support',
                room_name=f"Support: {topic}",
                created_at=datetime.now(),
                is_active=True
            )
            
            db.session.add(support_room)
            db.session.flush()
            
            # Add user and counselor as participants
            for uid in [user_id, counselor.id]:
                participant = ChatParticipant(
                    room_id=support_room.id,
                    user_id=uid,
                    joined_at=datetime.now()
                )
                db.session.add(participant)
            
            db.session.commit()
            
            # Send initial system message
            LiveChatService.send_message(
                support_room.room_id,
                counselor.id,
                f"Hi! I'm {counselor.full_name}, a counselor here to help you with {topic}. How can I assist you today?",
                message_type='system'
            )
            
            # Notify counselor via WebSocket
            socketio.emit('new_support_request', {
                'room_id': support_room.room_id,
                'user_id': user_id,
                'topic': topic
            }, room=f"user_{counselor.id}")
            
            logger.info(f"✅ Routed user {user_id} to counselor {counselor.id}")
            
            return {
                'success': True,
                'room_id': support_room.room_id,
                'counselor_name': counselor.full_name,
                'message': f"Connected to {counselor.full_name}"
            }
            
        except Exception as e:
            logger.error(f"Error routing to counselor: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': 'Failed to connect to counselor'
            }
    
    @staticmethod
    def set_user_online(user_id):
        """Mark user as online"""
        LiveChatService.online_users.add(user_id)
        socketio.emit('user_online', {'user_id': user_id}, broadcast=True)
        logger.info(f"User {user_id} is now online")
    
    @staticmethod
    def set_user_offline(user_id):
        """Mark user as offline"""
        LiveChatService.online_users.discard(user_id)
        socketio.emit('user_offline', {'user_id': user_id}, broadcast=True)
        logger.info(f"User {user_id} is now offline")
    
    @staticmethod
    def get_online_users():
        """Get list of online users"""
        return list(LiveChatService.online_users)
    
    @staticmethod
    def typing_indicator(room_id, user_id, is_typing):
        """
        Send typing indicator to room
        
        Args:
            room_id: Room ID
            user_id: User who is typing
            is_typing: Boolean - is user currently typing
        """
        user = User.query.get(user_id)
        socketio.emit('user_typing', {
            'room_id': room_id,
            'user_id': user_id,
            'user_name': user.full_name if user else 'Unknown',
            'is_typing': is_typing
        }, room=room_id)


# WebSocket Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle user connection"""
    logger.info(f"Client connected")
    emit('connected', {'status': 'success'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnection"""
    logger.info(f"Client disconnected")


@socketio.on('join_room')
def handle_join_room(data):
    """Handle user joining a room"""
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    
    if room_id and user_id:
        join_room(room_id)
        LiveChatService.set_user_online(user_id)
        
        emit('room_joined', {
            'room_id': room_id,
            'user_id': user_id
        }, room=room_id)
        
        logger.info(f"User {user_id} joined room {room_id}")


@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle user leaving a room"""
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    
    if room_id and user_id:
        leave_room(room_id)
        
        emit('room_left', {
            'room_id': room_id,
            'user_id': user_id
        }, room=room_id)
        
        logger.info(f"User {user_id} left room {room_id}")


@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message"""
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    message = data.get('message')
    message_type = data.get('message_type', 'text')
    
    if room_id and user_id and message:
        result = LiveChatService.send_message(room_id, user_id, message, message_type)
        
        if result:
            emit('message_sent', {'status': 'success', 'message_id': result['message_id']})
        else:
            emit('message_error', {'status': 'error', 'message': 'Failed to send message'})


@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    is_typing = data.get('is_typing', True)
    
    if room_id and user_id:
        LiveChatService.typing_indicator(room_id, user_id, is_typing)


@socketio.on('ai_query')
def handle_ai_query(data):
    """Handle AI chatbot query"""
    user_message = data.get('message')
    user_id = data.get('user_id')
    
    if user_message:
        ai_response = LiveChatService.get_ai_response(user_message, user_id)
        emit('ai_response', {
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
