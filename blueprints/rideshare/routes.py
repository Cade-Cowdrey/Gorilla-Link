from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import rideshare_bp
from extensions import db
from models_innovative_features import RideShare, RideRequest
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

@rideshare_bp.route('/')
def index():
    """Browse available rides"""
    # Get filter parameters
    direction = request.args.get('direction', 'all')
    origin = request.args.get('origin', '')
    date_from = request.args.get('date')
    trip_type = request.args.get('type', 'all')
    
    # Base query - only active rides with available seats
    query = RideShare.query.filter(
        RideShare.status == 'active',
        RideShare.available_seats > 0,
        RideShare.departure_date >= datetime.utcnow()
    )
    
    # Apply filters
    if direction != 'all':
        query = query.filter(RideShare.direction == direction)
    
    if origin:
        query = query.filter(
            or_(
                RideShare.origin_city.ilike(f'%{origin}%'),
                RideShare.destination_city.ilike(f'%{origin}%')
            )
        )
    
    if date_from:
        try:
            date_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(RideShare.departure_date >= date_obj)
        except ValueError:
            pass
    
    if trip_type != 'all':
        query = query.filter(RideShare.trip_type == trip_type)
    
    # Order by date
    rides = query.order_by(RideShare.departure_date.asc()).all()
    
    return render_template('rideshare/index.html', rides=rides)


@rideshare_bp.route('/ride/<int:ride_id>')
def view_ride(ride_id):
    """View ride details"""
    ride = RideShare.query.get_or_404(ride_id)
    
    # Increment view count
    ride.view_count += 1
    db.session.commit()
    
    # Check if user already requested this ride
    has_requested = False
    if current_user.is_authenticated:
        has_requested = RideRequest.query.filter_by(
            ride_id=ride_id,
            rider_id=current_user.id
        ).first() is not None
    
    return render_template('rideshare/view_ride.html', ride=ride, has_requested=has_requested)


@rideshare_bp.route('/offer', methods=['GET', 'POST'])
@login_required
def offer_ride():
    """Create new ride offer"""
    if request.method == 'POST':
        # Create ride
        ride = RideShare(
            driver_id=current_user.id,
            trip_type=request.form.get('trip_type'),
            direction=request.form.get('direction'),
            origin_city=request.form.get('origin_city'),
            origin_state=request.form.get('origin_state'),
            origin_zip=request.form.get('origin_zip'),
            destination_city=request.form.get('destination_city'),
            departure_date=datetime.strptime(request.form.get('departure_date'), '%Y-%m-%d'),
            departure_time=request.form.get('departure_time'),
            available_seats=int(request.form.get('available_seats')),
            total_seats=int(request.form.get('available_seats')),
            cost_per_person=float(request.form.get('cost_per_person', 0)) if request.form.get('cost_per_person') else 0,
            is_free=request.form.get('is_free') == 'on',
            no_smoking=request.form.get('no_smoking') == 'on',
            luggage_space=request.form.get('luggage_space') == 'on',
            stops_allowed=request.form.get('stops_allowed') == 'on',
            notes=request.form.get('notes'),
            phone_number=request.form.get('phone_number')
        )
        
        # Handle recurring rides
        if ride.trip_type == 'recurring':
            ride.recurring_days = request.form.get('recurring_days')
            ride.recurring_until = datetime.strptime(request.form.get('recurring_until'), '%Y-%m-%d').date()
        
        # Handle return trip
        if request.form.get('return_date'):
            ride.return_date = datetime.strptime(request.form.get('return_date'), '%Y-%m-%d')
        
        db.session.add(ride)
        db.session.commit()
        
        flash('Your ride has been posted! Students will be able to request to join.', 'success')
        return redirect(url_for('rideshare.my_rides'))
    
    return render_template('rideshare/offer_ride.html')


@rideshare_bp.route('/request/<int:ride_id>', methods=['POST'])
@login_required
def request_ride(ride_id):
    """Request to join a ride"""
    ride = RideShare.query.get_or_404(ride_id)
    
    # Check if already requested
    existing = RideRequest.query.filter_by(
        ride_id=ride_id,
        rider_id=current_user.id
    ).first()
    
    if existing:
        flash('You have already requested this ride.', 'info')
        return redirect(url_for('rideshare.view_ride', ride_id=ride_id))
    
    # Check if seats available
    if ride.available_seats <= 0:
        flash('Sorry, this ride is full.', 'error')
        return redirect(url_for('rideshare.view_ride', ride_id=ride_id))
    
    # Create request
    ride_request = RideRequest(
        ride_id=ride_id,
        rider_id=current_user.id,
        seats_requested=int(request.form.get('seats', 1)),
        message=request.form.get('message', '')
    )
    
    db.session.add(ride_request)
    db.session.commit()
    
    flash('Your request has been sent to the driver!', 'success')
    return redirect(url_for('rideshare.view_ride', ride_id=ride_id))


@rideshare_bp.route('/my-rides')
@login_required
def my_rides():
    """View user's offered rides and requests"""
    # Rides offered by user
    offered_rides = RideShare.query.filter_by(driver_id=current_user.id).order_by(RideShare.departure_date.desc()).all()
    
    # Rides requested by user
    requests = RideRequest.query.filter_by(rider_id=current_user.id).order_by(RideRequest.requested_at.desc()).all()
    
    return render_template('rideshare/my_rides.html', offered_rides=offered_rides, requests=requests)


@rideshare_bp.route('/manage-requests/<int:ride_id>')
@login_required
def manage_requests(ride_id):
    """Manage ride requests (driver only)"""
    ride = RideShare.query.get_or_404(ride_id)
    
    # Verify ownership
    if ride.driver_id != current_user.id:
        flash('You can only manage your own rides.', 'error')
        return redirect(url_for('rideshare.index'))
    
    requests = RideRequest.query.filter_by(ride_id=ride_id).order_by(RideRequest.requested_at.desc()).all()
    
    return render_template('rideshare/manage_requests.html', ride=ride, requests=requests)


@rideshare_bp.route('/respond-request/<int:request_id>', methods=['POST'])
@login_required
def respond_to_request(request_id):
    """Accept or decline a ride request"""
    ride_request = RideRequest.query.get_or_404(request_id)
    ride = ride_request.ride
    
    # Verify ownership
    if ride.driver_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('rideshare.index'))
    
    action = request.form.get('action')
    
    if action == 'accept':
        # Check if enough seats
        if ride.available_seats >= ride_request.seats_requested:
            ride_request.status = 'accepted'
            ride_request.responded_at = datetime.utcnow()
            ride.available_seats -= ride_request.seats_requested
            
            # Mark ride as full if no seats left
            if ride.available_seats == 0:
                ride.status = 'full'
            
            flash(f'Accepted {ride_request.rider.name}\'s request!', 'success')
        else:
            flash('Not enough seats available.', 'error')
    
    elif action == 'decline':
        ride_request.status = 'declined'
        ride_request.responded_at = datetime.utcnow()
        flash('Request declined.', 'info')
    
    db.session.commit()
    return redirect(url_for('rideshare.manage_requests', ride_id=ride.id))


@rideshare_bp.route('/cancel-ride/<int:ride_id>', methods=['POST'])
@login_required
def cancel_ride(ride_id):
    """Cancel a ride offer"""
    ride = RideShare.query.get_or_404(ride_id)
    
    if ride.driver_id != current_user.id:
        flash('You can only cancel your own rides.', 'error')
        return redirect(url_for('rideshare.index'))
    
    ride.status = 'cancelled'
    db.session.commit()
    
    flash('Your ride has been cancelled.', 'info')
    return redirect(url_for('rideshare.my_rides'))


@rideshare_bp.route('/popular-routes')
def popular_routes():
    """Show most common routes"""
    # Get popular city pairs
    from sqlalchemy import func
    
    routes = db.session.query(
        RideShare.origin_city,
        RideShare.destination_city,
        func.count(RideShare.id).label('count')
    ).filter(
        RideShare.status == 'active'
    ).group_by(
        RideShare.origin_city,
        RideShare.destination_city
    ).order_by(
        func.count(RideShare.id).desc()
    ).limit(10).all()
    
    return render_template('rideshare/popular_routes.html', routes=routes)
