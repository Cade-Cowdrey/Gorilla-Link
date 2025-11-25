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
            # Breakfast Items
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
                description="Stack of fluffy buttermilk pancakes with syrup",
                category="Breakfast",
                dietary_tags=["vegetarian"],
                allergens=["eggs", "milk", "wheat"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Bacon & Sausage",
                description="Crispy bacon and breakfast sausage links",
                category="Breakfast",
                allergens=["pork"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Fresh Fruit Bar",
                description="Selection of seasonal fresh fruits and berries",
                category="Breakfast",
                dietary_tags=["vegan", "gluten_free", "vegetarian"],
                allergens=[],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Oatmeal Bar",
                description="Hot oatmeal with toppings: brown sugar, raisins, nuts, berries",
                category="Breakfast",
                dietary_tags=["vegan", "vegetarian"],
                allergens=["tree_nuts"],
                is_available=True
            ),
            
            # Lunch/Dinner - A-Zone (Allergen-Aware Station)
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
                name="Baked Salmon (A-Zone)",
                description="Herb-seasoned baked salmon fillet",
                category="Dinner",
                dietary_tags=["gluten_free"],
                allergens=["fish"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Steamed Vegetables (A-Zone)",
                description="Fresh steamed seasonal vegetables without butter",
                category="Lunch",
                dietary_tags=["vegan", "gluten_free", "vegetarian"],
                allergens=[],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="White Rice (A-Zone)",
                description="Plain steamed white rice",
                category="Lunch",
                dietary_tags=["vegan", "gluten_free", "vegetarian"],
                allergens=[],
                is_available=True
            ),
            
            # Regular Lunch/Dinner Stations
            MenuItem(
                location_id=gibson.id,
                name="Pizza - Cheese & Pepperoni",
                description="Fresh baked pizza with variety of toppings daily",
                category="Lunch",
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Build-Your-Own Burger",
                description="Made-to-order burgers with all the fixings",
                category="Lunch",
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Salad Bar",
                description="Build your own salad with fresh greens, veggies, and dressings",
                category="Lunch",
                dietary_tags=["vegan", "vegetarian", "gluten_free"],
                allergens=[],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Pasta Station",
                description="Choice of pasta with marinara, alfredo, or meat sauce",
                category="Dinner",
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Taco Bar",
                description="Build your own tacos with seasoned beef, chicken, and toppings",
                category="Dinner",
                dietary_tags=["gluten_free"],
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Fried Chicken",
                description="Crispy fried chicken with choice of sides",
                category="Dinner",
                allergens=["wheat", "eggs"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Mashed Potatoes & Gravy",
                description="Creamy mashed potatoes with brown gravy",
                category="Dinner",
                dietary_tags=["vegetarian"],
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Soup of the Day",
                description="Fresh homemade soup - changes daily",
                category="Lunch",
                allergens=["varies"],
                is_available=True
            ),
            MenuItem(
                location_id=gibson.id,
                name="Dessert Bar",
                description="Cookies, brownies, ice cream, and daily specials",
                category="Dinner",
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk", "eggs"],
                is_available=True
            ),
        ]
        
        for item in gibson_items:
            db.session.add(item)
        
        # Add sample items for Gorilla Crossing with realistic pricing
        print("Adding sample menu items for Gorilla Crossing...")
        
        gc_items = [
            # Pizza Hut Items
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Pizza Hut Personal Pan Pizza - Cheese",
                description="Classic Pizza Hut personal cheese pizza",
                category="Lunch",
                price=6.49,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Pizza Hut Personal Pan Pizza - Pepperoni",
                description="Personal pepperoni pizza",
                category="Lunch",
                price=6.99,
                allergens=["wheat", "milk", "pork"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Pizza Hut Breadsticks",
                description="6 breadsticks with marinara sauce",
                category="Snacks",
                price=4.99,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            
            # Overman Burger Company
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Classic Overman Burger",
                description="1/4 lb burger with lettuce, tomato, pickle, onion",
                category="Lunch",
                price=7.49,
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Bacon Cheeseburger",
                description="1/4 lb burger with bacon, cheese, and all toppings",
                category="Lunch",
                price=8.99,
                allergens=["wheat", "soy", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Chicken Sandwich",
                description="Crispy or grilled chicken breast sandwich",
                category="Lunch",
                price=7.99,
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="French Fries",
                description="Crispy golden french fries",
                category="Snacks",
                price=3.49,
                dietary_tags=["vegan", "vegetarian"],
                allergens=["soy"],
                is_available=True
            ),
            
            # Pitt BBQ
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
                name="BBQ Chicken Sandwich",
                description="Grilled chicken with BBQ sauce",
                category="Lunch",
                price=7.49,
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="BBQ Brisket Plate",
                description="Smoked beef brisket with 2 sides",
                category="Lunch",
                price=9.99,
                allergens=["soy"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Mac & Cheese",
                description="Creamy homemade mac and cheese",
                category="Snacks",
                price=3.99,
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk"],
                is_available=True
            ),
            
            # Sub Stand
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Turkey & Cheese Sub",
                description="Fresh turkey sub with cheese, lettuce, tomato, mayo",
                category="Lunch",
                price=6.99,
                allergens=["wheat", "soy", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Italian Sub",
                description="Ham, salami, pepperoni with provolone and Italian dressing",
                category="Lunch",
                price=7.49,
                allergens=["wheat", "soy", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Veggie Sub",
                description="Fresh vegetables with cheese on your choice of bread",
                category="Lunch",
                price=6.49,
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=gorilla_crossing.id,
                name="Philly Cheesesteak",
                description="Thinly sliced steak with grilled peppers, onions, cheese",
                category="Lunch",
                price=8.49,
                allergens=["wheat", "soy", "milk"],
                is_available=True
            ),
        ]
        
        for item in gc_items:
            db.session.add(item)
        
        # Add sample items for Axe Grind (Starbucks)
        print("Adding sample menu items for Axe Grind...")
        
        axe_items = [
            # Hot Coffee
            MenuItem(
                location_id=axe_grind.id,
                name="Pike Place Roast",
                description="Starbucks signature medium roast coffee",
                category="Snacks",
                price=2.45,
                dietary_tags=["vegan"],
                allergens=[],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Caffe Latte",
                description="Espresso with steamed milk and light foam",
                category="Snacks",
                price=4.75,
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Cappuccino",
                description="Espresso with equal parts steamed milk and foam",
                category="Snacks",
                price=4.45,
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Caramel Macchiato",
                description="Vanilla-flavored latte with caramel drizzle",
                category="Snacks",
                price=5.25,
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="White Chocolate Mocha",
                description="Espresso with white chocolate and steamed milk",
                category="Snacks",
                price=5.45,
                allergens=["milk", "soy"],
                is_available=True
            ),
            
            # Cold Drinks
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
                name="Iced Caramel Macchiato",
                description="Cold version of the classic caramel macchiato",
                category="Snacks",
                price=5.45,
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Strawberry Acai Refresher",
                description="Sweet strawberry flavors with acai and green coffee",
                category="Snacks",
                price=4.95,
                dietary_tags=["vegan"],
                allergens=[],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Mango Dragonfruit Refresher",
                description="Tropical blend of mango and dragonfruit flavors",
                category="Snacks",
                price=4.95,
                dietary_tags=["vegan"],
                allergens=[],
                is_available=True
            ),
            
            # Frappuccinos
            MenuItem(
                location_id=axe_grind.id,
                name="Caramel Frappuccino",
                description="Blended caramel coffee drink with whipped cream",
                category="Snacks",
                price=5.95,
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Mocha Frappuccino",
                description="Blended coffee with chocolate, milk, and ice",
                category="Snacks",
                price=5.75,
                allergens=["milk", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Vanilla Bean Frappuccino",
                description="Creamy vanilla blended drink (no coffee)",
                category="Snacks",
                price=5.45,
                allergens=["milk"],
                is_available=True
            ),
            
            # Food Items
            MenuItem(
                location_id=axe_grind.id,
                name="Turkey & Cheese Sandwich",
                description="Fresh turkey and cheese on multigrain bread",
                category="Snacks",
                price=6.95,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Ham & Swiss Sandwich",
                description="Black forest ham with swiss cheese",
                category="Snacks",
                price=6.95,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Chicken Caesar Wrap",
                description="Grilled chicken with romaine and caesar dressing",
                category="Snacks",
                price=7.45,
                allergens=["wheat", "milk", "eggs", "fish"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Blueberry Muffin",
                description="Freshly baked blueberry muffin",
                category="Snacks",
                price=3.45,
                dietary_tags=["vegetarian"],
                allergens=["wheat", "eggs", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Chocolate Chip Cookie",
                description="Classic chocolate chip cookie",
                category="Snacks",
                price=2.95,
                dietary_tags=["vegetarian"],
                allergens=["wheat", "eggs", "milk", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=axe_grind.id,
                name="Protein Box - Eggs & Cheese",
                description="Hard-boiled eggs, cheese, fruit, and nuts",
                category="Snacks",
                price=6.45,
                dietary_tags=["vegetarian", "gluten_free"],
                allergens=["eggs", "milk", "tree_nuts"],
                is_available=True
            ),
        ]
        
        for item in axe_items:
            db.session.add(item)
        
        # Add items for University Club
        print("Adding sample menu items for University Club...")
        
        uc_items = [
            # Einstein Bros Bagels
            MenuItem(
                location_id=university_club.id,
                name="Plain Bagel with Cream Cheese",
                description="Fresh-baked plain bagel with plain cream cheese",
                category="Breakfast",
                price=3.99,
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Everything Bagel",
                description="Bagel with sesame, poppy seeds, onion, garlic",
                category="Breakfast",
                price=4.49,
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk", "sesame"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Turkey Sausage Breakfast Sandwich",
                description="Turkey sausage, egg, and cheese on a bagel",
                category="Breakfast",
                price=6.99,
                allergens=["wheat", "eggs", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Bacon & Egg Sandwich",
                description="Bacon, scrambled eggs, and cheddar on a bagel",
                category="Breakfast",
                price=6.99,
                allergens=["wheat", "eggs", "milk", "pork"],
                is_available=True
            ),
            
            # Chilaca Mexican
            MenuItem(
                location_id=university_club.id,
                name="Beef Burrito",
                description="Seasoned beef with rice, beans, cheese, and salsa",
                category="Lunch",
                price=7.99,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Chicken Burrito",
                description="Grilled chicken with rice, beans, cheese, and toppings",
                category="Lunch",
                price=7.99,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Veggie Burrito",
                description="Black beans, rice, peppers, onions, cheese, salsa",
                category="Lunch",
                price=7.49,
                dietary_tags=["vegetarian"],
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Beef Tacos (3)",
                description="Three soft or hard shell tacos with seasoned beef",
                category="Lunch",
                price=6.99,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Chicken Quesadilla",
                description="Grilled chicken and melted cheese in flour tortilla",
                category="Lunch",
                price=7.49,
                allergens=["wheat", "milk"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Chips & Queso",
                description="Tortilla chips with warm queso cheese dip",
                category="Snacks",
                price=4.99,
                dietary_tags=["vegetarian"],
                allergens=["milk"],
                is_available=True
            ),
            MenuItem(
                location_id=university_club.id,
                name="Chips & Guacamole",
                description="Fresh tortilla chips with homemade guacamole",
                category="Snacks",
                price=5.49,
                dietary_tags=["vegan", "vegetarian", "gluten_free"],
                allergens=[],
                is_available=True
            ),
        ]
        
        for item in uc_items:
            db.session.add(item)
        
        # Add items for KTC Cafe
        print("Adding sample menu items for KTC Cafe...")
        
        ktc_items = [
            MenuItem(
                location_id=ktc_cafe.id,
                name="Chicken Tenders with Fries",
                description="Crispy chicken tenders served with french fries",
                category="Lunch",
                price=7.99,
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=ktc_cafe.id,
                name="Grilled Chicken Wrap",
                description="Grilled chicken with lettuce, tomato, ranch in a wrap",
                category="Lunch",
                price=7.49,
                allergens=["wheat", "milk", "eggs"],
                is_available=True
            ),
            MenuItem(
                location_id=ktc_cafe.id,
                name="Caesar Salad",
                description="Romaine lettuce with parmesan and caesar dressing",
                category="Lunch",
                price=6.99,
                dietary_tags=["vegetarian"],
                allergens=["milk", "eggs", "fish"],
                is_available=True
            ),
            MenuItem(
                location_id=ktc_cafe.id,
                name="Cheeseburger",
                description="1/4 lb burger with cheese, lettuce, tomato",
                category="Lunch",
                price=7.99,
                allergens=["wheat", "milk", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=ktc_cafe.id,
                name="Soup & Sandwich Combo",
                description="Half sandwich with cup of soup",
                category="Lunch",
                price=8.49,
                allergens=["wheat", "varies"],
                is_available=True
            ),
            MenuItem(
                location_id=ktc_cafe.id,
                name="Hot Dog",
                description="All-beef hot dog with choice of toppings",
                category="Snacks",
                price=4.99,
                allergens=["wheat", "soy"],
                is_available=True
            ),
            MenuItem(
                location_id=ktc_cafe.id,
                name="Coffee - Regular or Decaf",
                description="Fresh brewed coffee",
                category="Snacks",
                price=2.25,
                dietary_tags=["vegan"],
                allergens=[],
                is_available=True
            ),
            MenuItem(
                location_id=ktc_cafe.id,
                name="Bottled Drinks",
                description="Soda, water, juice, sports drinks",
                category="Snacks",
                price=2.50,
                dietary_tags=["vegan", "vegetarian"],
                allergens=[],
                is_available=True
            ),
        ]
        
        for item in ktc_items:
            db.session.add(item)
        
        db.session.commit()
        print(f"✅ Added {len(gibson_items) + len(gc_items) + len(axe_items) + len(uc_items) + len(ktc_items)} menu items total:")
        print(f"   - Gibson Dining Hall: {len(gibson_items)} items")
        print(f"   - Gorilla Crossing: {len(gc_items)} items")
        print(f"   - Axe Grind (Starbucks): {len(axe_items)} items")
        print(f"   - University Club: {len(uc_items)} items")
        print(f"   - KTC Cafe: {len(ktc_items)} items")
        
        print("\n🎉 Dining data seeding complete!")
        print("\nLocations created:")
        print("1. Gibson Dining Hall (All-you-care-to-eat, meal plan swipes)")
        print("2. Gorilla Crossing (Food court, Dining Dollars only)")
        print("3. The University Club (Einstein Bros & Chilaca)")
        print("4. KTC Cafe (Kansas Technology Center)")
        print("5. Axe Grind (Starbucks in Axe Library)")
        
        # 2. Gorilla Crossing - Food court in Overman Student Center
        gorilla_crossing = DiningLocation(
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
        university_club = DiningLocation(
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
        ktc_cafe = DiningLocation(
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
        axe_grind = DiningLocation(
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
