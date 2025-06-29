# ---------------------------------------------------
# File Name: gcast.py
# Description: Broadcast & forward messages to users
# Author: Gagan (Updated by ChatGPT)
# ---------------------------------------------------

import asyncio
import time
import traceback
from pyrogram import filters
from pyrogram.errors import (
    FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
)
from config import OWNER_ID
from devgagan import app
from devgagan.core.mongo.users_db import get_users


# Send message (copied) and try to pin it
async def send_msg(user_id, message):
    try:
        sent_msg = await message.copy(chat_id=user_id)
        try:
            await sent_msg.pin()
        except Exception:
            try:
                await sent_msg.pin(both_sides=True)
            except Exception:
                pass
        return 200, None
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : invalid user ID\n"
    except Exception:
        return 500, f"{user_id} : {traceback.format_exc()}\n"


# Utility to split list into batches
def batched(iterable, size=20):
    it = iter(iterable)
    while batch := list([*it][:size]):
        yield batch


# /gcast command (copy broadcast)
@app.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast(_, message):
    # Determine content to send
    to_send = message.reply_to_message or (
        message.text.split(None, 1)[1] if len(message.text.split()) > 1 else None
    )

    if not to_send:
        return await message.reply_text("❌ Reply to a message or add text after `/gcast`.")

    # Prepare users
    exmsg = await message.reply_text("📤 Starting broadcast...")
    all_users = list(set(await get_users() or []))  # remove duplicates
    done_users = 0
    failed_users = 0
    start_time = time.time()

    # Broadcast in batches
    for batch in batched(all_users, 20):
        for user in batch:
            try:
                if isinstance(to_send, str):
                    await app.send_message(chat_id=int(user), text=to_send)
                else:
                    _, err = await send_msg(int(user), to_send)
                done_users += 1
            except Exception:
                failed_users += 1
        await asyncio.sleep(1)  # throttle to prevent FloodWaits

    # Final report
    elapsed = round(time.time() - start_time, 2)
    await exmsg.edit_text(
        f"✅ **Broadcast Completed**\n\n"
        f"👥 Total Users: `{len(all_users)}`\n"
        f"📤 Delivered: `{done_users}`\n"
        f"❌ Failed: `{failed_users}`\n"
        f"⏱ Duration: `{elapsed}s`"
    )


# /acast command (forward or text broadcast)
@app.on_message(filters.command("acast") & filters.user(OWNER_ID))
async def announced(_, message):
    users = list(set(await get_users() or []))  # remove duplicates
    done_users = 0
    failed_users = 0
    start_time = time.time()

    # Forward reply
    if message.reply_to_message:
        msg_id = message.reply_to_message.id
        chat_id = message.chat.id
        exmsg = await message.reply_text("📣 Starting forward broadcast...")

        for batch in batched(users, 20):
            for user in batch:
                try:
                    await app.forward_messages(
                        chat_id=int(user),
                        from_chat_id=chat_id,
                        message_ids=msg_id
                    )
                    done_users += 1
                except Exception:
                    failed_users += 1
            await asyncio.sleep(1)

    # Send as plain text
    elif len(message.text.split()) > 1:
        broadcast_text = message.text.split(None, 1)[1]
        exmsg = await message.reply_text("📤 Starting text broadcast...")

        for batch in batched(users, 20):
            for user in batch:
                try:
                    await app.send_message(chat_id=int(user), text=broadcast_text)
                    done_users += 1
                except Exception:
                    failed_users += 1
            await asyncio.sleep(1)

    else:
        return await message.reply_text("❌ Reply to a message or add text after `/acast`.")

    # Final report
    elapsed = round(time.time() - start_time, 2)
    await exmsg.edit_text(
        f"✅ **Broadcast Completed**\n\n"
        f"👥 Total Users: `{len(users)}`\n"
        f"📤 Delivered: `{done_users}`\n"
        f"❌ Failed: `{failed_users}`\n"
        f"⏱ Duration: `{elapsed}s`"
    )
