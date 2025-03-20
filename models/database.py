import sqlite3
import os

DB_NAME = "quiz_master.db"

def init_db():
    # Check if database file already exists
    db_exists = os.path.exists(DB_NAME)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        qualification TEXT,
        dob TEXT
    )""")
    
    # Create Admin Table (Predefined Admin)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")
    
    # Insert Default Admin if not exists
    cursor.execute("INSERT OR IGNORE INTO admin (id, username, password) VALUES (1, 'admin', 'admin123')")
    
    # Create Subjects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    )""")
    
    # Create Chapters Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )""")
    
    # Create Quizzes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_id INTEGER,
        date_of_quiz TEXT,
        time_duration TEXT,
        remarks TEXT,
        FOREIGN KEY (chapter_id) REFERENCES chapters (id)
    )""")
    
    # Create Questions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER,
        question_statement TEXT NOT NULL,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL,
        option4 TEXT NOT NULL,
        correct_option INTEGER NOT NULL,
        FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
    )""")
    
    # Create Scores Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER,
        user_id INTEGER,
        time_stamp_of_attempt DATETIME DEFAULT CURRENT_TIMESTAMP,
        total_scored INTEGER,
        FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )""")
    
    conn.commit()
    conn.close()
    
    print(f"Database initialization {'completed' if not db_exists else 'checked'}") 