# blueprints/careers/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash


careers_bp = Blueprint('careers', __name__, url_prefix='/careers')


@careers_bp.get('/')
def dashboard():
stats = {
'open_roles': 18,
'active_employers': 12,
'avg_salary': 64200,
'last_updated': 'Today'
}
return render_template('careers/dashboard.html', stats=stats)


@careers_bp.get('/by-department')
def by_department():
departments = [
{'slug': 'csis', 'title': 'Computer Science', 'open_roles': 7},
{'slug': 'marketing', 'title': 'Marketing', 'open_roles': 3},
{'slug': 'engineering', 'title': 'Engineering', 'open_roles': 8},
]
return render_template('careers/by_department.html', departments=departments)


@careers_bp.get('/<string:slug>')
def detail(slug):
job = {
'slug': slug,
'title': slug.replace('-', ' ').title(),
'company': 'Example Corp',
'location': 'Pittsburg, KS',
'salary': '60k–75k',
'description': 'Role description goes here.'
}
return render_template('careers/detail.html', job=job)


@careers_bp.route('/create', methods=['GET', 'POST'])
def create():
if request.method == 'POST':
flash('Job created', 'success')
return redirect(url_for('careers.dashboard'))
return render_template('careers/create.html')


@careers_bp.route('/<string:slug>/edit', methods=['GET', 'POST'])
def edit(slug):
if request.method == 'POST':
flash('Job updated', 'success')
return redirect(url_for('careers.detail', slug=slug))
return render_template('careers/edit.html', slug=slug)
