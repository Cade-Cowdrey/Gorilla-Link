from flask import Blueprint, render_template, redirect, url_for, flash, request


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.get('/')
def dashboard():
stats = {
'total_users': 312,
'active_departments': 15,
'active_events': 8,
'pending_notifications': 5,
}
return render_template('admin/dashboard.html', stats=stats)


@admin_bp.get('/users')
def users():
sample_users = [
{'id': 1, 'first_name': 'Cade', 'last_name': 'Cowdrey', 'email': 'ccowdrey@pittstate.edu', 'role': 'Admin'},
{'id': 2, 'first_name': 'Connor', 'last_name': 'Vandenberg', 'email': 'cvandenberg@pittstate.edu', 'role': 'Student'},
{'id': 3, 'first_name': 'Vance', 'last_name': 'Finch', 'email': 'vfinch@pittstate.edu', 'role': 'Alumni'},
]
return render_template('admin/manage_users.html', users=sample_users)


@admin_bp.get('/departments')
def departments():
departments = [
{'id': 1, 'title': 'Computer Science', 'faculty_count': 12},
{'id': 2, 'title': 'Marketing', 'faculty_count': 8},
{'id': 3, 'title': 'Engineering Technology', 'faculty_count': 20},
]
return render_template('admin/manage_departments.html', departments=departments)


@admin_bp.get('/events')
def events():
events = [
{'id': 1, 'title': 'Career Fair', 'date': '2025-11-15', 'location': 'Student Center'},
{'id': 2, 'title': 'Alumni Banquet', 'date': '2025-12-01', 'location': 'Crimson & Gold Ballroom'},
]
return render_template('admin/manage_events.html', events=events)


@admin_bp.get('/notifications')
def notifications():
notes = [
{'id': 1, 'subject': 'System Maintenance', 'status': 'Scheduled'},
{'id': 2, 'subject': 'New Job Postings', 'status': 'Sent'},
]
return render_template('admin/manage_notifications.html', notifications=notes)


@admin_bp.post('/notifications/send')
def send_notification():
subject = request.form.get('subject')
message = request.form.get('message')
flash(f'Notification sent: {subject}', 'success')
return redirect(url_for('admin.notifications'))


@admin_bp.get('/back')
def back_to_home():
flash('Returning to home', 'info')
return redirect(url_for('core.home'))
