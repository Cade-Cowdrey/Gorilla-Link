from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models_student_features import TextbookListing, TextbookInterest
from sqlalchemy import or_, and_
from datetime import datetime

textbook_bp = Blueprint('textbook', __name__, url_prefix='/textbooks')

@textbook_bp.route('/')
def index():
    """Textbook exchange marketplace homepage"""
    course_filter = request.args.get('course', '')
    condition_filter = request.args.get('condition', '')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'newest')
    
    query = TextbookListing.query.filter_by(status='available')
    
    # Apply filters
    if course_filter:
        query = query.filter(TextbookListing.course_code.ilike(f'%{course_filter}%'))
    
    if condition_filter:
        query = query.filter_by(condition=condition_filter)
    
    if search_query:
        query = query.filter(
            or_(
                TextbookListing.title.ilike(f'%{search_query}%'),
                TextbookListing.author.ilike(f'%{search_query}%'),
                TextbookListing.isbn.ilike(f'%{search_query}%'),
                TextbookListing.course_name.ilike(f'%{search_query}%')
            )
        )
    
    # Sorting
    if sort_by == 'price_low':
        query = query.order_by(TextbookListing.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(TextbookListing.price.desc())
    elif sort_by == 'popular':
        query = query.order_by(TextbookListing.views.desc())
    else:  # newest
        query = query.order_by(TextbookListing.created_at.desc())
    
    listings = query.limit(50).all()
    
    # Get popular courses
    popular_courses = db.session.query(
        TextbookListing.course_code,
        db.func.count(TextbookListing.id).label('count')
    ).filter_by(status='available').group_by(
        TextbookListing.course_code
    ).order_by(db.text('count DESC')).limit(10).all()
    
    return render_template('textbook_exchange/index.html',
                         listings=listings,
                         popular_courses=popular_courses,
                         course_filter=course_filter,
                         condition_filter=condition_filter,
                         search_query=search_query,
                         sort_by=sort_by)


@textbook_bp.route('/listing/<int:listing_id>')
def view_listing(listing_id):
    """View individual textbook listing"""
    listing = TextbookListing.query.get_or_404(listing_id)
    
    # Increment view count
    listing.views += 1
    db.session.commit()
    
    # Get similar books
    similar = TextbookListing.query.filter(
        and_(
            TextbookListing.id != listing_id,
            TextbookListing.status == 'available',
            or_(
                TextbookListing.course_code == listing.course_code,
                TextbookListing.isbn == listing.isbn
            )
        )
    ).limit(4).all()
    
    return render_template('textbook_exchange/listing.html',
                         listing=listing,
                         similar=similar)


@textbook_bp.route('/sell', methods=['GET', 'POST'])
@login_required
def sell_textbook():
    """List a textbook for sale"""
    if request.method == 'POST':
        listing = TextbookListing(
            user_id=current_user.id,
            title=request.form['title'],
            author=request.form.get('author'),
            isbn=request.form.get('isbn'),
            edition=request.form.get('edition'),
            course_code=request.form.get('course_code', '').upper(),
            course_name=request.form.get('course_name'),
            condition=request.form['condition'],
            price=float(request.form['price']),
            original_price=float(request.form.get('original_price', 0)) if request.form.get('original_price') else None,
            description=request.form.get('description'),
            is_negotiable=request.form.get('is_negotiable') == 'on'
        )
        
        db.session.add(listing)
        db.session.commit()
        
        flash('Your textbook has been listed successfully!', 'success')
        return redirect(url_for('textbook.view_listing', listing_id=listing.id))
    
    return render_template('textbook_exchange/sell.html')


@textbook_bp.route('/my-listings')
@login_required
def my_listings():
    """View current user's textbook listings"""
    listings = TextbookListing.query.filter_by(user_id=current_user.id).order_by(
        TextbookListing.created_at.desc()
    ).all()
    
    return render_template('textbook_exchange/my_listings.html', listings=listings)


@textbook_bp.route('/edit/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    """Edit a textbook listing"""
    listing = TextbookListing.query.get_or_404(listing_id)
    
    if listing.user_id != current_user.id:
        flash('You can only edit your own listings.', 'danger')
        return redirect(url_for('textbook.index'))
    
    if request.method == 'POST':
        listing.title = request.form['title']
        listing.author = request.form.get('author')
        listing.isbn = request.form.get('isbn')
        listing.edition = request.form.get('edition')
        listing.course_code = request.form.get('course_code', '').upper()
        listing.course_name = request.form.get('course_name')
        listing.condition = request.form['condition']
        listing.price = float(request.form['price'])
        listing.description = request.form.get('description')
        listing.is_negotiable = request.form.get('is_negotiable') == 'on'
        listing.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Listing updated successfully!', 'success')
        return redirect(url_for('textbook.view_listing', listing_id=listing.id))
    
    return render_template('textbook_exchange/edit.html', listing=listing)


@textbook_bp.route('/delete/<int:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    """Delete a textbook listing"""
    listing = TextbookListing.query.get_or_404(listing_id)
    
    if listing.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(listing)
    db.session.commit()
    
    flash('Listing deleted successfully.', 'success')
    return redirect(url_for('textbook.my_listings'))


@textbook_bp.route('/mark-sold/<int:listing_id>', methods=['POST'])
@login_required
def mark_sold(listing_id):
    """Mark listing as sold"""
    listing = TextbookListing.query.get_or_404(listing_id)
    
    if listing.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    listing.status = 'sold'
    listing.sold_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Marked as sold'})


@textbook_bp.route('/interest/<int:listing_id>', methods=['POST'])
@login_required
def express_interest(listing_id):
    """Express interest in buying a textbook"""
    listing = TextbookListing.query.get_or_404(listing_id)
    
    if listing.user_id == current_user.id:
        return jsonify({'error': 'Cannot buy your own listing'}), 400
    
    interest = TextbookInterest(
        listing_id=listing_id,
        user_id=current_user.id,
        message=request.form.get('message'),
        offer_price=float(request.form.get('offer_price')) if request.form.get('offer_price') else None
    )
    
    db.session.add(interest)
    db.session.commit()
    
    flash('Your interest has been sent to the seller!', 'success')
    return redirect(url_for('textbook.view_listing', listing_id=listing_id))
