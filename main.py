import os
import io
import asyncio
import random
import time
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiohttp import web, FormData
from database import init_db, get_products_by_category, set_user_lang, get_user_lang, get_all_categories, save_user_data, get_user_data

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "7723220237"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

@dp.message(F.text.in_(["⚙️ Til", "⚙️ Язык", "⚙️ Language"]))
async def change_lang_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz")], [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")]])
    await message.answer(LANGS[lang]['choose_lang'], reply_markup=menu)

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang_handler(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, new_lang)
    await callback.message.delete()
    await callback.message.answer(LANGS[new_lang]['welcome'].format(name=callback.from_user.first_name), reply_markup=get_main_menu(callback.from_user.id, new_lang), parse_mode="HTML")

# --- AQLLI AI CHAT ---
@dp.message(F.text.in_(["💬 Chat (AI)", "💬 Чат (ИИ)"]))
async def chat_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    await message.answer(LANGS[lang]['ai_start'], parse_mode="HTML")

@dp.message(F.text)
async def ai_handler(message: types.Message):
    if message.text.startswith("🏪") or message.text.startswith("⚙️") or message.text.startswith("📦"): return
    # Oddiy AI simulyatsiyasi
    text = message.text.lower()
    reply = "Kechirasiz, men do'kon yordamchisiman. Mahsulotlar haqida so'rang yoki 'Do'konni ochish' tugmasini bosing."
    if "salom" in text: reply = "Assalomu alaykum! Firdavs Group do'konida qanday mahsulot qidiryapsiz?"
    elif "dastavka" in text or "yetkazib" in text: reply = "Bizda O'zbekiston bo'ylab BTS va Yandex orqali yetkazib berish mavjud."
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
