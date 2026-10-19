import os
import asyncio
from pyrogram import Client, idle
from pytgcalls import PyTgCalls

# 1. Fetch and validate environment variables
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

if not API_ID or not API_HASH or not SESSION_STRING:
    raise ValueError("Missing required environment variables: API_ID, API_HASH, or SESSION_STRING.")

# Convert API_ID to integer (crucial for Pyrogram)
API_ID = int(API_ID)

# 2. Initialize the Pyrogram User/Bot Client using the Session String
app = Client(
    name="NGS_Music_Bot",
    api_id=31240366,
    api_hash=c24e5f042bf1689e471c4f0288984a19,
    session_string=BQHcsK4AXZbXeuV2K_R6QFxQQkg4FY4JgYL8lWOt6yk8mxW9l0DP0YcKnFtGRjmR4lH4cJd7e62sigbhB8IbODGoL9BqG4shaGv_Y5_j2zPBSuuMkjujWD8N1VbJn3QS66hX4xxy6ESVun1EjBmm4mSTStEbwBBpYM1XKkzD6RjiCYAORoSabXDWZl5A4F_0pwi5m1Pd1q_L7PA__mw9g1st_K8kY9Hky4jHFfJzMEON4vzAfXzuQW7GpDqIdnWV_u1pBnJCGEANm0NZoqLG-OReNetW1Z_fnosc0FRqj0hHJezqL1nhtVx2Ahj3ParwE7o7ZknR2P95mAL1dXYOuHdPthpXswAAAAG7ZHk-AA
)

# 3. Initialize PyTgCalls for Voice Chat streaming
call_py = PyTgCalls(app)

async def main():
    print("Starting Pyrogram Client...")
    await app.start()
    
    print("Starting PyTgCalls Voice Chat handler...")
    await call_py.start()
    
    print("NGS-Music-BOT is successfully running and online!")
    
    # Keeps the script alive and listening for telegram events/commands
    await idle()
    
    # Graceful shutdown
    print("Stopping bot...")
    await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped manually.")
