import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

API_TOKEN = os.getenv("8883984125:AAEXtpH54kyk0Ztu6bsSylCozwbFuwwbm8w")
ADMIN_ID = int(os.getenv("8584102298", "0"))

if not API_TOKEN:
    raise ValueError("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")
if ADMIN_ID == 0:
    raise ValueError("ADMIN_ID muhit o'zgaruvchisi o'rnatilmagan!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Konkurs holati va ishtirokchilar
is_contest_active = False
participants = {}  # {user_id: {"name": ..., "photo_id": ..., "count": ...}}

# ========================
# KLAVIATURALAR
# ========================

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Konkursni boshlash", callback_data="start_c")],
        [InlineKeyboardButton(text="🛑 Konkursni to'xtatish", callback_data="stop_c")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton(text="🏆 G'olibni e'lon qilish", callback_data="winner")],
        [InlineKeyboardButton(text="🗑 Ishtirokchilarni tozalash", callback_data="clear")],
    ])

def photo_action_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_{user_id}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")],
    ])

# ========================
# FOYDALANUVCHI KOMANDALAR
# ========================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    status = "🟢 Hozir konkurs ochiq!" if is_contest_active else "🔴 Hozir konkurs yo'q."
    await message.answer(
        f"🎨 Rasm chizish konkursi botiga xush kelibsiz!\n\n"
        f"{status}\n\n"
        f"Konkursga ishtirok etish uchun rasmingizni yuboring."
    )

@dp.message(Command("status"))
async def cmd_status(message: Message):
    status = "🟢 Konkurs ochiq" if is_contest_active else "🔴 Konkurs yopiq"
    count = len(participants)
    await message.answer(f"{status}\n👥 Ishtirokchilar: {count} nafar")

# ========================
# ADMIN PANEL
# ========================

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz!")
        return
    count = len(participants)
    status = "🟢 Ochiq" if is_contest_active else "🔴 Yopiq"
    await message.answer(
        f"👑 Admin panel\n\n"
        f"📌 Konkurs holati: {status}\n"
        f"👥 Ishtirokchilar: {count} nafar",
        reply_markup=admin_keyboard()
    )

@dp.callback_query(F.data.in_(["start_c", "stop_c", "stats", "winner", "clear"]))
async def callback_admin(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Faqat admin uchun!", show_alert=True)
        return

    global is_contest_active

    if callback.data == "start_c":
        is_contest_active = True
        await callback.message.edit_text(
            "✅ Konkurs boshlandi!\nIshtirokchilar rasm yuborishlarini kutamiz.",
            reply_markup=admin_keyboard()
        )

    elif callback.data == "stop_c":
        is_contest_active = False
        await callback.message.edit_text(
            "🛑 Konkurs to'xtatildi.",
            reply_markup=admin_keyboard()
        )

    elif callback.data == "stats":
        if not participants:
            text = "📊 Hali hech kim ishtirok etmagan."
        else:
            lines = ["📊 Ishtirokchilar ro'yxati:\n"]
            for i, (uid, data) in enumerate(participants.items(), 1):
                lines.append(f"{i}. {data['name']} — {data['count']} ta rasm")
            text = "\n".join(lines)
        await callback.message.edit_text(text, reply_markup=admin_keyboard())

    elif callback.data == "winner":
        if not participants:
            await callback.answer("Hali ishtirokchi yo'q!", show_alert=True)
            return
        winner_id = max(participants, key=lambda uid: participants[uid]["count"])
        winner = participants[winner_id]
        await callback.message.edit_text(
            f"🏆 G'olib: {winner['name']}\n"
            f"📸 Yuborilgan rasmlar: {winner['count']} ta",
            reply_markup=admin_keyboard()
        )

    elif callback.data == "clear":
        participants.clear()
        await callback.message.edit_text(
            "🗑 Ishtirokchilar ro'yxati tozalandi.",
            reply_markup=admin_keyboard()
        )

    await callback.answer()

# Admin rasm qabul/rad etish
@dp.callback_query(F.data.startswith("accept_") | F.data.startswith("reject_"))
async def photo_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Faqat admin!", show_alert=True)
        return

    action, user_id_str = callback.data.split("_", 1)
    user_id = int(user_id_str)

    if action == "accept":
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n✅ Qabul qilindi"
        )
        await bot.send_message(user_id, "✅ Rasmingiz konkursga qabul qilindi! Omad!")
        await callback.answer("Qabul qilindi!")
    else:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ Rad etildi"
        )
        await bot.send_message(user_id, "❌ Rasmingiz qabul qilinmadi. Boshqa rasm yuborishingiz mumkin.")
        await callback.answer("Rad etildi!")

# ========================
# RASM QABUL QILISH
# ========================

@dp.message(F.photo)
async def handle_photo(message: Message):
    if not is_contest_active:
        await message.answer("⏳ Hozir konkurs ochiq emas. Kuting!")
        return

    user_id = message.from_user.id
    user_name = message.from_user.full_name

    if user_id not in participants:
        participants[user_id] = {"name": user_name, "photo_id": message.photo[-1].file_id, "count": 0}
    participants[user_id]["count"] += 1
    participants[user_id]["photo_id"] = message.photo[-1].file_id

    await message.answer(
        f"🎨 Rasmingiz qabul qilindi!\n"
        f"📸 Siz {participants[user_id]['count']} ta rasm yubordingiz."
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=(
            f"🖼 Yangi rasm!\n"
            f"👤 Muallif: {user_name}\n"
            f"🆔 ID: {user_id}\n"
            f"📸 Jami: {participants[user_id]['count']} ta rasm"
        ),
        reply_markup=photo_action_keyboard(user_id)
    )

# ========================
# ISHGA TUSHIRISH
# ========================

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("✅ Bot ishga tushdi!")

    while True:
        try:
            await dp.start_polling(bot)
        except Exception:
            logging.exception("Botda xato yuz berdi. 10 soniyadan keyin qayta ishga tushiriladi...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
