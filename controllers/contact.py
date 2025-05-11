from flask import Blueprint, request, jsonify
import sqlite3

contact_bp = Blueprint('contact', __name__)
DB_NAME = "quiz_master.db"

@contact_bp.route('/contact', methods=['POST'])
def submit_contact():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    if not name or not email or not message:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)", (name, email, message))
        conn.commit()
        return jsonify({'success': True, 'message': 'Message sent!'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()
