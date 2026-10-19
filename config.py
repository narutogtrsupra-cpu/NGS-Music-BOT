import os

API_ID = int(os.getenv("API_ID", "1234567"))
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH")

# Reads the token saved as TELEGRAM_BOT_TOKEN by FadeHost
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN"))

# User helper session string for streaming into group Voice Chats
SESSION_STRING = os.getenv("SESSION_STRING", "YOUR_PYROGRAM_STRING_SESSION")
