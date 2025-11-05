from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models_student_features import ProfessorReview, ProfessorProfile
from sqlalchemy import or_, func
from datetime import datetime

professor_bp = Blueprint('professor', __name__, url_prefix='/professors')

@professor_bp.route('/')
def index():
    """Professor reviews homepage"""
    department = request.args.get('dept', '')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'rating')
    
    query = ProfessorProfile.query
    
    # Apply filters
    if department:
        query = query.filter_by(department=department)
    
    if search_query:
        query = query.filter(ProfessorProfile.name.ilike(f'%{search_query}%'))
    
    # Sorting
    if sort_by == 'name':
        query = query.order_by(ProfessorProfile.name.asc())
    elif sort_by == 'difficulty':
        query = query.order_by(ProfessorProfile.avg_difficulty.asc())
    elif sort_by == 'reviews':
        query = query.order_by(ProfessorProfile.review_count.desc())
    else:  # rating
        query = query.order_by(ProfessorProfile.avg_overall_rating.desc())
    
    professors = query.limit(100).all()
    
    # Get departments
    departments = db.session.query(
        ProfessorProfile.department
    ).distinct().order_by(ProfessorProfile.department).all()
    departments = [d[0] for d in departments if d[0]]
    
    return render_template('professor_reviews/index.html',
                         professors=professors,
                         departments=departments,
                         department=department,
                         search_query=search_query,
                         sort_by=sort_by)


@professor_bp.route('/professor/<int:professor_id>')
def view_professor(professor_id):
    """View professor profile and reviews"""
    professor = ProfessorProfile.query.get_or_404(professor_id)
    
    # Get reviews
    page = request.args.get('page', 1, type=int)
    course_filter = request.args.get('course', '')
    
    reviews_query = ProfessorReview.query.filter_by(professor_name=professor.name)
    
    if course_filter:
        reviews_query = reviews_query.filter_by(course_code=course_filter)
    
    reviews = reviews_query.order_by(
        ProfessorReview.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    
    # Get courses taught
    courses = db.session.query(
        ProfessorReview.course_code,
        ProfessorReview.course_name
    ).filter_by(professor_name=professor.name).distinct().all()
    
    return render_template('professor_reviews/professor.html',
                         professor=professor,
                         reviews=reviews,
                         courses=courses,
                         course_filter=course_filter)


@professor_bp.route('/review/<string:professor_name>', methods=['GET', 'POST'])
@login_required
def add_review(professor_name):
    """Add a review for a professor"""
    if request.method == 'POST':
        review = ProfessorReview(
            professor_name=professor_name,
            department=request.form.get('department'),
            course_code=request.form.get('course_code', '').upper(),
            course_name=request.form.get('course_name'),
            user_id=current_user.id,
            overall_rating=int(request.form['overall_rating']),
            difficulty_rating=int(request.form.get('difficulty_rating', 0)) or None,
            clarity_rating=int(request.form.get('clarity_rating', 0)) or None,
            helpfulness_rating=int(request.form.get('helpfulness_rating', 0)) or None,
            grading_fairness=int(request.form.get('grading_fairness', 0)) or None,
            semester_taken=request.form.get('semester_taken'),
            grade_received=request.form.get('grade_received'),
            attendance_mandatory=request.form.get('attendance_mandatory') == 'on',
            would_take_again=request.form.get('would_take_again') == 'on',
            review_text=request.form['review_text'],
            pros=request.form.get('pros'),
            cons=request.form.get('cons'),
            tips=request.form.get('tips'),
            hours_per_week=int(request.form.get('hours_per_week', 0)) or None,
            textbook_required=request.form.get('textbook_required') == 'on',
            verified_student=True  # Assume verified if logged in
        )
        
        db.session.add(review)
        
        # Update or create professor profile
        professor = ProfessorProfile.query.filter_by(name=professor_name).first()
        if not professor:
            professor = ProfessorProfile(
                name=professor_name,
                department=request.form.get('department')
            )
            db.session.add(professor)
        
        # Recalculate averages
        professor.review_count += 1
        
        avg_ratings = db.session.query(
            func.avg(ProfessorReview.overall_rating).label('overall'),
            func.avg(ProfessorReview.difficulty_rating).label('difficulty'),
            func.avg(ProfessorReview.clarity_rating).label('clarity'),
            func.avg(ProfessorReview.helpfulness_rating).label('helpfulness')
        ).filter_by(professor_name=professor_name).first()
        
        professor.avg_overall_rating = float(avg_ratings.overall) if avg_ratings.overall else 0
        professor.avg_difficulty = float(avg_ratings.difficulty) if avg_ratings.difficulty else 0
        professor.avg_clarity = float(avg_ratings.clarity) if avg_ratings.clarity else 0
        professor.avg_helpfulness = float(avg_ratings.helpfulness) if avg_ratings.helpfulness else 0
        
        # Calculate would take again percentage
        would_take_count = ProfessorReview.query.filter_by(
            professor_name=professor_name,
            would_take_again=True
        ).count()
        professor.would_take_again_percent = (would_take_count / professor.review_count * 100) if professor.review_count else 0
        
        db.session.commit()
        
        flash('Your review has been posted!', 'success')
        return redirect(url_for('professor.view_professor', professor_id=professor.id))
    
    # GET request
    professor = ProfessorProfile.query.filter_by(name=professor_name).first()
    return render_template('professor_reviews/add_review.html',
                         professor_name=professor_name,
                         professor=professor)


@professor_bp.route('/helpful/<int:review_id>', methods=['POST'])
@login_required
def mark_helpful(review_id):
    """Mark a review as helpful"""
    review = ProfessorReview.query.get_or_404(review_id)
    review.helpful_count += 1
    db.session.commit()
    
    return jsonify({'helpful_count': review.helpful_count})


@professor_bp.route('/search-autocomplete')
def search_autocomplete():
    """Autocomplete search for professor names"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    professors = ProfessorProfile.query.filter(
        ProfessorProfile.name.ilike(f'%{query}%')
    ).limit(10).all()
    
    results = [{'name': p.name, 'department': p.department, 'id': p.id} for p in professors]
    return jsonify(results)
