"""
PittState-Connect | Database Query Optimization
Tools for detecting and fixing N+1 queries, adding pagination, and optimizing database performance.
"""

from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Query, joinedload, selectinload
from flask import g, current_app, request
from functools import wraps
from typing import Any, Optional, List
import time
import logging

logger = logging.getLogger(__name__)


# Query performance tracking
class QueryTracker:
    """Track database queries for performance monitoring"""
    
    def __init__(self):
        self.queries = []
        self.total_time = 0
        self.enabled = False
    
    def start(self):
        """Start tracking queries"""
        self.queries = []
        self.total_time = 0
        self.enabled = True
    
    def stop(self):
        """Stop tracking"""
        self.enabled = False
    
    def add_query(self, statement: str, duration: float, params: tuple = None):
        """Record a query"""
        if not self.enabled:
            return
        
        self.queries.append({
            'statement': statement,
            'duration': duration,
            'params': params,
            'timestamp': time.time()
        })
        self.total_time += duration
    
    def get_stats(self) -> dict:
        """Get query statistics"""
        if not self.queries:
            return {
                'total_queries': 0,
                'total_time': 0,
                'avg_time': 0,
                'slowest_query': None
            }
        
        sorted_queries = sorted(self.queries, key=lambda q: q['duration'], reverse=True)
        
        return {
            'total_queries': len(self.queries),
            'total_time': round(self.total_time, 3),
            'avg_time': round(self.total_time / len(self.queries), 3),
            'slowest_query': {
                'statement': sorted_queries[0]['statement'][:200],
                'duration': round(sorted_queries[0]['duration'], 3)
            },
            'queries': self.queries
        }
    
    def detect_n_plus_one(self) -> List[str]:
        """Detect potential N+1 query patterns"""
        n_plus_one_patterns = []
        
        # Group similar queries
        query_groups = {}
        for query in self.queries:
            # Extract table name from query
            statement = query['statement'].upper()
            if 'FROM' in statement:
                table = statement.split('FROM')[1].split()[0].strip()
                if table not in query_groups:
                    query_groups[table] = []
                query_groups[table].append(query)
        
        # Check for repeated similar queries
        for table, queries in query_groups.items():
            if len(queries) > 10:
                # If we're making >10 queries to the same table, might be N+1
                n_plus_one_patterns.append(
                    f"Potential N+1: {len(queries)} queries to {table}. "
                    f"Consider using joinedload() or selectinload()"
                )
        
        return n_plus_one_patterns


# Global tracker
_tracker = QueryTracker()


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time"""
    conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query completion and track performance"""
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    _tracker.add_query(statement, total_time, parameters)


def track_queries(f):
    """
    Decorator to track all queries in a function
    
    Example:
        @track_queries
        def my_function():
            # All queries will be tracked
            users = User.query.all()
            return users
            
        # Access stats via g.query_stats after function completes
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        _tracker.start()
        try:
            result = f(*args, **kwargs)
            stats = _tracker.get_stats()
            g.query_stats = stats
            
            # Log slow queries
            if stats['total_time'] > 1.0:  # > 1 second
                logger.warning(
                    f"Slow query performance in {f.__name__}: "
                    f"{stats['total_queries']} queries, {stats['total_time']}s total"
                )
            
            # Check for N+1
            n_plus_one = _tracker.detect_n_plus_one()
            if n_plus_one:
                logger.warning(f"N+1 detected in {f.__name__}: {n_plus_one}")
                g.n_plus_one_warnings = n_plus_one
            
            return result
        finally:
            _tracker.stop()
    
    return wrapped


def paginate_query(query: Query, 
                   page: int = 1, 
                   per_page: int = 20,
                   max_per_page: int = 100) -> dict:
    """
    Paginate a SQLAlchemy query with metadata
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum items per page (security limit)
        
    Returns:
        dict with:
            - items: List of results
            - page: Current page
            - per_page: Items per page
            - total: Total item count
            - pages: Total page count
            - has_prev: bool
            - has_next: bool
            - prev_num: Previous page number
            - next_num: Next page number
    """
    # Validate inputs
    page = max(1, int(page))
    per_page = min(max(1, int(per_page)), max_per_page)
    
    # Get total count efficiently
    total = query.count()
    
    # Calculate pagination
    pages = (total + per_page - 1) // per_page  # Ceiling division
    has_prev = page > 1
    has_next = page < pages
    
    # Get items for current page
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None
    }


def optimize_query(query: Query, relationships: List[str] = None, strategy: str = 'joined') -> Query:
    """
    Automatically optimize query with eager loading
    
    Args:
        query: Original query
        relationships: List of relationship names to load
        strategy: 'joined' (joinedload) or 'select' (selectinload)
        
    Example:
        # Without optimization (N+1 problem):
        users = User.query.all()
        for user in users:
            print(user.posts)  # Each iteration makes a new query
        
        # With optimization:
        users = optimize_query(
            User.query,
            relationships=['posts', 'profile']
        ).all()
        for user in users:
            print(user.posts)  # No additional queries!
    """
    if not relationships:
        return query
    
    load_func = joinedload if strategy == 'joined' else selectinload
    
    for rel in relationships:
        if '.' in rel:
            # Handle nested relationships (e.g., 'posts.comments')
            parts = rel.split('.')
            current = getattr(query.column_descriptions[0]['type'], parts[0])
            loader = load_func(current)
            
            for part in parts[1:]:
                current = getattr(current.property.mapper.class_, part)
                loader = loader.selectinload(current)
            
            query = query.options(loader)
        else:
            # Simple relationship
            query = query.options(load_func(rel))
    
    return query


def get_query_plan(query: Query) -> str:
    """
    Get the SQL query execution plan (PostgreSQL)
    
    Args:
        query: SQLAlchemy query
        
    Returns:
        Query execution plan as string
    """
    try:
        from sqlalchemy.dialects import postgresql
        statement = query.statement.compile(dialect=postgresql.dialect())
        
        # Get execution plan
        plan_query = f"EXPLAIN ANALYZE {statement}"
        result = query.session.execute(plan_query)
        
        return '\n'.join([str(row) for row in result])
    except Exception as e:
        logger.error(f"Failed to get query plan: {str(e)}")
        return f"Error: {str(e)}"


def find_missing_indexes(model_class: type) -> List[str]:
    """
    Analyze model for potentially missing indexes
    
    Args:
        model_class: SQLAlchemy model class
        
    Returns:
        List of recommendations
    """
    recommendations = []
    inspector = inspect(model_class)
    
    # Check foreign keys have indexes
    for column in inspector.columns:
        for fk in column.foreign_keys:
            if not any(idx for idx in inspector.indexes if column.name in idx.columns):
                recommendations.append(
                    f"Consider adding index on {model_class.__name__}.{column.name} (foreign key)"
                )
    
    # Check commonly filtered fields
    # (This is heuristic - adjust based on your query patterns)
    common_filter_columns = ['email', 'username', 'status', 'type', 'created_at']
    for column in inspector.columns:
        if any(pattern in column.name.lower() for pattern in common_filter_columns):
            if not any(idx for idx in inspector.indexes if column.name in idx.columns):
                recommendations.append(
                    f"Consider adding index on {model_class.__name__}.{column.name} (frequently filtered)"
                )
    
    return recommendations


def log_slow_queries():
    """
    Middleware to log slow queries after each request
    """
    def after_request(response):
        if hasattr(g, 'query_stats'):
            stats = g.query_stats
            if stats['total_time'] > 0.5:  # Log if >500ms
                logger.warning(
                    f"Slow request: {request.path} - "
                    f"{stats['total_queries']} queries in {stats['total_time']}s"
                )
                
                if current_app.debug:
                    # Add debug header
                    response.headers['X-Query-Count'] = str(stats['total_queries'])
                    response.headers['X-Query-Time'] = str(stats['total_time'])
        
        return response
    
    return after_request


def bulk_insert_optimized(session, model_class: type, data_list: List[dict]):
    """
    Optimized bulk insert using SQLAlchemy Core
    
    Args:
        session: Database session
        model_class: Model class to insert
        data_list: List of dicts with data
        
    Example:
        users_data = [
            {'name': 'Alice', 'email': 'alice@example.com'},
            {'name': 'Bob', 'email': 'bob@example.com'},
        ]
        bulk_insert_optimized(db.session, User, users_data)
    """
    if not data_list:
        return
    
    try:
        # Use bulk_insert_mappings for better performance
        session.bulk_insert_mappings(model_class, data_list)
        session.commit()
        logger.info(f"Bulk inserted {len(data_list)} {model_class.__name__} records")
    except Exception as e:
        session.rollback()
        logger.error(f"Bulk insert failed: {str(e)}")
        raise


def bulk_update_optimized(session, model_class: type, data_list: List[dict]):
    """
    Optimized bulk update using SQLAlchemy Core
    
    Args:
        session: Database session
        model_class: Model class to update
        data_list: List of dicts with data (must include 'id')
    """
    if not data_list:
        return
    
    try:
        session.bulk_update_mappings(model_class, data_list)
        session.commit()
        logger.info(f"Bulk updated {len(data_list)} {model_class.__name__} records")
    except Exception as e:
        session.rollback()
        logger.error(f"Bulk update failed: {str(e)}")
        raise
