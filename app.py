from flask import Flask, render_template, request, redirect, url_for, session
import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_barber_key'

ALL_SLOTS = [
    "08:30 AM - 09:15 AM", "09:15 AM - 10:00 AM", "10:00 AM - 10:45 AM",
    "10:45 AM - 11:30 AM", "11:30 AM - 12:15 PM", "12:15 PM - 01:00 PM",
    "01:00 PM - 01:30 PM", 
    "02:20 PM - 03:05 PM", "03:05 PM - 03:50 PM", "03:50 PM - 04:35 PM",
    "04:35 PM - 05:20 PM", "05:20 PM - 06:05 PM", "06:05 PM - 06:50 PM",
    "06:50 PM - 07:35 PM", "07:35 PM - 08:20 PM"
]

DB_FILE = 'barber_shop.db'

# 👑 दुकान के मालिक की डिटेल्स (यह सिर्फ़ /admin पेज को लॉक करने के लिए है)
OWNER_DETAILS = {
    "name": "Aditya Kumhar",
    "phone": "9876543210",
    "dob": "2000-01-01"
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_date TEXT,
            slot TEXT,
            seat TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            customer_age TEXT,
            UNIQUE(booking_date, slot, seat)
        )
    ''')
    conn.commit()
    conn.close()

def get_bookings_for_date(date_str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT slot, seat, customer_name, customer_phone, customer_age FROM appointments WHERE booking_date = ?', (date_str,))
    rows = cursor.fetchall()
    conn.close()
    
    day_bookings = {slot: {"Seat 1": None, "Seat 2": None} for slot in ALL_SLOTS}
    for row in rows:
        slot, seat, name, phone, age = row
        if slot in day_bookings and seat in day_bookings[slot]:
            day_bookings[slot][seat] = {'name': name, 'phone': phone, 'age': age}
    return day_bookings

# 👤 ग्राहक का लॉगिन (यह सिर्फ़ ग्राहक का नाम और नंबर याद रखने के लिए है)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        phone = request.form.get('phone')
        confirm_phone = request.form.get('confirm_phone')
        
        # अगर कोई भी डिब्बा खाली है, या दोनों फोन नंबर मैच नहीं हुए
        if not name or not age or not phone or not confirm_phone:
            return "Error: All fields are mandatory!", 400
        if phone != confirm_phone:
            return "Error: Mobile numbers do not match!", 400
            
        session['user'] = {'name': name, 'phone': phone, 'age': age}
        return redirect(url_for('booking_page'))
    return render_template('login.html')

@app.route('/booking')
def booking_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    chosen_date = request.args.get('date')
    today = datetime.date.today()
    if not chosen_date:
        chosen_date = today.strftime('%Y-%m-%d')
        
    current_bookings = get_bookings_for_date(chosen_date)
    available_dates = [(today + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    return render_template('index.html', slots=ALL_SLOTS, bookings=current_bookings, user=session['user'], today_date=chosen_date, available_dates=available_dates, owner_phone=OWNER_DETAILS['phone'])

@app.route('/confirm_booking_view', methods=['GET'])
def confirm_booking_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    slot = request.args.get('slot')
    seat = request.args.get('seat')
    date = request.args.get('date')
    return render_template('confirm.html', slot=slot, seat=seat, user=session['user'], booking_date=date)

@app.route('/book_slot', methods=['POST'])
def book_slot():
    if 'user' not in session:
        return redirect(url_for('login'))
    slot = request.form.get('slot')
    seat = request.form.get('seat')
    chosen_date_str = request.form.get('booking_date')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO appointments (booking_date, slot, seat, customer_name, customer_phone, customer_age)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chosen_date_str, slot, seat, session['user']['name'], session['user']['phone'], session['user']['age']))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return f"Error: Slot already booked!", 400
    conn.close()
    return redirect(url_for('my_bookings_view'))

@app.route('/my_bookings')
def my_bookings_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_phone = session['user']['phone']
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT booking_date, slot, seat FROM appointments WHERE customer_phone = ?', (user_phone,))
    rows = cursor.fetchall()
    conn.close()
    user_slots = [{'date': row[0], 'slot': row[1], 'seat': row[2]} for row in rows]
    return render_template('my_bookings.html', user_slots=user_slots, user=session['user'], owner_phone=OWNER_DETAILS['phone'])

# 🔒 ओनर (मालिक) लॉगिन गेट
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        owner_name = request.form.get('owner_name')
        owner_phone = request.form.get('owner_phone')
        confirm_phone = request.form.get('confirm_phone')
        owner_dob = request.form.get('owner_dob')
        
        if owner_phone != confirm_phone:
            return "Error: Mobile numbers do not match!", 400
            
        if (owner_name == OWNER_DETAILS['name'] and 
            owner_phone == OWNER_DETAILS['phone'] and 
            owner_dob == OWNER_DETAILS['dob']):
            session['owner_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Error: Invalid Owner Credentials! Access Denied.", 403
            
    return render_template('admin_login.html')

# 👑 सुरक्षित ओनर डैशबोर्ड
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('owner_logged_in'):
        return redirect(url_for('admin_panel'))
        
    chosen_date = request.args.get('date')
    today = datetime.date.today()
    if not chosen_date:
        chosen_date = today.strftime('%Y-%m-%d')
        
    current_bookings = get_bookings_for_date(chosen_date)
    available_dates = [(today + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    return render_template('admin.html', slots=ALL_SLOTS, bookings=current_bookings, available_dates=available_dates, chosen_date=chosen_date)

@app.route('/admin/logout')
def admin_logout():
    session.pop('owner_logged_in', None)
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
