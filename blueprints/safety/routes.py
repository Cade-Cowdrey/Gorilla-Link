from flask import render_template
from . import bp

@bp.route("/")
def index():
    """Campus safety and security homepage"""
    
    # Real PSU safety services
    safety_services = [
        {
            'name': 'Campus Police',
            'icon': 'fa-shield-alt',
            'description': 'Professional police department providing 24/7 security for campus.',
            'location': 'Horace Mann Building',
            'phone': '(620) 235-4624',
            'emergency': '911 or (620) 235-4624',
            'services': ['24/7 Patrol', 'Emergency Response', 'Escorts', 'Investigations', 'Crime Prevention']
        },
        {
            'name': 'Safe Ride Program',
            'icon': 'fa-car',
            'description': 'Free safe transportation for students on campus during evening hours.',
            'location': 'Campus-wide service',
            'phone': '(620) 235-4050',
            'hours': 'Sun-Thu: 8:00 PM - 2:00 AM',
            'services': ['Free Rides', 'Evening Hours', 'Campus Locations', 'Student Drivers', 'Safe Transportation']
        },
        {
            'name': 'Emergency Call Boxes',
            'icon': 'fa-phone-square',
            'description': 'Blue light emergency phones located throughout campus.',
            'location': 'Multiple campus locations',
            'phone': 'Direct line to Campus Police',
            'hours': '24/7',
            'services': ['Immediate Connection', 'GPS Location', 'Visible Blue Lights', 'Campus-wide', 'Emergency Use']
        },
        {
            'name': 'Safety Escorts',
            'icon': 'fa-walking',
            'description': 'Walking escorts provided by campus police for your safety.',
            'location': 'Available campus-wide',
            'phone': '(620) 235-4624',
            'hours': '24/7',
            'services': ['Walking Escorts', 'Safe Arrival', 'Trained Officers', 'Any Time', 'Free Service']
        }
    ]
    
    # Emergency contacts
    emergency_contacts = [
        {'name': 'Campus Police Emergency', 'number': '(620) 235-4624', 'available': '24/7'},
        {'name': 'Pittsburg Fire Department', 'number': '911', 'available': '24/7'},
        {'name': 'Via Christi Hospital', 'number': '(620) 231-6100', 'available': '24/7'},
        {'name': 'Poison Control', 'number': '1-800-222-1222', 'available': '24/7'},
        {'name': 'Counseling Center Crisis', 'number': '(620) 235-4309', 'available': 'M-F 8-5'},
        {'name': 'National Suicide Prevention', 'number': '988', 'available': '24/7'}
    ]
    
    # Safety tips
    safety_tips = [
        {
            'title': 'Stay Aware',
            'icon': 'fa-eye',
            'description': 'Always be aware of your surroundings. Avoid distractions like headphones in isolated areas.'
        },
        {
            'title': 'Travel in Groups',
            'icon': 'fa-users',
            'description': 'Walk with friends at night. Use the buddy system, especially in unfamiliar areas.'
        },
        {
            'title': 'Lock Up',
            'icon': 'fa-lock',
            'description': 'Always lock doors and windows in your residence hall. Never prop open exterior doors.'
        },
        {
            'title': 'Report Suspicious Activity',
            'icon': 'fa-exclamation-triangle',
            'description': 'If you see something, say something. Contact Campus Police immediately.'
        },
        {
            'title': 'Use Emergency Services',
            'icon': 'fa-ambulance',
            'description': 'Don\'t hesitate to use Safe Ride, escorts, or call boxes. They exist for your safety.'
        },
        {
            'title': 'Stay Informed',
            'icon': 'fa-bell',
            'description': 'Sign up for emergency alerts. Follow campus safety on social media for updates.'
        }
    ]
    
    # Crime statistics (mock data for demo)
    crime_stats = {
        'title': 'Campus Safety Statistics',
        'year': '2024',
        'stats': [
            {'category': 'Overall Crime Rate', 'value': 'Below National Average', 'trend': 'down'},
            {'category': 'Emergency Response Time', 'value': 'Under 3 minutes', 'trend': 'stable'},
            {'category': 'Blue Light Call Boxes', 'value': '25 locations', 'trend': 'up'},
            {'category': 'Student Safety Satisfaction', 'value': '92%', 'trend': 'up'}
        ]
    }
    
    return render_template(
        "safety/index.html",
        safety_services=safety_services,
        emergency_contacts=emergency_contacts,
        safety_tips=safety_tips,
        crime_stats=crime_stats,
        title="Campus Safety & Security | PittState-Connect"
    )


@bp.route("/emergency")
def emergency():
    """Emergency procedures and contacts"""
    return render_template(
        "safety/emergency.html",
        title="Emergency Procedures | PittState-Connect"
    )


@bp.route("/crime-stats")
def crime_stats():
    """Campus crime statistics (Clery Act)"""
    return render_template(
        "safety/crime_stats.html",
        title="Crime Statistics | PittState-Connect"
    )
