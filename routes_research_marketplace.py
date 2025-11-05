"""
Research Project Marketplace Routes
Connect faculty research with student talent
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models_advanced_features import ResearchProject, ResearchApplication, ResearchTeamMember
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, desc

research_bp = Blueprint('research', __name__, url_prefix='/research')

# ==================== STUDENT: BROWSE PROJECTS ====================

@research_bp.route('/')
def browse_projects():
    """Main research marketplace"""
    research_area = request.args.get('area', 'all')
    compensation = request.args.get('compensation', 'all')
    search = request.args.get('search', '')
    
    query = ResearchProject.query.filter_by(status='active')
    
    if research_area != 'all':
        query = query.filter_by(research_area=research_area)
    
    if compensation != 'all':
        if compensation == 'paid':
            query = query.filter(
                or_(
                    ResearchProject.compensation_type == 'stipend',
                    ResearchProject.compensation_type == 'work_study'
                )
            )
        elif compensation == 'credit':
            query = query.filter_by(compensation_type='credit')
    
    if search:
        query = query.filter(
            or_(
                ResearchProject.title.ilike(f'%{search}%'),
                ResearchProject.description.ilike(f'%{search}%'),
                ResearchProject.specific_field.ilike(f'%{search}%')
            )
        )
    
    # Featured projects first, then by deadline
    projects = query.order_by(
        ResearchProject.is_featured.desc(),
        ResearchProject.application_deadline
    ).all()
    
    return render_template('research/browse.html',
                         projects=projects,
                         current_area=research_area,
                         current_compensation=compensation)


@research_bp.route('/project/<int:project_id>')
def view_project(project_id):
    """View detailed project information"""
    project = ResearchProject.query.get_or_404(project_id)
    
    # Track view
    project.view_count += 1
    db.session.commit()
    
    # Check if user already applied
    has_applied = False
    user_application = None
    if current_user.is_authenticated:
        user_application = ResearchApplication.query.filter_by(
            project_id=project_id,
            student_id=current_user.id
        ).first()
        has_applied = user_application is not None
    
    # Parse skills
    import json
    required_skills = json.loads(project.required_skills) if project.required_skills else []
    preferred_skills = json.loads(project.preferred_skills) if project.preferred_skills else []
    skills_gained = json.loads(project.skills_students_will_gain) if project.skills_students_will_gain else []
    
    return render_template('research/project_detail.html',
                         project=project,
                         has_applied=has_applied,
                         user_application=user_application,
                         required_skills=required_skills,
                         preferred_skills=preferred_skills,
                         skills_gained=skills_gained)


@research_bp.route('/project/<int:project_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_to_project(project_id):
    """Apply to research project"""
    project = ResearchProject.query.get_or_404(project_id)
    
    # Check if already applied
    existing = ResearchApplication.query.filter_by(
        project_id=project_id,
        student_id=current_user.id
    ).first()
    
    if existing:
        flash('You have already applied to this project', 'warning')
        return redirect(url_for('research.view_project', project_id=project_id))
    
    if request.method == 'POST':
        data = request.form
        
        application = ResearchApplication(
            project_id=project_id,
            student_id=current_user.id,
            cover_letter=data.get('cover_letter'),
            relevant_coursework=data.get('relevant_coursework'),
            relevant_experience=data.get('relevant_experience'),
            skills_list=data.get('skills_list'),
            major=data.get('major'),
            minor=data.get('minor'),
            gpa=float(data.get('gpa')) if data.get('gpa') else None,
            class_standing=data.get('class_standing'),
            available_hours_per_week=int(data.get('available_hours_per_week')),
            preferred_start_date=datetime.strptime(data.get('preferred_start_date'), '%Y-%m-%d').date() if data.get('preferred_start_date') else None,
            availability_notes=data.get('availability_notes'),
            reference_name_1=data.get('reference_name_1'),
            reference_email_1=data.get('reference_email_1'),
            reference_name_2=data.get('reference_name_2'),
            reference_email_2=data.get('reference_email_2'),
            status='pending'
        )
        
        # AI matching score
        match_score, explanation = calculate_match_score(application, project)
        application.match_score = match_score
        application.match_explanation = explanation
        
        db.session.add(application)
        
        # Update project stats
        project.application_count += 1
        
        db.session.commit()
        
        flash('Your application has been submitted successfully!', 'success')
        return redirect(url_for('research.my_applications'))
    
    return render_template('research/apply.html', project=project)


@research_bp.route('/my-applications')
@login_required
def my_applications():
    """View student's research applications"""
    applications = ResearchApplication.query.filter_by(
        student_id=current_user.id
    ).order_by(ResearchApplication.applied_at.desc()).all()
    
    return render_template('research/my_applications.html', applications=applications)


@research_bp.route('/application/<int:app_id>')
@login_required
def view_application(app_id):
    """View specific application"""
    application = ResearchApplication.query.get_or_404(app_id)
    
    # Security check
    if application.student_id != current_user.id and application.project.faculty_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('research.browse_projects'))
    
    return render_template('research/application_detail.html', application=application)


@research_bp.route('/application/<int:app_id>/withdraw', methods=['POST'])
@login_required
def withdraw_application(app_id):
    """Withdraw application"""
    application = ResearchApplication.query.get_or_404(app_id)
    
    if application.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if application.status in ['accepted', 'rejected']:
        return jsonify({'error': 'Cannot withdraw accepted or rejected application'}), 400
    
    application.status = 'withdrawn'
    db.session.commit()
    
    flash('Application withdrawn', 'success')
    return redirect(url_for('research.my_applications'))


# ==================== FACULTY: MANAGE PROJECTS ====================

@research_bp.route('/faculty/my-projects')
@login_required
def faculty_my_projects():
    """Faculty dashboard for research projects"""
    projects = ResearchProject.query.filter_by(
        faculty_id=current_user.id
    ).order_by(ResearchProject.created_at.desc()).all()
    
    return render_template('research/faculty_dashboard.html', projects=projects)


@research_bp.route('/faculty/create-project', methods=['GET', 'POST'])
@login_required
def faculty_create_project():
    """Create new research project"""
    if request.method == 'POST':
        data = request.form
        
        import json
        
        project = ResearchProject(
            faculty_id=current_user.id,
            title=data.get('title'),
            description=data.get('description'),
            research_area=data.get('research_area'),
            specific_field=data.get('specific_field'),
            project_type=data.get('project_type'),
            project_duration=data.get('project_duration'),
            time_commitment=data.get('time_commitment'),
            required_skills=json.dumps(data.getlist('required_skills')),
            preferred_skills=json.dumps(data.getlist('preferred_skills')),
            required_courses=json.dumps(data.getlist('required_courses')),
            minimum_gpa=float(data.get('minimum_gpa')) if data.get('minimum_gpa') else None,
            class_standing=data.get('class_standing'),
            positions_available=int(data.get('positions_available', 1)),
            compensation_type=data.get('compensation_type'),
            credit_hours=int(data.get('credit_hours')) if data.get('credit_hours') else None,
            stipend_amount=float(data.get('stipend_amount')) if data.get('stipend_amount') else None,
            stipend_frequency=data.get('stipend_frequency'),
            skills_students_will_gain=json.dumps(data.getlist('skills_gained')),
            publication_potential=data.get('publication_potential') == 'true',
            conference_presentation_potential=data.get('conference_potential') == 'true',
            thesis_eligible=data.get('thesis_eligible') == 'true',
            start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date() if data.get('start_date') else None,
            end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date() if data.get('end_date') else None,
            application_deadline=datetime.strptime(data.get('application_deadline'), '%Y-%m-%d').date() if data.get('application_deadline') else None,
            is_ongoing=data.get('is_ongoing') == 'true',
            is_grant_funded=data.get('is_grant_funded') == 'true',
            grant_name=data.get('grant_name'),
            application_instructions=data.get('application_instructions'),
            required_documents=data.get('required_documents'),
            interview_required=data.get('interview_required') == 'true',
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            office_location=data.get('office_location'),
            office_hours=data.get('office_hours'),
            status='active'
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash('Research project created successfully!', 'success')
        return redirect(url_for('research.faculty_my_projects'))
    
    return render_template('research/create_project.html')


@research_bp.route('/faculty/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def faculty_edit_project(project_id):
    """Edit research project"""
    project = ResearchProject.query.get_or_404(project_id)
    
    if project.faculty_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('research.faculty_my_projects'))
    
    if request.method == 'POST':
        data = request.form
        
        import json
        
        project.title = data.get('title')
        project.description = data.get('description')
        project.research_area = data.get('research_area')
        project.specific_field = data.get('specific_field')
        project.project_type = data.get('project_type')
        project.time_commitment = data.get('time_commitment')
        project.positions_available = int(data.get('positions_available', 1))
        project.compensation_type = data.get('compensation_type')
        project.stipend_amount = float(data.get('stipend_amount')) if data.get('stipend_amount') else None
        project.application_deadline = datetime.strptime(data.get('application_deadline'), '%Y-%m-%d').date() if data.get('application_deadline') else None
        project.status = data.get('status', 'active')
        
        db.session.commit()
        
        flash('Project updated successfully', 'success')
        return redirect(url_for('research.faculty_my_projects'))
    
    return render_template('research/edit_project.html', project=project)


@research_bp.route('/faculty/project/<int:project_id>/applications')
@login_required
def faculty_view_applications(project_id):
    """View applications for project"""
    project = ResearchProject.query.get_or_404(project_id)
    
    if project.faculty_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('research.faculty_my_projects'))
    
    status_filter = request.args.get('status', 'all')
    
    query = ResearchApplication.query.filter_by(project_id=project_id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Sort by match score descending
    applications = query.order_by(
        ResearchApplication.match_score.desc()
    ).all()
    
    return render_template('research/faculty_applications.html',
                         project=project,
                         applications=applications,
                         current_status=status_filter)


@research_bp.route('/faculty/application/<int:app_id>/update', methods=['POST'])
@login_required
def faculty_update_application(app_id):
    """Update application status"""
    application = ResearchApplication.query.get_or_404(app_id)
    
    if application.project.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    
    application.status = data.get('status', application.status)
    application.faculty_notes = data.get('faculty_notes', application.faculty_notes)
    
    if data.get('status') == 'interview_scheduled':
        application.interview_scheduled = datetime.fromisoformat(data.get('interview_datetime'))
        application.interview_location = data.get('interview_location')
    
    if data.get('status') in ['accepted', 'rejected']:
        application.decision_date = datetime.utcnow()
        if data.get('status') == 'accepted':
            # Set acceptance deadline (7 days)
            application.acceptance_deadline = datetime.utcnow() + timedelta(days=7)
    
    if data.get('status') == 'rejected':
        application.rejection_reason = data.get('rejection_reason')
    
    db.session.commit()
    
    return jsonify({'success': True})


@research_bp.route('/faculty/application/<int:app_id>/hire', methods=['POST'])
@login_required
def faculty_hire_student(app_id):
    """Hire student for research project"""
    application = ResearchApplication.query.get_or_404(app_id)
    
    if application.project.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if application.status != 'accepted' or not application.student_accepted_offer:
        return jsonify({'error': 'Student must accept offer first'}), 400
    
    data = request.json
    
    # Create team member record
    team_member = ResearchTeamMember(
        project_id=application.project_id,
        student_id=application.student_id,
        role=data.get('role', 'Research Assistant'),
        start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
        is_active=True
    )
    
    db.session.add(team_member)
    
    # Update project team size
    application.project.current_team_size += 1
    
    # Check if all positions filled
    if application.project.current_team_size >= application.project.positions_available:
        application.project.status = 'filled'
    
    db.session.commit()
    
    return jsonify({'success': True})


@research_bp.route('/faculty/team/<int:project_id>')
@login_required
def faculty_view_team(project_id):
    """View research team members"""
    project = ResearchProject.query.get_or_404(project_id)
    
    if project.faculty_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('research.faculty_my_projects'))
    
    team_members = ResearchTeamMember.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()
    
    return render_template('research/faculty_team.html',
                         project=project,
                         team_members=team_members)


@research_bp.route('/student/accept-offer/<int:app_id>', methods=['POST'])
@login_required
def student_accept_offer(app_id):
    """Student accepts research position offer"""
    application = ResearchApplication.query.get_or_404(app_id)
    
    if application.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if application.status != 'accepted':
        return jsonify({'error': 'No active offer'}), 400
    
    application.student_accepted_offer = True
    db.session.commit()
    
    flash('Congratulations! You have accepted the research position.', 'success')
    return redirect(url_for('research.view_application', app_id=app_id))


# ==================== ADMIN: FEATURED PROJECTS ====================

@research_bp.route('/admin/feature-project/<int:project_id>', methods=['POST'])
@login_required
def admin_feature_project(project_id):
    """Feature a research project"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    project = ResearchProject.query.get_or_404(project_id)
    project.is_featured = not project.is_featured
    db.session.commit()
    
    return jsonify({'success': True, 'is_featured': project.is_featured})


# ==================== ANALYTICS ====================

@research_bp.route('/analytics')
@login_required
def research_analytics():
    """Research marketplace analytics"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('research.browse_projects'))
    
    # Get stats
    total_projects = ResearchProject.query.count()
    active_projects = ResearchProject.query.filter_by(status='active').count()
    total_applications = ResearchApplication.query.count()
    acceptance_rate = db.session.query(
        db.func.count(ResearchApplication.id)
    ).filter_by(status='accepted').scalar() / max(total_applications, 1) * 100
    
    # Projects by research area
    projects_by_area = db.session.query(
        ResearchProject.research_area,
        db.func.count(ResearchProject.id)
    ).group_by(ResearchProject.research_area).all()
    
    # Top faculty by applications
    top_faculty = db.session.query(
        ResearchProject.faculty_id,
        db.func.sum(ResearchProject.application_count).label('total_apps')
    ).group_by(ResearchProject.faculty_id).order_by(desc('total_apps')).limit(10).all()
    
    return render_template('research/analytics.html',
                         total_projects=total_projects,
                         active_projects=active_projects,
                         total_applications=total_applications,
                         acceptance_rate=acceptance_rate,
                         projects_by_area=projects_by_area,
                         top_faculty=top_faculty)


# ==================== HELPER FUNCTIONS ====================

def calculate_match_score(application, project):
    """AI-powered matching score (0-100)"""
    import json
    
    score = 0
    explanation_parts = []
    
    # GPA match (20 points)
    if application.gpa:
        if project.minimum_gpa and application.gpa >= project.minimum_gpa:
            gpa_points = min(20, (application.gpa - project.minimum_gpa) * 20)
            score += gpa_points
            explanation_parts.append(f"Strong academic record (GPA: {application.gpa})")
        elif not project.minimum_gpa:
            score += 15
    
    # Skills match (30 points)
    required_skills = json.loads(project.required_skills) if project.required_skills else []
    student_skills = application.skills_list.lower() if application.skills_list else ""
    
    if required_skills:
        matched_skills = [skill for skill in required_skills if skill.lower() in student_skills]
        skill_match_rate = len(matched_skills) / len(required_skills)
        skill_points = skill_match_rate * 30
        score += skill_points
        
        if matched_skills:
            explanation_parts.append(f"Has required skills: {', '.join(matched_skills[:3])}")
    else:
        score += 20  # No requirements = partial points
    
    # Experience relevance (25 points)
    if application.relevant_experience:
        exp_length = len(application.relevant_experience)
        if exp_length > 500:
            score += 25
            explanation_parts.append("Extensive relevant experience")
        elif exp_length > 200:
            score += 15
            explanation_parts.append("Good relevant experience")
        else:
            score += 10
    
    # Coursework alignment (15 points)
    if application.relevant_coursework:
        course_length = len(application.relevant_coursework)
        if course_length > 100:
            score += 15
            explanation_parts.append("Strong coursework background")
        else:
            score += 10
    
    # Availability match (10 points)
    if application.available_hours_per_week:
        if application.available_hours_per_week >= 15:
            score += 10
            explanation_parts.append("Excellent availability")
        elif application.available_hours_per_week >= 10:
            score += 7
        else:
            score += 5
    
    explanation = " • " + "\n • ".join(explanation_parts) if explanation_parts else "Basic qualifications met"
    
    return round(min(100, score), 2), explanation
