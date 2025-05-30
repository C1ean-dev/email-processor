from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import db # Import db from the main app
from .auth import User # Import User from auth blueprint
from email_listener import listen_and_process_emails # Import the listener function
import os
from datetime import datetime

main = Blueprint('main', __name__)

# Database Models (PdfDocument remains here for now, could be moved later)
class PdfDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=False, default=datetime.UTC)
    # Add more fields here as per the specific data to be extracted from PDFs

    def __repr__(self):
        return f"PdfDocument('{self.filename}', '{self.subject}')"

@main.route('/')
@login_required
def index():
    return render_template('index.html')

@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            # Basic search for now, can be expanded with full-text search
            results = PdfDocument.query.filter(
                (PdfDocument.subject.contains(query)) |
                (PdfDocument.filename.contains(query)) |
                (PdfDocument.extracted_text.contains(query))
            ).all()
    return render_template('search.html', results=results, query=query)

@main.route('/setup', methods=['GET', 'POST'])
def setup():
    if User.query.first():
        flash('Setup already complete. Please login.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('setup.html')

        new_user = User(username=username, password=password) # In a real app, hash this password
        db.session.add(new_user)
        db.session.commit()
        flash('Initial user created successfully. Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('setup.html')

# Command to initialize the database
@current_app.cli.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    db.create_all()
    print('Initialized the database.')

# Command to create a default user (for testing)
@current_app.cli.command('create-user')
def create_user_command():
    """Create a default user for testing."""
    username = input("Enter username: ")
    password = input("Enter password: ") # In a real app, hash this password
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"User '{username}' already exists.")
    else:
        new_user = User(username=username, password=password) # Store hashed password
        db.session.add(new_user)
        db.session.commit()
        print(f"User '{username}' created successfully.")

# Command to run the email listener
@current_app.cli.command('run-listener')
def run_listener_command():
    """Runs the email listener to process new emails."""
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("Error: EMAIL_ADDRESS and EMAIL_PASSWORD environment variables must be set.")
        return

    print("Starting email listener...")
    with current_app.app_context(): # Ensure app context for database operations
        listen_and_process_emails(EMAIL_ADDRESS, EMAIL_PASSWORD, db, PdfDocument, IMAP_SERVER)
    print("Email listener finished.")
