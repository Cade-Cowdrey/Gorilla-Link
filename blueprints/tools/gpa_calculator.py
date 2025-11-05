"""
GPA Calculator Blueprint
Accurate GPA calculation with credit hour weighting
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User
from sqlalchemy import func
from datetime import datetime

gpa_bp = Blueprint('gpa_calculator', __name__, url_prefix='/tools/gpa')

# PSU Grade Point Scale (Simplified: A=4, B=3, C=2, D=1, F=0)
GRADE_POINTS = {
    'A': 4.0,
    'B': 3.0,
    'C': 2.0,
    'D': 1.0,
    'F': 0.0,
    'W': None,  # Withdrawn - doesn't count
    'I': None,  # Incomplete - doesn't count
    'P': None,  # Pass - doesn't count in GPA
}


@gpa_bp.route('/')
@login_required
def calculator_home():
    """GPA Calculator main page"""
    return render_template('tools/gpa_calculator.html', 
                         grade_points=GRADE_POINTS,
                         title='GPA Calculator')


@gpa_bp.route('/calculate', methods=['POST'])
@login_required
def calculate_gpa():
    """
    Calculate GPA based on courses, grades, and credit hours
    
    Expected JSON format:
    {
        "courses": [
            {"name": "CS 1080", "grade": "A", "credits": 3},
            {"name": "MATH 2130", "grade": "B+", "credits": 4},
            ...
        ],
        "current_gpa": 3.5,  # Optional - for cumulative GPA
        "current_credits": 45  # Optional - for cumulative GPA
    }
    """
    try:
        data = request.get_json()
        courses = data.get('courses', [])
        
        if not courses:
            return jsonify({'error': 'No courses provided'}), 400
        
        # Calculate semester GPA
        total_quality_points = 0.0
        total_credits = 0.0
        course_results = []
        
        for course in courses:
            grade = course.get('grade', '').upper()
            credits = float(course.get('credits', 0))
            course_name = course.get('name', 'Unnamed Course')
            
            # Validate grade
            if grade not in GRADE_POINTS:
                return jsonify({'error': f'Invalid grade: {grade}'}), 400
            
            # Skip grades that don't count (W, I, P)
            grade_point = GRADE_POINTS[grade]
            if grade_point is None:
                course_results.append({
                    'name': course_name,
                    'grade': grade,
                    'credits': credits,
                    'quality_points': 0,
                    'note': 'Does not count in GPA'
                })
                continue
            
            # Calculate quality points for this course
            quality_points = grade_point * credits
            total_quality_points += quality_points
            total_credits += credits
            
            course_results.append({
                'name': course_name,
                'grade': grade,
                'credits': credits,
                'grade_point': grade_point,
                'quality_points': round(quality_points, 2)
            })
        
        # Calculate semester GPA
        if total_credits == 0:
            return jsonify({'error': 'No valid courses with grades that count'}), 400
        
        semester_gpa = total_quality_points / total_credits
        
        # Calculate cumulative GPA if previous GPA provided
        cumulative_gpa = None
        new_total_credits = None
        
        current_gpa = data.get('current_gpa')
        current_credits = data.get('current_credits')
        
        if current_gpa is not None and current_credits is not None:
            current_gpa = float(current_gpa)
            current_credits = float(current_credits)
            
            # Calculate previous quality points
            previous_quality_points = current_gpa * current_credits
            
            # Add new quality points
            total_quality_points_cum = previous_quality_points + total_quality_points
            new_total_credits = current_credits + total_credits
            
            # Calculate new cumulative GPA
            cumulative_gpa = total_quality_points_cum / new_total_credits
        
        # Determine GPA standing
        gpa_standing = get_gpa_standing(semester_gpa)
        
        response = {
            'semester_gpa': round(semester_gpa, 3),
            'semester_credits': round(total_credits, 1),
            'total_quality_points': round(total_quality_points, 2),
            'gpa_standing': gpa_standing,
            'courses': course_results
        }
        
        if cumulative_gpa is not None:
            response['cumulative_gpa'] = round(cumulative_gpa, 3)
            response['total_credits'] = round(new_total_credits, 1)
            response['cumulative_standing'] = get_gpa_standing(cumulative_gpa)
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid number format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gpa_bp.route('/what-if', methods=['POST'])
@login_required
def what_if_analysis():
    """
    What-if GPA scenario calculator
    "What GPA do I need to raise my cumulative GPA to 3.5?"
    
    Expected JSON:
    {
        "current_gpa": 3.2,
        "current_credits": 60,
        "target_gpa": 3.5,
        "upcoming_credits": 15
    }
    """
    try:
        data = request.get_json()
        
        current_gpa = float(data.get('current_gpa', 0))
        current_credits = float(data.get('current_credits', 0))
        target_gpa = float(data.get('target_gpa', 0))
        upcoming_credits = float(data.get('upcoming_credits', 0))
        
        # Validate inputs
        if current_gpa < 0 or current_gpa > 4.0:
            return jsonify({'error': 'Current GPA must be between 0.0 and 4.0'}), 400
        if target_gpa < 0 or target_gpa > 4.0:
            return jsonify({'error': 'Target GPA must be between 0.0 and 4.0'}), 400
        if current_credits < 0 or upcoming_credits <= 0:
            return jsonify({'error': 'Invalid credit hours'}), 400
        
        # Calculate required quality points for target GPA
        current_quality_points = current_gpa * current_credits
        total_credits_after = current_credits + upcoming_credits
        required_total_quality_points = target_gpa * total_credits_after
        required_new_quality_points = required_total_quality_points - current_quality_points
        
        # Calculate required semester GPA
        required_semester_gpa = required_new_quality_points / upcoming_credits
        
        # Determine if it's achievable
        achievable = required_semester_gpa <= 4.0
        
        # Provide recommendations
        if required_semester_gpa > 4.0:
            recommendation = f"Not possible to reach {target_gpa} GPA with {upcoming_credits} credits. You would need a {round(required_semester_gpa, 2)} GPA (impossible - max is 4.0)."
            alternative_target = (current_quality_points + (4.0 * upcoming_credits)) / total_credits_after
            recommendation += f" With straight A's, you could reach {round(alternative_target, 2)} GPA."
        elif required_semester_gpa < 0:
            recommendation = f"You've already exceeded your target GPA! Your current {current_gpa} is above {target_gpa}."
        else:
            recommendation = f"To reach {target_gpa} GPA, you need a {round(required_semester_gpa, 2)} semester GPA in your next {upcoming_credits} credits."
            
            # Suggest grade distribution
            if required_semester_gpa >= 3.7:
                recommendation += " This requires mostly A's."
            elif required_semester_gpa >= 3.3:
                recommendation += " This requires mostly A's and B+'s."
            elif required_semester_gpa >= 3.0:
                recommendation += " This requires mostly B's and above."
            elif required_semester_gpa >= 2.7:
                recommendation += " This requires mostly B's and B-'s."
            elif required_semester_gpa >= 2.0:
                recommendation += " This requires mostly C's and above."
            else:
                recommendation += " This is very achievable with consistent effort."
        
        return jsonify({
            'current_gpa': round(current_gpa, 3),
            'current_credits': current_credits,
            'target_gpa': round(target_gpa, 3),
            'upcoming_credits': upcoming_credits,
            'required_semester_gpa': round(required_semester_gpa, 3) if achievable else None,
            'achievable': achievable,
            'recommendation': recommendation,
            'projected_total_credits': total_credits_after
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid number format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gpa_bp.route('/grades', methods=['GET'])
def get_grade_scale():
    """Get PSU's grade point scale"""
    grade_scale = [
        {'grade': grade, 'points': points} 
        for grade, points in GRADE_POINTS.items()
        if points is not None
    ]
    grade_scale.sort(key=lambda x: x['points'], reverse=True)
    
    return jsonify({
        'grade_scale': grade_scale,
        'system': '4.0 Scale',
        'university': 'Pittsburg State University'
    }), 200


def get_gpa_standing(gpa):
    """Determine academic standing based on GPA"""
    if gpa >= 3.9:
        return "Summa Cum Laude (Highest Honors)"
    elif gpa >= 3.7:
        return "Magna Cum Laude (High Honors)"
    elif gpa >= 3.5:
        return "Cum Laude (Honors)"
    elif gpa >= 3.0:
        return "Dean's List"
    elif gpa >= 2.0:
        return "Good Standing"
    else:
        return "Academic Warning"


@gpa_bp.route('/save', methods=['POST'])
@login_required
def save_gpa():
    """Save calculated GPA to user profile"""
    try:
        data = request.get_json()
        gpa = float(data.get('gpa', 0))
        credits = float(data.get('credits', 0))
        
        # Update user's GPA in profile
        current_user.gpa = gpa
        db.session.commit()
        
        return jsonify({
            'message': 'GPA saved to profile',
            'gpa': round(gpa, 3)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
