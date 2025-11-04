"""
GraphQL API Schema for PittState-Connect
Provides alternative API interface alongside REST
"""

import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from models import User, Post, Event, Scholarship, Job, Department, Notification
from models_extended import (
    AlumniProfile, ScholarshipApplication, Message, 
    EmployerPortal, Webinar, Forum, ForumThread
)
from extensions import db
from flask_login import current_user
from datetime import datetime


# ============================================================
# OBJECT TYPES
# ============================================================

class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (relay.Node,)
        exclude_fields = ('password_hash',)


class PostType(SQLAlchemyObjectType):
    class Meta:
        model = Post
        interfaces = (relay.Node,)


class EventType(SQLAlchemyObjectType):
    class Meta:
        model = Event
        interfaces = (relay.Node,)


class ScholarshipType(SQLAlchemyObjectType):
    class Meta:
        model = Scholarship
        interfaces = (relay.Node,)


class JobType(SQLAlchemyObjectType):
    class Meta:
        model = Job
        interfaces = (relay.Node,)


class DepartmentType(SQLAlchemyObjectType):
    class Meta:
        model = Department
        interfaces = (relay.Node,)


class AlumniProfileType(SQLAlchemyObjectType):
    class Meta:
        model = AlumniProfile
        interfaces = (relay.Node,)


class ScholarshipApplicationType(SQLAlchemyObjectType):
    class Meta:
        model = ScholarshipApplication
        interfaces = (relay.Node,)


class MessageType(SQLAlchemyObjectType):
    class Meta:
        model = Message
        interfaces = (relay.Node,)


class WebinarType(SQLAlchemyObjectType):
    class Meta:
        model = Webinar
        interfaces = (relay.Node,)


class ForumType(SQLAlchemyObjectType):
    class Meta:
        model = Forum
        interfaces = (relay.Node,)


# ============================================================
# QUERIES
# ============================================================

class Query(graphene.ObjectType):
    node = relay.Node.Field()
    
    # User queries
    user = graphene.Field(UserType, id=graphene.Int())
    all_users = SQLAlchemyConnectionField(UserType.connection)
    current_user = graphene.Field(UserType)
    
    # Content queries
    post = graphene.Field(PostType, id=graphene.Int())
    all_posts = SQLAlchemyConnectionField(PostType.connection)
    
    event = graphene.Field(EventType, id=graphene.Int())
    all_events = SQLAlchemyConnectionField(EventType.connection)
    upcoming_events = graphene.List(EventType)
    
    # Scholarship queries
    scholarship = graphene.Field(ScholarshipType, id=graphene.Int())
    all_scholarships = SQLAlchemyConnectionField(ScholarshipType.connection)
    active_scholarships = graphene.List(ScholarshipType)
    my_scholarship_applications = graphene.List(ScholarshipApplicationType)
    
    # Job queries
    job = graphene.Field(JobType, id=graphene.Int())
    all_jobs = SQLAlchemyConnectionField(JobType.connection)
    active_jobs = graphene.List(JobType)
    
    # Department queries
    department = graphene.Field(DepartmentType, id=graphene.Int())
    all_departments = SQLAlchemyConnectionField(DepartmentType.connection)
    
    # Alumni queries
    alumni_profile = graphene.Field(AlumniProfileType, user_id=graphene.Int())
    all_alumni = graphene.List(AlumniProfileType)
    mentors = graphene.List(AlumniProfileType)
    
    # Communication queries
    my_messages = graphene.List(MessageType)
    webinar = graphene.Field(WebinarType, id=graphene.Int())
    upcoming_webinars = graphene.List(WebinarType)
    
    # Search
    search = graphene.List(
        graphene.Union('SearchResult', (UserType, PostType, EventType, ScholarshipType)),
        query=graphene.String(required=True)
    )
    
    # Resolvers
    def resolve_user(self, info, id):
        return User.query.get(id)
    
    def resolve_current_user(self, info):
        if current_user.is_authenticated:
            return current_user._get_current_object()
        return None
    
    def resolve_post(self, info, id):
        return Post.query.get(id)
    
    def resolve_event(self, info, id):
        return Event.query.get(id)
    
    def resolve_upcoming_events(self, info):
        return Event.query.filter(
            Event.start_time >= datetime.utcnow()
        ).order_by(Event.start_time.asc()).limit(20).all()
    
    def resolve_scholarship(self, info, id):
        return Scholarship.query.get(id)
    
    def resolve_active_scholarships(self, info):
        return Scholarship.query.filter(
            Scholarship.deadline >= datetime.utcnow().date()
        ).order_by(Scholarship.deadline.asc()).all()
    
    def resolve_my_scholarship_applications(self, info):
        if not current_user.is_authenticated:
            return []
        return ScholarshipApplication.query.filter_by(
            user_id=current_user.id
        ).all()
    
    def resolve_job(self, info, id):
        return Job.query.get(id)
    
    def resolve_active_jobs(self, info):
        return Job.query.filter_by(is_active=True).order_by(
            Job.posted_at.desc()
        ).limit(50).all()
    
    def resolve_department(self, info, id):
        return Department.query.get(id)
    
    def resolve_alumni_profile(self, info, user_id):
        return AlumniProfile.query.filter_by(user_id=user_id).first()
    
    def resolve_all_alumni(self, info):
        return AlumniProfile.query.all()
    
    def resolve_mentors(self, info):
        return AlumniProfile.query.filter_by(is_mentor=True).all()
    
    def resolve_my_messages(self, info):
        if not current_user.is_authenticated:
            return []
        return Message.query.filter_by(
            recipient_id=current_user.id
        ).order_by(Message.created_at.desc()).limit(50).all()
    
    def resolve_webinar(self, info, id):
        return Webinar.query.get(id)
    
    def resolve_upcoming_webinars(self, info):
        return Webinar.query.filter(
            Webinar.scheduled_at >= datetime.utcnow()
        ).order_by(Webinar.scheduled_at.asc()).all()
    
    def resolve_search(self, info, query):
        results = []
        
        # Search users
        users = User.query.filter(
            db.or_(
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).limit(10).all()
        results.extend(users)
        
        # Search posts
        posts = Post.query.filter(
            Post.content.ilike(f'%{query}%')
        ).limit(10).all()
        results.extend(posts)
        
        # Search events
        events = Event.query.filter(
            db.or_(
                Event.title.ilike(f'%{query}%'),
                Event.description.ilike(f'%{query}%')
            )
        ).limit(10).all()
        results.extend(events)
        
        # Search scholarships
        scholarships = Scholarship.query.filter(
            db.or_(
                Scholarship.title.ilike(f'%{query}%'),
                Scholarship.description.ilike(f'%{query}%')
            )
        ).limit(10).all()
        results.extend(scholarships)
        
        return results


# ============================================================
# MUTATIONS
# ============================================================

class CreatePost(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)
        image_url = graphene.String()
    
    post = graphene.Field(lambda: PostType)
    success = graphene.Boolean()
    
    def mutate(self, info, content, image_url=None):
        if not current_user.is_authenticated:
            return CreatePost(success=False, post=None)
        
        post = Post(
            content=content,
            author_id=current_user.id,
            image_url=image_url
        )
        db.session.add(post)
        db.session.commit()
        
        return CreatePost(success=True, post=post)


class CreateEvent(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String()
        location = graphene.String()
        start_time = graphene.DateTime(required=True)
        end_time = graphene.DateTime(required=True)
    
    event = graphene.Field(lambda: EventType)
    success = graphene.Boolean()
    
    def mutate(self, info, title, start_time, end_time, description=None, location=None):
        if not current_user.is_authenticated:
            return CreateEvent(success=False, event=None)
        
        event = Event(
            title=title,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            organizer_id=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        
        return CreateEvent(success=True, event=event)


class ApplyToScholarship(graphene.Mutation):
    class Arguments:
        scholarship_id = graphene.Int(required=True)
        essay_text = graphene.String()
    
    application = graphene.Field(lambda: ScholarshipApplicationType)
    success = graphene.Boolean()
    
    def mutate(self, info, scholarship_id, essay_text=None):
        if not current_user.is_authenticated:
            return ApplyToScholarship(success=False, application=None)
        
        # Check if already applied
        existing = ScholarshipApplication.query.filter_by(
            user_id=current_user.id,
            scholarship_id=scholarship_id
        ).first()
        
        if existing:
            return ApplyToScholarship(success=False, application=None)
        
        application = ScholarshipApplication(
            user_id=current_user.id,
            scholarship_id=scholarship_id,
            essay_text=essay_text,
            status='draft'
        )
        db.session.add(application)
        db.session.commit()
        
        return ApplyToScholarship(success=True, application=application)


class SendMessage(graphene.Mutation):
    class Arguments:
        recipient_id = graphene.Int(required=True)
        subject = graphene.String(required=True)
        body = graphene.String(required=True)
    
    message = graphene.Field(lambda: MessageType)
    success = graphene.Boolean()
    
    def mutate(self, info, recipient_id, subject, body):
        if not current_user.is_authenticated:
            return SendMessage(success=False, message=None)
        
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            subject=subject,
            body=body
        )
        db.session.add(message)
        db.session.commit()
        
        return SendMessage(success=True, message=message)


class RegisterForWebinar(graphene.Mutation):
    class Arguments:
        webinar_id = graphene.Int(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, webinar_id):
        from services.communication_service import get_communication_service
        
        if not current_user.is_authenticated:
            return RegisterForWebinar(success=False, message="Authentication required")
        
        comm = get_communication_service()
        success = comm.register_for_webinar(webinar_id, current_user.id)
        
        return RegisterForWebinar(
            success=success,
            message="Registration successful" if success else "Registration failed"
        )


class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    create_event = CreateEvent.Field()
    apply_to_scholarship = ApplyToScholarship.Field()
    send_message = SendMessage.Field()
    register_for_webinar = RegisterForWebinar.Field()


# ============================================================
# SCHEMA
# ============================================================

schema = graphene.Schema(query=Query, mutation=Mutation)
