from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import parking_bp
from extensions import db
from models_innovative_features import ParkingSpot
from datetime import datetime

@parking_bp.route('/')
def index():
    """Browse parking spots"""
    listing_type = request.args.get('type', 'all')
    
    query = ParkingSpot.query.filter_by(status='available')
    
    if listing_type != 'all':
        query = query.filter_by(listing_type=listing_type)
    
    spots = query.order_by(ParkingSpot.price_per_day.asc()).all()
    
    return render_template('parking/index.html', spots=spots)


@parking_bp.route('/spot/<int:spot_id>')
def view_spot(spot_id):
    """View parking spot details"""
    spot = ParkingSpot.query.get_or_404(spot_id)
    return render_template('parking/view_spot.html', spot=spot)


@parking_bp.route('/list', methods=['GET', 'POST'])
@login_required
def list_spot():
    """List parking spot"""
    if request.method == 'POST':
        spot = ParkingSpot(
            user_id=current_user.id,
            listing_type=request.form.get('listing_type'),
            location_name=request.form.get('location_name'),
            distance_from_campus=float(request.form.get('distance_from_campus', 0)),
            proximity_to_buildings=request.form.get('proximity_to_buildings'),
            available_from=datetime.strptime(request.form.get('available_from'), '%Y-%m-%d').date(),
            days_available=request.form.get('days_available'),
            time_available=request.form.get('time_available'),
            price_per_day=float(request.form.get('price_per_day', 0)),
            negotiable=request.form.get('negotiable') == 'on',
            covered=request.form.get('covered') == 'on',
            reserved=request.form.get('reserved') == 'on',
            ev_charging=request.form.get('ev_charging') == 'on',
            description=request.form.get('description')
        )
        
        db.session.add(spot)
        db.session.commit()
        
        flash('Parking spot listed!', 'success')
        return redirect(url_for('parking.my_spots'))
    
    return render_template('parking/list.html')


@parking_bp.route('/my-spots')
@login_required
def my_spots():
    """View user's parking spots"""
    spots = ParkingSpot.query.filter_by(user_id=current_user.id).order_by(ParkingSpot.created_at.desc()).all()
    return render_template('parking/my_spots.html', spots=spots)
