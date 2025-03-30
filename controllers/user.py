from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import sqlite3

user_bp = Blueprint('user', __name__, url_prefix='/user')
DB_NAME = "quiz_master.db"

@user_bp.before_request
def check_user():
    if 'user' not in session and request.endpoint != 'user.register' and request.endpoint != 'user.profile':
        return redirect(url_for('login'))

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (data['username'],))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "User already exists"}), 400
    cursor.execute("""INSERT INTO users (username, password, first_name, last_name, education) VALUES (?, ?, ?, ?, ?)""", (data['username'], data['password'], data.get('first_name', ''), data.get('last_name', ''), data.get('education', '')))
    conn.commit()
    conn.close()
    return jsonify({"message": "User registered successfully!"})

@user_bp.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name, qualification, dob FROM users WHERE id = ?", (session['user_id'],))
    user_data = cursor.fetchone()
    if not user_data:
        conn.close()
        return redirect(url_for('login'))
    user_info = {'username': user_data[0], 'full_name': user_data[1], 'qualification': user_data[2], 'dob': user_data[3]}
    conn.close()
    return render_template('user_profile.html', **user_info)

@user_bp.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401
    full_name = request.form.get('full_name')
    qualification = request.form.get('qualification')
    dob = request.form.get('dob')
    if not full_name:
        return jsonify({'status': 'error', 'message': 'Full name is required'}), 400
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""UPDATE users SET full_name = ?, qualification = ?, dob = ? WHERE id = ?""", (full_name, qualification, dob, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Profile updated successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'status': 'error', 'message': str(e)}), 500