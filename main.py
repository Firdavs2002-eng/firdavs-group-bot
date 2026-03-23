import os
import asyncio
import logging
import aiohttp
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web
from database import init_db, get_user_lang, set_user_lang

# --- SOZLAMALAR ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "7723220237"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_menu(uid, lang):
    ts = int(time.time())
    url = f"https://firdavs2002-eng.github.io/firdavs-group-bot/?lang={lang}&uid={uid}&v={ts}"
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🏪 Super App", web_app=WebAppInfo(url=url))]], resize_keyboard=True)

@dp.message(Command("start"))
async def start(m: types.Message):
    lang = get_user_lang(m.from_user.id)
    await m.answer(f"Assalomu alaykum, Firdavs! 🚀\nSuper App'ga xush kelibsiz!", reply_markup=get_menu(m.from_user.id, lang))

# ==========================================
#        API SERVER
# ==========================================
async def api_ai_chat(request):
    data = await request.json()
    msg = data.get('message', '').lower()
    
    # AI mantiqi
    ans = "Kechirasiz, buni tushunmadim. Tez orada o'rganaman!"
    if "salom" in msg: ans = "Assalomu alaykum! Men Firdavs Group AI yordamchisiman."
    elif "dastavka" in msg: ans = "Bizda Yandex va BTS orqali yetkazib berish mavjud."
    elif "oyin" in msg: ans = "O'yin bo'limida ball yig'ib chegirmalar olishingiz mumkin!"

    return web.json_response({"answer": ans}, headers={"Access-Control-Allow-Origin": "*"})

async def handle(request): return web.Response(text="Server OK")

async def main():
    init_db()
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_post('/api/ai_chat', api_ai_chat)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
