from flask import render_template
from . import bp

@bp.route("/")
def index():
    """Health and wellness services homepage"""
    
    # Real PSU health services
    services = [
        {
            'name': 'Student Health Center',
            'icon': 'fa-hospital',
            'description': 'Primary medical care, sick visits, immunizations, and health screenings.',
            'location': 'Horace Mann Building, Room 106',
            'phone': '(620) 235-4251',
            'hours': 'Monday-Friday: 8:00 AM - 4:30 PM',
            'services': ['Sick Visits', 'Immunizations', 'Physical Exams', 'Lab Tests', 'Prescriptions']
        },
        {
            'name': 'Counseling Center',
            'icon': 'fa-brain',
            'description': 'Free confidential counseling and mental health support for all students.',
            'location': 'Whitesitt Hall, Room 102',
            'phone': '(620) 235-4309',
            'hours': 'Monday-Friday: 8:00 AM - 5:00 PM',
            'services': ['Individual Counseling', 'Group Therapy', 'Crisis Support', 'Workshops', 'Referrals']
        },
        {
            'name': 'Wellness Programs',
            'icon': 'fa-heartbeat',
            'description': 'Programs promoting physical fitness, nutrition, and overall wellbeing.',
            'location': 'Robert W. Plaster Center',
            'phone': '(620) 235-4661',
            'hours': 'Various times',
            'services': ['Fitness Classes', 'Nutrition Counseling', 'Stress Management', 'Health Education', 'Peer Support']
        },
        {
            'name': 'Student Disability Services',
            'icon': 'fa-universal-access',
            'description': 'Academic accommodations and support for students with disabilities.',
            'location': 'Whitesitt Hall, Room 110',
            'phone': '(620) 235-4169',
            'hours': 'Monday-Friday: 8:00 AM - 5:00 PM',
            'services': ['Testing Accommodations', 'Note-Taking', 'Assistive Technology', 'Advocacy', 'Resources']
        }
    ]
    
    # Crisis resources
    crisis_resources = [
        {
            'name': 'Campus Police Emergency',
            'phone': '(620) 235-4624',
            'available': '24/7',
            'description': 'For immediate emergencies on campus'
        },
        {
            'name': 'National Suicide Prevention Lifeline',
            'phone': '988',
            'available': '24/7',
            'description': 'Free and confidential crisis support'
        },
        {
            'name': 'Crisis Text Line',
            'phone': 'Text HOME to 741741',
            'available': '24/7',
            'description': 'Text-based crisis support'
        },
        {
            'name': 'Via Christi Hospital',
            'phone': '(620) 231-6100',
            'available': '24/7 Emergency Room',
            'description': 'Local emergency medical care'
        }
    ]
    
    # Health tips
    wellness_tips = [
        {
            'title': 'Get Enough Sleep',
            'icon': 'fa-bed',
            'description': 'Aim for 7-9 hours per night. Quality sleep improves focus and mood.'
        },
        {
            'title': 'Stay Active',
            'icon': 'fa-running',
            'description': 'Exercise 30 minutes daily. Use the free student rec center!'
        },
        {
            'title': 'Eat Well',
            'icon': 'fa-apple-alt',
            'description': 'Balanced meals fuel your body and brain. Visit dining halls for healthy options.'
        },
        {
            'title': 'Manage Stress',
            'icon': 'fa-spa',
            'description': 'Take breaks, practice mindfulness, and don\'t hesitate to ask for help.'
        }
    ]
    
    return render_template(
        "health/index.html",
        services=services,
        crisis_resources=crisis_resources,
        wellness_tips=wellness_tips,
        title="Health & Wellness | PittState-Connect"
    )


@bp.route("/counseling")
def counseling():
    """Counseling center information"""
    return render_template(
        "health/counseling.html",
        title="Counseling Services | PittState-Connect"
    )


@bp.route("/emergency")
def emergency():
    """Emergency and crisis resources"""
    return render_template(
        "health/emergency.html",
        title="Emergency Resources | PittState-Connect"
    )
