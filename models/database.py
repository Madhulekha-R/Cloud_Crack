import sqlite3
import os

DB_NAME = "quiz_master.db"

def init_db():
    conn = None  

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            qualification TEXT,
            dob TEXT,
            profile_pic TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL)""")

        cursor.execute("INSERT OR IGNORE INTO admin (id, username, password) VALUES (1, 'admin', 'admin123')")

        cursor.execute("""CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT)""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects (id))""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER,
            date_of_quiz TEXT,
            time_duration TEXT,
            remarks TEXT,
            FOREIGN KEY (chapter_id) REFERENCES chapters (id))""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_statement TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            correct_option TEXT NOT NULL,  
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id))""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                user_id INTEGER,
                time_stamp_of_attempt DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_scored REAL,
                UNIQUE(user_id, quiz_id),
                FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
                FOREIGN KEY (user_id) REFERENCES users (id))""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS user_quiz_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                user_id INTEGER,
                question_id INTEGER,
                user_answer TEXT,
                is_correct BOOLEAN,
                FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (question_id) REFERENCES questions (id))""")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")

        conn.commit()

    except Exception as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()    

if __name__ == "__main__":
    init_db()