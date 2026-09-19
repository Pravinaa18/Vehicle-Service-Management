import unittest
import json
from datetime import datetime, date, timedelta
from app import app
import db

class FullVehicleServiceSystemTests(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            db.check_and_seed()

    # 1. Public Pages & Contact
    def test_01_public_pages_and_contact(self):
        """Verify landing page, privacy, terms, and working contact form."""
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        self.assertIn(b'AutoCare', res_home.data)
        self.assertIn(b'About AutoCare', res_home.data)
        self.assertIn(b'Get Service', res_home.data)

        res_priv = self.client.get('/privacy')
        self.assertEqual(res_priv.status_code, 200)
        self.assertIn(b'Privacy Policy', res_priv.data)

        res_terms = self.client.get('/terms')
        self.assertEqual(res_terms.status_code, 200)
        self.assertIn(b'Terms & Conditions', res_terms.data)

        # Submit contact form
        res_contact = self.client.post('/contact', data={
            'name': 'David Miller',
            'email': 'david@example.com',
            'phone': '+1 555-123-4567',
            'subject': 'Fleet maintenance discount',
            'message': 'Inquiring about servicing 5 company vehicles monthly.'
        }, follow_redirects=True)
        self.assertEqual(res_contact.status_code, 200)
        self.assertIn(b'Thank you for reaching out', res_contact.data)
        msg = db.query_db("SELECT * FROM contact_messages WHERE email = 'david@example.com'", one=True)
        self.assertIsNotNone(msg)
        self.assertEqual(msg['subject'], 'Fleet maintenance discount')

    # 2. Authentication: Sign Up, Login, Remember Me, Forgot Password, Logout
    def test_02_auth_lifecycle(self):
        """Verify customer registration, duplicate email check, login, forgot password, logout."""
        db.execute_db("DELETE FROM users WHERE email = 'emma@example.com'")
        # Sign up new customer
        res_signup = self.client.post('/signup', data={
            'full_name': 'Emma Watson',
            'email': 'emma@example.com',
            'phone': '+1 (555) 987-6543',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res_signup.status_code, 200)
        self.assertIn(b'Welcome to AutoCare', res_signup.data)

        # Log out before testing duplicate registration from unauthenticated visitor
        self.client.get('/logout')

        # Duplicate email prevention
        res_dup = self.client.post('/signup', data={
            'full_name': 'Emma Duplicate',
            'email': 'emma@example.com',
            'phone': '+1 (555) 987-6543',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'already exists', res_dup.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out safely', res_logout.data)

        # Invalid login
        res_invalid = self.client.post('/login', data={
            'email': 'emma@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res_invalid.data)

        # Valid login with Remember Me
        res_valid = self.client.post('/login', data={
            'email': 'emma@example.com',
            'password': 'password123',
            'remember_me': 'on'
        }, follow_redirects=True)
        self.assertIn(b'Welcome back, Emma Watson!', res_valid.data)

        # Forgot password flow
        self.client.get('/logout')
        res_forgot = self.client.post('/forgot-password', data={
            'email': 'emma@example.com',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        self.assertIn(b'Password successfully reset', res_forgot.data)

        # Login with new password
        res_new_login = self.client.post('/login', data={
            'email': 'emma@example.com',
            'password': 'newpassword123'
        }, follow_redirects=True)
        self.assertIn(b'Welcome back, Emma Watson!', res_new_login.data)

    # 3. Authorization & RBAC Protection
    def test_03_role_based_access_control(self):
        """Verify customers are forbidden from admin routes and unauthenticated users are redirected."""
        # Unauthenticated access to customer dashboard
        res_guest_dash = self.client.get('/dashboard')
        self.assertEqual(res_guest_dash.status_code, 302)

        # Unauthenticated access to admin dashboard
        res_guest_admin = self.client.get('/admin/dashboard')
        self.assertEqual(res_guest_admin.status_code, 302)

        # Customer attempts to access admin dashboard
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2 # John Doe (Customer)
            sess['user_role'] = 'customer'
        res_cust_admin = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res_cust_admin.data)

        # Admin accesses admin dashboard
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1 # Admin
            sess['user_role'] = 'admin'
        res_admin = self.client.get('/admin/dashboard')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'Executive Overview', res_admin.data)

    # 4. Customer Garage & Vehicle CRUD
    def test_04_vehicle_crud(self):
        """Verify vehicle addition, duplicate registration check, edit, detail view, and deletion."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2 # John Doe
            sess['user_role'] = 'customer'

        # Add vehicle
        res_add = self.client.post('/vehicles/add', data={
            'vehicle_number': 'QA-777-TEST',
            'brand': 'Mercedes-Benz',
            'model': 'C300',
            'year': 2022,
            'fuel_type': 'Petrol',
            'vehicle_type': 'Sedan',
            'color': 'Polar White',
            'current_mileage': 18500
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b'QA-777-TEST', res_add.data)

        # Duplicate vehicle check
        res_dup_veh = self.client.post('/vehicles/add', data={
            'vehicle_number': 'QA-777-TEST',
            'brand': 'Mercedes-Benz',
            'model': 'C300',
            'year': 2022
        }, follow_redirects=True)
        self.assertIn(b'already registered', res_dup_veh.data)

        veh = db.query_db("SELECT id FROM vehicles WHERE vehicle_number = 'QA-777-TEST'", one=True)
        veh_id = veh['id']

        # View vehicle detail page
        res_detail = self.client.get(f'/vehicles/{veh_id}')
        self.assertEqual(res_detail.status_code, 200)
        self.assertIn(b'Lifetime Maintenance Summary', res_detail.data)

        # Edit vehicle
        res_edit = self.client.post(f'/vehicles/edit/{veh_id}', data={
            'brand': 'Mercedes-AMG',
            'model': 'C43',
            'year': 2023,
            'fuel_type': 'Petrol',
            'vehicle_type': 'Sedan',
            'color': 'Obsidian Black',
            'current_mileage': 20000
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertIn(b'Vehicle details updated successfully', res_edit.data)

        # Delete vehicle
        res_del = self.client.post(f'/vehicles/delete/{veh_id}', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        deleted = db.query_db(f"SELECT id FROM vehicles WHERE id = {veh_id}", one=True)
        self.assertIsNone(deleted)

    # 5. Service Booking, Past Date Prevention, and Dynamic Tracking
    def test_05_booking_and_dynamic_tracking(self):
        """Verify 7-step booking wizard, past date rejection, appointment code generation, and live polling API."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['user_role'] = 'customer'

        # Reject past appointment date
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        res_past = self.client.post('/book/submit', data={
            'vehicle_id': 1,
            'service_id': 2,
            'appointment_date': yesterday,
            'time_slot': '10:00 AM - 11:30 AM'
        }, follow_redirects=True)
        self.assertIn(b'Appointment date cannot be in the past', res_past.data)

        # Valid future booking
        future_date = (date.today() + timedelta(days=5)).isoformat()
        res_book = self.client.post('/book/submit', data={
            'vehicle_id': 1,
            'service_id': 2, # Oil Change
            'appointment_date': future_date,
            'time_slot': '01:30 PM - 03:00 PM',
            'problem_description': 'Synthetic oil service and multi-point check'
        }, follow_redirects=True)
        self.assertEqual(res_book.status_code, 200)
        self.assertIn(b'confirmed successfully', res_book.data)

        apt = db.query_db("SELECT * FROM appointments ORDER BY id DESC LIMIT 1", one=True)
        apt_id = apt['id']
        self.assertTrue(apt['appointment_code'].startswith('APT-'))

        # Live tracking polling endpoint
        res_poll = self.client.get(f'/api/appointments/{apt_id}/status')
        self.assertEqual(res_poll.status_code, 200)
        poll_data = res_poll.json
        self.assertEqual(poll_data['status'], 'Confirmed')

    # 6. Appointment Reschedule, Cancellation, and In-Progress Protection
    def test_06_appointment_reschedule_and_cancel(self):
        """Verify rescheduling with future date validation, and cancellation with reason."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['user_role'] = 'customer'

        apt = db.query_db("SELECT id FROM appointments WHERE user_id = 2 AND status = 'Confirmed' LIMIT 1", one=True)
        apt_id = apt['id']

        # Reject past reschedule date
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        res_past_resched = self.client.post(f'/appointments/{apt_id}/reschedule', data={
            'new_date': yesterday,
            'new_time_slot': '03:00 PM - 04:30 PM'
        }, follow_redirects=True)
        self.assertIn(b'Rescheduled date cannot be in the past', res_past_resched.data)

        # Valid reschedule
        next_week = (date.today() + timedelta(days=7)).isoformat()
        res_resched = self.client.post(f'/appointments/{apt_id}/reschedule', data={
            'new_date': next_week,
            'new_time_slot': '03:00 PM - 04:30 PM'
        }, follow_redirects=True)
        self.assertIn(b'successfully rescheduled', res_resched.data)

        # Cancel appointment
        res_cancel = self.client.post(f'/appointments/{apt_id}/cancel', data={
            'cancellation_reason': 'Travelling out of town'
        }, follow_redirects=True)
        self.assertIn(b'cancelled', res_cancel.data)

        updated_apt = db.query_db(f"SELECT status, cancellation_reason FROM appointments WHERE id = {apt_id}", one=True)
        self.assertEqual(updated_apt['status'], 'Cancelled')
        self.assertEqual(updated_apt['cancellation_reason'], 'Travelling out of town')

        # Cancellation should be blocked if in progress
        db.execute_db(f"UPDATE appointments SET status = 'In Service' WHERE id = {apt_id}")
        res_blocked = self.client.post(f'/appointments/{apt_id}/cancel', follow_redirects=True)
        self.assertIn(b'Cannot cancel an appointment that is already in service', res_blocked.data)

    # 7. Admin Mechanics CRUD and Service Catalog CRUD
    def test_07_mechanics_and_services_crud(self):
        """Verify adding, editing, toggling, and deleting mechanics and services."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'admin'

        # 1. Mechanic CRUD
        res_add_m = self.client.post('/admin/mechanics/add', data={
            'name': 'Lucas Scott',
            'email': 'lucas@autocare.com',
            'phone': '+1 (555) 444-1111',
            'specialization': 'Suspension & Steering',
            'experience_years': 7,
            'availability': 'available'
        }, follow_redirects=True)
        self.assertIn(b'Lucas Scott', res_add_m.data)

        mech = db.query_db("SELECT id FROM mechanics WHERE email = 'lucas@autocare.com'", one=True)
        mech_id = mech['id']

        # Edit mechanic
        res_edit_m = self.client.post(f'/admin/mechanics/edit/{mech_id}', data={
            'name': 'Lucas Scott Sr.',
            'email': 'lucas@autocare.com',
            'phone': '+1 (555) 444-2222',
            'specialization': 'Suspension & Steering Master',
            'experience_years': 8,
            'availability': 'on_job',
            'status': 'active'
        }, follow_redirects=True)
        self.assertIn(b'updated successfully', res_edit_m.data)

        # Delete mechanic
        res_del_m = self.client.post(f'/admin/mechanics/delete/{mech_id}', follow_redirects=True)
        self.assertIn(b'deleted', res_del_m.data)
        self.assertIsNone(db.query_db(f"SELECT id FROM mechanics WHERE id = {mech_id}", one=True))

        # 2. Service Catalog CRUD
        res_add_s = self.client.post('/admin/services/add', data={
            'service_name': 'Transmission Flush Pro',
            'category': 'Mechanical',
            'description': 'Complete synthetic fluid evacuation and filter swap.',
            'estimated_price': 199.00,
            'estimated_duration': '2 Hours',
            'icon': 'wrench'
        }, follow_redirects=True)
        self.assertIn(b'Transmission Flush Pro', res_add_s.data)

        srv = db.query_db("SELECT id FROM services WHERE service_name = 'Transmission Flush Pro'", one=True)
        srv_id = srv['id']

        # Toggle service active/inactive
        res_toggle_s = self.client.post(f'/admin/services/toggle/{srv_id}', follow_redirects=True)
        self.assertIn(b'is now inactive', res_toggle_s.data)
        updated_s = db.query_db(f"SELECT status FROM services WHERE id = {srv_id}", one=True)
        self.assertEqual(updated_s['status'], 'inactive')

        # Delete service
        res_del_s = self.client.post(f'/admin/services/delete/{srv_id}', follow_redirects=True)
        self.assertIn(b'deleted', res_del_s.data)
        self.assertIsNone(db.query_db(f"SELECT id FROM services WHERE id = {srv_id}", one=True))

    # 8. Complete Service Lifecycle: Mechanic Dispatch -> Progression -> Auto Invoice -> Payment -> Feedback
    def test_08_complete_service_journey(self):
        """Verify full lifecycle from intake to completion, automatic invoice creation, payment, and verified feedback."""
        # Step 1: Customer books service
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2 # John Doe
            sess['user_role'] = 'customer'

        future_date = (date.today() + timedelta(days=3)).isoformat()
        self.client.post('/book/submit', data={
            'vehicle_id': 2, # Ford F-150
            'service_id': 1, # General Service ($149)
            'appointment_date': future_date,
            'time_slot': '08:00 AM - 09:30 AM',
            'problem_description': '50k mile checkup'
        })

        apt = db.query_db("SELECT * FROM appointments WHERE user_id = 2 ORDER BY id DESC LIMIT 1", one=True)
        apt_id = apt['id']

        # Feedback should be blocked before completion
        res_early_fb = self.client.get(f'/feedback/{apt_id}', follow_redirects=True)
        self.assertIn(b'Feedback can only be provided after service is completed', res_early_fb.data)

        # Step 2: Admin assigns mechanic
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'admin'

        res_assign = self.client.post(f'/admin/appointments/{apt_id}/assign',
            data=json.dumps({'mechanic_id': 1}), # Robert Vance
            content_type='application/json'
        )
        self.assertTrue(res_assign.json['success'])

        # Step 3: Admin advances status to 'Completed'
        res_complete = self.client.post(f'/admin/appointments/{apt_id}/status',
            data=json.dumps({
                'status': 'Completed',
                'notes': '50-point inspection completed. All fluid levels topped off.'
            }),
            content_type='application/json'
        )
        self.assertTrue(res_complete.json['success'])

        # Step 4: Verify auto-generated invoice and service record
        inv = db.query_db("SELECT * FROM invoices WHERE appointment_id = ?", (apt_id,), one=True)
        self.assertIsNotNone(inv)
        self.assertEqual(inv['payment_status'], 'Pending')
        self.assertGreater(inv['final_amount'], 0)

        rec = db.query_db("SELECT * FROM service_records WHERE appointment_id = ?", (apt_id,), one=True)
        self.assertIsNotNone(rec)

        # Step 5: Customer pays invoice via UPI simulation
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['user_role'] = 'customer'

        res_pay = self.client.post(f'/api/invoices/{inv["id"]}/pay',
            data=json.dumps({
                'payment_method': 'UPI',
                'meta_info': 'UPI VPA: john@oksbi'
            }),
            content_type='application/json'
        )
        self.assertTrue(res_pay.json['success'])
        self.assertTrue(res_pay.json['transaction_id'].startswith('TXN-UPI'))

        # Verify invoice is Paid
        paid_inv = db.query_db(f"SELECT payment_status FROM invoices WHERE id = {inv['id']}", one=True)
        self.assertEqual(paid_inv['payment_status'], 'Paid')

        # Step 6: Customer submits review
        res_fb = self.client.post(f'/feedback/{apt_id}', data={
            'rating': 5,
            'service_quality': 5,
            'mechanic_rating': 5,
            'review': 'Great experience, thoroughly inspected everything and finished early!'
        }, follow_redirects=True)
        self.assertIn(b'Thank you for your valuable feedback', res_fb.data)

        # Step 7: Admin reviews feedback in /admin/feedback
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'admin'

        res_admin_fb = self.client.get('/admin/feedback')
        self.assertIn(b'Great experience', res_admin_fb.data)

    # 9. Notifications Center: Read & Read All
    def test_09_notifications_center(self):
        """Verify viewing notifications, marking single as read, and marking all as read."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['user_role'] = 'customer'

        res_notif = self.client.get('/notifications')
        self.assertEqual(res_notif.status_code, 200)

        notif = db.query_db("SELECT id FROM notifications WHERE user_id = 2 AND is_read = 0 LIMIT 1", one=True)
        if notif:
            res_read = self.client.post(f'/api/notifications/read/{notif["id"]}')
            self.assertTrue(res_read.json['success'])

        res_read_all = self.client.post('/api/notifications/read-all')
        self.assertTrue(res_read_all.json['success'])

        unread_count = db.query_db("SELECT COUNT(*) as c FROM notifications WHERE user_id = 2 AND is_read = 0", one=True)['c']
        self.assertEqual(unread_count, 0)

    # 10. Admin Reports and Customer Directory Management
    def test_10_admin_reports_and_customer_toggle(self):
        """Verify admin reports calculation and customer activation/deactivation."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'admin'

        res_reports = self.client.get('/admin/reports')
        self.assertEqual(res_reports.status_code, 200)
        self.assertIn(b'Gross Paid Revenue', res_reports.data)
        self.assertIn(b'Revenue Contribution', res_reports.data)

        # Toggle customer status (Michael Chang user_id 4)
        res_deact = self.client.post('/admin/customers/4/toggle', follow_redirects=True)
        self.assertIn(b'has been deactivated', res_deact.data)
        cust_status = db.query_db("SELECT status FROM users WHERE id = 4", one=True)['status']
        self.assertEqual(cust_status, 'inactive')

        # Reactivate customer
        res_act = self.client.post('/admin/customers/4/toggle', follow_redirects=True)
        self.assertIn(b'has been activated', res_act.data)
        cust_status2 = db.query_db("SELECT status FROM users WHERE id = 4", one=True)['status']
        self.assertEqual(cust_status2, 'active')

if __name__ == '__main__':
    unittest.main()
