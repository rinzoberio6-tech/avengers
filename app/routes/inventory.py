from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from app.models import Medicine
from app.forms import MedicineForm

inventory = Blueprint('inventory', __name__)

@inventory.route('/inventory', methods=['GET', 'POST'])
@login_required
def list_inventory():
    form = MedicineForm()
    if form.validate_on_submit():
        med = Medicine(
            name=form.name.data,
            generic_name=form.generic_name.data,
            quantity=form.quantity.data,
            expiry_date=form.expiry_date.data
        )
        db.session.add(med)
        db.session.commit()
        flash('Medicine added to inventory!', 'success')
        return redirect(url_for('inventory.list_inventory'))
    
    all_medicines = Medicine.query.order_by(Medicine.name).all()
    return render_template('inventory/list.html', title='Inventory', medicines=all_medicines, form=form)

@inventory.route('/inventory/delete/<int:med_id>')
@login_required
def delete_medicine(med_id):
    if current_user.role != 'Admin':
        flash('Only admins can delete inventory items.', 'danger')
        return redirect(url_for('inventory.list_inventory'))
    med = Medicine.query.get_or_404(med_id)
    db.session.delete(med)
    db.session.commit()
    flash('Medicine removed from inventory.', 'info')
    return redirect(url_for('inventory.list_inventory'))
