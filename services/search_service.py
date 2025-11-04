"""
Advanced Search Service for PittState Connect
Implements full-text search, faceted navigation, and saved searches
Uses PostgreSQL full-text search capabilities
"""

from extensions import db
from models import User, Job, Scholarship, Event, Post, Department, Faculty
from sqlalchemy import func, or_, and_, text
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced search functionality with filters and saved searches"""
    
    # Searchable entity types
    SEARCHABLE_TYPES = ['jobs', 'scholarships', 'events', 'users', 'posts', 'faculty']
    
    @staticmethod
    def universal_search(query, entity_types=None, filters=None, page=1, per_page=20, user_id=None):
        """
        Universal search across multiple entity types
        
        Args:
            query: Search query string
            entity_types: List of entity types to search (default: all)
            filters: Dict of filters to apply
            page: Page number for pagination
            per_page: Results per page
            user_id: Current user ID for personalization
            
        Returns:
            dict: Search results with metadata
        """
        if not query or len(query.strip()) < 2:
            return {
                'results': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'query': query,
                'entity_types': entity_types,
                'took_ms': 0
            }
        
        start_time = datetime.now()
        entity_types = entity_types or SearchService.SEARCHABLE_TYPES
        filters = filters or {}
        
        all_results = []
        total_count = 0
        
        # Search each entity type
        if 'jobs' in entity_types:
            job_results = SearchService._search_jobs(query, filters)
            all_results.extend([{'type': 'job', 'data': r} for r in job_results])
            total_count += len(job_results)
        
        if 'scholarships' in entity_types:
            scholarship_results = SearchService._search_scholarships(query, filters)
            all_results.extend([{'type': 'scholarship', 'data': r} for r in scholarship_results])
            total_count += len(scholarship_results)
        
        if 'events' in entity_types:
            event_results = SearchService._search_events(query, filters)
            all_results.extend([{'type': 'event', 'data': r} for r in event_results])
            total_count += len(event_results)
        
        if 'users' in entity_types:
            user_results = SearchService._search_users(query, filters)
            all_results.extend([{'type': 'user', 'data': r} for r in user_results])
            total_count += len(user_results)
        
        if 'posts' in entity_types:
            post_results = SearchService._search_posts(query, filters)
            all_results.extend([{'type': 'post', 'data': r} for r in post_results])
            total_count += len(post_results)
        
        if 'faculty' in entity_types:
            faculty_results = SearchService._search_faculty(query, filters)
            all_results.extend([{'type': 'faculty', 'data': r} for r in faculty_results])
            total_count += len(faculty_results)
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = all_results[start_idx:end_idx]
        
        took_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Record search analytics
        if user_id:
            SearchService._record_search(user_id, query, entity_types, total_count)
        
        return {
            'results': paginated_results,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'query': query,
            'entity_types': entity_types,
            'filters': filters,
            'took_ms': round(took_ms, 2)
        }
    
    @staticmethod
    def _search_jobs(query, filters):
        """Search jobs with full-text search"""
        try:
            # Base query with full-text search
            search_query = Job.query.filter(
                or_(
                    Job.title.ilike(f'%{query}%'),
                    Job.description.ilike(f'%{query}%'),
                    Job.company.ilike(f'%{query}%'),
                    Job.location.ilike(f'%{query}%')
                )
            )
            
            # Apply filters
            if filters.get('location'):
                search_query = search_query.filter(Job.location.ilike(f'%{filters["location"]}%'))
            
            if filters.get('job_type'):
                search_query = search_query.filter(Job.job_type == filters['job_type'])
            
            if filters.get('salary_min'):
                search_query = search_query.filter(Job.salary >= filters['salary_min'])
            
            if filters.get('remote_only'):
                search_query = search_query.filter(Job.is_remote == True)
            
            if filters.get('posted_within_days'):
                cutoff = datetime.now() - timedelta(days=filters['posted_within_days'])
                search_query = search_query.filter(Job.posted_date >= cutoff)
            
            # Order by relevance (could be enhanced with ts_rank)
            results = search_query.order_by(Job.posted_date.desc()).limit(50).all()
            
            return [SearchService._serialize_job(job) for job in results]
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return []
    
    @staticmethod
    def _search_scholarships(query, filters):
        """Search scholarships"""
        try:
            search_query = Scholarship.query.filter(
                or_(
                    Scholarship.name.ilike(f'%{query}%'),
                    Scholarship.description.ilike(f'%{query}%'),
                    Scholarship.eligibility.ilike(f'%{query}%')
                )
            )
            
            # Apply filters
            if filters.get('amount_min'):
                search_query = search_query.filter(Scholarship.amount >= filters['amount_min'])
            
            if filters.get('deadline_within_days'):
                cutoff = datetime.now() + timedelta(days=filters['deadline_within_days'])
                search_query = search_query.filter(Scholarship.deadline <= cutoff)
            
            if filters.get('department_id'):
                search_query = search_query.filter(Scholarship.department_id == filters['department_id'])
            
            results = search_query.order_by(Scholarship.deadline.asc()).limit(50).all()
            
            return [SearchService._serialize_scholarship(sch) for sch in results]
        except Exception as e:
            logger.error(f"Error searching scholarships: {str(e)}")
            return []
    
    @staticmethod
    def _search_events(query, filters):
        """Search events"""
        try:
            search_query = Event.query.filter(
                or_(
                    Event.title.ilike(f'%{query}%'),
                    Event.description.ilike(f'%{query}%'),
                    Event.location.ilike(f'%{query}%')
                )
            )
            
            # Apply filters
            if filters.get('event_type'):
                search_query = search_query.filter(Event.event_type == filters['event_type'])
            
            if filters.get('upcoming_only', True):
                search_query = search_query.filter(Event.start_time >= datetime.now())
            
            if filters.get('within_days'):
                cutoff = datetime.now() + timedelta(days=filters['within_days'])
                search_query = search_query.filter(Event.start_time <= cutoff)
            
            results = search_query.order_by(Event.start_time.asc()).limit(50).all()
            
            return [SearchService._serialize_event(event) for event in results]
        except Exception as e:
            logger.error(f"Error searching events: {str(e)}")
            return []
    
    @staticmethod
    def _search_users(query, filters):
        """Search users (students/alumni)"""
        try:
            search_query = User.query.filter(
                or_(
                    User.first_name.ilike(f'%{query}%'),
                    User.last_name.ilike(f'%{query}%'),
                    User.email.ilike(f'%{query}%'),
                    User.major.ilike(f'%{query}%'),
                    User.bio.ilike(f'%{query}%')
                )
            )
            
            # Apply filters
            if filters.get('role'):
                search_query = search_query.filter(User.role == filters['role'])
            
            if filters.get('graduation_year'):
                search_query = search_query.filter(User.graduation_year == filters['graduation_year'])
            
            if filters.get('major'):
                search_query = search_query.filter(User.major.ilike(f'%{filters["major"]}%'))
            
            # Only return verified/public profiles
            search_query = search_query.filter(User.is_verified == True)
            
            results = search_query.limit(50).all()
            
            return [SearchService._serialize_user(user) for user in results]
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []
    
    @staticmethod
    def _search_posts(query, filters):
        """Search posts"""
        try:
            search_query = Post.query.filter(
                Post.content.ilike(f'%{query}%')
            )
            
            # Apply filters
            if filters.get('author_id'):
                search_query = search_query.filter(Post.author_id == filters['author_id'])
            
            if filters.get('visibility'):
                search_query = search_query.filter(Post.visibility == filters['visibility'])
            else:
                search_query = search_query.filter(Post.visibility == 'public')
            
            if filters.get('posted_within_days'):
                cutoff = datetime.now() - timedelta(days=filters['posted_within_days'])
                search_query = search_query.filter(Post.timestamp >= cutoff)
            
            results = search_query.order_by(Post.timestamp.desc()).limit(50).all()
            
            return [SearchService._serialize_post(post) for post in results]
        except Exception as e:
            logger.error(f"Error searching posts: {str(e)}")
            return []
    
    @staticmethod
    def _search_faculty(query, filters):
        """Search faculty"""
        try:
            # Assuming Faculty model exists
            from models_extended import Faculty
            
            search_query = Faculty.query.filter(
                or_(
                    Faculty.first_name.ilike(f'%{query}%'),
                    Faculty.last_name.ilike(f'%{query}%'),
                    Faculty.title.ilike(f'%{query}%'),
                    Faculty.specialization.ilike(f'%{query}%'),
                    Faculty.bio.ilike(f'%{query}%')
                )
            )
            
            # Apply filters
            if filters.get('department_id'):
                search_query = search_query.filter(Faculty.department_id == filters['department_id'])
            
            results = search_query.limit(50).all()
            
            return [SearchService._serialize_faculty(fac) for fac in results]
        except Exception as e:
            logger.error(f"Error searching faculty: {str(e)}")
            return []
    
    # Serializers
    @staticmethod
    def _serialize_job(job):
        return {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'description': job.description[:200] if job.description else '',
            'job_type': job.job_type,
            'salary': job.salary,
            'is_remote': job.is_remote,
            'posted_date': job.posted_date.isoformat() if job.posted_date else None
        }
    
    @staticmethod
    def _serialize_scholarship(sch):
        return {
            'id': sch.id,
            'name': sch.name,
            'amount': sch.amount,
            'description': sch.description[:200] if sch.description else '',
            'deadline': sch.deadline.isoformat() if sch.deadline else None,
            'department_id': sch.department_id
        }
    
    @staticmethod
    def _serialize_event(event):
        return {
            'id': event.id,
            'title': event.title,
            'description': event.description[:200] if event.description else '',
            'location': event.location,
            'start_time': event.start_time.isoformat() if event.start_time else None,
            'event_type': getattr(event, 'event_type', None)
        }
    
    @staticmethod
    def _serialize_user(user):
        return {
            'id': user.id,
            'full_name': user.full_name,
            'email': user.email,
            'major': user.major,
            'graduation_year': user.graduation_year,
            'profile_image': user.profile_image,
            'bio': user.bio[:150] if user.bio else ''
        }
    
    @staticmethod
    def _serialize_post(post):
        return {
            'id': post.id,
            'content': post.content[:200] if post.content else '',
            'timestamp': post.timestamp.isoformat() if post.timestamp else None,
            'author_id': post.author_id,
            'likes': post.likes
        }
    
    @staticmethod
    def _serialize_faculty(fac):
        return {
            'id': fac.id,
            'full_name': f"{fac.first_name} {fac.last_name}",
            'title': fac.title,
            'specialization': fac.specialization,
            'department_id': fac.department_id,
            'bio': fac.bio[:150] if hasattr(fac, 'bio') and fac.bio else ''
        }
    
    @staticmethod
    def _record_search(user_id, query, entity_types, result_count):
        """Record search for analytics"""
        try:
            from models_extended import SearchHistory
            
            search_record = SearchHistory(
                user_id=user_id,
                query=query,
                entity_types=json.dumps(entity_types),
                result_count=result_count,
                timestamp=datetime.now()
            )
            db.session.add(search_record)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error recording search: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    def get_autocomplete_suggestions(query, entity_type='jobs', limit=10):
        """
        Get autocomplete suggestions for search
        
        Args:
            query: Partial search query
            entity_type: Type of entity to suggest
            limit: Max suggestions
            
        Returns:
            list: Suggested search terms
        """
        if not query or len(query) < 2:
            return []
        
        try:
            if entity_type == 'jobs':
                suggestions = db.session.query(Job.title).filter(
                    Job.title.ilike(f'%{query}%')
                ).distinct().limit(limit).all()
            elif entity_type == 'scholarships':
                suggestions = db.session.query(Scholarship.name).filter(
                    Scholarship.name.ilike(f'%{query}%')
                ).distinct().limit(limit).all()
            elif entity_type == 'majors':
                suggestions = db.session.query(User.major).filter(
                    User.major.ilike(f'%{query}%')
                ).distinct().limit(limit).all()
            else:
                return []
            
            return [s[0] for s in suggestions if s[0]]
        except Exception as e:
            logger.error(f"Error getting autocomplete: {str(e)}")
            return []
    
    @staticmethod
    def get_facets(entity_type, query=None):
        """
        Get facet counts for filters
        
        Args:
            entity_type: Type of entity
            query: Optional search query to filter facets
            
        Returns:
            dict: Facet counts
        """
        try:
            if entity_type == 'jobs':
                return SearchService._get_job_facets(query)
            elif entity_type == 'scholarships':
                return SearchService._get_scholarship_facets(query)
            elif entity_type == 'events':
                return SearchService._get_event_facets(query)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting facets: {str(e)}")
            return {}
    
    @staticmethod
    def _get_job_facets(query=None):
        """Get job facets"""
        base_query = Job.query
        if query:
            base_query = base_query.filter(
                or_(
                    Job.title.ilike(f'%{query}%'),
                    Job.description.ilike(f'%{query}%')
                )
            )
        
        facets = {
            'job_types': {},
            'locations': {},
            'remote': {'yes': 0, 'no': 0}
        }
        
        # Job types
        job_types = db.session.query(Job.job_type, func.count(Job.id)).group_by(Job.job_type).all()
        facets['job_types'] = {jt[0]: jt[1] for jt in job_types if jt[0]}
        
        # Locations
        locations = db.session.query(Job.location, func.count(Job.id)).group_by(Job.location).limit(20).all()
        facets['locations'] = {loc[0]: loc[1] for loc in locations if loc[0]}
        
        # Remote
        remote_count = base_query.filter(Job.is_remote == True).count()
        onsite_count = base_query.filter(Job.is_remote == False).count()
        facets['remote'] = {'yes': remote_count, 'no': onsite_count}
        
        return facets
    
    @staticmethod
    def _get_scholarship_facets(query=None):
        """Get scholarship facets"""
        base_query = Scholarship.query
        if query:
            base_query = base_query.filter(
                or_(
                    Scholarship.name.ilike(f'%{query}%'),
                    Scholarship.description.ilike(f'%{query}%')
                )
            )
        
        facets = {
            'departments': {},
            'amount_ranges': {
                '0-1000': 0,
                '1000-5000': 0,
                '5000-10000': 0,
                '10000+': 0
            }
        }
        
        # Departments
        dept_counts = db.session.query(
            Department.name, func.count(Scholarship.id)
        ).join(Scholarship).group_by(Department.name).all()
        facets['departments'] = {d[0]: d[1] for d in dept_counts}
        
        return facets
    
    @staticmethod
    def _get_event_facets(query=None):
        """Get event facets"""
        facets = {
            'event_types': {},
            'upcoming': 0,
            'this_week': 0,
            'this_month': 0
        }
        
        # Event types
        if hasattr(Event, 'event_type'):
            event_types = db.session.query(Event.event_type, func.count(Event.id)).group_by(Event.event_type).all()
            facets['event_types'] = {et[0]: et[1] for et in event_types if et[0]}
        
        # Time ranges
        now = datetime.now()
        facets['upcoming'] = Event.query.filter(Event.start_time >= now).count()
        facets['this_week'] = Event.query.filter(
            Event.start_time >= now,
            Event.start_time <= now + timedelta(days=7)
        ).count()
        facets['this_month'] = Event.query.filter(
            Event.start_time >= now,
            Event.start_time <= now + timedelta(days=30)
        ).count()
        
        return facets


# Saved Searches functionality
class SavedSearchService:
    """Manage saved searches for users"""
    
    @staticmethod
    def save_search(user_id, name, query, entity_types, filters, email_alerts=False):
        """Save a search for later"""
        try:
            from models_extended import SavedSearch
            
            saved_search = SavedSearch(
                user_id=user_id,
                name=name,
                query=query,
                entity_types=json.dumps(entity_types),
                filters=json.dumps(filters),
                email_alerts=email_alerts,
                created_at=datetime.now()
            )
            db.session.add(saved_search)
            db.session.commit()
            
            logger.info(f"Saved search for user {user_id}: {name}")
            return saved_search.id
        except Exception as e:
            logger.error(f"Error saving search: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_saved_searches(user_id):
        """Get all saved searches for user"""
        try:
            from models_extended import SavedSearch
            
            searches = SavedSearch.query.filter_by(user_id=user_id).order_by(SavedSearch.created_at.desc()).all()
            return [{
                'id': s.id,
                'name': s.name,
                'query': s.query,
                'entity_types': json.loads(s.entity_types) if s.entity_types else [],
                'filters': json.loads(s.filters) if s.filters else {},
                'email_alerts': s.email_alerts,
                'created_at': s.created_at.isoformat() if s.created_at else None
            } for s in searches]
        except Exception as e:
            logger.error(f"Error getting saved searches: {str(e)}")
            return []
    
    @staticmethod
    def delete_saved_search(search_id, user_id):
        """Delete a saved search"""
        try:
            from models_extended import SavedSearch
            
            search = SavedSearch.query.filter_by(id=search_id, user_id=user_id).first()
            if search:
                db.session.delete(search)
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting saved search: {str(e)}")
            db.session.rollback()
            return False
