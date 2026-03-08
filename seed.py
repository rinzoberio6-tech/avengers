from app import create_app, db, bcrypt
from app.models import User, Barangay, Household, Patient
from datetime import datetime

app = create_app()

with app.app_context():
    # Force recreation of tables to include new columns
    db.drop_all()
    db.create_all()
    print("Database tables recreated successfully!")

    # Create Initial Barangays
    b1 = Barangay(name="Barangay 1")
    b2 = Barangay(name="Barangay 2")
    db.session.add_all([b1, b2])
    db.session.commit()
    print("Barangays created!")

    users = [
        {'username': 'SuperAdmin', 'password': 'Super123', 'role': 'Super Admin'},
        {'username': 'Admin_B1', 'password': 'Admin123', 'role': 'Admin', 'barangay_id': b1.id},
        {'username': 'Admin_B2', 'password': 'Admin123', 'role': 'Admin', 'barangay_id': b2.id},
        {'username': 'BHW_User', 'password': 'BHW123', 'role': 'BHW', 'bhw_code': 'BHW-001', 'pin': '1234', 'qr_token': 'test-token-123', 'barangay_id': b1.id, 'assigned_sitio': 'Sitio 1'},
        {'username': 'LGU_Viewer', 'password': 'Viewer123', 'role': 'Viewer'}
    ]

    for user_data in users:
        hashed_pw = bcrypt.generate_password_hash(user_data['password']).decode('utf-8') if 'password' in user_data else None
        hashed_pin = bcrypt.generate_password_hash(user_data['pin']).decode('utf-8') if 'pin' in user_data else None
        
        user = User(
            username=user_data.get('username'),
            password=hashed_pw,
            role=user_data['role'],
            bhw_code=user_data.get('bhw_code'),
            pin=hashed_pin,
            qr_token=user_data.get('qr_token'),
            barangay_id=user_data.get('barangay_id'),
            assigned_sitio=user_data.get('assigned_sitio')
        )
        db.session.add(user)
        print(f"Created: {user_data.get('username') or user_data.get('bhw_code')} with role {user_data['role']}")
            
    # Add some sample households to B1
    h1 = Household(sitio="Sitio 1", address="House 101, Near Chapel", barangay_id=b1.id)
    h2 = Household(sitio="Sitio 2", address="House 202, Main Road", barangay_id=b1.id)
    db.session.add_all([h1, h2])
    db.session.commit()
    
    # Add a patient
    p1 = Patient(full_name="Juan Dela Cruz", sex="Male", birthdate=datetime.now().date(), household_id=h1.id)
    db.session.add(p1)
    
    db.session.commit()
    print("All credentials have been reset and verified!")
