from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
import secrets
from datetime import datetime, timedelta
import json
import traceback

from database import (
    init_db,
    add_batch,
    add_subject,
    add_content,
    get_all_batches,
    get_batch,
    get_subjects,
    get_contents
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here_123'

# Configuration
app.config['DATABASE'] = 'pw_data.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
TOKEN_EXPIRY_HOURS = 24

# Admin credentials
ADMIN_CREDENTIALS = {
    'username': 'LB_HUB_1302_MERI_PYARI_WEBSITE',
    'password': 'tu web nahi _$&_mehnat hai meri'
}

# Token functions
def generate_user_token():
    """Generate a unique token for user"""
    try:
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        
        print(f"Generated token: {token[:10]}... expiry: {expiry}")
        
        # Store token in session with expiry
        session['user_token'] = token
        session['token_expiry'] = expiry.isoformat()
        
        print(f"Session updated: token={session.get('user_token', 'None')[:10]}...")
        return token
    except Exception as e:
        print(f"Error generating token: {str(e)}")
        print(traceback.format_exc())
        return None

def is_token_valid():
    """Check if user has valid token"""
    try:
        if 'user_token' not in session or 'token_expiry' not in session:
            print("Token or expiry not in session")
            return False
        
        expiry = datetime.fromisoformat(session['token_expiry'])
        is_valid = datetime.now() < expiry
        print(f"Token validity check: {is_valid}, expires: {expiry}")
        return is_valid
    except Exception as e:
        print(f"Error checking token validity: {str(e)}")
        return False

def clear_expired_token():
    """Clear expired token from session"""
    print("Clearing expired token...")
    session.pop('user_token', None)
    session.pop('token_expiry', None)

@app.before_request
def check_access():
    print(f"📋 Checking access for: {request.endpoint}, path: {request.path}")
    
    # Skip token check for these endpoints and static files
    skip_endpoints = ['generate_token', 'create_token', 'verify_token', 'admin_login', 
                     'static', 'redirect_to_1dm', 'page_not_found', 'internal_server_error',
                     'admin_logout']
    
    # Always allow static files
    if request.path.startswith('/static/'):
        print("📁 Allowing static file")
        return None  # Explicitly return None for static files
    
    # Allow token-related and admin login pages
    if request.endpoint in skip_endpoints:
        print(f"✅ Skipping token check for: {request.endpoint}")
        return None
    
    # Allow admin routes if logged in
    if request.endpoint and request.endpoint.startswith('admin_') and session.get('admin_logged_in'):
        print(f"👨‍💼 Allowing admin route: {request.endpoint}")
        return None
    
    # Browser check - sirf Chrome allow karo
    user_agent = request.headers.get('User-Agent', '').lower()
    is_chrome = 'chrome' in user_agent
    is_edge = 'edg/' in user_agent
    is_opera = 'opr/' in user_agent
    is_brave = 'brave' in user_agent
    
    if not is_chrome or is_edge or is_opera or is_brave:
        print("🚫 Browser check failed, redirecting to Chrome")
        return redirect("https://www.google.com/chrome/")
    
    # Check token for all other routes
    print("🔐 Checking token validity...")
    if not is_token_valid():
        print("❌ Token invalid, redirecting to generate token")
        clear_expired_token()
        return redirect(url_for('generate_token'))
    
    print("✅ Token is valid, proceeding...")
    return None  

# Token routes
@app.route("/generate-token", methods=["GET", "POST"])
def generate_token():
    if is_token_valid():
        return redirect(url_for('home'))
    
    # Agar GET request hai to direct page show karo
    if request.method == "GET":
        return render_template("token/generate.html")
        
    # Agar POST request hai to EarnLinks se aaya hai ya nahi check karo
    if request.method == "POST":
        # Check if request came from EarnLinks
        referer = request.headers.get('Referer', '')
        if 'earnlinks.in' not in referer:
            # Agar direct access kiya hai to EarnLinks par redirect karo
            earnlinks_url = f"https://earnlinks.in/st?api=d63fe6c1526ed7118474ff058eae9fdf0a92426b&url={url_for('generate_token', _external=True)}"
            return redirect(earnlinks_url)
        
        # Agar EarnLinks se aaya hai to token generate karo
        token = generate_user_token()
        if token:
            expiry = datetime.fromisoformat(session['token_expiry'])
            expiry_str = expiry.strftime('%d-%m-%Y %I:%M %p')
            return render_template("token/success.html", token=token, expiry=expiry_str)
        else:
            flash('Failed to generate token. Please try again.', 'danger')
            return redirect(url_for('generate_token'))

@app.route('/create-token', methods=['POST'])
def create_token():
    print("Create token route called")
    try:
        # Generate new token
        token = generate_user_token()
        
        if not token:
            print("Failed to generate token")
            flash('Failed to generate token. Please try again.', 'danger')
            return redirect(url_for('generate_token'))
        
        # Get expiry time for display
        expiry = datetime.fromisoformat(session['token_expiry'])
        expiry_str = expiry.strftime('%d-%m-%Y %I:%M %p')
        
        print(f"Token created successfully, redirecting to success page")
        return render_template('token/success.html', 
                             token=token, 
                             expiry=expiry_str,
                             expiry_iso=expiry.isoformat())  # ISO format bhi send karo
    except Exception as e:
        print(f"Error in create_token: {str(e)}")
        print(traceback.format_exc())
        flash('Error generating token. Please try again.', 'danger')
        return redirect(url_for('generate_token'))

@app.route('/verify-token')
def verify_token():
    print("Verify token route called")
    if is_token_valid():
        print("Token is valid, redirecting to home")
        return redirect(url_for('home'))
    else:
        print("Token is invalid, redirecting to generate")
        clear_expired_token()
        flash('Token expired or invalid. Please generate a new token.', 'danger')
        return redirect(url_for('generate_token'))

# Home route
@app.route('/')
def home():
    print("Home route accessed")
    if not is_token_valid():
        print("Direct access attempt without valid token, redirecting")
        return redirect(url_for('generate_token'))
    
    try:
        batches = get_all_batches()
        
        # Token info for display
        token_info = None
        if 'token_expiry' in session:
            try:
                expiry = datetime.fromisoformat(session['token_expiry'])
                time_left = expiry - datetime.now()
                
                # Convert timedelta to readable format
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                time_left_str = f"{hours}h {minutes}m"
                
                token_info = {
                    'expires_at': expiry.strftime('%d-%m-%Y %I:%M %p'),
                    'time_left': time_left_str
                }
                print(f"Token info: {token_info}")
            except Exception as e:
                print(f"Error getting token info: {str(e)}")
        
        return render_template('index.html', batches=batches, token_info=token_info)
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        print(traceback.format_exc())
        return render_template('index.html', batches=[], token_info=None)

# Debug route
@app.route('/debug-session')
def debug_session():
    if not session.get('admin_logged_in'):
        return "Access denied"
    
    return jsonify({
        'session_data': dict(session),
        'token_valid': is_token_valid(),
        'current_time': datetime.now().isoformat()
    })

# Delete batch route
@app.route('/admin/delete_batch/<batch_id>', methods=['POST'])
def delete_batch_route(batch_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        delete_batch(batch_id)
        flash(f'Batch {batch_id} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting batch: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

# Redirect route
@app.route("/redirect")
def redirect_to_1dm():
    link = request.args.get("link")
    return render_template("redirect.html", file_url=link)

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Delete existing batch and its dependencies
def delete_batch(batch_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    
    # Delete contents associated with subjects
    c.execute("SELECT subject_id FROM subjects WHERE batch_id = ?", (batch_id,))
    subject_ids = [row[0] for row in c.fetchall()]
    if subject_ids:
        c.execute("DELETE FROM contents WHERE subject_id IN ({})".format(','.join('?' * len(subject_ids))), subject_ids)
    
    # Delete subjects
    c.execute("DELETE FROM subjects WHERE batch_id = ?", (batch_id,))
    
    # Delete batch
    c.execute("DELETE FROM batches WHERE batch_id = ?", (batch_id,))
    
    conn.commit()
    conn.close()
    print(f"Deleted batch and dependencies: {batch_id}")

# Parse TXT file with overwrite logic
def parse_txt(filepath, batch_id, batch_title):
    success = False
    try:
        # Check if batch exists and delete it
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("SELECT batch_id FROM batches WHERE batch_id = ?", (batch_id,))
        if c.fetchone():
            delete_batch(batch_id)
            print(f"Overwriting existing batch: {batch_id}")
        conn.close()
        
        # Add new batch
        try:
            add_batch(batch_id, batch_title, description="")
            print(f"Batch added successfully: {batch_id}, {batch_title}")
        except sqlite3.IntegrityError as e:
            print(f"Batch insertion failed: {batch_id} already exists or invalid data, Error: {str(e)}")
            return False
        
        subjects = {}
        current_subject = None
        
        with open(filepath, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Detect subject lines (format: "SubjectName - ")
                if line.endswith(" -"):
                    current_subject = line[:-2].strip()
                    if current_subject:
                        subjects[current_subject] = {
                            "Lecture": [],
                            "Notes": [],
                            "DPP": [],
                            "DPP Solution": [],
                            "Other": []
                        }
                        try:
                            subject_id = add_subject(batch_id, current_subject)
                            subjects[current_subject]['id'] = subject_id
                            print(f"Subject added: {current_subject}, ID: {subject_id}, Line: {line_number}")
                        except Exception as e:
                            print(f"Subject insertion failed: {current_subject}, Line: {line_number}, Error: {str(e)}")
                            current_subject = None
                    else:
                        print(f"Empty subject name at line {line_number}")
                    continue
                
                # Process content lines (format: "Title:URL")
                if "http" in line and current_subject:
                    try:
                        title, url = line.split(":", 1)
                        title = title.strip()
                        url = url.strip()
                        
                        if not title or not url:
                            print(f"Invalid title or URL at line {line_number}: {line}")
                            continue
                        
                        # Validate URL (basic check)
                        if not url.startswith(('http://', 'https://')):
                            print(f"Invalid URL format at line {line_number}: {url}")
                            continue
                        
                        # Classify content type
                        content_type = "other"
                        title_lower = title.lower()
                        
                        if any(ext in url.lower() for ext in ['.mp4', '.m3u8', '.mpd']):
                            content_type = "lecture"
                        elif "class notes" in title_lower:
                            content_type = "notes"
                        elif "dpp solution" in title_lower:
                            content_type = "solution"
                        elif "dpp" in title_lower:
                            content_type = "dpp"
                        
                        try:
                            add_content(subjects[current_subject]['id'], content_type, title, url)
                            print(f"Content added: {title}, Type: {content_type}, URL: {url}, Line: {line_number}")
                            subjects[current_subject][content_type.capitalize()].append({
                                "title": title,
                                "url": url
                            })
                        except Exception as e:
                            print(f"Content insertion failed: {title}, Line: {line_number}, Error: {str(e)}")
                            continue
                    except ValueError as e:
                        print(f"Error parsing line {line_number}: {line}, Error: {str(e)}")
                        continue
                elif "http" in line and not current_subject:
                    print(f"Content line {line_number} ignored: No current subject - {line}")
        
        success = True
    except Exception as e:
        print(f"Error processing file: {str(e)}, File: {filepath}, Stack trace: {str(e.__traceback__)}")
    finally:
        return success

# Admin Upload Route
@app.route('/admin/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        file = request.files['file']
        batch_id = request.form['batch_id']
        title = request.form.get('title', '')
        
        print(f"Starting upload for batch: {batch_id}")
        
        if not file or file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        if not allowed_file(file.filename):
            flash('Only TXT files are allowed', 'danger')
            return redirect(request.url)
            
        try:
            # Save file
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            print(f"File saved to: {filepath}")
            
            # Process file
            print("Starting file processing...")
            if parse_txt(filepath, batch_id, title):
                flash('Batch uploaded successfully! (Overwrote existing batch if any)', 'success')
                print("File processed successfully")
            else:
                flash('Failed to process file content', 'danger')
                print("File processing failed. Check logs for details.")
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            print(f"Upload error: {str(e)}")
            flash(f'Error: {str(e)}', 'danger')
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return redirect(request.url)
    
    return render_template('admin/upload.html')

# Subject details
@app.route('/subject/<int:subject_id>')
def show_subject(subject_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE subject_id = ?', (subject_id,))
    subject = cursor.fetchone()
    
    if not subject:
        conn.close()
        flash('Subject not found!', 'danger')
        return redirect(url_for('home'))
    
    # Get contents and categorize
    contents = get_contents(subject_id)
    lectures = [c for c in contents if c['content_type'] == 'lecture']
    notes = [c for c in contents if c['content_type'] == 'notes']
    dpps = [c for c in contents if c['content_type'] == 'dpp']
    solutions = [c for c in contents if c['content_type'] == 'solution']
    others = [c for c in contents if c['content_type'] == 'other']
    
    conn.close()
    return render_template('subject.html', subject=subject, lectures=lectures, notes=notes, dpps=dpps, solutions=solutions, others=others)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['admin_logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

# Static files route
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    batches = get_all_batches()
    return render_template('admin/dashboard.html', batches=batches)

# API endpoint
@app.route('/api/batches')
def api_batches():
    batches = get_all_batches()
    return jsonify([dict(batch) for batch in batches])

@app.route('/batch/<batch_id>')
def show_batch(batch_id):
    batch = get_batch(batch_id)
    print(f"Batch data: {dict(batch) if batch else 'None'}")
    
    if not batch:
        flash('Batch not found!', 'danger')
        return redirect(url_for('home'))
    
    subjects = get_subjects(batch_id)
    print(f"Subjects data: {[dict(s) for s in subjects] if subjects else 'None'}")
    
    return render_template('batch.html', batch=batch, subjects=subjects)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('404.html'), 500

# Initialize the database and run the app
if __name__ == '__main__':
    init_db()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=False)