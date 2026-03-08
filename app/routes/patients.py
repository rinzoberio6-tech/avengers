from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from app.models import Patient, Household, Immunization, Visit, Sitio, Barangay
from app.forms import PatientForm, ImmunizationForm, VisitForm

patients = Blueprint('patients', __name__)

@patients.route('/households')
@login_required
def list_households():
    if current_user.role == 'Super Admin':
        households = Household.query.all()
    else:
        households = Household.query.filter_by(barangay_id=current_user.barangay_id).all()
    return render_template('patients/list_households.html', title='Households', households=households)

@patients.route('/household/<int:h_id>/delete', methods=['POST'])
@login_required
def delete_household(h_id):
    if current_user.role not in ['Admin', 'Super Admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('patients.list_households'))
    
    household = Household.query.get_or_404(h_id)
    
    if current_user.role == 'Admin' and household.barangay_id != current_user.barangay_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('patients.list_households'))

    if len(household.patients) > 0:
        flash('Cannot delete household while it still has residents registered.', 'danger')
        return redirect(url_for('patients.list_households'))
        
    # Delete related visits before deleting the household
    for visit in household.visits:
        db.session.delete(visit)
        
    db.session.delete(household)
    db.session.commit()
    flash('Household record has been deleted.', 'info')
    return redirect(url_for('patients.list_households'))

@patients.route('/household/<int:h_id>')
@login_required
def view_household(h_id):
    household = Household.query.get_or_404(h_id)
    if current_user.role != 'Super Admin' and household.barangay_id != current_user.barangay_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('patients.list_households'))
    
    visit_form = VisitForm()
    return render_template('patients/view_household.html', title=f"Household {household.id}", household=household, visit_form=visit_form)

@patients.route('/household/<int:h_id>/record_visit', methods=['POST'])
@login_required
def record_visit(h_id):
    if current_user.role != 'BHW':
        flash('Only BHWs can record visits.', 'danger')
        return redirect(url_for('patients.view_household', h_id=h_id))
    
    household = Household.query.get_or_404(h_id)
    form = VisitForm()
    if form.validate_on_submit():
        visit = Visit(
            household_id=household.id,
            bhw_id=current_user.id,
            notes=form.notes.data,
            health_remarks=form.health_remarks.data,
            follow_up_needed=bool(form.follow_up_needed.data)
        )
        db.session.add(visit)
        db.session.commit()
        flash('Visit recorded successfully!', 'success')
    return redirect(url_for('patients.view_household', h_id=h_id))

@patients.route('/patient/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if user has permission
    if current_user.role == 'Viewer':
        flash('Access denied.', 'danger')
        return redirect(url_for('patients.list_patients'))
        
    if current_user.role != 'Super Admin' and patient.household.barangay_id != current_user.barangay_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('patients.list_patients'))

    form = PatientForm()
    
    # Setup Barangay choices
    if current_user.role == 'Super Admin':
        barangays = Barangay.query.all()
        form.barangay_id.choices = [(b.id, b.name) for b in barangays]
    else:
        form.barangay_id.choices = [(current_user.barangay.id, current_user.barangay.name)]

    # Populate Sitio choices based on the patient's current barangay
    target_barangay_id = patient.household.barangay_id
    sitios = Sitio.query.filter_by(barangay_id=target_barangay_id).all()
    if sitios:
        form.sitio.choices = [(s.name, s.name) for s in sitios]
    else:
        form.sitio.choices = [('N/A', 'No Sitios Registered')]
    
    if form.validate_on_submit():
        patient.full_name = form.full_name.data
        patient.sex = form.sex.data
        patient.birthdate = form.birthdate.data
        patient.civil_status = form.civil_status.data
        patient.contact = form.contact.data
        
        # Also update the household's sitio/address and barangay
        patient.household.sitio = form.sitio.data
        patient.household.address = form.sitio.data
        patient.household.barangay_id = form.barangay_id.data
        
        db.session.commit()
        flash('Resident profile updated successfully!', 'success')
        return redirect(url_for('patients.list_patients'))
    
    elif request.method == 'GET':
        form.full_name.data = patient.full_name
        form.sex.data = patient.sex
        form.birthdate.data = patient.birthdate
        form.civil_status.data = patient.civil_status
        form.contact.data = patient.contact
        form.barangay_id.data = patient.household.barangay_id
        form.sitio.data = patient.household.sitio
        
    return render_template('patients/list.html', title='Edit Resident', form=form, edit_mode=True, patient_to_edit=patient, patients=get_patients_list())

def get_patients_list():
    if current_user.role == 'Super Admin':
        return Patient.query.order_by(Patient.id.desc()).all()
    else:
        return Patient.query.join(Household).filter(Household.barangay_id == current_user.barangay_id).order_by(Patient.id.desc()).all()

@patients.route('/patients', methods=['GET', 'POST'])
@login_required
def list_patients():
    form = PatientForm()
    
    # Setup Barangay choices
    if current_user.role == 'Super Admin':
        barangays = Barangay.query.all()
        form.barangay_id.choices = [(0, '-- Select Barangay --')] + [(b.id, b.name) for b in barangays]
    else:
        form.barangay_id.choices = [(current_user.barangay.id, current_user.barangay.name)]
    
    # Initial Sitio population (will be updated by JS)
    if current_user.role != 'Super Admin':
        sitios = Sitio.query.filter_by(barangay_id=current_user.barangay_id).all()
        if sitios:
            form.sitio.choices = [(s.name, s.name) for s in sitios]
        else:
            form.sitio.choices = [('N/A', 'No Sitios Registered')]
    else:
        form.sitio.choices = [('', 'Select Barangay first')]

    if form.validate_on_submit():
        if not form.sitio.data or form.sitio.data in ['', 'N/A']:
            flash('Please select a valid Sitio.', 'danger')
            return redirect(url_for('patients.list_patients'))
            
        if current_user.role == 'BHW':
            flash('BHWs cannot create new households directly.', 'danger')
            return redirect(url_for('patients.list_patients'))
            
        target_barangay_id = form.barangay_id.data if current_user.role == 'Super Admin' else current_user.barangay_id
        
        if target_barangay_id == 0:
            flash('Please select a valid Barangay.', 'danger')
            return redirect(url_for('patients.list_patients'))

        # Search for Sitio object to get ID
        selected_sitio_name = form.sitio.data
        sitio_obj = Sitio.query.filter_by(name=selected_sitio_name, barangay_id=target_barangay_id).first()
        
        # 1. Smart Search: Look for existing household with same name in same Sitio
        h_name = form.household_name.data.strip()
        household = Household.query.filter(
            Household.household_name == h_name,
            Household.sitio == selected_sitio_name,
            Household.barangay_id == target_barangay_id
        ).first()

        if not household:
            # Create a new household if it doesn't exist
            household = Household(
                household_name=h_name,
                sitio=selected_sitio_name, 
                sitio_id=sitio_obj.id if sitio_obj else None,
                address=selected_sitio_name, 
                barangay_id=target_barangay_id
            )
            db.session.add(household)
            db.session.commit()
        
        patient = Patient(
            full_name=form.full_name.data,
            sex=form.sex.data,
            birthdate=form.birthdate.data,
            civil_status=form.civil_status.data,
            contact=form.contact.data,
            household_id=household.id
        )
        db.session.add(patient)
        db.session.commit()
        flash(f'Patient registered under {household.household_name}!', 'success')
        return redirect(url_for('patients.list_patients'))
        if current_user.role == 'BHW':
            flash('BHWs cannot create new households directly. Please contact your Admin.', 'danger')
            return redirect(url_for('patients.list_patients'))
            
        # Create a new household for the patient
        household = Household(sitio=form.sitio.data, address=form.sitio.data, barangay_id=current_user.barangay_id)
        db.session.add(household)
        db.session.commit()
        
        patient = Patient(
            full_name=form.full_name.data,
            sex=form.sex.data,
            birthdate=form.birthdate.data,
            civil_status=form.civil_status.data,
            contact=form.contact.data,
            household_id=household.id
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient and Household registered successfully!', 'success')
        return redirect(url_for('patients.list_patients'))
    
    if current_user.role == 'Super Admin':
        all_patients = Patient.query.order_by(Patient.id.desc()).all()
    else:
        # Filter patients by barangay
        all_patients = Patient.query.join(Household).filter(Household.barangay_id == current_user.barangay_id).order_by(Patient.id.desc()).all()
        
    return render_template('patients/list.html', title='Patients', patients=all_patients, form=form)

@patients.route('/patient/register', methods=['GET', 'POST'])
@login_required
def register_patient():
    return redirect(url_for('patients.list_patients'))

@patients.route('/patient/<int:patient_id>')
@login_required
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    imm_form = ImmunizationForm()
    return render_template('patients/view.html', title=patient.full_name, patient=patient, imm_form=imm_form)

@patients.route('/patient/<int:patient_id>/delete', methods=['POST'])
@login_required
def delete_patient(patient_id):
    if current_user.role not in ['Admin', 'Super Admin']:
        flash('Access denied. Only admins can delete resident records.', 'danger')
        return redirect(url_for('patients.list_patients'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if admin belongs to same barangay
    if current_user.role == 'Admin' and patient.household.barangay_id != current_user.barangay_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('patients.list_patients'))

    # Delete related records (optional depending on DB cascading, but safe to do)
    for imm in patient.immunizations:
        db.session.delete(imm)
    for consult in patient.consultations:
        db.session.delete(consult)
        
    db.session.delete(patient)
    db.session.commit()
    flash('Resident record has been permanently deleted.', 'info')
    return redirect(url_for('patients.list_patients'))

@patients.route('/patient/<int:patient_id>/add_immunization', methods=['POST'])
@login_required
def add_immunization(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = ImmunizationForm()
    if form.validate_on_submit():
        imm = Immunization(
            patient_id=patient.id,
            vaccine=form.vaccine.data,
            dose=form.dose.data,
            date_administered=form.date_administered.data,
            remarks=form.remarks.data
        )
        db.session.add(imm)
        db.session.commit()
        flash('Immunization record added!', 'success')
    return redirect(url_for('patients.view_patient', patient_id=patient.id))
