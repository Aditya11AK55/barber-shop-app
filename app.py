import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_aditya_key_2026"

DB_FILE = "barber_shop.db"

# 👑 सुपर एडमिन (सिर्फ आपके लिए - आदित्य कुमार)
SUPER_ADMIN = {
    "username": "aditya_developer",
    "password_hash": generate_password_hash("Aditya@2026!") # आपका खुफिया पासवर्ड
}

# 💈 दुकानदार/मालिक की डिटेल्स (दुकानदार के लॉगिन के लिए)
OWNER_DETAILS = {
    "name": "Aditya Kumhar",
    "phone": "9876543210",
    "dob": "2000-01-01"
}

# 🗄️ डेटाबेस सेटअप (ऐप चालू होते ही अपने आप टेबल बन जाएंगे)
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 1. ग्राहकों के अकाउंट की टेबल
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            age INTEGER NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # 2. बुकिंग की टेबल
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT NOT NULL,
            user_name TEXT NOT NULL,
            service TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 🏠 होम पेज (कस्टमर यहाँ से शुरू करेगा)
@app.route('/')
def home():
    if 'user_phone' in session:
        return render_template('index.html', logged_in=True, name=session['user_name'])
    return render_template('index.html', logged_in=False)

# 📝 ग्राहक साइन-अप (Sign Up)
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

# 🔑 ग्राहक लॉगिन (Login)
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

# 🚪 लॉगआउट (Logout)
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

# 📅 स्लॉट बुकिंग (सिर्फ लॉगिन किए हुए ग्राहक ही कर सकते हैं)
@app.route('/book', methods=['POST'])
def book():
    if 'user_phone' not in session:
        flash("Please login first to book an appointment!", "warning")
        return redirect(url_for('login'))
        
    service = request.form['service']
    date = request.form['date']
    time = request.form['time']
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointments (user_phone, user_name, service, date, time) VALUES (?, ?, ?, ?, ?)",
                   (session['user_phone'], session['user_name'], service, date, time))
    conn.commit()
    conn.close()
    
    flash("Your Appointment is Booked Successfully! 🎉", "success")
    return redirect(url_for('home'))

# 💈 दुकानदार/मालिक का वेरिफिकेशन पेज (/admin)
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

# 📊 दुकानदार का डैशबोर्ड
@app.route('/owner-dashboard')
def owner_dashboard():
    if not session.get('owner_logged_in'):
        return redirect(url_for('admin_verify'))
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments")
    bookings = cursor.fetchall()
    conn.close()
    return render_template('owner_dashboard.html', bookings=bookings)

# 🕵️ सीक्रेट सुपर एडमिन पेज (सिर्फ आपके लिए - आदित्य कुमार)
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
    
