import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, get_products_by_category

# .env faylini o'qiymiz
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Botga to'g'ridan-to'g'ri ulanamiz (proxysiz)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
# ... qolgan kodlar o'zgarishsiz ...

# --- FSM (Holatlar) ---
class OrderState(StatesGroup):
    waiting_for_address = State()
    waiting_for_payment_method = State()

# --- Klaviaturalar ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Katalog")],
        [KeyboardButton(text="🛒 Savat"), KeyboardButton(text="📦 Buyurtmalarim")],
        [KeyboardButton(text="ℹ️ FIRDAVS GROUP haqida"), KeyboardButton(text="📞 Aloqa")]
    ],
    resize_keyboard=True
)

catalog_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Ayollar kiyimlari", callback_data="cat_ayollar kiyimlari")],
        [InlineKeyboardButton(text="👠 Ayollar oyoq kiyimlari", callback_data="cat_ayollar oyoq kiyimlari")],
        [InlineKeyboardButton(text="💄 Ayollar kosmetikasi", callback_data="cat_ayollar kosmetikasi")],
        [InlineKeyboardButton(text="👜 Ayollar taqinchoqlari", callback_data="cat_ayollar taqinchoqlari")],
        [InlineKeyboardButton(text="👔 Erkaklar kiyimlari", callback_data="cat_erkaklar kiyimlari")],
        [InlineKeyboardButton(text="👞 Erkaklar oyoq kiyimlari", callback_data="cat_erkaklar oyoq kiyimlari")],
        [InlineKeyboardButton(text="👶 Bolalar uchun", callback_data="cat_bolalar uchun")],
        [InlineKeyboardButton(text="📱 Telefon aksessuarlar", callback_data="cat_telefon aksessuarlar")]
    ]
)

location_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)],
        [KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)

payment_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💵 Naqd pul (Kuryerga)")],
        [KeyboardButton(text="💳 Karta orqali (Click/Payme - Tez kunda)")]
    ],
    resize_keyboard=True
)

# --- Handlerlar ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "<b>FIRDAVS GROUP</b> onlayn do'koniga xush kelibsiz. Quyidagi menyudan foydalaning:",
        reply_markup=main_menu, parse_mode="HTML"
    )

@dp.message(F.text == "🛍 Katalog")
async def show_catalog(message: types.Message):
    await message.answer("🛒 Bo'limni tanlang:", reply_markup=catalog_menu)

@dp.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: types.CallbackQuery):
    category_name = callback.data.split("_")[1]
    products = get_products_by_category(category_name)
    
    if not products:
        await callback.message.answer(f"Hozircha <b>{category_name.capitalize()}</b> bo'limida mahsulotlar yo'q.", parse_mode="HTML")
    else:
        # Baza ulanganidan keyin shu yerda mahsulotlar ro'yxati chiqadi
        pass
    
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🛒 Savatchaga o'tish", callback_data="checkout_order")]])
    await callback.message.answer("Sinov uchun: Savatchaga o'tish tugmasini bosing 👇", reply_markup=markup)
    await callback.answer()

@dp.callback_query(F.data == "checkout_order")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Dastavka uchun manzilingizni kiriting.\n"
        "Masalan: <i>Toshkent sh., Uchtepa tumani, Lutfiy ko'chasi, 12-uy</i>\n\n"
        "Yoki pastdagi tugma orqali <b>Lokatsiya</b> yuboring:",
        reply_markup=location_menu, parse_mode="HTML"
    )
    await state.set_state(OrderState.waiting_for_address)
    await callback.answer()

@dp.message(OrderState.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Buyurtma bekor qilindi.", reply_markup=main_menu)
        return

    address_info = f"Google Maps: https://maps.google.com/?q={message.location.latitude},{message.location.longitude}" if message.location else message.text
    
    await state.update_data(address=address_info)
    
    await message.answer("Manzil qabul qilindi. To'lov turini tanlang:", reply_markup=payment_menu)
    await state.set_state(OrderState.waiting_for_payment_method)

@dp.message(OrderState.waiting_for_payment_method)
async def process_payment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    address_info = user_data.get("address")
    
    if message.text == "💳 Karta orqali (Click/Payme - Tez kunda)":
        await message.answer("Bu funksiya tez kunda ishga tushadi. Hozircha kuryerga naqd to'lashingiz mumkin.\nIltimos, qaytadan tanlang.")
        return
        
    admin_text = (
        f"📦 <b>Yangi buyurtma!</b>\n"
        f"👤 Mijoz: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"📍 Manzil: {address_info}\n"
        f"💵 To'lov: Kuryerga naqd"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
    except Exception as e:
        print(f"Adminga xabar yuborishda xatolik: {e}")

    await message.answer("✅ Buyurtmangiz qabul qilindi! Kuryer tez orada siz bilan bog'lanadi.", reply_markup=main_menu)
    await state.clear()

async def main():
    init_db() 
    logging.basicConfig(level=logging.INFO)
    print("FIRDAVS GROUP boti ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())