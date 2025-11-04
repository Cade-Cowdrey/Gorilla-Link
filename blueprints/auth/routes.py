from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db
from utils.analytics_util import record_page_view
from services.oauth_service import OAuthService, oauth

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=["GET", "POST"])
def login():
    record_page_view("auth_login")
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("core.home"))
        flash("Invalid credentials.", "danger")
    return render_template("auth/login.html", title="Login | PittState-Connect")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


# ========================
# OAuth Routes
# ========================

@bp.route("/login/<provider>")
def oauth_login(provider):
    """Initiate OAuth login with provider (google, linkedin, microsoft)"""
    if provider not in ['google', 'linkedin', 'microsoft']:
        flash("Invalid OAuth provider", "error")
        return redirect(url_for("auth.login"))
    
    # Redirect to OAuth provider
    return OAuthService.get_authorization_url(provider)


@bp.route("/callback/<provider>")
def oauth_callback(provider):
    """Handle OAuth callback from provider"""
    if provider not in ['google', 'linkedin', 'microsoft']:
        flash("Invalid OAuth provider", "error")
        return redirect(url_for("auth.login"))
    
    # Handle OAuth callback
    user, is_new, error = OAuthService.handle_callback(provider)
    
    if error:
        flash(f"Authentication failed: {error}", "error")
        return redirect(url_for("auth.login"))
    
    if not user:
        flash("Failed to authenticate. Please try again.", "error")
        return redirect(url_for("auth.login"))
    
    # Log user in
    login_user(user, remember=True)
    
    if is_new:
        flash(f"Welcome to PittState Connect! Your account has been created with {provider}.", "success")
        # Redirect to onboarding for new users
        return redirect(url_for("profile.onboarding"))
    else:
        flash(f"Welcome back! Logged in with {provider}.", "success")
        return redirect(url_for("core.home"))


@bp.route("/link/<provider>")
@login_required
def oauth_link(provider):
    """Link OAuth provider to existing account"""
    if provider not in ['google', 'linkedin', 'microsoft']:
        flash("Invalid OAuth provider", "error")
        return redirect(url_for("profile.settings"))
    
    # Store intent to link (not login)
    request.session['oauth_intent'] = 'link'
    return OAuthService.get_authorization_url(provider)


@bp.route("/unlink/<provider>", methods=["POST"])
@login_required
def oauth_unlink(provider):
    """Unlink OAuth provider from account"""
    if provider not in ['google', 'linkedin', 'microsoft']:
        flash("Invalid OAuth provider", "error")
        return redirect(url_for("profile.settings"))
    
    success = OAuthService.unlink_account(current_user.id, provider)
    
    if success:
        flash(f"Successfully unlinked {provider} account", "success")
    else:
        flash(f"Cannot unlink {provider}. You need at least one authentication method.", "error")
    
    return redirect(url_for("profile.settings"))
