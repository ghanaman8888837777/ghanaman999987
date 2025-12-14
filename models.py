import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
# Removed: cryptography.fernet imports
from dotenv import load_dotenv

load_dotenv()

# Initialize the db object without the app instance
db = SQLAlchemy()

# --- CHANGE NOTE 1: Added 'func' import from sqlalchemy ---
# The 'func' object is necessary to use func.utcnow() for reliable timestamp generation.
# from sqlalchemy import Integer, String, func 
# --------------------------------------------------------

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

    # --- CHANGE NOTE 2: Corrected the default value for last_checked ---
    # The previous definition was prone to throwing a Not Null constraint error
    # because the default function might not have been executed properly 
    # during object creation. func.utcnow() is the idiomatic SQLAlchemy 
    # way to set a creation/update timestamp reliably.
    last_checked: Mapped[datetime] = mapped_column(db.DateTime, 
                                                 default=func.utcnow(),
                                                 nullable=False)
    # ------------------------------------------------------------------

    def __repr__(self):
        return f'<VisaAccount {self.unique_id}>'
