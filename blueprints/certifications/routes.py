"""
Certifications Routes - Browse and track free certifications
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import bp
from models import db
from models_growth_features import (
    FreeCertification, UserCertificationProgress, 
    CertificationPathway, UserPathwayProgress
)
from datetime import datetime
from sqlalchemy import func


@bp.route('/')
def index():
    """Browse all free certifications"""
    # Get filter parameters
    category = request.args.get('category', 'all')
    provider = request.args.get('provider', 'all')
    difficulty = request.args.get('difficulty', 'all')
    sort_by = request.args.get('sort', 'popularity')
    
    # Base query
    query = FreeCertification.query
    
    # Apply filters
    if category != 'all':
        query = query.filter_by(category=category)
    if provider != 'all':
        query = query.filter_by(provider=provider)
    if difficulty != 'all':
        query = query.filter_by(difficulty_level=difficulty)
    
    # Apply sorting
    if sort_by == 'popularity':
        query = query.order_by(FreeCertification.resume_boost_score.desc())
    elif sort_by == 'duration_asc':
        query = query.order_by(FreeCertification.duration_hours.asc())
    elif sort_by == 'duration_desc':
        query = query.order_by(FreeCertification.duration_hours.desc())
    elif sort_by == 'salary':
        query = query.order_by(FreeCertification.estimated_salary_boost.desc().nullslast())
    
    certifications = query.all()
    
    # Get all unique categories and providers for filters
    categories = db.session.query(FreeCertification.category).distinct().all()
    categories = [c[0] for c in categories]
    
    providers = db.session.query(FreeCertification.provider).distinct().all()
    providers = [p[0] for p in providers]
    
    # Get user's enrollments if logged in
    user_enrollments = {}
    if current_user.is_authenticated:
        enrollments = UserCertificationProgress.query.filter_by(
            user_id=current_user.id
        ).all()
        user_enrollments = {e.certification_id: e for e in enrollments}
    
    # Get featured pathways
    featured_pathways = CertificationPathway.query.filter_by(
        is_featured=True
    ).limit(3).all()
    
    # Calculate totals
    total_value = sum(cert.estimated_salary_boost or 0 for cert in FreeCertification.query.all())
    total_certs = FreeCertification.query.count()
    
    return render_template('certifications/index.html',
                         certifications=certifications,
                         categories=categories,
                         providers=providers,
                         user_enrollments=user_enrollments,
                         featured_pathways=featured_pathways,
                         selected_category=category,
                         selected_provider=provider,
                         selected_difficulty=difficulty,
                         sort_by=sort_by,
                         total_value=total_value,
                         total_certs=total_certs)


@bp.route('/<int:id>')
def detail(id):
    """View certification details"""
    cert = FreeCertification.query.get_or_404(id)
    
    # Get user progress if logged in
    user_progress = None
    if current_user.is_authenticated:
        user_progress = UserCertificationProgress.query.filter_by(
            user_id=current_user.id,
            certification_id=id
        ).first()
    
    # Get related certifications (same category)
    related = FreeCertification.query.filter(
        FreeCertification.category == cert.category,
        FreeCertification.id != id
    ).limit(3).all()
    
    # Get pathways containing this certification
    pathways = CertificationPathway.query.filter(
        CertificationPathway.certification_sequence.contains([id])
    ).all()
    
    return render_template('certifications/detail.html',
                         cert=cert,
                         user_progress=user_progress,
                         related=related,
                         pathways=pathways)


@bp.route('/<int:id>/enroll', methods=['POST'])
@login_required
def enroll(id):
    """Enroll in a certification"""
    cert = FreeCertification.query.get_or_404(id)
    
    # Check if already enrolled
    existing = UserCertificationProgress.query.filter_by(
        user_id=current_user.id,
        certification_id=id
    ).first()
    
    if existing:
        flash('You are already enrolled in this certification!', 'info')
        return redirect(url_for('certifications.detail', id=id))
    
    # Create enrollment
    progress = UserCertificationProgress(
        user_id=current_user.id,
        certification_id=id,
        status='in_progress',
        progress_percentage=0,
        started_at=datetime.utcnow()
    )
    
    db.session.add(progress)
    db.session.commit()
    
    flash(f'Successfully enrolled in {cert.title}! Start learning now.', 'success')
    return redirect(url_for('certifications.my_progress'))


@bp.route('/<int:id>/update-progress', methods=['POST'])
@login_required
def update_progress(id):
    """Update certification progress"""
    progress = UserCertificationProgress.query.filter_by(
        user_id=current_user.id,
        certification_id=id
    ).first_or_404()
    
    data = request.get_json()
    
    # Update progress
    if 'progress_percentage' in data:
        progress.progress_percentage = min(100, max(0, int(data['progress_percentage'])))
    
    if 'notes' in data:
        progress.notes = data['notes']
    
    # Check if completed (100% progress)
    if progress.progress_percentage == 100 and not progress.completed_at:
        progress.status = 'completed'
        progress.completed_at = datetime.utcnow()
    
    progress.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'progress': progress.progress_percentage,
        'status': progress.status
    })


@bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    """Mark certification as completed and upload certificate"""
    progress = UserCertificationProgress.query.filter_by(
        user_id=current_user.id,
        certification_id=id
    ).first_or_404()
    
    # Get certificate URL from form
    certificate_url = request.form.get('certificate_url')
    
    # Mark as completed
    progress.status = 'completed'
    progress.progress_percentage = 100
    progress.completed_at = datetime.utcnow()
    
    if certificate_url:
        progress.certificate_url = certificate_url
    
    # Option to add to resume
    add_to_resume = request.form.get('add_to_resume') == 'true'
    if add_to_resume:
        progress.added_to_resume = True
    
    db.session.commit()
    
    flash(f'🎉 Congratulations! You completed {progress.certification.title}!', 'success')
    return redirect(url_for('certifications.my_progress'))


@bp.route('/my-certifications')
@login_required
def my_progress():
    """View user's certification progress"""
    # Get user's enrollments
    in_progress = UserCertificationProgress.query.filter_by(
        user_id=current_user.id,
        status='in_progress'
    ).all()
    
    completed = UserCertificationProgress.query.filter_by(
        user_id=current_user.id,
        status='completed'
    ).all()
    
    # Calculate stats
    total_hours_completed = sum(
        c.certification.duration_hours for c in completed
    )
    
    total_value = sum(
        c.certification.estimated_salary_boost or 0 for c in completed
    )
    
    # Get pathway progress
    pathway_progress = UserPathwayProgress.query.filter_by(
        user_id=current_user.id
    ).all()
    
    # Get recommended certifications based on major/interests
    recommendations = get_recommendations(current_user)
    
    return render_template('certifications/my_progress.html',
                         in_progress=in_progress,
                         completed=completed,
                         total_hours_completed=total_hours_completed,
                         total_value=total_value,
                         pathway_progress=pathway_progress,
                         recommendations=recommendations)


@bp.route('/pathways')
def pathways():
    """Browse all certification pathways"""
    category = request.args.get('category', 'all')
    
    query = CertificationPathway.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    pathways = query.order_by(CertificationPathway.is_featured.desc()).all()
    
    # Get categories
    categories = db.session.query(CertificationPathway.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('certifications/pathways.html',
                         pathways=pathways,
                         categories=categories,
                         selected_category=category)


@bp.route('/pathways/<int:id>')
def pathway_detail(id):
    """View pathway details"""
    pathway = CertificationPathway.query.get_or_404(id)
    
    # Get certifications in pathway
    pathway_certs = FreeCertification.query.filter(
        FreeCertification.id.in_(pathway.certification_sequence)
    ).all()
    
    # Sort by pathway sequence
    cert_dict = {c.id: c for c in pathway_certs}
    ordered_certs = [cert_dict[id] for id in pathway.certification_sequence if id in cert_dict]
    
    # Get user progress if logged in
    user_pathway_progress = None
    user_cert_progress = {}
    
    if current_user.is_authenticated:
        user_pathway_progress = UserPathwayProgress.query.filter_by(
            user_id=current_user.id,
            pathway_id=id
        ).first()
        
        # Get progress on individual certifications
        cert_progress = UserCertificationProgress.query.filter_by(
            user_id=current_user.id
        ).filter(
            UserCertificationProgress.certification_id.in_(pathway.certification_sequence)
        ).all()
        
        user_cert_progress = {cp.certification_id: cp for cp in cert_progress}
    
    return render_template('certifications/pathway_detail.html',
                         pathway=pathway,
                         ordered_certs=ordered_certs,
                         user_pathway_progress=user_pathway_progress,
                         user_cert_progress=user_cert_progress)


@bp.route('/pathways/<int:id>/enroll', methods=['POST'])
@login_required
def enroll_pathway(id):
    """Enroll in a certification pathway"""
    pathway = CertificationPathway.query.get_or_404(id)
    
    # Check if already enrolled
    existing = UserPathwayProgress.query.filter_by(
        user_id=current_user.id,
        pathway_id=id
    ).first()
    
    if existing:
        flash('You are already enrolled in this pathway!', 'info')
        return redirect(url_for('certifications.pathway_detail', id=id))
    
    # Create pathway enrollment
    pathway_progress = UserPathwayProgress(
        user_id=current_user.id,
        pathway_id=id,
        certifications_completed=0,
        overall_progress=0,
        pathway_started_at=datetime.utcnow()
    )
    
    db.session.add(pathway_progress)
    
    # Enroll in first certification if not already enrolled
    if pathway.certification_sequence:
        first_cert_id = pathway.certification_sequence[0]
        existing_cert = UserCertificationProgress.query.filter_by(
            user_id=current_user.id,
            certification_id=first_cert_id
        ).first()
        
        if not existing_cert:
            cert_progress = UserCertificationProgress(
                user_id=current_user.id,
                certification_id=first_cert_id,
                status='in_progress',
                progress_percentage=0,
                started_at=datetime.utcnow()
            )
            db.session.add(cert_progress)
    
    db.session.commit()
    
    flash(f'Successfully enrolled in {pathway.title} pathway!', 'success')
    return redirect(url_for('certifications.pathway_detail', id=id))


@bp.route('/api/search')
def api_search():
    """API endpoint for certification search"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    results = FreeCertification.query.filter(
        db.or_(
            FreeCertification.title.ilike(f'%{query}%'),
            FreeCertification.provider.ilike(f'%{query}%'),
            FreeCertification.description.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': cert.id,
        'title': cert.title,
        'provider': cert.provider,
        'category': cert.category,
        'duration_hours': cert.duration_hours,
        'difficulty_level': cert.difficulty_level
    } for cert in results])


def get_recommendations(user):
    """Get certification recommendations based on user profile"""
    # Get user's major if available
    user_major = getattr(user, 'major', None)
    
    # Get certifications user hasn't enrolled in
    enrolled_ids = [
        e.certification_id 
        for e in UserCertificationProgress.query.filter_by(user_id=user.id).all()
    ]
    
    query = FreeCertification.query.filter(
        ~FreeCertification.id.in_(enrolled_ids) if enrolled_ids else True
    )
    
    # Filter by major if available
    if user_major:
        query = query.filter(
            FreeCertification.recommended_for_majors.contains([user_major])
        )
    
    # Get top recommendations by resume boost score
    recommendations = query.order_by(
        FreeCertification.resume_boost_score.desc()
    ).limit(6).all()
    
    # If no major-specific recommendations, get popular ones
    if not recommendations:
        recommendations = FreeCertification.query.filter(
            ~FreeCertification.id.in_(enrolled_ids) if enrolled_ids else True
        ).filter_by(
            is_featured=True
        ).order_by(
            FreeCertification.resume_boost_score.desc()
        ).limit(6).all()
    
    return recommendations
