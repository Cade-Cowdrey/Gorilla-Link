"""
Global PSU Collaboration Network Routes
International student support and virtual exchange programs
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models_advanced_features import (InternationalStudentProfile, GlobalAlumniMapping, 
                                     VirtualExchangeProgram, VirtualExchangeParticipant)
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, desc, func

global_network_bp = Blueprint('global_network', __name__, url_prefix='/global')

# ==================== INTERNATIONAL STUDENT SUPPORT ====================

@global_network_bp.route('/international')
def international_hub():
    """Main international student resource hub"""
    # Get stats
    total_intl_students = InternationalStudentProfile.query.filter_by(is_active=True).count()
    countries_represented = db.session.query(
        func.count(func.distinct(InternationalStudentProfile.home_country))
    ).scalar() or 0
    
    # Get students needing support
    needs_support = InternationalStudentProfile.query.filter(
        or_(
            InternationalStudentProfile.needs_visa_guidance == True,
            InternationalStudentProfile.needs_cultural_adjustment_support == True,
            InternationalStudentProfile.needs_language_support == True
        )
    ).count()
    
    return render_template('global/international_hub.html',
                         total_intl_students=total_intl_students,
                         countries_represented=countries_represented,
                         needs_support=needs_support)


@global_network_bp.route('/international/profile/create', methods=['GET', 'POST'])
@login_required
def create_intl_profile():
    """Create international student profile"""
    # Check if exists
    existing = InternationalStudentProfile.query.filter_by(user_id=current_user.id).first()
    if existing:
        return redirect(url_for('global_network.edit_intl_profile'))
    
    if request.method == 'POST':
        data = request.form
        
        import json
        
        profile = InternationalStudentProfile(
            user_id=current_user.id,
            home_country=data.get('home_country'),
            home_city=data.get('home_city'),
            native_language=data.get('native_language'),
            additional_languages=json.dumps(data.getlist('additional_languages')),
            visa_type=data.get('visa_type'),
            visa_expiration=datetime.strptime(data.get('visa_expiration'), '%Y-%m-%d').date() if data.get('visa_expiration') else None,
            i20_expiration=datetime.strptime(data.get('i20_expiration'), '%Y-%m-%d').date() if data.get('i20_expiration') else None,
            opt_status=data.get('opt_status', 'none'),
            program_start_date=datetime.strptime(data.get('program_start_date'), '%Y-%m-%d').date() if data.get('program_start_date') else None,
            expected_graduation=datetime.strptime(data.get('expected_graduation'), '%Y-%m-%d').date() if data.get('expected_graduation') else None,
            needs_cultural_adjustment_support=data.get('needs_cultural_adjustment_support') == 'true',
            needs_language_support=data.get('needs_language_support') == 'true',
            needs_visa_guidance=data.get('needs_visa_guidance') == 'true',
            needs_tax_assistance=data.get('needs_tax_assistance') == 'true',
            needs_employment_authorization_help=data.get('needs_employment_authorization_help') == 'true',
            wants_to_share_culture=data.get('wants_to_share_culture') == 'true',
            willing_to_mentor_new_students=data.get('willing_to_mentor_new_students') == 'true',
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_relationship=data.get('emergency_contact_relationship'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            emergency_contact_email=data.get('emergency_contact_email'),
            is_active=True
        )
        
        db.session.add(profile)
        db.session.commit()
        
        # Auto-assign mentor if available
        assign_mentor(profile)
        
        flash('International student profile created!', 'success')
        return redirect(url_for('global_network.my_intl_profile'))
    
    return render_template('global/create_intl_profile.html')


@global_network_bp.route('/international/profile/my')
@login_required
def my_intl_profile():
    """View my international student profile"""
    profile = InternationalStudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        return redirect(url_for('global_network.create_intl_profile'))
    
    # Check for expiring documents
    today = date.today()
    alerts = []
    
    if profile.visa_expiration and profile.visa_expiration - today < timedelta(days=90):
        alerts.append(('warning', f'Visa expires in {(profile.visa_expiration - today).days} days'))
    
    if profile.i20_expiration and profile.i20_expiration - today < timedelta(days=60):
        alerts.append(('warning', f'I-20 expires in {(profile.i20_expiration - today).days} days'))
    
    if profile.opt_expiration and profile.opt_expiration - today < timedelta(days=60):
        alerts.append(('danger', f'OPT expires in {(profile.opt_expiration - today).days} days'))
    
    return render_template('global/my_intl_profile.html',
                         profile=profile,
                         alerts=alerts)


@global_network_bp.route('/international/students')
def browse_intl_students():
    """Browse international students (for networking)"""
    country = request.args.get('country', 'all')
    language = request.args.get('language', 'all')
    
    query = InternationalStudentProfile.query.filter_by(is_active=True)
    
    if country != 'all':
        query = query.filter_by(home_country=country)
    
    if language != 'all':
        query = query.filter_by(native_language=language)
    
    profiles = query.all()
    
    # Get unique countries and languages for filters
    countries = db.session.query(InternationalStudentProfile.home_country).distinct().all()
    languages = db.session.query(InternationalStudentProfile.native_language).distinct().all()
    
    countries_list = sorted([c[0] for c in countries])
    languages_list = sorted([l[0] for l in languages])
    
    return render_template('global/browse_intl_students.html',
                         profiles=profiles,
                         countries_list=countries_list,
                         languages_list=languages_list,
                         current_country=country,
                         current_language=language)


# ==================== GLOBAL ALUMNI NETWORK ====================

@global_network_bp.route('/alumni/map')
def alumni_map():
    """Interactive global alumni map"""
    # Get all alumni locations
    alumni = GlobalAlumniMapping.query.filter_by(
        show_on_public_map=True
    ).all()
    
    # Group by country
    by_country = {}
    for alum in alumni:
        country = alum.current_country
        if country not in by_country:
            by_country[country] = []
        by_country[country].append(alum)
    
    # Get stats
    total_alumni = GlobalAlumniMapping.query.count()
    countries_count = db.session.query(
        func.count(func.distinct(GlobalAlumniMapping.current_country))
    ).scalar() or 0
    
    open_to_networking = GlobalAlumniMapping.query.filter_by(
        open_to_networking=True
    ).count()
    
    return render_template('global/alumni_map.html',
                         alumni=alumni,
                         by_country=by_country,
                         total_alumni=total_alumni,
                         countries_count=countries_count,
                         open_to_networking=open_to_networking)


@global_network_bp.route('/alumni/add-location', methods=['GET', 'POST'])
@login_required
def alumni_add_location():
    """Alumni adds their current location"""
    # Check if exists
    existing = GlobalAlumniMapping.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        data = request.form
        
        import json
        
        if existing:
            # Update existing
            alum = existing
        else:
            # Create new
            alum = GlobalAlumniMapping(user_id=current_user.id)
        
        alum.current_country = data.get('current_country')
        alum.current_city = data.get('current_city')
        alum.current_state_province = data.get('current_state_province')
        alum.graduation_year = int(data.get('graduation_year')) if data.get('graduation_year') else None
        alum.degree_earned = data.get('degree_earned')
        alum.major = data.get('major')
        alum.current_employer = data.get('current_employer')
        alum.current_job_title = data.get('current_job_title')
        alum.industry = data.get('industry')
        alum.open_to_networking = data.get('open_to_networking') == 'true'
        alum.offers_career_advice = data.get('offers_career_advice') == 'true'
        alum.offers_informational_interviews = data.get('offers_informational_interviews') == 'true'
        alum.can_help_with_relocation = data.get('can_help_with_relocation') == 'true'
        alum.speaks_languages = json.dumps(data.getlist('speaks_languages'))
        alum.show_on_public_map = data.get('show_on_public_map') == 'true'
        alum.show_employer = data.get('show_employer') == 'true'
        alum.show_exact_location = data.get('show_exact_location') == 'true'
        alum.last_updated_location = datetime.utcnow()
        
        if not existing:
            db.session.add(alum)
        
        db.session.commit()
        
        flash('Alumni profile updated!', 'success')
        return redirect(url_for('global_network.alumni_map'))
    
    return render_template('global/add_alumni_location.html', existing=existing)


@global_network_bp.route('/alumni/in/<country>')
def alumni_in_country(country):
    """View alumni in specific country"""
    alumni = GlobalAlumniMapping.query.filter_by(
        current_country=country,
        show_on_public_map=True
    ).all()
    
    # Get cities in this country
    cities = db.session.query(
        GlobalAlumniMapping.current_city,
        func.count(GlobalAlumniMapping.id).label('count')
    ).filter_by(current_country=country).group_by(
        GlobalAlumniMapping.current_city
    ).order_by(desc('count')).all()
    
    return render_template('global/alumni_country.html',
                         country=country,
                         alumni=alumni,
                         cities=cities)


# ==================== VIRTUAL EXCHANGE PROGRAMS ====================

@global_network_bp.route('/exchange')
def virtual_exchange():
    """Browse virtual exchange programs"""
    program_type = request.args.get('type', 'all')
    subject = request.args.get('subject', 'all')
    
    query = VirtualExchangeProgram.query.filter_by(status='active')
    
    if program_type != 'all':
        query = query.filter_by(program_type=program_type)
    
    if subject != 'all':
        query = query.filter_by(subject_area=subject)
    
    programs = query.order_by(
        VirtualExchangeProgram.is_featured.desc(),
        VirtualExchangeProgram.application_deadline
    ).all()
    
    # Stats
    total_programs = VirtualExchangeProgram.query.filter_by(status='active').count()
    partner_universities = db.session.query(
        func.count(func.distinct(VirtualExchangeProgram.partner_university))
    ).scalar() or 0
    total_participants = VirtualExchangeParticipant.query.count()
    
    return render_template('global/virtual_exchange.html',
                         programs=programs,
                         total_programs=total_programs,
                         partner_universities=partner_universities,
                         total_participants=total_participants,
                         current_type=program_type,
                         current_subject=subject)


@global_network_bp.route('/exchange/<int:program_id>')
def view_exchange_program(program_id):
    """View virtual exchange program details"""
    program = VirtualExchangeProgram.query.get_or_404(program_id)
    
    # Check if user already enrolled
    is_enrolled = False
    if current_user.is_authenticated:
        is_enrolled = VirtualExchangeParticipant.query.filter_by(
            program_id=program_id,
            student_id=current_user.id
        ).first() is not None
    
    # Get current participants count
    current_participants = VirtualExchangeParticipant.query.filter_by(
        program_id=program_id
    ).count()
    
    import json
    
    learning_objectives = program.learning_objectives.split('\n') if program.learning_objectives else []
    skills_gained = json.loads(program.skills_gained) if program.skills_gained else []
    
    return render_template('global/exchange_program_detail.html',
                         program=program,
                         is_enrolled=is_enrolled,
                         current_participants=current_participants,
                         learning_objectives=learning_objectives,
                         skills_gained=skills_gained)


@global_network_bp.route('/exchange/<int:program_id>/enroll', methods=['POST'])
@login_required
def enroll_exchange_program(program_id):
    """Enroll in virtual exchange program"""
    program = VirtualExchangeProgram.query.get_or_404(program_id)
    
    # Check if already enrolled
    existing = VirtualExchangeParticipant.query.filter_by(
        program_id=program_id,
        student_id=current_user.id
    ).first()
    
    if existing:
        flash('You are already enrolled in this program', 'warning')
        return redirect(url_for('global_network.view_exchange_program', program_id=program_id))
    
    # Check capacity
    if program.current_psu_enrollment >= program.psu_student_capacity:
        flash('This program is full', 'error')
        return redirect(url_for('global_network.view_exchange_program', program_id=program_id))
    
    # Create participant
    participant = VirtualExchangeParticipant(
        program_id=program_id,
        student_id=current_user.id,
        role='participant',
        total_sessions=10  # Default, would be calculated
    )
    
    db.session.add(participant)
    
    # Update enrollment count
    program.current_psu_enrollment += 1
    
    db.session.commit()
    
    flash('Successfully enrolled in virtual exchange program!', 'success')
    return redirect(url_for('global_network.my_exchange_programs'))


@global_network_bp.route('/exchange/my-programs')
@login_required
def my_exchange_programs():
    """View my enrolled exchange programs"""
    participations = VirtualExchangeParticipant.query.filter_by(
        student_id=current_user.id
    ).all()
    
    return render_template('global/my_exchange_programs.html',
                         participations=participations)


# ==================== FACULTY: MANAGE EXCHANGE PROGRAMS ====================

@global_network_bp.route('/faculty/exchange/create', methods=['GET', 'POST'])
@login_required
def faculty_create_exchange():
    """Faculty creates virtual exchange program"""
    if request.method == 'POST':
        data = request.form
        
        import json
        
        program = VirtualExchangeProgram(
            program_name=data.get('program_name'),
            program_type=data.get('program_type'),
            description=data.get('description'),
            partner_university=data.get('partner_university'),
            partner_country=data.get('partner_country'),
            partner_city=data.get('partner_city'),
            partner_department=data.get('partner_department'),
            subject_area=data.get('subject_area'),
            course_code_psu=data.get('course_code_psu'),
            credit_hours=int(data.get('credit_hours')) if data.get('credit_hours') else None,
            academic_level=data.get('academic_level'),
            duration=data.get('duration'),
            meeting_frequency=data.get('meeting_frequency'),
            time_commitment_hours_per_week=int(data.get('time_commitment_hours_per_week')) if data.get('time_commitment_hours_per_week') else None,
            platform_used=data.get('platform_used'),
            platform_url=data.get('platform_url'),
            application_deadline=datetime.strptime(data.get('application_deadline'), '%Y-%m-%d').date() if data.get('application_deadline') else None,
            program_start_date=datetime.strptime(data.get('program_start_date'), '%Y-%m-%d').date() if data.get('program_start_date') else None,
            program_end_date=datetime.strptime(data.get('program_end_date'), '%Y-%m-%d').date() if data.get('program_end_date') else None,
            psu_student_capacity=int(data.get('psu_student_capacity', 20)),
            partner_student_capacity=int(data.get('partner_student_capacity', 20)),
            language_requirements=data.get('language_requirements'),
            learning_objectives=data.get('learning_objectives'),
            skills_gained=json.dumps(data.getlist('skills_gained')),
            psu_faculty_coordinator_id=current_user.id,
            partner_faculty_name=data.get('partner_faculty_name'),
            partner_faculty_email=data.get('partner_faculty_email'),
            final_project_required=data.get('final_project_required') == 'true',
            is_funded=data.get('is_funded') == 'true',
            funding_source=data.get('funding_source'),
            student_cost=float(data.get('student_cost', 0)),
            status='active'
        )
        
        db.session.add(program)
        db.session.commit()
        
        flash('Virtual exchange program created!', 'success')
        return redirect(url_for('global_network.virtual_exchange'))
    
    return render_template('global/create_exchange_program.html')


# ==================== ADMIN ====================

@global_network_bp.route('/admin/intl-students')
@login_required
def admin_intl_students():
    """Admin dashboard for international students"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('global_network.international_hub'))
    
    # Students needing attention
    urgent = InternationalStudentProfile.query.filter(
        or_(
            InternationalStudentProfile.visa_expiration <= date.today() + timedelta(days=90),
            InternationalStudentProfile.i20_expiration <= date.today() + timedelta(days=60),
            InternationalStudentProfile.opt_expiration <= date.today() + timedelta(days=60)
        ),
        InternationalStudentProfile.is_active == True
    ).all()
    
    # Students needing support
    needs_support = InternationalStudentProfile.query.filter(
        or_(
            InternationalStudentProfile.needs_visa_guidance == True,
            InternationalStudentProfile.needs_cultural_adjustment_support == True,
            InternationalStudentProfile.needs_language_support == True,
            InternationalStudentProfile.needs_tax_assistance == True
        )
    ).all()
    
    # Students without mentors
    no_mentor = InternationalStudentProfile.query.filter_by(
        has_mentor=False,
        is_active=True
    ).all()
    
    return render_template('global/admin_intl_students.html',
                         urgent=urgent,
                         needs_support=needs_support,
                         no_mentor=no_mentor)


# ==================== HELPER FUNCTIONS ====================

def assign_mentor(profile):
    """Auto-assign mentor to international student"""
    # Find mentor from same country who is willing
    potential_mentors = InternationalStudentProfile.query.filter_by(
        home_country=profile.home_country,
        willing_to_mentor_new_students=True,
        is_active=True
    ).filter(
        InternationalStudentProfile.user_id != profile.user_id
    ).all()
    
    # Find mentor with fewest mentees
    if potential_mentors:
        best_mentor = min(
            potential_mentors,
            key=lambda m: InternationalStudentProfile.query.filter_by(
                mentor_id=m.user_id
            ).count()
        )
        
        profile.mentor_id = best_mentor.user_id
        profile.has_mentor = True
        profile.mentor_match_date = date.today()
        db.session.commit()
