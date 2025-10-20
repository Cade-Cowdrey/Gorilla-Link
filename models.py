# models.py
db = SQLAlchemy()


# ------------------------------
# Association Tables (examples — keep if referenced)
# ------------------------------
user_roles = db.Table(
'user_roles',
db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)


user_departments = db.Table(
'user_departments',
db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
db.Column('department_id', db.Integer, db.ForeignKey('departments.id'), primary_key=True)
)


# ------------------------------
# Core Models
# ------------------------------
class User(UserMixin, db.Model):
__tablename__ = 'users'


id = db.Column(db.Integer, primary_key=True)
email = db.Column(db.String(255), unique=True, nullable=False, index=True)


# Professional naming (no username):
first_name = db.Column(db.String(120), nullable=False)
last_name = db.Column(db.String(120), nullable=False)


created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


is_active = db.Column(db.Boolean, default=True, nullable=False)
is_staff = db.Column(db.Boolean, default=False, nullable=False)


roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
departments = db.relationship('Department', secondary=user_departments, backref=db.backref('users', lazy='dynamic'))


@property
def full_name(self) -> str:
"""Display helper: combine first and last name for templates.
Not a stored column; keeps the data model professional.
"""
return f"{(self.first_name or '').strip()} {(self.last_name or '').strip()}".strip()


def get_id(self):
return str(self.id)


def __repr__(self):
return f"<User {self.id} {self.email} {self.first_name} {self.last_name}>"




class Role(db.Model):
__tablename__ = 'roles'


id = db.Column(db.Integer, primary_key=True)
name = db.Column(db.String(64), unique=True, nullable=False)


def __repr__(self):
return f"<Role {self.name}>"




class Department(db.Model):
__tablename__ = 'departments'


id = db.Column(db.Integer, primary_key=True)
slug = db.Column(db.String(128), unique=True, nullable=False, index=True)
title = db.Column(db.String(255), nullable=False)
description = db.Column(db.Text, nullable=True)


created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def __repr__(self):
return f"<Department {self.slug}>"




# Useful composite index example
Index('ix_users_active_email', User.is_active, User.email)
