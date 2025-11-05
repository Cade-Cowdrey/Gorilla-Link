"""
Complete PSU Dining Seed Script with Real Menus and Pricing
Based on actual PSU dining hall menus from Fall 2023-2025
"""

from app_pro import app
from extensions import db
from models_dining import DiningLocation, MenuItem
from datetime import time

def seed_complete_dining_data():
    with app.app_context():
        # Clear existing data
        print("🗑️  Clearing existing dining data...")
        MenuItem.query.delete()
        DiningLocation.query.delete()
        db.session.commit()
        
        print("🏫 Creating PSU dining locations...")
        
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
        
        # =============================================================================
        # GIBSON DINING HALL MENU ITEMS (All-you-care-to-eat)
        # =============================================================================
        print("🍽️  Adding Gibson Dining Hall menu items...")
        
        gibson_items = [
            # BREAKFAST - Jumpstart Station
            MenuItem(location_id=gibson.id, name="Biscuit with Gravy", category="Breakfast", 
                    calories=220, dietary_tags=["vegetarian"], is_available=True),
            MenuItem(location_id=gibson.id, name="Corned Beef Hash", category="Breakfast", 
                    calories=120, is_available=True),
            MenuItem(location_id=gibson.id, name="Vegetable Egg Scramble with Feta", category="Breakfast", 
                    calories=210, dietary_tags=["vegetarian"], allergens=["eggs", "milk"], is_available=True),
            MenuItem(location_id=gibson.id, name="Scrambled Eggs", category="Breakfast", 
                    calories=150, dietary_tags=["vegetarian"], allergens=["eggs"], is_available=True),
            MenuItem(location_id=gibson.id, name="Sausage Links", category="Breakfast", 
                    calories=200, allergens=["soy"], is_available=True),
            MenuItem(location_id=gibson.id, name="Tater Tots", category="Breakfast", 
                    calories=150, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=gibson.id, name="Chocolate Banana Marble Bread", category="Breakfast", 
                    calories=220, dietary_tags=["vegetarian"], allergens=["wheat", "milk", "eggs"], is_available=True),
            MenuItem(location_id=gibson.id, name="Froot Loop Bar", category="Breakfast", 
                    calories=150, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gibson.id, name="Sweet Potato Hash (A-Zone)", category="Breakfast", 
                    calories=230, dietary_tags=["vegan", "gluten_free"], is_available=True),
            
            # LUNCH/DINNER - Classic Kitchen Station
            MenuItem(location_id=gibson.id, name="Ground Beef with Taco Seasoning", category="Lunch", 
                    calories=240, is_available=True),
            MenuItem(location_id=gibson.id, name="Seasoned Pulled Chicken", category="Lunch", 
                    calories=830, is_available=True),
            MenuItem(location_id=gibson.id, name="Corn Tortilla", category="Lunch", 
                    calories=30, dietary_tags=["vegan", "gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Flour Tortilla", category="Lunch", 
                    calories=90, dietary_tags=["vegan"], allergens=["wheat"], is_available=True),
            MenuItem(location_id=gibson.id, name="Mexican Fiesta Rice", category="Lunch", 
                    calories=210, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=gibson.id, name="Cumin Black Beans", category="Lunch", 
                    calories=70, dietary_tags=["vegan", "gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Fajita Pepper & Onion Blend", category="Lunch", 
                    calories=30, dietary_tags=["vegan", "gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Baked Tilapia", category="Dinner", 
                    calories=120, allergens=["fish"], is_available=True),
            MenuItem(location_id=gibson.id, name="Jerk Tofu", category="Dinner", 
                    calories=60, dietary_tags=["vegan", "vegetarian"], is_available=True),
            MenuItem(location_id=gibson.id, name="Garlic Cheddar Biscuit", category="Dinner", 
                    calories=110, dietary_tags=["vegetarian"], allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gibson.id, name="Roasted Brussels Sprouts", category="Dinner", 
                    calories=130, dietary_tags=["vegan", "gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Honey Buttered Carrots", category="Dinner", 
                    calories=120, dietary_tags=["vegetarian"], allergens=["milk"], is_available=True),
            MenuItem(location_id=gibson.id, name="Capri Vegetables", category="Dinner", 
                    calories=35, dietary_tags=["vegan", "gluten_free"], is_available=True),
            
            # FLAME Station (Grill)
            MenuItem(location_id=gibson.id, name="Herb Baked Chicken Breast (4oz)", category="Lunch", 
                    calories=210, dietary_tags=["gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Chicken Nuggets", category="Lunch", 
                    calories=220, allergens=["wheat"], is_available=True),
            MenuItem(location_id=gibson.id, name="Baked Potato Bar", category="Lunch", 
                    calories=420, dietary_tags=["vegan", "gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="French Fries", category="Lunch", 
                    calories=150, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=gibson.id, name="Sweet Potato Fries", category="Lunch", 
                    calories=240, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=gibson.id, name="White Rice", category="Lunch", 
                    calories=110, dietary_tags=["vegan", "gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Reuben on Marble Bread", category="Lunch", 
                    calories=160, allergens=["wheat"], is_available=True),
            
            # SAUCE & STONE (Pizza Station)
            MenuItem(location_id=gibson.id, name="Cheese Pizza", category="Lunch", 
                    calories=300, dietary_tags=["vegetarian"], allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gibson.id, name="Pepperoni Pizza", category="Lunch", 
                    calories=330, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gibson.id, name="Margherita Pizza", category="Lunch", 
                    calories=330, dietary_tags=["vegetarian"], allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gibson.id, name="BBQ Chicken Pizza", category="Lunch", 
                    calories=520, allergens=["wheat", "milk"], is_available=True),
            
            # SWEET SHOP (Desserts)
            MenuItem(location_id=gibson.id, name="Hurricane Chocolate Cake", category="Snacks", 
                    calories=530, dietary_tags=["vegetarian"], allergens=["wheat", "milk", "eggs"], is_available=True),
            MenuItem(location_id=gibson.id, name="Strawberry Swirl Cheesecake Bar", category="Snacks", 
                    calories=270, dietary_tags=["vegetarian"], allergens=["wheat", "milk", "eggs"], is_available=True),
            
            # A-ZONE (Allergen-Aware Station)
            MenuItem(location_id=gibson.id, name="Honey Glazed Ham (A-Zone)", category="Lunch", 
                    calories=150, dietary_tags=["gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Roasted Fingerling Potatoes (A-Zone)", category="Lunch", 
                    calories=120, dietary_tags=["vegan", "gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Garden Salad with Tomato (A-Zone)", category="Lunch", 
                    calories=35, dietary_tags=["vegan", "gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Taco Meat (A-Zone)", category="Dinner", 
                    calories=130, dietary_tags=["gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Taco Shell (A-Zone)", category="Dinner", 
                    calories=50, dietary_tags=["gluten_free"], is_available=True),
            MenuItem(location_id=gibson.id, name="Seasoned Black Beans (A-Zone)", category="Dinner", 
                    calories=130, dietary_tags=["vegan", "gluten_free"], is_available=True),
        ]
        
        for item in gibson_items:
            db.session.add(item)
        
        # =============================================================================
        # GORILLA CROSSING MENU ITEMS (Food Court)
        # =============================================================================
        print("🍔 Adding Gorilla Crossing menu items...")
        
        gc_items = [
            # OVERMAN BURGER COMPANY
            MenuItem(location_id=gorilla_crossing.id, name="All-American Cheeseburger", 
                    description="American Cheese, Gorilla Sauce, Lettuce, Tomato, Dill Pickle", 
                    category="Lunch", price=6.99, calories=760, 
                    allergens=["wheat", "milk", "eggs"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Jalapeño BBQ Cheeseburger", 
                    description="Cheddar, Pickled Jalapeños, BBQ Sauce, Lettuce, Tomato", 
                    category="Lunch", price=6.99, calories=750, 
                    allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Pub Burger", 
                    description="Burger covered with beer cheese and caramelized onions on a pretzel bun", 
                    category="Lunch", price=7.99, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Grilled Cheese", 
                    description="Classic grilled cheese sandwich", 
                    category="Lunch", price=3.99, dietary_tags=["vegetarian"],
                    allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Chicken Sandwich", 
                    description="Crispy or grilled fillet, Mayo, Lettuce, Tomato, Dill Pickle", 
                    category="Lunch", price=6.99, calories=665, 
                    allergens=["wheat", "eggs"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Chicken Tenders", 
                    description="Comes with your choice of dipping sauce", 
                    category="Lunch", price=6.99, calories=970, 
                    allergens=["wheat"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Philly Cheesesteak", 
                    description="Philly with grilled onions, peppers, and provolone cheese", 
                    category="Lunch", price=7.99, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Crinkle Cut Fries", 
                    description="Classic crinkle cut fries", 
                    category="Snacks", price=3.69, calories=200, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Sweet Potato Tots", 
                    description="Crispy sweet potato tots", 
                    category="Snacks", price=3.69, calories=180, 
                    dietary_tags=["vegetarian"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Fries N' Tots 50/50", 
                    description="Half fries, half tots", 
                    category="Snacks", price=3.69, calories=190, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Burger Combo", 
                    description="Any burger with fries and fountain drink", 
                    category="Lunch", price=3.99, is_available=True),
            
            # PITT BBQ
            MenuItem(location_id=gorilla_crossing.id, name="BBQ Pork", 
                    description="Slow-smoked pulled pork with your choice of BBQ sauce", 
                    category="Lunch", price=7.99, calories=338, allergens=["soy"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="BBQ Brisket", 
                    description="Tender smoked brisket ($2 upcharge)", 
                    category="Lunch", price=9.99, calories=263, is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Burnt Ends", 
                    description="Premium smoked burnt ends ($2 upcharge)", 
                    category="Lunch", price=9.99, calories=327, is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="BBQ Chicken", 
                    description="Tender BBQ chicken", 
                    category="Lunch", price=7.99, calories=200, is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Smoked Sausage", 
                    description="Juicy smoked sausage", 
                    category="Lunch", price=7.99, calories=275, allergens=["soy"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="BBQ Wings", 
                    description="Smoky BBQ chicken wings", 
                    category="Lunch", price=7.99, calories=275, is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="1-Meat, 1-Side Combo", 
                    description="Choose one meat and one side with drink and bread", 
                    category="Lunch", price=9.99, is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="2-Meats, 1-Side Combo", 
                    description="Choose two meats and one side with drink and bread", 
                    category="Lunch", price=10.99, is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Loaded Baked Potato", 
                    description="Baked potato loaded with BBQ toppings", 
                    category="Lunch", price=9.99, calories=279, 
                    dietary_tags=["vegetarian"], allergens=["milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Brisket Mac & Cheese", 
                    description="Mac and cheese topped with smoked brisket", 
                    category="Lunch", price=12.99, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Steak Fries", 
                    description="Thick-cut steak fries", 
                    category="Snacks", price=3.99, calories=213, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Onion Rings", 
                    description="Crispy beer-battered onion rings", 
                    category="Snacks", price=3.99, calories=181, allergens=["wheat"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Queso Mac & Cheese", 
                    description="Creamy queso mac and cheese", 
                    category="Snacks", price=3.99, calories=70, 
                    dietary_tags=["vegetarian"], allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Baked Beans", 
                    description="Southern-style baked beans", 
                    category="Snacks", price=3.99, calories=140, 
                    dietary_tags=["vegetarian"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Macaroni Salad", 
                    description="Classic macaroni salad", 
                    category="Snacks", price=3.99, calories=270, 
                    dietary_tags=["vegetarian"], allergens=["wheat", "eggs"], is_available=True),
            
            # SUB STAND
            MenuItem(location_id=gorilla_crossing.id, name='6" Turkey Sub', 
                    description="Fresh turkey with your choice of bread, cheese, veggies, and sauce", 
                    category="Lunch", price=7.29, calories=75, allergens=["wheat"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name='12" Turkey Sub', 
                    description="Fresh turkey with your choice of bread, cheese, veggies, and sauce", 
                    category="Lunch", price=11.29, allergens=["wheat"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name='6" Ham Sub', 
                    description="Fresh ham with your choice of toppings", 
                    category="Lunch", price=7.29, calories=90, allergens=["wheat"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name='12" Ham Sub', 
                    description="Fresh ham with your choice of toppings", 
                    category="Lunch", price=11.29, allergens=["wheat"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name='6" Tuna Salad Sub', 
                    description="Fresh tuna salad with veggies", 
                    category="Lunch", price=7.29, calories=310, 
                    allergens=["wheat", "eggs", "fish"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name='12" Tuna Salad Sub', 
                    description="Fresh tuna salad with veggies", 
                    category="Lunch", price=11.29, allergens=["wheat", "eggs", "fish"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Grilled Chicken Wrap", 
                    description="Grilled chicken in a whole wheat wrap with your choice of toppings", 
                    category="Lunch", price=9.99, calories=290, allergens=["wheat"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Crispy Chicken Wrap", 
                    description="Crispy chicken in your choice of wrap with toppings", 
                    category="Lunch", price=9.99, calories=330, allergens=["wheat"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Chicken Parmesan Sub", 
                    description="Breaded chicken with marinara and parmesan", 
                    category="Lunch", price=7.29, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Sub Combo", 
                    description="Any sub with bag of chips and 20oz fountain soda", 
                    category="Lunch", price=3.99, is_available=True),
            
            # PIZZA HUT (Prices not listed, using standard pricing)
            MenuItem(location_id=gorilla_crossing.id, name="Pizza Hut Personal Pan Pizza", 
                    description="Classic Pizza Hut personal pizza - Cheese or Pepperoni", 
                    category="Lunch", price=6.99, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=gorilla_crossing.id, name="Pizza Hut Breadsticks", 
                    description="Fresh baked breadsticks with marinara", 
                    category="Snacks", price=4.99, allergens=["wheat", "milk"], is_available=True),
        ]
        
        for item in gc_items:
            db.session.add(item)
        
        # =============================================================================
        # UNIVERSITY CLUB MENU ITEMS (Einstein Bros & Chilaca)
        # =============================================================================
        print("🥯 Adding University Club menu items...")
        
        uc_items = [
            # EINSTEIN BROS BAGELS - Egg Sandwiches
            MenuItem(location_id=university_club.id, name="Classic Egg Sandwich", 
                    description="Egg, cheese, and your choice of meat on a bagel", 
                    category="Breakfast", price=5.99, allergens=["wheat", "eggs", "milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Farmhouse Egg Sandwich", 
                    description="Cage-free eggs, bacon, cheddar, on a bagel", 
                    category="Breakfast", price=6.49, allergens=["wheat", "eggs", "milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Avocado Egg Sandwich", 
                    description="Cage-free eggs, avocado, tomato on a bagel", 
                    category="Breakfast", price=6.99, allergens=["wheat", "eggs"], is_available=True),
            
            # EINSTEIN BROS - Signature Lunch
            MenuItem(location_id=university_club.id, name="Turkey Avocado Sandwich", 
                    description="Roasted turkey, avocado, lettuce, tomato", 
                    category="Lunch", price=7.99, allergens=["wheat"], is_available=True),
            MenuItem(location_id=university_club.id, name="Bacon Turkey Bravo", 
                    description="Turkey, bacon, cheddar, tomato, honey mustard", 
                    category="Lunch", price=8.49, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Classic NY Deli Sandwich", 
                    description="Pastrami or turkey, Swiss, lettuce, tomato", 
                    category="Lunch", price=8.99, allergens=["wheat", "milk"], is_available=True),
            
            # EINSTEIN BROS - Beverages
            MenuItem(location_id=university_club.id, name="Hot Coffee (12oz)", 
                    description="Fresh brewed coffee", 
                    category="Snacks", price=2.19, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=university_club.id, name="Iced Coffee (16oz)", 
                    description="Refreshing iced coffee", 
                    category="Snacks", price=3.49, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=university_club.id, name="Latte (16oz)", 
                    description="Espresso with steamed milk", 
                    category="Snacks", price=4.49, allergens=["milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Cappuccino (16oz)", 
                    description="Espresso with foamed milk", 
                    category="Snacks", price=4.49, allergens=["milk"], is_available=True),
            
            # CHILACA (Mexican)
            MenuItem(location_id=university_club.id, name="Burrito Bowl", 
                    description="Rice, beans, meat, cheese, veggies, salsa", 
                    category="Lunch", price=8.99, allergens=["milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Burrito", 
                    description="Large flour tortilla with rice, beans, meat, toppings", 
                    category="Lunch", price=8.99, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Tacos (3)", 
                    description="Three tacos with your choice of meat and toppings", 
                    category="Lunch", price=8.49, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Quesadilla", 
                    description="Grilled tortilla with cheese and your choice of meat", 
                    category="Lunch", price=7.99, allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Nachos", 
                    description="Tortilla chips with cheese, beans, meat, jalapeños", 
                    category="Lunch", price=7.49, allergens=["milk"], is_available=True),
            MenuItem(location_id=university_club.id, name="Chips & Guacamole", 
                    description="Fresh tortilla chips with house-made guacamole", 
                    category="Snacks", price=4.99, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=university_club.id, name="Chips & Queso", 
                    description="Tortilla chips with warm cheese dip", 
                    category="Snacks", price=4.49, allergens=["milk"], is_available=True),
        ]
        
        for item in uc_items:
            db.session.add(item)
        
        # =============================================================================
        # KTC CAFE MENU ITEMS
        # =============================================================================
        print("☕ Adding KTC Cafe menu items...")
        
        ktc_items = [
            # BREAKFAST
            MenuItem(location_id=ktc_cafe.id, name="Egg, Meat & Cheese Biscuit", 
                    description="Biscuit with egg, your choice of meat, and cheese", 
                    category="Breakfast", price=5.49, calories=440, 
                    allergens=["wheat", "eggs", "milk"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Egg & Cheese Biscuit", 
                    description="Fluffy biscuit with egg and cheese", 
                    category="Breakfast", price=4.99, calories=350, 
                    dietary_tags=["vegetarian"], allergens=["wheat", "eggs", "milk"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Sausage Biscuit", 
                    description="Biscuit with sausage patty", 
                    category="Breakfast", price=4.49, calories=350, 
                    allergens=["wheat", "soy"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Breakfast Burrito", 
                    description="Eggs, cheese, meat, and veggies in a flour tortilla", 
                    category="Breakfast", price=6.99, calories=610, 
                    allergens=["wheat", "eggs", "milk"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Biscuits & Gravy", 
                    description="Biscuits smothered in sausage gravy", 
                    category="Breakfast", price=4.99, calories=320, 
                    allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Hash Browns", 
                    description="Crispy golden hash browns", 
                    category="Breakfast", price=2.99, calories=163, 
                    dietary_tags=["vegan"], is_available=True),
            
            # LUNCH
            MenuItem(location_id=ktc_cafe.id, name="Cheeseburger", 
                    description="Classic cheeseburger with lettuce, tomato, pickle", 
                    category="Lunch", price=5.99, calories=350, 
                    allergens=["wheat", "milk"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Chicken Tenders", 
                    description="Crispy chicken tenders with dipping sauce", 
                    category="Lunch", price=6.99, calories=350, 
                    allergens=["wheat"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Daily Special", 
                    description="Ask staff for today's hot lunch special", 
                    category="Lunch", price=7.99, calories=350, is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Chips", 
                    description="Bag of chips", 
                    category="Snacks", price=2.00, is_available=True),
            
            # DRINKS
            MenuItem(location_id=ktc_cafe.id, name="Fountain Drink", 
                    description="Soft drink (Coke, Pepsi, Sprite, etc.)", 
                    category="Snacks", price=2.79, is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Bottled Water", 
                    description="Cold bottled water", 
                    category="Snacks", price=2.19, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Bottled Juice", 
                    description="Assorted juice flavors", 
                    category="Snacks", price=2.99, dietary_tags=["vegetarian"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Bottled Iced Coffee", 
                    description="Cold brew or iced coffee", 
                    category="Snacks", price=4.99, is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Monster Energy", 
                    description="Energy drink", 
                    category="Snacks", price=3.99, is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Bottled Iced Tea", 
                    description="Sweet or unsweet tea", 
                    category="Snacks", price=2.99, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Powerade", 
                    description="Sports drink", 
                    category="Snacks", price=2.79, dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Milk", 
                    description="2% or chocolate milk", 
                    category="Snacks", price=3.49, allergens=["milk"], is_available=True),
            MenuItem(location_id=ktc_cafe.id, name="Coffee", 
                    description="Fresh brewed hot coffee", 
                    category="Snacks", price=2.19, dietary_tags=["vegan"], is_available=True),
        ]
        
        for item in ktc_items:
            db.session.add(item)
        
        # =============================================================================
        # AXE GRIND (STARBUCKS) MENU ITEMS
        # =============================================================================
        print("☕ Adding Axe Grind (Starbucks) menu items...")
        
        starbucks_items = [
            # HOT ESPRESSO DRINKS (Grande size)
            MenuItem(location_id=axe_grind.id, name="Caffe Latte (Grande)", 
                    description="Espresso with steamed milk", 
                    category="Snacks", price=4.85, calories=190, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Cappuccino (Grande)", 
                    description="Espresso with foam", 
                    category="Snacks", price=4.85, calories=140, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Caramel Macchiato (Grande)", 
                    description="Espresso with vanilla, steamed milk, and caramel drizzle", 
                    category="Snacks", price=5.75, calories=250, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Cafe Mocha (Grande)", 
                    description="Espresso with chocolate and steamed milk", 
                    category="Snacks", price=5.25, calories=370, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="White Chocolate Mocha (Grande)", 
                    description="Espresso with white chocolate and steamed milk", 
                    category="Snacks", price=5.75, calories=430, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Cafe Americano (Grande)", 
                    description="Espresso shots with hot water", 
                    category="Snacks", price=3.95, calories=15, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Matcha Latte (Grande)", 
                    description="Premium matcha green tea with steamed milk", 
                    category="Snacks", price=4.95, calories=240, 
                    allergens=["milk"], is_available=True),
            
            # HOT DRINKS
            MenuItem(location_id=axe_grind.id, name="Fresh Brewed Coffee (Grande)", 
                    description="Pike Place roast coffee", 
                    category="Snacks", price=2.95, calories=5, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Chai Tea Latte (Grande)", 
                    description="Spiced chai tea with steamed milk", 
                    category="Snacks", price=4.95, calories=240, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Hot Tea (Grande)", 
                    description="Selection of Teavana teas", 
                    category="Snacks", price=3.45, calories=0, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Hot Chocolate (Grande)", 
                    description="Rich hot chocolate with steamed milk", 
                    category="Snacks", price=4.45, calories=370, 
                    allergens=["milk"], is_available=True),
            
            # COLD DRINKS
            MenuItem(location_id=axe_grind.id, name="Iced Coffee (Grande)", 
                    description="Refreshing iced coffee", 
                    category="Snacks", price=3.95, calories=5, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Cold Brew (Grande)", 
                    description="Smooth, bold cold brew coffee", 
                    category="Snacks", price=4.95, calories=5, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Nitro Cold Brew (Grande)", 
                    description="Cold brew infused with nitrogen", 
                    category="Snacks", price=5.45, calories=5, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Shaken Iced Tea (Grande)", 
                    description="Refreshing shaken iced tea", 
                    category="Snacks", price=3.95, dietary_tags=["vegan"], is_available=True),
            
            # REFRESHERS
            MenuItem(location_id=axe_grind.id, name="Strawberry Acai Refresher (Grande)", 
                    description="Sweet strawberry flavors with acai", 
                    category="Snacks", price=4.95, calories=90, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Strawberry Acai Lemonade (Grande)", 
                    description="Strawberry Acai with lemonade", 
                    category="Snacks", price=5.25, calories=200, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Mango Dragon Fruit Refresher (Grande)", 
                    description="Tropical mango and dragonfruit flavors", 
                    category="Snacks", price=4.95, calories=130, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Pink Drink (Grande)", 
                    description="Strawberry Acai with coconut milk", 
                    category="Snacks", price=5.25, calories=140, 
                    dietary_tags=["vegan"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Dragon Drink (Grande)", 
                    description="Mango Dragonfruit with coconut milk", 
                    category="Snacks", price=5.25, calories=130, 
                    dietary_tags=["vegan"], is_available=True),
            
            # FRAPPUCCINOS
            MenuItem(location_id=axe_grind.id, name="Coffee Frappuccino (Grande)", 
                    description="Blended coffee with ice", 
                    category="Snacks", price=5.45, calories=230, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Caramel Frappuccino (Grande)", 
                    description="Blended coffee with caramel", 
                    category="Snacks", price=5.65, calories=370, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Mocha Frappuccino (Grande)", 
                    description="Blended coffee with chocolate", 
                    category="Snacks", price=5.65, calories=410, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Vanilla Bean Frappuccino (Grande)", 
                    description="Creamy vanilla blended creme", 
                    category="Snacks", price=5.45, calories=380, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Strawberries & Creme Frappuccino (Grande)", 
                    description="Strawberry blended creme", 
                    category="Snacks", price=5.65, calories=370, 
                    allergens=["milk"], is_available=True),
            MenuItem(location_id=axe_grind.id, name="Matcha Green Tea Frappuccino (Grande)", 
                    description="Matcha blended with milk and ice", 
                    category="Snacks", price=5.65, calories=410, 
                    allergens=["milk"], is_available=True),
        ]
        
        for item in starbucks_items:
            db.session.add(item)
        
        db.session.commit()
        
        # Calculate totals
        total_items = (len(gibson_items) + len(gc_items) + len(uc_items) + 
                      len(ktc_items) + len(starbucks_items))
        
        print(f"\n✅ Successfully added {total_items} menu items!")
        print(f"   - Gibson Dining Hall: {len(gibson_items)} items")
        print(f"   - Gorilla Crossing: {len(gc_items)} items")
        print(f"   - University Club: {len(uc_items)} items")
        print(f"   - KTC Cafe: {len(ktc_items)} items")
        print(f"   - Axe Grind (Starbucks): {len(starbucks_items)} items")
        
        print("\n🎉 Complete PSU dining data seeding finished!")
        print("\n📍 Locations created:")
        print("1. Gibson Dining Hall (All-you-care-to-eat, meal plan swipes)")
        print("2. Gorilla Crossing (Food court, Dining Dollars only)")
        print("   - Overman Burger Company")
        print("   - Pitt BBQ")
        print("   - Sub Stand")
        print("   - Pizza Hut")
        print("3. The University Club (Einstein Bros & Chilaca)")
        print("4. KTC Cafe (Kansas Technology Center)")
        print("5. Axe Grind (Starbucks in Axe Library)")

if __name__ == "__main__":
    seed_complete_dining_data()
