# ©️ LISA-KOREA | @LISA_FAN_LK | NT_BOT_CHANNEL | LISA-KOREA/YouTube-Video-Download-Bot

# [⚠️ Do not change this repo link ⚠️] :- https://github.com/LISA-KOREA/YouTube-Video-Download-Bot

import os
import time
import math
import logging
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Youtube.config import Config
from Youtube.forcesub import handle_force_subscribe

youtube_dl_username = None  
youtube_dl_password = None 

# ---------------- UTILS ---------------- #

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    power_labels = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {power_labels[n]}"

def time_formatter(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    (hours, remainder) = divmod(remainder, 3600)
    (minutes, seconds) = divmod(remainder, 60)
    if days:
        result += f"{int(days)}d "
    if hours:
        result += f"{int(hours)}h "
    if minutes:
        result += f"{int(minutes)}m "
    if seconds:
        result += f"{int(seconds)}s"
    return result

async def progress_for_pyrogram(current, total, message, start, status_text="⬇️ Downloading..."):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0:  # update every ~5s
        percentage = current * 100 / total
        speed = current / diff if diff != 0 else 0
        elapsed_time = round(diff)
        time_to_completion = round((total - current) / speed) if speed != 0 else 0
        estimated_total_time = elapsed_time + time_to_completion

        progress_str = "[{0}{1}]".format(
            ''.join(["▰" for i in range(math.floor(percentage / 10))]),
            ''.join(["▱" for i in range(10 - math.floor(percentage / 10))])
        )

        msg_text = f"""
**{status_text}**

{progress_str} {percentage:.2f}%

✅ Done: {humanbytes(current)}
📂 Total: {humanbytes(total)}
🚀 Speed: {humanbytes(speed)}/s
⏱ Time: {time_formatter(estimated_total_time)}
"""

        try:
            await message.edit_text(
                text=msg_text,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⛔ Cancel", callback_data="cancel_download")]]
                )
            )
        except:
            pass

# ---------------- BOT HANDLERS ---------------- #

@Client.on_message(filters.regex(r'^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+'))
async def process_youtube_link(client, message):
    if Config.CHANNEL:
        fsub = await handle_force_subscribe(client, message)
        if fsub == 400:
            return
    youtube_link = message.text
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Best Quality", callback_data=f"download|best|{youtube_link}")],
        [InlineKeyboardButton("1080p", callback_data=f"download|1080p|{youtube_link}")],
        [InlineKeyboardButton("2K", callback_data=f"download|2k|{youtube_link}")],
        [InlineKeyboardButton("4K", callback_data=f"download|4k|{youtube_link}")],
        [InlineKeyboardButton("Medium Quality", callback_data=f"download|medium|{youtube_link}")],
        [InlineKeyboardButton("Low Quality", callback_data=f"download|low|{youtube_link}")]
    ])
    
    await message.reply_text("**Select quality to download**", reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^download\|'))
async def handle_download_button(client, callback_query):
    quality, youtube_link = callback_query.data.split('|')[1:]
    start_time = time.time()

    quality_format = {
        'best': 'best',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '2k': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
        '4k': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
        'medium': 'best[height<=480]',
        'low': 'best[height<=360]'
    }.get(quality, 'best')

    try:
        await callback_query.message.edit_text("**Fetching video info...**")

        def progress_hook(d):
            if d['status'] == 'downloading':
                asyncio.get_event_loop().create_task(
                    progress_for_pyrogram(
                        d.get("downloaded_bytes", 0),
                        d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0),
                        callback_query.message,
                        start_time,
                        "⬇️ Downloading..."
                    )
                )

        ydl_opts = {
            'format': quality_format,
            'outtmpl': 'downloaded_video_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
            'cookiefile': 'cookies.txt'
        }

        if Config.HTTP_PROXY:
            ydl_opts['proxy'] = Config.HTTP_PROXY
        if youtube_dl_username:
            ydl_opts['username'] = youtube_dl_username
        if youtube_dl_password:
            ydl_opts['password'] = youtube_dl_password

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_link, download=False)
            video_id = info_dict.get('id')
            title = info_dict.get('title')
            duration = info_dict.get("duration", 0)

            if title and video_id:
                ydl.download([youtube_link])
                await callback_query.message.edit_text("📤 **Uploading video...**")

                video_filename = f"downloaded_video_{video_id}.mp4"
                if os.path.exists(video_filename):
                    await client.send_video(
                        callback_query.message.chat.id,
                        video=open(video_filename, 'rb'),
                        caption=title,
                        duration=duration,
                        progress=progress_for_pyrogram,
                        progress_args=(callback_query.message, start_time, "📤 Uploading...")
                    )
                    os.remove(video_filename)

                await callback_query.message.edit_text("✅ **Successfully Uploaded!**")
            else:
                logging.error("No video streams found.")
                await callback_query.message.edit_text("❌ Error: No downloadable video found.")

    except yt_dlp.utils.DownloadError as e:
        logging.exception("Error downloading YouTube video: %s", e)
        await callback_query.message.edit_text("❌ Error: The video is unavailable. It may have been removed or is restricted.")
    except Exception as e:
        logging.exception("Error processing YouTube link: %s", e)
        await callback_query.message.edit_text("❌ Error: Failed to process the YouTube link. Please try again later.")
