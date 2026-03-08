from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Barangay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    users = db.relationship('User', backref='barangay', lazy=True)
    households = db.relationship('Household', backref='barangay', lazy=True)
    sitios = db.relationship('Sitio', backref='barangay', lazy=True, cascade="all, delete-orphan")

class Sitio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangay.id'), nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=True)
    password = db.Column(db.String(60), nullable=True)
    role = db.Column(db.String(20), nullable=False)  # 'Super Admin', 'Admin', 'BHW', 'Viewer', 'Supervisor', 'Nurse', 'Midwife'
    title = db.Column(db.String(50), nullable=True) # Official Title (e.g., Barangay Captain, Head Nurse)
    is_active = db.Column(db.Boolean, default=True)
    bio = db.Column(db.Text, nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.now)
    
    # BHW Specific fields
    bhw_code = db.Column(db.String(20), unique=True, nullable=True)
    pin = db.Column(db.String(60), nullable=True) # Hashed 4-digit PIN
    qr_token = db.Column(db.String(100), unique=True, nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    assigned_sitio = db.Column(db.String(50), nullable=True)
    
    # Relationships
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangay.id'), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.now)
    visits = db.relationship('Visit', backref='bhw', lazy=True)

class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_name = db.Column(db.String(100), nullable=True) # e.g. Dela Cruz Family
    sitio_id = db.Column(db.Integer, db.ForeignKey('sitio.id'), nullable=True)
    sitio = db.Column(db.String(100), nullable=False) # Keep for backward compatibility/display
    address = db.Column(db.String(200), nullable=False)
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangay.id'), nullable=False)
    patients = db.relationship('Patient', backref='household', lazy=True)
    visits = db.relationship('Visit', backref='household', lazy=True)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey('household.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    civil_status = db.Column(db.String(20))
    contact = db.Column(db.String(20))
    consultations = db.relationship('Consultation', backref='patient', lazy=True)
    immunizations = db.relationship('Immunization', backref='patient', lazy=True)

class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    complaints = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    created_by = db.Column(db.String(50))

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey('household.id'), nullable=False)
    bhw_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_visited = db.Column(db.DateTime, nullable=False, default=datetime.now)
    notes = db.Column(db.Text)
    health_remarks = db.Column(db.Text) # BP, symptoms, etc.
    follow_up_needed = db.Column(db.Boolean, default=False)

class Immunization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    vaccine = db.Column(db.String(100), nullable=False)
    dose = db.Column(db.Integer, nullable=False)
    date_administered = db.Column(db.Date, nullable=False)
    remarks = db.Column(db.String(200))

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    generic_name = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    expiry_date = db.Column(db.Date, nullable=False)
