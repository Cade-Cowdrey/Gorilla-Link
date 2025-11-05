"""
Emergency Resources & Crisis Relief Center Routes
Comprehensive emergency support system for PSU students
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models_advanced_features import EmergencyResource, CrisisIntakeForm, CommunityFundDonation
from datetime import datetime, date
from sqlalchemy import or_, and_

emergency_bp = Blueprint('emergency', __name__, url_prefix='/emergency')

# ==================== EMERGENCY RESOURCE DIRECTORY ====================

@emergency_bp.route('/')
def directory():
    """Main emergency resources directory"""
    resource_type = request.args.get('type', 'all')
    search = request.args.get('search', '')
    
    query = EmergencyResource.query.filter_by(is_active=True)
    
    if resource_type != 'all':
        query = query.filter_by(resource_type=resource_type)
    
    if search:
        query = query.filter(
            or_(
                EmergencyResource.title.ilike(f'%{search}%'),
                EmergencyResource.description.ilike(f'%{search}%')
            )
        )
    
    # Crisis resources first, then by priority
    resources = query.order_by(
        EmergencyResource.is_crisis_resource.desc(),
        EmergencyResource.priority_level.desc()
    ).all()
    
    # Get 24/7 hotlines for header
    crisis_hotlines = EmergencyResource.query.filter_by(
        is_24_7=True,
        is_crisis_resource=True,
        is_active=True
    ).all()
    
    return render_template('emergency/directory.html',
                         resources=resources,
                         crisis_hotlines=crisis_hotlines,
                         current_type=resource_type)


@emergency_bp.route('/resource/<int:resource_id>')
def view_resource(resource_id):
    """View detailed resource information"""
    resource = EmergencyResource.query.get_or_404(resource_id)
    
    # Track view
    resource.view_count += 1
    db.session.commit()
    
    return render_template('emergency/resource_detail.html', resource=resource)


@emergency_bp.route('/resource/<int:resource_id>/refer')
@login_required
def track_referral(resource_id):
    """Track when student uses a resource"""
    resource = EmergencyResource.query.get_or_404(resource_id)
    resource.referral_count += 1
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== CRISIS INTAKE SYSTEM ====================

@emergency_bp.route('/help', methods=['GET', 'POST'])
@login_required
def crisis_intake():
    """Smart intake form for crisis situations"""
    if request.method == 'POST':
        data = request.form
        
        intake = CrisisIntakeForm(
            user_id=current_user.id,
            crisis_type=data.get('crisis_type'),
            urgency_level=data.get('urgency_level'),
            situation_description=data.get('situation_description'),
            immediate_needs=data.get('immediate_needs'),
            has_safe_housing=data.get('has_safe_housing') == 'true',
            has_food_access=data.get('has_food_access') == 'true',
            has_transportation=data.get('has_transportation') == 'true',
            has_medical_care=data.get('has_medical_care') == 'true',
            has_financial_resources=data.get('has_financial_resources') == 'true',
            dependents=int(data.get('dependents', 0)),
            estimated_cost_needed=float(data.get('estimated_cost_needed', 0)) if data.get('estimated_cost_needed') else None,
            timeline_needed=data.get('timeline_needed'),
            previous_help_received=data.get('previous_help_received'),
            other_resources_tried=data.get('other_resources_tried'),
            preferred_contact_method=data.get('preferred_contact_method'),
            best_time_to_contact=data.get('best_time_to_contact'),
            secondary_contact_name=data.get('secondary_contact_name'),
            secondary_contact_phone=data.get('secondary_contact_phone'),
            consent_to_share_info=data.get('consent_to_share_info') == 'true',
            status='pending'
        )
        
        # AI-powered resource matching
        matched_resources = match_resources_to_crisis(intake)
        intake.auto_matched_resources = str(matched_resources)
        
        # Auto-route based on crisis type
        intake.routed_to_department = route_to_department(intake.crisis_type)
        
        db.session.add(intake)
        db.session.commit()
        
        flash('Your request has been submitted. A support staff member will contact you within 24 hours. If this is an emergency, please call 911 or the PSU Campus Police at (620) 235-4624.', 'success')
        return redirect(url_for('emergency.my_requests'))
    
    return render_template('emergency/crisis_intake.html')


@emergency_bp.route('/my-requests')
@login_required
def my_requests():
    """View user's crisis intake requests"""
    intakes = CrisisIntakeForm.query.filter_by(
        user_id=current_user.id
    ).order_by(CrisisIntakeForm.submitted_at.desc()).all()
    
    return render_template('emergency/my_requests.html', intakes=intakes)


@emergency_bp.route('/request/<int:intake_id>')
@login_required
def view_request(intake_id):
    """View specific intake request"""
    intake = CrisisIntakeForm.query.get_or_404(intake_id)
    
    # Security: only requester or assigned staff can view
    if intake.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('emergency.my_requests'))
    
    # Parse matched resources
    import json
    matched_resources = []
    if intake.auto_matched_resources:
        resource_ids = json.loads(intake.auto_matched_resources)
        matched_resources = EmergencyResource.query.filter(
            EmergencyResource.id.in_(resource_ids)
        ).all()
    
    return render_template('emergency/request_detail.html',
                         intake=intake,
                         matched_resources=matched_resources)


# ==================== COMMUNITY FUND ====================

@emergency_bp.route('/community-fund')
def community_fund():
    """Community emergency fund landing page"""
    # Get recent donations (anonymous aggregated)
    total_raised = db.session.query(
        db.func.sum(CommunityFundDonation.amount)
    ).filter_by(payment_status='completed').scalar() or 0
    
    students_helped = db.session.query(
        db.func.sum(CommunityFundDonation.students_helped)
    ).filter_by(payment_status='completed').scalar() or 0
    
    recent_donors = CommunityFundDonation.query.filter_by(
        payment_status='completed',
        is_anonymous=False
    ).order_by(CommunityFundDonation.donated_at.desc()).limit(10).all()
    
    return render_template('emergency/community_fund.html',
                         total_raised=total_raised,
                         students_helped=students_helped,
                         recent_donors=recent_donors)


@emergency_bp.route('/donate', methods=['GET', 'POST'])
@login_required
def donate():
    """Process donation to emergency fund"""
    if request.method == 'POST':
        data = request.form
        
        donation = CommunityFundDonation(
            donor_id=current_user.id,
            amount=float(data.get('amount')),
            donation_type=data.get('donation_type', 'one_time'),
            designated_purpose=data.get('designated_purpose', 'general'),
            donor_name=data.get('donor_name') if not data.get('is_anonymous') else None,
            is_anonymous=data.get('is_anonymous') == 'true',
            donor_type=data.get('donor_type'),
            public_message=data.get('public_message'),
            payment_method=data.get('payment_method'),
            payment_status='pending'
        )
        
        # Calculate recognition level
        amount = float(data.get('amount'))
        if amount >= 10000:
            donation.recognition_level = 'platinum'
        elif amount >= 5000:
            donation.recognition_level = 'gold'
        elif amount >= 1000:
            donation.recognition_level = 'silver'
        else:
            donation.recognition_level = 'bronze'
        
        db.session.add(donation)
        db.session.commit()
        
        # In production, integrate with payment processor here
        # For now, mark as completed
        donation.payment_status = 'completed'
        donation.processed_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Thank you for your ${amount:,.2f} donation! You are helping PSU students in need.', 'success')
        return redirect(url_for('emergency.community_fund'))
    
    return render_template('emergency/donate.html')


# ==================== ADMIN: CRISIS MANAGEMENT ====================

@emergency_bp.route('/admin/manage-cases')
@login_required
def admin_manage_cases():
    """Admin dashboard for crisis case management"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('emergency.directory'))
    
    status_filter = request.args.get('status', 'pending')
    
    cases = CrisisIntakeForm.query
    if status_filter != 'all':
        cases = cases.filter_by(status=status_filter)
    
    cases = cases.order_by(
        CrisisIntakeForm.urgency_level == 'immediate',
        CrisisIntakeForm.urgency_level == 'urgent',
        CrisisIntakeForm.submitted_at.desc()
    ).all()
    
    return render_template('emergency/admin_cases.html', cases=cases, current_status=status_filter)


@emergency_bp.route('/admin/case/<int:case_id>/update', methods=['POST'])
@login_required
def admin_update_case(case_id):
    """Update crisis case status"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    intake = CrisisIntakeForm.query.get_or_404(case_id)
    data = request.json
    
    intake.status = data.get('status', intake.status)
    intake.assigned_to_staff_id = data.get('assigned_to_staff_id', intake.assigned_to_staff_id)
    intake.resolution_notes = data.get('resolution_notes', intake.resolution_notes)
    intake.assistance_provided = data.get('assistance_provided', intake.assistance_provided)
    intake.follow_up_required = data.get('follow_up_required', False)
    
    if intake.status in ['assistance_provided', 'resolved', 'closed']:
        intake.resolved_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})


@emergency_bp.route('/admin/resources/manage')
@login_required
def admin_manage_resources():
    """Manage emergency resources"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('emergency.directory'))
    
    resources = EmergencyResource.query.order_by(
        EmergencyResource.priority_level.desc()
    ).all()
    
    return render_template('emergency/admin_resources.html', resources=resources)


@emergency_bp.route('/admin/resources/add', methods=['POST'])
@login_required
def admin_add_resource():
    """Add new emergency resource"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form
    
    resource = EmergencyResource(
        resource_type=data.get('resource_type'),
        title=data.get('title'),
        description=data.get('description'),
        phone_number=data.get('phone_number'),
        emergency_hotline=data.get('emergency_hotline'),
        email=data.get('email'),
        website=data.get('website'),
        physical_address=data.get('physical_address'),
        hours_of_operation=data.get('hours_of_operation'),
        is_24_7=data.get('is_24_7') == 'true',
        is_crisis_resource=data.get('is_crisis_resource') == 'true',
        priority_level=int(data.get('priority_level', 0)),
        is_psu_operated=data.get('is_psu_operated') == 'true',
        is_active=True,
        last_verified=datetime.utcnow()
    )
    
    db.session.add(resource)
    db.session.commit()
    
    flash('Emergency resource added successfully', 'success')
    return redirect(url_for('emergency.admin_manage_resources'))


# ==================== HELPER FUNCTIONS ====================

def match_resources_to_crisis(intake):
    """AI-powered resource matching"""
    import json
    matched_ids = []
    
    # Match based on crisis type
    type_mapping = {
        'financial': ['financial_aid', 'food_assistance'],
        'housing': ['housing_emergency'],
        'food_insecurity': ['food_assistance'],
        'mental_health': ['mental_health'],
        'medical': ['medical'],
        'academic': ['academic_crisis'],
        'family_emergency': ['financial_aid', 'housing_emergency'],
        'safety_concern': ['legal_aid', 'domestic_violence']
    }
    
    resource_types = type_mapping.get(intake.crisis_type, [])
    if resource_types:
        resources = EmergencyResource.query.filter(
            EmergencyResource.resource_type.in_(resource_types),
            EmergencyResource.is_active == True
        ).all()
        matched_ids = [r.id for r in resources]
    
    return matched_ids


def route_to_department(crisis_type):
    """Route intake to appropriate department"""
    routing = {
        'financial': 'Financial Aid Office',
        'housing': 'Student Housing & Residence Life',
        'food_insecurity': 'Gorilla Food Pantry',
        'mental_health': 'Counseling Services',
        'medical': 'Student Health Center',
        'academic': 'Academic Advising',
        'family_emergency': 'Dean of Students',
        'safety_concern': 'Campus Police & Title IX',
        'other': 'Student Affairs'
    }
    return routing.get(crisis_type, 'Dean of Students')
