import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# TOKEN va ADMIN ID ni o'zingizniki bilan almashtiring
API_TOKEN = '8883984125:AAFaDXz9apNNsCz2fxAkv8dnreqto0b9HQQ'
ADMIN_ID = 8584102298 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Konkurs holati
is_contest_active = False

# Adminlikni tekshirish
def is_admin(user_id):
    return user_id == ADMIN_ID

# Admin paneli uchun tugmalar
def admin_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Konkursni boshlash", callback_data="start_c")],
        [InlineKeyboardButton(text="🛑 Konkursni to‘xtatish", callback_data="stop_c")]
    ])
    return keyboard

# /start buyrug'i
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Salom! Rasm chizish konkursi botiga xush kelibsiz!")

# Admin paneli (tugmalar bilan)
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("Xush kelibsiz, Admin! Quyidagi tugmalardan foydalaning:", reply_markup=admin_keyboard())
    else:
        await message.answer("Siz admin emassiz!")

# Tugmalarni boshqarish
@dp.callback_query(F.data.in_(["start_c", "stop_c"]))
async def callback_admin(callback: types.CallbackQuery):
    global is_contest_active
    if callback.data == "start_c":
        is_contest_active = True
        await callback.message.edit_text("✅ Konkurs boshlandi! Foydalanuvchilar rasm yuborishlari mumkin.")
    elif callback.data == "stop_c":
        is_contest_active = False
        await callback.message.edit_text("🛑 Konkurs to‘xtatildi!")

# Rasm qabul qilish
@dp.message(F.photo)
async def handle_photo(message: Message):
    if not is_contest_active:
        await message.answer("Hozir konkurs ochiq emas. Administrator konkursni boshlashini kuting.")
        return
    
    await message.answer("Rasmingiz qabul qilindi! Adminlar ko'rib chiqishguncha kuting.")
    
    # Rasmni adminga yuborish
    await bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=message.photo[-1].file_id, 
        caption=f"Yangi rasm keldi!\nMuallif: {message.from_user.full_name or 'Noma\'lum'}"
    )

# Botni ishga tushirish
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())