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
# Diqqat: Sizning ID raqamingiz qat'iy qilib belgilandi!
ADMIN_ID = "7723220237" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM HOLATLARI ---
class AdminCatImage(StatesGroup):
    category_name = State()
    photo = State()

# --- LUG'AT (DICTIONARY) ---
LANGS = {
    'uz': {
        'welcome': "Assalomu alaykum, {name}!\n<b>FIRDAVS GROUP</b> onlayn do'koniga xush kelibsiz!",
        'shop': "🏪 Do'kon", 'orders': "📦 Mening buyurtmalarim", 'lang': "⚙️ Tilni o'zgartirish", 'chat': "💬 Chat",
        'chat_info': "🧑‍💻 <b>Mijozlarni qo'llab-quvvatlash:</b>\nSavollaringiz bo'lsa, @admin ga yozing.",
        'orders_info': "Sizda hozircha faol buyurtmalar yo'q.", 'choose_lang': "🇺🇿 O'zingizga qulay tilni tanlang:"
    },
    'ru': {
        'welcome': "Здравствуйте, {name}!\nДобро пожаловать в магазин <b>FIRDAVS GROUP</b>!",
        'shop': "🏪 Магазин", 'orders': "📦 Мои заказы", 'lang': "⚙️ Изменить язык", 'chat': "💬 Чат",
        'chat_info': "🧑‍💻 <b>Служба поддержки:</b>\nЕсли у вас есть вопросы, напишите @admin.",
        'orders_info': "У вас пока нет активных заказов.", 'choose_lang': "🇷🇺 Выберите язык:"
    },
    'en': {
        'welcome': "Hello, {name}!\nWelcome to the <b>FIRDAVS GROUP</b> store!",
        'shop': "🏪 Shop", 'orders': "📦 My Orders", 'lang': "⚙️ Change Language", 'chat': "💬 Chat",
        'chat_info': "🧑‍💻 <b>Support:</b>\nIf you have questions, contact @admin.",
        'orders_info': "You have no active orders yet.", 'choose_lang': "🇬🇧 Choose your language:"
    }
}

# --- ANTI-CACHE VA DINAMIK URL ---
def get_main_menu(user_id, lang):
    ts = int(time.time())
    web_app_url = f"https://firdavs2002-eng.github.io/firdavs-group-bot/?lang={lang}&uid={user_id}&v={ts}"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGS[lang]['shop'], web_app=WebAppInfo(url=web_app_url))],
            [KeyboardButton(text=LANGS[lang]['orders'])],
            [KeyboardButton(text=LANGS[lang]['lang']), KeyboardButton(text=LANGS[lang]['chat'])]
        ], resize_keyboard=True
    )

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="🖼 Toifa rasmini o'zgartirish")],
        [KeyboardButton(text="⬅️ Asosiy menyuga qaytish")]
    ], resize_keyboard=True
)

catalog_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛍 Ayollar kiyimlari", callback_data="catimg_Ayollar kiyimlari")],
    [InlineKeyboardButton(text="👠 Ayollar oyoq kiyimlari", callback_data="catimg_Ayollar oyoq kiyimlari")],
    [InlineKeyboardButton(text="💄 Ayollar kosmetikasi", callback_data="catimg_Ayollar kosmetikasi")],
    [InlineKeyboardButton(text="👜 Ayollar taqinchoqlari", callback_data="catimg_Ayollar taqinchoqlari")],
    [InlineKeyboardButton(text="👔 Erkaklar kiyimlari", callback_data="catimg_Erkaklar kiyimlari")],
    [InlineKeyboardButton(text="👞 Erkaklar oyoq kiyimlari", callback_data="catimg_Erkaklar oyoq kiyimlari")],
    [InlineKeyboardButton(text="👶 Bolalar uchun", callback_data="catimg_Bolalar uchun")],
    [InlineKeyboardButton(text="📱 Telefon aksessuarlar", callback_data="catimg_Telefon aksessuarlar")]
])

lang_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz")],
    [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
    [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")]
])

def btn_filter(btn_key):
    return F.text.in_([LANGS['uz'][btn_key], LANGS['ru'][btn_key], LANGS['en'][btn_key]])

# --- BOT HANDLERLARI ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    text = LANGS[lang]['welcome'].format(name=message.from_user.first_name)
    await message.answer(text, reply_markup=get_main_menu(message.from_user.id, lang), parse_mode="HTML")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    # Bu yerda bot sizning raqamingizni qat'iy tekshiradi
    if str(message.from_user.id) == ADMIN_ID:
        await message.answer("👨‍💻 Admin panelga xush kelibsiz, Firdavs:", reply_markup=admin_menu)
    else:
        await message.answer("Sizda admin huquqi yo'q.")

@dp.message(F.text == "⬅️ Asosiy menyuga qaytish")
async def back_main(message: types.Message, state: FSMContext):
    await state.clear()
    lang = get_user_lang(message.from_user.id)
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(message.from_user.id, lang))

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
    await callback.message.answer(text, reply_markup=get_main_menu(callback.from_user.id, new_lang), parse_mode="HTML")

@dp.message(btn_filter('chat'))
async def chat_cmd(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(LANGS[lang]['chat_info'], parse_mode="HTML")

@dp.message(btn_filter('orders'))
async def orders_cmd(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(LANGS[lang]['orders_info'], parse_mode="HTML")

# --- KATEGORIYA RASMINI YUKLASH (TELEGRAPH API) ---
@dp.message(F.text == "🖼 Toifa rasmini o'zgartirish")
async def start_cat_img(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == ADMIN_ID:
        await message.answer("Qaysi toifaga rasm qo'ymoqchisiz?", reply_markup=catalog_menu)
        await state.set_state(AdminCatImage.category_name)

@dp.callback_query(AdminCatImage.category_name, F.data.startswith("catimg_"))
async def process_cat_name(callback: types.CallbackQuery, state: FSMContext):
    cat_name = callback.data.split("_")[1]
    await state.update_data(category_name=cat_name)
    await callback.message.answer(f"📸 <b>{cat_name}</b> uchun 1 ta kvadrat rasm yuboring:", parse_mode="HTML")
    await state.set_state(AdminCatImage.photo)
    await callback.answer()

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
                img_url = "https://telegra.ph" + res[0]['src']
        set_category_image(cat_name, img_url)
        await wait_msg.edit_text(f"✅ <b>{cat_name}</b> rasmi o'zgardi.", parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text("❌ Xatolik yuz berdi.")
    await state.clear()

# ==========================================
#        API SERVER (WEB APP UCHUN)
# ==========================================
def set_cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

async def api_categories(request):
    return web.json_response(get_all_categories(), headers=set_cors_headers())

async def api_products(request):
    category = request.query.get('category')
    products = get_products_by_category(category)
    prod_list = [{"id": p[0], "name": p[1], "price": p[2], "size": p[3], "color": p[4], "image_url": p[5]} for p in products]
    return web.json_response(prod_list, headers=set_cors_headers())

async def api_send_code(request):
    uid = request.query.get('uid')
    phone = request.query.get('phone')
    if not uid or not phone:
        return web.json_response({"error": "Parametrlar yetishmayapti"}, status=400, headers=set_cors_headers())

    code = random.randint(1000, 9999) 
    text = f"🔐 <b>FIRDAVS GROUP</b>\n\nSizning tasdiqlash kodingiz: <b>{code}</b>\nHech kimga bermang!"
    try:
        await bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
        return web.json_response({"success": True}, headers=set_cors_headers())
    except Exception as e:
        return web.json_response({"error": "Botga yuborib bo'lmadi."}, status=500, headers=set_cors_headers())

async def handle(request):
    return web.Response(text="FIRDAVS GROUP Web App Boti 24/7 ishlamoqda!")

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/api/categories', api_categories) 
    app.router.add_get('/api/products', api_products)
    app.router.add_get('/api/send_code', api_send_code) 
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    print("FIRDAVS GROUP API ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
