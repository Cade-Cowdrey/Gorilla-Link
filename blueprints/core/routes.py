from flask import Blueprint, render_template, request, flash, redirect, url_for

core = Blueprint('core', __name__, template_folder='templates', static_folder='static')

# -----------------------------------------------------------
# 🏠 Home Page
# -----------------------------------------------------------
@core.route('/')
def home():
    return render_template('core/home.html')


# -----------------------------------------------------------
# 👥 Team Page
# -----------------------------------------------------------
@core.route('/team')
def team():
    return render_template('core/team.html')


# -----------------------------------------------------------
# 💼 Careers Page
# -----------------------------------------------------------
@core.route('/careers')
def careers():
    return render_template('core/careers.html')


# -----------------------------------------------------------
# 📅 Events Page
# -----------------------------------------------------------
@core.route('/events')
def events():
    return render_template('core/events.html')


# -----------------------------------------------------------
# 🏫 About Page
# -----------------------------------------------------------
@core.route('/about')
def about():
    """
    Display the PSU-branded About page describing the mission, vision,
    and purpose of the PittState-Connect platform.
    """
    return render_template('core/about.html')


# -----------------------------------------------------------
# 📞 Contact Page (GET + POST)
# -----------------------------------------------------------
@core.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Display a contact form and handle submissions.
    This version flashes a success message but can be upgraded later
    to send real emails via utils/mail_util.py or Flask-Mail.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('Please fill out all required fields.', 'error')
        else:
            # Placeholder logic — replace with mail_util.send_contact_email() later
            flash('Thank you, your message has been sent successfully!', 'success')
            return redirect(url_for('core.contact'))

    return render_template('core/contact.html')


# -----------------------------------------------------------
# ⚠️ 404 Fallback (optional)
# -----------------------------------------------------------
@core.app_errorhandler(404)
def page_not_found(error):
    """
    Custom PSU-branded 404 page.
    """
    return render_template('errors/404.html'), 404


# -----------------------------------------------------------
# 🧹 Optional: future pages or redirects
# -----------------------------------------------------------
@core.route('/privacy')
def privacy():
    """Privacy Policy placeholder page."""
    return render_template('core/privacy.html')


@core.route('/terms')
def terms():
    """Terms of Service placeholder page."""
    return render_template('core/terms.html')
