# 🚗 AutoCare - Vehicle Service Management System

A production-ready, full-stack automotive service and workshop management web platform built with **Python Flask**, **SQLite**, and modern **HTML5 / CSS3 / JavaScript (ES6)**.

---

## 🌟 Key Highlights & Features

### 1. 🎨 Modern Automotive UI / UX Design
- **Responsive Layout**: Designed for seamless desktop, tablet, and mobile usage with responsive drawers, flexible tables, and card layouts.
- **Theme Switcher**: Instant **Light Mode** & **Dark Mode** toggle with `localStorage` persistence.
- **Micro-Interactions**: Real-time toast notifications, animated pulsing status nodes, interactive confirmation modals for destructive operations, and zero dead buttons or fake links.

### 2. 🛡️ Role-Based Authentication & Access Control
- **Customer Role**: Vehicle garage management, 7-step service booking wizard, appointment rescheduling/cancellation, live visual tracking timeline, digital invoice settlement, and completed service review.
- **Admin / Service Manager Role**: KPI analytics board, interactive Chart.js revenue & bay breakdown charts, mechanic dispatching, service stage advancement, service catalog pricing CRUD, and customer directory control.
- **Security**: Robust password hashing via Werkzeug PBKDF2, session cookies, input validation, and parameterized SQL queries to safeguard against SQL injection.

### 3. 📅 Multi-Step Booking Wizard (7 Steps)
1. **Select Vehicle**: Choose from registered garage vehicles or quickly add a new one.
2. **Select Service**: Browse maintenance packages with transparent pricing & durations.
3. **Select Date**: Smart datepicker preventing past date bookings.
4. **Select Time Slot**: Pick workshop intake windows (morning, afternoon, evening).
5. **Symptoms & Description**: Document problem details and technician notes.
6. **Review Booking**: Live estimate breakdown with taxes and subtotal calculations.
7. **Confirmation**: Instant appointment ID generation (`APT-YYYYMM-XXXX`) with in-app notification dispatch.

### 4. 📍 Live Visual Service Tracking Timeline
Real-time 7-stage interactive pipeline:
$$\text{Confirmed} \longrightarrow \text{Received} \longrightarrow \text{Inspection} \longrightarrow \text{In Service} \longrightarrow \text{Quality Check} \longrightarrow \text{Ready for Pickup} \longrightarrow \text{Completed}$$
- Highlights active stage with glowing pulse animations.
- Displays lead mechanic profile, experience, contact details, and diagnostic notes.

### 5. 🧾 Digital Invoices & Local Simulated Payments
- Itemized parts and labor breakdowns with tax computation and discount allowances.
- **Print & PDF Download**: Dedicated print stylesheet (`@media print`) rendering clean receipts without UI controls.
- **Interactive Simulated Payment**: Checkout with **Credit/Debit Card**, **Instant UPI**, or **Counter Cash** without paid external API requirements, transitioning invoices to `Paid`.

### 6. ⭐ Verified Customer Feedback System
- Enabled strictly after service completion.
- Collects 1-5 star ratings, service quality, technician competence scores, and reviews.

---

## 🔑 Demo Test Credentials

| Role | Email | Password | Access |
| :--- | :--- | :--- | :--- |
| **Admin / Manager** | `admin@autocare.com` | `admin123` | Full workshop control, analytics, dispatch |
| **Customer** | `john@example.com` | `customer123` | Garage, bookings, live tracker, invoices |
| **Customer 2** | `sarah@example.com` | `customer123` | EV & SUV vehicles, invoices |

> 💡 **Tip:** Quick-fill pills are embedded directly on the `/login` screen for 1-click test credential entry.

---

## 🚀 Running the Application Locally

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- `pip` package manager

### Installation & Launch Steps

1. **Clone or navigate to the project directory:**
   ```bash
   cd vehicle-service-management
   ```

2. **Activate the virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
   - **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open in browser:**
   ```
   http://127.0.0.1:5000
   ```

---

## 🧪 Running Automated Integration Tests

Run the included verification test suite covering auth, vehicle CRUD, booking, mechanic assignment, status advancement, simulated payments, and reviews:

```powershell
python -m unittest tests/test_app.py
```

---

## 📁 Project Architecture

```
vehicle-service-management/
│
├── app.py                     # Main Flask application with routes and API handlers
├── config.py                  # Environment configuration & secret keys
├── db.py                      # Database access layer and query wrappers
├── requirements.txt           # Python package requirements
├── README.md                  # Documentation and setup instructions
│
├── database/
│   ├── __init__.py
│   ├── schema.sql             # SQLite relational schema with foreign key constraints
│   └── seed.py                # Database population script with realistic demo data
│
├── static/
│   ├── css/
│   │   ├── style.css          # Main automotive theme, variables, toast & modal rules
│   │   ├── dashboard.css      # Dashboard grid, sidebar, topbar, timeline & tables
│   │   └── print.css          # Dedicated print stylesheet for digital invoices
│   └── js/
│       ├── main.js            # Theme toggle, toast system, modals, mobile drawer
│       ├── auth.js            # Form validation, password meter, demo credentials
│       ├── booking.js         # 7-step interactive booking wizard logic
│       ├── tracking.js        # Visual service tracking timeline engine
│       ├── payment.js         # Simulated payment modal (Card, UPI, Cash)
│       └── admin.js           # Chart.js dashboards, status updates, technician assignment
│
├── templates/
│   ├── base.html              # Base HTML template with navbar and footer
│   ├── index.html             # Landing page with hero, services, and working contact form
│   ├── login.html             # Login view with 1-click test credentials
│   ├── signup.html            # Registration view with real-time validation
│   ├── forgot_password.html   # Password recovery flow
│   ├── privacy.html           # Privacy policy
│   ├── terms.html             # Terms of service
│   │
│   ├── customer/
│   │   ├── base_customer.html # Customer portal shell with responsive sidebar & topbar
│   │   ├── dashboard.html     # Customer metrics, upcoming service banner & history
│   │   ├── vehicles.html      # Garage management (CRUD) with modals & confirmation
│   │   ├── vehicle_detail.html# Vehicle-specific lifetime maintenance & spending metrics
│   │   ├── booking.html       # 7-step interactive booking wizard
│   │   ├── appointments.html  # Appointment management (view, reschedule, cancel)
│   │   ├── tracking.html      # Visual 7-node service tracking timeline
│   │   ├── history.html       # Digital service history with search & vehicle filters
│   │   ├── invoices.html      # Digital invoice list
│   │   ├── invoice_detail.html# Itemized printable digital invoice
│   │   ├── _payment_modal.html# Reusable simulated payment modal
│   │   ├── notifications.html # In-app notification center
│   │   ├── profile.html       # Customer profile & password change
│   │   └── feedback.html      # Post-service feedback & review submission
│   │
│   └── admin/
│       ├── base_admin.html    # Admin portal shell with operations sidebar
│       ├── dashboard.html     # KPI metrics cards, Chart.js graphs & recent queues
│       ├── appointments.html  # Appointment master board (assign technician, update status)
│       ├── customers.html     # Customer directory with account status toggles
│       ├── customer_detail.html # Customer profile & historical vehicle records
│       ├── vehicles.html      # Master vehicle fleet registry across all owners
│       ├── mechanics.html     # Mechanics roster CRUD & availability management
│       ├── services.html      # Services catalog CRUD & visibility toggles
│       ├── invoices.html      # Revenue ledger & payment records
│       ├── feedback.html      # Customer satisfaction reviews audit
│       └── reports.html       # Financial performance & mechanic productivity reports
│
└── tests/
    └── test_app.py            # Comprehensive automated integration test suite
```
