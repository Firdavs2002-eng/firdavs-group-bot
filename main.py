import os
import io
import asyncio
import logging
import aiohttp
import random
import time
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiohttp import web, FormData
from database import init_db, get_products_by_category, add_product, set_user_lang, get_user_lang, set_category_image, get_all_categories

# --- SOZLAMALAR ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "7723220237" # Sizning ID raqamingiz

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- LUG'AT ---
LANGS = {
    'uz': {
        'welcome': "Assalomu alaykum, Firdavs!\n<b>FIRDAVS GROUP Super App</b>'ga xush kelibsiz! 🚀\n\nEndi bu yerda nafaqat do'kon, balki AI yordamchi va o'yinlar ham bor!",
        'shop': "🏪 Super App (Do'kon/O'yin/AI)", 'lang': "⚙️ Til", 'chat': "💬 Admin bilan aloqa"
    },
    'ru': {
        'welcome': "Здравствуйте, Фирдавс!\nДобро пожаловать в <b>FIRDAVS GROUP Super App</b>! 🚀\n\nТеперь здесь не только магазин, но и ИИ-помощник и игры!",
        'shop': "🏪 Super App (Магазин/Игры/ИИ)", 'lang': "⚙️ Язык", 'chat': "💬 Связь с админом"
    }
}

def get_main_menu(user_id, lang):
    ts = int(time.time())
    # Web App URL - hamma narsa bitta ssilka ichida
    web_app_url = f"https://firdavs2002-eng.github.io/firdavs-group-bot/?lang={lang}&uid={user_id}&v={ts}"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGS[lang]['shop'], web_app=WebAppInfo(url=web_app_url))],
            [KeyboardButton(text=LANGS[lang]['lang']), KeyboardButton(text=LANGS[lang]['chat'])]
        ], resize_keyboard=True
    )

# --- BOT HANDLERLARI ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    text = LANGS[lang]['welcome']
    await message.answer(text, reply_markup=get_main_menu(message.from_user.id, lang), parse_mode="HTML")

@dp.message(F.text == "⚙️ Til" or F.text == "⚙️ Язык")
async def change_lang(message: types.Message):
    menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")]
    ])
    await message.answer("Tilni tanlang / Выберите язык:", reply_markup=menu)

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, lang)
    await callback.message.delete()
    await callback.message.answer("Tayyor! / Готово!", reply_markup=get_main_menu(callback.from_user.id, lang))

# ==========================================
#        API SERVER (SUPER APP UCHUN)
# ==========================================
def set_cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

# 1. KATEGORIYALAR API
async def api_categories(request):
    return web.json_response(get_all_categories(), headers=set_cors_headers())

# 2. MAHSULOTLAR API
async def api_products(request):
    category = request.query.get('category')
    products = get_products_by_category(category)
    prod_list = [{"id": p[0], "name": p[1], "price": p[2], "image_url": p[5]} for p in products]
    return web.json_response(prod_list, headers=set_cors_headers())

# 3. AI CHAT API (Sun'iy intellekt javobi uchun yashirin yo'lak)
async def api_ai_chat(request):
    data = await request.json()
    user_msg = data.get('message', '').lower()
    
    # Oddiy AI mantiqi (Buni keyinchalik murakkablashtiramiz)
    responses = {
        "salom": "Assalomu alaykum! Men Firdavs Group sun'iy intellektiman. Sizga qanday yordam bera olaman?",
        "dastavka": "Bizda yetkazib berish Yandex va BTS orqali butun O'zbekiston bo'ylab amalga oshiriladi.",
        "pulingiz ko'pmi": "Mening boyligim — sizga yordam berishimda! 😊",
        "o'yin": "O'yin bo'limiga o'ting va tangalar yig'ib chegirmalar yuting!"
    }
    
    answer = responses.get(user_msg, "Kechirasiz, buni hali tushunmadim. Lekin o'rganyapman! Savolingizni administratorga yo'llashimni xohlaysizmi?")
    return web.json_response({"answer": answer}, headers=set_cors_headers())

# 4. GAME SAVE API (O'yin ballarini bazaga yozish uchun)
async def api_save_game(request):
    data = await request.json()
    uid = data.get('uid')
    coins = data.get('coins')
    # Kelajakda bazaga saqlash kodi shu yerda bo'ladi
    print(f"User {uid} yangi ball to'pladi: {coins}")
    return web.json_response({"status": "ok"}, headers=set_cors_headers())

async def handle(request):
    return web.Response(text="FIRDAVS GROUP Super App Server is Running!")

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/api/categories', api_categories)
    app.router.add_get('/api/products', api_products)
    app.router.add_post('/api/ai_chat', api_ai_chat) # AI uchun POST metod
    app.router.add_post('/api/save_game', api_save_game) # O'yin uchun POST metod
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
