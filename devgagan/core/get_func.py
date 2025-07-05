# ---------------------------------------------------
# File Name: get_func.py
# Description: Telegram bot for file transfer with 4GB support
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Version: 2.0.6
# ---------------------------------------------------

import asyncio
import time
import gc
import os
import re
import math
from devgagan import app
import aiofiles
from devgagan import sex as gf
from telethon.tl.types import DocumentAttributeVideo
import pymongo
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid
from pyrogram.enums import MessageMediaType, ParseMode
from devgagan.core.func import *
from pyrogram.errors import RPCError
from config import MONGO_DB as MONGODB_CONNECTION_STRING, LOG_GROUP, OWNER_ID, STRING
from devgagan.core.mongo import db as odb
from telethon import events, Button
from devgagantools import fast_upload

def humanbytes(size):
    if not size: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024: break
        size /= 1024
    return f"{size:.2f} {unit}"

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s") if seconds else "")
    return tmp[:-2] if tmp.endswith(", ") else tmp or "0s"

def thumbnail(sender):
    return f'{sender}.jpg' if os.path.exists(f'{sender}.jpg') else None

# MongoDB setup
DB_NAME = "smart_users"
COLLECTION_NAME = "super_user"
mongo_app = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = mongo_app[DB_NAME]
collection = db[COLLECTION_NAME]

VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'webm', 'mpg', 'mpeg', '3gp', 'ts', 'm4v', 'f4v', 'vob']

if STRING:
    from devgagan import pro
    print("App imported from devgagan.")
else:
    pro = None
    print("STRING not available. 'app' set to None.")
    
async def fetch_upload_method(user_id):
    user_data = collection.find_one({"user_id": user_id})
    return user_data.get("upload_method", "Pyrogram") if user_data else "Pyrogram"

async def format_caption_to_html(caption: str) -> str:
    replacements = [
        (r"^> (.*)", r"<blockquote>\1</blockquote>"),
        (r"```(.*?)```", r"<pre>\1</pre>"),
        (r"`(.*?)`", r"<code>\1</code>"),
        (r"\*\*(.*?)\*\*", r"<b>\1</b>"),
        (r"\*(.*?)\*", r"<b>\1</b>"),
        (r"__(.*?)__", r"<i>\1</i>"),
        (r"_(.*?)_", r"<i>\1</i>"),
        (r"~~(.*?)~~", r"<s>\1</s>"),
        (r"\|\|(.*?)\|\|", r"<details>\1</details>"),
        (r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>')
    ]
    for pattern, replacement in replacements:
        caption = re.sub(pattern, replacement, caption, flags=re.DOTALL|re.MULTILINE)
    return caption.strip() if caption else None
    

async def upload_media(sender, target_chat_id, file, caption, edit, topic_id):
    try:
        upload_method = await fetch_upload_method(sender)
        metadata = video_metadata(file)
        width, height, duration = metadata['width'], metadata['height'], metadata['duration']
        thumb_path = await screenshot(file, duration, sender) if duration else None

        file_extension = str(file).split('.')[-1].lower()
        
        # Pyrogram upload
        if upload_method == "Pyrogram":
            if file_extension in VIDEO_EXTENSIONS:
                dm = await app.send_video(
                    chat_id=target_chat_id,
                    video=file,
                    caption=caption,
                    height=height,
                    width=width,
                    duration=duration,
                    thumb=thumb_path,
                    reply_to_message_id=topic_id,
                    parse_mode=ParseMode.MARKDOWN,
                    progress=progress_bar,
                    progress_args=("╭─────────────────────╮\n│      **__Pyro Uploader__**\n├─────────────────────", edit, time.time())
                )
                await dm.copy(LOG_GROUP)
                
            elif file_extension in ['jpg', 'png', 'jpeg']:
                dm = await app.send_photo(
                    chat_id=target_chat_id,
                    photo=file,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    progress=progress_bar,
                    reply_to_message_id=topic_id,
                    progress_args=("╭─────────────────────╮\n│      **__Pyro Uploader__**\n├─────────────────────", edit, time.time())
                )
                await dm.copy(LOG_GROUP)
            else:
                dm = await app.send_document(
                    chat_id=target_chat_id,
                    document=file,
                    caption=caption,
                    thumb=thumb_path,
                    reply_to_message_id=topic_id,
                    progress=progress_bar,
                    parse_mode=ParseMode.MARKDOWN,
                    progress_args=("╭─────────────────────╮\n│      **__Pyro Uploader__**\n├─────────────────────", edit, time.time())
                )
                await asyncio.sleep(2)
                await dm.copy(LOG_GROUP)

        # Telethon upload
        elif upload_method == "Telethon":
            await edit.delete()
            progress_message = await gf.send_message(sender, "**__Uploading...__**")
            caption = await format_caption_to_html(caption)
            uploaded = await fast_upload(
                gf, file,
                reply=progress_message,
                name=os.path.basename(file),
                progress_bar_function=lambda done, total: progress_callback(done, total, sender),
                user_id=sender
            )
            await progress_message.delete()

            attributes = [
                DocumentAttributeVideo(
                    duration=duration,
                    w=width,
                    h=height,
                    supports_streaming=True
                )
            ] if file_extension in VIDEO_EXTENSIONS else []

            await gf.send_file(
                target_chat_id,
                uploaded,
                caption=caption,
                attributes=attributes,
                reply_to=topic_id,
                parse_mode='html',
                thumb=thumb_path
            )
            await gf.send_file(
                LOG_GROUP,
                uploaded,
                caption=caption,
                attributes=attributes,
                parse_mode='html',
                thumb=thumb_path
            )

        os.remove(file)
    except Exception as e:
        await app.send_message(LOG_GROUP, f"**Upload Failed:** {str(e)}")
        print(f"Error during media upload: {e}")
    finally:
        if thumb_path and os.path.exists(thumb_path) and os.path.basename(thumb_path) != f"{sender}.jpg":
            os.remove(thumb_path)
        gc.collect()

async def chunked_download(userbot, msg, file_name, edit, sender):
    try:
        os.makedirs("downloads", exist_ok=True)
        file_path = os.path.join("downloads", file_name)
        total_size = get_message_file_size(msg) or 1
        start_time = time.time()
        downloaded = 0
        chunk_size = 10 * 1024 * 1024
        last_update = 0
        
        async with aiofiles.open(file_path, 'wb') as f:
            async for chunk in userbot.iter_download(msg.media, chunk_size=chunk_size):
                await f.write(chunk)
                downloaded += len(chunk)
                if downloaded - last_update >= 50 * 1024 * 1024 or downloaded == total_size:
                    await update_download_progress(edit, start_time, downloaded, total_size)
                    last_update = downloaded
        
        return file_path
    except Exception as e:
        print(f"Chunked download error: {e}")
        return None

async def update_download_progress(edit, start_time, downloaded, total):
    try:
        elapsed = time.time() - start_time
        percentage = (downloaded / total) * 100
        speed = downloaded / elapsed if elapsed > 0 else 0
        eta = (total - downloaded) / speed if speed > 0 else 0
        
        progress_bar_length = 20
        completed_blocks = int(progress_bar_length * (percentage / 100))
        progress_bar = "♦" * completed_blocks + "◇" * (progress_bar_length - completed_blocks)
        
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        speed_mb = speed / (1024 * 1024)
        eta_min, eta_sec = divmod(eta, 60)
        
        progress_text = (
            f"╭─────────────────────╮\n"
            f"│      **__Chunked Download__**\n"
            f"├─────────────────────\n"
            f"│ {progress_bar} {percentage:.1f}%\n"
            f"│ **Size:** {downloaded_mb:.1f}MB / {total_mb:.1f}MB\n"
            f"│ **Speed:** {speed_mb:.2f} MB/s\n"
            f"│ **ETA:** {int(eta_min)}m {int(eta_sec)}s\n"
            f"╰─────────────────────╯"
        )
        
        await edit.edit(progress_text)
    except Exception as e:
        print(f"Progress update error: {e}")

async def get_msg(userbot, sender, edit_id, msg_link, i, message):
    try:
        msg_link = msg_link.split("?single")[0]
        chat, msg_id = None, None
        saved_channel_ids = load_saved_channel_ids()
        size_limit = 4 * 1024 * 1024 * 1024
        file = ''
        edit = ''
        
        if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
            parts = msg_link.split("/")
            if 't.me/b/' in msg_link:
                chat = parts[-2]
                msg_id = int(parts[-1]) + i
            else:
                chat = int('-100' + parts[parts.index('c') + 1])
                msg_id = int(parts[-1]) + i

            if chat in saved_channel_ids:
                await app.edit_message_text(message.chat.id, edit_id, "Sorry! This channel is protected.")
                return
            
        elif '/s/' in msg_link:
            edit = await app.edit_message_text(sender, edit_id, "Story Link Detected...")
            if not userbot:
                await edit.edit("Login in bot save stories...")     
                return
            parts = msg_link.split("/")
            chat = f"-100{parts[3]}" if parts[3].isdigit() else parts[3]
            msg_id = int(parts[-1])
            await download_user_stories(userbot, chat, msg_id, edit, sender)
            await edit.delete()
            return
        
        else:
            edit = await app.edit_message_text(sender, edit_id, "Public link detected...")
            chat = msg_link.split("t.me/")[1].split("/")[0]
            msg_id = int(msg_link.split("/")[-1])
            await copy_message_with_chat_id(app, userbot, sender, chat, msg_id, edit)
            await edit.delete()
            return
            
        msg = await userbot.get_messages(chat, msg_id)
        if msg.service or msg.empty:
            await app.delete_messages(sender, edit_id)
            return

        target_chat_id = user_chat_ids.get(message.chat.id, message.chat.id)
        topic_id = None
        if '/' in str(target_chat_id):
            target_chat_id, topic_id = map(int, target_chat_id.split('/', 1))

        if msg.media == MessageMediaType.WEB_PAGE_PREVIEW:
            await clone_message(app, msg, target_chat_id, topic_id, edit_id, LOG_GROUP)
            return

        if msg.text:
            await clone_text_message(app, msg, target_chat_id, topic_id, edit_id, LOG_GROUP)
            return

        if msg.sticker:
            await handle_sticker(app, msg, target_chat_id, topic_id, edit_id, LOG_GROUP)
            return

        file_size = get_message_file_size(msg)
        free_check = 0
        file_name = await get_media_filename(msg)
        edit = await app.edit_message_text(sender, edit_id, "**Downloading...**")

        if file_size > 1 * 1024 * 1024 * 1024:
            file = await chunked_download(userbot, msg, file_name, edit, sender)
        else:
            file = await userbot.download_media(
                msg,
                file_name=file_name,
                progress=progress_bar,
                progress_args=("╭─────────────────────╮\n│      **__Downloading__...**\n├─────────────────────", edit, time.time())
            )
        
        if not file:
            await edit.edit("**❌ Download failed!**")
            return
        
        caption = await get_final_caption(msg, sender)
        file = await rename_file(file, sender)
        
        if msg.audio:
            result = await app.send_audio(target_chat_id, file, caption=caption, reply_to_message_id=topic_id)
            await result.copy(LOG_GROUP)
            await edit.delete()
            os.remove(file)
            return
        
        if msg.voice:
            result = await app.send_voice(target_chat_id, file, reply_to_message_id=topic_id)
            await result.copy(LOG_GROUP)
            await edit.delete()
            os.remove(file)
            return

        if msg.video_note:
            result = await app.send_video_note(target_chat_id, file, reply_to_message_id=topic_id)
            await result.copy(LOG_GROUP)
            await edit.delete()
            os.remove(file)
            return

        if msg.photo:
            result = await app.send_photo(target_chat_id, file, caption=caption, reply_to_message_id=topic_id)
            await result.copy(LOG_GROUP)
            await edit.delete()
            os.remove(file)
            return

        if file_size > 8 * 1024 * 1024 * 1024:
            await edit.edit("**❌ File size exceeds maximum limit (8GB)**")
            os.remove(file)
            return
            
        if file_size > size_limit and (free_check == 1 or pro is None):
            await edit.delete()
            await split_and_upload_file(app, sender, target_chat_id, file, caption, topic_id)
            return
        elif file_size > size_limit:
            await handle_large_file(file, sender, edit, caption)
        else:
            await upload_media(sender, target_chat_id, file, caption, edit, topic_id)

    except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
        await app.edit_message_text(sender, edit_id, "Have you joined the channel?")
    except Exception as e:
        await app.edit_message_text(sender, edit_id, f"Failed to save: `{msg_link}`\n\nError: {str(e)}")
        print(f"Error: {e}")
    finally:
        if file and os.path.exists(file):
            os.remove(file)
        if edit:
            try: await edit.delete()
            except: pass

async def clone_message(app, msg, target_chat_id, topic_id, edit_id, log_group):
    edit = await app.edit_message_text(target_chat_id, edit_id, "Cloning...")
    devgaganin = await app.send_message(target_chat_id, msg.text.markdown, reply_to_message_id=topic_id)
    await devgaganin.copy(log_group)
    await edit.delete()

async def clone_text_message(app, msg, target_chat_id, topic_id, edit_id, log_group):
    edit = await app.edit_message_text(target_chat_id, edit_id, "Cloning text message...")
    devgaganin = await app.send_message(target_chat_id, msg.text.markdown, reply_to_message_id=topic_id)
    await devgaganin.copy(log_group)
    await edit.delete()

async def handle_sticker(app, msg, target_chat_id, topic_id, edit_id, log_group):
    edit = await app.edit_message_text(target_chat_id, edit_id, "Handling sticker...")
    result = await app.send_sticker(target_chat_id, msg.sticker.file_id, reply_to_message_id=topic_id)
    await result.copy(log_group)
    await edit.delete()

async def get_media_filename(msg):
    if msg.document: return msg.document.file_name
    if msg.video: return msg.video.file_name or "temp.mp4"
    if msg.photo: return "temp.jpg"
    return "unknown_file"

def get_message_file_size(msg):
    if msg.document: return msg.document.file_size
    if msg.photo: return msg.photo.file_size
    if msg.video: return msg.video.file_size
    return 1

async def get_final_caption(msg, sender):
    original_caption = msg.caption.markdown if msg.caption else ""
    custom_caption = get_user_caption_preference(sender)
    final_caption = f"{original_caption}\n\n{custom_caption}" if custom_caption else original_caption
    replacements = load_replacement_words(sender)
    for word, replace_word in replacements.items():
        final_caption = final_caption.replace(word, replace_word)
    return final_caption or None

async def download_user_stories(userbot, chat_id, msg_id, edit, sender):
    try:
        story = await userbot.get_stories(chat_id, msg_id)
        if not story or not story.media:
            await edit.edit("No story available or no media in story.")
            return
        await edit.edit("Downloading Story...")
        file_path = await userbot.download_media(story)
        if story.media == MessageMediaType.VIDEO:
            await app.send_video(sender, file_path)
        elif story.media == MessageMediaType.DOCUMENT:
            await app.send_document(sender, file_path)
        elif story.media == MessageMediaType.PHOTO:
            await app.send_photo(sender, file_path)
        if os.path.exists(file_path): os.remove(file_path)
        await edit.edit("Story processed successfully.")
    except RPCError as e:
        await edit.edit(f"Error: {e}")
        
async def copy_message_with_chat_id(app, userbot, sender, chat_id, message_id, edit):
    target_chat_id = user_chat_ids.get(sender, sender)
    file = None
    topic_id = None
    if '/' in str(target_chat_id):
        target_chat_id, topic_id = map(int, target_chat_id.split('/', 1))

    try:
        msg = await app.get_messages(chat_id, message_id)
        custom_caption = get_user_caption_preference(sender)
        final_caption = format_caption(msg.caption or '', sender, custom_caption)

        if msg.media:
            result = await send_media_message(app, target_chat_id, msg, final_caption, topic_id)
            return
        elif msg.text:
            result = await app.copy_message(target_chat_id, chat_id, message_id, reply_to_message_id=topic_id)
            return

        if result is None:
            await edit.edit("Trying if it is a group...")
            try: await userbot.join_chat(chat_id)
            except: pass
            chat_id = (await userbot.get_chat(f"@{chat_id}")).id
            msg = await userbot.get_messages(chat_id, message_id)

            if not msg or msg.service or msg.empty: return

            if msg.text:
                await app.send_message(target_chat_id, msg.text.markdown, reply_to_message_id=topic_id)
                return

            final_caption = format_caption(msg.caption.markdown if msg.caption else "", sender, custom_caption)
            file_size = get_message_file_size(msg)
            if file_size > 4 * 1024 * 1024 * 1024:
                file = await chunked_download(userbot, msg, await get_media_filename(msg), edit, sender)
            else:
                file = await userbot.download_media(
                    msg,
                    progress=progress_bar,
                    progress_args=("╭─────────────────────╮\n│      **__Downloading__...**\n├─────────────────────", edit, time.time())
                )
            if not file: return
            file = await rename_file(file, sender)

            if msg.photo:
                result = await app.send_photo(target_chat_id, file, caption=final_caption, reply_to_message_id=topic_id)
            elif msg.video or msg.document:
                if file_size > 4 * 1024 * 1024 * 1024 and (0 == 1 or pro is None):
                    await edit.delete()
                    await split_and_upload_file(app, sender, target_chat_id, file, final_caption, topic_id)
                    return       
                elif file_size > 4 * 1024 * 1024 * 1024:
                    await handle_large_file(file, sender, edit, final_caption)
                    return
                await upload_media(sender, target_chat_id, file, final_caption, edit, topic_id)
            elif msg.audio:
                result = await app.send_audio(target_chat_id, file, caption=final_caption, reply_to_message_id=topic_id)
            elif msg.voice:
                result = await app.send_voice(target_chat_id, file, reply_to_message_id=topic_id)
            elif msg.sticker:
                result = await app.send_sticker(target_chat_id, msg.sticker.file_id, reply_to_message_id=topic_id)
            else:
                await edit.edit("Unsupported media type.")
    except Exception as e:
        print(f"Error : {e}")
    finally:
        if file and os.path.exists(file): os.remove(file)

        async def send_media_message(app, target_chat_id, msg, caption, topic_id):
    try:
        if msg.video:
            return await app.send_video(target_chat_id, msg.video.file_id, caption=caption, reply_to_message_id=topic_id)
        if msg.document:
            return await app.send_document(target_chat_id, msg.document.file_id, caption=caption, reply_to_message_id=topic_id)
        if msg.photo:
            return await app.send_photo(target_chat_id, msg.photo.file_id, caption=caption, reply_to_message_id=topic_id)
    except:
        pass
    return await app.copy_message(target_chat_id, msg.chat.id, msg.id, reply_to_message_id=topic_id)
    

def format_caption(original_caption, sender, custom_caption):
    for word in load_delete_words(sender):
        original_caption = original_caption.replace(word, '  ')
    for word, replace_word in load_replacement_words(sender).items():
        original_caption = original_caption.replace(word, replace_word)
    return f"{original_caption}\n\n__**{custom_caption}**__" if custom_caption else original_caption

# User settings
user_chat_ids = {}

def load_user_data(user_id, key, default=None):
    user_data = collection.find_one({"_id": user_id})
    return user_data.get(key, default) if user_data else default

def load_saved_channel_ids():
    return {doc["channel_id"] for doc in collection.find({"channel_id": {"$exists": True}})}

def save_user_data(user_id, key, value):
    collection.update_one({"_id": user_id}, {"$set": {key: value}}, upsert=True)

load_delete_words = lambda user_id: set(load_user_data(user_id, "delete_words", []))
save_delete_words = lambda user_id, words: save_user_data(user_id, "delete_words", list(words))
load_replacement_words = lambda user_id: load_user_data(user_id, "replacement_words", {})
save_replacement_words = lambda user_id, replacements: save_user_data(user_id, "replacement_words", replacements)

user_rename_preferences = {}
user_caption_preferences = {}

async def set_rename_command(user_id, custom_rename_tag):
    user_rename_preferences[str(user_id)] = custom_rename_tag

get_user_rename_preference = lambda user_id: user_rename_preferences.get(str(user_id), 'Team SPY')

async def set_caption_command(user_id, custom_caption):
    user_caption_preferences[str(user_id)] = custom_caption

get_user_caption_preference = lambda user_id: user_caption_preferences.get(str(user_id), '')

sessions = {}
SET_PIC = "settings.jpg"
MESS = "Customize your settings ..."

@gf.on(events.NewMessage(incoming=True, pattern='/settings'))
async def settings_command(event):
    user_id = event.sender_id
    buttons = [
        [Button.inline("Set Chat ID", b'setchat'), Button.inline("Set Rename Tag", b'setrename')],
        [Button.inline("Caption", b'setcaption'), Button.inline("Replace Words", b'setreplacement')],
        [Button.inline("Remove Words", b'delete'), Button.inline("Reset", b'reset')],
        [Button.inline("Session Login", b'addsession'), Button.inline("Logout", b'logout')],
        [Button.inline("Set Thumbnail", b'setthumb'), Button.inline("Remove Thumbnail", b'remthumb')],
        [Button.inline("Upload Method", b'uploadmethod')],
        [Button.url("Report Errors", "https://t.me/arsh_beniwal")]
    ]
    await gf.send_file(event.chat_id, file=SET_PIC, caption=MESS, buttons=buttons)

pending_photos = {}

@gf.on(events.CallbackQuery)
async def callback_query_handler(event):
    user_id = event.sender_id
    data = event.data
    
    if data == b'setchat':
        await event.respond("Send me the ID of that chat:")
        sessions[user_id] = 'setchat'

    elif data == b'setrename':
        await event.respond("Send me the rename tag:")
        sessions[user_id] = 'setrename'
    
    elif data == b'setcaption':
        await event.respond("Send me the caption:")
        sessions[user_id] = 'setcaption'

    elif data == b'setreplacement':
        await event.respond("Send me the replacement words in the format: 'WORD(s)' 'REPLACEWORD'")
        sessions[user_id] = 'setreplacement'

    elif data == b'addsession':
        await event.respond("Send Pyrogram V2 session")
        sessions[user_id] = 'addsession'

    elif data == b'delete':
        await event.respond("Send words separated by space to delete them from caption/filename ...")
        sessions[user_id] = 'deleteword'
        
    elif data == b'logout':
        await odb.remove_session(user_id)
        user_data = await odb.get_data(user_id)
        await event.respond("Logged out successfully." if user_data and user_data.get("session") is None else "You are not logged in.")

elif data == b'setthumb':
        pending_photos[user_id] = True
        await event.respond('Please send the photo for thumbnail.')
    
    elif data == b'uploadmethod':
        user_data = collection.find_one({'user_id': user_id})
        current_method = user_data.get('upload_method', 'Pyrogram') if user_data else 'Pyrogram'
        buttons = [
            [Button.inline(f"Pyrogram v2 {'✅' if current_method=='Pyrogram' else ''}", b'pyrogram')],
            [Button.inline(f"SpyLib v1 ⚡{'✅' if current_method=='Telethon' else ''}", b'telethon')]
        ]
        await event.edit("Choose your preferred upload method:\n\n__Note: SpyLib ⚡ (Telethon) is in beta.__", buttons=buttons)

    elif data == b'pyrogram':
        save_user_upload_method(user_id, "Pyrogram")
        await event.edit("Upload method set to **Pyrogram** ✅")

    elif data == b'telethon':
        save_user_upload_method(user_id, "Telethon")
        await event.edit("Upload method set to **SpyLib ⚡** ✅")        

elif data == b'reset':
        try:
            user_id_str = str(user_id)
            collection.update_one({"_id": user_id}, {"$unset": {
                "delete_words": "", "replacement_words": "", "watermark_text": "", "duration_limit": ""}})
            user_chat_ids.pop(user_id, None)
            user_rename_preferences.pop(user_id_str, None)
            user_caption_preferences.pop(user_id_str, None)
            thumb_path = f"{user_id}.jpg"
            if os.path.exists(thumb_path): os.remove(thumb_path)
            await event.respond("✅ Reset successfully")
        except Exception as e:
            await event.respond(f"Error: {e}")
    
    elif data == b'remthumb':
        try:
            os.remove(f'{user_id}.jpg')
            await event.respond('Thumbnail removed!')
        except FileNotFoundError:
            await event.respond("No thumbnail found.")

@gf.on(events.NewMessage(func=lambda e: e.sender_id in pending_photos))
async def save_thumbnail(event):
    user_id = event.sender_id
    if event.photo:
        temp_path = await event.download_media()
        if os.path.exists(f'{user_id}.jpg'): os.remove(f'{user_id}.jpg')
        os.rename(temp_path, f'./{user_id}.jpg')
        await event.respond('Thumbnail saved!')
    else:
        await event.respond('Please send a photo...')
    pending_photos.pop(user_id, None)

def save_user_upload_method(user_id, method):
    collection.update_one({'user_id': user_id}, {'$set': {'upload_method': method}}, upsert=True)

@gf.on(events.NewMessage)
async def handle_user_input(event):
    user_id = event.sender_id
    if user_id not in sessions: return
    session_type = sessions[user_id]
    text = event.text

    if session_type == 'setchat':
        try:
            user_chat_ids[user_id] = text
            await event.respond("Chat ID set successfully!")
        except: await event.respond("Invalid chat ID!")
                
    elif session_type == 'setrename':
        await set_rename_command(user_id, text)
        await event.respond(f"Custom rename tag set to: {text}")

elif session_type == 'setcaption':
        await set_caption_command(user_id, text)
        await event.respond(f"Custom caption set to: {text}")

    elif session_type == 'setreplacement':
        match = re.match(r"'(.+)' '(.+)'", text)
        if not match:
            await event.respond("Usage: 'WORD(s)' 'REPLACEWORD'")
        else:
            word, replace_word = match.groups()
            if word in load_delete_words(user_id):
                await event.respond(f"The word '{word}' is in delete list and cannot be replaced.")
            else:
                replacements = load_replacement_words(user_id)
                replacements[word] = replace_word
                save_replacement_words(user_id, replacements)
                await event.respond(f"Replacement saved: '{word}' → '{replace_word}'")

    elif session_type == 'addsession':
        await odb.set_session(user_id, text)
        await event.respond("✅ Session string added!")

    elif session_type == 'deleteword':
        words = text.split()
        delete_words = load_delete_words(user_id)
        delete_words.update(words)
        save_delete_words(user_id, delete_words)
        await event.respond(f"Words added to delete list: {', '.join(words)}")
            
    del sessions[user_id]
    
@gf.on(events.NewMessage(incoming=True, pattern='/lock'))
async def lock_command_handler(event):
    if event.sender_id not in OWNER_ID:
        return await event.respond("Not authorized.")
    try:
        channel_id = int(event.text.split(' ')[1])
        collection.insert_one({"channel_id": channel_id})
        await event.respond(f"Channel ID {channel_id} locked.")
    except:
        await event.respond("Invalid /lock command. Use /lock CHANNEL_ID.")

async def handle_large_file(file, sender, edit, caption):
    if not pro:
        await edit.edit('**__ ❌ 4GB uploader not found__**')
        os.remove(file)
        return

try:
        await edit.edit('**__ ✅ 4GB uploader connected...__**\n\n')
        file_extension = str(file).split('.')[-1].lower()
        metadata = video_metadata(file)
        thumb_path = await screenshot(file, metadata['duration'], sender) if 'duration' in metadata else None
        
        if file_extension in VIDEO_EXTENSIONS:
            dm = await pro.send_video(
                LOG_GROUP,
                video=file,
                caption=caption,
                thumb=thumb_path,
                height=metadata.get('height', 0),
                width=metadata.get('width', 0),
                duration=metadata.get('duration', 0),
                progress=progress_bar,
                progress_args=("╭─────────────────────╮\n│       **__4GB Uploader__ ⚡**\n├─────────────────────", edit, time.time())
            )
        else:
            dm = await pro.send_document(
                LOG_GROUP,
                document=file,
                caption=caption,
                thumb=thumb_path,
                progress=progress_bar,
                progress_args=("╭─────────────────────╮\n│      **__4GB Uploader ⚡__**\n├─────────────────────", edit, time.time())
)

await app.copy_message(user_chat_ids.get(sender, sender), dm.chat.id, dm.id)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await edit.delete()
        os.remove(file)

async def rename_file(file, sender):
    delete_words = load_delete_words(sender)
    custom_rename_tag = get_user_rename_preference(sender)
    replacements = load_replacement_words(sender)
    
    base, ext = os.path.splitext(file)
    ext = ext.lstrip('.').lower()
    if not ext.isalpha() or len(ext) > 9 or ext in VIDEO_EXTENSIONS:
        ext = 'mp4'
    
    base_name = os.path.basename(base)
    for word in delete_words:
        base_name = base_name.replace(word, "")
    for word, replace_word in replacements.items():
        base_name = base_name.replace(word, replace_word)

    new_file_name = f"{base_name} {custom_rename_tag}.{ext}"
    os.rename(file, new_file_name)
    return new_file_name

user_progress = {}

def progress_callback(done, total, user_id):
    if user_id not in user_progress:
        user_progress[user_id] = {'previous_done': 0, 'previous_time': time.time()}
    
    user_data = user_progress[user_id]
    percent = (done / total) * 100
    completed_blocks = int(percent // 10)
    progress_bar = "♦" * completed_blocks + "◇" * (10 - completed_blocks)
    
    done_mb = done / (1024 * 1024)
    total_mb = total / (1024 * 1024)
    speed = done - user_data['previous_done']
    elapsed_time = time.time() - user_data['previous_time']
    speed_mbps = (speed / elapsed_time * 8) / (1024 * 1024) if elapsed_time > 0 else 0
    remaining_time = (total - done) / (speed / elapsed_time) if elapsed_time > 0 and speed > 0 else 0
    
    final = (
        f"╭──────────────────╮\n│     **__SpyLib ⚡ Uploader__**\n├──────────\n"
        f"│ {progress_bar}\n\n│ **__Progress:__** {percent:.2f}%\n"
        f"│ **__Done:__** {done_mb:.2f} MB / {total_mb:.2f} MB\n"
        f"│ **__Speed:__** {speed_mbps:.2f} Mbps\n"
        f"│ **__ETA:__** {remaining_time/60:.2f} min\n╰──────────────────╯\n\n"
        f"**__Powered by Team JB__**"
    )

user_data['previous_done'] = done
    user_data['previous_time'] = time.time()
    return final

async def split_and_upload_file(app, sender, target_chat_id, file_path, caption, topic_id):
    if not os.path.exists(file_path): return
    file_size = os.path.getsize(file_path)
    start = await app.send_message(sender, f"ℹ️ File size: {file_size / (1024 * 1024):.2f} MB")
    PART_SIZE = 1.9 * 1024 * 1024 * 1024
    part_number = 0
    
    async with aiofiles.open(file_path, "rb") as f:
        while chunk := await f.read(PART_SIZE):
            part_file = f"{os.path.splitext(file_path)[0]}.part{str(part_number).zfill(3)}.mp4"
            async with aiofiles.open(part_file, "wb") as part_f:
                await part_f.write(chunk)
                
            edit = await app.send_message(sender, f"⬆️ Uploading part {part_number + 1}...")
            await app.send_document(
                target_chat_id,
                document=part_file,
                caption=f"{caption} \n\n**Part : {part_number + 1}**",
                reply_to_message_id=topic_id,
                progress=progress_bar,
                progress_args=("╭─────────────────────╮\n│      **__Pyro Uploader__**\n├─────────────────────", edit, time.time())
            )
            await edit.delete()
            os.remove(part_file)
            part_number += 1

    await start.delete()
    os.remove(file_path)
