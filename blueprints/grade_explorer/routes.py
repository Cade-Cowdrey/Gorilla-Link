from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models_student_features import GradeDistribution
from sqlalchemy import or_, func
from datetime import datetime

grade_explorer_bp = Blueprint('grade_explorer', __name__, url_prefix='/grades')

@grade_explorer_bp.route('/')
def index():
    """Grade distribution explorer homepage"""
    department = request.args.get('dept', '')
    course_code = request.args.get('course', '')
    professor = request.args.get('professor', '')
    semester = request.args.get('semester', '')
    
    query = GradeDistribution.query
    
    # Apply filters
    if department:
        query = query.filter_by(department=department)
    
    if course_code:
        query = query.filter(GradeDistribution.course_code.ilike(f'%{course_code}%'))
    
    if professor:
        query = query.filter(GradeDistribution.professor_name.ilike(f'%{professor}%'))
    
    if semester:
        query = query.filter(GradeDistribution.semester.ilike(f'%{semester}%'))
    
    distributions = query.order_by(
        GradeDistribution.year.desc(),
        GradeDistribution.semester.desc()
    ).limit(50).all()
    
    # Get departments for filter
    departments = db.session.query(
        GradeDistribution.department
    ).distinct().order_by(GradeDistribution.department).all()
    departments = [d[0] for d in departments if d[0]]
    
    return render_template('grade_explorer/index.html',
                         distributions=distributions,
                         departments=departments,
                         department=department,
                         course_code=course_code,
                         professor=professor,
                         semester=semester)


@grade_explorer_bp.route('/course/<string:course_code>')
def course_detail(course_code):
    """View grade distribution for a specific course"""
    distributions = GradeDistribution.query.filter_by(
        course_code=course_code.upper()
    ).order_by(
        GradeDistribution.year.desc(),
        GradeDistribution.semester.desc()
    ).all()
    
    if not distributions:
        flash('No grade data found for this course.', 'warning')
        return redirect(url_for('grade_explorer.index'))
    
    # Calculate overall statistics
    total_students = sum(d.total_students for d in distributions)
    total_a = sum(d.grade_a for d in distributions)
    total_b = sum(d.grade_b for d in distributions)
    total_c = sum(d.grade_c for d in distributions)
    total_d = sum(d.grade_d for d in distributions)
    total_f = sum(d.grade_f for d in distributions)
    
    stats = {
        'total_students': total_students,
        'avg_a_percent': round((total_a / total_students * 100), 1) if total_students else 0,
        'avg_b_percent': round((total_b / total_students * 100), 1) if total_students else 0,
        'avg_c_percent': round((total_c / total_students * 100), 1) if total_students else 0,
        'avg_d_percent': round((total_d / total_students * 100), 1) if total_students else 0,
        'avg_f_percent': round((total_f / total_students * 100), 1) if total_students else 0,
        'avg_gpa': round(sum(d.gpa_average * d.total_students for d in distributions if d.gpa_average) / total_students, 2) if total_students else 0
    }
    
    return render_template('grade_explorer/course_detail.html',
                         course_code=course_code,
                         distributions=distributions,
                         stats=stats)


@grade_explorer_bp.route('/professor/<string:professor_name>')
def professor_detail(professor_name):
    """View grade distribution for a specific professor"""
    distributions = GradeDistribution.query.filter(
        GradeDistribution.professor_name.ilike(f'%{professor_name}%')
    ).order_by(
        GradeDistribution.year.desc(),
        GradeDistribution.semester.desc()
    ).all()
    
    if not distributions:
        flash('No grade data found for this professor.', 'warning')
        return redirect(url_for('grade_explorer.index'))
    
    # Group by course
    courses_data = {}
    for d in distributions:
        if d.course_code not in courses_data:
            courses_data[d.course_code] = {
                'course_name': d.course_name,
                'distributions': [],
                'total_students': 0,
                'avg_gpa': 0
            }
        courses_data[d.course_code]['distributions'].append(d)
        courses_data[d.course_code]['total_students'] += d.total_students
    
    # Calculate avg GPA per course
    for course_code, data in courses_data.items():
        total_students = data['total_students']
        if total_students > 0:
            data['avg_gpa'] = round(
                sum(d.gpa_average * d.total_students for d in data['distributions'] if d.gpa_average) / total_students,
                2
            )
    
    return render_template('grade_explorer/professor_detail.html',
                         professor_name=professor_name,
                         courses_data=courses_data)


@grade_explorer_bp.route('/compare')
def compare():
    """Compare grade distributions across professors for same course"""
    course_code = request.args.get('course', '')
    
    if not course_code:
        return render_template('grade_explorer/compare.html', distributions=None)
    
    distributions = GradeDistribution.query.filter_by(
        course_code=course_code.upper()
    ).order_by(GradeDistribution.professor_name).all()
    
    # Group by professor
    professor_stats = {}
    for d in distributions:
        if d.professor_name not in professor_stats:
            professor_stats[d.professor_name] = {
                'total_students': 0,
                'total_a': 0,
                'total_b': 0,
                'total_c': 0,
                'avg_gpa': 0,
                'pass_rate': 0
            }
        
        stats = professor_stats[d.professor_name]
        stats['total_students'] += d.total_students
        stats['total_a'] += d.grade_a
        stats['total_b'] += d.grade_b
        stats['total_c'] += d.grade_c
        
        if d.gpa_average:
            stats['avg_gpa'] = (stats['avg_gpa'] * (stats['total_students'] - d.total_students) + 
                              d.gpa_average * d.total_students) / stats['total_students']
        if d.pass_rate:
            stats['pass_rate'] = (stats['pass_rate'] * (stats['total_students'] - d.total_students) + 
                                d.pass_rate * d.total_students) / stats['total_students']
    
    return render_template('grade_explorer/compare.html',
                         course_code=course_code,
                         professor_stats=professor_stats)
