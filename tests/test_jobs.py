"""
Integration tests for job posting and application workflow
Tests the complete job lifecycle
"""

import pytest
from datetime import datetime, timedelta
from models import Job, JobApplication


@pytest.mark.integration
class TestJobWorkflow:
    """Test complete job posting and application workflow"""
    
    def test_job_listing_page(self, client):
        """Test that job listings page loads"""
        response = client.get('/careers/jobs')
        assert response.status_code == 200
        assert b'Jobs' in response.data or b'Opportunities' in response.data
    
    def test_create_job_posting(self, client, sample_alumni, db_session):
        """Test creating a job posting"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_alumni.id)
        
        response = client.post('/careers/jobs/create', data={
            'title': 'Junior Developer',
            'company': 'StartupCo',
            'location': 'Remote',
            'job_type': 'full_time',
            'salary_min': 50000,
            'salary_max': 70000,
            'description': 'Great opportunity for junior developers',
            'requirements': 'Bachelor degree, 1+ years experience',
            'deadline': (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify job was created
        job = Job.query.filter_by(title='Junior Developer').first()
        assert job is not None
        assert job.company == 'StartupCo'
    
    def test_view_job_detail(self, client, sample_job):
        """Test viewing job details"""
        response = client.get(f'/careers/jobs/{sample_job.id}')
        assert response.status_code == 200
        assert sample_job.title.encode() in response.data
        assert sample_job.company.encode() in response.data
    
    def test_apply_to_job(self, client, sample_user, sample_job, db_session):
        """Test applying to a job"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_user.id)
        
        from io import BytesIO
        
        response = client.post(f'/careers/jobs/{sample_job.id}/apply', data={
            'cover_letter': 'I am very interested in this position...',
            'resume': (BytesIO(b'fake resume data'), 'resume.pdf')
        }, content_type='multipart/form-data', follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_view_applications(self, client, sample_alumni, sample_job):
        """Test employer viewing applications"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_alumni.id)
        
        response = client.get(f'/careers/jobs/{sample_job.id}/applications')
        assert response.status_code == 200
    
    def test_job_search(self, client, sample_job):
        """Test job search functionality"""
        response = client.get('/careers/jobs/search', query_string={
            'q': 'Software',
            'location': 'Kansas',
            'job_type': 'full_time'
        })
        
        assert response.status_code == 200
    
    def test_job_filters(self, client):
        """Test job filtering"""
        response = client.get('/careers/jobs', query_string={
            'job_type': 'full_time',
            'salary_min': 60000
        })
        
        assert response.status_code == 200


@pytest.mark.api
class TestJobAPI:
    """Test job API endpoints"""
    
    def test_list_jobs_api(self, client, sample_job):
        """Test GET /api/jobs endpoint
        ---
        tags:
          - Jobs
        parameters:
          - name: page
            in: query
            type: integer
            default: 1
          - name: per_page
            in: query
            type: integer
            default: 20
        responses:
          200:
            description: List of jobs
            schema:
              $ref: '#/definitions/PaginatedResponse'
        """
        response = client.get('/api/jobs')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'items' in data or isinstance(data, list)
    
    def test_get_job_detail_api(self, client, sample_job):
        """Test GET /api/jobs/:id endpoint
        ---
        tags:
          - Jobs
        parameters:
          - name: id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Job details
            schema:
              $ref: '#/definitions/Job'
          404:
            description: Job not found
        """
        response = client.get(f'/api/jobs/{sample_job.id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == sample_job.id
        assert data['title'] == sample_job.title
    
    def test_create_job_api(self, client, sample_alumni):
        """Test POST /api/jobs endpoint
        ---
        tags:
          - Jobs
        parameters:
          - name: body
            in: body
            required: true
            schema:
              $ref: '#/definitions/Job'
        responses:
          201:
            description: Job created
          400:
            description: Validation error
          401:
            description: Unauthorized
        """
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_alumni.id)
        
        response = client.post('/api/jobs', json={
            'title': 'Data Scientist',
            'company': 'DataCorp',
            'location': 'Chicago, IL',
            'job_type': 'full_time',
            'salary_min': 80000,
            'salary_max': 100000,
            'description': 'Exciting data science role',
            'requirements': 'MS in Data Science, Python, SQL',
            'deadline': (datetime.utcnow() + timedelta(days=30)).isoformat()
        })
        
        assert response.status_code in [200, 201]
    
    def test_update_job_api(self, client, sample_alumni, sample_job):
        """Test PUT /api/jobs/:id endpoint"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_alumni.id)
        
        response = client.put(f'/api/jobs/{sample_job.id}', json={
            'title': 'Senior Software Engineer',
            'salary_max': 90000
        })
        
        assert response.status_code in [200, 201]
    
    def test_delete_job_api(self, client, sample_alumni, sample_job):
        """Test DELETE /api/jobs/:id endpoint"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_alumni.id)
        
        response = client.delete(f'/api/jobs/{sample_job.id}')
        assert response.status_code in [200, 204]
