import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiohttp import web
from database import init_db, get_products_by_category, add_product, set_user_lang, get_user_lang

# --- SOZLAMALAR ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- LUG'AT (DICTIONARY) TIZIMI ---
LANGS = {
    'uz': {
        'welcome': "Assalomu alaykum, {name}!\n<b>FIRDAVS GROUP</b> onlayn do'koniga xush kelibsiz!",
        'shop': "🏪 Do'kon",
        'orders': "📦 Mening buyurtmalarim",
        'lang': "⚙️ Tilni o'zgartirish",
        'chat': "💬 Chat",
        'chat_info': "🧑‍💻 <b>Mijozlarni qo'llab-quvvatlash xizmati:</b>\nSavollaringiz yoki takliflaringiz bo'lsa, bizning administratorga yozing.",
        'orders_info': "Sizda hozircha faol buyurtmalar yo'q.",
        'choose_lang': "🇺🇿 O'zingizga qulay tilni tanlang:"
    },
    'ru': {
        'welcome': "Здравствуйте, {name}!\nДобро пожаловать в онлайн-магазин <b>FIRDAVS GROUP</b>!",
        'shop': "🏪 Магазин",
        'orders': "📦 Мои заказы",
        'lang': "⚙️ Изменить язык",
        'chat': "💬 Чат",
        'chat_info': "🧑‍💻 <b>Служба поддержки:</b>\nЕсли у вас есть вопросы, напишите нашему администратору.",
        'orders_info': "У вас пока нет активных заказов.",
        'choose_lang': "🇷🇺 Выберите удобный для вас язык:"
    },
    'en': {
        'welcome': "Hello, {name}!\nWelcome to the <b>FIRDAVS GROUP</b> online store!",
        'shop': "🏪 Shop",
        'orders': "📦 My Orders",
        'lang': "⚙️ Change Language",
        'chat': "💬 Chat",
        'chat_info': "🧑‍💻 <b>Customer Support:</b>\nIf you have any questions, please contact our administrator.",
        'orders_info': "You have no active orders yet.",
        'choose_lang': "🇬🇧 Please choose your preferred language:"
    }
}

# Dinamik menyu yaratuvchi funksiya
def get_main_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGS[lang]['shop'], web_app=WebAppInfo(url="https://firdavs2002-eng.github.io/firdavs-group-bot/"))],
            [KeyboardButton(text=LANGS[lang]['orders'])],
            [KeyboardButton(text=LANGS[lang]['lang']), KeyboardButton(text=LANGS[lang]['chat'])]
        ], resize_keyboard=True
    )

# Til tanlash klaviaturasi
lang_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz")],
    [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
    [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")]
])

# Matnlar bo'yicha filtr (Qaysi tilda bosilganini aniqlash uchun)
def btn_filter(btn_key):
    return F.text.in_([LANGS['uz'][btn_key], LANGS['ru'][btn_key], LANGS['en'][btn_key]])

# ==========================================
#             BOT HANDLERLARI
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    text = LANGS[lang]['welcome'].format(name=message.from_user.first_name)
    await message.answer(text, reply_markup=get_main_menu(lang), parse_mode="HTML")

# --- TILNI O'ZGARTIRISH ---
@dp.message(btn_filter('lang'))
async def change_lang_cmd(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(LANGS[lang]['choose_lang'], reply_markup=lang_menu)

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang_handler(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, new_lang)
    
    await callback.message.delete()
    text = LANGS[new_lang]['welcome'].format(name=callback.from_user.first_name)
    await callback.message.answer(text, reply_markup=get_main_menu(new_lang), parse_mode="HTML")
    await callback.answer()

# --- CHAT (QO'LLAB-QUVVATLASH) ---
@dp.message(btn_filter('chat'))
async def chat_cmd(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(LANGS[lang]['chat_info'], parse_mode="HTML")

# --- BUYURTMALARIM ---
@dp.message(btn_filter('orders'))
async def orders_cmd(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(LANGS[lang]['orders_info'], parse_mode="HTML")

# ==========================================
#        RENDER SERVER (UXLAB QOLMASLIGI UCHUN)
# ==========================================
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

    print("FIRDAVS GROUP Pro Boti ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
