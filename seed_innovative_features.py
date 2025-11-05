"""
Seed data for innovative features
Realistic PSU data for testing (5 features PSU genuinely needs)
"""

from app_pro import app
from extensions import db
from models_innovative_features import *
from datetime import datetime, timedelta, date
from decimal import Decimal


def seed_study_groups():
    """Seed study groups"""
    print("Seeding study groups...")
    
    groups = [
        StudyGroup(
            creator_id=1,
            course_code='MATH 147',
            course_name='Calculus I',
            professor_name='Dr. Johnson',
            group_name='Calculus Crew',
            description='Study group for MATH 147. We meet weekly to work through homework and prepare for exams.',
            focus_topics='Derivatives, integrals, limits, exam prep',
            meeting_location='Axe Library Room 201',
            is_virtual=False,
            meeting_schedule='Tuesdays 6-8pm, Thursdays 7-9pm',
            next_meeting=datetime.utcnow() + timedelta(days=2, hours=18),
            max_members=6,
            current_members=3,
            group_type='open',
            commitment_level='moderate',
            requires_approval=False
        ),
        StudyGroup(
            creator_id=2,
            course_code='CHEM 121',
            course_name='General Chemistry I',
            professor_name='Dr. Williams',
            group_name='Chemistry Study Sessions',
            description='Preparing for midterm exam. All welcome!',
            focus_topics='Stoichiometry, atomic structure, chemical bonding',
            meeting_location='Virtual',
            is_virtual=True,
            virtual_link='https://zoom.us/j/123456789',
            meeting_schedule='Sundays 4-6pm',
            next_meeting=datetime.utcnow() + timedelta(days=4, hours=16),
            max_members=8,
            current_members=5,
            group_type='exam_prep',
            commitment_level='serious',
            requires_approval=False
        ),
        StudyGroup(
            creator_id=3,
            course_code='CS 101',
            course_name='Introduction to Computer Science',
            professor_name='Dr. Anderson',
            group_name='Code Gorillas',
            description='Learn Python together! Work on assignments and projects.',
            focus_topics='Python basics, loops, functions, debugging',
            meeting_location='Heckert-Wells Room 105',
            is_virtual=False,
            meeting_schedule='Wednesdays 5-7pm',
            next_meeting=datetime.utcnow() + timedelta(days=1, hours=17),
            max_members=10,
            current_members=7,
            group_type='project_team',
            commitment_level='casual',
            requires_approval=False
        ),
        StudyGroup(
            creator_id=1,
            course_code='BIO 101',
            course_name='General Biology',
            group_name='Bio Study Squad',
            description='Weekly study sessions for Biology 101. Exam prep and lab report help.',
            focus_topics='Cell biology, genetics, evolution',
            meeting_location='Yates Hall Study Room',
            meeting_schedule='Mondays 7-9pm',
            next_meeting=datetime.utcnow() + timedelta(hours=24),
            max_members=5,
            current_members=4,
            is_full=False,
            commitment_level='moderate'
        ),
    ]
    
    for group in groups:
        db.session.add(group)
    
    db.session.commit()
    print(f"✅ Created {len(groups)} study groups")


def seed_wellness_resources():
    """Seed wellness resources"""
    print("Seeding wellness resources...")
    
    resources = [
        WellnessResource(
            title='National Suicide Prevention Lifeline',
            description='24/7 crisis support for anyone in suicidal crisis or emotional distress.',
            category='crisis',
            phone_number='988',
            is_24_7=True,
            is_emergency=True,
            priority=10
        ),
        WellnessResource(
            title='Crisis Text Line',
            description='Free 24/7 crisis support via text. Text HOME to 741741.',
            category='crisis',
            phone_number='741741',
            is_24_7=True,
            is_emergency=True,
            priority=9
        ),
        WellnessResource(
            title='PSU Counseling Center',
            description='Free confidential counseling for PSU students. Individual and group therapy available.',
            category='counseling',
            phone_number='(620) 235-4522',
            email='counseling@pittstate.edu',
            location='Horace Mann Hall, Room 104',
            hours='M-F 8:00am-5:00pm',
            is_24_7=False,
            priority=8
        ),
        WellnessResource(
            title='Campus Police',
            description='Emergency services, campus safety, SafeRide program.',
            category='crisis',
            phone_number='(620) 235-4624',
            location='1701 S. Broadway',
            is_24_7=True,
            priority=7
        ),
        WellnessResource(
            title='Student Health Center',
            description='Medical services for students. Appointments and walk-ins available.',
            category='health',
            phone_number='(620) 235-4291',
            location='Horace Mann Hall, Ground Floor',
            hours='M-F 8:00am-4:30pm',
            priority=6
        ),
        WellnessResource(
            title='Academic Success Center',
            description='Free tutoring, study skills workshops, time management help.',
            category='academic',
            phone_number='(620) 235-4199',
            location='Gorilla Village, Building 5',
            hours='M-Th 10:00am-8:00pm, F 10:00am-2:00pm',
            priority=5
        ),
        WellnessResource(
            title='Financial Aid Office',
            description='Help with financial aid, scholarships, emergency grants.',
            category='financial',
            phone_number='(620) 235-4240',
            email='finaid@pittstate.edu',
            location='Russ Hall, Suite 203',
            hours='M-F 8:00am-5:00pm',
            priority=4
        ),
    ]
    
    for resource in resources:
        db.session.add(resource)
    
    db.session.commit()
    print(f"✅ Created {len(resources)} wellness resources")


def seed_lost_found():
    """Seed lost & found items"""
    print("Seeding lost & found items...")
    
    items = [
        LostItem(
            user_id=1,
            item_type='lost',
            category='phone',
            title='iPhone 13 - Black',
            description='Lost my black iPhone 13 in a Crimson & Gold phone case with PSU sticker on back.',
            location='Axe Library - 2nd floor',
            date_lost_found=date.today() - timedelta(days=1),
            time_approximate='Around 2pm',
            contact_method='email',
            status='active'
        ),
        LostItem(
            user_id=2,
            item_type='found',
            category='keys',
            title='Found: Car keys with Gorilla keychain',
            description='Found car keys on Honda keychain with PSU Gorilla keyring.',
            location='Parking Lot A',
            date_lost_found=date.today(),
            time_approximate='Morning',
            contact_method='message',
            status='active'
        ),
        LostItem(
            user_id=3,
            item_type='lost',
            category='wallet',
            title='Brown Leather Wallet',
            description='Brown leather bifold wallet with student ID, drivers license, and debit card.',
            location='Gorilla Crossing',
            date_lost_found=date.today() - timedelta(days=2),
            contact_method='phone',
            status='active'
        ),
        LostItem(
            user_id=1,
            item_type='found',
            category='clothing',
            title='Found: Gray PSU Hoodie',
            description='Gray PSU hoodie, size M, left in Heckert-Wells Room 105.',
            location='Heckert-Wells Room 105',
            date_lost_found=date.today() - timedelta(days=1),
            contact_method='message',
            status='active'
        ),
    ]
    
    for item in items:
        db.session.add(item)
    
    db.session.commit()
    print(f"✅ Created {len(items)} lost & found items")


def seed_sublease():
    """Seed sublease listings"""
    print("Seeding sublease listings...")
    
    listings = [
        SubleasePosting(
            user_id=1,
            title='Summer Sublease - Campus View Apartments',
            address='801 N. Elm St, Pittsburg, KS 66762',
            property_type='apartment',
            available_from=date(2025, 5, 15),
            available_until=date(2025, 8, 1),
            monthly_rent=Decimal('600.00'),
            security_deposit=Decimal('300.00'),
            bedrooms=1,
            bathrooms=Decimal('1.0'),
            furnished=True,
            utilities_included='Water, Trash, Internet',
            estimated_utilities=Decimal('50.00'),
            has_roommates=False,
            parking_available=True,
            pets_allowed=False,
            laundry='in_unit',
            description='Fully furnished 1BR apartment right across from campus! Perfect for summer internship or classes. All appliances included. Pool and gym access.',
            status='available'
        ),
        SubleasePosting(
            user_id=2,
            title='Room in 3BR House - Walking Distance to Campus',
            address='305 W. Cleveland St, Pittsburg, KS',
            property_type='room',
            available_from=date(2025, 1, 1),
            available_until=date(2025, 5, 15),
            monthly_rent=Decimal('450.00'),
            security_deposit=Decimal('450.00'),
            bedrooms=1,
            bathrooms=Decimal('1.5'),
            furnished=False,
            utilities_included='None',
            estimated_utilities=Decimal('80.00'),
            has_roommates=True,
            number_of_roommates=2,
            roommate_gender_preference='any',
            parking_available=True,
            pets_allowed=True,
            laundry='on_site',
            description='Graduating early! Need someone to take over my room in a great house. 2 cool roommates (both juniors). 10-minute walk to campus. Big backyard.',
            status='available'
        ),
        SubleasePosting(
            user_id=3,
            title='Study Abroad Sublease - Gorilla Heights',
            address='2401 S. Rouse St, Pittsburg, KS',
            property_type='apartment',
            available_from=date(2025, 8, 15),
            available_until=date(2025, 12, 15),
            monthly_rent=Decimal('550.00'),
            bedrooms=2,
            bathrooms=Decimal('2.0'),
            furnished=True,
            utilities_included='Water, Trash',
            has_roommates=True,
            number_of_roommates=1,
            parking_available=True,
            laundry='on_site',
            description='Going to study abroad in Spain for fall semester! 2BR/2BA apartment, you get your own bedroom and bathroom. Roommate is super chill. On shuttle route.',
            status='available'
        ),
    ]
    
    for listing in listings:
        db.session.add(listing)
    
    db.session.commit()
    print(f"✅ Created {len(listings)} sublease listings")


def seed_free_stuff():
    """Seed free stuff items"""
    print("Seeding free stuff items...")
    
    items = [
        FreeStuff(
            user_id=1,
            title='Mini Fridge - Works Great!',
            description='Black mini fridge, 3.2 cubic feet. Used for 2 years in dorm, works perfectly. Just don\'t have room in new apartment.',
            category='electronics',
            condition='good',
            pickup_location='Campus View Apartments, Building 3',
            pickup_instructions='Text me and I\'ll meet you in the lobby',
            available_until=date.today() + timedelta(days=7),
            first_come_first_serve=True,
            student_only=True,
            status='available'
        ),
        FreeStuff(
            user_id=2,
            title='Desk Lamp + Study Supplies',
            description='LED desk lamp (works great!) plus misc. study supplies: binders, pens, highlighters, post-its.',
            category='misc',
            condition='like_new',
            pickup_location='Gorilla Village Building 2, Room 205',
            pickup_instructions='Knock on door, usually home after 3pm',
            student_only=True,
            status='available'
        ),
        FreeStuff(
            user_id=3,
            title='PSYCH 101 Textbook (Old Edition)',
            description='Psychology textbook, 12th edition. Not the current edition but still has great info for studying!',
            category='books',
            condition='fair',
            pickup_location='Axe Library - I\'m usually on 2nd floor studying',
            student_only=True,
            status='available'
        ),
        FreeStuff(
            user_id=1,
            title='Futon - Free if you can move it!',
            description='Gray futon/couch. Decent condition, some stains but comfy. You MUST have a truck or SUV to haul it.',
            category='furniture',
            condition='fair',
            pickup_location='305 W. Cleveland (house), available this weekend',
            pickup_instructions='Must pick up Saturday or Sunday. Help loading it into your vehicle.',
            available_until=date.today() + timedelta(days=5),
            status='available'
        ),
        FreeStuff(
            user_id=2,
            title='Women\'s Winter Coat - Size M',
            description='Black North Face coat, size medium. Still warm and functional, just bought a new one.',
            category='clothing',
            condition='good',
            pickup_location='Gorilla Crossing - I work here M-F 11am-2pm',
            student_only=True,
            status='available'
        ),
    ]
    
    for item in items:
        db.session.add(item)
    
    db.session.commit()
    print(f"✅ Created {len(items)} free items")


def run_all_seeds():
    """Run all seed functions"""
    with app.app_context():
        print("=" * 60)
        print("SEEDING INNOVATIVE FEATURES (5 PSU-Specific Features)")
        print("=" * 60)
        
        seed_study_groups()
        seed_wellness_resources()
        seed_lost_found()
        seed_sublease()
        seed_free_stuff()
        
        print("\n" + "=" * 60)
        print("✅ ALL SEED DATA CREATED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📊 Summary:")
        print("  • 4 study groups")
        print("  • 7 wellness resources")
        print("  • 4 lost & found items")
        print("  • 3 sublease listings")
        print("  • 5 free items")
        print("\n🎉 Ready to test all features!")

if __name__ == '__main__':
    run_all_seeds()
