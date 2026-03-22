import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, get_products_by_category, add_product

# --- SOZLAMALAR ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM HOLATLARI ---
class OrderState(StatesGroup):
    waiting_for_address = State()
    waiting_for_payment_method = State()

class AdminAddProduct(StatesGroup):
    category = State()
    photo = State()
    name = State()
    price = State()
    color = State()
    size = State()

# Razmer so'ralmaydigan toifalar (Kichik harflar bilan tekshiramiz)
NO_SIZE_CATEGORIES = ["ayollar kosmetikasi", "ayollar taqinchoqlari", "telefon aksessuarlar"]

# --- KLAVIATURALAR ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Katalog")],
        [KeyboardButton(text="🛒 Savat"), KeyboardButton(text="📦 Buyurtmalarim")],
        [KeyboardButton(text="ℹ️ FIRDAVS GROUP haqida"), KeyboardButton(text="📞 Aloqa")]
    ], resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Mahsulot qo'shish")],
        [KeyboardButton(text="📦 Barcha mahsulotlar"), KeyboardButton(text="🗑 O'chirish")],
        [KeyboardButton(text="⬅️ Asosiy menyuga qaytish")]
    ], resize_keyboard=True
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
    ], resize_keyboard=True
)

payment_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💵 Naqd pul (Kuryerga)")],
        [KeyboardButton(text="💳 Karta orqali (Tez kunda)")]
    ], resize_keyboard=True
)


# ==========================================
#             ADMIN QISMI
# ==========================================

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("👨‍💻 Admin panelga xush kelibsiz!", reply_markup=admin_menu)

@dp.message(F.text == "⬅️ Asosiy menyuga qaytish")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyudasiz:", reply_markup=main_menu)

@dp.message(F.text == "➕ Mahsulot qo'shish")
async def add_product_start(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("Qaysi toifaga mahsulot qo'shamiz?", reply_markup=catalog_menu)
        await state.set_state(AdminAddProduct.category)

@dp.callback_query(AdminAddProduct.category, F.data.startswith("cat_"))
async def process_add_category(callback: types.CallbackQuery, state: FSMContext):
    category_name = callback.data.split("_")[1] # Masalan: "ayollar kosmetikasi"
    await state.update_data(category=category_name)
    await callback.message.answer(f"✅ Toifa: <b>{category_name.capitalize()}</b>\n\nEndi rasmni yuboring:", parse_mode="HTML")
    await state.set_state(AdminAddProduct.photo)
    await callback.answer()

@dp.message(AdminAddProduct.photo, F.photo)
async def process_add_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await message.answer("📸 Rasm qabul qilindi.\n\nMahsulot nomini yozing:")
    await state.set_state(AdminAddProduct.name)

@dp.message(AdminAddProduct.name)
async def process_add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("✏️ Nom qabul qilindi.\n\nNarxini faqat raqamlarda yozing (Masalan: 150000):")
    await state.set_state(AdminAddProduct.price)

@dp.message(AdminAddProduct.price)
async def process_add_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, narxni faqat raqamlarda kiriting!")
        return
    await state.update_data(price=int(message.text))
    await message.answer("🎨 Rangini kiriting (Agar bo'lmasa 'Yo'q' deb yozing):")
    await state.set_state(AdminAddProduct.color)

@dp.message(AdminAddProduct.color)
async def process_add_color(message: types.Message, state: FSMContext):
    await state.update_data(color=message.text)
    data = await state.get_data()
    category = data.get("category").lower()
    
    if category in NO_SIZE_CATEGORIES:
        await state.update_data(size="Mavjud emas")
        await finish_adding_product(message, state)
    else:
        await message.answer("📏 Razmerni kiriting (Masalan: 42, XL):")
        await state.set_state(AdminAddProduct.size)

@dp.message(AdminAddProduct.size)
async def process_add_size(message: types.Message, state: FSMContext):
    await state.update_data(size=message.text)
    await finish_adding_product(message, state)

async def finish_adding_product(message: types.Message, state: FSMContext):
    data = await state.get_data()
    add_product(
        category=data['category'], name=data['name'], price=data['price'],
        size=data['size'], color=data['color'], image_url=data['photo']
    )
    await message.answer("✅ Mahsulot bazaga muvaffaqiyatli qo'shildi!", reply_markup=admin_menu)
    await state.clear()


# ==========================================
#             MIJOZLAR QISMI
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "<b>FIRDAVS GROUP</b> do'koniga xush kelibsiz:",
        reply_markup=main_menu, parse_mode="HTML"
    )

@dp.message(F.text == "🛍 Katalog")
async def show_catalog(message: types.Message):
    await message.answer("🛒 Bo'limni tanlang:", reply_markup=catalog_menu)

# Mijoz toifani tanlaganda ishlaydi (Hozircha test rejimida)
@dp.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: types.CallbackQuery, state: FSMContext):
    # Agar admin mahsulot qo'shayotgan bo'lsa, bu funksiya ishlamasligi uchun tekshiramiz
    current_state = await state.get_state()
    if current_state == AdminAddProduct.category.state:
        return # Admin flowiga xalaqit bermaydi

    category_name = callback.data.split("_")[1]
    products = get_products_by_category(category_name)
    
    if not products:
        await callback.message.answer(f"Hozircha <b>{category_name.capitalize()}</b> bo'limida mahsulotlar yo'q.", parse_mode="HTML")
    else:
        await callback.message.answer(f"Bazada {len(products)} ta mahsulot bor. (Katalog dizayni tez kunda!)")
    
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🛒 Savatchaga o'tish (Test)", callback_data="checkout_order")]])
    await callback.message.answer("Savatchaga o'tish:", reply_markup=markup)
    await callback.answer()

@dp.callback_query(F.data == "checkout_order")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Dastavka uchun manzilingizni kiriting yoki <b>Lokatsiya</b> yuboring:",
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
    if message.text == "💳 Karta orqali (Tez kunda)":
        await message.answer("Hozircha kuryerga naqd to'lashingiz mumkin. Qaytadan tanlang.")
        return
        
    user_data = await state.get_data()
    address_info = user_data.get("address")
    
    admin_text = (
        f"📦 <b>Yangi buyurtma!</b>\n"
        f"👤 Mijoz: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"📍 Manzil: {address_info}\n"
        f"💵 To'lov: Kuryerga naqd"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
    except Exception as e:
        print(f"Xato: {e}")

    await message.answer("✅ Buyurtmangiz qabul qilindi! Kuryer bog'lanadi.", reply_markup=main_menu)
    await state.clear()

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    print("FIRDAVS GROUP boti ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
