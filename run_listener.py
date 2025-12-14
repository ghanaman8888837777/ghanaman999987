# run_listener.py
from visa_listener import VisaSlotListener
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

listener = VisaSlotListener(
    telegram_token=os.getenv("TELEGRAM_TOKEN"),
    telegram_chat_id=int(os.getenv("TELEGRAM_CHAT_ID")),
    poll_interval_seconds=3,
    location="Accra U.S. Embassy/Consulate"
)

asyncio.run(listener.run_async())