# ---------------------------------------------------
# File Name: __main__.py
# Description: Main entry point for the Telegram bot
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.5
# License: MIT License
# ---------------------------------------------------

import asyncio
import importlib
import gc
from pyrogram import idle
from aiojobs import create_scheduler

from devgagan.modules import ALL_MODULES
from devgagan.core.mongo.plans_db import check_and_remove_expired_users

# 🔁 Auto import module loader
async def load_all_modules():
    for all_module in ALL_MODULES:
        importlib.import_module("devgagan.modules." + all_module)

# 🔁 Background job for expired premium removals
async def schedule_expiry_check():
    scheduler = await create_scheduler()
    while True:
        await scheduler.spawn(check_and_remove_expired_users())
        await asyncio.sleep(3600)  # Run every hour
        gc.collect()

# 🔁 Full Bot Boot (including session clients and idle mode)
async def devggn_boot():
    # FIXED: Import from devgagan package instead of __init__
    from devgagan import start_all_clients

    # Start all bot & user clients
    await start_all_clients()

    # Load all features/modules
    await load_all_modules()

    print("""
---------------------------------------------------
📂 Bot Deployed successfully ...
📝 Description: A Pyrogram bot for downloading files from Telegram channels or groups 
                and uploading them back to Telegram.
👨‍💻 Author: Gagan
🌐 GitHub: https://github.com/devgaganin/
📬 Telegram: https://t.me/arsh_beniwal
▶️ YouTube: https://youtube.com/@dev_gagan
🗓️ Created: 2025-01-11
🔄 Last Modified: 2025-01-11
🛠️ Version: 2.0.5
📜 License: MIT License
---------------------------------------------------
""")

    asyncio.create_task(schedule_expiry_check())
    print("🛡️ Auto premium expiry cleanup started...")
    await idle()
    print("⛔ Bot stopped.")

# Start the main loop using modern asyncio API
if __name__ == "__main__":
    # FIXED: Use modern asyncio.run() instead of deprecated loop methods
    asyncio.run(devggn_boot())
