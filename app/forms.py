from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class BHWLoginForm(FlaskForm):
    bhw_code = StringField('BHW Code (ex: BHW-001)', validators=[DataRequired()])
    pin = PasswordField('4-Digit PIN', validators=[DataRequired(), Length(min=4, max=4)])
    submit = SubmitField('Login')

class PINForm(FlaskForm):
    pin = PasswordField('Enter your 4-digit PIN', validators=[DataRequired(), Length(min=4, max=4)])
    submit = SubmitField('Verify PIN')

class UserRegistrationForm(FlaskForm):
    username = StringField('Username (Optional)', validators=[Length(max=20)])
    role = SelectField('Role', choices=[
        ('BHW', 'Barangay Health Worker'),
        ('Admin', 'Administrator'),
        ('Viewer', 'Viewer'),
        ('Supervisor', 'Barangay Supervisor'),
        ('Nurse', 'Barangay Nurse'),
        ('Midwife', 'Barangay Midwife')
    ], validators=[DataRequired()])
    title = StringField('Official Title (e.g. Barangay Captain)', validators=[Length(max=50)])
    barangay_id = SelectField('Barangay', coerce=int)
    bhw_code = StringField('Username (Required for BHW)', validators=[Length(max=20)])
    contact_number = StringField('Contact Number', validators=[Length(max=20)])
    assigned_sitio = SelectField('Assigned Sitio', validators=[DataRequired()])
    bio = TextAreaField('Short Biography', validators=[Length(max=300)])
    pin = PasswordField('PIN (4 digits for BHW)', validators=[Length(min=0, max=4)])
    password = PasswordField('Password (For Login)', validators=[Length(min=0, max=60)])
    submit = SubmitField('Save Profile')

class BarangayForm(FlaskForm):
    name = StringField('Barangay Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Barangay')

class SitioForm(FlaskForm):
    name = StringField('Sitio Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Add Sitio')

class VisitForm(FlaskForm):
    notes = TextAreaField('Visit Notes')
    health_remarks = TextAreaField('Health Remarks (BP, Symptoms, Vaccination Status)', validators=[DataRequired()])
    follow_up_needed = SelectField('Follow-up Needed?', choices=[(0, 'No'), (1, 'Yes')], coerce=int)
    submit = SubmitField('Record Visit')

class PatientForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    sex = SelectField('Sex', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    birthdate = DateField('Birthdate', validators=[DataRequired()])
    barangay_id = SelectField('Barangay', coerce=int)
    sitio = SelectField('Sitio', validate_choice=False)
    household_name = StringField('Household/Family Name (e.g. Dela Cruz Family)', validators=[DataRequired(), Length(max=100)])
    civil_status = SelectField('Civil Status', choices=[('Single', 'Single'), ('Married', 'Married'), ('Widowed', 'Widowed'), ('Separated', 'Separated')], validators=[DataRequired()])
    contact = StringField('Contact Number')
    submit = SubmitField('Save Patient')

class ConsultationForm(FlaskForm):
    complaints = TextAreaField('Complaints', validators=[DataRequired()])
    diagnosis = TextAreaField('Diagnosis')
    treatment = TextAreaField('Treatment/Medicine Given')
    submit = SubmitField('Save Consultation')

class ImmunizationForm(FlaskForm):
    vaccine = StringField('Vaccine Name', validators=[DataRequired()])
    dose = IntegerField('Dose #', validators=[DataRequired()])
    date_administered = DateField('Date Administered', validators=[DataRequired()])
    remarks = StringField('Remarks')
    submit = SubmitField('Add Record')

class MedicineForm(FlaskForm):
    name = StringField('Medicine Brand Name', validators=[DataRequired()])
    generic_name = StringField('Generic Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    expiry_date = DateField('Expiry Date', validators=[DataRequired()])
    submit = SubmitField('Save Medicine')
