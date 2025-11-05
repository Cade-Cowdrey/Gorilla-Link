from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import free_stuff_bp
from extensions import db
from models_innovative_features import FreeStuff
from datetime import datetime

@free_stuff_bp.route('/')
def index():
    """Browse free stuff"""
    category = request.args.get('category', 'all')
    
    query = FreeStuff.query.filter_by(status='available')
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    items = query.order_by(FreeStuff.created_at.desc()).all()
    
    return render_template('free_stuff/index.html', items=items)


@free_stuff_bp.route('/item/<int:item_id>')
def view_item(item_id):
    """View free item details"""
    item = FreeStuff.query.get_or_404(item_id)
    item.view_count += 1
    db.session.commit()
    
    return render_template('free_stuff/view_item.html', item=item)


@free_stuff_bp.route('/post', methods=['GET', 'POST'])
@login_required
def post_item():
    """Post free item"""
    if request.method == 'POST':
        item = FreeStuff(
            user_id=current_user.id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            condition=request.form.get('condition'),
            pickup_location=request.form.get('pickup_location'),
            pickup_instructions=request.form.get('pickup_instructions'),
            first_come_first_serve=request.form.get('first_come_first_serve') == 'on',
            student_only=request.form.get('student_only') == 'on'
        )
        
        if request.form.get('available_until'):
            item.available_until = datetime.strptime(request.form.get('available_until'), '%Y-%m-%d').date()
        
        db.session.add(item)
        db.session.commit()
        
        flash('Item posted! Students will be able to claim it.', 'success')
        return redirect(url_for('free_stuff.my_items'))
    
    return render_template('free_stuff/post.html')


@free_stuff_bp.route('/claim/<int:item_id>', methods=['POST'])
@login_required
def claim_item(item_id):
    """Claim free item"""
    item = FreeStuff.query.get_or_404(item_id)
    
    if item.status != 'available':
        flash('This item is no longer available.', 'error')
        return redirect(url_for('free_stuff.index'))
    
    item.status = 'claimed'
    item.claimed_by_id = current_user.id
    item.claimed_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Item claimed! Contact the giver to arrange pickup.', 'success')
    return redirect(url_for('free_stuff.view_item', item_id=item_id))


@free_stuff_bp.route('/my-items')
@login_required
def my_items():
    """View user's items"""
    given_items = FreeStuff.query.filter_by(user_id=current_user.id).order_by(FreeStuff.created_at.desc()).all()
    claimed_items = FreeStuff.query.filter_by(claimed_by_id=current_user.id).order_by(FreeStuff.claimed_at.desc()).all()
    
    return render_template('free_stuff/my_items.html', given_items=given_items, claimed_items=claimed_items)
