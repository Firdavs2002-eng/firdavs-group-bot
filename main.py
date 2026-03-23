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
from database import init_db, get_products_by_category, add_product, set_user_lang, get_user_lang, set_category_image, get_all_categories

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "7723220237"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AdminCatImage(StatesGroup):
    category_name = State()
    photo = State()

# --- TILLAR LUG'ATI ---
LANGS = {
    'uz': {
        'welcome': "Assalomu alaykum, {name}!\n<b>FIRDAVS GROUP</b> onlayn do'koniga xush kelibsiz!",
        'shop': "🏪 Do'kon", 'game': "🎮 O'yin (Clicker)", 'orders': "📦 Mening buyurtmalarim", 
        'lang': "⚙️ Tilni o'zgartirish", 'chat': "💬 Chat",
        'chat_info': "🧑‍💻 <b>Mijozlarni qo'llab-quvvatlash:</b>\nSavollaringiz bo'lsa, @admin ga yozing.",
        'orders_info': "Sizda hozircha faol buyurtmalar yo'q.", 'choose_lang': "🇺🇿 O'zingizga qulay tilni tanlang:"
    },
    'ru': {
        'welcome': "Здравствуйте, {name}!\nДобро пожаловать в магазин <b>FIRDAVS GROUP</b>!",
        'shop': "🏪 Магазин", 'game': "🎮 Игра (Clicker)", 'orders': "📦 Мои заказы", 
        'lang': "⚙️ Изменить язык", 'chat': "💬 Чат",
        'chat_info': "🧑‍💻 <b>Служба поддержки:</b>\nНапишите @admin.",
        'orders_info': "У вас пока нет активных заказов.", 'choose_lang': "🇷🇺 Выберите язык:"
    }
}

# --- ALOHIDA TUGMALAR (NINIOSHOP USLUBI) ---
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
        ], 
        resize_keyboard=True
    )

def get_lang(uid):
    lang = get_user_lang(uid)
    return lang if lang in LANGS else 'uz'

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_lang(message.from_user.id)
    text = LANGS[lang]['welcome'].format(name=message.from_user.first_name)
    await message.answer(text, reply_markup=get_main_menu(message.from_user.id, lang), parse_mode="HTML")

# --- TIL O'ZGARTIRISH ---
@dp.message(F.text.in_(["⚙️ Tilni o'zgartirish", "⚙️ Изменить язык"]))
async def change_lang_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")]
    ])
    await message.answer(LANGS[lang]['choose_lang'], reply_markup=menu)

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang_handler(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, new_lang)
    await callback.message.delete()
    text = LANGS[new_lang]['welcome'].format(name=callback.from_user.first_name)
    await callback.message.answer(text, reply_markup=get_main_menu(callback.from_user.id, new_lang), parse_mode="HTML")

# --- CHAT VA BUYURTMALAR ---
@dp.message(F.text.in_(["💬 Chat", "💬 Чат"]))
async def chat_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    await message.answer(LANGS[lang]['chat_info'], parse_mode="HTML")

@dp.message(F.text.in_(["📦 Mening buyurtmalarim", "📦 Мои заказы"]))
async def orders_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    await message.answer(LANGS[lang]['orders_info'], parse_mode="HTML")

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if str(message.from_user.id) == ADMIN_ID:
        menu = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🖼 Toifa rasmini o'zgartirish")],
            [KeyboardButton(text="⬅️ Asosiy menyuga qaytish")]
        ], resize_keyboard=True)
        await message.answer("👨‍💻 Admin panel:", reply_markup=menu)

@dp.message(F.text == "⬅️ Asosiy menyuga qaytish")
async def back_main(message: types.Message):
    lang = get_lang(message.from_user.id)
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(message.from_user.id, lang))

catalog_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛍 Ayollar kiyimi", callback_data="catimg_Ayollar kiyimlari"), InlineKeyboardButton(text="👠 Oyoq kiyim", callback_data="catimg_Ayollar oyoq kiyimlari")],
    [InlineKeyboardButton(text="💄 Kosmetika", callback_data="catimg_Ayollar kosmetikasi"), InlineKeyboardButton(text="👜 Taqinchoq", callback_data="catimg_Ayollar taqinchoqlari")],
    [InlineKeyboardButton(text="👔 Erkaklar kiyimi", callback_data="catimg_Erkaklar kiyimlari"), InlineKeyboardButton(text="👞 Oyoq kiyim", callback_data="catimg_Erkaklar oyoq kiyimlari")],
    [InlineKeyboardButton(text="👶 Bolalar uchun", callback_data="catimg_Bolalar uchun"), InlineKeyboardButton(text="📱 Aksessuar", callback_data="catimg_Telefon aksessuarlar")]
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
        await wait_msg.edit_text(f"✅ <b>{cat_name}</b> rasmi o'zgardi.", parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text("❌ Xatolik yuz berdi.")
    await state.clear()

# --- API SERVER ---
def set_cors():
    return {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET", "Access-Control-Allow-Headers": "Content-Type"}

async def api_categories(request): 
    return web.json_response(get_all_categories(), headers=set_cors())

async def api_products(request):
    cat = request.query.get('category')
    return web.json_response([{"id": p[0], "name": p[1], "price": p[2], "image_url": p[5]} for p in get_products_by_category(cat)], headers=set_cors())

async def api_send_code(request):
    uid = request.query.get('uid')
    phone = request.query.get('phone')
    if not uid or not phone: return web.json_response({"error": "Xato"}, status=400, headers=set_cors())
    code = random.randint(1000, 9999) 
    try:
        await bot.send_message(chat_id=uid, text=f"FIRDAVS GROUP\nTasdiqlash kodingiz: <b>{code}</b>", parse_mode="HTML")
        return web.json_response({"success": True}, headers=set_cors())
    except: return web.json_response({"error": "Bot xatosi"}, status=500, headers=set_cors())

async def main():
    init_db()
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Server ishlayapti!"))
    app.router.add_get('/api/categories', api_categories) 
    app.router.add_get('/api/products', api_products)
    app.router.add_get('/api/send_code', api_send_code) 
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
