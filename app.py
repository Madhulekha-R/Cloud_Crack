from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from models.database import init_db
from controllers.file1 import admin_bp
from controllers.file2 import user_bp

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')

init_db()

@app.route('/')
def home():
    return render_template("file2.html")

@app.route('/auth')
def auth():
    return render_template("file1.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('quiz_master.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return "User already exists. Try logging in."

        cursor.execute("INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)", 
                    (username, password, username))  
        conn.commit()
        conn.close()
        
        return redirect(url_for('login'))

    return redirect(url_for('auth'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('quiz_master.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()
        if admin:
            session['admin'] = True
            session['user_id'] = admin[0]
            conn.close()
            return redirect(url_for('admin_dashboard'))

        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            session['user'] = username
            session['user_id'] = user[0]
            conn.close()
            return redirect(url_for('user_dashboard'))
        
        conn.close()
        return "Invalid credentials. Please try again."

    return redirect(url_for('auth'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' in session:
        return "Welcome, Admin! This is your dashboard."
    return redirect(url_for('login'))

@app.route('/user_dashboard')
def user_dashboard():
    if 'user' in session:
        return f"Welcome, {session['user']}! This is your dashboard."
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)