import os
import io
import asyncio
import logging
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
from database import init_db, get_products_by_category, set_user_lang, get_user_lang, set_category_image, get_all_categories, save_user_data, get_user_data, update_user_coins

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "7723220237"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AdminCatImage(StatesGroup):
    category_name = State()
    photo = State()

LANGS = {
    'uz': {
        'welcome': "Assalomu alaykum, {name}!\n<b>FIRDAVS GROUP</b> do'koniga xush kelibsiz!",
        'shop': "🏪 Do'kon", 'game': "🎮 O'yin (Clicker)", 'orders': "📦 Buyurtmalarim", 
        'lang': "⚙️ Tilni o'zgartirish", 'chat': "💬 Chat",
        'chat_info': "🧑‍💻 <b>Qo'llab-quvvatlash:</b>\nSavollaringiz bo'lsa, @admin ga yozing.",
        'choose_lang': "🇺🇿 Tilni tanlang:"
    },
    'ru': {
        'welcome': "Здравствуйте, {name}!\nДобро пожаловать в <b>FIRDAVS GROUP</b>!",
        'shop': "🏪 Магазин", 'game': "🎮 Игра (Clicker)", 'orders': "📦 Мои заказы", 
        'lang': "⚙️ Изменить язык", 'chat': "💬 Чат",
        'chat_info': "🧑‍💻 <b>Поддержка:</b>\nНапишите @admin.",
        'choose_lang': "🇷🇺 Выберите язык:"
    },
    'en': {
        'welcome': "Hello, {name}!\nWelcome to <b>FIRDAVS GROUP</b>!",
        'shop': "🏪 Shop", 'game': "🎮 Game", 'orders': "📦 My Orders", 
        'lang': "⚙️ Change Language", 'chat': "💬 Chat",
        'chat_info': "🧑‍💻 <b>Support:</b>\nContact @admin.",
        'choose_lang': "🇬🇧 Choose language:"
    }
}

def get_main_menu(user_id, lang):
    ts = int(time.time())
    shop_url = f"https://firdavs2002-eng.github.io/firdavs-group-bot/?app=shop&lang={lang}&uid={user_id}&v={ts}"
    game_url = f"https://firdavs2002-eng.github.io/firdavs-group-bot/?app=game&lang={lang}&uid={user_id}&v={ts}"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGS[lang]['shop'], web_app=WebAppInfo(url=shop_url))],
            [KeyboardButton(text=LANGS[lang]['game'], web_app=WebAppInfo(url=game_url))],
            [KeyboardButton(text=LANGS[lang]['lang']), KeyboardButton(text=LANGS[lang]['chat'])],
            [KeyboardButton(text=LANGS[lang]['orders'])]
        ], resize_keyboard=True
    )

def get_lang(uid):
    lang = get_user_lang(uid)
    return lang if lang in LANGS else 'uz'

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_lang(message.from_user.id)
    text = LANGS[lang]['welcome'].format(name=message.from_user.first_name)
    await message.answer(text, reply_markup=get_main_menu(message.from_user.id, lang), parse_mode="HTML")

@dp.message(F.text.in_(["⚙️ Tilni o'zgartirish", "⚙️ Изменить язык", "⚙️ Change Language"]))
async def change_lang_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")]
    ])
    await message.answer(LANGS[lang]['choose_lang'], reply_markup=menu)

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang_handler(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, new_lang)
    await callback.message.delete()
    text = LANGS[new_lang]['welcome'].format(name=callback.from_user.first_name)
    await callback.message.answer(text, reply_markup=get_main_menu(callback.from_user.id, new_lang), parse_mode="HTML")

@dp.message(F.text.in_(["💬 Chat", "💬 Чат"]))
async def chat_cmd(message: types.Message):
    await message.answer(LANGS[get_lang(message.from_user.id)]['chat_info'], parse_mode="HTML")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if str(message.from_user.id) == ADMIN_ID:
        menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🖼 Toifa rasmini o'zgartirish")], [KeyboardButton(text="⬅️ Asosiy menyuga qaytish")]], resize_keyboard=True)
        await message.answer("👨‍💻 Admin panel:", reply_markup=menu)

@dp.message(F.text == "⬅️ Asosiy menyuga qaytish")
async def back_main(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(message.from_user.id, get_lang(message.from_user.id)))

catalog_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛍 Ayollar", callback_data="catimg_Ayollar kiyimlari"), InlineKeyboardButton(text="💄 Kosmetika", callback_data="catimg_Ayollar kosmetikasi")],
    [InlineKeyboardButton(text="👔 Erkaklar", callback_data="catimg_Erkaklar kiyimlari"), InlineKeyboardButton(text="👶 Bolalar", callback_data="catimg_Bolalar uchun")]
])

@dp.message(F.text == "🖼 Toifa rasmini o'zgartirish")
async def start_cat_img(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == ADMIN_ID:
        await message.answer("Qaysi toifaga rasm qo'shmoqchisiz?", reply_markup=catalog_menu)
        await state.set_state(AdminCatImage.category_name)

@dp.callback_query(AdminCatImage.category_name, F.data.startswith("catimg_"))
async def process_cat_name(callback: types.CallbackQuery, state: FSMContext):
    cat_name = callback.data.split("_")[1]
    await state.update_data(category_name=cat_name)
    await callback.message.answer(f"📸 <b>{cat_name}</b> uchun rasm yuboring:", parse_mode="HTML")
    await state.set_state(AdminCatImage.photo)

@dp.message(AdminCatImage.photo, F.photo)
async def process_cat_photo(message: types.Message, state: FSMContext):
    wait_msg = await message.answer("⏳ Yuklanmoqda...")
    data = await state.get_data()
    cat_name = data['category_name']
    photo_io = io.BytesIO()
    await bot.download(message.photo[-1], destination=photo_io)
    photo_io.seek(0)
    form = FormData()
    form.add_field('file', photo_io.read(), filename='image.jpg', content_type='image/jpeg')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://telegra.ph/upload', data=form) as resp:
                res = await resp.json()
                set_category_image(cat_name, "https://telegra.ph" + res[0]['src'])
        await wait_msg.edit_text(f"✅ Rasm o'zgardi.")
    except: await wait_msg.edit_text("❌ Xatolik.")
    await state.clear()

# ==========================================
#          API SERVER (WEB APP UCHUN)
# ==========================================
def set_cors():
    return {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"}

async def handle_options(request): return web.Response(headers=set_cors())

async def api_categories(request): return web.json_response(get_all_categories(), headers=set_cors())
async def api_products(request):
    cat = request.query.get('category')
    return web.json_response([{"id": p[0], "name": p[1], "price": p[2], "image_url": p[3]} for p in get_products_by_category(cat)], headers=set_cors())

async def api_send_code(request):
    uid, phone = request.query.get('uid'), request.query.get('phone')
    if not uid or not phone: return web.json_response({"error": "Xato"}, status=400, headers=set_cors())
    code = random.randint(1000, 9999) 
    try:
        await bot.send_message(chat_id=uid, text=f"FIRDAVS GROUP\nKod: <b>{code}</b>", parse_mode="HTML")
        return web.json_response({"success": True}, headers=set_cors())
    except: return web.json_response({"error": "Bot xatosi"}, status=500, headers=set_cors())

# --- YANGI: BAZAGA SAQLASH API ---
async def api_get_user(request):
    uid = request.query.get('uid')
    data = get_user_data(uid)
    if data: return web.json_response({"success": True, "data": data}, headers=set_cors())
    return web.json_response({"success": False}, headers=set_cors())

async def api_save_user(request):
    data = await request.json()
    save_user_data(data.get('uid'), data.get('name'), data.get('phone'), data.get('email'), data.get('dob'), data.get('gender'))
    return web.json_response({"success": True}, headers=set_cors())

async def api_save_coins(request):
    data = await request.json()
    update_user_coins(data.get('uid'), data.get('coins'))
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
    app.router.add_post('/api/save_coins', api_save_coins)
    
    # CORS OPTIONS ni o'tkazib yuborish uchun
    app.router.add_options('/api/save_user', handle_options)
    app.router.add_options('/api/save_coins', handle_options)
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
