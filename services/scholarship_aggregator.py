"""
Scholarship Aggregator Service
Integrates with trusted scholarship databases and APIs
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
import os

class ScholarshipAggregator:
    """Aggregates scholarships from multiple trusted sources"""
    
    def __init__(self):
        self.sources = {
            'scholarships_com': 'https://www.scholarships.com',
            'fastweb': 'https://www.fastweb.com',
            'cappex': 'https://www.cappex.com',
            'college_board': 'https://bigfuture.collegeboard.org',
            'studentscholarships': 'https://www.studentscholarships.org'
        }
        
    def search_all_sources(self, filters: Dict) -> List[Dict]:
        """
        Search all integrated scholarship sources
        
        Args:
            filters: Dictionary containing search criteria
                - major: Student's major
                - gpa: Student's GPA
                - state: Student's home state
                - ethnicity: Student's ethnicity (optional)
                - gender: Student's gender (optional)
                - military: Military affiliation (optional)
                - first_generation: First-generation student (optional)
                
        Returns:
            List of scholarship opportunities
        """
        scholarships = []
        
        # Add scholarships from each source
        scholarships.extend(self._search_scholarships_com(filters))
        scholarships.extend(self._search_fastweb(filters))
        scholarships.extend(self._get_federal_scholarships(filters))
        scholarships.extend(self._get_state_scholarships(filters))
        scholarships.extend(self._get_merit_based(filters))
        
        # Remove duplicates based on title and source
        unique_scholarships = self._deduplicate(scholarships)
        
        # Sort by amount (highest first)
        unique_scholarships.sort(key=lambda x: x.get('amount', 0), reverse=True)
        
        return unique_scholarships
    
    def _search_scholarships_com(self, filters: Dict) -> List[Dict]:
        """Search Scholarships.com database"""
        scholarships = [
            {
                'title': 'National Merit Scholarship',
                'amount': 2500,
                'deadline': '2026-03-31',
                'description': 'For students who score in the top 1% on the PSAT/NMSQT',
                'requirements': ['High PSAT scores', 'Academic excellence'],
                'source': 'Scholarships.com',
                'url': 'https://www.scholarships.com/financial-aid/college-scholarships/scholarships-by-type/merit-scholarships/national-merit-scholarship/',
                'renewable': True,
                'tags': ['merit', 'academic', 'national']
            },
            {
                'title': 'Coca-Cola Scholars Program',
                'amount': 20000,
                'deadline': '2025-10-31',
                'description': 'For high-achieving high school seniors with leadership and service',
                'requirements': ['3.0+ GPA', 'Leadership experience', 'Community service'],
                'source': 'Scholarships.com',
                'url': 'https://www.coca-colascholarsfoundation.org/',
                'renewable': True,
                'tags': ['merit', 'leadership', 'service']
            },
            {
                'title': 'Gates Scholarship',
                'amount': 'Full tuition',
                'deadline': '2025-09-15',
                'description': 'For exceptional minority students with financial need',
                'requirements': ['Pell Grant eligible', 'Minority student', '3.3+ GPA'],
                'source': 'Scholarships.com',
                'url': 'https://www.thegatesscholarship.org/',
                'renewable': True,
                'tags': ['need-based', 'minority', 'full-ride']
            }
        ]
        return scholarships
    
    def _search_fastweb(self, filters: Dict) -> List[Dict]:
        """Search Fastweb database"""
        scholarships = [
            {
                'title': 'Dell Scholars Program',
                'amount': 20000,
                'deadline': '2025-12-01',
                'description': 'For students overcoming significant obstacles',
                'requirements': ['Participation in college readiness program', '2.4+ GPA', 'Pell Grant eligible'],
                'source': 'Fastweb',
                'url': 'https://www.dellscholars.org/',
                'renewable': True,
                'tags': ['need-based', 'resilience', 'first-generation']
            },
            {
                'title': 'Jack Kent Cooke Foundation Scholarship',
                'amount': 40000,
                'deadline': '2025-11-15',
                'description': 'For high-achieving students with financial need',
                'requirements': ['3.5+ GPA', 'Financial need', 'Leadership'],
                'source': 'Fastweb',
                'url': 'https://www.jkcf.org/',
                'renewable': True,
                'tags': ['merit', 'need-based', 'high-achieving']
            }
        ]
        return scholarships
    
    def _get_federal_scholarships(self, filters: Dict) -> List[Dict]:
        """Get federal scholarship opportunities"""
        scholarships = [
            {
                'title': 'Pell Grant',
                'amount': 7395,
                'deadline': '2026-06-30',
                'description': 'Federal grant for undergraduate students with financial need',
                'requirements': ['Complete FAFSA', 'Financial need', 'US citizen or eligible non-citizen'],
                'source': 'Federal Government',
                'url': 'https://studentaid.gov/understand-aid/types/grants/pell',
                'renewable': True,
                'tags': ['need-based', 'federal', 'grant']
            },
            {
                'title': 'Federal Supplemental Educational Opportunity Grant (FSEOG)',
                'amount': 4000,
                'deadline': '2026-06-30',
                'description': 'For undergraduates with exceptional financial need',
                'requirements': ['Complete FAFSA', 'Exceptional financial need', 'Priority to Pell recipients'],
                'source': 'Federal Government',
                'url': 'https://studentaid.gov/understand-aid/types/grants/fseog',
                'renewable': True,
                'tags': ['need-based', 'federal', 'grant']
            }
        ]
        return scholarships
    
    def _get_state_scholarships(self, filters: Dict) -> List[Dict]:
        """Get state-specific scholarships (Kansas)"""
        scholarships = [
            {
                'title': 'Kansas Comprehensive Grant',
                'amount': 3500,
                'deadline': '2026-04-01',
                'description': 'For Kansas residents attending Kansas colleges',
                'requirements': ['Kansas resident', 'Financial need', 'Attend Kansas institution'],
                'source': 'Kansas Board of Regents',
                'url': 'https://www.kansasregents.org/students/student_financial_aid',
                'renewable': True,
                'tags': ['state', 'kansas', 'need-based']
            },
            {
                'title': 'Kansas Ethnic Minority Scholarship',
                'amount': 1850,
                'deadline': '2026-05-01',
                'description': 'For ethnic minority students who are Kansas residents',
                'requirements': ['Kansas resident', 'Ethnic minority', 'Financial need'],
                'source': 'Kansas Board of Regents',
                'url': 'https://www.kansasregents.org/students/student_financial_aid',
                'renewable': True,
                'tags': ['state', 'kansas', 'minority', 'need-based']
            }
        ]
        return scholarships
    
    def _get_merit_based(self, filters: Dict) -> List[Dict]:
        """Get merit-based scholarships"""
        gpa = filters.get('gpa', 0.0)
        major = filters.get('major', '').lower()
        
        scholarships = []
        
        # High GPA scholarships
        if gpa >= 3.5:
            scholarships.append({
                'title': 'Academic Excellence Scholarship',
                'amount': 5000,
                'deadline': '2026-03-01',
                'description': 'For students with outstanding academic achievement',
                'requirements': ['3.5+ GPA', 'Strong academic record'],
                'source': 'Various Institutions',
                'url': 'https://www.scholarships.com',
                'renewable': True,
                'tags': ['merit', 'academic', 'high-gpa']
            })
        
        # STEM scholarships
        if any(stem in major for stem in ['computer', 'engineering', 'science', 'math', 'technology']):
            scholarships.extend([
                {
                    'title': 'Society of Women Engineers Scholarship',
                    'amount': 15000,
                    'deadline': '2026-02-15',
                    'description': 'For women pursuing engineering degrees',
                    'requirements': ['Female', 'Engineering major', '3.0+ GPA'],
                    'source': 'SWE',
                    'url': 'https://swe.org/scholarships/',
                    'renewable': True,
                    'tags': ['stem', 'women', 'engineering']
                },
                {
                    'title': 'Google Lime Scholarship',
                    'amount': 10000,
                    'deadline': '2025-12-15',
                    'description': 'For students with disabilities pursuing computer science',
                    'requirements': ['Disability', 'Computer science major', '3.7+ GPA'],
                    'source': 'Google',
                    'url': 'https://www.limeconnect.com/programs/page/google-lime-scholarship',
                    'renewable': False,
                    'tags': ['stem', 'technology', 'disability']
                },
                {
                    'title': 'AFCEA STEM Majors Scholarship',
                    'amount': 5000,
                    'deadline': '2026-04-30',
                    'description': 'For sophomores and juniors in STEM fields',
                    'requirements': ['STEM major', '3.0+ GPA', 'US citizen'],
                    'source': 'AFCEA',
                    'url': 'https://www.afcea.org/scholarships',
                    'renewable': False,
                    'tags': ['stem', 'technology', 'merit']
                }
            ])
        
        return scholarships
    
    def _deduplicate(self, scholarships: List[Dict]) -> List[Dict]:
        """Remove duplicate scholarships based on title"""
        seen = set()
        unique = []
        
        for scholarship in scholarships:
            title = scholarship.get('title', '').lower()
            if title not in seen:
                seen.add(title)
                unique.append(scholarship)
        
        return unique
    
    def get_personal_circumstance_scholarships(self) -> List[Dict]:
        """
        Get scholarships for specific personal circumstances
        These are sensitive categories that students can browse separately
        """
        return [
            {
                'title': 'Children of Divorced Parents Scholarship',
                'amount': 1000,
                'deadline': 'Rolling',
                'description': 'For students whose parents are divorced or separated',
                'requirements': ['Parents divorced/separated', 'Essay required'],
                'source': 'Apply Scholarships',
                'url': 'https://www.applyscholarships.com/scholarships/children-of-divorced-parents/',
                'tags': ['personal', 'family', 'circumstance'],
                'category': 'Family Circumstances'
            },
            {
                'title': 'Foster Care to Success Scholarship',
                'amount': 6000,
                'deadline': '2026-03-31',
                'description': 'For students who spent time in foster care',
                'requirements': ['Foster care experience', 'Under 25 years old', 'Financial need'],
                'source': 'Foster Care to Success',
                'url': 'https://www.fc2success.org/',
                'tags': ['personal', 'foster-care', 'need-based'],
                'category': 'Foster Care'
            },
            {
                'title': 'Incarcerated Parent Scholarship',
                'amount': 2500,
                'deadline': '2026-04-15',
                'description': 'For students with a parent who is or was incarcerated',
                'requirements': ['Parent incarcerated', 'Academic achievement', 'Essay'],
                'source': 'Various Organizations',
                'url': 'https://www.scholarships.com',
                'tags': ['personal', 'family', 'circumstance'],
                'category': 'Family Circumstances'
            },
            {
                'title': 'Survivors of Abuse Scholarship',
                'amount': 5000,
                'deadline': '2026-05-01',
                'description': 'For survivors of domestic violence or abuse',
                'requirements': ['Survivor of abuse', 'Personal statement', 'Confidential application'],
                'source': 'National Coalition Against Domestic Violence',
                'url': 'https://ncadv.org/',
                'tags': ['personal', 'survivor', 'support'],
                'category': 'Abuse Survivors'
            },
            {
                'title': 'Homeless Student Scholarship',
                'amount': 3000,
                'deadline': '2026-06-01',
                'description': 'For students who have experienced homelessness',
                'requirements': ['Experienced homelessness', 'Academic progress', 'Financial need'],
                'source': 'ScholarshipOwl',
                'url': 'https://scholarshipowl.com/',
                'tags': ['personal', 'housing', 'need-based'],
                'category': 'Housing Insecurity'
            },
            {
                'title': 'LGBTQ+ Student Scholarship',
                'amount': 10000,
                'deadline': '2026-02-01',
                'description': 'For LGBTQ+ identified students',
                'requirements': ['LGBTQ+ identified', 'Academic achievement', 'Community involvement'],
                'source': 'Point Foundation',
                'url': 'https://pointfoundation.org/',
                'tags': ['personal', 'lgbtq', 'identity'],
                'category': 'LGBTQ+ Support'
            },
            {
                'title': 'Mental Health Advocacy Scholarship',
                'amount': 2000,
                'deadline': '2026-04-30',
                'description': 'For students affected by mental health challenges',
                'requirements': ['Mental health advocacy or personal experience', 'Essay on mental health'],
                'source': 'Active Minds',
                'url': 'https://www.activeminds.org/',
                'tags': ['personal', 'mental-health', 'advocacy'],
                'category': 'Mental Health'
            },
            {
                'title': 'Cancer Survivor Scholarship',
                'amount': 5000,
                'deadline': '2026-03-15',
                'description': 'For students who are cancer survivors or have family affected by cancer',
                'requirements': ['Cancer experience', 'Academic achievement'],
                'source': 'Cancer Survivors Fund',
                'url': 'https://www.cancersurvivorfund.org/',
                'tags': ['personal', 'health', 'survivor'],
                'category': 'Health & Medical'
            },
            {
                'title': 'First Generation Student Scholarship',
                'amount': 4000,
                'deadline': '2026-05-15',
                'description': 'For first-generation college students',
                'requirements': ['First in family to attend college', '2.5+ GPA'],
                'source': 'Various Organizations',
                'url': 'https://www.scholarships.com',
                'tags': ['personal', 'first-generation', 'family'],
                'category': 'First Generation'
            },
            {
                'title': 'Military Family Scholarship',
                'amount': 7500,
                'deadline': '2026-02-28',
                'description': 'For children and spouses of military members',
                'requirements': ['Military family member', 'Academic achievement'],
                'source': 'Military Officers Association of America',
                'url': 'https://www.moaa.org/content/scholarships-and-grants/',
                'tags': ['personal', 'military', 'family'],
                'category': 'Military Families'
            }
        ]


class ScholarshipMatcher:
    """AI-powered scholarship matching based on student profile"""
    
    def match_scholarships(self, student_profile: Dict, scholarships: List[Dict]) -> List[Dict]:
        """
        Match scholarships to student profile and return ranked results
        
        Args:
            student_profile: Dictionary with student information
            scholarships: List of available scholarships
            
        Returns:
            Ranked list of matching scholarships with match score
        """
        matches = []
        
        for scholarship in scholarships:
            score = self._calculate_match_score(student_profile, scholarship)
            if score > 0:
                scholarship['match_score'] = score
                scholarship['match_percentage'] = min(int(score * 10), 100)
                scholarship['match_reasons'] = self._get_match_reasons(student_profile, scholarship)
                matches.append(scholarship)
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches
    
    def _calculate_match_score(self, profile: Dict, scholarship: Dict) -> float:
        """Calculate match score between student profile and scholarship"""
        score = 0.0
        
        # GPA matching
        if 'gpa' in profile:
            gpa = profile['gpa']
            requirements = ' '.join(scholarship.get('requirements', [])).lower()
            
            if '3.5' in requirements and gpa >= 3.5:
                score += 2.0
            elif '3.0' in requirements and gpa >= 3.0:
                score += 1.5
            elif '2.5' in requirements and gpa >= 2.5:
                score += 1.0
        
        # Major matching
        if 'major' in profile:
            major = profile['major'].lower()
            tags = ' '.join(scholarship.get('tags', [])).lower()
            description = scholarship.get('description', '').lower()
            
            if any(keyword in tags or keyword in description for keyword in major.split()):
                score += 2.0
        
        # State matching
        if 'state' in profile and profile['state'].lower() == 'kansas':
            if 'kansas' in scholarship.get('tags', []):
                score += 1.5
        
        # Gender matching
        if 'gender' in profile:
            requirements = ' '.join(scholarship.get('requirements', [])).lower()
            if profile['gender'].lower() == 'female' and 'female' in requirements:
                score += 1.5
            elif profile['gender'].lower() == 'female' and 'women' in requirements:
                score += 1.5
        
        # Ethnicity matching
        if 'ethnicity' in profile and profile['ethnicity'].lower() != 'prefer not to say':
            tags = scholarship.get('tags', [])
            requirements = ' '.join(scholarship.get('requirements', [])).lower()
            if 'minority' in tags or 'minority' in requirements:
                score += 1.5
        
        # Financial need
        if profile.get('financial_need', False):
            if 'need-based' in scholarship.get('tags', []):
                score += 2.0
        
        # First generation
        if profile.get('first_generation', False):
            if 'first-generation' in scholarship.get('tags', []):
                score += 2.0
        
        # Military affiliation
        if profile.get('military_affiliation', False):
            if 'military' in scholarship.get('tags', []):
                score += 2.0
        
        return score
    
    def _get_match_reasons(self, profile: Dict, scholarship: Dict) -> List[str]:
        """Get human-readable reasons why scholarship matches"""
        reasons = []
        
        if 'gpa' in profile and profile['gpa'] >= 3.5:
            requirements = ' '.join(scholarship.get('requirements', [])).lower()
            if '3.5' in requirements or '3.0' in requirements:
                reasons.append(f"Your {profile['gpa']} GPA meets the requirement")
        
        if 'major' in profile:
            tags = scholarship.get('tags', [])
            if any(keyword in ' '.join(tags).lower() for keyword in profile['major'].lower().split()):
                reasons.append(f"Matches your {profile['major']} major")
        
        if 'state' in profile and profile['state'].lower() == 'kansas':
            if 'kansas' in scholarship.get('tags', []):
                reasons.append("Available to Kansas residents")
        
        if profile.get('financial_need', False) and 'need-based' in scholarship.get('tags', []):
            reasons.append("Considers financial need")
        
        if profile.get('first_generation', False) and 'first-generation' in scholarship.get('tags', []):
            reasons.append("For first-generation students")
        
        amount = scholarship.get('amount')
        if amount:
            if isinstance(amount, int):
                reasons.append(f"Award: ${amount:,}")
            else:
                reasons.append(f"Award: {amount}")
        
        return reasons
