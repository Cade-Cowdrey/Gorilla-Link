"""
PittState-Connect | Blueprint Auto-Registration System
Safely registers all modular app blueprints in production.

Auto-loads:
- Core modules (core, auth, admin)
- Phase 2+ enhancements (scholarships, analytics, faculty)
- Optional enhancements (ai_assistant, alumni, employers, etc.)
"""

import importlib
import pkgutil
from loguru import logger

# ======================================================
# 🧱 BLUEPRINT REGISTRATION
# ======================================================

def register_blueprints(app):
    """
    Automatically discovers and registers all blueprints inside the /blueprints directory.
    Each subfolder must contain an __init__.py and a routes.py file defining a Blueprint instance named 'bp'.
    """
    logger.info("🔍 Auto-registering blueprints...")

    package_name = __name__
    package = importlib.import_module(package_name)

    # List of blueprints to skip if needed
    skip_modules = {"__pycache__", "tests", "archive"}

    # Walk through the blueprints directory dynamically
    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if is_pkg and module_name not in skip_modules:
            try:
                module = importlib.import_module(f"{package_name}.{module_name}.routes")

                if hasattr(module, "bp"):
                    app.register_blueprint(module.bp)
                    logger.info(f"✅ Registered blueprint: {module_name}")
                else:
                    logger.warning(f"⚠️ No 'bp' found in {module_name}.routes — skipped.")
            except ModuleNotFoundError:
                logger.warning(f"⚠️ No routes.py found for {module_name} — skipped.")
            except Exception as e:
                logger.error(f"❌ Failed to register blueprint '{module_name}': {e}")

    # Register growth feature blueprints (direct .py files)
    logger.info("🔍 Registering growth feature blueprints...")
    
    growth_features = [
        ('gamification', 'gamification_bp'),
        ('success_stories', 'success_stories_bp'),
        ('referrals', 'referrals_bp'),
        ('recommendations', 'recommendations_bp'),
        ('ai_coach', 'ai_coach_bp'),
        ('forums', 'forums_bp'),
        ('mentorship', 'mentorship_bp'),
        ('auto_apply', 'auto_apply_bp'),
        ('push_notifications', 'push_notifications_bp'),
        ('messages', 'messages_bp'),
    ]
    
    for module_name, bp_name in growth_features:
        try:
            module = importlib.import_module(f"{package_name}.{module_name}")
            if hasattr(module, bp_name):
                app.register_blueprint(getattr(module, bp_name))
                logger.info(f"✅ Registered growth feature: {module_name}")
            else:
                logger.warning(f"⚠️ No '{bp_name}' found in {module_name} — skipped.")
        except Exception as e:
            logger.error(f"❌ Failed to register growth feature '{module_name}': {e}")
    
    # Register analytics and events subdirectories
    try:
        from blueprints.analytics.user_dashboard import analytics_bp
        app.register_blueprint(analytics_bp)
        logger.info("✅ Registered analytics blueprint")
    except Exception as e:
        logger.error(f"❌ Failed to register analytics blueprint: {e}")
    
    try:
        from blueprints.events.live import events_bp as live_events_bp
        app.register_blueprint(live_events_bp)
        logger.info("✅ Registered live events blueprint")
    except Exception as e:
        logger.error(f"❌ Failed to register live events blueprint: {e}")
    
    try:
        from blueprints.admin.dashboard import admin_bp as admin_growth_dashboard_bp
        app.register_blueprint(admin_growth_dashboard_bp)
        logger.info("✅ Registered admin growth dashboard")
    except Exception as e:
        logger.error(f"❌ Failed to register admin growth dashboard: {e}")

    logger.info("🦍 All blueprints loaded successfully for PittState-Connect.")



# ======================================================
# 🧩 MANUAL BLUEPRINT OVERRIDES (OPTIONAL)
# ======================================================
# If you want to explicitly include critical blueprints even if auto-load fails,
# you can define them manually below.

def register_critical_blueprints(app):
    """
    Fallback manual registration for critical routes in case auto-registration misses any.
    """
    try:
        from blueprints.core.routes import bp as core_bp
        from blueprints.auth.routes import bp as auth_bp
        from blueprints.admin.routes import bp as admin_bp
        app.register_blueprint(core_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        logger.info("✅ Manually registered critical blueprints.")
    except Exception as e:
        logger.error(f"❌ Failed to manually register critical blueprints: {e}")
