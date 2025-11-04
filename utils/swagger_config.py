"""
Swagger/OpenAPI Configuration for API Documentation
Provides automatic API documentation with interactive UI
"""

from flasgger import Swagger
from flask import request, current_app
import os


def get_swagger_config():
    """
    Returns the Swagger configuration dictionary
    """
    return {
        'title': 'PittState Connect API',
        'version': '1.0.0',
        'description': '''
# PittState Connect API Documentation

Welcome to the PittState Connect API! This documentation provides comprehensive information about all available endpoints.

## Authentication

Most endpoints require authentication. Include your session cookie or use OAuth2 tokens.

```
Authorization: Bearer <your_token>
```

## Rate Limiting

API requests are rate-limited to prevent abuse:
- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour
- **Premium users**: 5000 requests/hour

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## Pagination

List endpoints support pagination with the following parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

Pagination metadata is included in responses:
```json
{
  "items": [...],
  "page": 1,
  "per_page": 20,
  "total": 150,
  "pages": 8,
  "has_prev": false,
  "has_next": true
}
```

## Error Handling

The API uses standard HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

Error responses include a JSON body:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {...}
}
```

## Versioning

The API is versioned. Current version: v1
Future versions will be accessible via `/api/v2/...`

## Support

For API support, contact: api-support@pittstate.edu
        ''',
        'termsOfService': 'https://pittstate.edu/terms',
        'contact': {
            'name': 'PittState Connect API Support',
            'email': 'api-support@pittstate.edu',
            'url': 'https://pittstate.edu/support'
        },
        'license': {
            'name': 'MIT',
            'url': 'https://opensource.org/licenses/MIT'
        },
        'host': os.getenv('API_HOST', 'localhost:5000'),
        'basePath': '/api',
        'schemes': [os.getenv('API_SCHEME', 'http')],
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
            },
            'SessionAuth': {
                'type': 'apiKey',
                'name': 'session',
                'in': 'cookie',
                'description': 'Session-based authentication using Flask-Login'
            },
            'OAuth2': {
                'type': 'oauth2',
                'flow': 'accessCode',
                'authorizationUrl': 'https://pittstate.edu/oauth/authorize',
                'tokenUrl': 'https://pittstate.edu/oauth/token',
                'scopes': {
                    'read:profile': 'Read user profile',
                    'write:profile': 'Update user profile',
                    'read:jobs': 'Read job listings',
                    'write:jobs': 'Post job listings',
                    'admin': 'Administrative access'
                }
            }
        },
        'security': [
            {'Bearer': []},
            {'SessionAuth': []},
            {'OAuth2': ['read:profile']}
        ],
        'tags': [
            {
                'name': 'Authentication',
                'description': 'User authentication and authorization endpoints'
            },
            {
                'name': 'Users',
                'description': 'User profile management'
            },
            {
                'name': 'Jobs',
                'description': 'Job posting and application management'
            },
            {
                'name': 'Events',
                'description': 'Campus events and RSVPs'
            },
            {
                'name': 'Scholarships',
                'description': 'Scholarship opportunities and applications'
            },
            {
                'name': 'Analytics',
                'description': 'Analytics and reporting endpoints'
            },
            {
                'name': 'Admin',
                'description': 'Administrative functions (requires admin role)'
            }
        ],
        'specs': [
            {
                'endpoint': 'apispec',
                'route': '/apispec.json',
                'rule_filter': lambda rule: True,  # Include all endpoints
                'model_filter': lambda tag: True,  # Include all models
            }
        ],
        'static_url_path': '/flasgger_static',
        'swagger_ui': True,
        'specs_route': '/docs/'
    }


def get_swagger_template():
    """
    Returns the Swagger UI template configuration
    """
    return {
        'swagger': '2.0',
        'info': {
            'title': 'PittState Connect API',
            'version': '1.0.0',
            'description': 'Alumni networking and career development platform'
        },
        'definitions': {
            'User': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'example': 123},
                    'email': {'type': 'string', 'example': 'john.doe@pittstate.edu'},
                    'first_name': {'type': 'string', 'example': 'John'},
                    'last_name': {'type': 'string', 'example': 'Doe'},
                    'role': {'type': 'string', 'enum': ['student', 'alumni', 'faculty', 'employer', 'admin']},
                    'graduation_year': {'type': 'integer', 'example': 2020},
                    'major': {'type': 'string', 'example': 'Computer Science'},
                    'created_at': {'type': 'string', 'format': 'date-time'},
                    'last_seen': {'type': 'string', 'format': 'date-time'}
                }
            },
            'Job': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'example': 456},
                    'title': {'type': 'string', 'example': 'Software Engineer'},
                    'company': {'type': 'string', 'example': 'Tech Corp'},
                    'location': {'type': 'string', 'example': 'Kansas City, MO'},
                    'job_type': {'type': 'string', 'enum': ['full_time', 'part_time', 'internship', 'contract']},
                    'salary_min': {'type': 'integer', 'example': 60000},
                    'salary_max': {'type': 'integer', 'example': 80000},
                    'description': {'type': 'string'},
                    'requirements': {'type': 'string'},
                    'posted_date': {'type': 'string', 'format': 'date'},
                    'deadline': {'type': 'string', 'format': 'date'},
                    'is_active': {'type': 'boolean'}
                }
            },
            'Event': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'example': 789},
                    'title': {'type': 'string', 'example': 'Career Fair 2024'},
                    'description': {'type': 'string'},
                    'start_time': {'type': 'string', 'format': 'date-time'},
                    'end_time': {'type': 'string', 'format': 'date-time'},
                    'location': {'type': 'string', 'example': 'Student Center'},
                    'event_type': {'type': 'string', 'enum': ['career_fair', 'networking', 'workshop', 'social']},
                    'capacity': {'type': 'integer', 'example': 100},
                    'attendees_count': {'type': 'integer', 'example': 45},
                    'is_virtual': {'type': 'boolean'}
                }
            },
            'Scholarship': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'example': 321},
                    'name': {'type': 'string', 'example': 'Excellence Scholarship'},
                    'amount': {'type': 'number', 'example': 5000.00},
                    'description': {'type': 'string'},
                    'eligibility': {'type': 'string'},
                    'deadline': {'type': 'string', 'format': 'date'},
                    'requirements': {'type': 'array', 'items': {'type': 'string'}},
                    'is_renewable': {'type': 'boolean'}
                }
            },
            'Error': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'Invalid request'},
                    'code': {'type': 'string', 'example': 'VALIDATION_ERROR'},
                    'details': {'type': 'object'}
                }
            },
            'PaginatedResponse': {
                'type': 'object',
                'properties': {
                    'items': {'type': 'array', 'items': {'type': 'object'}},
                    'page': {'type': 'integer', 'example': 1},
                    'per_page': {'type': 'integer', 'example': 20},
                    'total': {'type': 'integer', 'example': 150},
                    'pages': {'type': 'integer', 'example': 8},
                    'has_prev': {'type': 'boolean', 'example': False},
                    'has_next': {'type': 'boolean', 'example': True},
                    'prev_num': {'type': 'integer', 'nullable': True},
                    'next_num': {'type': 'integer', 'example': 2}
                }
            }
        }
    }


def init_swagger(app):
    """
    Initialize Swagger documentation for the Flask app
    
    Args:
        app: Flask application instance
    """
    config = get_swagger_config()
    template = get_swagger_template()
    
    # Initialize Swagger
    swagger = Swagger(app, config=config, template=template)
    
    # Add custom validator for API endpoints
    @app.before_request
    def validate_api_version():
        """Validate API version in request"""
        if request.path.startswith('/api/'):
            api_version = request.headers.get('X-API-Version', '1.0')
            if api_version not in ['1.0', '1']:
                return {
                    'error': 'Unsupported API version',
                    'code': 'INVALID_API_VERSION',
                    'supported_versions': ['1.0']
                }, 400
    
    app.logger.info('Swagger API documentation initialized at /docs/')
    
    return swagger


# Common Swagger response specifications
SWAGGER_RESPONSES = {
    '200': {
        'description': 'Success'
    },
    '201': {
        'description': 'Created successfully'
    },
    '400': {
        'description': 'Bad Request - Invalid input',
        'schema': {'$ref': '#/definitions/Error'}
    },
    '401': {
        'description': 'Unauthorized - Authentication required',
        'schema': {'$ref': '#/definitions/Error'}
    },
    '403': {
        'description': 'Forbidden - Insufficient permissions',
        'schema': {'$ref': '#/definitions/Error'}
    },
    '404': {
        'description': 'Not Found',
        'schema': {'$ref': '#/definitions/Error'}
    },
    '429': {
        'description': 'Too Many Requests - Rate limit exceeded',
        'schema': {'$ref': '#/definitions/Error'},
        'headers': {
            'X-RateLimit-Limit': {
                'description': 'Request limit per hour',
                'type': 'integer'
            },
            'X-RateLimit-Remaining': {
                'description': 'Remaining requests',
                'type': 'integer'
            },
            'X-RateLimit-Reset': {
                'description': 'Time when limit resets (Unix timestamp)',
                'type': 'integer'
            },
            'Retry-After': {
                'description': 'Seconds to wait before retrying',
                'type': 'integer'
            }
        }
    },
    '500': {
        'description': 'Internal Server Error',
        'schema': {'$ref': '#/definitions/Error'}
    }
}


# Parameter definitions for reuse
SWAGGER_PARAMETERS = {
    'page': {
        'name': 'page',
        'in': 'query',
        'type': 'integer',
        'required': False,
        'default': 1,
        'description': 'Page number for pagination'
    },
    'per_page': {
        'name': 'per_page',
        'in': 'query',
        'type': 'integer',
        'required': False,
        'default': 20,
        'description': 'Number of items per page (max: 100)'
    },
    'sort_by': {
        'name': 'sort_by',
        'in': 'query',
        'type': 'string',
        'required': False,
        'description': 'Field to sort by'
    },
    'order': {
        'name': 'order',
        'in': 'query',
        'type': 'string',
        'required': False,
        'enum': ['asc', 'desc'],
        'default': 'desc',
        'description': 'Sort order'
    },
    'search': {
        'name': 'search',
        'in': 'query',
        'type': 'string',
        'required': False,
        'description': 'Search query'
    }
}
