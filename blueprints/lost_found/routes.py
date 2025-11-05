from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import lost_found_bp
from extensions import db
from models_innovative_features import LostItem
from datetime import datetime, timedelta

@lost_found_bp.route('/')
def index():
    """Browse lost and found items"""
    item_type = request.args.get('type', 'all')  # lost, found, all
    category = request.args.get('category', 'all')
    
    query = LostItem.query.filter_by(status='active')
    
    if item_type != 'all':
        query = query.filter_by(item_type=item_type)
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    items = query.order_by(LostItem.date_lost_found.desc()).all()
    
    return render_template('lost_found/index.html', items=items)


@lost_found_bp.route('/item/<int:item_id>')
def view_item(item_id):
    """View item details"""
    item = LostItem.query.get_or_404(item_id)
    item.view_count += 1
    db.session.commit()
    
    return render_template('lost_found/view_item.html', item=item)


@lost_found_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report_item():
    """Report lost or found item"""
    if request.method == 'POST':
        item = LostItem(
            user_id=current_user.id,
            item_type=request.form.get('item_type'),
            category=request.form.get('category'),
            title=request.form.get('title'),
            description=request.form.get('description'),
            brand=request.form.get('brand'),
            color=request.form.get('color'),
            location=request.form.get('location'),
            date_lost_found=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            time_approximate=request.form.get('time'),
            contact_method=request.form.get('contact_method', 'message'),
            expires_at=datetime.utcnow() + timedelta(days=60)
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('Item reported! We\'ll notify you if there\'s a match.', 'success')
        return redirect(url_for('lost_found.my_items'))
    
    return render_template('lost_found/report.html')


@lost_found_bp.route('/my-items')
@login_required
def my_items():
    """View user's reported items"""
    items = LostItem.query.filter_by(user_id=current_user.id).order_by(LostItem.created_at.desc()).all()
    return render_template('lost_found/my_items.html', items=items)


@lost_found_bp.route('/mark-claimed/<int:item_id>', methods=['POST'])
@login_required
def mark_claimed(item_id):
    """Mark item as claimed"""
    item = LostItem.query.get_or_404(item_id)
    
    if item.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('lost_found.index'))
    
    item.status = 'claimed'
    item.claimed_at = datetime.utcnow()
    db.session.commit()
    
    flash('Item marked as claimed!', 'success')
    return redirect(url_for('lost_found.my_items'))
