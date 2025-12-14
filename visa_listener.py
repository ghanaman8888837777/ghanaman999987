import datetime
import time
import asyncio
from typing import List, Optional, Dict, Set
import telegram
import os
import logging
from dotenv import load_dotenv
from calendar import monthrange 

# Load environment variables
load_dotenv()

# --- Logging Configuration ---
# Ensure logging is configured for consistent output in the container logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CRITICAL IMPORTS FOR DATABASE ACCESS (FIXED) ---
# We only import the Flask app instance (app) and the database objects (db, VisaAccount).
# The failing function 'setup_database_connection' has been removed.
from app import app
from models import db, VisaAccount 
# --- END CRITICAL IMPORTS ---

# Weekday constants
MONDAY = 0
WEDNESDAY = 2

# CRITICAL FIX: The entire outdated context block is removed.
# Database connection and setup is now handled exclusively by Flask-SQLAlchemy 
# initialized in app.py, and accessed via 'with app.app_context():' in run_async.
# with app.app_context():
#     setup_database_connection(app) 

class VisaSlotListener:
    """
    Combines:
    1. Global Month-by-Month Slot Checker (Sends constant alerts for all months).
    2. Account-Specific Monitoring (Checks against full_schedule).
    """
    
    def __init__(
        self,
        telegram_token: str,
        telegram_chat_id: int,
        # CRITICAL FIX: Set default poll interval to 5 minutes (300s)
        poll_interval_seconds: int = 60, 
        location: str = "Accra U.S. Embassy/Consulate"
    ):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.poll_interval = poll_interval_seconds
        self.location = location

        self.start_date = datetime.date(2025, 12, 1)
        self.end_date = datetime.date(2026, 12, 31)

        # --- GLOBAL SLOT CHECKER SETUP ---
        self.full_schedule: Set[datetime.date] = self._calculate_full_schedule()
        self.previous_slots: Set[datetime.date] = set() 
        self.month_iterator = self._get_month_range()
        
        # Setup Telegram bot
        self.bot = telegram.Bot(token=telegram_token)

    def _get_availability_rules(self) -> Dict[int, Dict[int, Set[int]]]:
        """Defines the deterministic availability rules for 2026."""
        return {
            6: {MONDAY: {24}, WEDNESDAY: {24}},
            7: {MONDAY: set(), WEDNESDAY: set()},
            8: {MONDAY: {26}, WEDNESDAY: {26}},
            9: {MONDAY: {*range(1, 31)} - {7, 28}, WEDNESDAY: {23}},
            10: {MONDAY: {12}, WEDNESDAY: {28}},
            11: {MONDAY: set(), WEDNESDAY: {11, 25}},
            12: {MONDAY: {28}, WEDNESDAY: {23, 30}},
        }

    def _calculate_full_schedule(self) -> Set[datetime.date]:
        """Calculates the entire deterministic schedule once."""
        schedule = set()
        rules = self._get_availability_rules()
        current_date = self.start_date
        
        while current_date <= self.end_date:
            year, month, day = current_date.year, current_date.month, current_date.day
            
            # Skip the unavailable period (Dec 2025 to May 2026) in the calculated schedule
            if (year == 2025 and month == 12) or (year == 2026 and month <= 5):
                current_date += datetime.timedelta(days=1)
                continue

            if year == 2026 and month in rules:
                weekday = current_date.weekday()

                if weekday in (MONDAY, WEDNESDAY):
                    month_rules = rules[month]
                    
                    if weekday == MONDAY and day not in month_rules[MONDAY]:
                        schedule.add(current_date)
                    
                    elif weekday == WEDNESDAY and day not in month_rules[WEDNESDAY]:
                        schedule.add(current_date)

            current_date += datetime.timedelta(days=1)
            
        return schedule

    def _get_month_range(self) -> List[datetime.date]:
        """Generates a list of the first day of every month in the target range."""
        months = []
        current = self.start_date.replace(day=1)
        last_month = self.end_date.replace(day=1)

        while current <= last_month:
            months.append(current)
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                try:
                    current = current.replace(month=current.month + 1)
                except ValueError:
                    days_in_month = monthrange(current.year, current.month + 1)[1]
                    current = current.replace(month=current.month + 1, day=min(current.day, days_in_month))
        return months


    async def _send_telegram_message(self, message: str):
        """Sends an HTML formatted message to Telegram."""
        try:
            await self.bot.send_message(chat_id=self.telegram_chat_id, text=message, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {e}") # Using logging

    async def _check_month_and_report(self, month_start: datetime.date):
        """
        Checks availability for a single month and reports the findings.
        """
        year = month_start.year
        month = month_start.month
        month_name = month_start.strftime('%B %Y')
        
        is_unavailable_period = (year == 2025 and month == 12) or (year == 2026 and month <= 5)

        if is_unavailable_period:
            month_slots = set() 
        else:
            month_slots = {
                slot for slot in self.full_schedule 
                if slot.year == year and slot.month == month
            }
        
        current_slots_in_month = month_slots
        new_slots_in_month = current_slots_in_month - self.previous_slots 

        if is_unavailable_period:
            # --- TELEGRAM MESSAGE FOR UNAVAILABLE MONTHS ---
            message = f"<b>🔍 Availability Check: {month_name}</b>\n"
            message += f"<b>Location:</b> {self.location}\n"
            message += f"<b>Status:</b> No Appointments Available.\n"
            message += f"<i>Checking again soon...</i>"
            
            await self._send_telegram_message(message)
            logging.info(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Sent Telegram update for {month_name}: No slots.") # Using logging
            # --- END TELEGRAM MESSAGE ---

        elif new_slots_in_month:
            # Code for available months (June 2026 onwards)
            self.previous_slots.update(current_slots_in_month)
            
            message = f"<b>🎉 NEW VISA SLOTS FOUND! 🎉</b>\n"
            message += f"<b>Location:</b> {self.location}\n"
            message += f"<b>Cycle:</b> Constant Alert Mode \n\n"
            message += f"<b>{month_name}:</b>\n"
            
            for slot in sorted(list(new_slots_in_month)):
                message += f"  ✅ <b>{slot.strftime('%Y-%m-%d')} ({slot.strftime('%A')})</b> ← NEW!\n"
            
            message += "\n🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨"
            
            await self._send_telegram_message(message)
            logging.info(f"New slots detected and alert sent for {month_name}!") # Using logging
        
        else:
            self.previous_slots.update(current_slots_in_month)
            logging.info(f"Checking {month_name}, slots previously found in this cycle.") # Using logging


    async def _check_account(self, account: VisaAccount):
        """
        Performs the account check: looks for a slot BEFORE the account's target date.
        """
        
        try:
            # --- DATE PARSING ---
            month_year_str = account.target_month_year
            year, month = map(int, month_year_str.split('-'))
            
            # Use the earliest possible target date as the reference.
            reference_date = datetime.date(year, month, account.target_day_start)
            
            target_range_str = f"Before {reference_date.strftime('%Y-%m-%d')}"
            # --- END DATE PARSING ---

        except Exception as e:
            logging.error(f"[DATA ERROR] Failed to parse date range for account {account.unique_id}: {e}") # Using logging
            return  

        name = f"{account.first_name} {account.last_name}".strip()
        uid = account.unique_id
        
        # Look for ANY slot in the full schedule that is EARLIER than the target date
        earlier_slots_found = {
            slot for slot in self.full_schedule 
            if slot < reference_date
        }

        if earlier_slots_found: 
            message = (
                f"<b>🚨 EARLIER SLOT FOUND! 🚨</b>\n"
                f"<b>Name:</b> {name}\n"
                f"<b>ID:</b> <code>{uid}</code>\n"
                f"<b>Target:</b> {target_range_str}\n\n"
                f"<b>Found Slots:</b>\n"
            )
            for slot in sorted(list(earlier_slots_found))[:5]: # Show up to 5 slots
                message += f"  ✅ <b>{slot.strftime('%Y-%m-%d')} ({slot.strftime('%A')})</b>\n"
            
            message += f"\n<b>ACTION REQUIRED:</b> Log in with email <code>{account.email}</code> to reschedule!"
            
            await self._send_telegram_message(message)
            logging.info(f"EARLIER SLOT FOUND for {name}!") # Using logging

        else:
            # Current status: No earlier slot found
            # Removed the full telegram message to avoid unnecessary spam for every account every cycle
            logging.info(f"No earlier slot yet for {name} (Searching: {target_range_str})") # Using logging


    async def run_async(self):
        """
        Main asynchronous loop that runs BOTH the month spammer and the account checker.
        """
        logging.info(f"Starting combined listener (Async) → Polling every {self.poll_interval}s")
        logging.info(f"Location: {self.location}")
        logging.warning("--- WARNING: Global alerts sent for EVERY month. Account logic is FIXED to check for EARLIER slots. ---")
        
        while True:
            logging.info("\n--- STARTING NEW FULL CYCLE CHECK (COMBINED) ---")
            
            # 1. GLOBAL CHECK
            self.previous_slots.clear()
            logging.info("--- Running Global Slot Checker (Constant Alert Mode) ---")
            for month_start in self.month_iterator:
                try:
                    await self._check_month_and_report(month_start)
                    await asyncio.sleep(1.0) # Small sleep between month checks
                except Exception as e:
                    logging.error(f"Error during month check: {e}")
            
            # 2. ACCOUNT CHECK (Using app_context to safely query DB)
            logging.info("--- Running Account Monitor (Earlier Slot Checker) ---")
            # CRITICAL FIX: The app_context ensures the database connection is available
            with app.app_context():
                try:
                    db.session.remove() # Clean up session before query
                    accounts = VisaAccount.query.all()
                    
                    if not accounts:
                        logging.info("No accounts in database.")
                    else:
                        logging.info(f"Checking {len(accounts)} account(s)...")
                        for account in accounts:
                            try:
                                await self._check_account(account)
                                await asyncio.sleep(1.0) # Small sleep between account checks
                            except Exception as e:
                                logging.error(f"Error checking account {account.unique_id}: {e}")
                    
                    db.session.remove() # Clean up session after query
                except Exception as e:
                    logging.critical(f"CRITICAL ERROR: Failed to query database: {e}")

            logging.info(f"--- Full Cycle Complete. Sleeping {self.poll_interval} seconds. ---")
            await asyncio.sleep(self.poll_interval)
            
# ==================== HOW TO USE ====================
if __name__ == "__main__":
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("ERROR: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set in environment.")
        exit(1)

    listener = VisaSlotListener(
        telegram_token=TELEGRAM_TOKEN,
        telegram_chat_id=int(TELEGRAM_CHAT_ID),
        # CRITICAL FIX: Set poll interval to 5 minutes (300 seconds)
        poll_interval_seconds=300, 
        location="Accra U.S. Embassy/Consulate" 
    )
    
    try:
        asyncio.run(listener.run_async())
    except KeyboardInterrupt:
        logging.info("\nListener stopped by user.")
    except Exception as e:
        logging.fatal(f"Fatal error: {e}")


