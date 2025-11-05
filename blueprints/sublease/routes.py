from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import sublease_bp
from extensions import db
from models_innovative_features import SubleasePosting
from datetime import datetime

@sublease_bp.route('/')
def index():
    """Browse sublease listings"""
    property_type = request.args.get('type', 'all')
    min_rent = request.args.get('min_rent')
    max_rent = request.args.get('max_rent')
    bedrooms = request.args.get('bedrooms')
    
    query = SubleasePosting.query.filter_by(status='available')
    
    if property_type != 'all':
        query = query.filter_by(property_type=property_type)
    
    if min_rent:
        query = query.filter(SubleasePosting.monthly_rent >= float(min_rent))
    
    if max_rent:
        query = query.filter(SubleasePosting.monthly_rent <= float(max_rent))
    
    if bedrooms:
        query = query.filter_by(bedrooms=int(bedrooms))
    
    listings = query.order_by(SubleasePosting.created_at.desc()).all()
    
    return render_template('sublease/index.html', listings=listings)


@sublease_bp.route('/listing/<int:listing_id>')
def view_listing(listing_id):
    """View sublease listing details"""
    listing = SubleasePosting.query.get_or_404(listing_id)
    listing.view_count += 1
    db.session.commit()
    
    return render_template('sublease/view_listing.html', listing=listing)


@sublease_bp.route('/post', methods=['GET', 'POST'])
@login_required
def post_listing():
    """Post sublease listing"""
    if request.method == 'POST':
        listing = SubleasePosting(
            user_id=current_user.id,
            title=request.form.get('title'),
            address=request.form.get('address'),
            property_type=request.form.get('property_type'),
            available_from=datetime.strptime(request.form.get('available_from'), '%Y-%m-%d').date(),
            available_until=datetime.strptime(request.form.get('available_until'), '%Y-%m-%d').date(),
            monthly_rent=float(request.form.get('monthly_rent')),
            security_deposit=float(request.form.get('security_deposit', 0)),
            bedrooms=int(request.form.get('bedrooms', 1)),
            bathrooms=float(request.form.get('bathrooms', 1)),
            furnished=request.form.get('furnished') == 'on',
            utilities_included=request.form.get('utilities_included'),
            has_roommates=request.form.get('has_roommates') == 'on',
            parking_available=request.form.get('parking_available') == 'on',
            pets_allowed=request.form.get('pets_allowed') == 'on',
            laundry=request.form.get('laundry'),
            description=request.form.get('description')
        )
        
        db.session.add(listing)
        db.session.commit()
        
        flash('Sublease listing posted!', 'success')
        return redirect(url_for('sublease.my_listings'))
    
    return render_template('sublease/post.html')


@sublease_bp.route('/my-listings')
@login_required
def my_listings():
    """View user's sublease listings"""
    listings = SubleasePosting.query.filter_by(user_id=current_user.id).order_by(SubleasePosting.created_at.desc()).all()
    return render_template('sublease/my_listings.html', listings=listings)
