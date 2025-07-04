# ---------------------------------------------------
# File Name: gcast.py
# Description: Broadcast & forward messages to users
# Author: Gagan (Updated by ChatGPT)
# ---------------------------------------------------

import asyncio
import time
import traceback
from pyrogram import filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from config import OWNER_ID
from devgagan import app
from devgagan.core.mongo.users_db import get_users


# Send copied message and try pinning
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


# Utility to split list into chunks
def batched(iterable, size=20):
    it = iter(iterable)
    while True:
        batch = list()
        try:
            for _ in range(size):
                batch.append(next(it))
        except StopIteration:
            if batch:
                yield batch
            break
        yield batch


# /gcast command (copy broadcast)
@app.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast(_, message):
    if not message.reply_to_message:
        return await message.reply("❌ Please reply to a message you want to broadcast.")

    to_send = message.reply_to_message
    exmsg = await message.reply("📤 Starting broadcast...")
    all_users = list(set(await get_users() or []))  # remove duplicates
    done = 0
    failed = 0
    start = time.time()

    for batch in batched(all_users, 20):
        for user in batch:
            try:
                _, err = await send_msg(int(user), to_send)
                done += 1
            except Exception:
                failed += 1
        await asyncio.sleep(1)

    end = round(time.time() - start, 2)
    await exmsg.edit(
        f"✅ **Broadcast Completed**\n\n"
        f"👥 Total Users: `{len(all_users)}`\n"
        f"📤 Delivered: `{done}`\n"
        f"❌ Failed: `{failed}`\n"
        f"⏱ Duration: `{end}s`"
    )


# /acast command (forward broadcast or text)
@app.on_message(filters.command("acast") & filters.user(OWNER_ID))
async def announced(_, message):
    users = list(set(await get_users() or []))  # remove duplicates
    done = 0
    failed = 0
    start = time.time()

    if message.reply_to_message:
        msg_id = message.reply_to_message.id
        chat_id = message.chat.id
        exmsg = await message.reply("📣 Starting forward broadcast...")

        for batch in batched(users, 20):
            for user in batch:
                try:
                    await app.forward_messages(
                        chat_id=int(user),
                        from_chat_id=chat_id,
                        message_ids=msg_id
                    )
                    done += 1
                except Exception:
                    failed += 1
            await asyncio.sleep(1)

    elif len(message.command) > 1:
        text = " ".join(message.command[1:])
        exmsg = await message.reply("📤 Starting text broadcast...")

        for batch in batched(users, 20):
            for user in batch:
                try:
                    await app.send_message(chat_id=int(user), text=text)
                    done += 1
                except Exception:
                    failed += 1
            await asyncio.sleep(1)

    else:
        return await message.reply("❌ Reply to a message or give text after `/acast`.")

    end = round(time.time() - start, 2)
    await exmsg.edit(
        f"✅ **Broadcast Completed**\n\n"
        f"👥 Total Users: `{len(users)}`\n"
        f"📤 Delivered: `{done}`\n"
        f"❌ Failed: `{failed}`\n"
        f"⏱ Duration: `{end}s`"
                )
