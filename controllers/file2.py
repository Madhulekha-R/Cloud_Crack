from flask import Blueprint, request, jsonify, session, redirect, url_for
import sqlite3
import datetime

user_bp = Blueprint('user', __name__)
DB_NAME = "quiz_master.db"

@user_bp.before_request
def check_user():
    if 'user' not in session and request.endpoint != 'user.register':
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
    
    cursor.execute("INSERT INTO users (username, password, full_name, qualification, dob) VALUES (?, ?, ?, ?, ?)", 
                   (data['username'], data['password'], data['full_name'], data['qualification'], data['dob']))
    conn.commit()
    conn.close()
    return jsonify({"message": "User registered successfully!"})

@user_bp.route('/attempt_quiz/<int:quiz_id>', methods=['POST'])
def attempt_quiz(quiz_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
        
    data = request.json
    user_id = session['user_id']
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO scores (quiz_id, user_id, time_stamp_of_attempt, total_scored) VALUES (?, ?, ?, ?)", 
                   (quiz_id, user_id, timestamp, data['score']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Quiz attempt recorded!"})