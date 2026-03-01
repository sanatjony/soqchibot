import re
import asyncio
import os
import time

from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart

from pyrogram import Client
from pyrogram.errors import UserAdminInvalid
from pyrogram.raw.functions.channels import EditBanned
from pyrogram.raw.types import ChatBannedRights

from datetime import datetime, timedelta

# ================= TOKENS =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= PYROGRAM =================
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_string = os.getenv("SESSION")

app = Client(
    "hybrid",
    api_id=api_id,
    api_hash=api_hash,
    session_string=session_string
)
app = Client(
    "hybrid",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

user_strikes = {}

# ================= START =================

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.reply(
        "Salom 👋\n\n"
        "Men guruhni himoya qiluvchi botman.\n"
        "Guruhga ssilka tashlash taqiqlangan 🚫"
    )

# ================= AUTO DELETE =================

async def auto_delete(message, delay=600):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# ================= ADMIN CHECK =================

async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in [
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR
    ]

# ================= NEW MEMBER =================

@dp.message(lambda m: m.new_chat_members)
async def new_member(message: types.Message):

    try:
        await message.delete()
    except:
        pass

    for user in message.new_chat_members:

        msg = await message.answer(
            f"👋 {user.mention_html()} guruhga xush kelibsiz!",
            parse_mode="HTML"
        )

        asyncio.create_task(auto_delete(msg))

# ================= MUTE (HYBRID) =================

@dp.message(lambda m: m.text and m.text.startswith(".mute"))
async def mute_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    args = message.text.split()
    if len(args) < 2:
        return

    time_str = args[1]

    multiplier = {"m": 60, "h": 3600, "d": 86400}
    unit = time_str[-1]
    value = int(time_str[:-1])
    seconds = value * multiplier.get(unit, 0)

    until_date = datetime.now() + timedelta(seconds=seconds)
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        await app.restrict_chat_member(
            chat_id,
            user_id,
            permissions={
                "can_send_messages": False,
                "can_send_media_messages": False,
                "can_send_other_messages": False,
                "can_add_web_page_previews": False
            },
            until_date=until_date
        )
    except Exception as e:
        print("Pyrogram mute error:", e)
        return

    await message.reply("🔇 HARD MUTE berildi")
    asyncio.create_task(auto_delete(message))
# ================= UNMUTE =================
@dp.message(lambda m: m.text == ".unmute")
async def unmute_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        await app.restrict_chat_member(
            chat_id,
            user_id,
            permissions={
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True
            }
        )
    except Exception as e:
        print("Pyrogram unmute error:", e)
        return

    await message.reply("🔊 UNMUTE qilindi")
    asyncio.create_task(auto_delete(message))
# ================= BAN (HYBRID) =================

@dp.message(lambda m: m.text == ".ban")
async def ban_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(chat_id),
                participant=await app.resolve_peer(user_id),
                banned_rights=ChatBannedRights(
                    view_messages=True
                )
            )
        )
    except Exception as e:
        print("Ban error:", e)
        return

    asyncio.create_task(auto_delete(message))

# ================= START SYSTEM =================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await app.start()
    print("Hybrid bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

