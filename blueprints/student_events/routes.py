from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models_student_features import StudentEvent, EventRSVP
from sqlalchemy import or_, and_
from datetime import datetime, timedelta

events_bp = Blueprint('student_events', __name__, url_prefix='/events')

@events_bp.route('/')
def index():
    """Student events calendar homepage"""
    event_type = request.args.get('type', '')
    category = request.args.get('category', '')
    when = request.args.get('when', 'upcoming')  # upcoming, today, this_week, this_month
    search_query = request.args.get('q', '')
    
    query = StudentEvent.query.filter_by(status='upcoming')
    
    # Apply filters
    if event_type:
        query = query.filter_by(event_type=event_type)
    
    if category:
        query = query.filter_by(category=category)
    
    if search_query:
        query = query.filter(
            or_(
                StudentEvent.title.ilike(f'%{search_query}%'),
                StudentEvent.description.ilike(f'%{search_query}%'),
                StudentEvent.organization_name.ilike(f'%{search_query}%')
            )
        )
    
    # Time filters
    now = datetime.utcnow()
    if when == 'today':
        end_of_day = now.replace(hour=23, minute=59, second=59)
        query = query.filter(
            and_(
                StudentEvent.start_datetime >= now,
                StudentEvent.start_datetime <= end_of_day
            )
        )
    elif when == 'this_week':
        week_end = now + timedelta(days=7)
        query = query.filter(StudentEvent.start_datetime.between(now, week_end))
    elif when == 'this_month':
        month_end = now + timedelta(days=30)
        query = query.filter(StudentEvent.start_datetime.between(now, month_end))
    else:  # upcoming (all future events)
        query = query.filter(StudentEvent.start_datetime >= now)
    
    events = query.order_by(StudentEvent.start_datetime.asc()).limit(100).all()
    
    # Get featured events
    featured = StudentEvent.query.filter_by(
        is_featured=True,
        status='upcoming'
    ).filter(
        StudentEvent.start_datetime >= now
    ).order_by(StudentEvent.start_datetime.asc()).limit(3).all()
    
    return render_template('student_events/index.html',
                         events=events,
                         featured=featured,
                         event_type=event_type,
                         category=category,
                         when=when,
                         search_query=search_query)


@events_bp.route('/event/<int:event_id>')
def view_event(event_id):
    """View event details"""
    event = StudentEvent.query.get_or_404(event_id)
    
    # Increment view count
    event.view_count += 1
    db.session.commit()
    
    # Check if current user has RSVP'd
    user_rsvp = None
    if current_user.is_authenticated:
        user_rsvp = EventRSVP.query.filter_by(
            event_id=event_id,
            user_id=current_user.id
        ).first()
    
    # Get attendees count
    going_count = EventRSVP.query.filter_by(
        event_id=event_id,
        status='going'
    ).count()
    
    interested_count = EventRSVP.query.filter_by(
        event_id=event_id,
        status='interested'
    ).count()
    
    return render_template('student_events/event.html',
                         event=event,
                         user_rsvp=user_rsvp,
                         going_count=going_count,
                         interested_count=interested_count)


@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():
    """Create a new student event"""
    if request.method == 'POST':
        start_datetime = datetime.strptime(
            request.form['start_datetime'],
            '%Y-%m-%dT%H:%M'
        )
        
        end_datetime = None
        if request.form.get('end_datetime'):
            end_datetime = datetime.strptime(
                request.form['end_datetime'],
                '%Y-%m-%dT%H:%M'
            )
        
        event = StudentEvent(
            title=request.form['title'],
            description=request.form.get('description'),
            event_type=request.form['event_type'],
            category=request.form.get('category'),
            organizer_id=current_user.id,
            organization_name=request.form.get('organization_name'),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location_name=request.form.get('location_name'),
            address=request.form.get('address'),
            is_virtual=request.form.get('is_virtual') == 'on',
            virtual_link=request.form.get('virtual_link'),
            is_free=request.form.get('is_free') == 'on',
            cost=float(request.form.get('cost', 0)) if request.form.get('cost') else None,
            capacity=int(request.form.get('capacity', 0)) if request.form.get('capacity') else None,
            rsvp_required=request.form.get('rsvp_required') == 'on',
            students_only=request.form.get('students_only') == 'on'
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('student_events.view_event', event_id=event.id))
    
    return render_template('student_events/create.html')


@events_bp.route('/my-events')
@login_required
def my_events():
    """View user's created and RSVP'd events"""
    created_events = StudentEvent.query.filter_by(
        organizer_id=current_user.id
    ).order_by(StudentEvent.start_datetime.desc()).all()
    
    rsvp_events = db.session.query(StudentEvent).join(
        EventRSVP,
        StudentEvent.id == EventRSVP.event_id
    ).filter(
        EventRSVP.user_id == current_user.id,
        EventRSVP.status == 'going'
    ).order_by(StudentEvent.start_datetime.asc()).all()
    
    return render_template('student_events/my_events.html',
                         created_events=created_events,
                         rsvp_events=rsvp_events)


@events_bp.route('/rsvp/<int:event_id>', methods=['POST'])
@login_required
def rsvp(event_id):
    """RSVP to an event"""
    event = StudentEvent.query.get_or_404(event_id)
    status = request.form.get('status', 'going')  # going, interested, not_going
    
    # Check for existing RSVP
    existing_rsvp = EventRSVP.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()
    
    if existing_rsvp:
        existing_rsvp.status = status
        message = 'RSVP updated!'
    else:
        rsvp = EventRSVP(
            event_id=event_id,
            user_id=current_user.id,
            status=status
        )
        db.session.add(rsvp)
        message = 'RSVP submitted!'
    
    # Update event RSVP count
    event.rsvp_count = EventRSVP.query.filter_by(
        event_id=event_id,
        status='going'
    ).count()
    
    db.session.commit()
    
    flash(message, 'success')
    return redirect(url_for('student_events.view_event', event_id=event_id))


@events_bp.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    """Edit an event"""
    event = StudentEvent.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id:
        flash('You can only edit your own events.', 'danger')
        return redirect(url_for('student_events.view_event', event_id=event_id))
    
    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form.get('description')
        event.event_type = request.form['event_type']
        event.category = request.form.get('category')
        event.location_name = request.form.get('location_name')
        event.is_virtual = request.form.get('is_virtual') == 'on'
        event.virtual_link = request.form.get('virtual_link')
        event.is_free = request.form.get('is_free') == 'on'
        event.cost = float(request.form.get('cost', 0)) if request.form.get('cost') else None
        
        db.session.commit()
        flash('Event updated!', 'success')
        return redirect(url_for('student_events.view_event', event_id=event_id))
    
    return render_template('student_events/edit.html', event=event)


@events_bp.route('/cancel/<int:event_id>', methods=['POST'])
@login_required
def cancel_event(event_id):
    """Cancel an event"""
    event = StudentEvent.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    event.status = 'cancelled'
    db.session.commit()
    
    flash('Event cancelled.', 'info')
    return redirect(url_for('student_events.my_events'))


@events_bp.route('/calendar-view')
def calendar_view():
    """Calendar view of events"""
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    
    # Get events for the specified month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    events = StudentEvent.query.filter(
        and_(
            StudentEvent.start_datetime >= start_date,
            StudentEvent.start_datetime < end_date,
            StudentEvent.status == 'upcoming'
        )
    ).order_by(StudentEvent.start_datetime).all()
    
    return render_template('student_events/calendar.html',
                         events=events,
                         month=month,
                         year=year)
