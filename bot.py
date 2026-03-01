import asyncio
import os
import time

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart

from pyrogram import Client
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

app = Client(
    "hybrid",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

# ================= START =================

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.reply(
        "Salom 👋\n\n"
        "Men guruhni himoya qiluvchi botman.\n"
        "Guruhga ssilka tashlash taqiqlangan 🚫"
    )

# ================= ADMIN CHECK =================

async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in [
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR
    ]

# ================= TIME PARSER =================

def parse_time(time_str):
    multiplier = {"m": 60, "h": 3600, "d": 86400}
    try:
        unit = time_str[-1]
        value = int(time_str[:-1])
        return value * multiplier.get(unit, 600)
    except:
        return 600

# ================= HARD MUTE =================

@dp.message(lambda m: m.text and m.text.startswith(".mute"))
async def mute_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    args = message.text.split()

    # default values
    mute_time = "10m"
    reason = "Sabab ko‘rsatilmagan"

    if len(args) >= 2:
        mute_time = args[1]

    if len(args) >= 3:
        reason = " ".join(args[2:])

    seconds = parse_time(mute_time)
    until_date = int(time.time()) + seconds

    user = message.reply_to_message.from_user
    user_id = user.id
    chat_id = message.chat.id

    try:
        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(chat_id),
                participant=await app.resolve_peer(user_id),
                banned_rights=ChatBannedRights(
                    until_date=until_date,
                    send_messages=True,
                    send_media=True,
                    send_stickers=True,
                    send_gifs=True,
                    send_games=True,
                    send_inline=True,
                    send_polls=True,
                    embed_links=True
                )
            )
        )

        await message.reply(
            f"🔇 {user.first_name} {mute_time} ga mute qilindi\n"
            f"📌 Sabab: {reason}"
        )

    except Exception as e:
        print("Mute error:", e)

# ================= UNMUTE =================

@dp.message(lambda m: m.text == ".unmute")
async def unmute_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    user = message.reply_to_message.from_user

    try:
        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(message.chat.id),
                participant=await app.resolve_peer(user.id),
                banned_rights=ChatBannedRights()
            )
        )

        await message.reply(f"🔊 {user.first_name} unmute qilindi")

    except Exception as e:
        print("Unmute error:", e)

# ================= BAN =================

@dp.message(lambda m: m.text and m.text.startswith(".ban"))
async def ban_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    args = message.text.split()
    reason = "Sabab ko‘rsatilmagan"

    if len(args) >= 2:
        reason = " ".join(args[1:])

    user = message.reply_to_message.from_user

    try:
        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(message.chat.id),
                participant=await app.resolve_peer(user.id),
                banned_rights=ChatBannedRights(view_messages=True)
            )
        )

        await message.reply(
            f"🚫 {user.first_name} ban qilindi\n"
            f"📌 Sabab: {reason}"
        )

    except Exception as e:
        print("Ban error:", e)

# ================= UNBAN =================

@dp.message(lambda m: m.text == ".unban")
async def unban_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    user = message.reply_to_message.from_user

    try:
        await app.unban_chat_member(message.chat.id, user.id)
        await message.reply(f"✅ {user.first_name} unban qilindi")

    except Exception as e:
        print("Unban error:", e)

# ================= START SYSTEM =================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await app.start()
    print("Hybrid bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
