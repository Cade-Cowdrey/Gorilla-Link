"""
Seed data for innovative features
Realistic PSU data for testing
"""

from app_pro import app
from extensions import db
from models_innovative_features import *
from datetime import datetime, timedelta, date
from decimal import Decimal

def seed_rideshare():
    """Seed rideshare data"""
    print("Seeding rideshare data...")
    
    rides = [
        RideShare(
            driver_id=1,
            trip_type='one_time',
            direction='to_campus',
            origin_city='Kansas City',
            origin_state='MO',
            origin_zip='64108',
            destination_city='Pittsburg',
            departure_date=datetime.utcnow() + timedelta(days=2),
            departure_time='7:00 AM',
            available_seats=3,
            total_seats=3,
            cost_per_person=Decimal('15.00'),
            is_free=False,
            no_smoking=True,
            luggage_space=True,
            stops_allowed=True,
            notes='Coming back to campus after holiday break. Happy to split gas money!',
            phone_number='(913) 555-0101'
        ),
        RideShare(
            driver_id=2,
            trip_type='recurring',
            direction='round_trip',
            origin_city='Joplin',
            origin_state='MO',
            destination_city='Pittsburg',
            departure_date=datetime.utcnow() + timedelta(days=1),
            departure_time='8:00 AM',
            available_seats=2,
            total_seats=2,
            recurring_days='Monday,Wednesday,Friday',
            recurring_until=(datetime.utcnow() + timedelta(days=60)).date(),
            cost_per_person=Decimal('8.00'),
            is_free=False,
            no_smoking=True,
            luggage_space=False,
            notes='Commute from Joplin for MWF classes. Leave Joplin at 8am, return at 4pm.',
            phone_number='(417) 555-0202'
        ),
        RideShare(
            driver_id=3,
            trip_type='one_time',
            direction='from_campus',
            origin_city='Pittsburg',
            destination_city='Springfield',
            departure_date=datetime.utcnow() + timedelta(days=5),
            departure_time='3:00 PM',
            available_seats=4,
            total_seats=4,
            cost_per_person=Decimal('0'),
            is_free=True,
            no_smoking=True,
            luggage_space=True,
            stops_allowed=True,
            notes='Heading home for the weekend. Free ride! Just want company for the drive.',
            phone_number='(417) 555-0303'
        ),
        RideShare(
            driver_id=1,
            trip_type='one_time',
            direction='to_campus',
            origin_city='Tulsa',
            origin_state='OK',
            destination_city='Pittsburg',
            departure_date=datetime.utcnow() + timedelta(days=3),
            departure_time='9:00 AM',
            available_seats=1,
            total_seats=3,
            cost_per_person=Decimal('12.00'),
            is_free=False,
            no_smoking=True,
            luggage_space=True,
            notes='Going to Gorillas football game! Have 1 seat left.',
            phone_number='(918) 555-0404'
        ),
    ]
    
    for ride in rides:
        db.session.add(ride)
    
    db.session.commit()
    print(f"✅ Created {len(rides)} rideshare listings")


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


def seed_parking():
    """Seed parking spots"""
    print("Seeding parking spots...")
    
    spots = [
        ParkingSpot(
            user_id=1,
            listing_type='daily',
            location_name='Lot A - Reserved Spot near Library',
            distance_from_campus=Decimal('0.1'),
            proximity_to_buildings='2-minute walk to Axe Library, 5 minutes to Heckert-Wells',
            available_from=date.today() + timedelta(days=1),
            days_available='Monday-Friday',
            time_available='8am-5pm',
            price_per_day=Decimal('5.00'),
            negotiable=True,
            covered=False,
            reserved=True,
            security_features='Well-lit, camera surveillance',
            description='I have class Tuesday/Thursday only, so my Monday/Wednesday/Friday parking spot just sits empty. Help me offset my $300 parking pass!',
            status='available'
        ),
        ParkingSpot(
            user_id=2,
            listing_type='semester',
            location_name='Off-campus house - 5 blocks from campus',
            distance_from_campus=Decimal('0.3'),
            proximity_to_buildings='8-minute walk to campus center',
            available_from=date.today(),
            available_until=date(2025, 5, 15),
            days_available='All days',
            time_available='All day',
            price_per_semester=Decimal('150.00'),
            negotiable=True,
            covered=False,
            reserved=False,
            description='Extra driveway spot at my house. Cheaper than campus parking and very close! Perfect for commuters.',
            status='available'
        ),
        ParkingSpot(
            user_id=3,
            listing_type='event',
            location_name='Driveway - Walking distance to Carnie Smith Stadium',
            distance_from_campus=Decimal('0.2'),
            proximity_to_buildings='5-minute walk to football stadium',
            available_from=date.today() + timedelta(days=7),
            days_available='Game day',
            time_available='All day',
            price_per_day=Decimal('15.00'),
            covered=False,
            reserved=True,
            description='Rent my driveway for Gorillas home games! Way cheaper than stadium parking ($20) and you don\'t have to fight traffic.',
            status='available'
        ),
    ]
    
    for spot in spots:
        db.session.add(spot)
    
    db.session.commit()
    print(f"✅ Created {len(spots)} parking spots")


def seed_tutoring():
    """Seed tutoring profiles"""
    print("Seeding tutoring profiles...")
    
    tutors = [
        TutorProfile(
            user_id=1,
            bio='Math major, 3.8 GPA. I love helping students understand calculus! Took Calc I-III and got A\'s in all.',
            major='Mathematics',
            year='Senior',
            gpa=Decimal('3.8'),
            subjects='["MATH 147", "MATH 241", "MATH 242"]',
            availability='{"Monday": ["4pm-8pm"], "Wednesday": ["4pm-8pm"], "Saturday": ["10am-4pm"]}',
            preferred_location='Axe Library, Starbucks, or Zoom',
            offers_online=True,
            offers_in_person=True,
            hourly_rate=Decimal('20.00'),
            first_session_free=True,
            tutoring_experience='Tutored for 2 years at Academic Success Center. Helped 50+ students improve grades.',
            avg_rating=Decimal('4.9'),
            total_sessions=45,
            total_reviews=38,
            is_active=True,
            is_verified=True
        ),
        TutorProfile(
            user_id=2,
            bio='Chemistry major preparing for medical school. Aced General Chem I & II and Organic Chem.',
            major='Chemistry',
            year='Junior',
            gpa=Decimal('3.9'),
            subjects='["CHEM 121", "CHEM 122", "CHEM 320", "CHEM 321"]',
            availability='{"Tuesday": ["5pm-9pm"], "Thursday": ["5pm-9pm"], "Sunday": ["2pm-6pm"]}',
            preferred_location='Yates Hall study rooms, Online',
            offers_online=True,
            offers_in_person=True,
            hourly_rate=Decimal('25.00'),
            first_session_free=False,
            group_discount=True,
            tutoring_experience='1 year experience. Helped classmates prepare for MCAT chemistry section.',
            avg_rating=Decimal('5.0'),
            total_sessions=22,
            total_reviews=20,
            is_active=True
        ),
        TutorProfile(
            user_id=3,
            bio='Computer Science major. Expert in Python, Java, C++. Former TA for CS 101.',
            major='Computer Science',
            year='Senior',
            gpa=Decimal('3.7'),
            subjects='["CS 101", "CS 201", "CS 240", "Python", "Java"]',
            availability='{"Monday": ["6pm-10pm"], "Wednesday": ["6pm-10pm"], "Friday": ["4pm-8pm"]}',
            preferred_location='Heckert-Wells, Discord screenshare, Zoom',
            offers_online=True,
            offers_in_person=True,
            hourly_rate=Decimal('22.00'),
            first_session_free=True,
            tutoring_experience='Was a TA for CS 101, tutored 100+ students. Can help with debugging and projects.',
            avg_rating=Decimal('4.8'),
            total_sessions=67,
            total_reviews=55,
            is_active=True,
            is_verified=True
        ),
    ]
    
    for tutor in tutors:
        db.session.add(tutor)
    
    db.session.commit()
    print(f"✅ Created {len(tutors)} tutor profiles")


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
        print("SEEDING INNOVATIVE FEATURES")
        print("=" * 60)
        
        seed_rideshare()
        seed_study_groups()
        seed_wellness_resources()
        seed_lost_found()
        seed_sublease()
        seed_parking()
        seed_tutoring()
        seed_free_stuff()
        
        print("\n" + "=" * 60)
        print("✅ ALL SEED DATA CREATED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📊 Summary:")
        print("  • 4 rideshare trips")
        print("  • 4 study groups")
        print("  • 7 wellness resources")
        print("  • 4 lost & found items")
        print("  • 3 sublease listings")
        print("  • 3 parking spots")
        print("  • 3 tutor profiles")
        print("  • 5 free items")
        print("\n🎉 Ready to test all features!")

if __name__ == '__main__':
    run_all_seeds()
