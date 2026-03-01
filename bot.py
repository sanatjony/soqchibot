import asyncio
import os
import time

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart

from pyrogram import Client
from pyrogram.raw.functions.channels import EditBanned
from pyrogram.raw.types import ChatBannedRights

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

# ================= AUTO DELETE =================

async def delete_command(message, delay=1):
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

# ================= START =================

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.reply("Hybrid Guard ishga tushdi ✅")

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
    reason = " ".join(args[2:]) if len(args) > 2 else "sababsiz"

    multiplier = {"m": 60, "h": 3600, "d": 86400}

    try:
        unit = time_str[-1]
        value = int(time_str[:-1])
        seconds = value * multiplier.get(unit, 0)
    except:
        return

    until_date = int(time.time()) + seconds
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        await app.get_chat(chat_id)
        await app.get_chat_member(chat_id, user_id)
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
                    embed_links=True,
                    change_info=True,
                    invite_users=True,
                    pin_messages=True,
                    view_messages=False
                )
            )
        )

        await message.reply(
            f"🔇 {message.reply_to_message.from_user.mention_html()} {time_str} ga mute qilindi\n📌 Sabab: {reason}",
            parse_mode="HTML"
        )

    except Exception as e:
        print("Mute error:", e)

    asyncio.create_task(delete_command(message))

# ================= UNMUTE =================

@dp.message(lambda m: m.text and m.text.startswith(".unmute"))
async def unmute_user(message: types.Message):

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    chat_id = message.chat.id
    user_id = None

    # 1️⃣ Reply orqali
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id

    # 2️⃣ Username orqali
    elif len(message.text.split()) > 1:
        username = message.text.split()[1].replace("@", "")
        try:
            user = await app.get_users(username)
            user_id = user.id
        except:
            await message.reply("❌ User topilmadi")
            return

    if not user_id:
        await message.reply("❌ Reply yoki @username bilan yozing")
        return

    await ensure_peer(chat_id, user_id)

    try:
        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(chat_id),
                participant=await app.resolve_peer(user_id),
                banned_rights=ChatBannedRights(
                    send_messages=False,
                    send_media=False,
                    send_stickers=False,
                    send_gifs=False,
                    send_games=False,
                    send_inline=False,
                    send_polls=False,
                    embed_links=False
                )
            )
        )

        await message.reply("🔊 UNMUTE qilindi")

    except Exception as e:
        print("Unmute error:", e)
        await message.reply("❌ UNMUTE xato berdi")

    asyncio.create_task(delete_cmd(message))

# ================= BAN =================

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
                banned_rights=ChatBannedRights(view_messages=True)
            )
        )

        await message.reply("🚫 BAN berildi")

    except Exception as e:
        print("Ban error:", e)

    asyncio.create_task(delete_command(message))

# ================= UNBAN =================

@dp.message(lambda m: m.text == ".unban")
async def unban_user(message: types.Message):

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
                banned_rights=ChatBannedRights()
            )
        )

        await message.reply("♻️ UNBAN qilindi")

    except Exception as e:
        print("Unban error:", e)

    asyncio.create_task(delete_command(message))

# ================= MAIN =================

# ================= MAIN =================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await app.start()
    
    # 🔥 Pyrogramga barcha chatlarni tanitadi
    async for _ in app.get_dialogs():
        pass

    print("Hybrid bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())





