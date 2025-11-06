from flask import render_template
from . import bp

@bp.route("/")
def index():
    """Housing and residence life homepage"""
    
    # Real PSU residence halls with actual data
    residence_halls = [
        {
            'name': 'Gorilla Village',
            'type': 'Apartment-Style',
            'capacity': '400+ students',
            'cost': '$3,800/semester',
            'description': 'Modern apartment-style living with full kitchens, private bedrooms, and community spaces.',
            'features': ['Full Kitchen', 'Private Bedrooms', 'Study Lounges', 'Laundry Facilities', 'Parking'],
            'image': 'https://www.pittstate.edu/images/student-life/gorilla-village-residence-480w.jpg',
            'apply_url': 'https://www.pittstate.edu/housing/apply.html'
        },
        {
            'name': 'Crimson Commons',
            'type': 'Suite-Style',
            'capacity': '300 students',
            'cost': '$3,200/semester',
            'description': 'Suite-style residence hall with semi-private bathrooms and modern amenities.',
            'features': ['Semi-Private Bath', 'AC/Heat', 'Study Areas', 'Vending', 'WiFi'],
            'image': 'https://www.pittstate.edu/images/student-life/residence-halls-480w.jpg',
            'apply_url': 'https://www.pittstate.edu/housing/apply.html'
        },
        {
            'name': 'Dellinger Hall',
            'type': 'Traditional',
            'capacity': '200 students',
            'cost': '$2,900/semester',
            'description': 'Traditional residence hall experience with community bathrooms and shared spaces.',
            'features': ['Community Bath', 'Study Lounges', 'Laundry', 'Dining Access', 'Affordable'],
            'image': 'https://www.pittstate.edu/images/student-life/dellinger-hall-480w.jpg',
            'apply_url': 'https://www.pittstate.edu/housing/apply.html'
        },
        {
            'name': 'Nations Hall',
            'type': 'Traditional',
            'capacity': '250 students',
            'cost': '$2,900/semester',
            'description': 'Community-focused traditional hall close to campus dining and activities.',
            'features': ['Central Location', 'Study Rooms', 'Social Spaces', 'Laundry', 'Dining Hall'],
            'image': 'https://www.pittstate.edu/images/student-life/nations-hall-480w.jpg',
            'apply_url': 'https://www.pittstate.edu/housing/apply.html'
        }
    ]
    
    # Meal plan options
    meal_plans = [
        {
            'name': 'Unlimited Meal Plan',
            'cost': '$2,100/semester',
            'description': 'Unlimited access to all dining facilities',
            'meals': 'Unlimited',
            'flex_dollars': '$100'
        },
        {
            'name': '14 Meals Per Week',
            'cost': '$1,850/semester',
            'description': '14 meals per week plus flex dollars',
            'meals': '14/week',
            'flex_dollars': '$150'
        },
        {
            'name': '10 Meals Per Week',
            'cost': '$1,600/semester',
            'description': '10 meals per week plus flex dollars',
            'meals': '10/week',
            'flex_dollars': '$200'
        }
    ]
    
    return render_template(
        "housing/index.html",
        residence_halls=residence_halls,
        meal_plans=meal_plans,
        title="Housing & Residence Life | PittState-Connect"
    )


@bp.route("/apply")
def apply():
    """Housing application page"""
    return render_template(
        "housing/apply.html",
        title="Apply for Housing | PittState-Connect"
    )


@bp.route("/meal-plans")
def meal_plans():
    """Meal plans and dining options"""
    return render_template(
        "housing/meal_plans.html",
        title="Meal Plans | PittState-Connect"
    )
