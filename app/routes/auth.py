from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User, Barangay, Patient, Household, Visit, Sitio
from app.forms import LoginForm, BHWLoginForm, PINForm, UserRegistrationForm, BarangayForm, SitioForm
import secrets

from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/admin/barangays', methods=['GET', 'POST'])
@login_required
def list_barangays():
    if current_user.role not in ['Super Admin', 'Admin']:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = BarangayForm()
    sitio_form = SitioForm()
    
    if current_user.role == 'Super Admin' and form.validate_on_submit():
        barangay = Barangay(name=form.name.data)
        db.session.add(barangay)
        db.session.commit()
        flash('Barangay added successfully!', 'success')
        return redirect(url_for('auth.list_barangays'))
    
    barangays_data = []
    if current_user.role == 'Super Admin':
        all_barangays = Barangay.query.all()
    else:
        all_barangays = [current_user.barangay]
    
    # Calculate stats for each barangay
    today = datetime.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    for b in all_barangays:
        if not b: continue
        # 1. Total Residents
        res_count = Patient.query.join(Household).filter(Household.barangay_id == b.id).count()
        
        # 2. Total Households
        hh_count = Household.query.filter_by(barangay_id=b.id).count()
        
        # 3. Monthly Visits
        visit_count = Visit.query.join(Household).filter(Household.barangay_id == b.id, Visit.date_visited >= month_start).count()
        
        # 4. Assigned Admin
        admin_user = User.query.filter_by(barangay_id=b.id, role='Admin').first()
        
        # 5. Milestone Calculation
        visited_hh_count = db.session.query(Visit.household_id).join(Household).filter(
            Household.barangay_id == b.id, 
            Visit.date_visited >= month_start
        ).distinct().count()
        
        milestone = (visited_hh_count / hh_count * 100) if hh_count > 0 else 0
        
        barangays_data.append({
            'obj': b,
            'residents': res_count,
            'households': hh_count,
            'visits': visit_count,
            'admin': admin_user.username if admin_user else 'None Assigned',
            'milestone': round(milestone, 1),
            'sitios': b.sitios
        })
        
    return render_template('auth/list_barangays.html', title='Manage Barangays', barangays=barangays_data, form=form, sitio_form=sitio_form)

@auth.route('/admin/barangay/<int:b_id>/add_sitio', methods=['POST'])
@login_required
def add_sitio(b_id):
    if current_user.role not in ['Super Admin', 'Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Regular Admin can only add sitios to their own barangay
    if current_user.role == 'Admin' and current_user.barangay_id != b_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.list_barangays'))

    barangay = Barangay.query.get_or_404(b_id)
    form = SitioForm()
    if form.validate_on_submit():
        sitio = Sitio(name=form.name.data, barangay_id=b_id)
        db.session.add(sitio)
        db.session.commit()
        flash(f'Sitio "{form.name.data}" added to {barangay.name}.', 'success')
    return redirect(url_for('auth.list_barangays'))

@auth.route('/admin/sitio/<int:s_id>/edit', methods=['POST'])
@login_required
def edit_sitio(s_id):
    sitio = Sitio.query.get_or_404(s_id)
    
    if current_user.role == 'Admin' and current_user.barangay_id != sitio.barangay_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.list_barangays'))
    
    if current_user.role not in ['Super Admin', 'Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    new_name = request.form.get('name')
    if new_name:
        sitio.name = new_name
        db.session.commit()
        flash(f'Sitio renamed to "{new_name}".', 'success')
    return redirect(url_for('auth.list_barangays'))

@auth.route('/admin/sitio/<int:s_id>/delete', methods=['POST'])
@login_required
def delete_sitio(s_id):
    sitio = Sitio.query.get_or_404(s_id)
    
    if current_user.role == 'Admin' and current_user.barangay_id != sitio.barangay_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.list_barangays'))

    if current_user.role not in ['Super Admin', 'Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    name = sitio.name
    db.session.delete(sitio)
    db.session.commit()
    flash(f'Sitio "{name}" removed.', 'info')
    return redirect(url_for('auth.list_barangays'))

@auth.route('/admin/barangay/<int:b_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_barangay(b_id):
    if current_user.role != 'Super Admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    barangay = Barangay.query.get_or_404(b_id)
    form = BarangayForm()
    
    if form.validate_on_submit():
        barangay.name = form.name.data
        db.session.commit()
        flash('Barangay updated successfully!', 'success')
        return redirect(url_for('auth.list_barangays'))
    
    elif request.method == 'GET':
        form.name.data = barangay.name
    
    sitio_form = SitioForm()
    return render_template('auth/list_barangays.html', title='Edit Barangay', form=form, sitio_form=sitio_form, edit_mode=True, barangay_to_edit=barangay, barangays=get_barangays_data())

@auth.route('/admin/barangay/<int:b_id>/delete', methods=['POST'])
@login_required
def delete_barangay(b_id):
    if current_user.role != 'Super Admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    barangay = Barangay.query.get_or_404(b_id)
    
    # Check if there are users or households linked to this barangay
    if User.query.filter_by(barangay_id=b_id).first() or Household.query.filter_by(barangay_id=b_id).first():
        flash('Cannot delete barangay because it has linked users or households.', 'danger')
        return redirect(url_for('auth.list_barangays'))
        
    db.session.delete(barangay)
    db.session.commit()
    flash('Barangay deleted successfully!', 'info')
    return redirect(url_for('auth.list_barangays'))

def get_barangays_data():
    barangays_data = []
    all_barangays = Barangay.query.all()
    
    # Calculate stats for each barangay
    today = datetime.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for b in all_barangays:
        res_count = Patient.query.join(Household).filter(Household.barangay_id == b.id).count()
        hh_count = Household.query.filter_by(barangay_id=b.id).count()
        visit_count = Visit.query.join(Household).filter(Household.barangay_id == b.id, Visit.date_visited >= month_start).count()
        admin = User.query.filter_by(barangay_id=b.id, role='Admin').first()
        
        # Milestone Calculation
        visited_hh_count = db.session.query(Visit.household_id).join(Household).filter(
            Household.barangay_id == b.id, 
            Visit.date_visited >= month_start
        ).distinct().count()
        
        milestone = (visited_hh_count / hh_count * 100) if hh_count > 0 else 0

        barangays_data.append({
            'obj': b,
            'residents': res_count,
            'households': hh_count,
            'visits': visit_count,
            'admin': admin.username if admin else 'None Assigned',
            'milestone': round(milestone, 1),
            'sitios': b.sitios
        })
    return barangays_data

@auth.route('/admin/barangay/<int:b_id>/toggle', methods=['POST'])
@login_required
def toggle_barangay(b_id):
    if current_user.role != 'Super Admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    barangay = Barangay.query.get_or_404(b_id)
    barangay.is_active = not barangay.is_active
    db.session.commit()
    status = "activated" if barangay.is_active else "deactivated"
    flash(f'Barangay {barangay.name} has been {status}.', 'info')
    return redirect(url_for('auth.list_barangays'))

@auth.route('/directory')
@login_required
def directory():
    if current_user.role == 'Super Admin':
        personnel = User.query.all()
    else:
        # Others can only see personnel in their barangay
        personnel = User.query.filter_by(barangay_id=current_user.barangay_id).all()
    
    return render_template('auth/directory.html', title='Health Personnel Directory', personnel=personnel)

@auth.route('/personnel/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    # Check if they have access to this profile
    if current_user.role != 'Super Admin' and user.barangay_id != current_user.barangay_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.directory'))
        
    return render_template('auth/profile_view.html', title=f"Profile: {user.username or user.bhw_code}", user=user)

@auth.route('/admin/register_user', methods=['GET', 'POST'])
@login_required
def register_user():
    if current_user.role not in ['Admin', 'Super Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = UserRegistrationForm()
    # Populate barangay choices
    barangays = Barangay.query.all()
    form.barangay_id.choices = [(0, '-- None --')] + [(b.id, b.name) for b in barangays]
    
    # Handle Sitio choices (initial load or validation)
    b_id = form.barangay_id.data
    if b_id and b_id != 0:
        sitios = Sitio.query.filter_by(barangay_id=b_id).all()
        form.assigned_sitio.choices = [(s.name, s.name) for s in sitios]
    else:
        form.assigned_sitio.choices = [('', 'Select Barangay first')]

    if form.validate_on_submit():
        # Hierarchy checks
        if current_user.role == 'Admin' and form.role.data in ['Admin', 'Super Admin']:
            flash('Admins can only create BHW or Viewer accounts.', 'danger')
            return render_template('auth/register_user.html', title='Register User', form=form)
        
        # Check if username or bhw_code already exists
        if form.username.data and User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('auth/register_user.html', title='Register User', form=form)
        
        if form.bhw_code.data and User.query.filter_by(bhw_code=form.bhw_code.data).first():
            flash('BHW Code already exists. Please choose a different one.', 'danger')
            return render_template('auth/register_user.html', title='Register User', form=form)

        # PIN is required for new BHW
        if form.role.data == 'BHW' and not form.pin.data:
            flash('BHW users require a 4-digit PIN.', 'danger')
            return render_template('auth/register_user.html', title='Register User', form=form)

        hashed_password = None
        if form.password.data:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            
        hashed_pin = None
        if form.pin.data:
            hashed_pin = bcrypt.generate_password_hash(form.pin.data).decode('utf-8')
        
        # Generate a random QR token for the new user
        qr_token = secrets.token_hex(16)
        
        user = User(
            username=form.username.data if form.username.data else None,
            password=hashed_password,
            role=form.role.data,
            title=form.title.data,
            bhw_code=form.bhw_code.data if form.bhw_code.data else None,
            pin=hashed_pin,
            qr_token=qr_token,
            barangay_id=form.barangay_id.data if form.barangay_id.data != 0 else None,
            contact_number=form.contact_number.data,
            assigned_sitio=form.assigned_sitio.data,
            bio=form.bio.data
        )
        db.session.add(user)
        db.session.commit()
        flash(f'User created successfully!', 'success')
        return redirect(url_for('auth.list_users'))
        
    return render_template('auth/register_user.html', title='Register User', form=form)

@auth.route('/admin/users')
@login_required
def list_users():
    if current_user.role not in ['Admin', 'Super Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if current_user.role == 'Super Admin':
        users = User.query.all()
    else:
        # Admin can only see users in their barangay
        users = User.query.filter_by(barangay_id=current_user.barangay_id).all()
        
    return render_template('auth/list_users.html', title='User Management', users=users, now=datetime.now())

@auth.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role not in ['Admin', 'Super Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Hierarchy check
    if current_user.role == 'Admin':
        if user.role in ['Admin', 'Super Admin'] or user.barangay_id != current_user.barangay_id:
            flash('You do not have permission to edit this user.', 'danger')
            return redirect(url_for('auth.list_users'))

    form = UserRegistrationForm()
    barangays = Barangay.query.all()
    form.barangay_id.choices = [(0, '-- None --')] + [(b.id, b.name) for b in barangays]
    
    # Handle Sitio choices (Must be populated before validation)
    b_id = form.barangay_id.data if form.barangay_id.data else user.barangay_id
    if b_id and b_id != 0:
        sitios = Sitio.query.filter_by(barangay_id=b_id).all()
        form.assigned_sitio.choices = [('Captain', 'Captain (Barangay Hall)'), ('Viewer', 'Viewer (Guest/Audit)')] + [(s.name, s.name) for s in sitios]
    else:
        form.assigned_sitio.choices = [('Captain', 'Captain (Barangay Hall)'), ('Viewer', 'Viewer (Guest/Audit)')]

    if request.method == 'GET':
        form.username.data = user.username
        form.role.data = user.role
        form.title.data = user.title
        form.bhw_code.data = user.bhw_code
        form.barangay_id.data = user.barangay_id if user.barangay_id else 0
        form.contact_number.data = user.contact_number
        form.assigned_sitio.data = user.assigned_sitio
        form.bio.data = user.bio

    if form.validate_on_submit():
        if form.username.data and form.username.data != user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already taken.', 'danger')
                return render_template('auth/register_user.html', title='Edit User', form=form, user=user)
        
        user.username = form.username.data if form.username.data else None
        user.role = form.role.data
        user.title = form.title.data
        user.bhw_code = form.bhw_code.data if form.bhw_code.data else None
        user.barangay_id = form.barangay_id.data if form.barangay_id.data != 0 else None
        user.contact_number = form.contact_number.data
        user.assigned_sitio = form.assigned_sitio.data
        user.bio = form.bio.data
        
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        if form.pin.data:
            user.pin = bcrypt.generate_password_hash(form.pin.data).decode('utf-8')
            
        db.session.commit()
        flash('User details updated successfully!', 'success')
        return redirect(url_for('auth.list_users'))
        
    return render_template('auth/register_user.html', title='Edit User', form=form, user=user)

@auth.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role not in ['Admin', 'Super Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Hierarchy check
    if current_user.role == 'Admin':
        if user.role in ['Admin', 'Super Admin'] or user.barangay_id != current_user.barangay_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.list_users'))

    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('auth.list_users'))
        
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted.', 'info')
    return redirect(url_for('auth.list_users'))

@auth.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    if current_user.role not in ['Admin', 'Super Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Hierarchy check
    if current_user.role == 'Admin' and user.role in ['Admin', 'Super Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.list_users'))

    user.is_active = not user.is_active
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    flash(f'User {user.username or user.bhw_code} has been {status}.', 'info')
    return redirect(url_for('auth.list_users'))

@auth.route('/admin/user/<int:user_id>/print_id')
@login_required
def print_id(user_id):
    if current_user.role not in ['Admin', 'Super Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    if not user.bhw_code:
        flash('This user does not have a BHW Code.', 'warning')
        return redirect(url_for('auth.list_users'))
        
    qr_url = url_for('auth.qr_login', token=user.qr_token, _external=True)
    return render_template('auth/print_id.html', title='Print ID Card', user=user, qr_url=qr_url)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    admin_form = LoginForm()
    bhw_form = BHWLoginForm()

    # Handle Admin/Super Admin/Viewer Login
    if 'admin_login' in request.form and admin_form.validate_on_submit():
        user = User.query.filter_by(username=admin_form.username.data).first()
        if user and user.password and bcrypt.check_password_hash(user.password, admin_form.password.data):
            if not user.is_active:
                flash('Your account is deactivated. Please contact support.', 'danger')
            elif user.barangay and not user.barangay.is_active:
                flash('Your Barangay is currently deactivated.', 'danger')
            else:
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    # Handle BHW Manual Login
    if 'bhw_login' in request.form and bhw_form.validate_on_submit():
        user = User.query.filter_by(bhw_code=bhw_form.bhw_code.data).first()
        if user and user.pin and bcrypt.check_password_hash(user.pin, bhw_form.pin.data):
            if not user.is_active:
                flash('Your account is deactivated.', 'danger')
            elif user.barangay and not user.barangay.is_active:
                flash('Your Barangay is deactivated.', 'danger')
            else:
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check BHW Code and PIN', 'danger')

    return render_template('auth/login.html', title='Login', admin_form=admin_form, bhw_form=bhw_form)

@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='My Profile', user=current_user)

@auth.route('/qr-login/<token>', methods=['GET', 'POST'])
def qr_login(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    user = User.query.filter_by(qr_token=token).first()
    if not user:
        flash('Invalid QR Code. Please use your BHW Code and PIN.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = PINForm()
    if form.validate_on_submit():
        if user.pin and bcrypt.check_password_hash(user.pin, form.pin.data):
            login_user(user)
            flash(f'Welcome back, {user.bhw_code}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Incorrect PIN. Please try again.', 'danger')
    
    return render_template('auth/pin.html', title='QR Login - Enter PIN', form=form, user=user)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
