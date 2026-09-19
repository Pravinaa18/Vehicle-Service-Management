import os
import random
import string
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
import db

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database is initialized and seeded on boot
with app.app_context():
    db.check_and_seed()


# --- Authentication & Authorization Helpers ---

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        user = get_current_user()
        if not user or user['status'] != 'active':
            session.clear()
            flash('Your account is deactivated or invalid.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in with admin credentials.', 'warning')
            return redirect(url_for('login', next=request.url))
        user = get_current_user()
        if not user or user['role'] != 'admin':
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_vars():
    user = get_current_user()
    unread_notifs_count = 0
    recent_notifs = []
    if user:
        unread = db.query_db(
            "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0",
            (user['id'],), one=True
        )
        unread_notifs_count = unread['count'] if unread else 0
        recent_notifs = db.query_db(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (user['id'],)
        )
    return {
        'current_user': user,
        'unread_notifs_count': unread_notifs_count,
        'recent_notifs': recent_notifs,
        'current_year': datetime.now().year,
        'active_path': request.path
    }


# --- Error Handlers ---

@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error_title="404 - Page Not Found",
                           error_message="The page you requested could not be located."), 404

@app.errorhandler(403)
def access_forbidden(e):
    return render_template('base.html', error_title="403 - Forbidden Access",
                           error_message="You do not have permission to view this resource."), 403

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error_title="500 - Server Error",
                           error_message="An internal server error occurred. Please try again later."), 500


# --- Public Routes ---

@app.route('/')
def index():
    services = db.query_db("SELECT * FROM services WHERE status = 'active'")
    testimonials = db.query_db("""
        SELECT f.rating, f.review, u.full_name, m.name as mechanic_name, s.service_name
        FROM feedback f
        JOIN users u ON f.user_id = u.id
        JOIN appointments a ON f.appointment_id = a.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON f.mechanic_id = m.id
        ORDER BY f.created_at DESC LIMIT 3
    """)
    stats = {
        'services_count': db.query_db("SELECT COUNT(*) as c FROM appointments WHERE status = 'Completed'", one=True)['c'],
        'happy_clients': db.query_db("SELECT COUNT(*) as c FROM users WHERE role = 'customer'", one=True)['c'] + 150,
        'expert_mechanics': db.query_db("SELECT COUNT(*) as c FROM mechanics WHERE status = 'active'", one=True)['c']
    }
    return render_template('index.html', services=services, testimonials=testimonials, stats=stats)

@app.route('/services')
def public_services():
    return redirect(url_for('index') + '#services')

@app.route('/about')
def public_about():
    return redirect(url_for('index') + '#about')

@app.route('/contact', methods=['GET', 'POST'])
def public_contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Please fill out all required contact fields.', 'error')
            return redirect(url_for('index') + '#contact')

        db.execute_db("""
            INSERT INTO contact_messages (name, email, phone, subject, message)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, phone, subject or 'General Inquiry', message))

        flash('Thank you for reaching out! Our service advisor will get back to you shortly.', 'success')
        return redirect(url_for('index') + '#contact')
    return redirect(url_for('index') + '#contact')

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

@app.route('/terms')
def terms_conditions():
    return render_template('terms.html')


# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        user = get_current_user()
        if user and user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')

        user = db.query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password. Please try again.', 'error')
            return render_template('login.html')

        if user['status'] != 'active':
            flash('This account has been deactivated. Please contact support.', 'error')
            return render_template('login.html')

        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['user_role'] = user['role']
        if request.form.get('remember_me'):
            session.permanent = True

        flash(f"Welcome back, {user['full_name']}!", 'success')
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name or not email or not phone or not password:
            flash('All fields are required.', 'error')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('signup.html')

        existing = db.query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if existing:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        pwd_hash = generate_password_hash(password)
        new_user_id = db.execute_db("""
            INSERT INTO users (full_name, email, phone, password_hash, role, status)
            VALUES (?, ?, ?, ?, 'customer', 'active')
        """, (full_name, email, phone, pwd_hash))

        # Create welcome notification
        db.execute_db("""
            INSERT INTO notifications (user_id, title, message, link, type)
            VALUES (?, 'Welcome to AutoCare!', 'Your account has been created. Add your vehicle to book your first service.', '/vehicles', 'success')
        """, (new_user_id,))

        session['user_id'] = new_user_id
        session['user_name'] = full_name
        session['user_role'] = 'customer'

        flash('Registration successful! Welcome to AutoCare.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email or not new_password:
            flash('Please provide your registered email and a new password.', 'error')
            return render_template('forgot_password.html')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('forgot_password.html')

        user = db.query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if not user:
            flash('If an account exists with this email, password has been reset.', 'info')
            return redirect(url_for('login'))

        pwd_hash = generate_password_hash(new_password)
        db.execute_db("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user['id']))
        flash('Password successfully reset! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


# --- Customer Portal Routes ---

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    user_id = user['id']

    # KPI counts
    total_vehicles = db.query_db("SELECT COUNT(*) as c FROM vehicles WHERE user_id = ?", (user_id,), one=True)['c']
    upcoming_services = db.query_db("""
        SELECT COUNT(*) as c FROM appointments 
        WHERE user_id = ? AND status IN ('Confirmed', 'Assigned', 'Pending')
    """, (user_id,), one=True)['c']
    completed_services = db.query_db("""
        SELECT COUNT(*) as c FROM appointments 
        WHERE user_id = ? AND status = 'Completed'
    """, (user_id,), one=True)['c']
    pending_services = db.query_db("""
        SELECT COUNT(*) as c FROM appointments 
        WHERE user_id = ? AND status IN ('Vehicle Received', 'Inspection', 'In Service', 'Quality Check', 'Ready for Pickup')
    """, (user_id,), one=True)['c']
    
    total_spent_row = db.query_db("""
        SELECT SUM(final_amount) as total FROM invoices 
        WHERE user_id = ? AND payment_status = 'Paid'
    """, (user_id,), one=True)
    total_spent = total_spent_row['total'] or 0.0

    # Upcoming appointment snippet
    upcoming_apt = db.query_db("""
        SELECT a.*, v.brand, v.model, v.vehicle_number, s.service_name, m.name as mechanic_name
        FROM appointments a
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        WHERE a.user_id = ? AND a.status NOT IN ('Completed', 'Cancelled')
        ORDER BY a.appointment_date ASC, a.created_at DESC
        LIMIT 1
    """, (user_id,), one=True)

    # Recent completed history
    recent_history = db.query_db("""
        SELECT a.*, v.brand, v.model, v.vehicle_number, s.service_name, m.name as mechanic_name,
               i.id as invoice_id, i.payment_status, f.id as feedback_id
        FROM appointments a
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        LEFT JOIN invoices i ON i.appointment_id = a.id
        LEFT JOIN feedback f ON f.appointment_id = a.id
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
        LIMIT 5
    """, (user_id,))

    return render_template(
        'customer/dashboard.html',
        total_vehicles=total_vehicles,
        upcoming_services=upcoming_services,
        completed_services=completed_services,
        pending_services=pending_services,
        total_spent=total_spent,
        upcoming_apt=upcoming_apt,
        recent_history=recent_history
    )


# --- Customer Vehicle Management ---

@app.route('/vehicles')
@login_required
def customer_vehicles():
    user = get_current_user()
    vehicles = db.query_db("""
        SELECT v.*, 
               (SELECT COUNT(*) FROM appointments a WHERE a.vehicle_id = v.id) as service_count,
               (SELECT MAX(appointment_date) FROM appointments a WHERE a.vehicle_id = v.id AND a.status = 'Completed') as last_service_date
        FROM vehicles v
        WHERE v.user_id = ?
        ORDER BY v.created_at DESC
    """, (user['id'],))
    return render_template('customer/vehicles.html', vehicles=vehicles)

@app.route('/vehicles/add', methods=['POST'])
@login_required
def add_vehicle():
    user = get_current_user()
    vehicle_number = request.form.get('vehicle_number', '').strip().upper()
    brand = request.form.get('brand', '').strip()
    model = request.form.get('model', '').strip()
    year = request.form.get('year', '')
    fuel_type = request.form.get('fuel_type', 'Petrol')
    vehicle_type = request.form.get('vehicle_type', 'Sedan')
    color = request.form.get('color', '').strip()
    mileage = request.form.get('current_mileage', 0)

    if not vehicle_number or not brand or not model or not year:
        flash('Please fill out all required vehicle fields.', 'error')
        return redirect(url_for('customer_vehicles'))

    existing = db.query_db("SELECT id FROM vehicles WHERE vehicle_number = ?", (vehicle_number,), one=True)
    if existing:
        flash(f'Vehicle with registration {vehicle_number} is already registered.', 'error')
        return redirect(url_for('customer_vehicles'))

    db.execute_db("""
        INSERT INTO vehicles (user_id, vehicle_number, brand, model, year, fuel_type, vehicle_type, color, current_mileage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user['id'], vehicle_number, brand, model, int(year), fuel_type, vehicle_type, color or 'Silver', int(mileage or 0)))

    flash(f'Vehicle {brand} {model} ({vehicle_number}) added successfully!', 'success')
    return redirect(url_for('customer_vehicles'))

@app.route('/vehicles/edit/<int:vehicle_id>', methods=['POST'])
@login_required
def edit_vehicle(vehicle_id):
    user = get_current_user()
    vehicle = db.query_db("SELECT * FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, user['id']), one=True)
    if not vehicle:
        flash('Vehicle not found.', 'error')
        return redirect(url_for('customer_vehicles'))

    brand = request.form.get('brand', '').strip()
    model = request.form.get('model', '').strip()
    year = request.form.get('year', '')
    fuel_type = request.form.get('fuel_type', vehicle['fuel_type'])
    vehicle_type = request.form.get('vehicle_type', vehicle['vehicle_type'])
    color = request.form.get('color', '').strip()
    mileage = request.form.get('current_mileage', vehicle['current_mileage'])

    db.execute_db("""
        UPDATE vehicles
        SET brand = ?, model = ?, year = ?, fuel_type = ?, vehicle_type = ?, color = ?, current_mileage = ?
        WHERE id = ? AND user_id = ?
    """, (brand, model, int(year), fuel_type, vehicle_type, color, int(mileage), vehicle_id, user['id']))

    flash(f'Vehicle details updated successfully.', 'success')
    return redirect(url_for('customer_vehicles'))

@app.route('/vehicles/delete/<int:vehicle_id>', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    user = get_current_user()
    vehicle = db.query_db("SELECT * FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, user['id']), one=True)
    if not vehicle:
        flash('Vehicle not found.', 'error')
        return redirect(url_for('customer_vehicles'))

    db.execute_db("DELETE FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, user['id']))
    flash(f"Vehicle {vehicle['vehicle_number']} removed successfully.", 'info')
    return redirect(url_for('customer_vehicles'))

@app.route('/vehicles/<int:vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    user = get_current_user()
    vehicle = db.query_db("SELECT * FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, user['id']), one=True)
    if not vehicle:
        flash('Vehicle not found.', 'error')
        return redirect(url_for('customer_vehicles'))

    history = db.query_db("""
        SELECT a.*, s.service_name, m.name as mechanic_name, sr.parts_replaced, sr.total_cost, i.id as invoice_id
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        LEFT JOIN service_records sr ON sr.appointment_id = a.id
        LEFT JOIN invoices i ON i.appointment_id = a.id
        WHERE a.vehicle_id = ?
        ORDER BY a.appointment_date DESC
    """, (vehicle_id,))

    upcoming = [h for h in history if h['status'] not in ('Completed', 'Cancelled')]
    completed = [h for h in history if h['status'] == 'Completed']
    total_spent = sum([h['total_cost'] or h['total_amount'] or 0 for h in completed])

    return render_template(
        'customer/vehicle_detail.html',
        vehicle=vehicle,
        history=history,
        upcoming=upcoming,
        completed_count=len(completed),
        total_spent=total_spent
    )


# --- Customer Multi-Step Service Booking ---

@app.route('/book')
@login_required
def book_service():
    user = get_current_user()
    vehicles = db.query_db("SELECT * FROM vehicles WHERE user_id = ? ORDER BY created_at DESC", (user['id'],))
    services = db.query_db("SELECT * FROM services WHERE status = 'active' ORDER BY category, service_name")
    
    preselect_vehicle = request.args.get('vehicle_id')
    preselect_service = request.args.get('service_id')

    return render_template(
        'customer/booking.html',
        vehicles=vehicles,
        services=services,
        preselect_vehicle=preselect_vehicle,
        preselect_service=preselect_service,
        today_date=date.today().isoformat()
    )

@app.route('/book/submit', methods=['POST'])
@login_required
def submit_booking():
    user = get_current_user()
    vehicle_id = request.form.get('vehicle_id')
    service_id = request.form.get('service_id')
    appointment_date = request.form.get('appointment_date')
    time_slot = request.form.get('time_slot')
    problem_description = request.form.get('problem_description', '').strip()

    if not vehicle_id or not service_id or not appointment_date or not time_slot:
        flash('Please fill in all booking steps before confirming.', 'error')
        return redirect(url_for('book_service'))

    # Verify vehicle belongs to user
    vehicle = db.query_db("SELECT * FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, user['id']), one=True)
    if not vehicle:
        flash('Invalid vehicle selected.', 'error')
        return redirect(url_for('book_service'))

    service = db.query_db("SELECT * FROM services WHERE id = ?", (service_id,), one=True)
    if not service:
        flash('Invalid service selected.', 'error')
        return redirect(url_for('book_service'))

    # Validate date is not in the past
    try:
        book_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        if book_date < date.today():
            flash('Appointment date cannot be in the past. Please choose today or a future date.', 'error')
            return redirect(url_for('book_service'))
    except (ValueError, TypeError):
        flash('Invalid appointment date selected.', 'error')
        return redirect(url_for('book_service'))

    # Generate unique code APT-YYYYMM-XXXX
    rand_suffix = ''.join(random.choices(string.digits, k=4))
    appointment_code = f"APT-{datetime.now().strftime('%Y%m')}-{rand_suffix}"

    apt_id = db.execute_db("""
        INSERT INTO appointments (
            appointment_code, user_id, vehicle_id, service_id, appointment_date,
            time_slot, problem_description, status, total_amount, estimated_completion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?, 'Standard turnaround (Same Day)')
    """, (
        appointment_code, user['id'], vehicle_id, service_id, appointment_date,
        time_slot, problem_description, service['estimated_price']
    ))

    # Send notifications to customer and admin
    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, 'Booking Confirmed', ?, ?, 'success')
    """, (
        user['id'],
        f"Appointment {appointment_code} for {service['service_name']} confirmed on {appointment_date} ({time_slot}).",
        f"/tracking/{apt_id}"
    ))

    # Admin notification (Admin user_id is 1)
    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (1, 'New Appointment Booked', ?, '/admin/appointments', 'info')
    """, (
        f"{user['full_name']} booked {service['service_name']} for {vehicle['brand']} {vehicle['model']} ({vehicle['vehicle_number']}).",
    ))

    flash(f"Appointment {appointment_code} confirmed successfully!", 'success')
    return redirect(url_for('tracking_detail', appointment_id=apt_id))


# --- Customer Appointments & Service Tracking ---

@app.route('/appointments')
@login_required
def customer_appointments():
    user = get_current_user()
    status_filter = request.args.get('status', 'all')

    query = """
        SELECT a.*, v.brand, v.model, v.vehicle_number, s.service_name, s.estimated_duration,
               m.name as mechanic_name, m.phone as mechanic_phone,
               i.id as invoice_id, i.payment_status, f.id as feedback_id
        FROM appointments a
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        LEFT JOIN invoices i ON i.appointment_id = a.id
        LEFT JOIN feedback f ON f.appointment_id = a.id
        WHERE a.user_id = ?
    """
    args = [user['id']]

    if status_filter == 'active':
        query += " AND a.status IN ('Confirmed', 'Assigned', 'Vehicle Received', 'Inspection', 'In Service', 'Quality Check', 'Ready for Pickup')"
    elif status_filter == 'completed':
        query += " AND a.status = 'Completed'"
    elif status_filter == 'cancelled':
        query += " AND a.status = 'Cancelled'"

    query += " ORDER BY a.appointment_date DESC, a.created_at DESC"
    appointments = db.query_db(query, tuple(args))

    return render_template('customer/appointments.html', appointments=appointments, current_filter=status_filter)

@app.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    user = get_current_user()
    reason = request.form.get('cancellation_reason', 'Customer requested cancellation').strip()

    apt = db.query_db("SELECT * FROM appointments WHERE id = ? AND user_id = ?", (appointment_id, user['id']), one=True)
    if not apt:
        flash('Appointment not found.', 'error')
        return redirect(url_for('customer_appointments'))

    if apt['status'] in ('In Service', 'Quality Check', 'Ready for Pickup', 'Completed'):
        flash('Cannot cancel an appointment that is already in service or completed.', 'error')
        return redirect(url_for('customer_appointments'))

    db.execute_db("""
        UPDATE appointments
        SET status = 'Cancelled', cancellation_reason = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (reason, appointment_id))

    # Notify admin and customer
    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, 'Appointment Cancelled', ?, '/appointments', 'warning')
    """, (user['id'], f"Appointment {apt['appointment_code']} has been cancelled."))

    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (1, 'Customer Cancelled Appointment', ?, '/admin/appointments', 'warning')
    """, (f"Customer {user['full_name']} cancelled appointment {apt['appointment_code']}. Reason: {reason}",))

    flash(f"Appointment {apt['appointment_code']} cancelled.", 'info')
    return redirect(url_for('customer_appointments'))

@app.route('/appointments/<int:appointment_id>/reschedule', methods=['POST'])
@login_required
def reschedule_appointment(appointment_id):
    user = get_current_user()
    new_date = request.form.get('new_date')
    new_time_slot = request.form.get('new_time_slot')

    if not new_date or not new_time_slot:
        flash('Please select both a new date and time slot.', 'error')
        return redirect(url_for('customer_appointments'))

    # Validate date is not in the past
    try:
        resched_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        if resched_date < date.today():
            flash('Rescheduled date cannot be in the past.', 'error')
            return redirect(url_for('customer_appointments'))
    except (ValueError, TypeError):
        flash('Invalid date format.', 'error')
        return redirect(url_for('customer_appointments'))

    apt = db.query_db("SELECT * FROM appointments WHERE id = ? AND user_id = ?", (appointment_id, user['id']), one=True)
    if not apt:
        flash('Appointment not found.', 'error')
        return redirect(url_for('customer_appointments'))

    db.execute_db("""
        UPDATE appointments
        SET appointment_date = ?, time_slot = ?, status = 'Confirmed', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_date, new_time_slot, appointment_id))

    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, 'Appointment Rescheduled', ?, '/tracking/' || ?, 'info')
    """, (user['id'], f"Appointment {apt['appointment_code']} rescheduled to {new_date} ({new_time_slot}).", appointment_id))

    flash(f"Appointment {apt['appointment_code']} successfully rescheduled.", 'success')
    return redirect(url_for('customer_appointments'))

@app.route('/tracking/<int:appointment_id>')
@login_required
def tracking_detail(appointment_id):
    user = get_current_user()
    # Allow admin or owner to view
    apt = db.query_db("""
        SELECT a.*, v.brand, v.model, v.year, v.vehicle_number, v.color, v.fuel_type,
               s.service_name, s.estimated_duration, s.estimated_price, s.description as service_desc,
               m.name as mechanic_name, m.phone as mechanic_phone, m.specialization as mechanic_specialty,
               m.experience_years as mechanic_exp,
               i.id as invoice_id, i.payment_status,
               f.id as feedback_id
        FROM appointments a
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        LEFT JOIN invoices i ON i.appointment_id = a.id
        LEFT JOIN feedback f ON f.appointment_id = a.id
        WHERE a.id = ? AND (a.user_id = ? OR ? = 'admin')
    """, (appointment_id, user['id'], user['role']), one=True)

    if not apt:
        flash('Appointment not found or access denied.', 'error')
        return redirect(url_for('customer_appointments'))

    return render_template('customer/tracking.html', apt=apt)

@app.route('/api/appointments/<int:appointment_id>/status')
@login_required
def get_appointment_status_api(appointment_id):
    user = get_current_user()
    apt = db.query_db("""
        SELECT a.id, a.status, a.estimated_completion, a.technician_notes,
               m.name as mechanic_name, m.phone as mechanic_phone, m.specialization as mechanic_specialty
        FROM appointments a
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        WHERE a.id = ? AND (a.user_id = ? OR ? = 'admin')
    """, (appointment_id, user['id'], user['role']), one=True)
    if not apt:
        return jsonify({'error': 'Appointment not found'}), 404
    return jsonify(dict(apt))



# --- Service History & Records ---

@app.route('/history')
@login_required
def service_history():
    user = get_current_user()
    search_q = request.args.get('q', '').strip().lower()
    vehicle_filter = request.args.get('vehicle_id', '')

    vehicles = db.query_db("SELECT id, brand, model, vehicle_number FROM vehicles WHERE user_id = ?", (user['id'],))

    query = """
        SELECT a.*, v.brand, v.model, v.vehicle_number, s.service_name,
               m.name as mechanic_name,
               sr.parts_replaced, sr.labor_details, sr.total_cost as record_cost, sr.technician_notes,
               i.id as invoice_id, i.payment_status,
               f.id as feedback_id, f.rating as feedback_rating
        FROM appointments a
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        LEFT JOIN service_records sr ON sr.appointment_id = a.id
        LEFT JOIN invoices i ON i.appointment_id = a.id
        LEFT JOIN feedback f ON f.appointment_id = a.id
        WHERE a.user_id = ? AND a.status = 'Completed'
    """
    args = [user['id']]

    if vehicle_filter:
        query += " AND a.vehicle_id = ?"
        args.append(vehicle_filter)

    if search_q:
        query += " AND (LOWER(s.service_name) LIKE ? OR LOWER(v.vehicle_number) LIKE ? OR LOWER(v.model) LIKE ?)"
        term = f"%{search_q}%"
        args.extend([term, term, term])

    query += " ORDER BY a.appointment_date DESC"
    records = db.query_db(query, tuple(args))

    return render_template(
        'customer/history.html',
        records=records,
        vehicles=vehicles,
        current_vehicle=vehicle_filter,
        search_q=search_q
    )


# --- Invoice Management & Payment ---

@app.route('/invoices')
@login_required
def customer_invoices():
    user = get_current_user()
    invoices = db.query_db("""
        SELECT i.*, a.appointment_code, v.brand, v.model, v.vehicle_number, s.service_name
        FROM invoices i
        JOIN appointments a ON i.appointment_id = a.id
        JOIN vehicles v ON i.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        WHERE i.user_id = ?
        ORDER BY i.created_at DESC
    """, (user['id'],))
    return render_template('customer/invoices.html', invoices=invoices)

@app.route('/invoices/<int:invoice_id>')
@login_required
def invoice_detail(invoice_id):
    user = get_current_user()
    invoice = db.query_db("""
        SELECT i.*, a.appointment_code, a.appointment_date,
               v.brand, v.model, v.year, v.vehicle_number, v.fuel_type,
               u.full_name as customer_name, u.email as customer_email, u.phone as customer_phone,
               s.service_name
        FROM invoices i
        JOIN appointments a ON i.appointment_id = a.id
        JOIN vehicles v ON i.vehicle_id = v.id
        JOIN users u ON i.user_id = u.id
        JOIN services s ON a.service_id = s.id
        WHERE i.id = ? AND (i.user_id = ? OR ? = 'admin')
    """, (invoice_id, user['id'], user['role']), one=True)

    if not invoice:
        flash('Invoice not found or access denied.', 'error')
        return redirect(url_for('customer_invoices'))

    items = db.query_db("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    payment = db.query_db("SELECT * FROM payments WHERE invoice_id = ?", (invoice_id,), one=True)

    return render_template('customer/invoice_detail.html', invoice=invoice, items=items, payment=payment)

@app.route('/api/invoices/<int:invoice_id>/pay', methods=['POST'])
@login_required
def process_payment_api(invoice_id):
    user = get_current_user()
    invoice = db.query_db("SELECT * FROM invoices WHERE id = ? AND (user_id = ? OR ? = 'admin')",
                           (invoice_id, user['id'], user['role']), one=True)
    if not invoice:
        return jsonify({'success': False, 'error': 'Invoice not found'}), 404

    if invoice['payment_status'] == 'Paid':
        return jsonify({'success': False, 'error': 'Invoice is already paid'}), 400

    data = request.get_json() or {}
    payment_method = data.get('payment_method', 'Card')
    meta_info = data.get('meta_info', 'Simulated online payment')

    txn_prefix = {'Card': 'TXN-CARD', 'UPI': 'TXN-UPI', 'Cash': 'TXN-CASH'}.get(payment_method, 'TXN')
    rand_txn = ''.join(random.choices(string.digits, k=8))
    transaction_id = f"{txn_prefix}-{rand_txn}"

    # Insert payment record
    db.execute_db("""
        INSERT INTO payments (invoice_id, transaction_id, payment_method, amount, status, meta_info)
        VALUES (?, ?, ?, ?, 'Paid', ?)
    """, (invoice_id, transaction_id, payment_method, invoice['final_amount'], meta_info))

    # Update invoice
    db.execute_db("""
        UPDATE invoices
        SET payment_status = 'Paid', payment_method = ?, paid_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (payment_method, invoice_id))

    # Add notification for customer
    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, 'Payment Confirmed', ?, ?, 'success')
    """, (
        invoice['user_id'],
        f"Payment of ${invoice['final_amount']:.2f} for invoice {invoice['invoice_number']} processed successfully via {payment_method}.",
        f"/invoices/{invoice_id}"
    ))

    # Add notification for Admin (user_id 1)
    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (1, 'Payment Received', ?, ?, 'success')
    """, (
        f"Payment of ${invoice['final_amount']:.2f} received for {invoice['invoice_number']} ({payment_method}).",
        "/admin/invoices"
    ))

    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'amount': invoice['final_amount'],
        'payment_method': payment_method
    })



# --- Notifications & Feedback ---

@app.route('/notifications')
@login_required
def notifications_view():
    user = get_current_user()
    notifications = db.query_db("""
        SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC
    """, (user['id'],))
    return render_template('customer/notifications.html', notifications=notifications)

@app.route('/api/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    user = get_current_user()
    db.execute_db("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, user['id']))
    return jsonify({'success': True})

@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    user = get_current_user()
    db.execute_db("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user['id'],))
    return jsonify({'success': True})

@app.route('/feedback/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def submit_feedback(appointment_id):
    user = get_current_user()
    apt = db.query_db("""
        SELECT a.*, s.service_name, v.brand, v.model, v.vehicle_number, m.id as mechanic_id, m.name as mechanic_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN vehicles v ON a.vehicle_id = v.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        WHERE a.id = ? AND a.user_id = ?
    """, (appointment_id, user['id']), one=True)

    if not apt:
        flash('Appointment not found.', 'error')
        return redirect(url_for('customer_appointments'))

    if apt['status'] != 'Completed':
        flash('Feedback can only be provided after service is completed.', 'warning')
        return redirect(url_for('tracking_detail', appointment_id=appointment_id))

    existing_fb = db.query_db("SELECT * FROM feedback WHERE appointment_id = ?", (appointment_id,), one=True)

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        service_quality = int(request.form.get('service_quality', 5))
        mechanic_rating = int(request.form.get('mechanic_rating', 5))
        review = request.form.get('review', '').strip()

        if existing_fb:
            db.execute_db("""
                UPDATE feedback 
                SET rating = ?, service_quality = ?, mechanic_rating = ?, review = ?
                WHERE id = ?
            """, (rating, service_quality, mechanic_rating, review, existing_fb['id']))
            flash('Your feedback has been updated! Thank you.', 'success')
        else:
            db.execute_db("""
                INSERT INTO feedback (appointment_id, user_id, mechanic_id, rating, service_quality, mechanic_rating, review)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (appointment_id, user['id'], apt['mechanic_id'], rating, service_quality, mechanic_rating, review))
            flash('Thank you for your valuable feedback!', 'success')

        return redirect(url_for('service_history'))

    return render_template('customer/feedback.html', apt=apt, feedback=existing_fb)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def customer_profile():
    user = get_current_user()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            full_name = request.form.get('full_name', '').strip()
            phone = request.form.get('phone', '').strip()
            if full_name and phone:
                db.execute_db("UPDATE users SET full_name = ?, phone = ? WHERE id = ?", (full_name, phone, user['id']))
                session['user_name'] = full_name
                flash('Profile details updated successfully.', 'success')
            else:
                flash('Name and phone are required.', 'error')
        elif action == 'change_password':
            old_pwd = request.form.get('old_password', '')
            new_pwd = request.form.get('new_password', '')
            confirm_pwd = request.form.get('confirm_password', '')

            if not check_password_hash(user['password_hash'], old_pwd):
                flash('Incorrect current password.', 'error')
            elif new_pwd != confirm_pwd:
                flash('New passwords do not match.', 'error')
            elif len(new_pwd) < 6:
                flash('Password must be at least 6 characters.', 'error')
            else:
                db.execute_db("UPDATE users SET password_hash = ? WHERE id = ?",
                              (generate_password_hash(new_pwd), user['id']))
                flash('Password changed successfully!', 'success')
        return redirect(url_for('customer_profile'))

    return render_template('customer/profile.html', user=user)


# =========================================================
# --- ADMIN / SERVICE MANAGER PORTAL ---
# =========================================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_customers = db.query_db("SELECT COUNT(*) as c FROM users WHERE role = 'customer'", one=True)['c']
    total_vehicles = db.query_db("SELECT COUNT(*) as c FROM vehicles", one=True)['c']
    
    today_str = date.today().isoformat()
    today_appointments = db.query_db("SELECT COUNT(*) as c FROM appointments WHERE appointment_date = ?", (today_str,), one=True)['c']
    pending_services = db.query_db("SELECT COUNT(*) as c FROM appointments WHERE status = 'Pending'", one=True)['c']
    active_services = db.query_db("""
        SELECT COUNT(*) as c FROM appointments 
        WHERE status IN ('Confirmed', 'Assigned', 'Vehicle Received', 'Inspection', 'In Service', 'Quality Check', 'Ready for Pickup')
    """, one=True)['c']
    completed_services = db.query_db("SELECT COUNT(*) as c FROM appointments WHERE status = 'Completed'", one=True)['c']

    total_revenue_row = db.query_db("SELECT SUM(final_amount) as total FROM invoices WHERE payment_status = 'Paid'", one=True)
    total_revenue = total_revenue_row['total'] or 0.0

    recent_appointments = db.query_db("""
        SELECT a.*, u.full_name as customer_name, v.brand, v.model, v.vehicle_number, s.service_name, m.name as mechanic_name
        FROM appointments a
        JOIN users u ON a.user_id = u.id
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        ORDER BY a.created_at DESC
        LIMIT 6
    """)

    recent_customers = db.query_db("""
        SELECT u.*, 
               (SELECT COUNT(*) FROM vehicles WHERE user_id = u.id) as vehicle_count,
               (SELECT COUNT(*) FROM appointments WHERE user_id = u.id) as appointment_count
        FROM users u
        WHERE u.role = 'customer'
        ORDER BY u.created_at DESC
        LIMIT 5
    """)

    # Charts data calculation
    # 1. Appointment status breakdown
    statuses = ['Completed', 'In Service', 'Pending', 'Confirmed', 'Cancelled']
    status_counts = []
    for st in statuses:
        c = db.query_db("SELECT COUNT(*) as cnt FROM appointments WHERE status = ?", (st,), one=True)['cnt']
        status_counts.append(c)

    # 2. Top services
    top_services_raw = db.query_db("""
        SELECT s.service_name, COUNT(a.id) as count
        FROM services s
        LEFT JOIN appointments a ON a.service_id = s.id
        GROUP BY s.id
        ORDER BY count DESC
        LIMIT 5
    """)
    top_service_labels = [r['service_name'] for r in top_services_raw]
    top_service_values = [r['count'] for r in top_services_raw]

    # 3. Monthly revenue
    monthly_rev_labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
    monthly_rev_values = [320.0, 540.0, 890.0, 720.0, round(total_revenue, 2), 0.0]

    chart_data = {
        'statusBreakdown': {'labels': statuses, 'values': status_counts},
        'topServices': {'labels': top_service_labels, 'values': top_service_values},
        'monthlyRevenue': {'labels': monthly_rev_labels, 'values': monthly_rev_values}
    }

    mechanics = db.query_db("SELECT * FROM mechanics WHERE status = 'active'")

    return render_template(
        'admin/dashboard.html',
        total_customers=total_customers,
        total_vehicles=total_vehicles,
        today_appointments=today_appointments,
        pending_services=pending_services,
        active_services=active_services,
        completed_services=completed_services,
        total_revenue=total_revenue,
        recent_appointments=recent_appointments,
        recent_customers=recent_customers,
        chart_data=chart_data,
        mechanics=mechanics
    )


# --- Admin Appointment Management ---

@app.route('/admin/appointments')
@admin_required
def admin_appointments():
    status_filter = request.args.get('status', 'all')
    search_q = request.args.get('q', '').strip().lower()

    query = """
        SELECT a.*, u.full_name as customer_name, u.phone as customer_phone,
               v.brand, v.model, v.vehicle_number, s.service_name,
               m.id as mechanic_id, m.name as mechanic_name,
               i.id as invoice_id, i.payment_status
        FROM appointments a
        JOIN users u ON a.user_id = u.id
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        LEFT JOIN invoices i ON i.appointment_id = a.id
        WHERE 1=1
    """
    args = []

    if status_filter != 'all':
        query += " AND a.status = ?"
        args.append(status_filter)

    if search_q:
        query += " AND (LOWER(a.appointment_code) LIKE ? OR LOWER(u.full_name) LIKE ? OR LOWER(v.vehicle_number) LIKE ?)"
        term = f"%{search_q}%"
        args.extend([term, term, term])

    query += " ORDER BY a.created_at DESC"
    appointments = db.query_db(query, tuple(args))
    mechanics = db.query_db("SELECT * FROM mechanics WHERE status = 'active'")

    return render_template(
        'admin/appointments.html',
        appointments=appointments,
        mechanics=mechanics,
        current_status=status_filter,
        search_q=search_q
    )

@app.route('/admin/appointments/<int:appointment_id>/assign', methods=['POST'])
@admin_required
def admin_assign_mechanic(appointment_id):
    data = request.get_json() or {}
    mechanic_id = data.get('mechanic_id')

    if not mechanic_id:
        return jsonify({'success': False, 'error': 'Please provide a valid mechanic'}), 400

    mechanic = db.query_db("SELECT * FROM mechanics WHERE id = ?", (mechanic_id,), one=True)
    if not mechanic:
        return jsonify({'success': False, 'error': 'Mechanic not found'}), 404

    apt = db.query_db("SELECT * FROM appointments WHERE id = ?", (appointment_id,), one=True)
    if not apt:
        return jsonify({'success': False, 'error': 'Appointment not found'}), 404

    new_status = 'Assigned' if apt['status'] in ('Pending', 'Confirmed') else apt['status']
    db.execute_db("""
        UPDATE appointments
        SET mechanic_id = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (mechanic_id, new_status, appointment_id))

    # Notify customer
    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, 'Mechanic Assigned', ?, ?, 'info')
    """, (
        apt['user_id'],
        f"Mechanic {mechanic['name']} has been assigned to your appointment {apt['appointment_code']}.",
        f"/tracking/{appointment_id}"
    ))

    return jsonify({'success': True, 'mechanic_name': mechanic['name']})

@app.route('/admin/appointments/<int:appointment_id>/status', methods=['POST'])
@admin_required
def admin_update_status(appointment_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    notes = data.get('notes', '').strip()

    valid_statuses = [
        'Pending', 'Confirmed', 'Assigned', 'Vehicle Received', 'Inspection',
        'In Service', 'Quality Check', 'Ready for Pickup', 'Completed', 'Cancelled'
    ]
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    apt = db.query_db("""
        SELECT a.*, s.estimated_price, s.service_name, v.brand, v.model, v.vehicle_number
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN vehicles v ON a.vehicle_id = v.id
        WHERE a.id = ?
    """, (appointment_id,), one=True)

    if not apt:
        return jsonify({'success': False, 'error': 'Appointment not found'}), 404

    db.execute_db("""
        UPDATE appointments
        SET status = ?, technician_notes = COALESCE(NULLIF(?, ''), technician_notes), updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, notes, appointment_id))

    # If completed, generate service record and invoice if not yet existing
    if new_status == 'Completed':
        existing_rec = db.query_db("SELECT id FROM service_records WHERE appointment_id = ?", (appointment_id,), one=True)
        if not existing_rec:
            labor_cost = apt['estimated_price']
            total_cost = labor_cost
            db.execute_db("""
                INSERT INTO service_records (appointment_id, vehicle_id, mechanic_id, service_date, labor_details, labor_cost, total_cost, technician_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                appointment_id, apt['vehicle_id'], apt['mechanic_id'], date.today().isoformat(),
                f"Standard service completion for {apt['service_name']}", labor_cost, total_cost,
                notes or 'Service completed successfully and passed multi-point quality check.'
            ))

        existing_inv = db.query_db("SELECT id FROM invoices WHERE appointment_id = ?", (appointment_id,), one=True)
        if not existing_inv:
            rand_inv = ''.join(random.choices(string.digits, k=4))
            inv_number = f"INV-{datetime.now().strftime('%Y%m')}-{rand_inv}"
            subtotal = apt['estimated_price']
            tax = subtotal * 0.10
            final_amount = subtotal + tax

            inv_id = db.execute_db("""
                INSERT INTO invoices (invoice_number, appointment_id, user_id, vehicle_id, subtotal, tax_rate, tax_amount, final_amount, payment_status)
                VALUES (?, ?, ?, ?, ?, 10.0, ?, ?, 'Pending')
            """, (inv_number, appointment_id, apt['user_id'], apt['vehicle_id'], subtotal, tax, final_amount))

            db.execute_db("""
                INSERT INTO invoice_items (invoice_id, description, item_type, unit_price, quantity, total_price)
                VALUES (?, ?, 'service', ?, 1, ?)
            """, (inv_id, f"{apt['service_name']} Package", subtotal, subtotal))

    # Notify Customer
    status_messages = {
        'Vehicle Received': f"Your vehicle {apt['vehicle_number']} has arrived and was checked into workshop bay.",
        'Inspection': f"Multi-point diagnostic inspection underway for your vehicle {apt['vehicle_number']}.",
        'In Service': f"Service work is now actively in progress on your vehicle {apt['vehicle_number']}.",
        'Quality Check': f"Technician is conducting the final safety and quality audit on your vehicle.",
        'Ready for Pickup': f"Great news! Your vehicle {apt['vehicle_number']} is clean, inspected, and ready for pickup!",
        'Completed': f"Service for appointment {apt['appointment_code']} is complete. Thank you for choosing AutoCare!",
        'Cancelled': f"Appointment {apt['appointment_code']} has been cancelled."
    }

    msg = status_messages.get(new_status, f"Appointment status updated to {new_status}.")
    db.execute_db("""
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, ?, ?, ?, 'status')
    """, (apt['user_id'], f"Status: {new_status}", msg, f"/tracking/{appointment_id}"))

    return jsonify({'success': True, 'status': new_status})


# --- Admin Customer Management ---

@app.route('/admin/customers')
@admin_required
def admin_customers():
    search_q = request.args.get('q', '').strip().lower()
    status_filter = request.args.get('status', 'all')

    query = """
        SELECT u.*, 
               (SELECT COUNT(*) FROM vehicles v WHERE v.user_id = u.id) as vehicle_count,
               (SELECT COUNT(*) FROM appointments a WHERE a.user_id = u.id) as appointment_count,
               (SELECT COALESCE(SUM(i.final_amount), 0.0) FROM invoices i WHERE i.user_id = u.id AND i.payment_status = 'Paid') as total_spend
        FROM users u
        WHERE u.role = 'customer'
    """
    args = []

    if status_filter != 'all':
        query += " AND u.status = ?"
        args.append(status_filter)

    if search_q:
        query += " AND (LOWER(u.full_name) LIKE ? OR LOWER(u.email) LIKE ? OR u.phone LIKE ?)"
        term = f"%{search_q}%"
        args.extend([term, term, term])

    query += " ORDER BY u.created_at DESC"
    customers = db.query_db(query, tuple(args))

    return render_template('admin/customers.html', customers=customers, search_q=search_q, current_status=status_filter)

@app.route('/admin/customers/<int:user_id>')
@admin_required
def admin_customer_detail(user_id):
    customer = db.query_db("SELECT * FROM users WHERE id = ? AND role = 'customer'", (user_id,), one=True)
    if not customer:
        flash('Customer not found.', 'error')
        return redirect(url_for('admin_customers'))

    vehicles = db.query_db("SELECT * FROM vehicles WHERE user_id = ?", (user_id,))
    appointments = db.query_db("""
        SELECT a.*, v.brand, v.model, v.vehicle_number, s.service_name, m.name as mechanic_name,
               i.id as invoice_id, i.payment_status
        FROM appointments a
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON a.mechanic_id = m.id
        LEFT JOIN invoices i ON i.appointment_id = a.id
        WHERE a.user_id = ?
        ORDER BY a.appointment_date DESC
    """, (user_id,))

    return render_template('admin/customer_detail.html', customer=customer, vehicles=vehicles, appointments=appointments)

@app.route('/admin/customers/<int:user_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_customer(user_id):
    customer = db.query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    if not customer:
        flash('Customer not found.', 'error')
        return redirect(url_for('admin_customers'))

    new_status = 'inactive' if customer['status'] == 'active' else 'active'
    action_label = 'deactivated' if new_status == 'inactive' else 'activated'
    db.execute_db("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    flash(f"Customer {customer['full_name']} account has been {action_label}.", 'info')
    return redirect(url_for('admin_customers'))


# --- Admin Vehicle Management ---

@app.route('/admin/vehicles')
@admin_required
def admin_vehicles():
    search_q = request.args.get('q', '').strip().lower()
    query = """
        SELECT v.*, u.full_name as owner_name, u.email as owner_email, u.phone as owner_phone,
               (SELECT COUNT(*) FROM appointments a WHERE a.vehicle_id = v.id) as service_count
        FROM vehicles v
        JOIN users u ON v.user_id = u.id
        WHERE 1=1
    """
    args = []
    if search_q:
        query += " AND (LOWER(v.vehicle_number) LIKE ? OR LOWER(v.brand) LIKE ? OR LOWER(v.model) LIKE ? OR LOWER(u.full_name) LIKE ?)"
        term = f"%{search_q}%"
        args.extend([term, term, term, term])

    query += " ORDER BY v.created_at DESC"
    vehicles = db.query_db(query, tuple(args))
    return render_template('admin/vehicles.html', vehicles=vehicles, search_q=search_q)


# --- Admin Mechanics Management ---

@app.route('/admin/mechanics')
@admin_required
def admin_mechanics():
    mechanics = db.query_db("""
        SELECT m.*,
               (SELECT COUNT(*) FROM appointments a WHERE a.mechanic_id = m.id AND a.status IN ('Assigned', 'In Service', 'Inspection')) as active_jobs,
               (SELECT COUNT(*) FROM appointments a WHERE a.mechanic_id = m.id AND a.status = 'Completed') as completed_jobs,
               (SELECT ROUND(AVG(f.mechanic_rating), 1) FROM feedback f WHERE f.mechanic_id = m.id) as avg_rating
        FROM mechanics m
        ORDER BY m.name ASC
    """)
    return render_template('admin/mechanics.html', mechanics=mechanics)

@app.route('/admin/mechanics/add', methods=['POST'])
@admin_required
def admin_add_mechanic():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    specialization = request.form.get('specialization', '').strip()
    experience_years = int(request.form.get('experience_years', 1))
    availability = request.form.get('availability', 'available')

    if not name or not email or not phone or not specialization:
        flash('Please fill in all required mechanic details.', 'error')
        return redirect(url_for('admin_mechanics'))

    existing = db.query_db("SELECT id FROM mechanics WHERE email = ?", (email,), one=True)
    if existing:
        flash('A mechanic with this email already exists.', 'error')
        return redirect(url_for('admin_mechanics'))

    db.execute_db("""
        INSERT INTO mechanics (name, email, phone, specialization, experience_years, availability, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    """, (name, email, phone, specialization, experience_years, availability))

    flash(f"Mechanic {name} added to the team.", 'success')
    return redirect(url_for('admin_mechanics'))

@app.route('/admin/mechanics/edit/<int:mechanic_id>', methods=['POST'])
@admin_required
def admin_edit_mechanic(mechanic_id):
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    specialization = request.form.get('specialization', '').strip()
    experience_years = int(request.form.get('experience_years', 1))
    availability = request.form.get('availability', 'available')
    status = request.form.get('status', 'active')

    db.execute_db("""
        UPDATE mechanics
        SET name = ?, email = ?, phone = ?, specialization = ?, experience_years = ?, availability = ?, status = ?
        WHERE id = ?
    """, (name, email, phone, specialization, experience_years, availability, status, mechanic_id))

    flash(f"Mechanic {name} updated successfully.", 'success')
    return redirect(url_for('admin_mechanics'))

@app.route('/admin/mechanics/delete/<int:mechanic_id>', methods=['POST'])
@admin_required
def admin_delete_mechanic(mechanic_id):
    mech = db.query_db("SELECT name FROM mechanics WHERE id = ?", (mechanic_id,), one=True)
    if mech:
        db.execute_db("DELETE FROM mechanics WHERE id = ?", (mechanic_id,))
        flash(f"Mechanic {mech['name']} deleted.", 'info')
    return redirect(url_for('admin_mechanics'))


# --- Admin Services Catalog Management ---

@app.route('/admin/services')
@admin_required
def admin_services():
    services = db.query_db("""
        SELECT s.*,
               (SELECT COUNT(*) FROM appointments a WHERE a.service_id = s.id) as total_bookings
        FROM services s
        ORDER BY s.category, s.service_name
    """)
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/add', methods=['POST'])
@admin_required
def admin_add_service():
    service_name = request.form.get('service_name', '').strip()
    category = request.form.get('category', 'Maintenance')
    description = request.form.get('description', '').strip()
    price = float(request.form.get('estimated_price', 0.0))
    duration = request.form.get('estimated_duration', '1 Hour').strip()
    icon = request.form.get('icon', 'wrench').strip()

    if not service_name or not description or price <= 0:
        flash('Please provide valid service details and pricing.', 'error')
        return redirect(url_for('admin_services'))

    db.execute_db("""
        INSERT INTO services (service_name, category, description, estimated_price, estimated_duration, icon, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    """, (service_name, category, description, price, duration, icon))

    flash(f"Service {service_name} added to catalog.", 'success')
    return redirect(url_for('admin_services'))

@app.route('/admin/services/edit/<int:service_id>', methods=['POST'])
@admin_required
def admin_edit_service(service_id):
    service_name = request.form.get('service_name', '').strip()
    category = request.form.get('category', 'Maintenance')
    description = request.form.get('description', '').strip()
    price = float(request.form.get('estimated_price', 0.0))
    duration = request.form.get('estimated_duration', '1 Hour').strip()
    icon = request.form.get('icon', 'wrench').strip()
    status = request.form.get('status', 'active')

    db.execute_db("""
        UPDATE services
        SET service_name = ?, category = ?, description = ?, estimated_price = ?, estimated_duration = ?, icon = ?, status = ?
        WHERE id = ?
    """, (service_name, category, description, price, duration, icon, status, service_id))

    flash(f"Service {service_name} updated successfully.", 'success')
    return redirect(url_for('admin_services'))

@app.route('/admin/services/toggle/<int:service_id>', methods=['POST'])
@admin_required
def admin_toggle_service(service_id):
    service = db.query_db("SELECT * FROM services WHERE id = ?", (service_id,), one=True)
    if service:
        new_status = 'inactive' if service['status'] == 'active' else 'active'
        db.execute_db("UPDATE services SET status = ? WHERE id = ?", (new_status, service_id))
        flash(f"Service {service['service_name']} is now {new_status}.", 'info')
    return redirect(url_for('admin_services'))

@app.route('/admin/services/delete/<int:service_id>', methods=['POST'])
@admin_required
def admin_delete_service(service_id):
    service = db.query_db("SELECT service_name FROM services WHERE id = ?", (service_id,), one=True)
    if service:
        db.execute_db("DELETE FROM services WHERE id = ?", (service_id,))
        flash(f"Service {service['service_name']} deleted.", 'info')
    return redirect(url_for('admin_services'))


# --- Admin Invoices, Feedback & Reports ---

@app.route('/admin/invoices')
@admin_required
def admin_invoices():
    status_filter = request.args.get('status', 'all')
    query = """
        SELECT i.*, u.full_name as customer_name, v.brand, v.model, v.vehicle_number, s.service_name, a.appointment_code
        FROM invoices i
        JOIN users u ON i.user_id = u.id
        JOIN vehicles v ON i.vehicle_id = v.id
        JOIN appointments a ON i.appointment_id = a.id
        JOIN services s ON a.service_id = s.id
        WHERE 1=1
    """
    args = []
    if status_filter != 'all':
        query += " AND i.payment_status = ?"
        args.append(status_filter)

    query += " ORDER BY i.created_at DESC"
    invoices = db.query_db(query, tuple(args))
    return render_template('admin/invoices.html', invoices=invoices, current_status=status_filter)

@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    feedbacks = db.query_db("""
        SELECT f.*, u.full_name as customer_name, u.email as customer_email,
               v.brand, v.model, v.vehicle_number, s.service_name, m.name as mechanic_name
        FROM feedback f
        JOIN users u ON f.user_id = u.id
        JOIN appointments a ON f.appointment_id = a.id
        JOIN vehicles v ON a.vehicle_id = v.id
        JOIN services s ON a.service_id = s.id
        LEFT JOIN mechanics m ON f.mechanic_id = m.id
        ORDER BY f.created_at DESC
    """)
    avg_rating = db.query_db("SELECT ROUND(AVG(rating), 2) as avg FROM feedback", one=True)['avg'] or 5.0
    return render_template('admin/feedback.html', feedbacks=feedbacks, avg_rating=avg_rating)

@app.route('/admin/reports')
@admin_required
def admin_reports():
    revenue_by_service = db.query_db("""
        SELECT s.service_name, s.category, COUNT(a.id) as bookings, SUM(i.final_amount) as total_revenue
        FROM services s
        LEFT JOIN appointments a ON a.service_id = s.id
        LEFT JOIN invoices i ON i.appointment_id = a.id AND i.payment_status = 'Paid'
        GROUP BY s.id
        ORDER BY total_revenue DESC
    """)

    mechanic_workload = db.query_db("""
        SELECT m.name, m.specialization,
               COUNT(a.id) as total_jobs,
               SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) as completed_jobs,
               ROUND(AVG(f.mechanic_rating), 1) as rating
        FROM mechanics m
        LEFT JOIN appointments a ON a.mechanic_id = m.id
        LEFT JOIN feedback f ON f.mechanic_id = m.id
        GROUP BY m.id
        ORDER BY completed_jobs DESC
    """)

    total_revenue = sum([r['total_revenue'] or 0.0 for r in revenue_by_service])
    total_completed = sum([m['completed_jobs'] or 0 for m in mechanic_workload])

    return render_template(
        'admin/reports.html',
        revenue_by_service=revenue_by_service,
        mechanic_workload=mechanic_workload,
        total_revenue=total_revenue,
        total_completed=total_completed
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
