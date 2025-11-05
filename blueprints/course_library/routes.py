from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models_student_features import CourseMaterial, MaterialRating
from sqlalchemy import or_, func
from datetime import datetime

course_library_bp = Blueprint('course_library', __name__, url_prefix='/course-library')

@course_library_bp.route('/')
def index():
    """Course material library homepage"""
    department = request.args.get('dept', '')
    course_code = request.args.get('course', '')
    material_type = request.args.get('type', '')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'recent')
    
    query = CourseMaterial.query.filter_by(flagged=False)
    
    # Apply filters
    if department:
        query = query.filter_by(department=department)
    
    if course_code:
        query = query.filter(CourseMaterial.course_code.ilike(f'%{course_code}%'))
    
    if material_type:
        query = query.filter_by(material_type=material_type)
    
    if search_query:
        query = query.filter(
            or_(
                CourseMaterial.title.ilike(f'%{search_query}%'),
                CourseMaterial.course_name.ilike(f'%{search_query}%'),
                CourseMaterial.tags.ilike(f'%{search_query}%')
            )
        )
    
    # Sorting
    if sort_by == 'popular':
        query = query.order_by(CourseMaterial.downloads.desc())
    elif sort_by == 'rating':
        query = query.order_by(CourseMaterial.rating.desc())
    else:  # recent
        query = query.order_by(CourseMaterial.created_at.desc())
    
    materials = query.limit(100).all()
    
    # Get departments
    departments = db.session.query(
        CourseMaterial.department
    ).distinct().order_by(CourseMaterial.department).all()
    departments = [d[0] for d in departments if d[0]]
    
    # Get material types
    material_types = ['Notes', 'Study Guide', 'Exam', 'Syllabus', 'Slides', 'Assignment', 'Other']
    
    return render_template('course_library/index.html',
                         materials=materials,
                         departments=departments,
                         material_types=material_types,
                         department=department,
                         course_code=course_code,
                         material_type=material_type,
                         search_query=search_query,
                         sort_by=sort_by)


@course_library_bp.route('/material/<int:material_id>')
def view_material(material_id):
    """View material details"""
    material = CourseMaterial.query.get_or_404(material_id)
    
    # Get ratings
    ratings = MaterialRating.query.filter_by(material_id=material_id).order_by(
        MaterialRating.created_at.desc()
    ).limit(10).all()
    
    # Check if user has rated
    user_rating = None
    if current_user.is_authenticated:
        user_rating = MaterialRating.query.filter_by(
            material_id=material_id,
            user_id=current_user.id
        ).first()
    
    # Get similar materials
    similar = CourseMaterial.query.filter(
        CourseMaterial.id != material_id,
        CourseMaterial.course_code == material.course_code,
        CourseMaterial.flagged == False
    ).order_by(CourseMaterial.rating.desc()).limit(5).all()
    
    return render_template('course_library/material.html',
                         material=material,
                         ratings=ratings,
                         user_rating=user_rating,
                         similar=similar)


@course_library_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_material():
    """Upload course material"""
    if request.method == 'POST':
        material = CourseMaterial(
            course_code=request.form['course_code'].upper(),
            course_name=request.form['course_name'],
            department=request.form['department'],
            professor_name=request.form.get('professor_name'),
            semester=request.form.get('semester'),
            title=request.form['title'],
            material_type=request.form['material_type'],
            description=request.form.get('description'),
            file_url=request.form.get('file_url'),  # Cloud storage link
            external_link=request.form.get('external_link'),
            tags=request.form.get('tags'),
            uploader_id=current_user.id
        )
        
        db.session.add(material)
        db.session.commit()
        
        flash('Material uploaded successfully! It will be reviewed before appearing publicly.', 'success')
        return redirect(url_for('course_library.view_material', material_id=material.id))
    
    return render_template('course_library/upload.html')


@course_library_bp.route('/download/<int:material_id>')
@login_required
def download_material(material_id):
    """Track download and redirect to file"""
    material = CourseMaterial.query.get_or_404(material_id)
    
    # Increment download count
    material.downloads += 1
    db.session.commit()
    
    # In production, this would redirect to the actual file URL
    if material.file_url:
        return redirect(material.file_url)
    elif material.external_link:
        return redirect(material.external_link)
    else:
        flash('No download link available.', 'warning')
        return redirect(url_for('course_library.view_material', material_id=material_id))


@course_library_bp.route('/rate/<int:material_id>', methods=['POST'])
@login_required
def rate_material(material_id):
    """Rate a course material"""
    material = CourseMaterial.query.get_or_404(material_id)
    
    # Check for existing rating
    existing_rating = MaterialRating.query.filter_by(
        material_id=material_id,
        user_id=current_user.id
    ).first()
    
    rating_value = int(request.form['rating'])
    comment = request.form.get('comment')
    
    if existing_rating:
        existing_rating.rating = rating_value
        existing_rating.comment = comment
        message = 'Rating updated!'
    else:
        rating = MaterialRating(
            material_id=material_id,
            user_id=current_user.id,
            rating=rating_value,
            comment=comment
        )
        db.session.add(rating)
        material.rating_count += 1
        message = 'Rating submitted!'
    
    # Recalculate average rating
    avg_rating = db.session.query(
        func.avg(MaterialRating.rating)
    ).filter_by(material_id=material_id).scalar()
    
    material.rating = float(avg_rating) if avg_rating else 0
    
    db.session.commit()
    
    flash(message, 'success')
    return redirect(url_for('course_library.view_material', material_id=material_id))


@course_library_bp.route('/my-uploads')
@login_required
def my_uploads():
    """View user's uploaded materials"""
    materials = CourseMaterial.query.filter_by(
        uploader_id=current_user.id
    ).order_by(CourseMaterial.created_at.desc()).all()
    
    return render_template('course_library/my_uploads.html', materials=materials)


@course_library_bp.route('/edit/<int:material_id>', methods=['GET', 'POST'])
@login_required
def edit_material(material_id):
    """Edit a course material"""
    material = CourseMaterial.query.get_or_404(material_id)
    
    if material.uploader_id != current_user.id:
        flash('You can only edit your own uploads.', 'danger')
        return redirect(url_for('course_library.view_material', material_id=material_id))
    
    if request.method == 'POST':
        material.title = request.form['title']
        material.description = request.form.get('description')
        material.tags = request.form.get('tags')
        material.file_url = request.form.get('file_url')
        material.external_link = request.form.get('external_link')
        
        db.session.commit()
        flash('Material updated!', 'success')
        return redirect(url_for('course_library.view_material', material_id=material_id))
    
    return render_template('course_library/edit.html', material=material)


@course_library_bp.route('/delete/<int:material_id>', methods=['POST'])
@login_required
def delete_material(material_id):
    """Delete a course material"""
    material = CourseMaterial.query.get_or_404(material_id)
    
    if material.uploader_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(material)
    db.session.commit()
    
    flash('Material deleted.', 'success')
    return redirect(url_for('course_library.my_uploads'))


@course_library_bp.route('/flag/<int:material_id>', methods=['POST'])
@login_required
def flag_material(material_id):
    """Flag material for review"""
    material = CourseMaterial.query.get_or_404(material_id)
    material.flagged = True
    db.session.commit()
    
    flash('Material flagged for review. Thank you!', 'info')
    return redirect(url_for('course_library.index'))


@course_library_bp.route('/course/<string:course_code>')
def course_materials(course_code):
    """View all materials for a specific course"""
    materials = CourseMaterial.query.filter_by(
        course_code=course_code.upper(),
        flagged=False
    ).order_by(CourseMaterial.rating.desc()).all()
    
    if not materials:
        flash('No materials found for this course.', 'warning')
        return redirect(url_for('course_library.index'))
    
    return render_template('course_library/course_materials.html',
                         course_code=course_code,
                         materials=materials)
