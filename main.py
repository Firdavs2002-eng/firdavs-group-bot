import os
import io
import asyncio
import random
import time
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiohttp import web, FormData
from database import init_db, get_products_by_category, set_user_lang, get_user_lang, get_all_categories, save_user_data, get_user_data, set_category_image, add_product

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "7723220237"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM (Holatlar) ---
class AdminCatImage(StatesGroup):
    category_name = State()
    photo = State()

class AdminAddProduct(StatesGroup):
    category = State()
    name = State()
    price = State()
    photo = State()

LANGS = {
    'uz': {
        'welcome': "Assalomu alaykum, {name}!\n<b>FIRDAVS GROUP</b> do'koniga xush kelibsiz! 🚀",
        'shop': "🏪 Do'konni ochish", 'orders': "📦 Buyurtmalarim", 
        'lang': "⚙️ Til", 'chat': "💬 Chat (AI)",
        'ai_start': "🤖 <b>Firdavs AI</b>: Assalomu alaykum! Men sun'iy intellekt yordamchisiman. Sizga nima qidirishga yordam beray?",
        'choose_lang': "🇺🇿 Tilni tanlang:"
    },
    'ru': {
        'welcome': "Здравствуйте, {name}!\nДобро пожаловать в <b>FIRDAVS GROUP</b>! 🚀",
        'shop': "🏪 Открыть магазин", 'orders': "📦 Мои заказы", 
        'lang': "⚙️ Язык", 'chat': "💬 Чат (ИИ)",
        'ai_start': "🤖 <b>Firdavs AI</b>: Здравствуйте! Я ИИ-помощник. Чем могу помочь?",
        'choose_lang': "🇷🇺 Выберите язык:"
    },
    'en': {
        'welcome': "Hello, {name}!\nWelcome to <b>FIRDAVS GROUP</b>! 🚀",
        'shop': "🏪 Open Shop", 'orders': "📦 My Orders", 
        'lang': "⚙️ Language", 'chat': "💬 Chat (AI)",
        'ai_start': "🤖 <b>Firdavs AI</b>: Hello! I am your AI assistant. How can I help you?",
        'choose_lang': "🇬🇧 Choose language:"
    }
}

def get_main_menu(user_id, lang):
    ts = int(time.time())
    shop_url = f"https://firdavs2002-eng.github.io/firdavs-group-bot/?lang={lang}&uid={user_id}&v={ts}"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGS[lang]['shop'], web_app=WebAppInfo(url=shop_url))],
            [KeyboardButton(text=LANGS[lang]['lang']), KeyboardButton(text=LANGS[lang]['chat'])],
            [KeyboardButton(text=LANGS[lang]['orders'])]
        ], resize_keyboard=True
    )

def get_lang(uid): return get_user_lang(uid) if get_user_lang(uid) in LANGS else 'uz'

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_lang(message.from_user.id)
    await message.answer(LANGS[lang]['welcome'].format(name=message.from_user.first_name), reply_markup=get_main_menu(message.from_user.id, lang), parse_mode="HTML")

# --- 3 TA TIL TUGMASI (TO'G'RILANDI) ---
@dp.message(F.text.in_(["⚙️ Til", "⚙️ Язык", "⚙️ Language"]))
async def change_lang_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz"), 
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")]
    ])
    await message.answer(LANGS[lang]['choose_lang'], reply_markup=menu)

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang_handler(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, new_lang)
    await callback.message.delete()
    await callback.message.answer(LANGS[new_lang]['welcome'].format(name=callback.from_user.first_name), reply_markup=get_main_menu(callback.from_user.id, new_lang), parse_mode="HTML")

# --- AQLLI AI CHAT ---
@dp.message(F.text.in_(["💬 Chat (AI)", "💬 Чат (ИИ)", "💬 Chat (AI)"]))
async def chat_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    await message.answer(LANGS[lang]['ai_start'], parse_mode="HTML")

# =======================================================
#                  ADMIN PANEL (MAHSULOT QO'SHISH)
# =======================================================
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if str(message.from_user.id) == ADMIN_ID:
        menu = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🛒 Mahsulot qo'shish")],
            [KeyboardButton(text="🖼 Toifa rasmini o'zgartirish")], 
            [KeyboardButton(text="⬅️ Asosiy menyuga qaytish")]
        ], resize_keyboard=True)
        await message.answer("👨‍💻 Boshqaruv paneli:", reply_markup=menu)

@dp.message(F.text == "⬅️ Asosiy menyuga qaytish")
async def back_main(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(message.from_user.id, get_lang(message.from_user.id)))

# -- TOIFA VA MAHSULOT UCHUN KATEGORIYALAR MENYUSI --
admin_cat_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛍 Ayollar kiyimi", callback_data="cat_Ayollar kiyimlari"), InlineKeyboardButton(text="👠 Ayollar oyoq kiyimi", callback_data="cat_Ayollar oyoq kiyimlari")],
    [InlineKeyboardButton(text="💄 Kosmetika", callback_data="cat_Ayollar kosmetikasi"), InlineKeyboardButton(text="👜 Taqinchoq", callback_data="cat_Ayollar taqinchoqlari")],
    [InlineKeyboardButton(text="👔 Erkaklar kiyimi", callback_data="cat_Erkaklar kiyimlari"), InlineKeyboardButton(text="👞 Erkaklar oyoq kiyimi", callback_data="cat_Erkaklar oyoq kiyimlari")],
    [InlineKeyboardButton(text="👶 Bolalar uchun", callback_data="cat_Bolalar uchun"), InlineKeyboardButton(text="📱 Aksessuar", callback_data="cat_Telefon aksessuarlar")]
])

# 1. TOIFA RASMINI O'ZGARTIRISH
@dp.message(F.text == "🖼 Toifa rasmini o'zgartirish")
async def start_cat_img(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == ADMIN_ID:
        await message.answer("Qaysi toifaga rasm qo'shmoqchisiz?", reply_markup=admin_cat_menu)
        await state.set_state(AdminCatImage.category_name)

@dp.callback_query(AdminCatImage.category_name, F.data.startswith("cat_"))
async def process_cat_name(callback: types.CallbackQuery, state: FSMContext):
    cat_name = callback.data.split("_")[1]
    await state.update_data(category_name=cat_name)
    await callback.message.answer(f"📸 <b>{cat_name}</b> uchun rasm yuboring:", parse_mode="HTML")
    await state.set_state(AdminCatImage.photo)

@dp.message(AdminCatImage.photo, F.photo)
async def process_cat_photo(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("⏳ Yuklanmoqda...")
    data = await state.get_data()
    photo_io = io.BytesIO()
    await bot.download(message.photo[-1], destination=photo_io)
    photo_io.seek(0)
    form = FormData()
    form.add_field('file', photo_io.read(), filename='image.jpg', content_type='image/jpeg')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://telegra.ph/upload', data=form) as resp:
                res = await resp.json()
                set_category_image(data['category_name'], "https://telegra.ph" + res[0]['src'])
        await wait_msg.edit_text(f"✅ Rasm o'zgardi.")
    except: await wait_msg.edit_text("❌ Xatolik.")
    await state.clear()

# 2. MAHSULOT QO'SHISH
@dp.message(F.text == "🛒 Mahsulot qo'shish")
async def start_add_prod(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == ADMIN_ID:
        await message.answer("Yangi mahsulot qaysi toifaga tegishli?", reply_markup=admin_cat_menu)
        await state.set_state(AdminAddProduct.category)

@dp.callback_query(AdminAddProduct.category, F.data.startswith("cat_"))
async def add_prod_cat(callback: types.CallbackQuery, state: FSMContext):
    cat_name = callback.data.split("_")[1]
    await state.update_data(category=cat_name)
    await callback.message.answer(f"Tanlandi: <b>{cat_name}</b>\n\nEndi mahsulot nomini yozing (Masalan: Premium Krossovka):", parse_mode="HTML")
    await state.set_state(AdminAddProduct.name)

@dp.message(AdminAddProduct.name, F.text)
async def add_prod_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Yaxshi! Endi mahsulot narxini faqat raqamlarda yozing (Masalan: 150000):")
    await state.set_state(AdminAddProduct.price)

@dp.message(AdminAddProduct.price, F.text)
async def add_prod_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, narxni faqat raqamlarda yozing:")
        return
    await state.update_data(price=int(message.text))
    await message.answer("Ajoyib! Oxirgi qadam: Mahsulotning chiroyli rasmini yuboring.")
    await state.set_state(AdminAddProduct.photo)

@dp.message(AdminAddProduct.photo, F.photo)
async def add_prod_photo(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("⏳ Bazaga saqlanmoqda...")
    data = await state.get_data()
    
    photo_io = io.BytesIO()
    await bot.download(message.photo[-1], destination=photo_io)
    photo_io.seek(0)
    form = FormData()
    form.add_field('file', photo_io.read(), filename='image.jpg', content_type='image/jpeg')
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://telegra.ph/upload', data=form) as resp:
                res = await resp.json()
                photo_url = "https://telegra.ph" + res[0]['src']
                
        # Bazaga saqlash
        add_product(data['category'], data['name'], data['price'], "", "", photo_url)
        await wait_msg.edit_text(f"✅ <b>{data['name']}</b> mahsuloti muvaffaqiyatli qo'shildi!\nWeb App do'koningizga kirib ko'rishingiz mumkin.", parse_mode="HTML")
    except Exception as e:
        await wait_msg.edit_text("❌ Rasm yuklashda xatolik yuz berdi. Boshqa rasm bilan urinib ko'ring.")
    
    await state.clear()

# --- CHAT AI LOGIKASI ---
@dp.message(F.text)
async def ai_handler(message: types.Message):
    if message.text.startswith("🏪") or message.text.startswith("⚙️") or message.text.startswith("📦") or message.text.startswith("🛒") or message.text.startswith("🖼") or message.text.startswith("⬅️"): return
    text = message.text.lower()
    reply = "Kechirasiz, men do'kon yordamchisiman. Mahsulotlar haqida so'rang yoki 'Do'konni ochish' tugmasini bosing."
    if "salom" in text: reply = "Assalomu alaykum! Firdavs Group do'konida qanday mahsulot qidiryapsiz?"
    elif "dastavka" in text or "yetkazib" in text: reply = "Bizda O'zbekiston bo'ylab tezkor yetkazib berish mavjud."
    elif "narx" in text: reply = "Barcha narxlarni do'konimizga kirib, 'Katalog' bo'limidan ko'rishingiz mumkin."
    await message.answer(f"🤖 <b>AI:</b> {reply}", parse_mode="HTML")

# --- API SERVER ---
def set_cors(): return {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"}
async def handle_options(request): return web.Response(headers=set_cors())

async def api_categories(request): return web.json_response(get_all_categories(), headers=set_cors())
async def api_products(request):
    cat = request.query.get('category')
    return web.json_response([{"id": p[0], "name": p[1], "price": p[2], "image_url": p[3]} for p in get_products_by_category(cat)], headers=set_cors())

async def api_send_code(request):
    uid, phone = request.query.get('uid'), request.query.get('phone')
    code = random.randint(1000, 9999) 
    try:
        await bot.send_message(chat_id=uid, text=f"🔐 <b>FIRDAVS GROUP</b>\nKod: <b>{code}</b>", parse_mode="HTML")
        return web.json_response({"success": True}, headers=set_cors())
    except: return web.json_response({"error": "Bot xatosi"}, status=500, headers=set_cors())

async def api_get_user(request):
    uid = request.query.get('uid')
    data = get_user_data(uid)
    if data: return web.json_response({"success": True, "data": data}, headers=set_cors())
    return web.json_response({"success": False}, headers=set_cors())

async def api_save_user(request):
    data = await request.json()
    save_user_data(data.get('uid'), data.get('name'), data.get('phone'), data.get('email'), data.get('dob'), data.get('gender'))
    return web.json_response({"success": True}, headers=set_cors())

async def main():
    init_db()
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Server OK"))
    app.router.add_get('/api/categories', api_categories) 
    app.router.add_get('/api/products', api_products)
    app.router.add_get('/api/send_code', api_send_code) 
    app.router.add_get('/api/get_user', api_get_user)
    app.router.add_post('/api/save_user', api_save_user)
    app.router.add_options('/api/save_user', handle_options)
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
