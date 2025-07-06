# __init__.py

import asyncio
import logging
import time

from pyrogram import Client
from pyrogram.enums import ParseMode
from telethon.sync import TelegramClient
from motor.motor_asyncio import AsyncIOMotorClient

from config import (
    API_ID, API_HASH, BOT_TOKEN,
    STRING, DEFAULT_SESSION,
    MONGO_DB
)

# 🟢 Logging setup
logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

# 🕒 Bot start time tracker
botStartTime = time.time()

# 🟢 Pyrogram bot client
app = Client(
    "pyrobot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,
    parse_mode=ParseMode.MARKDOWN
)

# 🟢 Pyrogram userbot from session string
pro = Client("ggbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING) if STRING else None

# 🟢 Optional second userbot (default session)
userrbot = Client("userrbot", api_id=API_ID, api_hash=API_HASH, session_string=DEFAULT_SESSION) if DEFAULT_SESSION else None

# 🟢 Telethon client
telethon_client = TelegramClient("telethon_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🟢 MongoDB client
mongo_client = AsyncIOMotorClient(MONGO_DB)
tdb = mongo_client["telegram_bot"]
token_collection = tdb["tokens"]

# 🟢 Create TTL index in MongoDB
async def create_ttl_index():
    await token_collection.create_index("expires_at", expireAfterSeconds=0)

# 🟢 Initialize all clients
async def start_all_clients():
    await create_ttl_index()
    logging.info("MongoDB TTL index ensured.")

    await app.start()
    me = await app.get_me()
    global BOT_ID, BOT_USERNAME, BOT_NAME
    BOT_ID = me.id
    BOT_USERNAME = me.username
    BOT_NAME = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name
    logging.info(f"Bot Started as @{BOT_USERNAME}")

    if pro:
        try:
            await pro.start()
            logging.info("Userbot (STRING) started.")
        except Exception as e:
            logging.warning(f"Userbot (STRING) failed to start: {e}")

    if userrbot:
        try:
            await userrbot.start()
            logging.info("Userbot (DEFAULT_SESSION) started.")
        except Exception as e:
            logging.warning(f"Userbot (DEFAULT_SESSION) failed to start: {e}")

# 🟢 Start event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(start_all_clients())
