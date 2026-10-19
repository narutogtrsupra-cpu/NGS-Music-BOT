
import os
import asyncio
from pathlib import Path

import yt_dlp
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality

# =========================
# CONFIGURATION
# =========================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# =========================
# TELEGRAM CLIENTS
# =========================

bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

user = Client(
    "music_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)

calls = PyTgCalls(user)
current_tracks = {}


# =========================
# AUDIO SEARCH
# =========================

def find_audio(query):
    options = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "default_search": "ytsearch1",
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(query, download=False)

        if "entries" in info:
            info = next(
                (item for item in info["entries"] if item),
                None,
            )

        if not info or not info.get("url"):
            raise ValueError("No playable audio found.")

        return info["url"], info.get("title", query)


async def start_track(chat_id, source, title):
    await calls.play(
        chat_id,
        MediaStream(source, AudioQuality.HIGH),
    )
    current_tracks[chat_id] = title


# =========================
# START COMMAND
# =========================

@bot.on_message(filters.command("start"))
async def start_command(_, message):
    await message.reply_text(
        "🎵 Welcome to Music Bot!\n\n"
        "/play song name - Play online audio\n"
        "/play (reply to audio) - Play Telegram audio\n"
        "/pause - Pause music\n"
        "/resume - Resume music\n"
        "/skip - Stop current track\n"
        "/end - Stop and leave voice chat\n"
        "/queue - Show current track"
    )


# =========================
# PLAY COMMAND
# =========================

@bot.on_message(filters.command("play") & filters.group)
async def play_command(_, message):
    chat_id = message.chat.id
    reply = message.reply_to_message

    try:
        if reply and (
            reply.audio
            or reply.voice
            or (
                reply.document
                and (reply.document.mime_type or "").startswith("audio/")
            )
        ):
            media = reply.audio or reply.voice or reply.document

            status = await message.reply_text(
                "⬇️ Downloading Telegram audio..."
            )

            path = await bot.download_media(
                reply,
                file_name=str(DOWNLOAD_DIR) + "/",
            )

            if not path:
                raise ValueError("Failed to download audio.")

            title = (
                getattr(media, "file_name", None)
                or getattr(media, "title", None)
                or "Telegram audio"
            )

            source = str(path)
            await status.delete()

        else:
            query = " ".join(message.command[1:]).strip()

            if not query:
                await message.reply_text(
                    "Usage: /play song name\n"
                    "Or reply to an audio file with /play."
                )
                return

            status = await message.reply_text(
                "🔎 Searching for your song..."
            )

            source, title = await asyncio.to_thread(
                find_audio, query
            )

            await status.delete()

        await start_track(chat_id, source, title)
        await message.reply_text(f"🎶 Now playing: {title}")

    except Exception as exc:
        await message.reply_text(
            f"❌ Playback failed: {str(exc)[:250]}"
        )


# =========================
# PAUSE COMMAND
# =========================

@bot.on_message(filters.command("pause") & filters.group)
async def pause_command(_, message):
    try:
        await calls.pause(message.chat.id)
        await message.reply_text("⏸️ Music paused.")
    except Exception as exc:
        await message.reply_text(
            f"❌ Pause failed: {str(exc)[:200]}"
        )


# =========================
# RESUME COMMAND
# =========================

@bot.on_message(filters.command("resume") & filters.group)
async def resume_command(_, message):
    try:
        await calls.resume(message.chat.id)
        await message.reply_text("▶️ Music resumed.")
    except Exception as exc:
        await message.reply_text(
            f"❌ Resume failed: {str(exc)[:200]}"
        )


# =========================
# SKIP COMMAND
# =========================

@bot.on_message(filters.command("skip") & filters.group)
async def skip_command(_, message):
    try:
        await calls.leave_call(message.chat.id)
        current_tracks.pop(message.chat.id, None)
        await message.reply_text(
            "⏭️ Track stopped. Queue support is not enabled yet."
        )
    except Exception as exc:
        await message.reply_text(
            f"❌ Skip failed: {str(exc)[:200]}"
        )


# =========================
# END COMMAND
# =========================

@bot.on_message(filters.command("end") & filters.group)
async def end_command(_, message):
    try:
        await calls.leave_call(message.chat.id)
        current_tracks.pop(message.chat.id, None)
        await message.reply_text("⏹️ Music stopped.")
    except Exception as exc:
        await message.reply_text(
            f"❌ Stop failed: {str(exc)[:200]}"
        )


# =========================
# QUEUE COMMAND
# =========================

@bot.on_message(filters.command("queue") & filters.group)
async def queue_command(_, message):
    title = current_tracks.get(message.chat.id)

    if title:
        await message.reply_text(f"🎵 Now playing: {title}")
    else:
        await message.reply_text("🎵 Nothing is playing.")


# =========================
# STARTUP AND SHUTDOWN
# =========================

async def main():
    print("Starting Telegram Music Bot...", flush=True)

    try:
        await user.start()
        print("Telegram user session started.", flush=True)

        await bot.start()
        print("Telegram bot started.", flush=True)

        await calls.start()
        print("Voice chat engine started.", flush=True)

        print("Bot is running and waiting for commands.", flush=True)

        await idle()

    finally:
        print("Stopping Music Bot...", flush=True)

        try:
            await calls.stop()
        except Exception as exc:
            print(f"Voice engine shutdown: {exc}", flush=True)

        try:
            await bot.stop()
        except Exception as exc:
            print(f"Bot shutdown: {exc}", flush=True)

        try:
            await user.stop()
        except Exception as exc:
            print(f"User shutdown: {exc}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
