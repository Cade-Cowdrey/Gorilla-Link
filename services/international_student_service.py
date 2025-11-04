"""
International Student Hub Service
Comprehensive visa resources, sponsorship database, and immigration support for international students

Features:
- F-1, OPT, CPT, H-1B visa resources and guidance
- Company sponsorship database (H-1B willing employers)
- Immigration attorney directory with ratings
- Document checklists and timeline calculators
- STEM extension tracking and OPT day counter
- Visa status notifications and deadline alerts
- International student community and peer support
- Cultural adjustment resources and events
- Tax guidance (1040NR-EZ, treaty benefits)
- Country-specific resources and embassy contacts

Revenue Model:
- Premium attorney consultations: $150-500/session
- Sponsored company listings: $2,000-5,000/year
- Document review service: $100-300/review
- Premium resource access: $20/month subscription
- Webinar series: $50-200/event
- Partnership revenue: Universities, law firms, relocation services
Target: $300,000+ annually
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy import and_, or_, func
from models import db, User, Job, Company, Experience

logger = logging.getLogger(__name__)


class InternationalStudentService:
    """Service for international student visa and immigration support"""
    
    # Visa types and their details
    VISA_TYPES = {
        'F-1': {
            'name': 'F-1 Student Visa',
            'description': 'Academic student visa for full-time study at US universities',
            'duration': 'Duration of academic program + 60 days',
            'work_authorization': 'On-campus (20 hrs/week), CPT, OPT',
            'requirements': [
                'Full-time enrollment (minimum 12 credits)',
                'Maintain SEVIS status',
                'Valid passport',
                'I-20 from university',
                'Proof of financial support'
            ],
            'restrictions': [
                'Cannot work off-campus without authorization',
                'Must maintain full-time enrollment',
                'Limited travel restrictions (need travel signature)',
                'Cannot stay more than 60 days after program completion without OPT/new status'
            ]
        },
        'OPT': {
            'name': 'Optional Practical Training',
            'description': 'Work authorization for F-1 students (12 months, 24-month STEM extension)',
            'duration': '12 months (36 months total with STEM extension)',
            'work_authorization': 'Full-time employment in field of study',
            'requirements': [
                'Completed 1 academic year on F-1',
                'Apply before program completion or within 60-day grace period',
                'Job must be related to degree field',
                'Cannot be unemployed more than 90 days (150 for STEM)'
            ],
            'application_timeline': '90 days before graduation to 60 days after'
        },
        'CPT': {
            'name': 'Curricular Practical Training',
            'description': 'Work authorization for internships/co-ops as part of curriculum',
            'duration': 'Per semester/academic year',
            'work_authorization': 'Part-time or full-time during studies',
            'requirements': [
                'Completed 1 academic year (waived for graduate students)',
                'Job must be required or integral to curriculum',
                'Must receive academic credit or be part of program',
                'Authorization from DSO required'
            ],
            'restrictions': [
                '12+ months of full-time CPT makes you ineligible for OPT',
                'Must be directly related to major'
            ]
        },
        'H-1B': {
            'name': 'H-1B Specialty Occupation Visa',
            'description': 'Work visa for specialized positions requiring bachelor\'s degree or higher',
            'duration': '3 years (extendable to 6 years)',
            'work_authorization': 'Full-time employment with sponsoring employer',
            'requirements': [
                'Bachelor\'s degree or higher in specialized field',
                'Job offer from US employer willing to sponsor',
                'Employer files petition with USCIS',
                'Position must require specialized knowledge',
                'Prevailing wage requirements'
            ],
            'lottery': {
                'regular_cap': 65000,
                'masters_cap': 20000,
                'filing_period': 'March 1-17 (typical)',
                'lottery_odds': '~14-26% (varies by year)'
            }
        },
        'H-1B_CAP_EXEMPT': {
            'name': 'H-1B Cap-Exempt',
            'description': 'H-1B positions not subject to annual lottery cap',
            'employers': [
                'Universities and affiliated research institutions',
                'Nonprofit research organizations',
                'Government research organizations'
            ],
            'advantages': [
                'No lottery required',
                'Can file any time of year',
                'Higher approval odds'
            ]
        },
        'O-1': {
            'name': 'O-1 Extraordinary Ability Visa',
            'description': 'Visa for individuals with extraordinary ability in sciences, arts, education, business, or athletics',
            'duration': '3 years (extendable)',
            'requirements': [
                'Sustained national or international acclaim',
                'Recognition for achievements',
                'Evidence: awards, publications, media coverage, high salary',
                'Agent or employer petition required'
            ]
        }
    }
    
    # STEM OPT eligible CIP codes (sample - expand with full list)
    STEM_CIP_CODES = {
        '11': 'Computer and Information Sciences',
        '14': 'Engineering',
        '15': 'Engineering Technologies',
        '26': 'Biological and Biomedical Sciences',
        '27': 'Mathematics and Statistics',
        '30': 'Multi/Interdisciplinary Studies (certain programs)',
        '40': 'Physical Sciences',
        '41': 'Science Technologies'
    }

    def __init__(self):
        """Initialize the international student service"""
        self.logger = logger
    
    def get_visa_guidance(self, visa_type: str, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive visa guidance for specific type
        
        Args:
            visa_type: Type of visa (F-1, OPT, CPT, H-1B, etc.)
            user_id: User requesting guidance
        
        Returns:
            Detailed visa information and personalized guidance
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            visa_info = self.VISA_TYPES.get(visa_type)
            if not visa_info:
                return {'success': False, 'error': 'Invalid visa type'}
            
            # Get user's current status and education
            current_status = user.profile.get('visa_status') if user.profile else None
            major = user.profile.get('major') if user.profile else None
            graduation_date = user.profile.get('graduation_date') if user.profile else None
            
            # Generate personalized timeline
            timeline = self._generate_visa_timeline(visa_type, current_status, graduation_date)
            
            # Get relevant next steps
            next_steps = self._get_next_steps(visa_type, current_status, user)
            
            # Check STEM eligibility if relevant
            stem_eligible = False
            if visa_type in ['OPT', 'H-1B'] and major:
                stem_eligible = self._check_stem_eligibility(major)
            
            # Get relevant resources
            resources = self._get_visa_resources(visa_type)
            
            return {
                'success': True,
                'visa_info': visa_info,
                'personalized': {
                    'current_status': current_status,
                    'timeline': timeline,
                    'next_steps': next_steps,
                    'stem_eligible': stem_eligible,
                    'days_until_graduation': self._calculate_days_until(graduation_date) if graduation_date else None
                },
                'resources': resources,
                'faqs': self._get_visa_faqs(visa_type),
                'common_mistakes': self._get_common_mistakes(visa_type)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting visa guidance: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_opt_days(self, user_id: int, opt_start_date: str, employment_gaps: List[Dict] = None) -> Dict[str, Any]:
        """
        Calculate remaining OPT days and unemployment days
        
        Args:
            user_id: User ID
            opt_start_date: OPT start date (YYYY-MM-DD)
            employment_gaps: List of unemployment periods [{'start': date, 'end': date}]
        
        Returns:
            OPT day calculations and alerts
        """
        try:
            start = datetime.strptime(opt_start_date, '%Y-%m-%d')
            today = datetime.now()
            
            # Calculate total OPT duration
            days_elapsed = (today - start).days
            standard_opt_days = 365
            
            user = User.query.get(user_id)
            is_stem = user.profile.get('is_stem_eligible', False) if user and user.profile else False
            
            total_opt_days = 1095 if is_stem else 365  # 36 months vs 12 months
            
            # Calculate unemployment days
            unemployment_days = 0
            if employment_gaps:
                for gap in employment_gaps:
                    gap_start = datetime.strptime(gap['start'], '%Y-%m-%d')
                    gap_end = datetime.strptime(gap['end'], '%Y-%m-%d') if gap.get('end') else today
                    unemployment_days += (gap_end - gap_start).days
            
            max_unemployment = 150 if is_stem else 90
            remaining_unemployment = max_unemployment - unemployment_days
            
            # Calculate remaining OPT days
            opt_end_date = start + timedelta(days=total_opt_days)
            remaining_opt_days = (opt_end_date - today).days
            
            # Generate alerts
            alerts = []
            if unemployment_days > max_unemployment * 0.7:
                alerts.append({
                    'level': 'warning',
                    'message': f'You have used {unemployment_days} of {max_unemployment} allowed unemployment days'
                })
            
            if unemployment_days >= max_unemployment:
                alerts.append({
                    'level': 'critical',
                    'message': 'URGENT: You have exceeded maximum unemployment days. Your SEVIS status may be terminated.'
                })
            
            if remaining_opt_days < 90 and remaining_opt_days > 0:
                alerts.append({
                    'level': 'warning',
                    'message': f'Your OPT expires in {remaining_opt_days} days. Consider H-1B or other status options.'
                })
            
            return {
                'success': True,
                'opt_start': opt_start_date,
                'opt_end': opt_end_date.strftime('%Y-%m-%d'),
                'days_elapsed': days_elapsed,
                'remaining_days': remaining_opt_days,
                'unemployment_days_used': unemployment_days,
                'unemployment_days_remaining': remaining_unemployment,
                'max_unemployment_days': max_unemployment,
                'is_stem': is_stem,
                'percentage_complete': round((days_elapsed / total_opt_days) * 100, 1),
                'alerts': alerts,
                'recommendations': self._get_opt_recommendations(remaining_opt_days, unemployment_days, is_stem)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating OPT days: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def search_h1b_sponsors(self, filters: Dict[str, Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search database of H-1B sponsoring companies
        
        Args:
            filters: Search filters (industry, location, job_title, company_size, approval_rate)
            page: Page number
            per_page: Results per page
        
        Returns:
            List of companies willing to sponsor H-1B visas
        """
        try:
            # Build query
            query = Company.query.filter(Company.sponsors_visas == True)
            
            # Apply filters
            if filters.get('industry'):
                query = query.filter(Company.industry == filters['industry'])
            
            if filters.get('location'):
                location = filters['location']
                query = query.filter(
                    or_(
                        Company.city.ilike(f'%{location}%'),
                        Company.state.ilike(f'%{location}%')
                    )
                )
            
            if filters.get('min_approval_rate'):
                # Filter by H-1B approval rate from company profile
                query = query.filter(
                    Company.h1b_approval_rate >= filters['min_approval_rate']
                )
            
            if filters.get('company_size'):
                size = filters['company_size']
                if size == 'small':
                    query = query.filter(Company.employee_count < 50)
                elif size == 'medium':
                    query = query.filter(and_(Company.employee_count >= 50, Company.employee_count < 500))
                elif size == 'large':
                    query = query.filter(Company.employee_count >= 500)
            
            # Get total count
            total = query.count()
            
            # Paginate
            companies = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Enrich with H-1B data
            results = []
            for company in companies:
                # Get H-1B statistics from historical data
                h1b_stats = self._get_company_h1b_stats(company.id)
                
                # Get current open positions
                open_positions = Job.query.filter(
                    and_(
                        Job.company_id == company.id,
                        Job.status == 'active',
                        Job.visa_sponsorship == True
                    )
                ).count()
                
                results.append({
                    'company_id': company.id,
                    'name': company.name,
                    'industry': company.industry,
                    'location': f"{company.city}, {company.state}",
                    'size': company.employee_count,
                    'website': company.website,
                    'description': company.description,
                    'h1b_stats': h1b_stats,
                    'open_visa_positions': open_positions,
                    'cap_exempt': company.is_cap_exempt,  # University/nonprofit
                    'sponsorship_notes': company.sponsorship_notes
                })
            
            return {
                'success': True,
                'companies': results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                },
                'filters_applied': filters,
                'tips': self._get_sponsorship_search_tips()
            }
            
        except Exception as e:
            self.logger.error(f"Error searching H-1B sponsors: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def find_immigration_attorneys(self, specialty: str = None, location: str = None, rating_min: float = 4.0) -> Dict[str, Any]:
        """
        Find immigration attorneys with ratings and specialties
        
        Args:
            specialty: Attorney specialty (H-1B, OPT, family-based, asylum, etc.)
            location: Location preference
            rating_min: Minimum rating filter
        
        Returns:
            List of immigration attorneys with contact info and ratings
        """
        try:
            # This would query an ImmigrationAttorney model
            # For now, return sample data structure
            attorneys = [
                {
                    'id': 1,
                    'name': 'Sarah Chen, Esq.',
                    'firm': 'Chen Immigration Law',
                    'bar_number': 'CA-123456',
                    'specialties': ['H-1B', 'OPT', 'PERM', 'Green Card'],
                    'location': 'San Francisco, CA',
                    'rating': 4.8,
                    'reviews_count': 156,
                    'languages': ['English', 'Mandarin', 'Cantonese'],
                    'consultation_fee': 150,
                    'free_initial_consultation': True,
                    'response_time': '< 24 hours',
                    'success_rate': 0.94,
                    'years_experience': 12,
                    'contact': {
                        'phone': '(415) 555-0100',
                        'email': 'contact@chenimmigration.com',
                        'website': 'https://chenimmigration.com'
                    },
                    'recent_reviews': [
                        {
                            'rating': 5,
                            'text': 'Excellent help with H-1B transfer. Very knowledgeable and responsive.',
                            'date': '2025-10-15',
                            'case_type': 'H-1B Transfer'
                        }
                    ]
                },
                {
                    'id': 2,
                    'name': 'Michael Rodriguez, Esq.',
                    'firm': 'Global Immigration Partners',
                    'bar_number': 'NY-789012',
                    'specialties': ['H-1B', 'L-1', 'O-1', 'EB-1'],
                    'location': 'New York, NY',
                    'rating': 4.9,
                    'reviews_count': 203,
                    'languages': ['English', 'Spanish'],
                    'consultation_fee': 200,
                    'free_initial_consultation': False,
                    'response_time': '< 48 hours',
                    'success_rate': 0.96,
                    'years_experience': 15,
                    'contact': {
                        'phone': '(212) 555-0200',
                        'email': 'info@globalimmigration.com',
                        'website': 'https://globalimmigration.com'
                    },
                    'recent_reviews': [
                        {
                            'rating': 5,
                            'text': 'Successfully handled my O-1 visa. Highly recommended for exceptional ability cases.',
                            'date': '2025-10-20',
                            'case_type': 'O-1 Visa'
                        }
                    ]
                }
            ]
            
            # Filter by specialty
            if specialty:
                attorneys = [a for a in attorneys if specialty in a['specialties']]
            
            # Filter by rating
            attorneys = [a for a in attorneys if a['rating'] >= rating_min]
            
            return {
                'success': True,
                'attorneys': attorneys,
                'total': len(attorneys),
                'filters': {
                    'specialty': specialty,
                    'location': location,
                    'min_rating': rating_min
                },
                'tips': [
                    'Always verify attorney bar membership before hiring',
                    'Ask about success rates for your specific visa type',
                    'Request fee estimates in writing',
                    'Check reviews from international students'
                ],
                'red_flags': [
                    'Guarantees of approval (no attorney can guarantee)',
                    'Extremely low fees (may indicate lack of experience)',
                    'Poor communication or responsiveness',
                    'Not licensed to practice immigration law'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error finding immigration attorneys: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_document_checklist(self, visa_type: str, current_step: str = 'initial') -> Dict[str, Any]:
        """
        Get document checklist for visa application
        
        Args:
            visa_type: Type of visa application
            current_step: Current step in process
        
        Returns:
            Comprehensive checklist with document requirements
        """
        try:
            checklists = {
                'F-1': {
                    'initial_application': [
                        {'doc': 'Valid passport', 'required': True, 'notes': 'Must be valid for at least 6 months beyond stay'},
                        {'doc': 'DS-160 confirmation', 'required': True, 'notes': 'Online nonimmigrant visa application'},
                        {'doc': 'I-20 from university', 'required': True, 'notes': 'Certificate of Eligibility'},
                        {'doc': 'SEVIS fee receipt', 'required': True, 'notes': 'Form I-901, $350'},
                        {'doc': 'Visa application fee receipt', 'required': True, 'notes': '$160 MRV fee'},
                        {'doc': 'Passport-style photo', 'required': True, 'notes': '2x2 inches, recent'},
                        {'doc': 'Financial documents', 'required': True, 'notes': 'Bank statements, sponsor letters, scholarships'},
                        {'doc': 'Academic transcripts', 'required': True, 'notes': 'Previous degrees and grades'},
                        {'doc': 'Test scores', 'required': True, 'notes': 'TOEFL, IELTS, GRE, GMAT as applicable'},
                        {'doc': 'Proof of ties to home country', 'required': False, 'notes': 'Property, family, job offer'}
                    ],
                    'maintaining_status': [
                        {'doc': 'Full-time enrollment verification', 'required': True, 'notes': 'Minimum 12 credits'},
                        {'doc': 'I-20 with travel signature', 'required': True, 'notes': 'Valid for 12 months for re-entry'},
                        {'doc': 'Current passport', 'required': True, 'notes': 'Valid F-1 visa stamp'},
                        {'doc': 'Proof of financial support', 'required': True, 'notes': 'For each semester'}
                    ]
                },
                'OPT': {
                    'application': [
                        {'doc': 'I-765 form', 'required': True, 'notes': 'Application for Employment Authorization'},
                        {'doc': 'Copy of I-20 with OPT recommendation', 'required': True, 'notes': 'Endorsed by DSO'},
                        {'doc': 'Copy of I-94', 'required': True, 'notes': 'Arrival/departure record'},
                        {'doc': 'Copy of F-1 visa', 'required': True, 'notes': 'Both sides'},
                        {'doc': 'Copy of passport bio page', 'required': True, 'notes': 'Clear, readable'},
                        {'doc': 'Two passport photos', 'required': True, 'notes': '2x2 inches'},
                        {'doc': 'Filing fee', 'required': True, 'notes': '$410 check/money order'},
                        {'doc': 'Copy of EAD (if extending)', 'required': False, 'notes': 'For STEM extension only'},
                        {'doc': 'I-983 Training Plan', 'required': False, 'notes': 'For STEM extension only'},
                        {'doc': 'STEM degree proof', 'required': False, 'notes': 'For STEM extension only'}
                    ]
                },
                'H-1B': {
                    'employer_petition': [
                        {'doc': 'Form I-129', 'required': True, 'notes': 'Petition filed by employer'},
                        {'doc': 'LCA (Labor Condition Application)', 'required': True, 'notes': 'DOL certified, ETA-9035'},
                        {'doc': 'Degree certificates', 'required': True, 'notes': 'Bachelor\'s or higher'},
                        {'doc': 'Transcripts', 'required': True, 'notes': 'Official university transcripts'},
                        {'doc': 'Resume/CV', 'required': True, 'notes': 'Detailed work history'},
                        {'doc': 'Job offer letter', 'required': True, 'notes': 'Position, salary, duties'},
                        {'doc': 'Company documents', 'required': True, 'notes': 'Business license, tax returns, org chart'},
                        {'doc': 'Evaluation (if needed)', 'required': False, 'notes': 'For foreign degrees'},
                        {'doc': 'Prevailing wage determination', 'required': True, 'notes': 'From DOL'}
                    ],
                    'employee_documents': [
                        {'doc': 'Valid passport', 'required': True, 'notes': 'Valid for duration of stay'},
                        {'doc': 'DS-160', 'required': True, 'notes': 'If applying from outside US'},
                        {'doc': 'I-797 Approval Notice', 'required': True, 'notes': 'From USCIS'},
                        {'doc': 'Visa fee receipt', 'required': True, 'notes': 'If applying for visa stamp'}
                    ]
                }
            }
            
            checklist = checklists.get(visa_type, {}).get(current_step, [])
            
            if not checklist:
                return {'success': False, 'error': 'No checklist found for this combination'}
            
            # Calculate completion stats
            required_docs = len([d for d in checklist if d['required']])
            optional_docs = len([d for d in checklist if not d['required']])
            
            return {
                'success': True,
                'visa_type': visa_type,
                'step': current_step,
                'checklist': checklist,
                'stats': {
                    'required_documents': required_docs,
                    'optional_documents': optional_docs,
                    'total_documents': len(checklist)
                },
                'tips': [
                    'Make copies of all documents before mailing',
                    'Use certified mail with tracking',
                    'Keep digital backups of everything',
                    'Organize documents in the order listed on instructions'
                ],
                'common_errors': [
                    'Unsigned forms',
                    'Missing passport photos',
                    'Incorrect filing fee',
                    'Expired documents'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting document checklist: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_h1b_timeline(self, filing_date: str = None, is_cap_exempt: bool = False) -> Dict[str, Any]:
        """
        Calculate H-1B timeline including lottery, processing, and start date
        
        Args:
            filing_date: Expected filing date (defaults to next April 1)
            is_cap_exempt: Whether position is cap-exempt (university, nonprofit research)
        
        Returns:
            Detailed timeline with key dates and milestones
        """
        try:
            today = datetime.now()
            
            if is_cap_exempt:
                # Cap-exempt can file anytime
                if filing_date:
                    file_date = datetime.strptime(filing_date, '%Y-%m-%d')
                else:
                    file_date = today + timedelta(days=30)  # Assume 30 days to prepare
                
                # Standard processing: 2-4 months
                # Premium processing: 15 calendar days
                approval_date_standard = file_date + timedelta(days=90)
                approval_date_premium = file_date + timedelta(days=15)
                start_date = approval_date_premium + timedelta(days=7)  # Can start immediately after approval
                
                timeline = [
                    {'date': file_date.strftime('%Y-%m-%d'), 'event': 'File H-1B Petition', 'description': 'Employer submits I-129 to USCIS'},
                    {'date': approval_date_premium.strftime('%Y-%m-%d'), 'event': 'Expected Approval (Premium)', 'description': '15 calendar days with premium processing'},
                    {'date': approval_date_standard.strftime('%Y-%m-%d'), 'event': 'Expected Approval (Standard)', 'description': '2-4 months standard processing'},
                    {'date': start_date.strftime('%Y-%m-%d'), 'event': 'Can Start Work', 'description': 'Begin H-1B employment'}
                ]
                
                return {
                    'success': True,
                    'cap_exempt': True,
                    'timeline': timeline,
                    'advantages': [
                        'No lottery required',
                        'Can file year-round',
                        'Faster processing available',
                        'Can start work immediately upon approval'
                    ],
                    'premium_processing': {
                        'available': True,
                        'fee': 2500,
                        'processing_time': '15 calendar days'
                    }
                }
            
            # Cap-subject H-1B (standard lottery process)
            current_year = today.year
            next_filing_year = current_year if today.month < 3 else current_year + 1
            
            # Key dates for cap-subject H-1B
            registration_open = datetime(next_filing_year, 3, 1)
            registration_close = datetime(next_filing_year, 3, 17, 12, 0)  # Noon ET
            lottery_results = datetime(next_filing_year, 3, 31)
            filing_window_start = datetime(next_filing_year, 4, 1)
            filing_window_end = datetime(next_filing_year, 6, 30)
            earliest_start_date = datetime(next_filing_year, 10, 1)
            
            # Processing times (estimates)
            approval_date = filing_window_start + timedelta(days=120)  # 4 months average
            
            timeline = [
                {
                    'date': registration_open.strftime('%Y-%m-%d'),
                    'event': 'H-1B Registration Opens',
                    'description': 'Employers register for lottery (online)',
                    'action': 'Employer must register on USCIS website'
                },
                {
                    'date': registration_close.strftime('%Y-%m-%d %H:%M ET'),
                    'event': 'Registration Deadline',
                    'description': 'Last day to register for lottery',
                    'action': 'CRITICAL DEADLINE - miss this and wait another year'
                },
                {
                    'date': lottery_results.strftime('%Y-%m-%d'),
                    'event': 'Lottery Results',
                    'description': 'Selected registrations notified',
                    'action': 'Check USCIS account for selection notice'
                },
                {
                    'date': filing_window_start.strftime('%Y-%m-%d'),
                    'event': 'Filing Window Opens',
                    'description': 'Selected petitions can be filed',
                    'action': 'Submit complete I-129 petition package'
                },
                {
                    'date': filing_window_end.strftime('%Y-%m-%d'),
                    'event': 'Filing Window Closes',
                    'description': 'Deadline to file selected petitions',
                    'action': 'Must file by this date if selected'
                },
                {
                    'date': approval_date.strftime('%Y-%m-%d'),
                    'event': 'Expected Approval',
                    'description': 'Estimated approval date (varies)',
                    'action': 'Receive I-797 approval notice'
                },
                {
                    'date': earliest_start_date.strftime('%Y-%m-%d'),
                    'event': 'H-1B Start Date',
                    'description': 'Earliest you can begin H-1B employment',
                    'action': 'Can start work in H-1B status'
                }
            ]
            
            # Calculate lottery odds (approximate, varies by year)
            lottery_stats = {
                'regular_cap': 65000,
                'advanced_degree_cap': 20000,
                'typical_registrations': 500000,
                'estimated_odds_bachelors': 0.14,  # ~14%
                'estimated_odds_masters': 0.26  # ~26% (two chances: masters + regular)
            }
            
            return {
                'success': True,
                'cap_exempt': False,
                'filing_year': next_filing_year,
                'timeline': timeline,
                'lottery_stats': lottery_stats,
                'important_notes': [
                    'Registration fee: $10 (non-refundable)',
                    'Only selected registrations can file petitions',
                    'Premium processing: $2,500 (15 days)',
                    'Total costs typically $5,000-10,000 (employer pays)',
                    'Start date is always October 1, even if approved earlier'
                ],
                'strategies': [
                    'Apply with employer who has high success rate',
                    'Consider cap-exempt positions (universities)',
                    'Have backup plans (O-1, L-1, etc.)',
                    'If on OPT, apply for STEM extension as backup',
                    'Consider master\'s degree for better odds'
                ],
                'days_until_registration': (registration_open - today).days if registration_open > today else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating H-1B timeline: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_country_specific_resources(self, country: str) -> Dict[str, Any]:
        """
        Get country-specific resources, embassy info, and community
        
        Args:
            country: Country of origin
        
        Returns:
            Country-specific visa resources and community info
        """
        try:
            # Sample country-specific data
            country_data = {
                'india': {
                    'embassy': {
                        'name': 'Embassy of India, Washington DC',
                        'address': '2107 Massachusetts Ave NW, Washington, DC 20008',
                        'phone': '+1 (202) 939-7000',
                        'website': 'https://www.indianembassyusa.gov.in',
                        'consulates': [
                            {'city': 'New York', 'jurisdiction': 'NY, NJ, CT, PA'},
                            {'city': 'San Francisco', 'jurisdiction': 'Northern CA, NV'},
                            {'city': 'Chicago', 'jurisdiction': 'IL, IN, WI, MI, OH'},
                            {'city': 'Houston', 'jurisdiction': 'TX, LA, OK, AR'}
                        ]
                    },
                    'tax_treaty': {
                        'available': True,
                        'student_exemption': '$9,000 per year for 5 years',
                        'researcher_exemption': '$9,000 per year for 2 years',
                        'form': 'W-8BEN (claim treaty benefits)'
                    },
                    'common_challenges': [
                        'Administrative processing delays for visa stamping',
                        'Long wait times for visa appointments in India',
                        'F-1 visa renewal challenges',
                        'H-1B lottery odds'
                    ],
                    'community': {
                        'student_organizations': ['Indian Students Association', 'Hindu Students Council'],
                        'professional_networks': ['The Indus Entrepreneurs (TiE)', 'NetIP'],
                        'cultural_events': ['Diwali celebrations', 'Holi festivals', 'India Independence Day']
                    }
                },
                'china': {
                    'embassy': {
                        'name': 'Embassy of China, Washington DC',
                        'address': '3505 International Place NW, Washington, DC 20008',
                        'phone': '+1 (202) 495-2266',
                        'website': 'http://www.china-embassy.org'
                    },
                    'tax_treaty': {
                        'available': True,
                        'student_exemption': 'Full exemption for 5 years',
                        'form': 'Form 8833 treaty disclosure'
                    },
                    'common_challenges': [
                        'Technology Alert List (TAL) processing for STEM fields',
                        'Administrative processing (6-12 weeks common)',
                        'Difficulty returning home for visa renewal',
                        'WeChat pay/banking restrictions'
                    ]
                }
                # Add more countries as needed
            }
            
            country_lower = country.lower()
            country_info = country_data.get(country_lower)
            
            if not country_info:
                return {
                    'success': False,
                    'error': 'Country data not available yet',
                    'message': 'We are continuously expanding our country-specific resources'
                }
            
            return {
                'success': True,
                'country': country,
                'embassy_info': country_info.get('embassy'),
                'tax_treaty': country_info.get('tax_treaty'),
                'common_challenges': country_info.get('common_challenges', []),
                'community': country_info.get('community', {}),
                'helpful_links': [
                    {'title': 'US Embassy in ' + country, 'url': f'https://www.usembassy.gov'},
                    {'title': 'USCIS International Offices', 'url': 'https://www.uscis.gov/about-us/find-a-uscis-office/international-immigration-offices'}
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting country resources: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_visa_timeline(self, visa_type: str, current_status: str, graduation_date: str) -> List[Dict]:
        """Generate personalized visa timeline based on current status"""
        timeline = []
        
        if visa_type == 'OPT' and graduation_date:
            grad = datetime.strptime(graduation_date, '%Y-%m-%d')
            timeline = [
                {'date': (grad - timedelta(days=90)).strftime('%Y-%m-%d'), 'event': 'Earliest OPT application date', 'status': 'upcoming'},
                {'date': grad.strftime('%Y-%m-%d'), 'event': 'Graduation', 'status': 'milestone'},
                {'date': (grad + timedelta(days=60)).strftime('%Y-%m-%d'), 'event': 'Latest OPT application date', 'status': 'deadline'}
            ]
        
        return timeline
    
    def _get_next_steps(self, visa_type: str, current_status: str, user: User) -> List[str]:
        """Get personalized next steps based on visa type and current status"""
        steps = {
            'F-1': [
                'Maintain full-time enrollment (minimum 12 credits)',
                'Keep SEVIS record up to date',
                'Get travel signature every 12 months',
                'Plan for CPT or OPT before graduation'
            ],
            'OPT': [
                'Apply 90 days before graduation (earliest)',
                'Get OPT recommendation from DSO',
                'Submit I-765 form with all required documents',
                'Track application status online',
                'Start job search immediately'
            ],
            'H-1B': [
                'Find employer willing to sponsor',
                'Ensure job qualifies as specialty occupation',
                'Register for H-1B lottery (March 1-17)',
                'Prepare all required documents',
                'Consider premium processing ($2,500)'
            ]
        }
        
        return steps.get(visa_type, ['Consult with international student office'])
    
    def _check_stem_eligibility(self, major: str) -> bool:
        """Check if major is STEM-eligible for OPT extension"""
        # Check CIP code prefix
        for code_prefix, description in self.STEM_CIP_CODES.items():
            if code_prefix in major or description.lower() in major.lower():
                return True
        return False
    
    def _get_visa_resources(self, visa_type: str) -> List[Dict]:
        """Get relevant resources for visa type"""
        resources = {
            'F-1': [
                {'title': 'USCIS F-1 Students', 'url': 'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/students-and-employment'},
                {'title': 'Study in the States', 'url': 'https://studyinthestates.dhs.gov/students'},
                {'title': 'SEVP Portal', 'url': 'https://www.ice.gov/sevis'}
            ],
            'OPT': [
                {'title': 'OPT Overview', 'url': 'https://www.uscis.gov/opt'},
                {'title': 'STEM OPT Extension', 'url': 'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students'},
                {'title': 'STEM Designated Degree Program List', 'url': 'https://www.ice.gov/sevis/stemlist'}
            ],
            'H-1B': [
                {'title': 'H-1B Specialty Occupations', 'url': 'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations'},
                {'title': 'H-1B Registration Process', 'url': 'https://www.uscis.gov/h-1b'},
                {'title': 'DOL Wage Determinations', 'url': 'https://www.dol.gov/agencies/eta/foreign-labor'}
            ]
        }
        
        return resources.get(visa_type, [])
    
    def _get_visa_faqs(self, visa_type: str) -> List[Dict]:
        """Get frequently asked questions for visa type"""
        faqs = {
            'F-1': [
                {'q': 'Can I work on campus with F-1 visa?', 'a': 'Yes, up to 20 hours/week during semester, full-time during breaks'},
                {'q': 'How long can I stay after graduation?', 'a': '60 days grace period, or longer with OPT approval'},
                {'q': 'Can I transfer to another university?', 'a': 'Yes, through SEVIS transfer process with new I-20'}
            ],
            'H-1B': [
                {'q': 'What are my chances in the lottery?', 'a': 'Approximately 14-26% depending on education level'},
                {'q': 'Can I work while H-1B is pending?', 'a': 'Yes, if you have valid work authorization (e.g., OPT, Cap-Gap extension)'},
                {'q': 'What happens if I don\'t get selected?', 'a': 'You can try again next year, or explore alternatives like O-1, L-1'}
            ]
        }
        
        return faqs.get(visa_type, [])
    
    def _get_common_mistakes(self, visa_type: str) -> List[str]:
        """Get common mistakes to avoid for visa type"""
        mistakes = {
            'OPT': [
                'Applying too late (miss the 60-day deadline)',
                'Not getting DSO recommendation first',
                'Forgetting to report employment to school',
                'Exceeding unemployment days',
                'Working before receiving EAD card'
            ],
            'H-1B': [
                'Missing registration deadline (no second chance)',
                'Not verifying employer is legitimate',
                'Accepting positions that don\'t qualify as specialty occupation',
                'Forgetting to file extension before expiration',
                'Changing jobs without H-1B transfer'
            ]
        }
        
        return mistakes.get(visa_type, [])
    
    def _calculate_days_until(self, date_str: str) -> int:
        """Calculate days until a specific date"""
        if not date_str:
            return None
        target = datetime.strptime(date_str, '%Y-%m-%d')
        return (target - datetime.now()).days
    
    def _get_opt_recommendations(self, remaining_days: int, unemployment_days: int, is_stem: bool) -> List[str]:
        """Get recommendations based on OPT status"""
        recommendations = []
        
        if remaining_days < 180 and not is_stem:
            recommendations.append('Apply for H-1B in next registration period')
            recommendations.append('Consider STEM extension if your degree qualifies')
        
        if unemployment_days > 60:
            recommendations.append('Actively apply to jobs - unemployment days are limited')
        
        if remaining_days < 90:
            recommendations.append('Consult immigration attorney about status options')
        
        return recommendations
    
    def _get_company_h1b_stats(self, company_id: int) -> Dict[str, Any]:
        """Get H-1B statistics for a company"""
        # This would query historical H-1B data
        # For now, return sample structure
        return {
            'total_applications_2024': 120,
            'approvals_2024': 102,
            'approval_rate': 0.85,
            'average_salary': 95000,
            'most_common_positions': ['Software Engineer', 'Data Analyst', 'Business Analyst'],
            'has_filed_in_last_year': True
        }
    
    def _get_sponsorship_search_tips(self) -> List[str]:
        """Get tips for searching H-1B sponsors"""
        return [
            'Universities and research institutions are cap-exempt',
            'Larger companies have higher sponsorship budgets',
            'Tech companies sponsor most H-1B visas',
            'Check company reviews on H1BGrader.com',
            'Apply early - companies plan sponsorship budgets in advance',
            'Network with current H-1B employees at target companies'
        ]


# Example usage and testing
if __name__ == '__main__':
    service = InternationalStudentService()
    
    # Test visa guidance
    print("Testing F-1 Visa Guidance:")
    result = service.get_visa_guidance('F-1', user_id=1)
    print(f"Success: {result['success']}")
    
    # Test OPT calculator
    print("\nTesting OPT Day Calculator:")
    opt_result = service.calculate_opt_days(
        user_id=1,
        opt_start_date='2024-06-01',
        employment_gaps=[{'start': '2024-07-01', 'end': '2024-07-15'}]
    )
    print(f"Remaining OPT days: {opt_result.get('remaining_days')}")
    
    # Test H-1B sponsor search
    print("\nTesting H-1B Sponsor Search:")
    sponsors = service.search_h1b_sponsors({'industry': 'Technology', 'location': 'San Francisco'})
    print(f"Found {len(sponsors.get('companies', []))} sponsoring companies")
    
    # Test H-1B timeline
    print("\nTesting H-1B Timeline Calculator:")
    timeline = service.calculate_h1b_timeline()
    print(f"Filing year: {timeline.get('filing_year')}")
    print(f"Days until registration: {timeline.get('days_until_registration')}")
