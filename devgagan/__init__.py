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

# ✅ Logging Setup
logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

# ⏱️ Bot Start Time
botStartTime = time.time()

# ✅ Pyrogram Bot Client
app = Client(
    "pyrobot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,
    parse_mode=ParseMode.MARKDOWN
)

# ✅ Pyrogram Userbot (Session String)
pro = Client(
    "ggbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING
) if STRING else None

# ✅ Pyrogram Optional Userbot (Default Session)
userrbot = Client(
    "userrbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=DEFAULT_SESSION
) if DEFAULT_SESSION else None

# ✅ Telethon Client
telethon_client = TelegramClient(
    "telethon_session",
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

# ✅ MongoDB Setup
mongo_client = AsyncIOMotorClient(MONGO_DB)
tdb = mongo_client["telegram_bot"]
token_collection = tdb["tokens"]

# ✅ TTL Index Setup for MongoDB
async def create_ttl_index():
    try:
        await token_collection.create_index("expires_at", expireAfterSeconds=0)
        logging.info("MongoDB TTL index ensured.")
    except Exception as e:
        logging.error(f"Failed to create TTL index: {e}")

# ✅ Start All Clients
async def start_all_clients():
    await create_ttl_index()

    # Start Bot Client
    await app.start()
    me = await app.get_me()
    global BOT_ID, BOT_USERNAME, BOT_NAME
    BOT_ID = me.id
    BOT_USERNAME = me.username
    BOT_NAME = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name
    logging.info(f"Bot started as @{BOT_USERNAME}")

    # Start STRING userbot
    if pro:
        try:
            await pro.start()
            logging.info("Userbot (STRING) started.")
        except Exception as e:
            logging.warning(f"Failed to start userbot (STRING): {e}")

    # Start DEFAULT_SESSION userbot
    if userrbot:
        try:
            await userrbot.start()
            logging.info("Userbot (DEFAULT_SESSION) started.")
        except Exception as e:
            logging.warning(f"Failed to start userbot (DEFAULT_SESSION): {e}")

# ✅ Run Event Loop
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_all_clients())
