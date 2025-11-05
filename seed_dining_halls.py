"""
Seed script for Pittsburg State University dining locations
Run this after creating the dining tables migration
"""

from app_pro import app
from extensions import db
from models_dining import DiningLocation, MenuItem
from datetime import time

def seed_dining_data():
    with app.app_context():
        # Clear existing data
        print("Clearing existing dining data...")
        MenuItem.query.delete()
        DiningLocation.query.delete()
        db.session.commit()
        
        print("Creating PSU dining locations...")
        
        # 1. Gibson Dining Hall - All-you-care-to-eat
        gibson = DiningLocation(
            name="Gibson Dining Hall",
            location="Pittsburg State University Campus",
            description="All-you-care-to-eat facility featuring sit-down meals, beverages, and desserts. Primary location for meal plan swipes with the A-Zone allergen and gluten-aware station.",
            hours={
                "monday": {"open": "07:00", "close": "20:00"},
                "tuesday": {"open": "07:00", "close": "20:00"},
                "wednesday": {"open": "07:00", "close": "20:00"},
                "thursday": {"open": "07:00", "close": "20:00"},
                "friday": {"open": "07:00", "close": "19:00"},
                "saturday": {"open": "10:00", "close": "19:00"},
                "sunday": {"open": "10:00", "close": "20:00"}
            },
            accepts_meal_plan=True,
            cuisine_types=["American", "International", "Vegetarian", "Allergen-Aware"],
            website="https://pittstate.campusdish.com/",
            phone="620-235-4169",
            is_active=True
        )
        db.session.add(gibson)
        
        # 2. Gorilla Crossing - Food court in Overman Student Center
        gorilla_crossing = DiningLocation(
            name="Gorilla Crossing",
            location="Overman Student Center",
            description="Food court featuring Pizza Hut, Overman Burger Company, Pitt BBQ, and Sub Stand. Offers quick-service dining options. Note: Meal plan swipes not accepted - use Dining Dollars.",
            hours={
                "monday": {"open": "07:30", "close": "21:00"},
                "tuesday": {"open": "07:30", "close": "21:00"},
                "wednesday": {"open": "07:30", "close": "21:00"},
                "thursday": {"open": "07:30", "close": "21:00"},
                "friday": {"open": "07:30", "close": "19:00"},
                "saturday": {"open": "11:00", "close": "19:00"},
                "sunday": {"open": "11:00", "close": "21:00"}
            },
            accepts_meal_plan=False,
            cuisine_types=["Pizza", "Burgers", "BBQ", "Sandwiches"],
            website="https://pittstate.campusdish.com/",
            phone="620-235-4169",
            is_active=True
        )
        db.session.add(gorilla_crossing)
        
        # 3. The University Club - Einstein Bros & Chilaca
        university_club = DiningLocation(
            name="The University Club",
            location="Lower Level, Overman Student Center",
            description="Features Einstein Bros. Bagels and Chilaca Mexican cuisine. Perfect spot for coffee, bagels, and fresh Mexican dishes.",
            hours={
                "monday": {"open": "07:30", "close": "17:00"},
                "tuesday": {"open": "07:30", "close": "17:00"},
                "wednesday": {"open": "07:30", "close": "17:00"},
                "thursday": {"open": "07:30", "close": "17:00"},
                "friday": {"open": "07:30", "close": "15:00"},
                "saturday": None,
                "sunday": None
            },
            accepts_meal_plan=True,
            cuisine_types=["Bagels", "Coffee", "Mexican", "Breakfast"],
            website="https://pittstate.campusdish.com/",
            phone="620-235-4169",
            is_active=True
        )
        db.session.add(university_club)
        
        # 4. KTC Cafe - Kansas Technology Center
        ktc_cafe = DiningLocation(
            name="KTC Cafe",
            location="Kansas Technology Center",
            description="Convenient cafe offering hot meals, sandwiches, snacks, and drinks for students and faculty in the technology center.",
            hours={
                "monday": {"open": "07:30", "close": "15:00"},
                "tuesday": {"open": "07:30", "close": "15:00"},
                "wednesday": {"open": "07:30", "close": "15:00"},
                "thursday": {"open": "07:30", "close": "15:00"},
                "friday": {"open": "07:30", "close": "14:00"},
                "saturday": None,
                "sunday": None
            },
            accepts_meal_plan=True,
            cuisine_types=["Cafe", "Sandwiches", "Snacks"],
            website="https://pittstate.campusdish.com/",
            phone="620-235-4169",
            is_active=True
        )
        db.session.add(ktc_cafe)
        
        # 5. Axe Grind - Starbucks in Axe Library
        axe_grind = DiningLocation(
            name="Axe Grind",
            location="Axe Library",
            description="Starbucks location serving premium coffee, drinks, smoothies, sandwiches, and snacks. Perfect study break spot in the library.",
            hours={
                "monday": {"open": "07:30", "close": "22:00"},
                "tuesday": {"open": "07:30", "close": "22:00"},
                "wednesday": {"open": "07:30", "close": "22:00"},
                "thursday": {"open": "07:30", "close": "22:00"},
                "friday": {"open": "07:30", "close": "17:00"},
                "saturday": {"open": "10:00", "close": "17:00"},
                "sunday": {"open": "12:00", "close": "22:00"}
            },
            accepts_meal_plan=True,
            cuisine_types=["Coffee", "Starbucks", "Snacks", "Smoothies"],
            website="https://pittstate.campusdish.com/",
            phone="620-235-4169",
            is_active=True
        )
        db.session.add(axe_grind)
        
        db.session.commit()
        print("✅ Created 5 PSU dining locations")
        
        # Add sample menu items for Gibson Dining Hall
        print("Adding sample menu items for Gibson Dining Hall...")
        
        gibson_items = [
            # Breakfast
            MenuItem(
                location_id=gibson.id,
                name="Scrambled Eggs",
                description="Fluffy scrambled eggs made to order",
                category="Breakfast",
                dietary_tags=["vegetarian", "gluten_free"],
                allergens=["eggs"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Pancakes",
                description="Stack of fluffy buttermilk pancakes",
                category="Breakfast",
                dietary_tags=["vegetarian"],
                allergens=["eggs", "milk", "wheat"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Fresh Fruit Bar",
                description="Selection of seasonal fresh fruits",
                category="Breakfast",
                dietary_tags=["vegan", "gluten_free", "vegetarian"],
                allergens=[],
                is_available=True
            ),
            
            # Lunch/Dinner - A-Zone (Allergen-Aware)
            MenuItem(
                location_id=gibson.id,
                name="Grilled Chicken Breast (A-Zone)",
                description="Plain grilled chicken breast from allergen-aware station",
                category="Lunch",
                dietary_tags=["gluten_free"],
                allergens=[],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Steamed Vegetables (A-Zone)",
                description="Fresh steamed seasonal vegetables",
                category="Lunch",
                dietary_tags=["vegan", "gluten_free", "vegetarian"],
                allergens=[],
                is_available=True
            ),
            
            # Regular Lunch/Dinner
            MenuItem(
                location_id=gibson.id,
                name="Pizza",
                description="Fresh baked pizza with variety of toppings",
                category="Lunch",
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Burgers",
                description="Made-to-order burgers with all the fixings",
                category="Lunch",
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Salad Bar",
                description="Build your own salad with fresh ingredients",
                category="Lunch",
                dietary_tags=["vegan", "vegetarian", "gluten_free"],
                allergens=[],
                is_available=True
            ),
        ]
        
        for item in gibson_items:
            db.session.add(item)
        
        # Add sample items for Gorilla Crossing
        print("Adding sample menu items for Gorilla Crossing...")
        
        gc_items = [
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Pizza Hut Personal Pan Pizza",
                description="Classic Pizza Hut personal pizza",
                category="Lunch",
                price=6.99,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Overman Burger",
                description="Signature burger from Overman Burger Company",
                category="Lunch",
                price=7.49,
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Pitt BBQ Pulled Pork Sandwich",
                description="Slow-cooked pulled pork with BBQ sauce",
                category="Lunch",
                price=7.99,
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Sub Stand Turkey Sub",
                description="Fresh turkey sub with veggies",
                category="Lunch",
                price=6.99,
                allergens=["wheat", "soy"],
                is_available=True
            ),
        ]
        
        for item in gc_items:
            db.session.add(item)
        
        # Add sample items for Axe Grind (Starbucks)
        print("Adding sample menu items for Axe Grind...")
        
        axe_items = [
            MenuItem(
                location_id=axe_grind.id,
                name="Caffe Latte",
                description="Starbucks signature espresso with steamed milk",
                category="Snacks",
                price=4.75,
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Cold Brew Coffee",
                description="Smooth, bold cold brew coffee",
                category="Snacks",
                price=4.25,
                dietary_tags=["vegan"],
                allergens=[],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Turkey & Cheese Sandwich",
                description="Fresh turkey and cheese sandwich",
                category="Snacks",
                price=6.95,
                allergens=["wheat", "milk"],
                is_available=True
            ),
        ]
        
        for item in axe_items:
            db.session.add(item)
        
        db.session.commit()
        print(f"✅ Added {len(gibson_items) + len(gc_items) + len(axe_items)} sample menu items")
        
        print("\n🎉 Dining data seeding complete!")
        print("\nLocations created:")
        print("1. Gibson Dining Hall (All-you-care-to-eat, meal plan swipes)")
        print("2. Gorilla Crossing (Food court, Dining Dollars only)")
        print("3. The University Club (Einstein Bros & Chilaca)")
        print("4. KTC Cafe (Kansas Technology Center)")
        print("5. Axe Grind (Starbucks in Axe Library)")

if __name__ == "__main__":
    seed_dining_data()

        
        # 2. Gorilla Crossing - Food court in Overman Student Center
        gorilla_crossing = DiningHall(
            name="Gorilla Crossing",
            location="Overman Student Center",
            description="Food court featuring Pizza Hut, Overman Burger Company, Pitt BBQ, and Sub Stand. Offers quick-service dining options. Note: Meal plan swipes not accepted - use Dining Dollars.",
            hours_json={
                "monday": {"open": "07:30", "close": "21:00"},
                "tuesday": {"open": "07:30", "close": "21:00"},
                "wednesday": {"open": "07:30", "close": "21:00"},
                "thursday": {"open": "07:30", "close": "21:00"},
                "friday": {"open": "07:30", "close": "19:00"},
                "saturday": {"open": "11:00", "close": "19:00"},
                "sunday": {"open": "11:00", "close": "21:00"}
            },
            menu_url="https://pittstate.campusdish.com/",
            image_url="/static/images/dining/gorilla_crossing.jpg",
            phone="620-235-4169",
            capacity=300
        )
        db.session.add(gorilla_crossing)
        
        # 3. The University Club - Einstein Bros & Chilaca
        university_club = DiningHall(
            name="The University Club",
            location="Lower Level, Overman Student Center",
            description="Features Einstein Bros. Bagels and Chilaca Mexican cuisine. Perfect spot for coffee, bagels, and fresh Mexican dishes.",
            hours_json={
                "monday": {"open": "07:30", "close": "17:00"},
                "tuesday": {"open": "07:30", "close": "17:00"},
                "wednesday": {"open": "07:30", "close": "17:00"},
                "thursday": {"open": "07:30", "close": "17:00"},
                "friday": {"open": "07:30", "close": "15:00"},
                "saturday": {"open": "closed", "close": "closed"},
                "sunday": {"open": "closed", "close": "closed"}
            },
            menu_url="https://pittstate.campusdish.com/",
            image_url="/static/images/dining/university_club.jpg",
            phone="620-235-4169",
            capacity=150
        )
        db.session.add(university_club)
        
        # 4. KTC Cafe - Kansas Technology Center
        ktc_cafe = DiningHall(
            name="KTC Cafe",
            location="Kansas Technology Center",
            description="Convenient cafe offering hot meals, sandwiches, snacks, and drinks for students and faculty in the technology center.",
            hours_json={
                "monday": {"open": "07:30", "close": "15:00"},
                "tuesday": {"open": "07:30", "close": "15:00"},
                "wednesday": {"open": "07:30", "close": "15:00"},
                "thursday": {"open": "07:30", "close": "15:00"},
                "friday": {"open": "07:30", "close": "14:00"},
                "saturday": {"open": "closed", "close": "closed"},
                "sunday": {"open": "closed", "close": "closed"}
            },
            menu_url="https://pittstate.campusdish.com/",
            image_url="/static/images/dining/ktc_cafe.jpg",
            phone="620-235-4169",
            capacity=100
        )
        db.session.add(ktc_cafe)
        
        # 5. Axe Grind - Starbucks in Axe Library
        axe_grind = DiningHall(
            name="Axe Grind",
            location="Axe Library",
            description="Starbucks location serving premium coffee, drinks, smoothies, sandwiches, and snacks. Perfect study break spot in the library.",
            hours_json={
                "monday": {"open": "07:30", "close": "22:00"},
                "tuesday": {"open": "07:30", "close": "22:00"},
                "wednesday": {"open": "07:30", "close": "22:00"},
                "thursday": {"open": "07:30", "close": "22:00"},
                "friday": {"open": "07:30", "close": "17:00"},
                "saturday": {"open": "10:00", "close": "17:00"},
                "sunday": {"open": "12:00", "close": "22:00"}
            },
            menu_url="https://pittstate.campusdish.com/",
            image_url="/static/images/dining/axe_grind.jpg",
            phone="620-235-4169",
            capacity=75
        )
        db.session.add(axe_grind)
        
        db.session.commit()
        print("✅ Created 5 PSU dining locations")
        
        # Add sample menu items for Gibson Dining Hall
        print("Adding sample menu items for Gibson Dining Hall...")
        
        gibson_items = [
            # Breakfast
            MenuItem(
                dining_hall_id=gibson.id,
                name="Scrambled Eggs",
                description="Fluffy scrambled eggs made to order",
                category="Breakfast",
                dietary_tags=["vegetarian", "gluten_free"],
                allergens=["eggs"],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=gibson.id,
                name="Pancakes",
                description="Stack of fluffy buttermilk pancakes",
                category="Breakfast",
                dietary_tags=["vegetarian"],
                allergens=["eggs", "milk", "wheat"],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=gibson.id,
                name="Fresh Fruit Bar",
                description="Selection of seasonal fresh fruits",
                category="Breakfast",
                dietary_tags=["vegan", "gluten_free", "vegetarian"],
                allergens=[],
                created_at=db.func.now()
            ),
            
            # Lunch/Dinner - A-Zone (Allergen-Aware)
            MenuItem(
                dining_hall_id=gibson.id,
                name="Grilled Chicken Breast (A-Zone)",
                description="Plain grilled chicken breast from allergen-aware station",
                category="Lunch",
                dietary_tags=["gluten_free"],
                allergens=[],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=gibson.id,
                name="Steamed Vegetables (A-Zone)",
                description="Fresh steamed seasonal vegetables",
                category="Lunch",
                dietary_tags=["vegan", "gluten_free", "vegetarian"],
                allergens=[],
                created_at=db.func.now()
            ),
            
            # Regular Lunch/Dinner
            MenuItem(
                dining_hall_id=gibson.id,
                name="Pizza",
                description="Fresh baked pizza with variety of toppings",
                category="Lunch",
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk"],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=gibson.id,
                name="Burgers",
                description="Made-to-order burgers with all the fixings",
                category="Lunch",
                allergens=["wheat", "soy"],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=gibson.id,
                name="Salad Bar",
                description="Build your own salad with fresh ingredients",
                category="Lunch",
                dietary_tags=["vegan", "vegetarian", "gluten_free"],
                allergens=[],
                created_at=db.func.now()
            ),
        ]
        
        for item in gibson_items:
            db.session.add(item)
        
        # Add sample items for Gorilla Crossing
        print("Adding sample menu items for Gorilla Crossing...")
        
        gc_items = [
            MenuItem(
                dining_hall_id=gorilla_crossing.id,
                name="Pizza Hut Personal Pan Pizza",
                description="Classic Pizza Hut personal pizza",
                category="Lunch",
                price=6.99,
                allergens=["wheat", "milk"],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=gorilla_crossing.id,
                name="Overman Burger",
                description="Signature burger from Overman Burger Company",
                category="Lunch",
                price=7.49,
                allergens=["wheat", "soy"],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=gorilla_crossing.id,
                name="Pitt BBQ Pulled Pork Sandwich",
                description="Slow-cooked pulled pork with BBQ sauce",
                category="Lunch",
                price=7.99,
                allergens=["wheat", "soy"],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=gorilla_crossing.id,
                name="Sub Stand Turkey Sub",
                description="Fresh turkey sub with veggies",
                category="Lunch",
                price=6.99,
                allergens=["wheat", "soy"],
                created_at=db.func.now()
            ),
        ]
        
        for item in gc_items:
            db.session.add(item)
        
        # Add sample items for Axe Grind (Starbucks)
        print("Adding sample menu items for Axe Grind...")
        
        axe_items = [
            MenuItem(
                dining_hall_id=axe_grind.id,
                name="Caffe Latte",
                description="Starbucks signature espresso with steamed milk",
                category="Snacks",
                price=4.75,
                allergens=["milk"],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=axe_grind.id,
                name="Cold Brew Coffee",
                description="Smooth, bold cold brew coffee",
                category="Snacks",
                price=4.25,
                dietary_tags=["vegan"],
                allergens=[],
                created_at=db.func.now()
            ),
            MenuItem(
                dining_hall_id=axe_grind.id,
                name="Turkey & Cheese Sandwich",
                description="Fresh turkey and cheese sandwich",
                category="Snacks",
                price=6.95,
                allergens=["wheat", "milk"],
                created_at=db.func.now()
            ),
        ]
        
        for item in axe_items:
            db.session.add(item)
        
        db.session.commit()
        print(f"✅ Added {len(gibson_items) + len(gc_items) + len(axe_items)} sample menu items")
        
        print("\n🎉 Dining data seeding complete!")
        print("\nLocations created:")
        print("1. Gibson Dining Hall (All-you-care-to-eat, meal plan swipes)")
        print("2. Gorilla Crossing (Food court, Dining Dollars only)")
        print("3. The University Club (Einstein Bros & Chilaca)")
        print("4. KTC Cafe (Kansas Technology Center)")
        print("5. Axe Grind (Starbucks in Axe Library)")

if __name__ == "__main__":
    seed_dining_data()
