# blueprints/departments/routes.py
from flask import Blueprint, render_template, request
from utils.security_util import login_required_safe
from utils.analytics_util import record_page_view
from models import User, Department
from models_extended import AlumniProfile

bp = Blueprint("departments_bp", __name__, url_prefix="/departments")

@bp.route("/")
@login_required_safe
def department_index():
    """Display a list of departments."""
    record_page_view("departments_index")
    return render_template("departments/index.html", title="Departments | PittState-Connect")

@bp.route("/showcase")
@bp.route("/showcase/<string:dept_code>")
@login_required_safe
def showcase(dept_code=None):
    """Display curated department showcase with projects, alumni, and faculty."""
    record_page_view("departments_showcase")
    
    # Sample department data (in production, would query Department model)
    departments = {
        'business': {
            'name': 'Kelce College of Business',
            'code': 'business',
            'tagline': 'Building Tomorrow\'s Business Leaders',
            'description': 'AACSB-accredited programs in accounting, finance, management, and marketing. Known for real-world projects and strong employer partnerships.',
            'stats': {
                'students': 850,
                'faculty': 42,
                'placement_rate': 94,
                'avg_salary': 58000
            },
            'colors': {'primary': '#003366', 'accent': '#FFC72C'},
            'projects': [
                {
                    'title': 'PSU Business Plan Competition 2024',
                    'student': 'Sarah Martinez',
                    'description': 'Developed a sustainable fashion startup that won $10K in seed funding.',
                    'image': '/static/img/project-business-1.jpg',
                    'tags': ['Entrepreneurship', 'Sustainability', 'Innovation']
                },
                {
                    'title': 'Regional Marketing Analytics Dashboard',
                    'student': 'James Chen',
                    'description': 'Built real-time analytics for local businesses using Tableau and Python.',
                    'image': '/static/img/project-business-2.jpg',
                    'tags': ['Marketing', 'Data Analytics', 'Python']
                },
                {
                    'title': 'Financial Literacy App for Students',
                    'student': 'Emily Rodriguez',
                    'description': 'Mobile app teaching budgeting and investing, used by 500+ PSU students.',
                    'image': '/static/img/project-business-3.jpg',
                    'tags': ['Finance', 'Mobile Dev', 'FinTech']
                }
            ],
            'alumni_quotes': [
                {
                    'name': 'Michael Thompson',
                    'class_year': 2019,
                    'role': 'Senior Financial Analyst at Cerner',
                    'quote': 'The hands-on experience at Kelce prepared me to hit the ground running. My professors became mentors for life.',
                    'image': '/static/img/alumni-business-1.jpg'
                },
                {
                    'name': 'Jessica Park',
                    'class_year': 2021,
                    'role': 'Marketing Manager at Sprint',
                    'quote': 'PSU\'s business program gave me real client experience before graduation. That made all the difference.',
                    'image': '/static/img/alumni-business-2.jpg'
                }
            ],
            'faculty_highlights': [
                {
                    'name': 'Dr. Robert Johnson',
                    'title': 'Dean, Kelce College',
                    'expertise': 'Supply Chain Management, Operations',
                    'bio': '25+ years industry experience. Published author. Former VP of Operations at Fortune 500.',
                    'image': '/static/img/faculty-business-1.jpg'
                },
                {
                    'name': 'Prof. Linda Chen',
                    'title': 'Director of Marketing Programs',
                    'expertise': 'Digital Marketing, Brand Strategy',
                    'bio': 'Award-winning marketing professional. Leads student consulting teams with local businesses.',
                    'image': '/static/img/faculty-business-2.jpg'
                }
            ],
            'career_paths': [
                {'title': 'Financial Analyst', 'avg_salary': '$62,000', 'growth': '+8%'},
                {'title': 'Marketing Manager', 'avg_salary': '$68,000', 'growth': '+10%'},
                {'title': 'Business Consultant', 'avg_salary': '$72,000', 'growth': '+14%'},
                {'title': 'Operations Manager', 'avg_salary': '$65,000', 'growth': '+6%'}
            ]
        },
        'technology': {
            'name': 'College of Technology',
            'code': 'technology',
            'tagline': 'Innovating the Future of Tech',
            'description': 'Cutting-edge programs in computer science, cybersecurity, and engineering technology. State-of-the-art labs and industry certifications.',
            'stats': {
                'students': 620,
                'faculty': 38,
                'placement_rate': 97,
                'avg_salary': 72000
            },
            'colors': {'primary': '#BA0C2F', 'accent': '#FFC72C'},
            'projects': [
                {
                    'title': 'AI-Powered Campus Navigation App',
                    'student': 'David Kim',
                    'description': 'Mobile app using ML to help students navigate campus buildings with AR overlays.',
                    'image': '/static/img/project-tech-1.jpg',
                    'tags': ['AI', 'Mobile', 'AR']
                },
                {
                    'title': 'Cybersecurity Threat Detection System',
                    'student': 'Amanda Foster',
                    'description': 'Real-time network monitoring tool detecting anomalies using machine learning.',
                    'image': '/static/img/project-tech-2.jpg',
                    'tags': ['Cybersecurity', 'ML', 'Networking']
                }
            ],
            'alumni_quotes': [
                {
                    'name': 'Kevin Zhang',
                    'class_year': 2020,
                    'role': 'Software Engineer at Google',
                    'quote': 'PSU gave me the technical skills and work ethic to succeed at a top tech company.',
                    'image': '/static/img/alumni-tech-1.jpg'
                }
            ],
            'faculty_highlights': [
                {
                    'name': 'Dr. Sarah Mitchell',
                    'title': 'Chair, Computer Science',
                    'expertise': 'AI, Machine Learning, Data Science',
                    'bio': 'PhD from MIT. Research in neural networks. Active in women-in-tech advocacy.',
                    'image': '/static/img/faculty-tech-1.jpg'
                }
            ],
            'career_paths': [
                {'title': 'Software Engineer', 'avg_salary': '$75,000', 'growth': '+22%'},
                {'title': 'Cybersecurity Analyst', 'avg_salary': '$78,000', 'growth': '+31%'},
                {'title': 'Data Scientist', 'avg_salary': '$85,000', 'growth': '+36%'}
            ]
        },
        'education': {
            'name': 'College of Education',
            'code': 'education',
            'tagline': 'Shaping Future Educators',
            'description': 'Nationally recognized teacher preparation programs. Strong emphasis on field experience and educational technology.',
            'stats': {
                'students': 480,
                'faculty': 32,
                'placement_rate': 92,
                'avg_salary': 45000
            },
            'colors': {'primary': '#003B71', 'accent': '#FFC72C'},
            'projects': [
                {
                    'title': 'Interactive STEM Curriculum for K-5',
                    'student': 'Maria Gonzalez',
                    'description': 'Hands-on science lessons adopted by 5 local elementary schools.',
                    'image': '/static/img/project-edu-1.jpg',
                    'tags': ['Curriculum', 'STEM', 'Elementary Ed']
                }
            ],
            'alumni_quotes': [
                {
                    'name': 'Brian Walker',
                    'class_year': 2018,
                    'role': 'Principal, Lincoln Elementary',
                    'quote': 'PSU prepared me not just to teach, but to lead. I\'m now shaping an entire school community.',
                    'image': '/static/img/alumni-edu-1.jpg'
                }
            ],
            'faculty_highlights': [
                {
                    'name': 'Dr. Patricia Moore',
                    'title': 'Dean, College of Education',
                    'expertise': 'Literacy, Early Childhood Education',
                    'bio': '30 years in education. Former superintendent. National speaker on reading instruction.',
                    'image': '/static/img/faculty-edu-1.jpg'
                }
            ],
            'career_paths': [
                {'title': 'Elementary Teacher', 'avg_salary': '$44,000', 'growth': '+4%'},
                {'title': 'Secondary Teacher', 'avg_salary': '$46,000', 'growth': '+4%'},
                {'title': 'School Administrator', 'avg_salary': '$68,000', 'growth': '+8%'}
            ]
        }
    }
    
    # Get requested department or show all
    if dept_code and dept_code in departments:
        dept_data = departments[dept_code]
        return render_template(
            "departments/showcase_detail.html",
            department=dept_data,
            title=f"{dept_data['name']} Showcase | PittState-Connect"
        )
    else:
        return render_template(
            "departments/showcase.html",
            departments=departments,
            title="Department Showcases | PittState-Connect"
        )

