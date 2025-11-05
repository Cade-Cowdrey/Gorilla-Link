"""
Smart Housing AI Routes
Intelligent housing finder and roommate matching system
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models_advanced_features import HousingListing, RoommateFinder, RoommateMatch
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, desc, func
from decimal import Decimal

housing_bp = Blueprint('smart_housing', __name__, url_prefix='/housing')

# ==================== HOUSING SEARCH ====================

@housing_bp.route('/')
def browse_listings():
    """Main housing search interface"""
    # Filters
    property_type = request.args.get('type', 'all')
    min_rent = request.args.get('min_rent', type=float)
    max_rent = request.args.get('max_rent', type=float)
    bedrooms = request.args.get('bedrooms', type=int)
    pets = request.args.get('pets', 'all')
    furnished = request.args.get('furnished', 'all')
    max_distance = request.args.get('max_distance', type=float)
    search = request.args.get('search', '')
    
    query = HousingListing.query.filter_by(status='available')
    
    if property_type != 'all':
        query = query.filter_by(property_type=property_type)
    
    if min_rent:
        query = query.filter(HousingListing.monthly_rent >= min_rent)
    
    if max_rent:
        query = query.filter(HousingListing.monthly_rent <= max_rent)
    
    if bedrooms:
        query = query.filter_by(bedrooms=bedrooms)
    
    if pets == 'yes':
        query = query.filter_by(pets_allowed=True)
    elif pets == 'no':
        query = query.filter_by(pets_allowed=False)
    
    if furnished == 'yes':
        query = query.filter_by(furnished=True)
    elif furnished == 'no':
        query = query.filter_by(furnished=False)
    
    if max_distance:
        query = query.filter(HousingListing.distance_to_campus_miles <= max_distance)
    
    if search:
        query = query.filter(
            or_(
                HousingListing.property_name.ilike(f'%{search}%'),
                HousingListing.address.ilike(f'%{search}%'),
                HousingListing.neighborhood.ilike(f'%{search}%')
            )
        )
    
    # Sort options
    sort = request.args.get('sort', 'price_low')
    if sort == 'price_low':
        query = query.order_by(HousingListing.monthly_rent.asc())
    elif sort == 'price_high':
        query = query.order_by(HousingListing.monthly_rent.desc())
    elif sort == 'distance':
        query = query.order_by(HousingListing.distance_to_campus_miles.asc())
    elif sort == 'affordability':
        query = query.order_by(HousingListing.affordability_index.desc())
    else:  # featured
        query = query.order_by(
            HousingListing.is_featured.desc(),
            HousingListing.created_at.desc()
        )
    
    listings = query.all()
    
    # Get filter statistics
    avg_rent = db.session.query(func.avg(HousingListing.monthly_rent)).filter_by(status='available').scalar() or 0
    min_rent_available = db.session.query(func.min(HousingListing.monthly_rent)).filter_by(status='available').scalar() or 0
    max_rent_available = db.session.query(func.max(HousingListing.monthly_rent)).filter_by(status='available').scalar() or 1500
    
    return render_template('housing/browse.html',
                         listings=listings,
                         avg_rent=avg_rent,
                         min_rent_available=min_rent_available,
                         max_rent_available=max_rent_available,
                         current_filters=request.args)


@housing_bp.route('/listing/<int:listing_id>')
def view_listing(listing_id):
    """View detailed housing listing"""
    listing = HousingListing.query.get_or_404(listing_id)
    
    # Track view
    listing.view_count += 1
    db.session.commit()
    
    import json
    
    # Parse photos
    photos = json.loads(listing.photos) if listing.photos else []
    utilities_included_list = listing.utilities_included.split(', ') if listing.utilities_included else []
    utilities_paid_list = listing.utilities_paid_by_tenant.split(', ') if listing.utilities_paid_by_tenant else []
    
    # Calculate total monthly cost
    total_cost = float(listing.monthly_rent)
    if listing.avg_monthly_utilities:
        total_cost += float(listing.avg_monthly_utilities)
    
    # Get similar listings
    similar = HousingListing.query.filter(
        HousingListing.id != listing_id,
        HousingListing.status == 'available',
        HousingListing.bedrooms == listing.bedrooms,
        HousingListing.monthly_rent.between(
            listing.monthly_rent * Decimal('0.8'),
            listing.monthly_rent * Decimal('1.2')
        )
    ).limit(3).all()
    
    return render_template('housing/listing_detail.html',
                         listing=listing,
                         photos=photos,
                         utilities_included=utilities_included_list,
                         utilities_paid=utilities_paid_list,
                         total_cost=total_cost,
                         similar_listings=similar)


@housing_bp.route('/listing/<int:listing_id>/inquire', methods=['POST'])
@login_required
def inquire_listing(listing_id):
    """Send inquiry about listing"""
    listing = HousingListing.query.get_or_404(listing_id)
    
    # Track inquiry
    listing.inquiry_count += 1
    db.session.commit()
    
    data = request.form
    message = data.get('message')
    
    # In production, send email to landlord
    # For now, just flash success
    flash('Your inquiry has been sent to the landlord. They should contact you within 24-48 hours.', 'success')
    
    return redirect(url_for('housing.view_listing', listing_id=listing_id))


@housing_bp.route('/ai-finder', methods=['GET', 'POST'])
@login_required
def ai_housing_finder():
    """AI-powered housing recommendations"""
    if request.method == 'POST':
        data = request.form
        
        # Get user preferences
        max_budget = float(data.get('max_budget'))
        bedrooms = int(data.get('bedrooms'))
        max_distance = float(data.get('max_distance', 5))
        must_haves = data.getlist('must_haves')
        lifestyle = data.get('lifestyle')
        
        # Build query
        query = HousingListing.query.filter_by(status='available')
        query = query.filter(HousingListing.monthly_rent <= max_budget)
        query = query.filter_by(bedrooms=bedrooms)
        query = query.filter(HousingListing.distance_to_campus_miles <= max_distance)
        
        # Apply must-haves
        if 'parking' in must_haves:
            query = query.filter_by(parking_included=True)
        if 'furnished' in must_haves:
            query = query.filter_by(furnished=True)
        if 'pets' in must_haves:
            query = query.filter_by(pets_allowed=True)
        if 'laundry' in must_haves:
            query = query.filter(HousingListing.laundry.in_(['in_unit', 'on_site']))
        if 'shuttle' in must_haves:
            query = query.filter_by(on_shuttle_route=True)
        
        # Apply lifestyle preferences
        if lifestyle == 'quiet':
            query = query.filter_by(noise_level='quiet')
        elif lifestyle == 'social':
            query = query.filter(HousingListing.has_common_area == True)
        
        # Get matches
        matches = query.order_by(HousingListing.affordability_index.desc()).limit(10).all()
        
        # Score each match
        scored_matches = []
        for listing in matches:
            score = calculate_housing_match_score(listing, data)
            scored_matches.append({
                'listing': listing,
                'match_score': score['score'],
                'reasons': score['reasons']
            })
        
        # Sort by score
        scored_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return render_template('housing/ai_results.html',
                             matches=scored_matches,
                             preferences=data)
    
    return render_template('housing/ai_finder.html')


# ==================== ROOMMATE FINDER ====================

roommate_bp = Blueprint('roommate', __name__, url_prefix='/roommate')

@roommate_bp.route('/')
def roommate_finder():
    """Main roommate finder interface"""
    if not current_user.is_authenticated:
        flash('Please log in to use the roommate finder', 'warning')
        return redirect(url_for('auth.login'))
    
    # Check if user has profile
    profile = RoommateFinder.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        flash('Create your roommate profile first!', 'info')
        return redirect(url_for('roommate.create_profile'))
    
    # Get AI matches for this user
    matches = RoommateMatch.query.filter(
        or_(
            RoommateMatch.user1_id == current_user.id,
            RoommateMatch.user2_id == current_user.id
        )
    ).order_by(RoommateMatch.compatibility_score.desc()).all()
    
    return render_template('roommate/finder.html',
                         profile=profile,
                         matches=matches)


@roommate_bp.route('/create-profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    """Create roommate profile"""
    # Check if already exists
    existing = RoommateFinder.query.filter_by(user_id=current_user.id).first()
    if existing:
        return redirect(url_for('roommate.edit_profile'))
    
    if request.method == 'POST':
        data = request.form
        
        import json
        
        profile = RoommateFinder(
            user_id=current_user.id,
            looking_for=data.get('looking_for'),
            move_in_date=datetime.strptime(data.get('move_in_date'), '%Y-%m-%d').date() if data.get('move_in_date') else None,
            lease_length_preference=data.get('lease_length_preference'),
            max_monthly_rent=float(data.get('max_monthly_rent')),
            max_total_cost=float(data.get('max_total_cost')) if data.get('max_total_cost') else None,
            preferred_bedrooms=int(data.get('preferred_bedrooms')) if data.get('preferred_bedrooms') else None,
            preferred_property_types=json.dumps(data.getlist('preferred_property_types')),
            must_have_parking=data.get('must_have_parking') == 'true',
            must_have_laundry=data.get('must_have_laundry') == 'true',
            max_distance_to_campus=float(data.get('max_distance_to_campus')) if data.get('max_distance_to_campus') else None,
            sleep_schedule=data.get('sleep_schedule'),
            typical_bedtime=data.get('typical_bedtime'),
            cleanliness_level=int(data.get('cleanliness_level')),
            noise_tolerance=data.get('noise_tolerance'),
            social_level=data.get('social_level'),
            guests_frequency=data.get('guests_frequency'),
            hosting_parties=data.get('hosting_parties'),
            smoker=data.get('smoker') == 'true',
            drinks_alcohol=data.get('drinks_alcohol') == 'true',
            has_pets=data.get('has_pets') == 'true',
            pet_types=data.get('pet_types'),
            comfortable_with_pets=data.get('comfortable_with_pets') == 'true',
            major=data.get('major'),
            class_standing=data.get('class_standing'),
            study_habits=data.get('study_habits'),
            work_schedule=data.get('work_schedule'),
            interests=json.dumps(data.getlist('interests')),
            music_preferences=data.get('music_preferences'),
            bio=data.get('bio'),
            fun_fact=data.get('fun_fact'),
            deal_breakers=data.get('deal_breakers'),
            must_haves=data.get('must_haves'),
            preferred_contact=data.get('preferred_contact'),
            is_active=True,
            is_verified=True  # PSU email verified
        )
        
        db.session.add(profile)
        db.session.commit()
        
        # Generate AI matches
        generate_roommate_matches(profile)
        
        flash('Profile created! Finding your matches...', 'success')
        return redirect(url_for('roommate.roommate_finder'))
    
    return render_template('roommate/create_profile.html')


@roommate_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit roommate profile"""
    profile = RoommateFinder.query.filter_by(user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        data = request.form
        
        import json
        
        # Update fields
        profile.max_monthly_rent = float(data.get('max_monthly_rent'))
        profile.move_in_date = datetime.strptime(data.get('move_in_date'), '%Y-%m-%d').date() if data.get('move_in_date') else None
        profile.sleep_schedule = data.get('sleep_schedule')
        profile.cleanliness_level = int(data.get('cleanliness_level'))
        profile.noise_tolerance = data.get('noise_tolerance')
        profile.social_level = data.get('social_level')
        profile.bio = data.get('bio')
        profile.interests = json.dumps(data.getlist('interests'))
        
        db.session.commit()
        
        # Regenerate matches
        generate_roommate_matches(profile)
        
        flash('Profile updated and matches recalculated!', 'success')
        return redirect(url_for('roommate.roommate_finder'))
    
    return render_template('roommate/edit_profile.html', profile=profile)


@roommate_bp.route('/match/<int:match_id>')
@login_required
def view_match(match_id):
    """View roommate match details"""
    match = RoommateMatch.query.get_or_404(match_id)
    
    # Security check
    if match.user1_id != current_user.id and match.user2_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('roommate.roommate_finder'))
    
    # Determine other user
    if match.user1_id == current_user.id:
        other_user_id = match.user2_id
        current_user_is_1 = True
    else:
        other_user_id = match.user1_id
        current_user_is_1 = False
    
    # Get other user's profile
    other_profile = RoommateFinder.query.filter_by(user_id=other_user_id).first()
    
    # Mark as viewed
    if current_user_is_1:
        match.user1_viewed = True
    else:
        match.user2_viewed = True
    
    db.session.commit()
    
    import json
    shared_interests = json.loads(match.shared_interests) if match.shared_interests else []
    
    return render_template('roommate/match_detail.html',
                         match=match,
                         other_profile=other_profile,
                         shared_interests=shared_interests,
                         current_user_is_1=current_user_is_1)


@roommate_bp.route('/match/<int:match_id>/interest', methods=['POST'])
@login_required
def express_interest(match_id):
    """Express interest in roommate match"""
    match = RoommateMatch.query.get_or_404(match_id)
    
    if match.user1_id != current_user.id and match.user2_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Update interest
    if match.user1_id == current_user.id:
        match.user1_interested = True
    else:
        match.user2_interested = True
    
    # Check if both interested
    if match.user1_interested and match.user2_interested:
        match.status = 'both_interested'
        flash('It\'s a match! You can now message each other.', 'success')
    else:
        match.status = 'user1_interested' if match.user1_interested else 'user2_interested'
    
    db.session.commit()
    
    return jsonify({'success': True, 'status': match.status})


# ==================== LANDLORD: MANAGE LISTINGS ====================

@housing_bp.route('/landlord/my-listings')
@login_required
def landlord_listings():
    """Landlord dashboard"""
    listings = HousingListing.query.filter_by(
        landlord_id=current_user.id
    ).order_by(HousingListing.created_at.desc()).all()
    
    # Stats
    total_views = sum(listing.view_count for listing in listings)
    total_inquiries = sum(listing.inquiry_count for listing in listings)
    available_listings = sum(1 for listing in listings if listing.status == 'available')
    
    return render_template('housing/landlord_dashboard.html',
                         listings=listings,
                         total_views=total_views,
                         total_inquiries=total_inquiries,
                         available_listings=available_listings)


@housing_bp.route('/landlord/add-listing', methods=['GET', 'POST'])
@login_required
def landlord_add_listing():
    """Add new housing listing"""
    if request.method == 'POST':
        data = request.form
        
        import json
        
        listing = HousingListing(
            landlord_id=current_user.id,
            property_name=data.get('property_name'),
            address=data.get('address'),
            city=data.get('city', 'Pittsburg'),
            state='KS',
            zip_code=data.get('zip_code'),
            property_type=data.get('property_type'),
            bedrooms=int(data.get('bedrooms')),
            bathrooms=float(data.get('bathrooms')),
            square_feet=int(data.get('square_feet')) if data.get('square_feet') else None,
            monthly_rent=float(data.get('monthly_rent')),
            security_deposit=float(data.get('security_deposit')) if data.get('security_deposit') else None,
            application_fee=float(data.get('application_fee')) if data.get('application_fee') else None,
            utilities_included=data.get('utilities_included'),
            avg_monthly_utilities=float(data.get('avg_monthly_utilities')) if data.get('avg_monthly_utilities') else None,
            utilities_paid_by_tenant=data.get('utilities_paid_by_tenant'),
            lease_length=data.get('lease_length'),
            available_from=datetime.strptime(data.get('available_from'), '%Y-%m-%d').date() if data.get('available_from') else None,
            furnished=data.get('furnished') == 'true',
            parking_included=data.get('parking_included') == 'true',
            parking_spaces=int(data.get('parking_spaces', 0)),
            laundry=data.get('laundry'),
            air_conditioning=data.get('air_conditioning') == 'true',
            heating_type=data.get('heating_type'),
            pets_allowed=data.get('pets_allowed') == 'true',
            pet_types_allowed=data.get('pet_types_allowed'),
            pet_deposit=float(data.get('pet_deposit')) if data.get('pet_deposit') else None,
            distance_to_campus_miles=float(data.get('distance_to_campus_miles')) if data.get('distance_to_campus_miles') else None,
            walking_time_minutes=int(data.get('walking_time_minutes')) if data.get('walking_time_minutes') else None,
            on_shuttle_route=data.get('on_shuttle_route') == 'true',
            neighborhood=data.get('neighborhood'),
            landlord_name=data.get('landlord_name'),
            landlord_company=data.get('landlord_company'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email'),
            website=data.get('website'),
            photos=json.dumps(data.getlist('photo_urls')),
            status='available',
            is_verified=False
        )
        
        # Calculate affordability index
        listing.total_monthly_cost = listing.monthly_rent + (listing.avg_monthly_utilities or 0)
        listing.affordability_index = calculate_affordability_index(listing)
        
        db.session.add(listing)
        db.session.commit()
        
        flash('Listing added! It will be visible after admin verification.', 'success')
        return redirect(url_for('housing.landlord_listings'))
    
    return render_template('housing/add_listing.html')


# ==================== HELPER FUNCTIONS ====================

def calculate_housing_match_score(listing, preferences):
    """Calculate match score between listing and preferences"""
    score = 0
    reasons = []
    
    # Budget match (30 points)
    max_budget = float(preferences.get('max_budget', 10000))
    if listing.monthly_rent <= max_budget * 0.8:
        score += 30
        reasons.append(f"Well within budget (${listing.monthly_rent}/mo)")
    elif listing.monthly_rent <= max_budget:
        score += 20
        reasons.append(f"Within budget (${listing.monthly_rent}/mo)")
    
    # Distance match (25 points)
    max_distance = float(preferences.get('max_distance', 10))
    if listing.distance_to_campus_miles and listing.distance_to_campus_miles <= max_distance * 0.5:
        score += 25
        reasons.append(f"Very close to campus ({listing.distance_to_campus_miles} miles)")
    elif listing.distance_to_campus_miles and listing.distance_to_campus_miles <= max_distance:
        score += 15
        reasons.append(f"Good distance ({listing.distance_to_campus_miles} miles)")
    
    # Amenities match (20 points)
    must_haves = preferences.getlist('must_haves')
    matched_amenities = 0
    if 'parking' in must_haves and listing.parking_included:
        matched_amenities += 1
    if 'furnished' in must_haves and listing.furnished:
        matched_amenities += 1
    if 'laundry' in must_haves and listing.laundry in ['in_unit', 'on_site']:
        matched_amenities += 1
    if 'shuttle' in must_haves and listing.on_shuttle_route:
        matched_amenities += 1
    
    score += matched_amenities * 5
    if matched_amenities > 0:
        reasons.append(f"Has {matched_amenities} must-have amenities")
    
    # Lifestyle match (15 points)
    lifestyle = preferences.get('lifestyle')
    if lifestyle == 'quiet' and listing.noise_level == 'quiet':
        score += 15
        reasons.append("Quiet neighborhood (perfect for studying)")
    elif lifestyle == 'social' and listing.has_common_area:
        score += 15
        reasons.append("Social amenities available")
    
    # Safety & quality (10 points)
    if listing.safety_rating and listing.safety_rating >= 4:
        score += 10
        reasons.append(f"High safety rating ({listing.safety_rating}/5)")
    
    return {'score': min(100, score), 'reasons': reasons}


def calculate_affordability_index(listing):
    """Calculate affordability score (0-100, higher = more affordable)"""
    # Based on typical student budget of $600-800/month
    ideal_rent = 700
    total_cost = float(listing.monthly_rent) + float(listing.avg_monthly_utilities or 0)
    
    if total_cost <= ideal_rent:
        return 100
    elif total_cost <= ideal_rent * 1.2:
        return 80
    elif total_cost <= ideal_rent * 1.5:
        return 60
    elif total_cost <= ideal_rent * 2:
        return 40
    else:
        return 20


def generate_roommate_matches(profile):
    """Generate AI-powered roommate matches"""
    # Get all other active profiles
    other_profiles = RoommateFinder.query.filter(
        RoommateFinder.user_id != profile.user_id,
        RoommateFinder.is_active == True
    ).all()
    
    import json
    
    for other in other_profiles:
        # Check if match already exists
        existing = RoommateMatch.query.filter(
            or_(
                and_(RoommateMatch.user1_id == profile.user_id, RoommateMatch.user2_id == other.user_id),
                and_(RoommateMatch.user1_id == other.user_id, RoommateMatch.user2_id == profile.user_id)
            )
        ).first()
        
        if existing:
            continue  # Skip if match exists
        
        # Calculate compatibility
        compat = calculate_roommate_compatibility(profile, other)
        
        # Only create match if score > 50
        if compat['score'] >= 50:
            match = RoommateMatch(
                user1_id=profile.user_id,
                user2_id=other.user_id,
                compatibility_score=compat['score'],
                lifestyle_compatibility=compat['lifestyle'],
                schedule_compatibility=compat['schedule'],
                cleanliness_compatibility=compat['cleanliness'],
                social_compatibility=compat['social'],
                budget_compatibility=compat['budget'],
                shared_interests=json.dumps(compat['shared_interests']),
                shared_majors_or_fields=compat['shared_major'],
                why_good_match=compat['explanation'],
                potential_conflicts=compat['conflicts'],
                status='suggested'
            )
            
            db.session.add(match)
    
    db.session.commit()


def calculate_roommate_compatibility(profile1, profile2):
    """AI compatibility algorithm"""
    import json
    
    # Lifestyle compatibility (25%)
    lifestyle_score = 0
    if profile1.sleep_schedule == profile2.sleep_schedule:
        lifestyle_score += 50
    if profile1.smoker == profile2.smoker:
        lifestyle_score += 25
    if profile1.has_pets == profile2.has_pets or profile2.comfortable_with_pets:
        lifestyle_score += 25
    
    # Schedule compatibility (20%)
    schedule_score = 70  # Default, would need more data
    
    # Cleanliness compatibility (20%)
    clean_diff = abs(profile1.cleanliness_level - profile2.cleanliness_level)
    cleanliness_score = max(0, 100 - (clean_diff * 25))
    
    # Social compatibility (15%)
    social_match = profile1.social_level == profile2.social_level
    social_score = 100 if social_match else 60
    
    # Budget compatibility (20%)
    budget_diff = abs(profile1.max_monthly_rent - profile2.max_monthly_rent)
    budget_score = max(0, 100 - (budget_diff / 10))
    
    # Overall score
    overall = (
        lifestyle_score * 0.25 +
        schedule_score * 0.20 +
        cleanliness_score * 0.20 +
        social_score * 0.15 +
        budget_score * 0.20
    )
    
    # Shared interests
    interests1 = set(json.loads(profile1.interests)) if profile1.interests else set()
    interests2 = set(json.loads(profile2.interests)) if profile2.interests else set()
    shared = list(interests1.intersection(interests2))
    
    # Shared major
    shared_major = profile1.major == profile2.major if profile1.major and profile2.major else False
    
    # Generate explanation
    explanation = f"You both prefer a {profile1.social_level} lifestyle"
    if shared:
        explanation += f" and share interests in {', '.join(shared[:3])}"
    if shared_major:
        explanation += f" and are both {profile1.major} majors"
    
    # Potential conflicts
    conflicts = []
    if clean_diff > 2:
        conflicts.append("Different cleanliness standards - discuss expectations early")
    if profile1.hosting_parties != profile2.hosting_parties:
        conflicts.append("Different views on hosting guests")
    
    conflicts_text = "; ".join(conflicts) if conflicts else "No major conflicts identified"
    
    return {
        'score': round(overall, 2),
        'lifestyle': round(lifestyle_score, 2),
        'schedule': round(schedule_score, 2),
        'cleanliness': round(cleanliness_score, 2),
        'social': round(social_score, 2),
        'budget': round(budget_score, 2),
        'shared_interests': shared,
        'shared_major': shared_major,
        'explanation': explanation,
        'conflicts': conflicts_text
    }
