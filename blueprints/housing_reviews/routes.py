from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models_advanced_features import HousingListing
from models_student_features import HousingReview
from sqlalchemy import or_, func
from datetime import datetime

housing_bp = Blueprint('housing_reviews', __name__, url_prefix='/housing')

@housing_bp.route('/')
def index():
    """Housing reviews homepage"""
    property_type = request.args.get('type', '')
    min_rent = request.args.get('min_rent', type=int)
    max_rent = request.args.get('max_rent', type=int)
    bedrooms = request.args.get('bedrooms', type=int)
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'rating')
    
    query = HousingListing.query
    
    # Apply filters
    if property_type:
        query = query.filter_by(property_type=property_type)
    
    if min_rent:
        query = query.filter(HousingListing.rent_min >= min_rent)
    
    if max_rent:
        query = query.filter(HousingListing.rent_max <= max_rent)
    
    if bedrooms:
        query = query.filter_by(bedrooms=bedrooms)
    
    if search_query:
        query = query.filter(
            or_(
                HousingListing.property_name.ilike(f'%{search_query}%'),
                HousingListing.address.ilike(f'%{search_query}%'),
                HousingListing.landlord_name.ilike(f'%{search_query}%')
            )
        )
    
    # Sorting
    if sort_by == 'price_low':
        query = query.order_by(HousingListing.rent_min.asc())
    elif sort_by == 'price_high':
        query = query.order_by(HousingListing.rent_max.desc())
    elif sort_by == 'distance':
        query = query.order_by(HousingListing.distance_to_campus.asc())
    elif sort_by == 'newest':
        query = query.order_by(HousingListing.created_at.desc())
    else:  # rating
        query = query.order_by(HousingListing.avg_rating.desc())
    
    listings = query.limit(50).all()
    
    return render_template('housing_reviews/index.html',
                         listings=listings,
                         property_type=property_type,
                         sort_by=sort_by,
                         search_query=search_query)


@housing_bp.route('/property/<int:listing_id>')
def view_property(listing_id):
    """View property details and reviews"""
    listing = HousingListing.query.get_or_404(listing_id)
    
    # Get reviews with pagination
    page = request.args.get('page', 1, type=int)
    reviews = HousingReview.query.filter_by(listing_id=listing_id).order_by(
        HousingReview.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('housing_reviews/property.html',
                         listing=listing,
                         reviews=reviews)


@housing_bp.route('/add-property', methods=['GET', 'POST'])
@login_required
def add_property():
    """Add a new housing property"""
    if request.method == 'POST':
        listing = HousingListing(
            property_name=request.form['property_name'],
            address=request.form['address'],
            landlord_name=request.form.get('landlord_name'),
            landlord_contact=request.form.get('landlord_contact'),
            property_type=request.form['property_type'],
            bedrooms=int(request.form['bedrooms']) if request.form.get('bedrooms') else None,
            bathrooms=float(request.form['bathrooms']) if request.form.get('bathrooms') else None,
            rent_min=float(request.form['rent_min']) if request.form.get('rent_min') else None,
            rent_max=float(request.form['rent_max']) if request.form.get('rent_max') else None,
            amenities=request.form.get('amenities'),
            utilities_included=request.form.get('utilities_included'),
            distance_to_campus=float(request.form['distance_to_campus']) if request.form.get('distance_to_campus') else None
        )
        
        db.session.add(listing)
        db.session.commit()
        
        flash('Property added successfully!', 'success')
        return redirect(url_for('housing.view_property', listing_id=listing.id))
    
    return render_template('housing_reviews/add_property.html')


@housing_bp.route('/review/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def add_review(listing_id):
    """Add a review for a property"""
    listing = HousingListing.query.get_or_404(listing_id)
    
    # Check if user already reviewed
    existing_review = HousingReview.query.filter_by(
        listing_id=listing_id,
        user_id=current_user.id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this property.', 'warning')
        return redirect(url_for('housing.view_property', listing_id=listing_id))
    
    if request.method == 'POST':
        review = HousingReview(
            listing_id=listing_id,
            user_id=current_user.id,
            overall_rating=int(request.form['overall_rating']),
            safety_rating=int(request.form.get('safety_rating', 0)) or None,
            maintenance_rating=int(request.form.get('maintenance_rating', 0)) or None,
            value_rating=int(request.form.get('value_rating', 0)) or None,
            landlord_rating=int(request.form.get('landlord_rating', 0)) or None,
            title=request.form.get('title'),
            review_text=request.form['review_text'],
            pros=request.form.get('pros'),
            cons=request.form.get('cons'),
            would_recommend=request.form.get('would_recommend') == 'on',
            verified_resident=request.form.get('verified_resident') == 'on'
        )
        
        db.session.add(review)
        
        # Update listing averages
        listing.review_count += 1
        
        # Recalculate averages
        avg_ratings = db.session.query(
            func.avg(HousingReview.overall_rating).label('overall'),
            func.avg(HousingReview.safety_rating).label('safety'),
            func.avg(HousingReview.maintenance_rating).label('maintenance'),
            func.avg(HousingReview.value_rating).label('value')
        ).filter_by(listing_id=listing_id).first()
        
        listing.avg_rating = float(avg_ratings.overall) if avg_ratings.overall else 0
        listing.avg_safety_rating = float(avg_ratings.safety) if avg_ratings.safety else 0
        listing.avg_maintenance_rating = float(avg_ratings.maintenance) if avg_ratings.maintenance else 0
        listing.avg_value_rating = float(avg_ratings.value) if avg_ratings.value else 0
        
        db.session.commit()
        
        flash('Your review has been posted!', 'success')
        return redirect(url_for('housing.view_property', listing_id=listing_id))
    
    return render_template('housing_reviews/add_review.html', listing=listing)


@housing_bp.route('/helpful/<int:review_id>', methods=['POST'])
@login_required
def mark_helpful(review_id):
    """Mark a review as helpful"""
    review = HousingReview.query.get_or_404(review_id)
    review.helpful_count += 1
    db.session.commit()
    
    return jsonify({'helpful_count': review.helpful_count})
