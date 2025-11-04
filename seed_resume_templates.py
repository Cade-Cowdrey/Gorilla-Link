"""
Seed Resume Templates - Professional resume designs
Run this after database migration to populate templates
"""

from extensions import db
from models import ResumeTemplate


def seed_resume_templates():
    """Create initial resume templates"""
    
    templates = [
        # MODERN TEMPLATES
        {
            'name': 'Modern Professional',
            'description': 'Clean, contemporary design with bold headers. Perfect for tech, creative, and modern industries.',
            'preview_image': '/static/img/templates/modern_professional.png',
            'category': 'modern',
            'color_scheme': '#2C3E50',
            'font_family': 'Open Sans',
            'is_active': True,
            'is_premium': False
        },
        {
            'name': 'Minimalist',
            'description': 'Simple and elegant. Lets your content shine. Great for any industry.',
            'preview_image': '/static/img/templates/minimalist.png',
            'category': 'modern',
            'color_scheme': '#34495E',
            'font_family': 'Roboto',
            'is_active': True,
            'is_premium': False
        },
        {
            'name': 'Tech Forward',
            'description': 'Modern design for software engineers and tech professionals. ATS-friendly.',
            'preview_image': '/static/img/templates/tech_forward.png',
            'category': 'technical',
            'color_scheme': '#3498DB',
            'font_family': 'Source Code Pro',
            'is_active': True,
            'is_premium': False
        },
        
        # CLASSIC TEMPLATES
        {
            'name': 'Traditional',
            'description': 'Timeless professional format. Ideal for conservative industries like finance, law, government.',
            'preview_image': '/static/img/templates/traditional.png',
            'category': 'classic',
            'color_scheme': '#000000',
            'font_family': 'Times New Roman',
            'is_active': True,
            'is_premium': False
        },
        {
            'name': 'Executive',
            'description': 'Sophisticated design for senior-level positions and executive roles.',
            'preview_image': '/static/img/templates/executive.png',
            'category': 'classic',
            'color_scheme': '#1A1A1A',
            'font_family': 'Georgia',
            'is_active': True,
            'is_premium': False
        },
        
        # CREATIVE TEMPLATES
        {
            'name': 'Creative Pro',
            'description': 'Stand out with this creative design. Perfect for designers, marketers, and creative roles.',
            'preview_image': '/static/img/templates/creative_pro.png',
            'category': 'creative',
            'color_scheme': '#E74C3C',
            'font_family': 'Montserrat',
            'is_active': True,
            'is_premium': True
        },
        {
            'name': 'Designer Portfolio',
            'description': 'Visual-focused resume for graphic designers and creative professionals.',
            'preview_image': '/static/img/templates/designer.png',
            'category': 'creative',
            'color_scheme': '#9B59B6',
            'font_family': 'Raleway',
            'is_active': True,
            'is_premium': True
        },
        
        # ACADEMIC TEMPLATES
        {
            'name': 'Academic CV',
            'description': 'Comprehensive format for academic positions, research, and teaching roles.',
            'preview_image': '/static/img/templates/academic.png',
            'category': 'academic',
            'color_scheme': '#16A085',
            'font_family': 'Palatino',
            'is_active': True,
            'is_premium': False
        },
        {
            'name': 'Research Focused',
            'description': 'Highlight publications, grants, and research experience.',
            'preview_image': '/static/img/templates/research.png',
            'category': 'academic',
            'color_scheme': '#27AE60',
            'font_family': 'Garamond',
            'is_active': True,
            'is_premium': False
        },
        
        # SPECIALIZED TEMPLATES
        {
            'name': 'Entry Level',
            'description': 'Optimized for students and recent graduates with limited experience.',
            'preview_image': '/static/img/templates/entry_level.png',
            'category': 'modern',
            'color_scheme': '#3498DB',
            'font_family': 'Lato',
            'is_active': True,
            'is_premium': False
        },
        {
            'name': 'Career Changer',
            'description': 'Emphasize transferable skills for those switching careers.',
            'preview_image': '/static/img/templates/career_change.png',
            'category': 'modern',
            'color_scheme': '#E67E22',
            'font_family': 'Arial',
            'is_active': True,
            'is_premium': False
        },
        {
            'name': 'Two Column',
            'description': 'Efficient use of space with two-column layout. Modern and professional.',
            'preview_image': '/static/img/templates/two_column.png',
            'category': 'modern',
            'color_scheme': '#2C3E50',
            'font_family': 'Helvetica',
            'is_active': True,
            'is_premium': True
        },
        {
            'name': 'ATS Optimized',
            'description': 'Maximum ATS compatibility. Simple format that all systems can parse perfectly.',
            'preview_image': '/static/img/templates/ats_optimized.png',
            'category': 'classic',
            'color_scheme': '#333333',
            'font_family': 'Calibri',
            'is_active': True,
            'is_premium': False
        },
        {
            'name': 'Infographic',
            'description': 'Visual resume with charts and graphics. Best for creative and marketing roles.',
            'preview_image': '/static/img/templates/infographic.png',
            'category': 'creative',
            'color_scheme': '#1ABC9C',
            'font_family': 'Poppins',
            'is_active': True,
            'is_premium': True
        },
        {
            'name': 'International',
            'description': 'Versatile format suitable for international job applications.',
            'preview_image': '/static/img/templates/international.png',
            'category': 'classic',
            'color_scheme': '#2C3E50',
            'font_family': 'Arial',
            'is_active': True,
            'is_premium': False
        }
    ]
    
    print("Seeding resume templates...")
    
    for template_data in templates:
        # Check if template already exists
        existing = ResumeTemplate.query.filter_by(name=template_data['name']).first()
        
        if not existing:
            template = ResumeTemplate(**template_data)
            db.session.add(template)
            print(f"✓ Added template: {template_data['name']}")
        else:
            print(f"- Template already exists: {template_data['name']}")
    
    db.session.commit()
    print(f"\n✅ Successfully seeded {len(templates)} resume templates!")
    
    # Print summary
    free_count = sum(1 for t in templates if not t['is_premium'])
    premium_count = sum(1 for t in templates if t['is_premium'])
    
    print(f"\nSummary:")
    print(f"  Free templates: {free_count}")
    print(f"  Premium templates: {premium_count}")
    print(f"  Categories:")
    print(f"    - Modern: {sum(1 for t in templates if t['category'] == 'modern')}")
    print(f"    - Classic: {sum(1 for t in templates if t['category'] == 'classic')}")
    print(f"    - Creative: {sum(1 for t in templates if t['category'] == 'creative')}")
    print(f"    - Academic: {sum(1 for t in templates if t['category'] == 'academic')}")
    print(f"    - Technical: {sum(1 for t in templates if t['category'] == 'technical')}")


if __name__ == '__main__':
    from app_pro import app  # Import your Flask app
    
    with app.app_context():
        seed_resume_templates()
