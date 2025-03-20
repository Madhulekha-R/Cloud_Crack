from flask import Blueprint, request, jsonify, session, redirect, url_for
import sqlite3

admin_bp = Blueprint('admin', __name__)
DB_NAME = "quiz_master.db"

@admin_bp.before_request
def check_admin():
    if 'admin' not in session and request.endpoint != 'admin.login':
        return redirect(url_for('login'))

@admin_bp.route('/add_subject', methods=['POST'])
def add_subject():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subjects (name, description) VALUES (?, ?)", 
                   (data['name'], data['description']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Subject added successfully!"})