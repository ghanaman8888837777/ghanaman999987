import os
from flask import Flask, render_template, redirect, url_for, flash
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Flask App Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')

# --- DATABASE CONFIGURATION CHANGE ---
# The default path for SQLite is the instance folder relative to the app.
# We explicitly set the URI here.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# This is required for SQLite file-based databases:
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

# If using SQLite, set the path to the instance folder for the database file
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
    # Creates the instance folder if it doesn't exist (required for relative SQLite paths)
    os.makedirs(app.instance_path, exist_ok=True)
# --- END DATABASE CONFIGURATION CHANGE ---

# Import database and models after app configuration
from models import db, VisaAccount 
from forms import LoginForm, AddAccountForm

# --- DATABASE SETUP ---
def setup_database_connection(application):
    """Initializes the db instance with the Flask application."""
    db.init_app(application)
# --- END DATABASE SETUP ---

# ... (All routes remain the same) ...

@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('dashboard'))
# ... (dashboard, add_account, delete_account routes remain the same) ...

@app.route('/')
@app.route('/dashboard')
def dashboard():
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
                password=form.password.data, # Stored as PLAINTEXT
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
    # Initialize DB connection and create tables
    with app.app_context():
        setup_database_connection(app) 
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)