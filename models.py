import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
# Removed: cryptography.fernet imports
from dotenv import load_dotenv

load_dotenv()

# Initialize the db object without the app instance
db = SQLAlchemy()

class User(db.Model):
    # This model is kept for consistency but is unused by the application logic
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False) 

class VisaAccount(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    email: Mapped[str] = mapped_column(String, nullable=False)
    # CRITICAL: Field is now a standard String (plaintext storage)
    password: Mapped[str] = mapped_column(String, nullable=False) 
    unique_id: Mapped[str] = mapped_column(String, unique=True, nullable=False) 
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    
    appointment_type: Mapped[str] = mapped_column(String, nullable=False) 
    target_month_year: Mapped[str] = mapped_column(String, nullable=False) 
    target_day_start: Mapped[int] = mapped_column(Integer, nullable=False) 
    target_day_end: Mapped[int] = mapped_column(Integer, nullable=True) 

    last_checked: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<VisaAccount {self.unique_id}>'