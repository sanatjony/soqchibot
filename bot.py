import re
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.enums import ChatMemberStatus
from pyrogram import Client
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_strikes = {}

app = Client(
    "hybrid",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

LINK_PATTERN = re.compile(
    r"(https?:\/\/|t\.me\/|telegram\.me\/|@\w+)",
    re.IGNORECASE
)

async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in [
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR
    ]

def is_link(text):
    return bool(LINK_PATTERN.search(text))

# ================= ANTI LINK =================

@dp.message()
async def anti_link(message: types.Message):

    if not message.text:
        return

    if await is_admin(message.chat.id, message.from_user.id):
        return

    if not is_link(message.text):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        await message.delete()
    except:
        pass

    strikes = user_strikes.get(user_id, 0) + 1
    user_strikes[user_id] = strikes

    if strikes >= 3:
        try:
            await app.ban_chat_member(chat_id, user_id)
        except Exception as e:
            print("Hybrid ban error:", e)

        user_strikes[user_id] = 0

# ================= MUTE =================

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

    try:
        await app.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=False
            ),
            until_date=until_date
        )
    except Exception as e:
        print("Hybrid mute error:", e)

# ================= BAN =================

@dp.message(lambda m: m.text == ".ban")
async def ban_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    user_id = message.reply_to_message.from_user.id

    try:
        await app.ban_chat_member(message.chat.id, user_id)
    except Exception as e:
        print("Hybrid ban error:", e)

# ================= START =================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await app.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
