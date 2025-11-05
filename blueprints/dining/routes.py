"""
Dining Hall Routes - Real-time food reviews and ratings
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models_dining import (
    DiningLocation, MenuItem, MealReview, ReviewHelpful, 
    WaitTimeReport, DailySpecial, MealPlanBalance
)
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import os

dining_bp = Blueprint('dining', __name__, url_prefix='/dining')


@dining_bp.route('/')
def dining_home():
    """Main dining hall page - show all locations"""
    locations = DiningLocation.query.filter_by(is_active=True).all()
    
    # Get today's specials
    today = datetime.now().date()
    specials = DailySpecial.query.filter_by(
        special_date=today,
        is_active=True
    ).limit(5).all()
    
    # Get trending items (highest rated this week)
    week_ago = datetime.now() - timedelta(days=7)
    trending_items = MenuItem.query.join(MealReview).filter(
        MealReview.created_at >= week_ago
    ).group_by(MenuItem.id).order_by(
        desc(func.avg(MealReview.rating))
    ).limit(6).all()
    
    return render_template('dining/index.html',
                         locations=locations,
                         specials=specials,
                         trending_items=trending_items,
                         title='Campus Dining')


@dining_bp.route('/location/<int:location_id>')
def location_detail(location_id):
    """Detail page for a specific dining location"""
    location = DiningLocation.query.get_or_404(location_id)
    
    # Get recent reviews
    reviews = location.reviews.filter_by(is_hidden=False).order_by(
        desc(MealReview.created_at)
    ).limit(20).all()
    
    # Get menu items
    menu_items = location.menu_items.filter_by().order_by(
        MenuItem.category, MenuItem.name
    ).all()
    
    # Group menu by category
    menu_by_category = {}
    for item in menu_items:
        category = item.category or 'Other'
        if category not in menu_by_category:
            menu_by_category[category] = []
        menu_by_category[category].append(item)
    
    # Get current wait time
    current_wait = location.get_current_wait_time()
    
    # Check if location is open
    is_open = location.is_open_now()
    
    return render_template('dining/location_detail.html',
                         location=location,
                         reviews=reviews,
                         menu_by_category=menu_by_category,
                         current_wait=current_wait,
                         is_open=is_open,
                         title=location.name)


@dining_bp.route('/item/<int:item_id>')
def menu_item_detail(item_id):
    """Detail page for a specific menu item"""
    item = MenuItem.query.get_or_404(item_id)
    
    # Get reviews for this item
    reviews = item.reviews.filter_by(is_hidden=False).order_by(
        desc(MealReview.created_at)
    ).limit(20).all()
    
    return render_template('dining/menu_item_detail.html',
                         item=item,
                         reviews=reviews,
                         title=item.name)


@dining_bp.route('/review/new', methods=['GET', 'POST'])
@login_required
def create_review():
    """Create a new meal review"""
    if request.method == 'GET':
        # Show review form
        locations = DiningLocation.query.filter_by(is_active=True).all()
        return render_template('dining/create_review.html',
                             locations=locations,
                             title='Write a Review')
    
    # Handle POST - save review
    try:
        location_id = request.form.get('location_id', type=int)
        item_id = request.form.get('item_id', type=int) if request.form.get('item_id') else None
        rating = request.form.get('rating', type=int)
        review_text = request.form.get('review_text', '').strip()
        meal_type = request.form.get('meal_type', '')
        
        if not location_id or not rating or rating < 1 or rating > 5:
            flash('Please select a location and rating', 'error')
            return redirect(url_for('dining.create_review'))
        
        # Create review
        review = MealReview(
            user_id=current_user.id,
            dining_location_id=location_id,
            menu_item_id=item_id,
            rating=rating,
            review_text=review_text,
            meal_type=meal_type
        )
        
        db.session.add(review)
        
        # Update location average rating
        location = DiningLocation.query.get(location_id)
        location.total_reviews += 1
        avg_rating = db.session.query(func.avg(MealReview.rating)).filter(
            MealReview.dining_location_id == location_id,
            MealReview.is_hidden == False
        ).scalar()
        location.average_rating = float(avg_rating) if avg_rating else 0.0
        
        # Update menu item rating if applicable
        if item_id:
            item = MenuItem.query.get(item_id)
            item.total_reviews += 1
            avg_item_rating = db.session.query(func.avg(MealReview.rating)).filter(
                MealReview.menu_item_id == item_id,
                MealReview.is_hidden == False
            ).scalar()
            item.average_rating = float(avg_item_rating) if avg_item_rating else 0.0
        
        db.session.commit()
        
        flash('Review posted successfully!', 'success')
        return redirect(url_for('dining.location_detail', location_id=location_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error posting review: {str(e)}', 'error')
        return redirect(url_for('dining.create_review'))


@dining_bp.route('/api/review/<int:review_id>/helpful', methods=['POST'])
@login_required
def mark_helpful(review_id):
    """Mark a review as helpful"""
    try:
        review = MealReview.query.get_or_404(review_id)
        
        # Check if user already voted
        existing_vote = ReviewHelpful.query.filter_by(
            review_id=review_id,
            user_id=current_user.id
        ).first()
        
        if existing_vote:
            # Toggle vote
            db.session.delete(existing_vote)
            review.helpful_count -= 1
            action = 'removed'
        else:
            # Add vote
            vote = ReviewHelpful(
                review_id=review_id,
                user_id=current_user.id,
                is_helpful=True
            )
            db.session.add(vote)
            review.helpful_count += 1
            action = 'added'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'action': action,
            'helpful_count': review.helpful_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@dining_bp.route('/api/wait-time/report', methods=['POST'])
@login_required
def report_wait_time():
    """Report current wait time at a location"""
    try:
        data = request.get_json()
        location_id = data.get('location_id')
        wait_minutes = data.get('wait_minutes')
        crowd_level = data.get('crowd_level', 'moderate')
        
        if not location_id or wait_minutes is None:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create wait time report
        report = WaitTimeReport(
            location_id=location_id,
            user_id=current_user.id,
            wait_minutes=wait_minutes,
            crowd_level=crowd_level
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Wait time reported',
            'wait_minutes': wait_minutes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@dining_bp.route('/api/menu/items')
def get_menu_items():
    """API: Get menu items for a location"""
    location_id = request.args.get('location_id', type=int)
    
    if not location_id:
        return jsonify({'error': 'location_id required'}), 400
    
    items = MenuItem.query.filter_by(location_id=location_id).all()
    
    return jsonify({
        'items': [{
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'category': item.category,
            'price': item.price,
            'rating': item.average_rating,
            'dietary_tags': item.dietary_tags or []
        } for item in items]
    }), 200


@dining_bp.route('/trending')
def trending():
    """Show trending/popular items this week"""
    week_ago = datetime.now() - timedelta(days=7)
    
    # Get highest rated items from this week
    trending_items = db.session.query(
        MenuItem,
        func.avg(MealReview.rating).label('avg_rating'),
        func.count(MealReview.id).label('review_count')
    ).join(MealReview).filter(
        MealReview.created_at >= week_ago,
        MealReview.is_hidden == False
    ).group_by(MenuItem.id).having(
        func.count(MealReview.id) >= 3  # At least 3 reviews
    ).order_by(desc('avg_rating')).limit(20).all()
    
    return render_template('dining/trending.html',
                         trending_items=trending_items,
                         title='Trending This Week')


@dining_bp.route('/specials')
def specials():
    """Show today's specials"""
    today = datetime.now().date()
    
    specials_list = DailySpecial.query.filter_by(
        special_date=today,
        is_active=True
    ).join(DiningLocation).order_by(DiningLocation.name).all()
    
    return render_template('dining/specials.html',
                         specials=specials_list,
                         title="Today's Specials")


@dining_bp.route('/my-balance')
@login_required
def meal_plan_balance():
    """Show user's meal plan balance"""
    balance = MealPlanBalance.query.filter_by(user_id=current_user.id).first()
    
    if balance:
        # Calculate projection
        projected_end = balance.calculate_projection()
    else:
        projected_end = None
    
    return render_template('dining/meal_plan_balance.html',
                         balance=balance,
                         projected_end=projected_end,
                         title='My Meal Plan')


@dining_bp.route('/search')
def search():
    """Search menu items"""
    query = request.args.get('q', '').strip()
    dietary_filter = request.args.get('dietary', '')
    
    if not query and not dietary_filter:
        return render_template('dining/search.html',
                             results=[],
                             query='',
                             title='Search Menu')
    
    # Build query
    items_query = MenuItem.query
    
    if query:
        items_query = items_query.filter(
            db.or_(
                MenuItem.name.ilike(f'%{query}%'),
                MenuItem.description.ilike(f'%{query}%')
            )
        )
    
    if dietary_filter:
        items_query = items_query.filter(
            MenuItem.dietary_tags.contains([dietary_filter])
        )
    
    results = items_query.order_by(desc(MenuItem.average_rating)).limit(50).all()
    
    return render_template('dining/search.html',
                         results=results,
                         query=query,
                         dietary_filter=dietary_filter,
                         title='Search Results')
