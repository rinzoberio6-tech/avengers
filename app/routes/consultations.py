from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from app.models import Patient, Consultation
from app.forms import ConsultationForm

consultations = Blueprint('consultations', __name__)

@consultations.route('/consultations')
@login_required
def list_consultations():
    all_consultations = Consultation.query.order_by(Consultation.date.desc()).all()
    return render_template('consultations/list.html', title='Consultations', consultations=all_consultations)

@consultations.route('/patient/<int:patient_id>/consult', methods=['GET', 'POST'])
@login_required
def add_consultation(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = ConsultationForm()
    if form.validate_on_submit():
        consult = Consultation(
            patient_id=patient.id,
            complaints=form.complaints.data,
            diagnosis=form.diagnosis.data,
            treatment=form.treatment.data,
            created_by=current_user.username
        )
        db.session.add(consult)
        db.session.commit()
        flash('Consultation record saved!', 'success')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))
    return render_template('consultations/add.html', title='New Consultation', form=form, patient=patient)
