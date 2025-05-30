import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user, UserMixin
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from email_listener import listen_and_process_emails # Import the listener function
from database import db # Import db from database.py
from auth import auth, User # Import the auth blueprint and User model

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
logger.info('Flask app created')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) # Initialize db with the app
logger.info('Database initialized with app')

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
logger.info('Flask-Login initialized')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database Models
class PdfDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    # Add more fields here as per the specific data to be extracted from PDFs

    def __repr__(self):
        return f"PdfDocument('{self.filename}', '{self.subject}')"

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
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

# Command to initialize the database
@app.cli.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    logger.info('Initializing the database...')
    with app.app_context():
        db.create_all()
    logger.info('Database initialized.')

# Command to create a default user (for testing)
@app.cli.command('create-user')
def create_user_command():
    """Create a default user for testing."""
    username = input("Enter username: ")
    password = input("Enter password: ") # In a real app, hash this password
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            logger.warning(f"User '{username}' already exists.")
        else:
            new_user = User(username=username, password=password) # Store hashed password
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"User '{username}' created successfully.")

# Command to run the email listener
@app.cli.command('run-listener')
def run_listener_command():
    """Runs the email listener to process new emails."""
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        logger.error("EMAIL_ADDRESS and EMAIL_PASSWORD environment variables must be set.")
        return

    logger.info("Starting email listener...")
    with app.app_context(): # Ensure app context for database operations
        listen_and_process_emails(EMAIL_ADDRESS, EMAIL_PASSWORD, db, PdfDocument, IMAP_SERVER)
    logger.info("Email listener finished.")

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    logger.info('Accessing setup route')
    with app.app_context():
        if User.query.first():
            logger.warning('Setup already complete, redirecting to login.')
            flash('Setup already complete. Please login.', 'info')
            return redirect(url_for('auth.login'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                logger.warning('Setup attempt failed: Username or password missing.')
                flash('Username and password are required.', 'danger')
                return render_template('setup.html')

            new_user = User(username=username, password=password) # In a real app, hash this password
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"Initial user '{username}' created successfully during setup.")
            flash('Initial user created successfully. Please login.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('setup.html')

app.register_blueprint(auth) # Register the auth blueprint
logger.info('Auth blueprint registered')

if __name__ == '__main__':
    with app.app_context():
        logger.info('Creating database tables if they do not exist...')
        db.create_all() # Create tables if they don't exist
        logger.info('Database table creation checked.')
    logger.info('Starting Flask development server...')
    app.run(debug=True)
