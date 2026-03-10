from flask import Blueprint, render_template, redirect, url_for, jsonify, flash, request
from flask_login import login_required, current_user, logout_user
from app.models import Patient, Consultation, Medicine, Immunization, User, Barangay, Visit, Household, Sitio
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db, bcrypt

main = Blueprint('main', __name__)

@main.route('/system/reset', methods=['GET', 'POST'])
def system_reset():
    try:
        # Check if any users exist safely
        user_count = db.session.query(User).count()
    except Exception:
        user_count = 0

    # If users exist, ONLY a logged-in Super Admin can use this via POST
    if user_count > 0:
        if not current_user.is_authenticated or current_user.role != 'Super Admin' or request.method == 'GET':
            return redirect(url_for('auth.login'))

    try:
        # Close all existing connections to avoid locks
        db.session.remove()
        db.engine.dispose()

        # Drop and Recreate tables
        db.drop_all()
        db.create_all()

        # Recreate Super Admin
        hashed_pw = bcrypt.generate_password_hash('Super123').decode('utf-8')
        super_admin = User(
            username='SuperAdmin',
            password=hashed_pw,
            role='Super Admin',
            is_active=True
        )
        db.session.add(super_admin)
        db.session.commit()

        if current_user.is_authenticated:
            logout_user()

        flash('System Initialized! Login with SuperAdmin / Super123', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        print(f"Reset Error: {e}")
        flash('An error occurred during reset. Check logs.', 'danger')
        return redirect(url_for('auth.login'))

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='Welcome')

@main.route('/dashboard')
@login_required
def dashboard():
    # Role-based dashboard data
    if current_user.role == 'Super Admin':
        total_barangays = Barangay.query.count()
        active_barangays = Barangay.query.filter_by(is_active=True).count()
        total_users = User.query.count()
        total_patients = Patient.query.count()
        return render_template('dashboard_superadmin.html', 
                               title='System Owner Dashboard',
                               total_barangays=total_barangays,
                               active_barangays=active_barangays,
                               total_users=total_users,
                               total_patients=total_patients)

    elif current_user.role == 'Admin':
        # Barangay Admin logic
        patient_count = Patient.query.join(Household).filter(Household.barangay_id == current_user.barangay_id).count()
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        consultation_today = Consultation.query.join(Patient).join(Household).filter(Household.barangay_id == current_user.barangay_id, Consultation.date >= today_start).count()
        
        low_stock_count = Medicine.query.filter(Medicine.quantity <= 20).count()
        
        # Real Alert Logic
        alerts = []
        low_stock_item = Medicine.query.filter(Medicine.quantity <= 20).order_by(Medicine.quantity.asc()).first()
        if low_stock_item:
            alerts.append({'type': 'danger', 'msg': f'Medicine "{low_stock_item.name}" is almost out ({low_stock_item.quantity} left).'})
        
        if datetime.now().day <= 7:
            alerts.append({'type': 'info', 'msg': f'Monthly reports for {datetime.now().strftime("%B")} are now ready.'})
        
        # Active BHWs (last seen within 30 mins)
        active_bhws = User.query.filter(
            User.barangay_id == current_user.barangay_id,
            User.role == 'BHW',
            User.last_seen >= datetime.now() - timedelta(minutes=30)
        ).count()

        recent_consultations = Consultation.query.join(Patient).join(Household).filter(Household.barangay_id == current_user.barangay_id).order_by(Consultation.date.desc()).limit(5).all()
        
        return render_template('dashboard.html', 
                               title='Admin Dashboard',
                               patient_count=patient_count,
                               consultation_today=consultation_today,
                               low_stock=low_stock_count,
                               active_bhws=active_bhws,
                               alerts=alerts,
                               recent_consultations=recent_consultations,
                               now=datetime.now())

    elif current_user.role == 'BHW':
        # BHW Dashboard - Personal Stats
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)
        
        visits_today = Visit.query.filter(Visit.bhw_id == current_user.id, Visit.date_visited >= today_start).count()
        visits_month = Visit.query.filter(Visit.bhw_id == current_user.id, Visit.date_visited >= month_start).count()
        
        # Get recent visits for history
        recent_visits = Visit.query.filter_by(bhw_id=current_user.id).order_by(Visit.date_visited.desc()).limit(10).all()
        
        return render_template('dashboard_bhw.html',
                               title='BHW Dashboard',
                               visits_today=visits_today,
                               visits_month=visits_month,
                               recent_visits=recent_visits,
                               user=current_user)

    # For Viewer or others
    return render_template('dashboard.html', title='Dashboard')

@main.route('/api/analytics')
@login_required
def get_analytics():
    data = {}
    
    if current_user.role == 'Super Admin':
        # 1. Line Graph: Global Consultations per month (Last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Use a cross-platform way to format dates
        if db.engine.name == 'postgresql':
            date_format = func.to_char(Consultation.date, 'YYYY-MM')
        else:
            date_format = func.strftime('%Y-%m', Consultation.date)

        consultations_by_month = db.session.query(
            date_format.label('month'),
            func.count(Consultation.id)
        ).filter(Consultation.date >= six_months_ago)\
         .group_by('month').order_by('month').all()
        
        data['line_graph'] = {
            'labels': [row[0] for row in consultations_by_month],
            'datasets': [{
                'label': 'Global Consultations',
                'data': [row[1] for row in consultations_by_month],
                'borderColor': '#2ecc71',
                'tension': 0.3
            }]
        }
        
        # 2. Bar Graph: Patients per Barangay
        patients_by_barangay = db.session.query(
            Barangay.name,
            func.count(Patient.id)
        ).join(Household, Barangay.id == Household.barangay_id)\
         .join(Patient, Household.id == Patient.household_id)\
         .group_by(Barangay.name).all()
        
        data['bar_graph'] = {
            'labels': [row[0] for row in patients_by_barangay],
            'datasets': [{
                'label': 'Resident Count',
                'data': [row[1] for row in patients_by_barangay],
                'backgroundColor': '#3498db'
            }]
        }
        
        # 3. Pie Graph: User Roles
        user_roles = db.session.query(
            User.role,
            func.count(User.id)
        ).group_by(User.role).all()
        
        data['pie_graph'] = {
            'labels': [row[0] for row in user_roles],
            'datasets': [{
                'data': [row[1] for row in user_roles],
                'backgroundColor': ['#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c', '#34495e']
            }]
        }

    elif current_user.role == 'Admin':
        # 1. Line Graph: Barangay Consultations per month
        six_months_ago = datetime.now() - timedelta(days=180)
        
        if db.engine.name == 'postgresql':
            date_format = func.to_char(Consultation.date, 'YYYY-MM')
        else:
            date_format = func.strftime('%Y-%m', Consultation.date)

        consultations_by_month = db.session.query(
            date_format.label('month'),
            func.count(Consultation.id)
        ).join(Patient).join(Household)\
         .filter(Household.barangay_id == current_user.barangay_id, Consultation.date >= six_months_ago)\
         .group_by('month').order_by('month').all()
        
        data['line_graph'] = {
            'labels': [row[0] for row in consultations_by_month],
            'datasets': [{
                'label': 'Barangay Consultations',
                'data': [row[1] for row in consultations_by_month],
                'borderColor': '#3498db',
                'tension': 0.3
            }]
        }
        
        # 2. Bar Graph: Patients by Sex
        patients_by_sex = db.session.query(
            Patient.sex,
            func.count(Patient.id)
        ).join(Household)\
         .filter(Household.barangay_id == current_user.barangay_id)\
         .group_by(Patient.sex).all()
        
        data['bar_graph'] = {
            'labels': [row[0] for row in patients_by_sex],
            'datasets': [{
                'label': 'Residents by Sex',
                'data': [row[1] for row in patients_by_sex],
                'backgroundColor': ['#ff6384', '#36a2eb']
            }]
        }
        
        # 3. Pie Graph: Medicine Quantity (Top 5)
        top_medicines = Medicine.query.order_by(Medicine.quantity.desc()).limit(5).all()
        
        data['pie_graph'] = {
            'labels': [m.name for m in top_medicines],
            'datasets': [{
                'data': [m.quantity for m in top_medicines],
                'backgroundColor': ['#2ecc71', '#e67e22', '#e74c3c', '#3498db', '#9b59b6']
            }]
        }
        
    return jsonify(data)

@main.route('/api/barangay/<int:b_id>/sitios')
@login_required
def get_barangay_sitios(b_id):
    sitios = Sitio.query.filter_by(barangay_id=b_id).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in sitios])

@main.route('/help')
@login_required
def help():
    return render_template('help.html', title='Help & Support')
