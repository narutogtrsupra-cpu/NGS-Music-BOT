
import os
import asyncio
from pathlib import Path

import yt_dlp
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]

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
downloads = Path("downloads")
downloads.mkdir(exist_ok=True)

# One current track per group
current_tracks = {}


def find_audio(query):
    """Find one result and return its direct audio stream URL."""
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
        MediaStream(
            source,
            AudioQuality.HIGH,
            video_flags=MediaStream.Flags.IGNORE,
        ),
    )
    current_tracks[chat_id] = title


@bot.on_message(filters.command("start"))
async def start_command(_, message):
    await message.reply_text(
        "🎵 Music Bot\n\n"
        "/play song name — Play online audio\n"
        "/play (reply to audio) — Play a Telegram audio file\n"
        "/pause — Pause\n"
        "/resume — Resume\n"
        "/skip — Stop current track\n"
        "/end — Leave voice chat\n"
        "/queue — Show current track"
    )


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
            path = await bot.download_media(
                reply,
                file_name=str(downloads) + "/",
            )

            if not path:
                raise ValueError("Could not download the audio file.")

            title = getattr(media, "file_name", None) or "Telegram audio"
            source = str(path)

        else:
            query = " ".join(message.command[1:]).strip()

            if not query:
                await message.reply_text(
                    "Use /play song name, or reply to an audio file with /play."
                )
                return

            status = await message.reply_text("🔎 Finding audio...")
            source, title = await asyncio.to_thread(find_audio, query)
            await status.delete()

        await start_track(chat_id, source, title)
        await message.reply_text(f"🎶 Playing: {title}")

    except Exception as exc:
        await message.reply_text(
            f"Couldn't play that track: {str(exc)[:250]}"
        )


@bot.on_message(filters.command("pause") & filters.group)
async def pause_command(_, message):
    try:
        await calls.pause(message.chat.id)
        await message.reply_text("⏸️ Paused.")
    except Exception as exc:
        await message.reply_text(f"Pause failed: {str(exc)[:200]}")


@bot.on_message(filters.command("resume") & filters.group)
async def resume_command(_, message):
    try:
        await calls.resume(message.chat.id)
        await message.reply_text("▶️ Resumed.")
    except Exception as exc:
        await message.reply_text(f"Resume failed: {str(exc)[:200]}")


@bot.on_message(filters.command("skip") & filters.group)
async def skip_command(_, message):
    try:
        await calls.leave_call(message.chat.id)
        current_tracks.pop(message.chat.id, None)
        await message.reply_text(
            "⏭️ Stopped the current track. Queue support comes next."
        )
    except Exception as exc:
        await message.reply_text(f"Skip failed: {str(exc)[:200]}")


@bot.on_message(filters.command("end") & filters.group)
async def end_command(_, message):
    try:
        await calls.leave_call(message.chat.id)
        current_tracks.pop(message.chat.id, None)
        await message.reply_text("⏹️ Music stopped.")
    except Exception as exc:
        await message.reply_text(f"Couldn't stop playback: {str(exc)[:200]}")


@bot.on_message(filters.command("queue") & filters.group)
async def queue_command(_, message):
    title = current_tracks.get(message.chat.id)
    if title:
        await message.reply_text(f"🎵 Now playing: {title}")
    else:
        await message.reply_text("Nothing is playing right now.")


async def main():
    await user.start()
    await bot.start()
    calls.start()

    print("Music bot started.")
    try:
        await idle()
    finally:
        calls.stop()
        await bot.stop()
        await user.stop()


if __name__ == "__main__":
    asyncio.run(main())
