from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import study_groups_bp
from extensions import db
from models_innovative_features import StudyGroup, StudyGroupMember
from datetime import datetime
from sqlalchemy import or_

@study_groups_bp.route('/')
def index():
    """Browse study groups"""
    # Get filter parameters
    course_code = request.args.get('course', '')
    group_type = request.args.get('type', 'all')
    commitment = request.args.get('commitment', 'all')
    
    # Base query - only active groups that aren't full
    query = StudyGroup.query.filter(StudyGroup.is_active == True)
    
    # Apply filters
    if course_code:
        query = query.filter(
            or_(
                StudyGroup.course_code.ilike(f'%{course_code}%'),
                StudyGroup.course_name.ilike(f'%{course_code}%')
            )
        )
    
    if group_type != 'all':
        query = query.filter(StudyGroup.group_type == group_type)
    
    if commitment != 'all':
        query = query.filter(StudyGroup.commitment_level == commitment)
    
    # Order by next meeting
    groups = query.order_by(StudyGroup.next_meeting.asc().nullslast()).all()
    
    return render_template('study_groups/index.html', groups=groups)


@study_groups_bp.route('/group/<int:group_id>')
def view_group(group_id):
    """View study group details"""
    group = StudyGroup.query.get_or_404(group_id)
    
    # Check if user is a member
    is_member = False
    membership = None
    if current_user.is_authenticated:
        membership = StudyGroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id,
            status='active'
        ).first()
        is_member = membership is not None
    
    # Get active members
    members = StudyGroupMember.query.filter_by(
        group_id=group_id,
        status='active'
    ).all()
    
    return render_template('study_groups/view_group.html', 
                         group=group, 
                         is_member=is_member,
                         members=members)


@study_groups_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create new study group"""
    if request.method == 'POST':
        # Create group
        group = StudyGroup(
            creator_id=current_user.id,
            course_code=request.form.get('course_code').upper(),
            course_name=request.form.get('course_name'),
            professor_name=request.form.get('professor_name'),
            group_name=request.form.get('group_name'),
            description=request.form.get('description'),
            focus_topics=request.form.get('focus_topics'),
            meeting_location=request.form.get('meeting_location'),
            is_virtual=request.form.get('is_virtual') == 'on',
            virtual_link=request.form.get('virtual_link'),
            meeting_schedule=request.form.get('meeting_schedule'),
            max_members=int(request.form.get('max_members', 8)),
            current_members=1,
            group_type=request.form.get('group_type', 'open'),
            commitment_level=request.form.get('commitment_level', 'moderate'),
            requires_approval=request.form.get('requires_approval') == 'on'
        )
        
        # Handle next meeting date
        if request.form.get('next_meeting'):
            group.next_meeting = datetime.strptime(request.form.get('next_meeting'), '%Y-%m-%dT%H:%M')
        
        # GPA requirement (optional)
        if request.form.get('gpa_requirement'):
            group.gpa_requirement = float(request.form.get('gpa_requirement'))
        
        db.session.add(group)
        db.session.flush()  # Get group ID
        
        # Add creator as first member
        member = StudyGroupMember(
            group_id=group.id,
            user_id=current_user.id,
            status='active'
        )
        db.session.add(member)
        db.session.commit()
        
        flash('Study group created successfully!', 'success')
        return redirect(url_for('study_groups.view_group', group_id=group.id))
    
    return render_template('study_groups/create_group.html')


@study_groups_bp.route('/join/<int:group_id>', methods=['POST'])
@login_required
def join_group(group_id):
    """Join a study group"""
    group = StudyGroup.query.get_or_404(group_id)
    
    # Check if already a member
    existing = StudyGroupMember.query.filter_by(
        group_id=group_id,
        user_id=current_user.id
    ).first()
    
    if existing and existing.status == 'active':
        flash('You are already a member of this group.', 'info')
        return redirect(url_for('study_groups.view_group', group_id=group_id))
    
    # Check if group is full
    if group.is_full or group.current_members >= group.max_members:
        flash('This group is full.', 'error')
        return redirect(url_for('study_groups.view_group', group_id=group_id))
    
    # Create or reactivate membership
    if existing:
        existing.status = 'active'
        existing.joined_at = datetime.utcnow()
    else:
        member = StudyGroupMember(
            group_id=group_id,
            user_id=current_user.id,
            status='active'
        )
        db.session.add(member)
    
    # Update member count
    group.current_members += 1
    if group.current_members >= group.max_members:
        group.is_full = True
    
    db.session.commit()
    
    flash(f'Successfully joined {group.group_name}!', 'success')
    return redirect(url_for('study_groups.view_group', group_id=group_id))


@study_groups_bp.route('/leave/<int:group_id>', methods=['POST'])
@login_required
def leave_group(group_id):
    """Leave a study group"""
    group = StudyGroup.query.get_or_404(group_id)
    
    membership = StudyGroupMember.query.filter_by(
        group_id=group_id,
        user_id=current_user.id,
        status='active'
    ).first()
    
    if not membership:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('study_groups.index'))
    
    # Can't leave if you're the creator
    if group.creator_id == current_user.id:
        flash('Group creators cannot leave. Please delete the group instead.', 'error')
        return redirect(url_for('study_groups.view_group', group_id=group_id))
    
    membership.status = 'inactive'
    group.current_members -= 1
    group.is_full = False
    
    db.session.commit()
    
    flash('You have left the study group.', 'info')
    return redirect(url_for('study_groups.my_groups'))


@study_groups_bp.route('/my-groups')
@login_required
def my_groups():
    """View user's study groups"""
    # Groups created by user
    created_groups = StudyGroup.query.filter_by(
        creator_id=current_user.id,
        is_active=True
    ).all()
    
    # Groups user is a member of
    memberships = StudyGroupMember.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()
    
    joined_groups = [m.group for m in memberships if m.group.creator_id != current_user.id]
    
    return render_template('study_groups/my_groups.html', 
                         created_groups=created_groups,
                         joined_groups=joined_groups)


@study_groups_bp.route('/edit/<int:group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    """Edit study group (creator only)"""
    group = StudyGroup.query.get_or_404(group_id)
    
    if group.creator_id != current_user.id:
        flash('Only the group creator can edit the group.', 'error')
        return redirect(url_for('study_groups.view_group', group_id=group_id))
    
    if request.method == 'POST':
        group.group_name = request.form.get('group_name')
        group.description = request.form.get('description')
        group.focus_topics = request.form.get('focus_topics')
        group.meeting_location = request.form.get('meeting_location')
        group.is_virtual = request.form.get('is_virtual') == 'on'
        group.virtual_link = request.form.get('virtual_link')
        group.meeting_schedule = request.form.get('meeting_schedule')
        
        if request.form.get('next_meeting'):
            group.next_meeting = datetime.strptime(request.form.get('next_meeting'), '%Y-%m-%dT%H:%M')
        
        db.session.commit()
        
        flash('Study group updated!', 'success')
        return redirect(url_for('study_groups.view_group', group_id=group_id))
    
    return render_template('study_groups/edit_group.html', group=group)


@study_groups_bp.route('/delete/<int:group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    """Delete study group (creator only)"""
    group = StudyGroup.query.get_or_404(group_id)
    
    if group.creator_id != current_user.id:
        flash('Only the group creator can delete the group.', 'error')
        return redirect(url_for('study_groups.view_group', group_id=group_id))
    
    group.is_active = False
    db.session.commit()
    
    flash('Study group deleted.', 'info')
    return redirect(url_for('study_groups.my_groups'))


@study_groups_bp.route('/by-course/<course_code>')
def by_course(course_code):
    """View all study groups for a specific course"""
    groups = StudyGroup.query.filter(
        StudyGroup.course_code.ilike(f'%{course_code}%'),
        StudyGroup.is_active == True
    ).order_by(StudyGroup.next_meeting.asc().nullslast()).all()
    
    return render_template('study_groups/by_course.html', 
                         course_code=course_code,
                         groups=groups)


@study_groups_bp.route('/search')
def search():
    """AJAX search for courses"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    # Search for unique course codes
    from sqlalchemy import func, distinct
    
    results = db.session.query(
        distinct(StudyGroup.course_code),
        StudyGroup.course_name
    ).filter(
        or_(
            StudyGroup.course_code.ilike(f'%{query}%'),
            StudyGroup.course_name.ilike(f'%{query}%')
        ),
        StudyGroup.is_active == True
    ).limit(10).all()
    
    return jsonify([{
        'code': r[0],
        'name': r[1]
    } for r in results])
