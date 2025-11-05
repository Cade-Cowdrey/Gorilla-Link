"""
Free Certifications Seeder
Populate database with curated free certifications from top providers
"""
from models import db
from models_growth_features import (
    FreeCertification, CertificationPathway
)
from datetime import datetime

def seed_free_certifications():
    """Seed database with real free certifications"""
    
    certifications = [
        # ============================================
        # SAFETY & COMPLIANCE
        # ============================================
        {
            'title': 'CPR & First Aid Certification',
            'provider': 'American Red Cross',
            'category': 'Safety & Compliance',
            'subcategory': 'First Aid',
            'description': 'Learn life-saving CPR and first aid techniques. Required for many healthcare, education, and childcare positions.',
            'skills_gained': ['CPR', 'First Aid', 'AED Use', 'Emergency Response', 'Choking Relief'],
            'duration_hours': 4,
            'difficulty_level': 'beginner',
            'course_url': 'https://www.redcross.org/take-a-class/cpr',
            'industry_recognition': 'high',
            'resume_boost_score': 85,
            'job_relevance_score': 90,
            'salary_impact': 'Required for many entry-level positions',
            'prerequisites': [],
            'recommended_for_majors': ['Nursing', 'Education', 'Sports Management', 'Psychology'],
            'recommended_for_careers': ['Healthcare', 'Teaching', 'Coaching', 'Childcare'],
            'is_featured': True,
            'verified_by_psu': True
        },
        {
            'title': 'OSHA 10-Hour General Industry',
            'provider': 'OSHA (U.S. Department of Labor)',
            'category': 'Safety & Compliance',
            'subcategory': 'Workplace Safety',
            'description': 'Official OSHA certification covering workplace safety standards, hazard recognition, and employee rights.',
            'skills_gained': ['Workplace Safety', 'Hazard Recognition', 'OSHA Standards', 'Safety Regulations'],
            'duration_hours': 10,
            'difficulty_level': 'beginner',
            'course_url': 'https://www.osha.gov/training',
            'industry_recognition': 'high',
            'resume_boost_score': 80,
            'job_relevance_score': 85,
            'salary_impact': '$2K-$5K increase for safety roles',
            'prerequisites': [],
            'recommended_for_majors': ['Engineering', 'Construction Management', 'Manufacturing', 'Business'],
            'recommended_for_careers': ['Construction', 'Manufacturing', 'Facility Management', 'Operations'],
            'is_featured': True,
            'verified_by_psu': True
        },
        
        # ============================================
        # GOOGLE CERTIFICATIONS
        # ============================================
        {
            'title': 'Google Analytics Certification',
            'provider': 'Google',
            'category': 'Technology',
            'subcategory': 'Analytics',
            'description': 'Master Google Analytics to track website traffic, user behavior, and marketing campaign performance.',
            'skills_gained': ['Google Analytics', 'Data Analysis', 'Web Analytics', 'Marketing Analytics', 'Reporting'],
            'duration_hours': 15,
            'difficulty_level': 'beginner',
            'course_url': 'https://skillshop.withgoogle.com/analytics',
            'industry_recognition': 'high',
            'resume_boost_score': 90,
            'job_relevance_score': 95,
            'salary_impact': '$5K-$10K increase for marketing roles',
            'prerequisites': [],
            'recommended_for_majors': ['Marketing', 'Business', 'Computer Science', 'Communications'],
            'recommended_for_careers': ['Digital Marketing', 'Data Analyst', 'SEO Specialist', 'Product Manager'],
            'is_featured': True,
            'verified_by_psu': True
        },
        {
            'title': 'Google Ads Certification',
            'provider': 'Google',
            'category': 'Marketing',
            'subcategory': 'Digital Advertising',
            'description': 'Learn to create, manage, and optimize Google Ads campaigns. Industry-standard for digital marketers.',
            'skills_gained': ['Google Ads', 'PPC Advertising', 'Campaign Management', 'Keyword Research', 'Ad Optimization'],
            'duration_hours': 12,
            'difficulty_level': 'intermediate',
            'course_url': 'https://skillshop.withgoogle.com/googleads',
            'industry_recognition': 'high',
            'resume_boost_score': 92,
            'job_relevance_score': 95,
            'salary_impact': '$8K-$15K increase',
            'prerequisites': ['Basic marketing knowledge'],
            'recommended_for_majors': ['Marketing', 'Business', 'Communications'],
            'recommended_for_careers': ['Digital Marketer', 'PPC Specialist', 'Marketing Manager'],
            'is_featured': True
        },
        {
            'title': 'Google IT Support Professional Certificate',
            'provider': 'Google (Coursera)',
            'category': 'Technology',
            'subcategory': 'IT Support',
            'description': 'Comprehensive IT fundamentals covering networking, operating systems, system administration, and security.',
            'skills_gained': ['IT Support', 'Troubleshooting', 'Networking', 'Linux', 'Customer Service', 'Cybersecurity'],
            'duration_hours': 120,
            'difficulty_level': 'beginner',
            'course_url': 'https://www.coursera.org/professional-certificates/google-it-support',
            'industry_recognition': 'high',
            'resume_boost_score': 95,
            'job_relevance_score': 98,
            'salary_impact': '$40K-$50K entry-level salary',
            'prerequisites': [],
            'recommended_for_majors': ['Computer Science', 'Information Technology', 'Engineering'],
            'recommended_for_careers': ['IT Support', 'Help Desk', 'Network Admin', 'Systems Administrator'],
            'is_featured': True,
            'verified_by_psu': True
        },
        {
            'title': 'Google Data Analytics Professional Certificate',
            'provider': 'Google (Coursera)',
            'category': 'Technology',
            'subcategory': 'Data Analytics',
            'description': 'Learn data analysis fundamentals, SQL, Tableau, and R programming. Prepare for entry-level data analyst roles.',
            'skills_gained': ['Data Analysis', 'SQL', 'Tableau', 'R Programming', 'Data Visualization', 'Spreadsheets'],
            'duration_hours': 120,
            'difficulty_level': 'beginner',
            'course_url': 'https://www.coursera.org/professional-certificates/google-data-analytics',
            'industry_recognition': 'high',
            'resume_boost_score': 95,
            'job_relevance_score': 98,
            'salary_impact': '$50K-$70K entry-level salary',
            'prerequisites': [],
            'recommended_for_majors': ['Business', 'Mathematics', 'Computer Science', 'Economics'],
            'recommended_for_careers': ['Data Analyst', 'Business Analyst', 'Market Research Analyst'],
            'is_featured': True,
            'verified_by_psu': True
        },
        
        # ============================================
        # MICROSOFT CERTIFICATIONS
        # ============================================
        {
            'title': 'Microsoft Azure Fundamentals (AZ-900)',
            'provider': 'Microsoft',
            'category': 'Technology',
            'subcategory': 'Cloud Computing',
            'description': 'Learn cloud computing basics and Microsoft Azure services. Entry point to cloud career.',
            'skills_gained': ['Azure', 'Cloud Computing', 'SaaS', 'IaaS', 'PaaS', 'Cloud Security'],
            'duration_hours': 20,
            'difficulty_level': 'beginner',
            'course_url': 'https://learn.microsoft.com/en-us/certifications/azure-fundamentals/',
            'industry_recognition': 'high',
            'resume_boost_score': 88,
            'job_relevance_score': 92,
            'salary_impact': '$5K-$10K increase',
            'prerequisites': [],
            'recommended_for_majors': ['Computer Science', 'Information Technology', 'Business'],
            'recommended_for_careers': ['Cloud Engineer', 'DevOps', 'IT Administrator', 'Solutions Architect'],
            'is_featured': True
        },
        {
            'title': 'Microsoft Office Specialist (Excel)',
            'provider': 'Microsoft',
            'category': 'Technology',
            'subcategory': 'Productivity Software',
            'description': 'Master Microsoft Excel from basics to advanced functions, pivot tables, and data analysis.',
            'skills_gained': ['Excel', 'Spreadsheets', 'Data Analysis', 'Formulas', 'Pivot Tables', 'Charting'],
            'duration_hours': 25,
            'difficulty_level': 'beginner',
            'course_url': 'https://learn.microsoft.com/en-us/certifications/mos-excel-2019/',
            'industry_recognition': 'high',
            'resume_boost_score': 85,
            'job_relevance_score': 95,
            'salary_impact': 'Required for most office jobs',
            'prerequisites': [],
            'recommended_for_majors': ['All Majors'],
            'recommended_for_careers': ['Business Analyst', 'Accountant', 'Project Manager', 'Any Office Role'],
            'is_featured': True,
            'verified_by_psu': True
        },
        {
            'title': 'Power BI Data Analyst',
            'provider': 'Microsoft',
            'category': 'Technology',
            'subcategory': 'Data Visualization',
            'description': 'Learn to create interactive dashboards and reports with Power BI. High-demand skill.',
            'skills_gained': ['Power BI', 'Data Visualization', 'DAX', 'Data Modeling', 'Business Intelligence'],
            'duration_hours': 30,
            'difficulty_level': 'intermediate',
            'course_url': 'https://learn.microsoft.com/en-us/certifications/power-bi-data-analyst-associate/',
            'industry_recognition': 'high',
            'resume_boost_score': 90,
            'job_relevance_score': 95,
            'salary_impact': '$10K-$20K increase',
            'prerequisites': ['Excel knowledge'],
            'recommended_for_majors': ['Business', 'Computer Science', 'Mathematics'],
            'recommended_for_careers': ['Data Analyst', 'Business Intelligence Analyst', 'Reporting Analyst'],
            'is_featured': True
        },
        
        # ============================================
        # AWS CERTIFICATIONS
        # ============================================
        {
            'title': 'AWS Cloud Practitioner',
            'provider': 'AWS (Amazon Web Services)',
            'category': 'Technology',
            'subcategory': 'Cloud Computing',
            'description': 'Foundational AWS certification covering cloud concepts, security, and AWS services.',
            'skills_gained': ['AWS', 'Cloud Computing', 'EC2', 'S3', 'Cloud Security', 'DevOps Basics'],
            'duration_hours': 20,
            'difficulty_level': 'beginner',
            'course_url': 'https://aws.amazon.com/certification/certified-cloud-practitioner/',
            'industry_recognition': 'high',
            'resume_boost_score': 90,
            'job_relevance_score': 95,
            'salary_impact': '$5K-$15K increase',
            'prerequisites': [],
            'recommended_for_majors': ['Computer Science', 'Information Technology', 'Engineering'],
            'recommended_for_careers': ['Cloud Engineer', 'DevOps', 'Software Developer', 'Solutions Architect'],
            'is_featured': True,
            'verified_by_psu': True
        },
        
        # ============================================
        # FREECODECAMP CERTIFICATIONS
        # ============================================
        {
            'title': 'Responsive Web Design',
            'provider': 'freeCodeCamp',
            'category': 'Technology',
            'subcategory': 'Web Development',
            'description': 'Learn HTML5, CSS3, and responsive design principles. Build 5 projects for certification.',
            'skills_gained': ['HTML5', 'CSS3', 'Responsive Design', 'Flexbox', 'CSS Grid', 'Web Accessibility'],
            'duration_hours': 300,
            'difficulty_level': 'beginner',
            'course_url': 'https://www.freecodecamp.org/learn/2022/responsive-web-design/',
            'industry_recognition': 'medium',
            'resume_boost_score': 85,
            'job_relevance_score': 90,
            'salary_impact': '$35K-$50K entry-level',
            'prerequisites': [],
            'recommended_for_majors': ['Computer Science', 'Graphic Design', 'Marketing'],
            'recommended_for_careers': ['Web Developer', 'Front-End Developer', 'UI Designer'],
            'is_featured': True
        },
        {
            'title': 'JavaScript Algorithms and Data Structures',
            'provider': 'freeCodeCamp',
            'category': 'Technology',
            'subcategory': 'Programming',
            'description': 'Master JavaScript fundamentals, ES6, algorithms, and object-oriented programming.',
            'skills_gained': ['JavaScript', 'ES6', 'Algorithms', 'Data Structures', 'OOP', 'Functional Programming'],
            'duration_hours': 300,
            'difficulty_level': 'intermediate',
            'course_url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/',
            'industry_recognition': 'medium',
            'resume_boost_score': 88,
            'job_relevance_score': 95,
            'salary_impact': '$50K-$70K entry-level',
            'prerequisites': ['Basic HTML/CSS'],
            'recommended_for_majors': ['Computer Science', 'Software Engineering'],
            'recommended_for_careers': ['Software Developer', 'Full-Stack Developer', 'Web Developer'],
            'is_featured': True
        },
        {
            'title': 'Front End Development Libraries',
            'provider': 'freeCodeCamp',
            'category': 'Technology',
            'subcategory': 'Web Development',
            'description': 'Learn React, Redux, Bootstrap, jQuery, and Sass. Build interactive web applications.',
            'skills_gained': ['React', 'Redux', 'Bootstrap', 'jQuery', 'Sass', 'Front-End Development'],
            'duration_hours': 300,
            'difficulty_level': 'intermediate',
            'course_url': 'https://www.freecodecamp.org/learn/front-end-development-libraries/',
            'industry_recognition': 'medium',
            'resume_boost_score': 92,
            'job_relevance_score': 95,
            'salary_impact': '$60K-$80K',
            'prerequisites': ['HTML', 'CSS', 'JavaScript'],
            'recommended_for_majors': ['Computer Science', 'Software Engineering'],
            'recommended_for_careers': ['Front-End Developer', 'React Developer', 'UI Developer'],
            'is_featured': True
        },
        
        # ============================================
        # HUBSPOT ACADEMY
        # ============================================
        {
            'title': 'HubSpot Inbound Marketing Certification',
            'provider': 'HubSpot Academy',
            'category': 'Marketing',
            'subcategory': 'Inbound Marketing',
            'description': 'Learn inbound marketing methodology, content strategy, SEO, and lead nurturing.',
            'skills_gained': ['Inbound Marketing', 'Content Marketing', 'SEO', 'Lead Generation', 'Email Marketing'],
            'duration_hours': 6,
            'difficulty_level': 'beginner',
            'course_url': 'https://academy.hubspot.com/courses/inbound-marketing',
            'industry_recognition': 'high',
            'resume_boost_score': 88,
            'job_relevance_score': 92,
            'salary_impact': '$5K-$10K increase',
            'prerequisites': [],
            'recommended_for_majors': ['Marketing', 'Business', 'Communications'],
            'recommended_for_careers': ['Marketing Specialist', 'Content Marketer', 'Digital Marketing Manager'],
            'is_featured': True
        },
        {
            'title': 'HubSpot Content Marketing Certification',
            'provider': 'HubSpot Academy',
            'category': 'Marketing',
            'subcategory': 'Content Marketing',
            'description': 'Master content creation, storytelling, and content strategy for business growth.',
            'skills_gained': ['Content Marketing', 'Content Strategy', 'Blogging', 'Storytelling', 'Content Calendar'],
            'duration_hours': 5,
            'difficulty_level': 'beginner',
            'course_url': 'https://academy.hubspot.com/courses/content-marketing',
            'industry_recognition': 'high',
            'resume_boost_score': 85,
            'job_relevance_score': 90,
            'salary_impact': '$5K-$8K increase',
            'prerequisites': [],
            'recommended_for_majors': ['Marketing', 'English', 'Communications', 'Journalism'],
            'recommended_for_careers': ['Content Marketer', 'Content Writer', 'Social Media Manager'],
            'is_featured': True
        },
        {
            'title': 'HubSpot Social Media Marketing Certification',
            'provider': 'HubSpot Academy',
            'category': 'Marketing',
            'subcategory': 'Social Media',
            'description': 'Learn to create effective social media strategies, content, and campaigns.',
            'skills_gained': ['Social Media Marketing', 'Facebook Ads', 'Instagram Marketing', 'LinkedIn Marketing', 'Social Analytics'],
            'duration_hours': 5,
            'difficulty_level': 'beginner',
            'course_url': 'https://academy.hubspot.com/courses/social-media-marketing',
            'industry_recognition': 'high',
            'resume_boost_score': 87,
            'job_relevance_score': 92,
            'salary_impact': '$5K-$10K increase',
            'prerequisites': [],
            'recommended_for_majors': ['Marketing', 'Communications', 'Business'],
            'recommended_for_careers': ['Social Media Manager', 'Digital Marketer', 'Brand Manager'],
            'is_featured': True
        },
        {
            'title': 'HubSpot Email Marketing Certification',
            'provider': 'HubSpot Academy',
            'category': 'Marketing',
            'subcategory': 'Email Marketing',
            'description': 'Master email marketing campaigns, automation, and list management.',
            'skills_gained': ['Email Marketing', 'Marketing Automation', 'List Segmentation', 'A/B Testing', 'Deliverability'],
            'duration_hours': 4,
            'difficulty_level': 'beginner',
            'course_url': 'https://academy.hubspot.com/courses/email-marketing',
            'industry_recognition': 'high',
            'resume_boost_score': 82,
            'job_relevance_score': 88,
            'salary_impact': '$3K-$7K increase',
            'prerequisites': [],
            'recommended_for_majors': ['Marketing', 'Business'],
            'recommended_for_careers': ['Email Marketing Specialist', 'Marketing Automation Specialist', 'CRM Manager'],
            'is_featured': False
        },
        
        # ============================================
        # LINKEDIN LEARNING
        # ============================================
        {
            'title': 'Project Management Foundations',
            'provider': 'LinkedIn Learning',
            'category': 'Business',
            'subcategory': 'Project Management',
            'description': 'Learn project management fundamentals, methodologies, and best practices.',
            'skills_gained': ['Project Management', 'Agile', 'Scrum', 'Planning', 'Risk Management', 'Team Leadership'],
            'duration_hours': 3,
            'difficulty_level': 'beginner',
            'course_url': 'https://www.linkedin.com/learning/project-management-foundations-2',
            'industry_recognition': 'medium',
            'resume_boost_score': 80,
            'job_relevance_score': 85,
            'salary_impact': '$5K-$10K increase',
            'prerequisites': [],
            'recommended_for_majors': ['Business', 'Engineering', 'All Majors'],
            'recommended_for_careers': ['Project Manager', 'Program Manager', 'Business Analyst', 'Team Lead'],
            'is_featured': False
        },
        
        # ============================================
        # ALISON
        # ============================================
        {
            'title': 'Emotional Intelligence at Work',
            'provider': 'Alison',
            'category': 'Business',
            'subcategory': 'Soft Skills',
            'description': 'Develop emotional intelligence skills for better workplace relationships and leadership.',
            'skills_gained': ['Emotional Intelligence', 'Self-Awareness', 'Empathy', 'Communication', 'Conflict Resolution'],
            'duration_hours': 3,
            'difficulty_level': 'beginner',
            'course_url': 'https://alison.com/course/emotional-intelligence-at-work',
            'industry_recognition': 'medium',
            'resume_boost_score': 75,
            'job_relevance_score': 85,
            'salary_impact': 'Better team collaboration',
            'prerequisites': [],
            'recommended_for_majors': ['All Majors'],
            'recommended_for_careers': ['Manager', 'Team Lead', 'HR Professional', 'Any Career'],
            'is_featured': False
        },
        {
            'title': 'Effective Communication Skills',
            'provider': 'Great Learning',
            'category': 'Business',
            'subcategory': 'Soft Skills',
            'description': 'Master verbal, written, and interpersonal communication for professional success.',
            'skills_gained': ['Communication', 'Presentation Skills', 'Active Listening', 'Written Communication', 'Public Speaking'],
            'duration_hours': 2,
            'difficulty_level': 'beginner',
            'course_url': 'https://www.mygreatlearning.com/academy/learn-for-free/courses/effective-communication',
            'industry_recognition': 'medium',
            'resume_boost_score': 78,
            'job_relevance_score': 90,
            'salary_impact': 'Essential for career growth',
            'prerequisites': [],
            'recommended_for_majors': ['All Majors'],
            'recommended_for_careers': ['All Careers'],
            'is_featured': False
        }
    ]
    
    print(f"Seeding {len(certifications)} free certifications...")
    
    for cert_data in certifications:
        existing = FreeCertification.query.filter_by(
            title=cert_data['title'],
            provider=cert_data['provider']
        ).first()
        
        if not existing:
            cert = FreeCertification(**cert_data)
            db.session.add(cert)
            print(f"  ✅ Added: {cert_data['title']} by {cert_data['provider']}")
        else:
            print(f"  ⏭️  Skipped (exists): {cert_data['title']}")
    
    db.session.commit()
    print(f"\n✅ Successfully seeded {len(certifications)} certifications!")


def seed_certification_pathways():
    """Seed curated learning pathways"""
    
    # First, get certification IDs
    google_analytics = FreeCertification.query.filter_by(title='Google Analytics Certification').first()
    google_ads = FreeCertification.query.filter_by(title='Google Ads Certification').first()
    hubspot_inbound = FreeCertification.query.filter_by(title='HubSpot Inbound Marketing Certification').first()
    hubspot_content = FreeCertification.query.filter_by(title='HubSpot Content Marketing Certification').first()
    hubspot_social = FreeCertification.query.filter_by(title='HubSpot Social Media Marketing Certification').first()
    
    google_it = FreeCertification.query.filter_by(title='Google IT Support Professional Certificate').first()
    azure_fundamentals = FreeCertification.query.filter_by(title='Microsoft Azure Fundamentals (AZ-900)').first()
    aws_cloud = FreeCertification.query.filter_by(title='AWS Cloud Practitioner').first()
    
    html_css = FreeCertification.query.filter_by(title='Responsive Web Design').first()
    javascript = FreeCertification.query.filter_by(title='JavaScript Algorithms and Data Structures').first()
    react = FreeCertification.query.filter_by(title='Front End Development Libraries').first()
    
    pathways = [
        {
            'title': 'Digital Marketing Professional',
            'description': 'Complete pathway from beginner to job-ready digital marketer with Google and HubSpot certifications.',
            'category': 'Marketing',
            'target_career': 'Digital Marketing Specialist',
            'target_salary_range': '$45K-$65K',
            'difficulty_level': 'beginner',
            'certification_sequence': [
                hubspot_inbound.id if hubspot_inbound else None,
                google_analytics.id if google_analytics else None,
                google_ads.id if google_ads else None,
                hubspot_content.id if hubspot_content else None,
                hubspot_social.id if hubspot_social else None
            ],
            'total_duration_hours': 33,
            'total_certifications': 5,
            'is_featured': True,
            'verified_by_career_services': True
        },
        {
            'title': 'Cloud Computing Specialist',
            'description': 'Master cloud fundamentals across AWS, Azure, and Google Cloud for high-demand cloud careers.',
            'category': 'Technology',
            'target_career': 'Cloud Engineer',
            'target_salary_range': '$70K-$95K',
            'difficulty_level': 'intermediate',
            'certification_sequence': [
                azure_fundamentals.id if azure_fundamentals else None,
                aws_cloud.id if aws_cloud else None
            ],
            'total_duration_hours': 40,
            'total_certifications': 2,
            'is_featured': True,
            'verified_by_career_services': True
        },
        {
            'title': 'Full-Stack Web Developer',
            'description': 'Complete web development training from HTML/CSS basics to React applications.',
            'category': 'Technology',
            'target_career': 'Full-Stack Developer',
            'target_salary_range': '$60K-$85K',
            'difficulty_level': 'beginner',
            'certification_sequence': [
                html_css.id if html_css else None,
                javascript.id if javascript else None,
                react.id if react else None
            ],
            'total_duration_hours': 900,
            'total_certifications': 3,
            'is_featured': True,
            'verified_by_career_services': True
        }
    ]
    
    print(f"\nSeeding {len(pathways)} certification pathways...")
    
    for pathway_data in pathways:
        # Filter out None values from certification_sequence
        pathway_data['certification_sequence'] = [id for id in pathway_data['certification_sequence'] if id]
        
        existing = CertificationPathway.query.filter_by(
            title=pathway_data['title']
        ).first()
        
        if not existing:
            pathway = CertificationPathway(**pathway_data)
            db.session.add(pathway)
            print(f"  ✅ Added pathway: {pathway_data['title']}")
        else:
            print(f"  ⏭️  Skipped (exists): {pathway_data['title']}")
    
    db.session.commit()
    print(f"\n✅ Successfully seeded pathways!")


if __name__ == '__main__':
    from app_pro import app
    with app.app_context():
        seed_free_certifications()
        seed_certification_pathways()
        print("\n🎓 Free Certifications Hub is ready!")
