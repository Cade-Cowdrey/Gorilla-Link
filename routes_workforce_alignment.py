"""
Workforce & Employer Alignment Hub Routes
Career pathways, salary data, and skill demand forecasting
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models_advanced_features import CareerPathway, SkillDemandForecast, FacultyIndustryCollaboration
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, desc, func

workforce_bp = Blueprint('workforce', __name__, url_prefix='/workforce')

# ==================== CAREER PATHWAY EXPLORER ====================

@workforce_bp.route('/')
def career_pathways():
    """Main career alignment dashboard"""
    major = request.args.get('major', '')
    field = request.args.get('field', 'all')
    
    query = CareerPathway.query
    
    if major:
        query = query.filter_by(major=major)
    
    if field != 'all':
        query = query.filter_by(career_field=field)
    
    pathways = query.order_by(
        CareerPathway.regional_median_salary.desc()
    ).all()
    
    # Get unique majors for filter
    all_majors = db.session.query(CareerPathway.major).distinct().all()
    majors_list = sorted([m[0] for m in all_majors])
    
    return render_template('workforce/career_pathways.html',
                         pathways=pathways,
                         majors_list=majors_list,
                         current_major=major,
                         current_field=field)


@workforce_bp.route('/pathway/<int:pathway_id>')
def view_pathway(pathway_id):
    """Detailed career pathway information"""
    pathway = CareerPathway.query.get_or_404(pathway_id)
    
    import json
    
    # Parse JSON fields
    required_skills = json.loads(pathway.required_skills) if pathway.required_skills else []
    courses_map = json.loads(pathway.psu_courses_that_teach_skills) if pathway.psu_courses_that_teach_skills else {}
    skill_gaps = json.loads(pathway.skill_gaps) if pathway.skill_gaps else []
    certifications = json.loads(pathway.recommended_certifications) if pathway.recommended_certifications else []
    career_progression = json.loads(pathway.typical_career_progression) if pathway.typical_career_progression else []
    top_employers = json.loads(pathway.top_employers) if pathway.top_employers else []
    alumni_at_employers = json.loads(pathway.psu_alumni_at_employers) if pathway.psu_alumni_at_employers else {}
    top_cities = json.loads(pathway.top_hiring_cities) if pathway.top_hiring_cities else []
    
    # Get related skill demand data
    skill_demands = []
    if required_skills:
        skill_demands = SkillDemandForecast.query.filter(
            SkillDemandForecast.skill_name.in_(required_skills[:5])
        ).order_by(SkillDemandForecast.current_demand_score.desc()).limit(5).all()
    
    return render_template('workforce/pathway_detail.html',
                         pathway=pathway,
                         required_skills=required_skills,
                         courses_map=courses_map,
                         skill_gaps=skill_gaps,
                         certifications=certifications,
                         career_progression=career_progression,
                         top_employers=top_employers,
                         alumni_at_employers=alumni_at_employers,
                         top_cities=top_cities,
                         skill_demands=skill_demands)


@workforce_bp.route('/compare')
def compare_pathways():
    """Compare multiple career pathways"""
    pathway_ids = request.args.getlist('pathways')
    
    if not pathway_ids:
        flash('Select pathways to compare', 'warning')
        return redirect(url_for('workforce.career_pathways'))
    
    pathways = CareerPathway.query.filter(
        CareerPathway.id.in_([int(p) for p in pathway_ids])
    ).all()
    
    import json
    
    # Prepare comparison data
    comparison_data = []
    for pathway in pathways:
        comparison_data.append({
            'pathway': pathway,
            'skills': json.loads(pathway.required_skills) if pathway.required_skills else [],
            'certifications': json.loads(pathway.recommended_certifications) if pathway.recommended_certifications else []
        })
    
    return render_template('workforce/compare_pathways.html',
                         comparison_data=comparison_data)


# ==================== SKILL DEMAND INTELLIGENCE ====================

@workforce_bp.route('/skills')
def skill_demand():
    """Skill demand dashboard"""
    category = request.args.get('category', 'all')
    trend = request.args.get('trend', 'all')
    search = request.args.get('search', '')
    
    query = SkillDemandForecast.query
    
    if category != 'all':
        query = query.filter_by(skill_category=category)
    
    if trend != 'all':
        query = query.filter_by(trend=trend)
    
    if search:
        query = query.filter(SkillDemandForecast.skill_name.ilike(f'%{search}%'))
    
    # Get most recent data for each skill
    subquery = db.session.query(
        SkillDemandForecast.skill_name,
        func.max(SkillDemandForecast.data_date).label('max_date')
    ).group_by(SkillDemandForecast.skill_name).subquery()
    
    skills = query.join(
        subquery,
        and_(
            SkillDemandForecast.skill_name == subquery.c.skill_name,
            SkillDemandForecast.data_date == subquery.c.max_date
        )
    ).order_by(SkillDemandForecast.current_demand_score.desc()).all()
    
    # Get trending skills (rising demand)
    trending_skills = SkillDemandForecast.query.filter_by(
        trend='rising'
    ).order_by(SkillDemandForecast.year_over_year_change.desc()).limit(10).all()
    
    return render_template('workforce/skill_demand.html',
                         skills=skills,
                         trending_skills=trending_skills,
                         current_category=category,
                         current_trend=trend)


@workforce_bp.route('/skill/<int:skill_id>')
def view_skill_detail(skill_id):
    """Detailed skill demand information"""
    skill = SkillDemandForecast.query.get_or_404(skill_id)
    
    import json
    
    # Parse fields
    psu_courses = json.loads(skill.psu_courses_teaching_skill) if skill.psu_courses_teaching_skill else []
    complementary = json.loads(skill.complementary_skills) if skill.complementary_skills else []
    industries = json.loads(skill.top_industries_needing_skill) if skill.top_industries_needing_skill else []
    
    # Get historical data for this skill (last 12 months)
    historical = SkillDemandForecast.query.filter_by(
        skill_name=skill.skill_name
    ).order_by(SkillDemandForecast.data_date.desc()).limit(12).all()
    
    # Get complementary skill details
    complementary_details = []
    if complementary:
        complementary_details = SkillDemandForecast.query.filter(
            SkillDemandForecast.skill_name.in_(complementary[:5])
        ).all()
    
    return render_template('workforce/skill_detail.html',
                         skill=skill,
                         psu_courses=psu_courses,
                         complementary=complementary,
                         industries=industries,
                         historical=historical,
                         complementary_details=complementary_details)


@workforce_bp.route('/my-skill-gap-analysis')
@login_required
def my_skill_gap():
    """Personalized skill gap analysis"""
    # Get student's major (assuming it's in user profile)
    student_major = getattr(current_user, 'major', None)
    
    if not student_major:
        flash('Please update your profile with your major', 'warning')
        return redirect(url_for('profile.edit'))
    
    # Get career pathways for student's major
    pathways = CareerPathway.query.filter_by(major=student_major).all()
    
    import json
    
    # Aggregate required skills across all pathways
    all_required_skills = set()
    for pathway in pathways:
        if pathway.required_skills:
            skills = json.loads(pathway.required_skills)
            all_required_skills.update(skills)
    
    # Get demand data for these skills
    skill_analysis = []
    for skill_name in all_required_skills:
        skill_data = SkillDemandForecast.query.filter_by(
            skill_name=skill_name
        ).order_by(SkillDemandForecast.data_date.desc()).first()
        
        if skill_data:
            skill_analysis.append(skill_data)
    
    # Sort by demand score
    skill_analysis.sort(key=lambda x: x.current_demand_score or 0, reverse=True)
    
    return render_template('workforce/my_skill_gap.html',
                         pathways=pathways,
                         skill_analysis=skill_analysis,
                         student_major=student_major)


# ==================== INDUSTRY COLLABORATIONS ====================

@workforce_bp.route('/industry-partnerships')
def industry_partnerships():
    """Browse faculty-industry collaborations"""
    industry = request.args.get('industry', 'all')
    collab_type = request.args.get('type', 'all')
    
    query = FacultyIndustryCollaboration.query.filter_by(is_public=True)
    
    if industry != 'all':
        query = query.filter_by(industry=industry)
    
    if collab_type != 'all':
        query = query.filter_by(collaboration_type=collab_type)
    
    collaborations = query.order_by(
        FacultyIndustryCollaboration.is_ongoing.desc(),
        FacultyIndustryCollaboration.students_involved.desc()
    ).all()
    
    # Get stats
    total_partnerships = FacultyIndustryCollaboration.query.filter_by(is_public=True).count()
    active_partnerships = FacultyIndustryCollaboration.query.filter_by(status='active', is_public=True).count()
    total_students_impacted = db.session.query(
        func.sum(FacultyIndustryCollaboration.students_involved)
    ).filter_by(is_public=True).scalar() or 0
    total_jobs_created = db.session.query(
        func.sum(FacultyIndustryCollaboration.jobs_created)
    ).filter_by(is_public=True).scalar() or 0
    
    return render_template('workforce/industry_partnerships.html',
                         collaborations=collaborations,
                         total_partnerships=total_partnerships,
                         active_partnerships=active_partnerships,
                         total_students_impacted=total_students_impacted,
                         total_jobs_created=total_jobs_created,
                         current_industry=industry,
                         current_type=collab_type)


@workforce_bp.route('/partnership/<int:collab_id>')
def view_partnership(collab_id):
    """View partnership details"""
    collab = FacultyIndustryCollaboration.query.get_or_404(collab_id)
    
    if not collab.is_public:
        flash('This partnership information is not publicly available', 'error')
        return redirect(url_for('workforce.industry_partnerships'))
    
    import json
    
    courses_enhanced = json.loads(collab.courses_enhanced) if collab.courses_enhanced else []
    
    return render_template('workforce/partnership_detail.html',
                         collab=collab,
                         courses_enhanced=courses_enhanced)


# ==================== FACULTY: MANAGE PARTNERSHIPS ====================

@workforce_bp.route('/faculty/my-partnerships')
@login_required
def faculty_partnerships():
    """Faculty dashboard for industry partnerships"""
    collaborations = FacultyIndustryCollaboration.query.filter_by(
        faculty_id=current_user.id
    ).order_by(FacultyIndustryCollaboration.created_at.desc()).all()
    
    return render_template('workforce/faculty_partnerships.html',
                         collaborations=collaborations)


@workforce_bp.route('/faculty/add-partnership', methods=['GET', 'POST'])
@login_required
def faculty_add_partnership():
    """Add new industry partnership"""
    if request.method == 'POST':
        data = request.form
        
        import json
        
        collab = FacultyIndustryCollaboration(
            faculty_id=current_user.id,
            company_name=data.get('company_name'),
            industry=data.get('industry'),
            company_size=data.get('company_size'),
            collaboration_type=data.get('collaboration_type'),
            project_title=data.get('project_title'),
            description=data.get('description'),
            funding_amount=float(data.get('funding_amount')) if data.get('funding_amount') else None,
            in_kind_contributions=data.get('in_kind_contributions'),
            start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date() if data.get('start_date') else None,
            end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date() if data.get('end_date') else None,
            is_ongoing=data.get('is_ongoing') == 'true',
            students_involved=int(data.get('students_involved', 0)),
            internships_created=int(data.get('internships_created', 0)),
            jobs_created=int(data.get('jobs_created', 0)),
            courses_enhanced=json.dumps(data.getlist('courses_enhanced')),
            equipment_acquired=data.get('equipment_acquired'),
            company_contact_name=data.get('company_contact_name'),
            company_contact_email=data.get('company_contact_email'),
            company_contact_phone=data.get('company_contact_phone'),
            status='active',
            is_public=data.get('is_public') == 'true',
            featured_on_website=False
        )
        
        db.session.add(collab)
        db.session.commit()
        
        flash('Industry partnership added successfully!', 'success')
        return redirect(url_for('workforce.faculty_partnerships'))
    
    return render_template('workforce/add_partnership.html')


# ==================== SALARY & COMPENSATION DATA ====================

@workforce_bp.route('/salary-data')
def salary_explorer():
    """Explore salary data by career/major"""
    major = request.args.get('major', '')
    career_field = request.args.get('field', 'all')
    
    query = CareerPathway.query
    
    if major:
        query = query.filter_by(major=major)
    
    if career_field != 'all':
        query = query.filter_by(career_field=career_field)
    
    # Get pathways with salary data
    pathways = query.filter(
        CareerPathway.regional_median_salary.isnot(None)
    ).order_by(CareerPathway.regional_median_salary.desc()).all()
    
    # Calculate averages
    if pathways:
        avg_entry = sum(p.entry_level_salary or 0 for p in pathways) / len(pathways)
        avg_median = sum(p.regional_median_salary or 0 for p in pathways) / len(pathways)
        avg_experienced = sum(p.experienced_salary or 0 for p in pathways) / len(pathways)
    else:
        avg_entry = avg_median = avg_experienced = 0
    
    # Get unique majors
    all_majors = db.session.query(CareerPathway.major).distinct().all()
    majors_list = sorted([m[0] for m in all_majors])
    
    return render_template('workforce/salary_explorer.html',
                         pathways=pathways,
                         avg_entry=avg_entry,
                         avg_median=avg_median,
                         avg_experienced=avg_experienced,
                         majors_list=majors_list,
                         current_major=major,
                         current_field=career_field)


# ==================== ADMIN: DATA MANAGEMENT ====================

@workforce_bp.route('/admin/update-pathway-data', methods=['POST'])
@login_required
def admin_update_pathway_data():
    """Update career pathway data (admin)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    pathway_id = data.get('pathway_id')
    
    pathway = CareerPathway.query.get_or_404(pathway_id)
    
    # Update salary data
    if 'regional_median_salary' in data:
        pathway.regional_median_salary = data['regional_median_salary']
    if 'national_median_salary' in data:
        pathway.national_median_salary = data['national_median_salary']
    if 'job_growth_rate' in data:
        pathway.job_growth_rate = data['job_growth_rate']
    
    pathway.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})


@workforce_bp.route('/admin/add-skill-data', methods=['POST'])
@login_required
def admin_add_skill_data():
    """Add skill demand data (admin)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form
    
    import json
    
    skill = SkillDemandForecast(
        skill_name=data.get('skill_name'),
        skill_category=data.get('skill_category'),
        current_demand_score=int(data.get('current_demand_score')),
        trend=data.get('trend'),
        year_over_year_change=float(data.get('year_over_year_change')) if data.get('year_over_year_change') else None,
        regional_job_postings=int(data.get('regional_job_postings', 0)),
        national_job_postings=int(data.get('national_job_postings', 0)),
        avg_salary_with_skill=float(data.get('avg_salary_with_skill')) if data.get('avg_salary_with_skill') else None,
        avg_salary_without_skill=float(data.get('avg_salary_without_skill')) if data.get('avg_salary_without_skill') else None,
        psu_courses_teaching_skill=json.dumps(data.getlist('psu_courses')),
        complementary_skills=json.dumps(data.getlist('complementary_skills')),
        forecasted_demand=data.get('forecasted_demand'),
        top_industries_needing_skill=json.dumps(data.getlist('top_industries')),
        data_date=datetime.strptime(data.get('data_date'), '%Y-%m-%d').date() if data.get('data_date') else date.today(),
        data_source=data.get('data_source', 'Manual Entry')
    )
    
    # Calculate salary premium
    if skill.avg_salary_with_skill and skill.avg_salary_without_skill:
        skill.salary_premium_percentage = (
            (skill.avg_salary_with_skill - skill.avg_salary_without_skill) / 
            skill.avg_salary_without_skill * 100
        )
    
    db.session.add(skill)
    db.session.commit()
    
    flash('Skill demand data added successfully', 'success')
    return redirect(url_for('workforce.skill_demand'))


# ==================== ANALYTICS ====================

@workforce_bp.route('/analytics')
@login_required
def workforce_analytics():
    """Workforce alignment analytics dashboard"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('workforce.career_pathways'))
    
    # Career pathway stats
    total_pathways = CareerPathway.query.count()
    pathways_with_salary = CareerPathway.query.filter(
        CareerPathway.regional_median_salary.isnot(None)
    ).count()
    
    # Skill stats
    total_skills_tracked = SkillDemandForecast.query.with_entities(
        SkillDemandForecast.skill_name
    ).distinct().count()
    
    rising_skills = SkillDemandForecast.query.filter_by(trend='rising').count()
    
    # Industry partnerships
    total_partnerships = FacultyIndustryCollaboration.query.count()
    active_partnerships = FacultyIndustryCollaboration.query.filter_by(status='active').count()
    
    # Top growing careers
    top_growth = CareerPathway.query.filter(
        CareerPathway.job_growth_rate.isnot(None)
    ).order_by(CareerPathway.job_growth_rate.desc()).limit(10).all()
    
    # Highest paying careers
    top_salary = CareerPathway.query.filter(
        CareerPathway.regional_median_salary.isnot(None)
    ).order_by(CareerPathway.regional_median_salary.desc()).limit(10).all()
    
    return render_template('workforce/analytics.html',
                         total_pathways=total_pathways,
                         pathways_with_salary=pathways_with_salary,
                         total_skills_tracked=total_skills_tracked,
                         rising_skills=rising_skills,
                         total_partnerships=total_partnerships,
                         active_partnerships=active_partnerships,
                         top_growth=top_growth,
                         top_salary=top_salary)
