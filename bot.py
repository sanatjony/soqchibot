import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.enums import ChatMemberStatus
from datetime import datetime, timedelta
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_strikes = {}

from aiogram.filters import CommandStart

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.reply(
        "Salom 👋\n\n"
        "Men guruhni himoya qiluvchi botman.\n"
        "Guruhga ssilka tashlash taqiqlangan 🚫\n\n"
        "Qoidani buzganlar ogohlantiriladi va ban qilinadi."
    )

LINK_PATTERN = re.compile(
    r"(https?:\/\/|t\.me\/|telegram\.me\/|@\w+)",
    re.IGNORECASE
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

# ================= LINK CHECK =================

def is_link(text):
    return bool(LINK_PATTERN.search(text))

# ================= NEW USER JOIN =================

@dp.message(lambda m: m.new_chat_members)
async def new_member(message: types.Message):

    try:
        await message.delete()
    except:
        pass

    for user in message.new_chat_members:
        try:
            await bot.restrict_chat_member(
                message.chat.id,
                user.id,
                ChatPermissions(can_send_messages=False),
                until_date=datetime.now() + timedelta(minutes=1)
            )
        except:
            pass

        msg = await message.answer(
            f"👋 {user.mention_html()} guruhga xush kelibsiz!\n1 daqiqa yozish cheklovi qo‘llandi.",
            parse_mode="HTML"
        )

        asyncio.create_task(auto_delete(msg))

# ================= USER LEFT =================
@dp.message(lambda m: m.left_chat_member)
async def left_member(message: types.Message):
    try:
        await message.delete()
    except:
        pass
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
    username = message.from_user.mention_html()

    # message delete safe
    try:
        await message.delete()
    except:
        pass

    strikes = user_strikes.get(user_id, 0) + 1
    user_strikes[user_id] = strikes

    if strikes == 1:
        msg = await message.answer(
            "⚠️ Guruhga ssilka tashlash mumkin emas.\nYana tashlasangiz ban beriladi.",
            parse_mode="HTML"
        )
        asyncio.create_task(auto_delete(msg))

    elif strikes == 2:
        msg = await message.answer(
            "❗ Oxirgi ogohlantirish!\nKeyingi ssilka → BAN",
            parse_mode="HTML"
        )
        asyncio.create_task(auto_delete(msg))

    elif strikes >= 3:
        await bot.ban_chat_member(chat_id, user_id)
        msg = await message.answer(
            f"🚫 {username} guruh qoidalarini buzdi va ban qilindi.",
            parse_mode="HTML"
        )
        asyncio.create_task(auto_delete(msg))
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

    await bot.restrict_chat_member(
        message.chat.id,
        user_id,
        ChatPermissions(can_send_messages=False),
        until_date=until_date
    )

    asyncio.create_task(auto_delete(message))

# ================= UNMUTE =================

@dp.message(lambda m: m.text == ".unmute")
async def unmute_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    user_id = message.reply_to_message.from_user.id

    await bot.restrict_chat_member(
        message.chat.id,
        user_id,
        ChatPermissions(can_send_messages=True)
    )

    user_strikes[user_id] = 0
    asyncio.create_task(auto_delete(message))

# ================= BAN =================

@dp.message(lambda m: m.text == ".ban")
async def ban_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    user_id = message.reply_to_message.from_user.id
    await bot.ban_chat_member(message.chat.id, user_id)

    asyncio.create_task(auto_delete(message))

# ================= UNBAN =================

@dp.message(lambda m: m.text == ".unban")
async def unban_user(message: types.Message):

    if not message.reply_to_message:
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        return

    user_id = message.reply_to_message.from_user.id
    await bot.unban_chat_member(message.chat.id, user_id)

    user_strikes[user_id] = 0
    asyncio.create_task(auto_delete(message))

# ================= START =================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)

    # eski container o‘lishini kutamiz
    await asyncio.sleep(15)

    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())












