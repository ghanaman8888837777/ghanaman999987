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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CRITICAL IMPORTS FOR DATABASE ACCESS (FIXED) ---
from app import app
from models import db, VisaAccount 
# --- END CRITICAL IMPORTS ---

# Weekday constants
MONDAY = 0
WEDNESDAY = 2

# CRITICAL FIX: The entire outdated context block is removed.

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
        # TIMING CHANGE: Changed default cycle poll interval to 15 seconds
        poll_interval_seconds: int = 15, 
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
        
        # NOTE: New attribute for inner Telegram delays
        self.telegram_delay_seconds = 5 

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
                    current = current.replace(month=current.month + 1, day=min(current.day, days_in.month))
        return months


    async def _send_telegram_message(self, message: str):
        """Sends an HTML formatted message to Telegram."""
        try:
            await self.bot.send_message(chat_id=self.telegram_chat_id, text=message, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {e}")

    async def _check_month_and_report(self, month_start: datetime.date):
        # ... (implementation remains the same) ...
        # [No changes needed in this function aside from the calling logic in run_async]
        
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
            message = f"<b>🔍 Availability Check: {month_name}</b>\n"
            message += f"<b>Location:</b> {self.location}\n"
            message += f"<b>Status:</b> No Appointments Available.\n"
            message += f"<i>Checking again soon...</i>"
            
            await self._send_telegram_message(message)
            logging.info(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Sent Telegram update for {month_name}: No slots.")

        elif new_slots_in_month:
            self.previous_slots.update(current_slots_in_month)
            
            message = f"<b>🎉 NEW VISA SLOTS FOUND! 🎉</b>\n"
            message += f"<b>Location:</b> {self.location}\n"
            message += f"<b>Cycle:</b> Constant Alert Mode \n\n"
            message += f"<b>{month_name}:</b>\n"
            
            for slot in sorted(list(new_slots_in_month)):
                message += f"  ✅ <b>{slot.strftime('%Y-%m-%d')} ({slot.strftime('%A')})</b> ← NEW!\n"
            
            message += "\n🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨"
            
            await self._send_telegram_message(message)
            logging.info(f"New slots detected and alert sent for {month_name}!")
        
        else:
            self.previous_slots.update(current_slots_in_month)
            logging.info(f"Checking {month_name}, slots previously found in this cycle.")


    async def _check_account(self, account: VisaAccount):
        # ... (implementation remains the same) ...
        # [No changes needed in this function aside from the calling logic in run_async]
        
        try:
            month_year_str = account.target_month_year
            year, month = map(int, month_year_str.split('-'))
            reference_date = datetime.date(year, month, account.target_day_start)
            target_range_str = f"Before {reference_date.strftime('%Y-%m-%d')}"
        except Exception as e:
            logging.error(f"[DATA ERROR] Failed to parse date range for account {account.unique_id}: {e}")
            return  

        name = f"{account.first_name} {account.last_name}".strip()
        uid = account.unique_id
        
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
            for slot in sorted(list(earlier_slots_found))[:5]:
                message += f"  ✅ <b>{slot.strftime('%Y-%m-%d')} ({slot.strftime('%A')})</b>\n"
            
            message += f"\n<b>ACTION REQUIRED:</b> Log in with email <code>{account.email}</code> to reschedule!"
            
            await self._send_telegram_message(message)
            logging.info(f"EARLIER SLOT FOUND for {name}!")

        else:
            logging.info(f"No earlier slot yet for {name} (Searching: {target_range_str})")


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
                    # TIMING CHANGE: 5-second break between month checks/updates
                    await asyncio.sleep(self.telegram_delay_seconds) 
                except Exception as e:
                    logging.error(f"Error during month check: {e}")
            
            # 2. ACCOUNT CHECK (Using app_context to safely query DB)
            logging.info("--- Running Account Monitor (Earlier Slot Checker) ---")
            with app.app_context():
                try:
                    db.session.remove()
                    accounts = VisaAccount.query.all()
                    
                    if not accounts:
                        logging.info("No accounts in database.")
                    else:
                        logging.info(f"Checking {len(accounts)} account(s)...")
                        for account in accounts:
                            try:
                                await self._check_account(account)
                                # TIMING CHANGE: 5-second break between account checks/updates
                                await asyncio.sleep(self.telegram_delay_seconds) 
                            except Exception as e:
                                logging.error(f"Error checking account {account.unique_id}: {e}")
                    
                    db.session.remove()
                except Exception as e:
                    logging.critical(f"CRITICAL ERROR: Failed to query database: {e}")

            logging.info(f"--- Full Cycle Complete. Sleeping {self.poll_interval} seconds. ---")
            # TIMING CHANGE: 15-second break before the next cycle starts
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
        # TIMING CHANGE: Main loop poll interval set to 15 seconds
        poll_interval_seconds=15, 
        location="Accra U.S. Embassy/Consulate" 
    )
    
    try:
        asyncio.run(listener.run_async())
    except KeyboardInterrupt:
        logging.info("\nListener stopped by user.")
    except Exception as e:
        logging.fatal(f"Fatal error: {e}")
