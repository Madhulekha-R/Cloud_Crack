from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename
from models.database import init_db
from controllers.admin import admin_bp
from controllers.user import user_bp
from controllers.contact import contact_bp
import json
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from controllers.chatbot import chatbot_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(contact_bp)
app.register_blueprint(chatbot_bp)

def get_google_auth_flow():
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,  
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_uri=url_for('google_callback', _external=True)
    )

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            session['profile_pic'] = user[6]  
            conn.close()
            return redirect(url_for('user_dashboard'))
        conn.close()
        return "Invalid credentials. Please try again."
    return render_template('auth.html')

@app.route('/google_login')
def google_login():
    flow = get_google_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/google_callback')
def google_callback():
    flow = get_google_auth_flow()
    try:
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        try:
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=10  
            )
        except TypeError:
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )
        google_id = id_info['sub']
        email = id_info['email']
        name = id_info.get('name', '')
        picture = id_info.get('picture', '')
        username = email.split('@')[0]
        conn = sqlite3.connect('quiz_master.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
        user = cursor.fetchone()
        if not user:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user:
                cursor.execute("UPDATE users SET google_id = ? WHERE id = ?", (google_id, user[0]))
                user_id = user[0]
            else:
                dummy_password = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO users 
                    (username, google_id, email, full_name, profile_pic, password, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (username, google_id, email, name, picture, dummy_password))
                user_id = cursor.lastrowid
            conn.commit()
        else:
            user_id = user[0]
        conn.close()
        session['user'] = username
        session['user_id'] = user_id
        session['profile_pic'] = picture
        return redirect(url_for('user_dashboard'))
    except ValueError as e:
        if "Token used too early" in str(e):
            flash("Google login failed: Your computer's clock is out of sync. Please synchronize your system time with the internet and try again.")
            return render_template("auth.html", error="Google login failed: Please sync your system clock and try again."), 400
        else:
            print(f"Google OAuth error: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "success": False
            }), 500
    except Exception as e:
        print(f"Google OAuth error: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "success": False
        }), 500

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
    cursor.execute("SELECT profile_pic FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()
    profile_pic = result[0] if result and result[0] and not result[0].startswith('http') else None
    try:
        cursor.execute("SELECT COUNT(DISTINCT quiz_id) FROM scores WHERE user_id = ?", (user_id,))
        total_quizzes = cursor.fetchone()[0] or 0
        cursor.execute("SELECT ROUND(AVG(total_scored), 2), MAX(total_scored) FROM scores WHERE user_id = ?", (user_id,))
        score_result = cursor.fetchone()
        avg_score = score_result[0] if score_result and score_result[0] else 0
        max_score = score_result[1] if score_result and score_result[1] else 0
        cursor.execute("""SELECT q.id, s.name, ch.name, q.date_of_quiz, MAX(sc.total_scored) FROM scores sc JOIN quizzes q ON sc.quiz_id = q.id JOIN chapters ch ON q.chapter_id = ch.id JOIN subjects s ON ch.subject_id = s.id 
            WHERE sc.user_id = ? GROUP BY q.id ORDER BY MAX(sc.total_scored) DESC LIMIT 5""", (user_id,))
        recent_attempts = cursor.fetchall()
        chart_data = {
            'quizDates': [attempt[3] for attempt in recent_attempts],
            'quizScores': [attempt[4] for attempt in recent_attempts]
        }
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
    return render_template('user_dashboard.html', username=session['user'], total_quizzes=total_quizzes, avg_score=avg_score, max_score=max_score, recent_attempts=recent_attempts, chart_data_json=chart_data_json, profile_pic=profile_pic, now=int(datetime.utcnow().timestamp()))

@app.route('/search', methods=['GET'])
def search():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = request.args.get('query', '').strip()
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT 'subject' as type, id, name FROM subjects WHERE name LIKE ? UNION SELECT 'chapter' as type, id, name FROM chapters WHERE name LIKE ? UNION SELECT 'quiz' as type, id, date_of_quiz FROM quizzes WHERE CAST(id as TEXT) LIKE ?
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
        cursor.execute("""SELECT id, question_statement, option1, option2, option3, option4, correct_option FROM questions WHERE quiz_id = ?""", (quiz_id,))
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
        cursor.execute("""DELETE FROM user_quiz_answers WHERE quiz_id = ? AND user_id = ?""", (quiz_id, session['user_id']))
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
    return render_template('result.html', score=score, total_questions=total_questions, percentage_score=percentage_score, quiz_id=quiz_id)

@app.route('/review_answers/<int:quiz_id>')
def review_answers(quiz_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT q.id, q.question_statement, q.option1, q.option2, q.option3, q.option4, q.correct_option FROM questions q WHERE q.quiz_id = ?""", (quiz_id,))
    questions = cursor.fetchall()
    cursor.execute("""SELECT question_id, user_answer FROM user_quiz_answers WHERE quiz_id = ? AND user_id = ?""", (quiz_id, user_id))
    user_answers = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    review_data = []
    for q in questions:
        q_id = q[0]
        q_text = q[1]
        options = [q[2], q[3], q[4], q[5]]
        correct_option_index = int(q[6])
        correct_answer = options[correct_option_index]
        user_answer = user_answers.get(q_id, "Not Answered")
        review_data.append({
            'question': q_text,
            'options': options,
            'user_answer': user_answer,
            'correct_answer': correct_answer
        })
    return render_template('review_answers.html', review_data=review_data)

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

@app.route('/admin/users')
def get_users():
    conn = sqlite3.connect('quiz_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = [{"username": row[0]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"users": users})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)