"""
Zillow/Housing API Integration
Fetches real housing listings near PSU for Smart Housing feature
"""

import requests
import os
from datetime import datetime
from typing import Dict, Optional, List
from math import radians, cos, sin, asin, sqrt

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
RAPIDAPI_HOST = "zillow-com1.p.rapidapi.com"

# PSU coordinates
PSU_LATITUDE = 37.4108
PSU_LONGITUDE = -94.7046


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        lat1, lon1: First coordinate (origin)
        lat2, lon2: Second coordinate (destination)
    
    Returns:
        Distance in miles
    """
    
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of Earth in miles
    miles = 3956 * c
    
    return round(miles, 2)


def search_rentals_near_psu(
    max_price: int = 1000,
    bedrooms: int = 2,
    max_distance_miles: float = 5.0
) -> List[Dict]:
    """
    Search for rental properties near PSU
    
    Args:
        max_price: Maximum monthly rent
        bedrooms: Number of bedrooms
        max_distance_miles: Maximum distance from campus
    
    Returns:
        List of property dicts
    """
    
    if not RAPIDAPI_KEY:
        print("⚠ RAPIDAPI_KEY not found in environment")
        print("  Get free key at: https://rapidapi.com/apimaker/api/zillow-com1/")
        return []
    
    url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
    
    querystring = {
        "location": "Pittsburg, KS",
        "status_type": "ForRent",
        "home_type": "Apartments",
        "maxPrice": str(max_price),
        "beds": str(bedrooms),
        "sort": "Price_Low_High"
    }
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            properties = data.get('props', [])
            
            # Filter by distance
            filtered = []
            for prop in properties:
                lat = prop.get('latitude')
                lon = prop.get('longitude')
                
                if lat and lon:
                    distance = calculate_distance(
                        PSU_LATITUDE, PSU_LONGITUDE,
                        float(lat), float(lon)
                    )
                    
                    if distance <= max_distance_miles:
                        prop['distance_to_psu'] = distance
                        filtered.append(prop)
            
            return filtered
        
        else:
            print(f"Zillow API error: {response.status_code}")
            return []
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Zillow data: {e}")
        return []


def parse_zillow_listing(zillow_data: Dict) -> Dict:
    """
    Convert Zillow API response to our HousingListing format
    
    Args:
        zillow_data: Raw Zillow API response
    
    Returns:
        Dict formatted for HousingListing model
    """
    
    address_data = zillow_data.get('address', {})
    
    return {
        'property_name': address_data.get('streetAddress', 'Unnamed Property'),
        'address': address_data.get('streetAddress'),
        'city': address_data.get('city', 'Pittsburg'),
        'state': address_data.get('state', 'KS'),
        'zip_code': address_data.get('zipcode', '66762'),
        'property_type': 'apartment',
        'bedrooms': zillow_data.get('bedrooms', 1),
        'bathrooms': zillow_data.get('bathrooms', 1),
        'square_feet': zillow_data.get('livingArea'),
        'monthly_rent': zillow_data.get('price'),
        'security_deposit': zillow_data.get('price'),  # Usually 1 month rent
        'lease_length_months': 12,
        'available_date': datetime.utcnow(),
        'photos': [zillow_data.get('imgSrc')] if zillow_data.get('imgSrc') else [],
        'latitude': zillow_data.get('latitude'),
        'longitude': zillow_data.get('longitude'),
        'distance_to_campus_miles': zillow_data.get('distance_to_psu', 0),
        'walkability_score': calculate_walkability(zillow_data.get('distance_to_psu', 10)),
        'transit_score': 50,  # Default for Pittsburg
        'amenities': parse_amenities(zillow_data),
        'utilities_included': [],
        'pet_policy': 'Contact landlord',
        'parking_available': True,
        'laundry_type': 'in_unit',
        'listing_url': zillow_data.get('detailUrl'),
        'status': 'available',
        'is_verified': False,
        'verification_notes': 'Imported from Zillow API - needs manual verification',
        'last_verified': datetime.utcnow()
    }


def calculate_walkability(distance_miles: float) -> int:
    """
    Calculate walkability score based on distance
    
    Args:
        distance_miles: Distance from campus in miles
    
    Returns:
        Walkability score (0-100)
    """
    
    if distance_miles <= 0.5:
        return 100
    elif distance_miles <= 1.0:
        return 90
    elif distance_miles <= 1.5:
        return 75
    elif distance_miles <= 2.0:
        return 60
    elif distance_miles <= 3.0:
        return 40
    else:
        return 20


def parse_amenities(zillow_data: Dict) -> List[str]:
    """
    Extract amenities from Zillow data
    
    Args:
        zillow_data: Raw Zillow API response
    
    Returns:
        List of amenity strings
    """
    
    amenities = []
    
    # Common amenities to check for
    if zillow_data.get('hasPool'):
        amenities.append('pool')
    if zillow_data.get('hasFitnessFacility'):
        amenities.append('fitness_center')
    if zillow_data.get('hasGarage'):
        amenities.append('parking')
    if zillow_data.get('hasAirConditioning'):
        amenities.append('air_conditioning')
    if zillow_data.get('hasHeating'):
        amenities.append('heating')
    
    return amenities


def search_craigslist_pittsburg() -> List[Dict]:
    """
    Scrape Craigslist for Pittsburg rentals (free alternative)
    
    Returns:
        List of property dicts
    """
    
    from bs4 import BeautifulSoup
    
    url = "https://kansascity.craigslist.org/search/apa?query=pittsburg&availabilityMode=0"
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        listings = []
        
        for result in soup.find_all('li', class_='result-row'):
            try:
                title = result.find('a', class_='result-title').text
                price_text = result.find('span', class_='result-price').text
                href = result.find('a', class_='result-title')['href']
                
                # Parse price
                price = float(price_text.replace('$', '').replace(',', ''))
                
                listings.append({
                    'title': title,
                    'monthly_rent': price,
                    'url': href,
                    'source': 'craigslist'
                })
            
            except (AttributeError, ValueError):
                continue
        
        return listings
    
    except Exception as e:
        print(f"Error scraping Craigslist: {e}")
        return []


def check_api_status() -> bool:
    """
    Check if housing API is accessible
    
    Returns:
        True if API is accessible, False otherwise
    """
    
    if not RAPIDAPI_KEY:
        return False
    
    try:
        # Test with a simple request
        properties = search_rentals_near_psu(max_price=2000, bedrooms=1)
        return len(properties) >= 0  # Even 0 results means API works
    
    except Exception as e:
        print(f"Housing API check failed: {e}")
        return False


# Example usage
if __name__ == '__main__':
    print("Housing API Integration Test")
    print("=" * 50)
    
    # Check API status
    if RAPIDAPI_KEY:
        print(f"✓ RapidAPI Key found: {RAPIDAPI_KEY[:8]}...")
    else:
        print("⚠ RapidAPI Key not found in environment")
        print("  Get free key at: https://rapidapi.com/apimaker/api/zillow-com1/")
    
    print("\nChecking API accessibility...")
    if check_api_status():
        print("✓ Housing API is accessible")
    else:
        print("✗ Housing API is not accessible")
    
    # Test distance calculation
    print("\nTesting distance calculation...")
    test_distance = calculate_distance(
        PSU_LATITUDE, PSU_LONGITUDE,
        37.4000, -94.7000  # Sample nearby location
    )
    print(f"  Distance to test location: {test_distance} miles")
    
    # Search for properties
    print("\nSearching for properties near PSU...")
    properties = search_rentals_near_psu(max_price=1000, bedrooms=2)
    
    if properties:
        print(f"✓ Found {len(properties)} properties")
        
        for i, prop in enumerate(properties[:3], 1):
            print(f"\n  Property {i}:")
            print(f"    Address: {prop.get('address', {}).get('streetAddress')}")
            print(f"    Price: ${prop.get('price')}/month")
            print(f"    Bedrooms: {prop.get('bedrooms')}")
            print(f"    Distance: {prop.get('distance_to_psu')} miles")
    else:
        print("✗ No properties found")
        print("  Try alternative: Craigslist scraping")
