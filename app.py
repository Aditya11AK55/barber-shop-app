import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import pytz  # Strict Indian Timezone Fix

app = Flask(__name__)
app.secret_key = "super_secret_aditya_key_2026"

# Keeping it synced with the current database structure
DB_FILE = "barber_shop_v2.db"

OWNER_DETAILS = {
    "name": "Aditya Kumhar",
    "phone": "9876543210",
    "dob": "2000-01-01"
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            age INTEGER NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT NOT NULL,
            user_name TEXT NOT NULL,
            seat TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    # 🌍 Fixing the Date Issue: Forcing Asia/Kolkata Timezone so it never shows yesterday's date
    IST = pytz.timezone('Asia/Kolkata')
    current_date_ist = datetime.now(IST).strftime('%Y-%m-%d')
    
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = current_date_ist

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT seat, time, user_name FROM appointments WHERE date=?", (selected_date,))
    rows = cursor.fetchall()
    conn.close()
    
    booked_slots = {}
    for row in rows:
        seat, time, u_name = row[0], row[1], row[2]
        if time not in booked_slots:
            booked_slots[time] = {}
        booked_slots[time][seat] = u_name

    # Exact 45-Minute Intervals
    slots = [
        '08:30 AM', '09:15 AM', '10:00 AM', '10:45 AM', '11:30 AM', 
        '12:15 PM', '01:00 PM', '01:45 PM', '02:30 PM', '03:15 PM', 
        '04:00 PM', '04:45 PM', '05:30 PM', '06:15 PM', '07:00 PM', '07:45 PM'
    ]
    
    logged_in = 'user_phone' in session
    name = session.get('user_name', '')
    
    return render_template('index.html', logged_in=logged_in, name=name, 
                           slots=slots, bookings=booked_slots, 
                           selected_date=selected_date, owner_phone=OWNER_DETAILS['phone'])

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        age = request.form['age']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, phone, age, password) VALUES (?, ?, ?, ?)", 
                           (name, phone, age, hashed_pw))
            conn.commit()
            conn.close()
            flash("Account created successfully! Please Login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("This Mobile Number is already registered!", "danger")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[4], password):
            session['user_phone'] = user[2]
            session['user_name'] = user[1]
            flash("Logged in successfully!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid Mobile Number or Password!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/confirm', methods=['POST'])
def confirm_booking_view():
    if 'user_phone' not in session:
        flash("Please login first to book a slot!", "warning")
        return redirect(url_for('login'))
        
    time = request.form.get('time', '')
    seat = request.form.get('seat', '')
    date = request.form.get('date', '')
    
    if not time or not seat or not date:
        flash("Missing appointment details!", "danger")
        return redirect(url_for('home'))
        
    return render_template('confirm.html', time=time, seat=seat, date=date, 
                           name=session['user_name'], phone=session['user_phone'])

@app.route('/book', methods=['POST'])
def book():
    if 'user_phone' not in session:
        flash("Please login first to book a slot!", "warning")
        return redirect(url_for('login'))
        
    seat = request.form.get('seat')
    time = request.form.get('time')
    date = request.form.get('date')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments WHERE seat=? AND time=? AND date=?", (seat, time, date))
    already_booked = cursor.fetchone()
    
    if already_booked:
        conn.close()
        flash("Sorry, this seat is already booked by someone else!", "danger")
        return redirect(url_for('home'))
        
    cursor.execute("INSERT INTO appointments (user_phone, user_name, seat, date, time) VALUES (?, ?, ?, ?, ?)",
                   (session['user_phone'], session['user_name'], seat, date, time))
    conn.commit()
    conn.close()
    
    flash("🎉 Appointment Booked Successfully!", "success")
    return redirect(url_for('home'))

@app.route('/my_bookings')
def my_bookings():
    if 'user_phone' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, seat, date, time FROM appointments WHERE user_phone=?", (session['user_phone'],))
    user_slots = cursor.fetchall()
    conn.close()
    return render_template('my_bookings.html', bookings=user_slots)

# 🔐 Admin route re-verified and locked for perfect routing
@app.route('/admin', methods=['GET', 'POST'])
def admin_verify():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        dob = request.form.get('dob')
        
        if name == OWNER_DETAILS['name'] and phone == OWNER_DETAILS['phone'] and dob == OWNER_DETAILS['dob']:
            session['owner_logged_in'] = True
            return redirect(url_for('owner_dashboard'))
        else:
            flash("Invalid Owner Credentials! Access Denied.", "danger")
    return render_template('admin_login.html')

@app.route('/owner-dashboard')
def owner_dashboard():
    if not session.get('owner_logged_in'):
        return redirect(url_for('admin_verify'))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_name, user_phone, seat, date, time FROM appointments")
    bookings = cursor.fetchall()
    conn.close()
    return render_template('owner_dashboard.html', bookings=bookings)

if __name__ == '__main__':
    app.run(debug=True)
    
