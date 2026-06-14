import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_aditya_key_2026"

DB_FILE = "barber_shop.db"

SUPER_ADMIN = {
    "username": "aditya_developer",
    "password_hash": generate_password_hash("Aditya@2026!")
}

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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT seat, time FROM appointments")
    rows = cursor.fetchall()
    conn.close()
    
    # कौन सी कुर्सी किस टाइम बुक है, उसकी लिस्ट बनाना
    booked_slots = {}
    for row in rows:
        seat, time = row[0], row[1]
        if time not in booked_slots:
            booked_slots[time] = {}
        booked_slots[time][seat] = True

    available_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    slots = ['09:00 AM', '11:00 AM', '02:00 PM', '05:00 PM']
    
    logged_in = 'user_phone' in session
    name = session.get('user_name', '')
    
    return render_template('index.html', logged_in=logged_in, name=name, 
                           slots=slots, bookings=booked_slots, 
                           available_dates=available_dates, owner_phone=OWNER_DETAILS['phone'])

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
        user = cursor.fetchall()
        conn.close()
        
        if user and check_password_hash(user[0][4], password):
            session['user_phone'] = user[0][2]
            session['user_name'] = user[0][1]
            flash("Logged in successfully!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid Mobile Number or Password!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/book', methods=['POST'])
def book():
    if 'user_phone' not in session:
        flash("Please login first to book a slot!", "warning")
        return redirect(url_for('login'))
        
    seat = request.form['seat']
    time = request.form['time']
    date = request.form['date']
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # चेक करना कि कहीं किसी ने पहले ही तो बुक नहीं कर लिया
    cursor.execute("SELECT * FROM appointments WHERE seat=? AND time=?", (seat, time))
    already_booked = cursor.fetchone()
    
    if already_booked:
        conn.close()
        flash("Sorry, this seat is already booked by someone else!", "danger")
        return redirect(url_for('home'))
        
    cursor.execute("INSERT INTO appointments (user_phone, user_name, seat, date, time) VALUES (?, ?, ?, ?, ?)",
                   (session['user_phone'], session['user_name'], seat, date, time))
    conn.commit()
    conn.close()
    
    flash(f"🎉 {seat} at {time} Booked Successfully!", "success")
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_verify():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        dob = request.form['dob']
        
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

@app.route('/super-secret-aditya-control', methods=['GET', 'POST'])
def super_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == SUPER_ADMIN['username'] and check_password_hash(SUPER_ADMIN['password_hash'], password):
            session['super_admin_logged_in'] = True
        else:
            flash("Wrong Developer Credentials!", "danger")
            
    if session.get('super_admin_logged_in'):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, age FROM users")
        all_users = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_accounts = cursor.fetchone()[0]
        conn.close()
        return render_template('super_admin.html', users=all_users, total=total_accounts)
    return render_template('super_login.html')

if __name__ == '__main__':
    app.run(debug=True)
    
