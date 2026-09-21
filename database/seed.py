import sqlite3
import os
from werkzeug.security import generate_password_hash

def seed_data(db_path=None):
    if db_path is None:
        if os.environ.get('VERCEL') == '1':
            db_path = '/tmp/database.db'
        else:
            db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'database.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # Clear existing data in reverse order of foreign keys
    tables = [
        'feedback', 'payments', 'invoice_items', 'invoices', 'service_records',
        'notifications', 'appointments', 'vehicles', 'services', 'mechanics',
        'password_resets', 'contact_messages', 'users'
    ]
    for table in tables:
        try:
            cur.execute(f"DELETE FROM {table}")
            cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except sqlite3.OperationalError:
            pass

    # 1. Users (Admin and Customers)
    hashed_admin_pwd = generate_password_hash('admin123')
    hashed_cust_pwd = generate_password_hash('customer123')

    cur.execute("""
        INSERT INTO users (id, full_name, email, phone, password_hash, role, status)
        VALUES 
        (1, 'AutoCare Admin', 'admin@autocare.com', '+1 (555) 019-2834', ?, 'admin', 'active'),
        (2, 'John Doe', 'john@example.com', '+1 (555) 432-8765', ?, 'customer', 'active'),
        (3, 'Sarah Jenkins', 'sarah@example.com', '+1 (555) 890-1234', ?, 'customer', 'active'),
        (4, 'Michael Chang', 'michael@example.com', '+1 (555) 789-4561', ?, 'customer', 'active')
    """, (hashed_admin_pwd, hashed_cust_pwd, hashed_cust_pwd, hashed_cust_pwd))

    # 2. Mechanics
    cur.execute("""
        INSERT INTO mechanics (id, name, email, phone, specialization, experience_years, availability, status)
        VALUES
        (1, 'Robert Vance', 'robert.vance@autocare.com', '+1 (555) 301-1122', 'Engine & Transmission Specialist', 12, 'available', 'active'),
        (2, 'Elena Rodriguez', 'elena.r@autocare.com', '+1 (555) 301-2233', 'Electrical Systems & Hybrid/EV Tech', 8, 'on_job', 'active'),
        (3, 'Marcus Brody', 'marcus.b@autocare.com', '+1 (555) 301-3344', 'Brakes, Suspension & Wheel Alignment', 10, 'on_job', 'active'),
        (4, 'David Kim', 'david.k@autocare.com', '+1 (555) 301-4455', 'Master Diagnostic & Computer Tuning', 14, 'available', 'active'),
        (5, 'Siddharth Patel', 'siddharth.p@autocare.com', '+1 (555) 301-5566', 'HVAC, Cooling & General Maintenance', 6, 'available', 'active')
    """)

    # 3. Services (9 standard services)
    cur.execute("""
        INSERT INTO services (id, service_name, category, description, estimated_price, estimated_duration, icon, status)
        VALUES
        (1, 'General Service', 'Maintenance', 'Full 50-point bumper-to-bumper vehicle inspection, vital fluids top-up, spark plug check, engine diagnostic scan, and road test.', 149.00, '2 Hours', 'wrench', 'active'),
        (2, 'Oil Change', 'Maintenance', 'Complete oil drain, synthetic motor oil refill (up to 5 quarts), OEM oil filter replacement, and chassis lubrication.', 79.00, '45 Mins', 'droplet', 'active'),
        (3, 'Brake Service', 'Mechanical', 'Front and rear brake pad inspection and replacement, rotor resurfacing, brake fluid flush, and caliper inspection.', 189.00, '1.5 Hours', 'disc', 'active'),
        (4, 'Engine Repair', 'Mechanical', 'Engine timing diagnosis, spark plug replacement, fuel injector cleaning, compression test, and computer error reset.', 349.00, '4 Hours', 'cpu', 'active'),
        (5, 'Battery Service', 'Electrical', 'Computerized load testing, terminal cleaning, anti-corrosion spray, alternator output verification, and battery installation.', 129.00, '30 Mins', 'zap', 'active'),
        (6, 'AC Service', 'Climate', 'Air conditioning refrigerant recovery and recharge, evaporator core sanitize, leak detection, and cabin air filter change.', 119.00, '1 Hour', 'wind', 'active'),
        (7, 'Tyre Service', 'Wheels', 'Digital 4-wheel dynamic balancing, tire rotation, valve stem inspection, tread depth assessment, and puncture check.', 69.00, '45 Mins', 'circle', 'active'),
        (8, 'Car Wash & Detailing', 'Detailing', 'High-pressure foam exterior wash, hand clay bar decontaminate, interior deep vacuum, leather condition, and tire shine.', 49.00, '1 Hour', 'sparkles', 'active'),
        (9, 'Wheel Alignment', 'Wheels', 'High-precision 3D computerized laser wheel alignment, camber and caster calibration, and steering center adjustment.', 89.00, '1 Hour', 'crosshair', 'active')
    """)

    # 4. Vehicles
    cur.execute("""
        INSERT INTO vehicles (id, user_id, vehicle_number, brand, model, year, fuel_type, vehicle_type, color, current_mileage)
        VALUES
        (1, 2, 'NY-7892-AB', 'BMW', '330i', 2022, 'Petrol', 'Sedan', 'Alpine White', 24500),
        (2, 2, 'CA-5421-TX', 'Ford', 'F-150 Lariat', 2021, 'Diesel', 'Truck', 'Shadow Black', 42100),
        (3, 3, 'TX-9012-ZZ', 'Tesla', 'Model 3 LR', 2023, 'Electric', 'Sedan', 'Pearl White', 15200),
        (4, 3, 'FL-3388-GH', 'Honda', 'CR-V Touring', 2020, 'Petrol', 'SUV', 'Sonic Gray', 38900),
        (5, 4, 'WA-4411-MN', 'Toyota', 'Camry Hybrid', 2021, 'Hybrid', 'Sedan', 'Celestial Silver', 31000)
    """)

    # 5. Appointments
    cur.execute("""
        INSERT INTO appointments (id, appointment_code, user_id, vehicle_id, service_id, mechanic_id, appointment_date, time_slot, problem_description, status, estimated_completion, technician_notes, total_amount)
        VALUES
        (1, 'APT-202609-001', 2, 1, 2, 1, '2026-09-10', '10:00 AM - 11:00 AM', 'Routine 25k synthetic oil change and filter replacement.', 'Completed', '2026-09-10 11:30 AM', 'Installed Castrol Edge 5W-30 Full Synthetic Oil and Mann Filter. Vehicle checked all clear.', 104.00),
        (2, 'APT-202609-002', 2, 2, 3, 3, '2026-09-20', '02:00 PM - 03:30 PM', 'Slight squeaking sound heard when applying brakes at low speed.', 'In Service', 'Today 04:30 PM', 'Inspected front brake rotors. Replacing pads with OEM ceramic pads.', 189.00),
        (3, 'APT-202609-003', 2, 1, 8, 4, '2026-09-21', '09:00 AM - 10:00 AM', 'Full interior detail and exterior clay bar polishing.', 'Ready for Pickup', 'Today 11:00 AM', 'Car wash and detailing completed. Vehicle parked at Bay 3.', 49.00),
        (4, 'APT-202609-004', 3, 3, 1, 2, '2026-09-22', '11:00 AM - 01:00 PM', 'Annual EV system check, brake fluid moisture test, and tire inspection.', 'Confirmed', '2026-09-22 01:30 PM', 'Technician Elena assigned to bay.', 149.00),
        (5, 'APT-202609-005', 3, 4, 6, 5, '2026-09-08', '03:00 PM - 04:00 PM', 'AC blowing lukewarm air during hot afternoons.', 'Completed', '2026-09-08 04:30 PM', 'Recharged R134a refrigerant and replaced cabin air filter.', 154.00),
        (6, 'APT-202609-006', 4, 5, 9, NULL, '2026-09-25', '01:00 PM - 02:00 PM', 'Steering pulls slightly to the left on highway speeds.', 'Pending', 'Pending Inspection', 'Awaiting service advisor confirmation.', 89.00)
    """)

    # 6. Service Records (for completed appointments)
    cur.execute("""
        INSERT INTO service_records (id, appointment_id, vehicle_id, mechanic_id, service_date, parts_replaced, labor_details, parts_cost, labor_cost, total_cost, technician_notes)
        VALUES
        (1, 1, 1, 1, '2026-09-10', 'Full Synthetic Oil 5W-30 (5 Qts), OEM Oil Filter, Drain Plug Washer', 'Oil drain, filter swap, safety inspection', 35.00, 69.00, 104.00, 'All systems normal. Next service recommended in 8,000 km.'),
        (2, 5, 4, 5, '2026-09-08', 'R134a AC Refrigerant (500g), Premium HEPA Cabin Air Filter', 'System vacuum test, leak test, refrigerant recharge', 45.00, 109.00, 154.00, 'AC cooling restored to 42°F at center vent.')
    """)

    # 7. Invoices
    cur.execute("""
        INSERT INTO invoices (id, invoice_number, appointment_id, user_id, vehicle_id, subtotal, tax_rate, tax_amount, discount_amount, final_amount, payment_status, payment_method, paid_at)
        VALUES
        (1, 'INV-202609-001', 1, 2, 1, 104.00, 10.0, 10.40, 10.00, 104.40, 'Paid', 'Card', '2026-09-10 11:45:00'),
        (2, 'INV-202609-002', 3, 2, 1, 49.00, 10.0, 4.90, 0.00, 53.90, 'Pending', NULL, NULL),
        (3, 'INV-202609-003', 5, 3, 4, 154.00, 10.0, 15.40, 5.00, 164.40, 'Paid', 'UPI', '2026-09-08 16:45:00')
    """)

    # 8. Invoice Items
    cur.execute("""
        INSERT INTO invoice_items (invoice_id, description, item_type, unit_price, quantity, total_price)
        VALUES
        (1, 'Oil Change Service Labor', 'labor', 69.00, 1, 69.00),
        (1, 'Full Synthetic Engine Oil 5W-30', 'part', 25.00, 1, 25.00),
        (1, 'Mann OEM Oil Filter', 'part', 10.00, 1, 10.00),
        (2, 'Car Wash & Express Detailing', 'service', 49.00, 1, 49.00),
        (3, 'AC Service Labor & System Vacuum', 'labor', 109.00, 1, 109.00),
        (3, 'R134a Eco-Refrigerant Canister', 'part', 25.00, 1, 25.00),
        (3, 'OEM HEPA Cabin Air Filter', 'part', 20.00, 1, 20.00)
    """)

    # 9. Payments
    cur.execute("""
        INSERT INTO payments (id, invoice_id, transaction_id, payment_method, amount, status, meta_info)
        VALUES
        (1, 1, 'TXN-CARD-88921471', 'Card', 104.40, 'Paid', 'Visa ending in 4242'),
        (2, 3, 'TXN-UPI-39912048', 'UPI', 164.40, 'Paid', 'UPI ID: sarah@oksbi')
    """)

    # 10. Notifications
    cur.execute("""
        INSERT INTO notifications (user_id, title, message, link, type, is_read)
        VALUES
        (2, 'Vehicle Ready for Pickup', 'Your BMW 330i (NY-7892-AB) detailing service is finished and ready for pickup at Bay 3.', '/tracking/3', 'success', 0),
        (2, 'Service In Progress', 'Technician Marcus has begun brake pad replacement on your Ford F-150.', '/tracking/2', 'status', 0),
        (2, 'Payment Confirmed', 'Payment of $104.40 for Invoice INV-202609-001 has been received successfully.', '/invoices/1', 'info', 1),
        (1, 'New Service Appointment', 'Michael Chang booked Wheel Alignment for Toyota Camry (WA-4411-MN).', '/admin/appointments', 'info', 0),
        (1, 'Vehicle In Service', 'Appointment APT-202609-002 status advanced to In Service.', '/admin/appointments', 'status', 0)
    """)

    # 11. Feedback
    cur.execute("""
        INSERT INTO feedback (id, appointment_id, user_id, mechanic_id, rating, service_quality, mechanic_rating, review)
        VALUES
        (1, 1, 2, 1, 5, 5, 5, 'Exceptional experience. Fast synthetic oil service, clean work area, and Robert explained the vehicle health report clearly.'),
        (2, 5, 3, 5, 5, 5, 5, 'AC is cooling instantly even in extreme heat. Very courteous service and fair pricing. Highly recommended!')
    """)

    conn.commit()
    conn.close()
    print("AutoCare database successfully seeded with realistic demo data!")

if __name__ == '__main__':
    seed_data()
