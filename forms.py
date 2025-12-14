import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, NumberRange, Optional
from datetime import datetime

# Helper to generate choices for the target period (December 2025 to May 2026)
def get_month_choices():
    choices = []
    
    # Start at December 2025
    current_date = datetime(2025, 12, 1)
    
    # End before June 2026 (i.e., end at May 2026)
    while current_date < datetime(2026, 6, 1):
        month_str = current_date.strftime('%B')
        year_str = current_date.strftime('%Y')
        month_code = current_date.strftime('%Y-%m')
        
        choices.append((month_code, f'{month_str} {year_str}'))

        # Move to the next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
            
    return choices

MONTH_CHOICES = get_month_choices()

class LoginForm(FlaskForm):
    # This form is still required for rendering, even if the route just redirects
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class AddAccountForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    unique_id = StringField('Unique Account ID', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    appointment_type = SelectField('Appointment Type', choices=[('new', 'Creating New Appointment'), ('reschedule', 'Rescheduling Existing Appointment')], validators=[DataRequired()])
    
    # New Fields for Date Specification
    target_month_year = SelectField(
        'Target Month',
        choices=MONTH_CHOICES,
        validators=[DataRequired()],
        coerce=str 
    )

    target_day_start = IntegerField(
        'Start Day (1-31)',
        validators=[DataRequired(), NumberRange(min=1, max=31)]
    )
    
    target_day_end = IntegerField(
        'End Day (Optional: Leave empty for a single specific day)',
        validators=[Optional(), NumberRange(min=1, max=31)]
    )

    submit = SubmitField('Add Account') 
    import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, NumberRange, Optional
from datetime import datetime

# Helper to generate choices for the target period (December 2025 to May 2026)
def get_month_choices():
    choices = []
    
    # Start at December 2025
    current_date = datetime(2025, 12, 1)
    
    # End before June 2026 (i.e., end at May 2026)
    while current_date < datetime(2026, 6, 1):
        month_str = current_date.strftime('%B')
        year_str = current_date.strftime('%Y')
        month_code = current_date.strftime('%Y-%m')
        
        choices.append((month_code, f'{month_str} {year_str}'))

        # Move to the next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
            
    return choices

MONTH_CHOICES = get_month_choices()

class LoginForm(FlaskForm):
    # This form is still required for rendering, even if the route just redirects
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class AddAccountForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    unique_id = StringField('Unique Account ID', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    appointment_type = SelectField('Appointment Type', choices=[('new', 'Creating New Appointment'), ('reschedule', 'Rescheduling Existing Appointment')], validators=[DataRequired()])
    
    # New Fields for Date Specification
    target_month_year = SelectField(
        'Target Month',
        choices=MONTH_CHOICES,
        validators=[DataRequired()],
        coerce=str 
    )

    target_day_start = IntegerField(
        'Start Day (1-31)',
        validators=[DataRequired(), NumberRange(min=1, max=31)]
    )
    
    target_day_end = IntegerField(
        'End Day (Optional: Leave empty for a single specific day)',
        validators=[Optional(), NumberRange(min=1, max=31)]
    )

    submit = SubmitField('Add Account')