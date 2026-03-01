import asyncio
import os
import time

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart

from pyrogram import Client
from pyrogram.raw.functions.channels import EditBanned
from pyrogram.raw.types import ChatBannedRights

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

# ================= ADMIN CHECK (ANONYMOUS SUPPORT) =================

async def is_admin(message: types.Message):

    chat_id = message.chat.id

    # Oddiy admin
    if message.from_user:
        member = await bot.get_chat_member(chat_id, message.from_user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            return True

    # Anonymous admin
    if message.sender_chat:
        if message.sender_chat.id == chat_id:
            return True

    return False

# ================= PEER INIT =================

async def ensure_peer(chat_id, user_id):
    try:
        await app.get_chat(chat_id)
        await app.get_chat_member(chat_id, user_id)
    except:
        pass

# ================= START =================

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.reply("Hybrid Guard ishga tushdi ✅")

# ================= TARGET UNIVERSAL =================

async def get_target(message: types.Message):

    args = message.text.split()

    # Reply orqali
    if message.reply_to_message:
        if message.reply_to_message.from_user:
            return message.reply_to_message.from_user.id, message.reply_to_message.from_user.mention_html()
        elif message.reply_to_message.sender_chat:
            return message.reply_to_message.sender_chat.id, message.reply_to_message.sender_chat.title

    # Username orqali
    if len(args) >= 2:
        try:
            user = await bot.get_chat(args[1])
            mention = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
            return user.id, mention
        except:
            return None, None

    return None, None

# ================= MUTE =================

@dp.message(lambda m: m.text and m.text.startswith(".mute"))
async def mute_user(message: types.Message):

    if not await is_admin(message):
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

    target, mention = await get_target(message)
    if not target:
        return

    until_date = int(time.time()) + seconds
    chat_id = message.chat.id

    try:
        await ensure_peer(chat_id, target)

        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(chat_id),
                participant=await app.resolve_peer(target),
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
            f"🔇 {mention} {time_str} ga mute qilindi\n📌 Sabab: {reason}",
            parse_mode="HTML"
        )

    except Exception as e:
        print("Mute error:", e)

    asyncio.create_task(delete_command(message))

# ================= UNMUTE =================

@dp.message(lambda m: m.text and m.text.startswith(".unmute"))
async def unmute_user(message: types.Message):

    if not await is_admin(message):
        return

    target, mention = await get_target(message)
    if not target:
        return

    chat_id = message.chat.id

    try:
        await ensure_peer(chat_id, target)

        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(chat_id),
                participant=await app.resolve_peer(target),
                banned_rights=ChatBannedRights()
            )
        )

        await message.reply(
            f"🔊 {mention} UNMUTE qilindi",
            parse_mode="HTML"
        )

    except Exception as e:
        print("Unmute error:", e)

    asyncio.create_task(delete_command(message))

# ================= BAN =================

@dp.message(lambda m: m.text.startswith(".ban"))
async def ban_user(message: types.Message):

    if not await is_admin(message):
        return

    target, mention = await get_target(message)
    if not target:
        return

    chat_id = message.chat.id

    try:
        await ensure_peer(chat_id, target)

        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(chat_id),
                participant=await app.resolve_peer(target),
                banned_rights=ChatBannedRights(view_messages=True)
            )
        )

        await message.reply(f"🚫 {mention} BAN berildi", parse_mode="HTML")

    except Exception as e:
        print("Ban error:", e)

    asyncio.create_task(delete_command(message))

# ================= UNBAN =================

@dp.message(lambda m: m.text.startswith(".unban"))
async def unban_user(message: types.Message):

    if not await is_admin(message):
        return

    target, mention = await get_target(message)
    if not target:
        return

    chat_id = message.chat.id

    try:
        await ensure_peer(chat_id, target)

        await app.invoke(
            EditBanned(
                channel=await app.resolve_peer(chat_id),
                participant=await app.resolve_peer(target),
                banned_rights=ChatBannedRights()
            )
        )

        await message.reply(f"♻️ {mention} UNBAN qilindi", parse_mode="HTML")

    except Exception as e:
        print("Unban error:", e)

    asyncio.create_task(delete_command(message))

# ================= MAIN =================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await app.start()
    print("Hybrid bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
