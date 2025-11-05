from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models_student_features import StudentDiscount, DiscountUsage
from sqlalchemy import or_
from datetime import datetime, date

discounts_bp = Blueprint('discounts', __name__, url_prefix='/discounts')

@discounts_bp.route('/')
def index():
    """Student discounts directory"""
    category = request.args.get('category', '')
    location = request.args.get('location', 'all')  # local, online, all
    search_query = request.args.get('q', '')
    
    query = StudentDiscount.query
    
    # Apply filters
    if category:
        query = query.filter_by(business_type=category)
    
    if location == 'local':
        query = query.filter_by(is_local=True)
    elif location == 'online':
        query = query.filter_by(is_online=True)
    
    if search_query:
        query = query.filter(
            or_(
                StudentDiscount.business_name.ilike(f'%{search_query}%'),
                StudentDiscount.discount_description.ilike(f'%{search_query}%')
            )
        )
    
    # Filter active discounts
    today = date.today()
    query = query.filter(
        or_(
            StudentDiscount.end_date == None,
            StudentDiscount.end_date >= today
        )
    )
    
    discounts = query.order_by(StudentDiscount.popularity_score.desc()).limit(100).all()
    
    # Get categories with counts
    categories = db.session.query(
        StudentDiscount.business_type,
        db.func.count(StudentDiscount.id).label('count')
    ).group_by(StudentDiscount.business_type).all()
    
    return render_template('student_discounts/index.html',
                         discounts=discounts,
                         categories=categories,
                         category=category,
                         location=location,
                         search_query=search_query)


@discounts_bp.route('/discount/<int:discount_id>')
def view_discount(discount_id):
    """View discount details"""
    discount = StudentDiscount.query.get_or_404(discount_id)
    
    # Increment view count
    discount.view_count += 1
    db.session.commit()
    
    return render_template('student_discounts/view.html', discount=discount)


@discounts_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_discount():
    """Submit a new discount"""
    if request.method == 'POST':
        discount = StudentDiscount(
            business_name=request.form['business_name'],
            business_type=request.form['business_type'],
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            website=request.form.get('website'),
            discount_description=request.form['discount_description'],
            discount_amount=request.form.get('discount_amount'),
            promo_code=request.form.get('promo_code'),
            requirements=request.form.get('requirements'),
            is_local=request.form.get('is_local') == 'on',
            is_online=request.form.get('is_online') == 'on',
            verification_required=request.form.get('verification_required') == 'on'
        )
        
        db.session.add(discount)
        db.session.commit()
        
        flash('Discount submitted! It will be reviewed before appearing publicly.', 'success')
        return redirect(url_for('discounts.index'))
    
    return render_template('student_discounts/submit.html')


@discounts_bp.route('/use/<int:discount_id>', methods=['POST'])
@login_required
def mark_used(discount_id):
    """Mark discount as used by current user"""
    discount = StudentDiscount.query.get_or_404(discount_id)
    
    usage = DiscountUsage(
        discount_id=discount_id,
        user_id=current_user.id
    )
    
    discount.popularity_score += 1
    db.session.add(usage)
    db.session.commit()
    
    return jsonify({'message': 'Marked as used!'})


@discounts_bp.route('/save/<int:discount_id>', methods=['POST'])
@login_required
def save_discount(discount_id):
    """Save discount for later"""
    discount = StudentDiscount.query.get_or_404(discount_id)
    discount.save_count += 1
    db.session.commit()
    
    return jsonify({'message': 'Saved!', 'save_count': discount.save_count})
