"""
Bureau of Labor Statistics (BLS) API Integration
Fetches real career and salary data for Gorilla-Link Career Intelligence
"""

import requests
import os
from datetime import datetime
from typing import Dict, Optional, List

BLS_API_KEY = os.getenv('BLS_API_KEY')
BLS_BASE_URL = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'

# Common occupation codes for PSU majors
OCCUPATION_CODES = {
    'Software Developer': '151252',
    'Web Developer': '151254',
    'Management Analyst': '131111',
    'Registered Nurse': '291141',
    'Elementary Teacher': '252021',
    'Secondary Teacher': '252031',
    'Accountant': '132011',
    'Financial Analyst': '132051',
    'Marketing Manager': '112021',
    'HR Manager': '113121',
    'Mechanical Engineer': '172141',
    'Civil Engineer': '172051',
    'Data Scientist': '152098',
    'Business Analyst': '131199',
    'Physical Therapist': '291123',
}


def fetch_occupation_data(series_id: str, start_year: int, end_year: int) -> Dict:
    """
    Fetch BLS data for specific occupation
    
    Args:
        series_id: BLS series ID (e.g., 'OEUM000000151252' for Software Developers)
        start_year: Start year for data
        end_year: End year for data
    
    Returns:
        Dict with BLS API response
    """
    
    headers = {'Content-type': 'application/json'}
    data = {
        'seriesid': [series_id],
        'startyear': str(start_year),
        'endyear': str(end_year),
    }
    
    # Add API key if available
    if BLS_API_KEY:
        data['registrationkey'] = BLS_API_KEY
    
    try:
        response = requests.post(BLS_BASE_URL, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"BLS API error: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching BLS data: {e}")
        return None


def get_median_salary(occupation_code: str) -> Optional[float]:
    """
    Get median salary for occupation
    
    Args:
        occupation_code: BLS occupation code (e.g., '151252' for Software Developer)
    
    Returns:
        Median annual salary or None if unavailable
    """
    current_year = datetime.now().year
    
    # BLS series ID format: OEUM000000[occupation_code]
    series_id = f'OEUM000000{occupation_code}'
    
    data = fetch_occupation_data(series_id, current_year - 1, current_year)
    
    if not data:
        return None
    
    # Parse most recent salary
    try:
        series = data['Results']['series'][0]
        latest = series['data'][0]
        # BLS returns annual wages in dollars
        return float(latest['value'])
    except (KeyError, IndexError, ValueError) as e:
        print(f"Error parsing BLS salary data: {e}")
        return None


def get_occupation_data(occupation_title: str) -> Optional[Dict]:
    """
    Get comprehensive data for occupation
    
    Args:
        occupation_title: Occupation title (e.g., 'Software Developer')
    
    Returns:
        Dict with salary, employment, and outlook data
    """
    
    if occupation_title not in OCCUPATION_CODES:
        print(f"Occupation '{occupation_title}' not found in OCCUPATION_CODES")
        return None
    
    occupation_code = OCCUPATION_CODES[occupation_title]
    salary = get_median_salary(occupation_code)
    
    if not salary:
        return None
    
    # Return structured data
    return {
        'occupation_title': occupation_title,
        'occupation_code': occupation_code,
        'national_median_salary': salary,
        'data_source': 'Bureau of Labor Statistics (BLS)',
        'last_updated': datetime.utcnow()
    }


def get_all_occupation_data() -> List[Dict]:
    """
    Get data for all tracked occupations
    
    Returns:
        List of occupation data dicts
    """
    
    results = []
    
    for occupation_title in OCCUPATION_CODES.keys():
        print(f"Fetching data for {occupation_title}...")
        
        data = get_occupation_data(occupation_title)
        
        if data:
            results.append(data)
        else:
            print(f"  ⚠ Could not fetch data for {occupation_title}")
    
    return results


def check_api_status() -> bool:
    """
    Check if BLS API is accessible
    
    Returns:
        True if API is accessible, False otherwise
    """
    
    try:
        # Test with a simple request
        current_year = datetime.now().year
        data = fetch_occupation_data('OEUM000000151252', current_year, current_year)
        return data is not None
    
    except Exception as e:
        print(f"BLS API check failed: {e}")
        return False


# Example usage
if __name__ == '__main__':
    print("BLS API Integration Test")
    print("=" * 50)
    
    # Check API status
    if BLS_API_KEY:
        print(f"✓ BLS API Key found: {BLS_API_KEY[:8]}...")
    else:
        print("⚠ BLS API Key not found in environment")
        print("  Get free key at: https://data.bls.gov/registrationEngine/")
    
    print("\nChecking API accessibility...")
    if check_api_status():
        print("✓ BLS API is accessible")
    else:
        print("✗ BLS API is not accessible")
    
    # Fetch sample data
    print("\nFetching sample occupation data...")
    
    software_dev_data = get_occupation_data('Software Developer')
    
    if software_dev_data:
        print(f"\n✓ Software Developer Data:")
        print(f"  Median Salary: ${software_dev_data['national_median_salary']:,.0f}")
        print(f"  Source: {software_dev_data['data_source']}")
        print(f"  Updated: {software_dev_data['last_updated']}")
    else:
        print("\n✗ Could not fetch Software Developer data")
        print("  Using cached data from seed script")
