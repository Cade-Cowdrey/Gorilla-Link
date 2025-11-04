"""
PSU Connect - Salary Negotiation Calculator
Market rates, cost of living, negotiation scripts generator
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import openai
import os

salary_bp = Blueprint('salary_calculator', __name__, url_prefix='/tools/salary')

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Cost of living indices (relative to national average = 100)
COST_OF_LIVING = {
    'pittsburg_ks': 85,
    'kansas_city_mo': 95,
    'wichita_ks': 88,
    'topeka_ks': 87,
    'springfield_mo': 86,
    'tulsa_ok': 89,
    'joplin_mo': 84,
    'new_york_ny': 187,
    'san_francisco_ca': 192,
    'los_angeles_ca': 151,
    'chicago_il': 114,
    'austin_tx': 119,
    'dallas_tx': 101,
    'denver_co': 121,
    'seattle_wa': 145,
    'boston_ma': 148,
    'atlanta_ga': 99,
    'miami_fl': 108,
    'phoenix_az': 97,
    'national_average': 100
}

# Average salaries by field and experience (in thousands)
SALARY_DATA = {
    'software_engineering': {'entry': 65, 'mid': 95, 'senior': 135},
    'data_science': {'entry': 70, 'mid': 105, 'senior': 145},
    'business_analyst': {'entry': 55, 'mid': 75, 'senior': 95},
    'marketing': {'entry': 45, 'mid': 65, 'senior': 85},
    'accounting': {'entry': 50, 'mid': 68, 'senior': 85},
    'teaching': {'entry': 40, 'mid': 52, 'senior': 65},
    'nursing': {'entry': 60, 'mid': 75, 'senior': 90},
    'engineering': {'entry': 65, 'mid': 85, 'senior': 110},
    'sales': {'entry': 45, 'mid': 70, 'senior': 100},
    'project_management': {'entry': 60, 'mid': 85, 'senior': 115},
    'hr': {'entry': 48, 'mid': 65, 'senior': 85},
    'finance': {'entry': 58, 'mid': 80, 'senior': 120}
}


@salary_bp.route('/')
def calculator():
    """Main salary calculator page"""
    return render_template('tools/salary_calculator.html',
                         cities=COST_OF_LIVING,
                         fields=SALARY_DATA)


@salary_bp.route('/api/calculate', methods=['POST'])
def calculate_salary():
    """Calculate recommended salary based on inputs"""
    data = request.json
    
    job_title = data.get('job_title', '')
    field = data.get('field', '')
    experience_level = data.get('experience_level', 'entry')  # entry, mid, senior
    location = data.get('location', 'national_average')
    offer_amount = data.get('offer_amount', type=float)
    
    # Get base salary for field and experience
    base_salary = SALARY_DATA.get(field, {}).get(experience_level, 60)
    
    # Adjust for cost of living
    col_index = COST_OF_LIVING.get(location, 100)
    adjusted_salary = base_salary * (col_index / 100)
    
    # Calculate ranges
    low_range = adjusted_salary * 0.85
    high_range = adjusted_salary * 1.15
    target = adjusted_salary
    
    # Compare to offer
    comparison = None
    if offer_amount:
        diff_percent = ((offer_amount - target) / target) * 100
        
        if offer_amount < low_range:
            comparison = {
                'status': 'below',
                'message': f'This offer is {abs(diff_percent):.1f}% below market rate',
                'recommendation': 'Strong negotiation recommended'
            }
        elif offer_amount > high_range:
            comparison = {
                'status': 'above',
                'message': f'This offer is {diff_percent:.1f}% above market rate',
                'recommendation': 'Excellent offer!'
            }
        else:
            comparison = {
                'status': 'fair',
                'message': f'This offer is within market range ({diff_percent:+.1f}%)',
                'recommendation': 'Fair offer, minor negotiation possible'
            }
    
    return jsonify({
        'success': True,
        'base_salary': round(base_salary, 1),
        'adjusted_salary': round(adjusted_salary, 1),
        'low_range': round(low_range, 1),
        'high_range': round(high_range, 1),
        'target': round(target, 1),
        'col_index': col_index,
        'comparison': comparison
    })


@salary_bp.route('/api/total-compensation', methods=['POST'])
def calculate_total_compensation():
    """Calculate total compensation including benefits"""
    data = request.json
    
    base_salary = data.get('base_salary', type=float, default=0)
    bonus = data.get('bonus', type=float, default=0)
    stock = data.get('stock', type=float, default=0)
    health_insurance = data.get('health_insurance', type=float, default=0)
    retirement_match = data.get('retirement_match', type=float, default=0)
    pto_days = data.get('pto_days', type=int, default=0)
    other_benefits = data.get('other_benefits', type=float, default=0)
    
    # Calculate PTO value (daily rate * days)
    if base_salary and pto_days:
        daily_rate = base_salary / 260  # ~260 work days per year
        pto_value = daily_rate * pto_days
    else:
        pto_value = 0
    
    total = base_salary + bonus + stock + health_insurance + retirement_match + pto_value + other_benefits
    
    breakdown = {
        'base_salary': base_salary,
        'bonus': bonus,
        'stock': stock,
        'health_insurance': health_insurance,
        'retirement_match': retirement_match,
        'pto_value': round(pto_value, 2),
        'other_benefits': other_benefits,
        'total': round(total, 2)
    }
    
    return jsonify({
        'success': True,
        'breakdown': breakdown,
        'total': round(total, 2)
    })


@salary_bp.route('/api/negotiation-script', methods=['POST'])
@login_required
def generate_negotiation_script():
    """Generate AI negotiation script"""
    if not openai.api_key:
        return jsonify({
            'error': 'AI features not configured',
            'script': get_fallback_script()
        }), 500
    
    data = request.json
    
    job_title = data.get('job_title', '')
    offer_amount = data.get('offer_amount', type=float)
    target_amount = data.get('target_amount', type=float)
    strengths = data.get('strengths', '')
    
    try:
        prompt = f"""Generate a professional salary negotiation script.

Job Title: {job_title}
Current Offer: ${offer_amount:,.0f}
Target Salary: ${target_amount:,.0f}
Candidate Strengths: {strengths}

Write a professional, confident negotiation script (3-4 paragraphs) that:
1. Thanks them for the offer
2. Expresses enthusiasm for the role
3. Presents the counteroffer with market data justification
4. Highlights unique value and strengths
5. Remains positive and collaborative

Keep it concise and natural-sounding."""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a career negotiation expert. Write professional, confident negotiation scripts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        script = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'script': script
        })
    
    except Exception as e:
        print(f"Script generation error: {e}")
        return jsonify({
            'success': True,
            'script': get_fallback_script(job_title, offer_amount, target_amount)
        })


def get_fallback_script(job_title='', offer_amount=0, target_amount=0):
    """Fallback negotiation script if AI fails"""
    return f"""Thank you so much for the {job_title or 'position'} offer! I'm very excited about the opportunity to join your team and contribute to the company's success.

After reviewing the offer and considering my qualifications, experience, and the market rates for similar positions, I'd like to discuss the salary. Based on my research and the value I'll bring to the role, I believe a salary of ${target_amount:,.0f} would be more appropriate.

I'm confident that my skills and experience will allow me to make significant contributions from day one. I'm very enthusiastic about this role and believe this adjustment would reflect the value I'll bring to the team.

I'm flexible and open to discussion. What are your thoughts on this?"""


@salary_bp.route('/tips')
def negotiation_tips():
    """Negotiation tips and best practices"""
    tips = [
        {
            'title': 'Do Your Research',
            'description': 'Know the market rate for your role, experience level, and location before negotiating.',
            'icon': 'search'
        },
        {
            'title': 'Wait for the Right Moment',
            'description': 'Negotiate after receiving a written offer, not during interviews.',
            'icon': 'clock'
        },
        {
            'title': 'Consider Total Compensation',
            'description': 'Look beyond base salary - bonuses, stock, benefits, PTO, and flexible work matter.',
            'icon': 'list'
        },
        {
            'title': 'Be Specific with Numbers',
            'description': 'Use precise figures ($73,500) rather than round numbers ($70,000) to show research.',
            'icon': 'calculator'
        },
        {
            'title': 'Stay Positive',
            'description': 'Express enthusiasm for the role while negotiating. It\'s not adversarial.',
            'icon': 'smile'
        },
        {
            'title': 'Get it in Writing',
            'description': 'Once you reach agreement, get the final offer in writing before accepting.',
            'icon': 'file-contract'
        },
        {
            'title': 'Know Your Walk-Away Point',
            'description': 'Decide your minimum acceptable offer beforehand and stick to it.',
            'icon': 'door-open'
        },
        {
            'title': 'Practice Your Pitch',
            'description': 'Rehearse your negotiation conversation with a friend or mentor.',
            'icon': 'microphone'
        }
    ]
    
    return render_template('tools/negotiation_tips.html', tips=tips)


@salary_bp.route('/comparison')
def cost_of_living_comparison():
    """Compare cost of living between cities"""
    return render_template('tools/col_comparison.html',
                         cities=COST_OF_LIVING)


@salary_bp.route('/api/col-adjust', methods=['POST'])
def adjust_for_col():
    """Adjust salary for cost of living difference"""
    data = request.json
    
    current_salary = data.get('current_salary', type=float)
    from_city = data.get('from_city', 'national_average')
    to_city = data.get('to_city', 'national_average')
    
    from_index = COST_OF_LIVING.get(from_city, 100)
    to_index = COST_OF_LIVING.get(to_city, 100)
    
    adjusted_salary = current_salary * (to_index / from_index)
    difference = adjusted_salary - current_salary
    percent_change = (difference / current_salary) * 100
    
    return jsonify({
        'success': True,
        'adjusted_salary': round(adjusted_salary, 2),
        'difference': round(difference, 2),
        'percent_change': round(percent_change, 1),
        'from_index': from_index,
        'to_index': to_index
    })
