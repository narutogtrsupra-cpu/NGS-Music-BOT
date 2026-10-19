import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import yt_dlp

import config

# Initialize Pyrogram Clients
bot = Client(
    "MusicBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

user = Client(
    "MusicAssistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION_STRING
)

# Initialize PyTgCalls Engine
call_py = PyTgCalls(user)

# Active queues per chat: {chat_id: [{"title": str, "url": str}]}
queues = {}


def fetch_audio_url(query: str) -> tuple[str, str]:
    """Search YouTube and extract raw stream URL using yt-dlp."""
    ydl_opts = {
        "format": "bestaudio/best",
        "default_search": "ytsearch1",
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return info["url"], info.get("title", "Unknown Track")


@bot.on_message(filters.command("start"))
async def start_cmd(_, message: Message):
    await message.reply_text(
        "🎶 **Telegram VC Music Bot Active!**\n\n"
        "**Available Commands:**\n"
        "• `/play <song name/link>` - Play audio in Group VC\n"
        "• `/pause` - Pause audio stream\n"
        "• `/resume` - Resume audio stream\n"
        "• `/skip` - Skip current track\n"
        "• `/stop` - Stop audio & leave VC"
    )


@bot.on_message(filters.command("play") & filters.group)
async def play_cmd(_, message: Message):
    chat_id = message.chat.id

    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a song name or link!\nExample: `/play Faded`")
        return

    query = message.text.split(maxsplit=1)[1]
    msg = await message.reply_text("🔎 **Searching track...**")

    loop = asyncio.get_event_loop()
    try:
        stream_url, title = await loop.run_in_executor(None, fetch_audio_url, query)
    except Exception as e:
        await msg.edit_text(f"❌ Failed to fetch track: `{str(e)}`")
        return

    if chat_id not in queues:
        queues[chat_id] = []

    queues[chat_id].append({"title": title, "url": stream_url})

    if len(queues[chat_id]) > 1:
        await msg.edit_text(f"➕ **Queued at position #{len(queues[chat_id])}:** `{title}`")
        return

    try:
        await call_py.join_group_call(
            chat_id,
            AudioPiped(stream_url)
        )
        await msg.edit_text(f"▶️ **Now Playing:** `{title}`")
    except Exception as e:
        queues[chat_id].pop(0)
        await msg.edit_text(f"❌ Error joining VC: `{str(e)}`\nMake sure VC is active in this group!")


@bot.on_message(filters.command("skip") & filters.group)
async def skip_cmd(_, message: Message):
    chat_id = message.chat.id

    if chat_id not in queues or not queues[chat_id]:
        await message.reply_text("❌ Nothing is currently playing.")
        return

    queues[chat_id].pop(0)

    if queues[chat_id]:
        next_track = queues[chat_id][0]
        await call_py.change_stream(chat_id, AudioPiped(next_track["url"]))
        await message.reply_text(f"⏭️ **Skipped! Now Playing:** `{next_track['title']}`")
    else:
        await call_py.leave_group_call(chat_id)
        await message.reply_text("🏁 **Queue finished. Left voice chat.**")


@bot.on_message(filters.command("pause") & filters.group)
async def pause_cmd(_, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.pause_stream(chat_id)
        await message.reply_text("⏸️ **Playback Paused.**")
    except Exception:
        await message.reply_text("❌ No active stream found.")


@bot.on_message(filters.command("resume") & filters.group)
async def resume_cmd(_, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.resume_stream(chat_id)
        await message.reply_text("▶️ **Playback Resumed.**")
    except Exception:
        await message.reply_text("❌ No active stream paused.")


@bot.on_message(filters.command("stop") & filters.group)
async def stop_cmd(_, message: Message):
    chat_id = message.chat.id
    if chat_id in queues:
        queues[chat_id].clear()

    try:
        await call_py.leave_group_call(chat_id)
        await message.reply_text("⏹️ **Stopped playback & left Voice Chat.**")
    except Exception:
        await message.reply_text("❌ Bot is not in VC.")


async def main():
    await user.start()
    await bot.start()
    await call_py.start()
    print("🚀 Music Bot Started Successfully!")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
