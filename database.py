import sqlite3
import os

def init_db():
    conn = sqlite3.connect('pw_data.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS batches (
                batch_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                name TEXT NOT NULL,
                FOREIGN KEY (batch_id) REFERENCES batches(batch_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS contents (
            content_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            content_type TEXT CHECK(content_type IN ('lecture', 'notes', 'dpp', 'solution', 'other')),
            title TEXT NOT NULL,
            file_url TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id))''')
    
    conn.commit()
    conn.close()

def add_batch(batch_id, title, description=""):
    conn = sqlite3.connect('pw_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO batches VALUES (?, ?, ?, datetime('now'))", 
              (batch_id, title, description))
    conn.commit()
    conn.close()

def add_subject(batch_id, subject_name):
    conn = sqlite3.connect('pw_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO subjects (batch_id, name) VALUES (?, ?)",
              (batch_id, subject_name))
    subject_id = c.lastrowid
    conn.commit()
    conn.close()
    return subject_id

def add_content(subject_id, content_type, title, file_url):
    conn = sqlite3.connect('pw_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO contents (subject_id, content_type, title, file_url) VALUES (?, ?, ?, ?)",
              (subject_id, content_type, title, file_url))
    conn.commit()
    conn.close()

def get_all_batches():
    conn = sqlite3.connect('pw_data.db')
    conn.row_factory = sqlite3.Row  # Use Row factory for dictionary-like access
    c = conn.cursor()
    c.execute("SELECT batch_id, title, created_at FROM batches ORDER BY created_at DESC")
    batches = c.fetchall()
    conn.close()
    return batches

def get_batch(batch_id):
    conn = sqlite3.connect('pw_data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT batch_id, title, created_at FROM batches WHERE batch_id=?", (batch_id,))
    batch = c.fetchone()
    conn.close()
    return batch

def get_subjects(batch_id):
    conn = sqlite3.connect('pw_data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT subject_id, name FROM subjects WHERE batch_id=?", (batch_id,))
    subjects = c.fetchall()
    conn.close()
    return subjects

def get_contents(subject_id):
    conn = sqlite3.connect('pw_data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT content_type, title, file_url FROM contents WHERE subject_id=?", (subject_id,))
    contents = c.fetchall()
    conn.close()
    return contents