import os
from flask import Flask, render_template, redirect, url_for, flash
from dotenv import load_dotenv
from datetime import datetime
from models import db, VisaAccount 
from forms import LoginForm, AddAccountForm

# Load environment variables
load_dotenv()

# --- 1. Flask App Creation and Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')

# Database Configuration (Render will provide the DATABASE_URL)
# CRITICAL: This config must be set before db.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

# If using SQLite locally, ensure instance folder exists (optional for Render)
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
    os.makedirs(app.instance_path, exist_ok=True)
# --- END Flask Config ---


# --- 2. CRITICAL FIX: Database Initialization ---
# The db instance must be registered with the app object immediately
db.init_app(app)
# --- END CRITICAL FIX ---


# --- DATABASE INITIALIZATION COMMAND (For Render/Production) ---
@app.cli.command("init-db")
def init_db():
    """Initializes the database by creating all tables."""
    print("Attempting to initialize database tables...")
    with app.app_context():
        # This is safe to run multiple times; it will only create tables if they don't exist
        db.create_all()
    print("Database tables created successfully!")
# --- END CLI Command ---


# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect directly to dashboard as login is disabled
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    # Performs no action
    flash('Logout successful (system is publicly accessible).', 'info')
    return redirect(url_for('dashboard'))

@app.route('/')
@app.route('/dashboard')
def dashboard():
    # Query to display all accounts on the dashboard
    accounts = VisaAccount.query.all()
    return render_template('dashboard.html', accounts=accounts)

@app.route('/add', methods=['GET', 'POST'])
def add_account():
    form = AddAccountForm()
    if form.validate_on_submit():
        try:
            # Password field is saved as PLAIN TEXT
            new_account = VisaAccount(
                email=form.email.data,
                password=form.password.data,
                unique_id=form.unique_id.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                appointment_type=form.appointment_type.data,
                target_month_year=form.target_month_year.data,
                target_day_start=form.target_day_start.data,
                target_day_end=form.target_day_end.data if form.target_day_end.data else None,
                last_checked=datetime.utcnow()
            )
            db.session.add(new_account)
            db.session.commit()
            flash(f'Account {new_account.unique_id} added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            if 'unique_id' in str(e):
                flash('Error: An account with this Unique ID already exists.', 'danger')
            else:
                flash(f'An unexpected database error occurred: {e}', 'danger')
                
    return render_template('add_account.html', form=form)

@app.route('/delete/<int:account_id>')
def delete_account(account_id):
    account = db.session.get(VisaAccount, account_id)
    if account:
        db.session.delete(account)
        db.session.commit()
        flash(f'Account {account.unique_id} deleted.', 'warning')
    else:
        flash('Account not found.', 'danger')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    # Initialize DB connection and create tables for LOCAL development only
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
