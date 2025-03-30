from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from models.database import init_db
from controllers.admin import admin_bp
from controllers.user import user_bp
import json

app = Flask(__name__)
app.secret_key = "your_secret_key_here_change_in_production"
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')

init_db()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/auth')
def auth():
    return render_template("auth.html")

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
        cursor.execute("INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)", (username, password, username))  
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' in session:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('login'))

@app.route('/user_dashboard')
def user_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""SELECT COUNT(DISTINCT quiz_id) FROM scores WHERE user_id = ?""", (user_id,))
        total_quizzes = cursor.fetchone()[0] or 0
        cursor.execute("""SELECT ROUND(AVG(total_scored), 2), MAX(total_scored) FROM scores WHERE user_id = ?""", (user_id,))
        avg_score, max_score = cursor.fetchone()
        avg_score = avg_score or 0
        max_score = max_score or 0
        cursor.execute("""SELECT q.id, s.name AS subject_name, ch.name AS chapter_name, q.date_of_quiz, MAX(sc.total_scored) FROM scores sc JOIN quizzes q ON sc.quiz_id = q.id JOIN chapters ch ON q.chapter_id = ch.id
            JOIN subjects s ON ch.subject_id = s.id WHERE sc.user_id = ? GROUP BY q.id, s.name, ch.name, q.date_of_quiz ORDER BY MAX(sc.total_scored) DESC LIMIT 5""", (user_id,))
        recent_attempts = cursor.fetchall()
        chart_data = {'quizDates': [attempt[3] for attempt in recent_attempts],'quizScores': [attempt[4] for attempt in recent_attempts]}
        chart_data_json = json.dumps(chart_data)
    except Exception as e:
        print(f"Database error: {e}")
        total_quizzes = 0
        avg_score = 0
        max_score = 0
        recent_attempts = []
        chart_data_json = json.dumps({'quizDates': [], 'quizScores': []})  
    finally:
        conn.close()
    return render_template('user_dashboard.html', username=session['user'], total_quizzes=total_quizzes, avg_score=avg_score, max_score=max_score, recent_attempts=recent_attempts, chart_data_json=chart_data_json) 

@app.route('/search', methods=['GET'])
def search():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = request.args.get('query', '').strip()
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT 'subject' as type, id, name FROM subjects WHERE name LIKE ? UNION SELECT 'chapter' as type, id, name FROM chapters WHERE name LIKE ? UNION SELECT 'quiz' as type, id, date_of_quiz FROM quizzes WHERE id LIKE ?
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))
    results = cursor.fetchall()
    conn.close()
    return render_template('search_results.html', results=results, query=query)

@app.route('/subjects')
def view_subjects():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM subjects")
    subjects = cursor.fetchall()
    conn.close()
    return render_template('subjects.html', subjects=subjects)

@app.route('/chapters/<int:subject_id>')
def view_chapters(subject_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()  
    cursor.execute("SELECT name FROM subjects WHERE id = ?", (subject_id,))
    subject_name = cursor.fetchone()[0]
    cursor.execute("SELECT id, name, description FROM chapters WHERE subject_id = ?", (subject_id,))
    chapters = cursor.fetchall()
    conn.close()
    return render_template('chapters.html', chapters=chapters, subject_name=subject_name, subject_id=subject_id)

@app.route('/quizzes/<int:chapter_id>')
def view_quizzes(chapter_id):
    if 'user' not in session:
        return redirect(url_for('login')) 
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, subject_id FROM chapters WHERE id = ?", (chapter_id,))
    chapter_info = cursor.fetchone()
    chapter_name = chapter_info[0]
    subject_id = chapter_info[1]
    cursor.execute("SELECT id, date_of_quiz, time_duration, remarks FROM quizzes WHERE chapter_id = ?", (chapter_id,))
    quizzes = cursor.fetchall()
    conn.close()
    return render_template('quizzes.html', quizzes=quizzes, chapter_name=chapter_name, chapter_id=chapter_id, subject_id=subject_id)

@app.route('/take_quiz/<int:quiz_id>')
def take_quiz(quiz_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT q.id, q.date_of_quiz, q.time_duration, ch.name AS chapter_name, s.name AS subject_name FROM quizzes q JOIN chapters ch ON q.chapter_id = ch.id JOIN subjects s ON ch.subject_id = s.id WHERE q.id = ?""", (quiz_id,))
    quiz_info = cursor.fetchone()
    cursor.execute("""SELECT id, question_statement, option1, option2, option3, option4 FROM questions WHERE quiz_id = ?""", (quiz_id,))
    questions = cursor.fetchall()
    cursor.execute("""SELECT total_scored FROM scores WHERE quiz_id = ? AND user_id = ?""", (quiz_id, session['user_id']))
    previous_attempts = cursor.fetchall()
    conn.close()
    return render_template('take_quiz.html', quiz_id=quiz_id, quiz_info=quiz_info, questions=questions, previous_attempts=previous_attempts)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = None
    try:
        conn = sqlite3.connect('quiz_master.db')
        cursor = conn.cursor()
        cursor.execute("""SELECT id, question_statement, option1, option2, option3, option4, correct_option FROM questionsWHERE quiz_id = ?""", (quiz_id,))
        questions = cursor.fetchall()
        user_answers = request.form
        score = 0
        total_questions = len(questions)
        user_quiz_answers = []
        for question in questions:
            question_id = question[0]
            correct_option_index = int(question[6])  
            user_answer = user_answers.get(f'question_{question_id}')
            print(f"Question ID: {question_id}")
            print(f"Correct Option Index (Database): {correct_option_index}")
            print(f"User Answer (Form): {user_answer}")
            options = [question[2], question[3], question[4], question[5]]
            correct_option_value = options[correct_option_index]
            print(f"Correct Option Value: {correct_option_value}")
            if user_answer:
                if user_answer.strip().lower() == correct_option_value.strip().lower():
                    score += 1
                    is_correct = 1
                    print(f"Correct Answer for Question {question_id}")
                else:
                    is_correct = 0
                    print(f"Incorrect Answer for Question {question_id}")
            else:
                is_correct = 0
                print(f"No answer provided for question {question_id}")
            user_quiz_answers.append((quiz_id, session['user_id'], question_id, user_answer, is_correct))
        percentage_score = round((score / total_questions) * 100, 2) if total_questions > 0 else 0

        cursor.execute("""INSERT OR REPLACE INTO scores (user_id, quiz_id, total_scored)VALUES (?, ?, ?)""", (session['user_id'], quiz_id, percentage_score))
        cursor.execute("""DELETE FROM user_quiz_answersWHERE quiz_id = ? AND user_id = ?""", (quiz_id, session['user_id']))
        try:
            cursor.executemany("""INSERT INTO user_quiz_answers (quiz_id, user_id, question_id, user_answer, is_correct) VALUES (?, ?, ?, ?, ?)""", [(quiz_id, session['user_id'], q_id, str(u_answer), is_corr) for quiz_id, session['user_id'], q_id, u_answer, is_corr in user_quiz_answers])
            conn.commit()
        except Exception as e:
            print(f"An error occurred during data insertion: {e}")
            if conn:
                conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        return "An error occurred while submitting the quiz", 500
    finally:
        if conn:
            conn.close()
    return render_template('result.html', score=score, total_questions=total_questions, percentage_score=percentage_score)

@app.route('/add_question', methods=['POST'])
def add_question():
    conn = None  
    try:
        quiz_id = request.form['quiz_id']
        question_statement = request.form['question_statement']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option_index = int(request.form['correct_option'])
        correct_option = [option1, option2, option3, option4][correct_option_index]
        conn = sqlite3.connect('quiz_master.db')
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO questions (quiz_id, question_statement, option1, option2, option3, option4, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?)""", (quiz_id, question_statement, option1, option2, option3, option4, correct_option))
        conn.commit()
    except Exception as e:
        print(f"Error adding question: {e}")
        if conn:
            conn.rollback()
        return "An error occurred while adding the question", 500
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)