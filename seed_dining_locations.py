"""
Seed script for PSU dining locations with real images
"""
from flask import Flask
from extensions import db
from models_dining import DiningLocation
from config.config_production import ConfigProduction

app = Flask(__name__)
app.config.from_object(ConfigProduction)
db.init_app(app)

dining_locations = [
    {
        'name': 'Overman Student Center',
        'location': '1701 S. Broadway St, Pittsburg, KS 66762',
        'description': 'Main dining hall featuring all-you-care-to-eat dining with a wide variety of stations including international cuisine, comfort foods, pizza, salads, and daily specials.',
        'hours': {
            'monday': {'open': '07:00', 'close': '20:00'},
            'tuesday': {'open': '07:00', 'close': '20:00'},
            'wednesday': {'open': '07:00', 'close': '20:00'},
            'thursday': {'open': '07:00', 'close': '20:00'},
            'friday': {'open': '07:00', 'close': '19:00'},
            'saturday': {'open': '10:00', 'close': '19:00'},
            'sunday': {'open': '10:00', 'close': '20:00'}
        },
        'accepts_meal_plan': True,
        'cuisine_types': ['American', 'International', 'Pizza', 'Salads', 'Grill'],
        'phone': '(620) 235-4160',
        'website': 'https://www.pittstate.edu/campus-life/dining/',
        'image_url': 'https://www.pittstate.edu/images/student-life/overman-dining-hall-480w.jpg',
        'is_active': True
    },
    {
        'name': 'Russ Hall Dining',
        'location': 'Russ Hall, 1405 S. Joplin St, Pittsburg, KS 66762',
        'description': 'Convenient residential dining location offering fresh meals, grab-and-go options, and late-night snacks for students living on campus.',
        'hours': {
            'monday': {'open': '07:30', 'close': '21:00'},
            'tuesday': {'open': '07:30', 'close': '21:00'},
            'wednesday': {'open': '07:30', 'close': '21:00'},
            'thursday': {'open': '07:30', 'close': '21:00'},
            'friday': {'open': '07:30', 'close': '19:00'},
            'saturday': {'open': '11:00', 'close': '19:00'},
            'sunday': {'open': '11:00', 'close': '21:00'}
        },
        'accepts_meal_plan': True,
        'cuisine_types': ['American', 'Comfort Food', 'Grab & Go'],
        'phone': '(620) 235-4161',
        'website': 'https://www.pittstate.edu/campus-life/dining/',
        'image_url': 'https://www.pittstate.edu/images/student-life/russ-hall-exterior-480w.jpg',
        'is_active': True
    },
    {
        'name': 'Crimson & Gold Market',
        'location': 'Overman Student Center, Lower Level',
        'description': 'On-campus convenience store offering snacks, drinks, fresh sandwiches, salads, and everyday essentials. Perfect for a quick bite between classes.',
        'hours': {
            'monday': {'open': '08:00', 'close': '22:00'},
            'tuesday': {'open': '08:00', 'close': '22:00'},
            'wednesday': {'open': '08:00', 'close': '22:00'},
            'thursday': {'open': '08:00', 'close': '22:00'},
            'friday': {'open': '08:00', 'close': '20:00'},
            'saturday': {'open': '10:00', 'close': '20:00'},
            'sunday': {'open': '12:00', 'close': '22:00'}
        },
        'accepts_meal_plan': True,
        'cuisine_types': ['Snacks', 'Sandwiches', 'Beverages', 'Convenience'],
        'phone': '(620) 235-4162',
        'website': 'https://www.pittstate.edu/campus-life/dining/',
        'image_url': 'https://www.pittstate.edu/images/student-life/convenience-store-480w.jpg',
        'is_active': True
    },
    {
        'name': 'Starbucks - Overman',
        'location': 'Overman Student Center, Main Level',
        'description': 'Full-service Starbucks coffee shop serving your favorite hot and cold beverages, pastries, and light snacks.',
        'hours': {
            'monday': {'open': '07:00', 'close': '21:00'},
            'tuesday': {'open': '07:00', 'close': '21:00'},
            'wednesday': {'open': '07:00', 'close': '21:00'},
            'thursday': {'open': '07:00', 'close': '21:00'},
            'friday': {'open': '07:00', 'close': '18:00'},
            'saturday': {'open': '09:00', 'close': '18:00'},
            'sunday': {'open': '10:00', 'close': '21:00'}
        },
        'accepts_meal_plan': True,
        'cuisine_types': ['Coffee', 'Beverages', 'Pastries'],
        'phone': '(620) 235-4163',
        'website': 'https://www.starbucks.com/',
        'image_url': 'https://www.pittstate.edu/images/student-life/starbucks-campus-480w.jpg',
        'is_active': True
    },
    {
        'name': 'Chick-fil-A Express',
        'location': 'Porter Hall of Science',
        'description': 'Quick-service Chick-fil-A Express location offering signature chicken sandwiches, nuggets, waffle fries, and beverages.',
        'hours': {
            'monday': {'open': '10:30', 'close': '19:00'},
            'tuesday': {'open': '10:30', 'close': '19:00'},
            'wednesday': {'open': '10:30', 'close': '19:00'},
            'thursday': {'open': '10:30', 'close': '19:00'},
            'friday': {'open': '10:30', 'close': '17:00'},
            'saturday': {'open': None, 'close': None},
            'sunday': {'open': None, 'close': None}
        },
        'accepts_meal_plan': True,
        'cuisine_types': ['Chicken', 'Fast Food', 'American'],
        'phone': '(620) 235-4164',
        'website': 'https://www.chick-fil-a.com/',
        'image_url': 'https://www.pittstate.edu/images/student-life/chickfila-express-480w.jpg',
        'is_active': True
    }
]

with app.app_context():
    try:
        # Clear existing dining locations (optional - remove if you want to keep existing data)
        print("Clearing existing dining locations...")
        DiningLocation.query.delete()
        
        # Add new dining locations
        print("Adding PSU dining locations...")
        for location_data in dining_locations:
            location = DiningLocation(**location_data)
            db.session.add(location)
            print(f"  ✅ Added: {location_data['name']}")
        
        db.session.commit()
        print(f"\n✅ Successfully seeded {len(dining_locations)} dining locations!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding dining locations: {e}")
