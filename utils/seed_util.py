from extensions import db

def safe_add(instance):
    db.session.add(instance)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
