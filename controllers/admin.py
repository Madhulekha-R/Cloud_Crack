from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import sqlite3

admin_bp = Blueprint('admin', __name__)
DB_NAME = "quiz_master.db"

@admin_bp.before_request
def check_admin():
    if 'admin' not in session and request.endpoint != 'admin.login':
        return redirect(url_for('login'))

@admin_bp.route('/dashboard')
def dashboard():
    return render_template("admin_dashboard.html")

@admin_bp.route('/subjects')
def get_subjects(): 
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects ORDER BY name")
    subjects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(subjects)

@admin_bp.route('/chapters/<int:subject_id>')
def get_chapters(subject_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chapters WHERE subject_id = ? ORDER BY name", (subject_id,))
    chapters = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(chapters)

@admin_bp.route('/quizzes/<int:chapter_id>')
def get_quizzes(chapter_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE chapter_id = ? ORDER BY date_of_quiz", (chapter_id,))
    quizzes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(quizzes)

@admin_bp.route('/questions/<int:quiz_id>')
def get_questions(quiz_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(questions)

@admin_bp.route('/add_subject', methods=['POST'])
def add_subject():
    data = request.json
    if not data or 'name' not in data:
        return jsonify({"error": "Subject name is required"}), 400 
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subjects (name, description) VALUES (?, ?)", (data['name'], data.get('description', '')))
        conn.commit()
        subject_id = cursor.lastrowid
        conn.close()        
        return jsonify({"message": "Subject added successfully!","id": subject_id})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/add_chapter', methods=['POST'])
def add_chapter():
    data = request.json
    if not data or 'subject_id' not in data or 'name' not in data:
        return jsonify({"error": "Subject ID and Chapter name are required"}), 400 
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chapters (subject_id, name, description) VALUES (?, ?, ?)", (data['subject_id'], data['name'], data.get('description', '')))
        conn.commit()
        chapter_id = cursor.lastrowid
        conn.close()
        return jsonify({"message": "Chapter added successfully!","id": chapter_id})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/add_quiz', methods=['POST'])
def add_quiz():
    data = request.json
    if not data or 'chapter_id' not in data or 'date_of_quiz' not in data or 'time_duration' not in data:
        return jsonify({"error": "Chapter ID, Date, and Duration are required"}), 400
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO quizzes (chapter_id, date_of_quiz, time_duration, remarks) VALUES (?, ?, ?, ?)", (data['chapter_id'], data['date_of_quiz'], data['time_duration'], data.get('remarks', '')))
        conn.commit()
        quiz_id = cursor.lastrowid
        conn.close()
        return jsonify({"message": "Quiz added successfully!","id": quiz_id})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/add_question', methods=['POST'])
def add_question():
    data = request.json
    if not data or 'quiz_id' not in data or 'question_statement' not in data:
        return jsonify({"error": "Quiz ID and Question Statement are required"}), 400
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""INSERT INTO questions (quiz_id, question_statement, option1, option2, option3, option4, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?)""", (
            data['quiz_id'], data['question_statement'], data['option1'], data['option2'], 
            data['option3'], data['option4'], data['correct_option']))
        conn.commit()
        question_id = cursor.lastrowid
        conn.close()
        return jsonify({"message": "Question added successfully!","id": question_id})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/edit_subject/<int:subject_id>', methods=['PUT'])
def edit_subject(subject_id):
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE subjects SET name = ?, description = ? WHERE id = ?", (data['name'], data.get('description', ''), subject_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Subject updated successfully!"})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/edit_chapter/<int:chapter_id>', methods=['PUT'])
def edit_chapter(chapter_id):
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE chapters SET name = ?, description = ? WHERE id = ?", (data['name'], data.get('description', ''), chapter_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Chapter updated successfully!"})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/edit_quiz/<int:quiz_id>', methods=['PUT'])
def edit_quiz(quiz_id):
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE quizzes SET date_of_quiz = ?, time_duration = ?, remarks = ? WHERE id = ?", (data['date_of_quiz'], data['time_duration'], data.get('remarks', ''), quiz_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Quiz updated successfully!"})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/edit_question/<int:question_id>', methods=['PUT'])
def edit_question(question_id):
    data = request.json  
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()  
    try:
        cursor.execute("""UPDATE questions SET question_statement = ?, option1 = ?, option2 = ?, option3 = ?, option4 = ?, correct_option = ? WHERE id = ?""", (
            data['question_statement'], data['option1'], data['option2'], 
            data['option3'], data['option4'], data['correct_option'], question_id
        ))
        conn.commit()
        conn.close() 
        return jsonify({"message": "Question updated successfully!"})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/delete_subject/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Subject deleted successfully!"})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/delete_chapter/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Chapter deleted successfully!"})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/delete_quiz/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Quiz deleted successfully!"})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@admin_bp.route('/delete_question/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        conn.close()  
        return jsonify({"message": "Question deleted successfully!"})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500