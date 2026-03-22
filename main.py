import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, WebAppInfo
from aiohttp import web
from database import init_db, get_products_by_category, add_product, add_to_cart, get_cart_items, clear_cart, toggle_wishlist

# --- SOZLAMALAR ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM HOLATLARI ---
class OrderState(StatesGroup):
    waiting_for_address = State()
    waiting_for_payment = State()

class AdminAddProduct(StatesGroup):
    category = State()
    photo = State()
    name = State()
    price = State()
    color = State()
    size = State()

NO_SIZE_CATEGORIES = ["ayollar kosmetikasi", "ayollar taqinchoqlari", "telefon aksessuarlar"]

# --- KLAVIATURALAR (Web App ulangan YANGLI MENYU) ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        # Web App (Mini ilova) ni ochadigan katta tugma (Ninioshop uslubida)
        [KeyboardButton(text="🏪 Do'kon", web_app=WebAppInfo(url="https://firdavs2002-eng.github.io/firdavs-group-bot/"))],
        [KeyboardButton(text="📦 Mening buyurtmalarim")],
        [KeyboardButton(text="⚙️ Tilni o'zgartirish"), KeyboardButton(text="💬 Chat")]
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
        [KeyboardButton(text="💳 Karta orqali (Uzum/Click)")]
    ], resize_keyboard=True
)

# ==========================================
#        WILDBERRIES LOGIKASI (Ichki qism)
# ==========================================

def get_product_markup(product_id, current_index, total_count, category):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 Savatga qo'shish", callback_data=f"add_cart_{product_id}"),
            InlineKeyboardButton(text="❤️ Saqlash", callback_data=f"wish_{product_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"prev_{category}_{current_index}"),
            InlineKeyboardButton(text=f"{current_index + 1} / {total_count}", callback_data="ignore"),
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"next_{category}_{current_index}")
        ],
        [InlineKeyboardButton(text="🔙 Kategoriyalarga qaytish", callback_data="back_to_cats")]
    ])

async def show_product_step(message, products, index, category, edit=False):
    product = products[index]
    caption = (
        f"🛍 <b>{product[1]}</b>\n\n"
        f"💰 Narxi: {product[2]:,} so'm\n"
        f"📏 Razmer: {product[3]}\n"
        f"🎨 Rangi: {product[4]}\n\n"
        f"🚚 Yetkazib berish: 1 kun (Mavjud)"
    )
    markup = get_product_markup(product[0], index, len(products), category)
    
    if edit:
        try:
            input_media = InputMediaPhoto(media=product[5], caption=caption, parse_mode="HTML")
            await message.edit_media(media=input_media, reply_markup=markup)
        except Exception:
            pass
    else:
        await message.answer_photo(photo=product[5], caption=caption, reply_markup=markup, parse_mode="HTML")

# --- SAVAT VA SEVIMLILAR MANTIQI ---
@dp.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    add_to_cart(callback.from_user.id, product_id)
    await callback.answer("✅ Mahsulot savatga qo'shildi!", show_alert=False)

@dp.callback_query(F.data.startswith("wish_"))
async def add_to_wishlist_handler(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    status = toggle_wishlist(callback.from_user.id, product_id)
    await callback.answer(f"❤️ Sevimlilarga {status}!", show_alert=False)

@dp.message(F.text == "🛒 Savat")
async def view_cart(message: types.Message):
    items = get_cart_items(message.from_user.id)
    if not items:
        await message.answer("Savat bo'sh. Do'kondan o'zingizga yoqqan mahsulotlarni tanlang! 😊")
        return

    res = "🛒 <b>Sizning savatingiz:</b>\n\n"
    total = 0
    for name, price, qty, p_id in items:
        res += f"🔸 {name} - {qty} dona x {price:,} = {qty*price:,} so'm\n"
        total += qty * price
    res += f"\n<b>Jami to'lov: {total:,} so'm</b>"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buyurtmani rasmiylashtirish", callback_data="checkout_start")],
        [InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart")]
    ])
    await message.answer(res, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: types.CallbackQuery):
    clear_cart(callback.from_user.id)
    await callback.message.edit_text("Savat tozalandi. 🗑")
    await callback.answer()

# --- BUYURTMA RASHMIYLASHTIRISH (Checkout) ---
@dp.callback_query(F.data == "checkout_start")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "🚚 <b>Dastavka qayerga yetkazilsin?</b>\nManzilingizni yozing yoki lokatsiya tashlang:", 
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

    address = f"Lokatsiya: https://maps.google.com/?q={message.location.latitude},{message.location.longitude}" if message.location else message.text
    await state.update_data(address=address)
    
    await message.answer("💵 To'lov usulini tanlang:", reply_markup=payment_menu)
    await state.set_state(OrderState.waiting_for_payment)

@dp.message(OrderState.waiting_for_payment)
async def process_payment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    address = user_data.get("address")
    payment_method = message.text
    
    items = get_cart_items(message.from_user.id)
    total = sum(qty * price for name, price, qty, pid in items)
    
    order_text = f"📦 <b>YANGI BUYURTMA!</b>\n\n"
    order_text += f"👤 Mijoz: {message.from_user.full_name} (@{message.from_user.username})\n"
    order_text += f"📍 Manzil: {address}\n"
    order_text += f"💳 To'lov: {payment_method}\n\n"
    order_text += "🛍 <b>Mahsulotlar:</b>\n"
    for name, price, qty, pid in items:
        order_text += f"- {name} ({qty} ta)\n"
    order_text += f"\n💰 <b>Jami summa: {total:,} so'm</b>"

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=order_text, parse_mode="HTML")
    except Exception as e:
        print("Admin topilmadi:", e)

    clear_cart(message.from_user.id)
    await state.clear()
    await message.answer("✅ Buyurtmangiz muvaffaqiyatli qabul qilindi! Tez orada kuryerimiz siz bilan bog'lanadi.", reply_markup=main_menu)

# ==========================================
#             ADMIN VA START
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Assalomu alaykum, {message.from_user.first_name}!\n<b>FIRDAVS GROUP</b> onlayn do'koniga xush kelibsiz!", reply_markup=main_menu, parse_mode="HTML")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("👨‍💻 Admin panel:", reply_markup=admin_menu)

@dp.message(F.text == "⬅️ Asosiy menyuga qaytish")
async def back_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu)

@dp.message(F.text == "➕ Mahsulot qo'shish")
async def admin_add(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("Toifani tanlang:", reply_markup=catalog_menu)
        await state.set_state(AdminAddProduct.category)

@dp.callback_query(AdminAddProduct.category, F.data.startswith("cat_"))
async def admin_cat(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data.split("_")[1])
    await callback.message.answer("Rasmni yuboring:")
    await state.set_state(AdminAddProduct.photo)
    await callback.answer()

@dp.message(AdminAddProduct.photo, F.photo)
async def admin_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("Nomini yozing:")
    await state.set_state(AdminAddProduct.name)

@dp.message(AdminAddProduct.name)
async def admin_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Narxini kiriting (raqam):")
    await state.set_state(AdminAddProduct.price)

@dp.message(AdminAddProduct.price)
async def admin_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam kiriting!")
        return
    await state.update_data(price=int(message.text))
    await message.answer("Rangini yozing (yo'q bo'lsa 'yo'q'):")
    await state.set_state(AdminAddProduct.color)

@dp.message(AdminAddProduct.color)
async def admin_color(message: types.Message, state: FSMContext):
    await state.update_data(color=message.text)
    data = await state.get_data()
    if data['category'].lower() in NO_SIZE_CATEGORIES:
        await state.update_data(size="Mavjud emas")
        await finish_add(message, state)
    else:
        await message.answer("Razmerini yozing:")
        await state.set_state(AdminAddProduct.size)

@dp.message(AdminAddProduct.size)
async def admin_size(message: types.Message, state: FSMContext):
    await state.update_data(size=message.text)
    await finish_add(message, state)

async def finish_add(message: types.Message, state: FSMContext):
    d = await state.get_data()
    add_product(d['category'], d['name'], d['price'], d['size'], d['color'], d['photo'])
    await message.answer("✅ Mahsulot katalogga qo'shildi!", reply_markup=admin_menu)
    await state.clear()

# --- RENDER UCHUN YOLG'ONCHI SERVER ---
async def handle(request):
    return web.Response(text="FIRDAVS GROUP Web App Boti 24/7 ishlamoqda!")

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    print("FIRDAVS GROUP Web App Boti ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
            
