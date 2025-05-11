from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, current_app
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

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
    cursor.execute("INSERT INTO users (username, password, full_name, qualification, dob, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
        (data['username'], data['password'], data.get('full_name', ''), data.get('qualification', ''), data.get('dob', '')))
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

    profile_pic = request.files.get('profile_pic')
    filename = None
    
    if profile_pic and allowed_file(profile_pic.filename):
        ext = profile_pic.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        profile_pic.save(filepath)

    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    try:
        if filename:
            cursor.execute("UPDATE users SET profile_pic=? WHERE id=?", (filename, session['user_id']))
            session['profile_pic'] = filename
        else:
            cursor.execute("""UPDATE users SET full_name=?, qualification=?, dob=? WHERE id=?""", 
                (request.form.get('full_name'), request.form.get('qualification'), request.form.get('dob'), session['user_id']))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Profile updated successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()