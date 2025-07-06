# ---------------------------------------------------
# File Name: func.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.5
# License: MIT License
# ---------------------------------------------------

import math
import time , re
from pyrogram import enums
from config import CHANNEL_ID, OWNER_ID 
from devgagan.core.mongo.plans_db import premium_users
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import cv2
from pyrogram.errors import FloodWait, InviteHashInvalid, InviteHashExpired, UserAlreadyParticipant, UserNotParticipant
from datetime import datetime as dt
import asyncio, subprocess, re, os, time
async def chk_user(message, user_id):
    user = await premium_users()
    if user_id in user or user_id in OWNER_ID:
        return 0
    else:
        return 1
async def gen_link(app,chat_id):
   link = await app.export_chat_invite_link(chat_id)
   return link

async def subscribe(app, message):
   update_channel = CHANNEL_ID
   url = await gen_link(app, update_channel)
   if update_channel:
      try:
         user = await app.get_chat_member(update_channel, message.from_user.id)
         if user.status == "kicked":
            await message.reply_text("You are Banned. Contact -- @arsh_beniwal")
            return 1
      except UserNotParticipant:
        caption = f"Join our channel to use the bot"
        await message.reply_photo(photo="https://files.catbox.moe/w10e8w.jpg",caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Now...", url=f"{url}")]]))
        return 1
      except Exception:
         await message.reply_text("Something Went Wrong. Contact us @arsh_beniwal...")
         return 1
async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""

        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1

        unit = ts[index:].lstrip()

        if value:
            value = int(value)

        return value, unit

    value, unit = extract_value_and_unit(time_string)

    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0
PROGRESS_BAR = """\n
│ **__Completed:__** {1}/{2}
│ **__Bytes:__** {0}%
│ **__Speed:__** {3}/s
│ **__ETA:__** {4}
╰─────────────────────╯
"""
# ... existing imports and code ...

# Remove size limit checks
async def progress_bar(current, total, ud_type, message, start):
    # ... existing progress bar implementation ...
    pass

# Enhanced for large files
def humanbytes(size):
    # Convert bytes to human-readable format
    if not size:
        return ""
    power = 2**10
    n = 0
    units = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {units.get(n, 'B')}"

# ... existing code ...

async def screenshot(video, duration, sender):
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    
    # Create thumbnail at 10% of duration
    time_stamp = hhmmss(int(duration) * 0.1)
    out = f"{sender}.jpg"
    
    # Use FFmpeg to generate thumbnail
    cmd = [
        "ffmpeg",
        "-ss", time_stamp,
        "-i", video,
        "-frames:v", "1",
        out,
        "-y"
    ]
    
    # ... existing subprocess code ...
    return out

# Improved progress callback for large files
async def progress_callback(current, total, progress_message, user_id):
    percent = (current / total) * 100
    completed_blocks = int(percent // 5)
    progress_bar = "⬢" * completed_blocks + "⬡" * (20 - completed_blocks)
    
    # Calculate speed
    elapsed = time.time() - user_progress[user_id]['start_time']
    speed = current / elapsed if elapsed > 0 else 0
    
    # Calculate ETA
    remaining = total - current
    eta = remaining / speed if speed > 0 else 0
    
    # Format progress message
    progress_text = (
        f"**Uploading Large File**\n"
        f"{progress_bar}\n"
        f"**Progress:** {percent:.2f}%\n"
        f"**Done:** {humanbytes(current)}/{humanbytes(total)}\n"
        f"**Speed:** {humanbytes(speed)}/s\n"
        f"**ETA:** {convert(eta)}"
    )
    
    try:
        await progress_message.edit(progress_text)
    except:
        pass

# Time formatter for ETA
def convert(seconds):
    if seconds < 0:
        return "N/A"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

# ... rest of the file remains the same ...
async def userbot_join(userbot, invite_link):
    try:
        await userbot.join_chat(invite_link)
        return "Successfully joined the Channel"
    except UserAlreadyParticipant:
        return "User is already a participant."
    except (InviteHashInvalid, InviteHashExpired):
        return "Could not join. Maybe your link is expired or Invalid."
    except FloodWait:
        return "Too many requests, try again later."
    except Exception as e:
        print(e)
        return "Could not join, try joining manually."
def get_link(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)   
    try:
        link = [x[0] for x in url][0]
        if link:
            return link
        else:
            return False
    except Exception:
        return False
def video_metadata(file):
    default_values = {'width': 1, 'height': 1, 'duration': 1}
    try:
        vcap = cv2.VideoCapture(file)
        if not vcap.isOpened():
            return default_values  

        width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = vcap.get(cv2.CAP_PROP_FPS)
        frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)

        if fps <= 0:
            return default_values  

        duration = round(frame_count / fps)
        if duration <= 0:
            return default_values  

        vcap.release()
        return {'width': width, 'height': height, 'duration': duration}

    except Exception as e:
        print(f"Error in video_metadata: {e}")
        return default_values

def hhmmss(seconds):
    return time.strftime('%H:%M:%S',time.gmtime(seconds))

async def screenshot(video, duration, sender):
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    time_stamp = hhmmss(int(duration)/2)
    out = dt.now().isoformat("_", "seconds") + ".jpg"
    cmd = ["ffmpeg",
           "-ss",
           f"{time_stamp}", 
           "-i",
           f"{video}",
           "-frames:v",
           "1", 
           f"{out}",
           "-y"
          ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    x = stderr.decode().strip()
    y = stdout.decode().strip()
    if os.path.isfile(out):
        return out
    else:
        None  
last_update_time = time.time()
async def progress_callback(current, total, progress_message):
    percent = (current / total) * 100
    global last_update_time
    current_time = time.time()

    if current_time - last_update_time >= 10 or percent % 10 == 0:
        completed_blocks = int(percent // 10)
        remaining_blocks = 10 - completed_blocks
        progress_bar = "♦" * completed_blocks + "◇" * remaining_blocks
        current_mb = current / (1024 * 1024)  
        total_mb = total / (1024 * 1024)      
        await progress_message.edit(
    f"╭──────────────────╮\n"
    f"│        **__Uploading...__**       \n"
    f"├──────────\n"
    f"│ {progress_bar}\n\n"
    f"│ **__Progress:__** {percent:.2f}%\n"
    f"│ **__Uploaded:__** {current_mb:.2f} MB / {total_mb:.2f} MB\n"
    f"╰──────────────────╯\n\n"
    f"**__Powered by Team JB__**"
        )

        last_update_time = current_time
async def prog_bar(current, total, ud_type, message, start):

    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:

        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["♦" for i in range(math.floor(percentage / 10))]),
            ''.join(["◇" for i in range(10 - math.floor(percentage / 10))]))

        tmp = progress + PROGRESS_BAR.format( 
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),

            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit_text(
                text="{}\n│ {}".format(ud_type, tmp),)             

        except:
            pass
