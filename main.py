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
from database import init_db, get_products_by_category, set_user_lang, get_user_lang, get_all_categories, set_category_image, add_product, delete_product

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "7723220237"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- HOLATLAR (FSM) ---
class AdminCatImage(StatesGroup):
    category_name = State()
    photo = State()

class AdminAddProduct(StatesGroup):
    category = State()
    name = State()
    price = State()
    description = State()
    photos = State()

LANGS = {
    'uz': {'welcome': "Assalomu alaykum!\n<b>FIRDAVS GROUP</b> do'koniga xush kelibsiz! 🚀", 'shop': "🏪 Do'konni ochish", 'orders': "📦 Buyurtmalarim", 'lang': "⚙️ Til", 'chat': "💬 Chat (AI)", 'choose_lang': "🇺🇿 Tilni tanlang:"},
    'ru': {'welcome': "Здравствуйте!\nДобро пожаловать в <b>FIRDAVS GROUP</b>! 🚀", 'shop': "🏪 Открыть магазин", 'orders': "📦 Мои заказы", 'lang': "⚙️ Язык", 'chat': "💬 Чат (ИИ)", 'choose_lang': "🇷🇺 Выберите язык:"},
    'en': {'welcome': "Hello!\nWelcome to <b>FIRDAVS GROUP</b>! 🚀", 'shop': "🏪 Open Shop", 'orders': "📦 My Orders", 'lang': "⚙️ Language", 'chat': "💬 Chat (AI)", 'choose_lang': "🇬🇧 Choose language:"}
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
    await message.answer(LANGS[lang]['welcome'], reply_markup=get_main_menu(message.from_user.id, lang), parse_mode="HTML")

# --- 3 TA TIL TUGMASI ---
@dp.message(F.text.in_(["⚙️ Til", "⚙️ Язык", "⚙️ Language"]))
async def change_lang_cmd(message: types.Message):
    menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz"), InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")], [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")]])
    await message.answer(LANGS[get_lang(message.from_user.id)]['choose_lang'], reply_markup=menu)

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang_handler(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, new_lang)
    await callback.message.delete()
    await callback.message.answer(LANGS[new_lang]['welcome'], reply_markup=get_main_menu(callback.from_user.id, new_lang), parse_mode="HTML")

# --- AI CHAT VA BOG'LANISH ---
@dp.message(F.text.in_(["💬 Chat (AI)", "💬 Чат (ИИ)"]))
async def chat_cmd(message: types.Message):
    await message.answer("🤖 <b>AI:</b> Assalomu alaykum! Men sun'iy intellekt yordamchisiman. Sizga nima qidirishga yordam beray?", parse_mode="HTML")

@dp.message(F.text)
async def ai_handler(message: types.Message):
    if message.text.startswith("🏪") or message.text.startswith("⚙️") or message.text.startswith("📦") or message.text.startswith("🛒") or message.text.startswith("🖼") or message.text.startswith("⬅️") or message.text.startswith("🗑"): return
    text = message.text.lower()
    reply = ""
    if "salom" in text: reply = "Assalomu alaykum! Firdavs Group do'konida qanday mahsulot qidiryapsiz?"
    elif "dastavka" in text or "yetkazib" in text: reply = "Bizda O'zbekiston bo'ylab Yandex va kuryerlarimiz orqali tezkor yetkazib berish mavjud."
    elif "narx" in text: reply = "Barcha narxlarni do'konimizga kirib, 'Katalog' bo'limidan ko'rishingiz mumkin."
    else:
        # AI javob topolmasa to'g'ridan-to'g'ri Admin ga yo'naltiradi
        reply = "Kechirasiz, savolingizga aniq javob topa olmadim. Murojaatingiz bo'yicha to'g'ridan-to'g'ri Adminimiz bilan bog'laning: @FIRDAVSI_RUZIBOY"
    await message.answer(f"🤖 <b>AI:</b> {reply}", parse_mode="HTML")

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if str(message.from_user.id) == ADMIN_ID:
        menu = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🛒 Mahsulot qo'shish"), KeyboardButton(text="🗑 Mahsulotni o'chirish")], 
            [KeyboardButton(text="🖼 Toifa rasmini o'zgartirish")],
            [KeyboardButton(text="⬅️ Asosiy menyuga qaytish")]
        ], resize_keyboard=True)
        await message.answer("👨‍💻 Boshqaruv paneli:", reply_markup=menu)

@dp.message(F.text == "⬅️ Asosiy menyuga qaytish")
async def back_main(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(message.from_user.id, get_lang(message.from_user.id)))

# 1. TOIFA RASMINI ALMASHTIRISH
admin_cat_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛍 Ayollar kiyimlari", callback_data="cat_Ayollar kiyimlari"), InlineKeyboardButton(text="👠 Oyoq kiyimi", callback_data="cat_Ayollar oyoq kiyimi")],
    [InlineKeyboardButton(text="💄 Kosmetika", callback_data="cat_Ayollar kosmetikasi"), InlineKeyboardButton(text="👜 Taqinchoqlar", callback_data="cat_Taqinchoqlar")],
    [InlineKeyboardButton(text="👔 Erkaklar kiyimlari", callback_data="cat_Erkaklar kiyimlari"), InlineKeyboardButton(text="👞 Erkaklar oyoq kiyimi", callback_data="cat_Erkaklar oyoq kiyimi")],
    [InlineKeyboardButton(text="👶 Bolalar uchun", callback_data="cat_Bolalar uchun"), InlineKeyboardButton(text="📱 Aksessuarlar", callback_data="cat_Aksessuarlar")]
])

@dp.message(F.text == "🖼 Toifa rasmini o'zgartirish")
async def start_cat_img(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == ADMIN_ID:
        await message.answer("Qaysi toifaga rasm qo'shmoqchisiz?", reply_markup=admin_cat_menu)
        await state.set_state(AdminCatImage.category_name)

@dp.callback_query(AdminCatImage.category_name, F.data.startswith("cat_"))
async def process_cat_name(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(category_name=callback.data.split("_")[1])
    await callback.message.answer("📸 Rasm yuboring:")
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
        await wait_msg.edit_text("✅ Rasm muvaffaqiyatli o'rnatildi.")
    except: await wait_msg.edit_text("❌ Xatolik yuz berdi.")
    await state.clear()

# 2. MAHSULOT QO'SHISH (Ko'p rasm va tavsif)
@dp.message(F.text == "🛒 Mahsulot qo'shish")
async def start_add_prod(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == ADMIN_ID:
        await message.answer("Yangi mahsulot qaysi toifaga tegishli?", reply_markup=admin_cat_menu)
        await state.set_state(AdminAddProduct.category)

@dp.callback_query(AdminAddProduct.category, F.data.startswith("cat_"))
async def add_prod_cat(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data.split("_")[1], photos=[])
    await callback.message.answer("📝 Mahsulot nomini yozing:")
    await state.set_state(AdminAddProduct.name)

@dp.message(AdminAddProduct.name, F.text)
async def add_prod_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("💰 Narxini faqat raqamda yozing (Masalan: 150000):")
    await state.set_state(AdminAddProduct.price)

@dp.message(AdminAddProduct.price, F.text)
async def add_prod_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, narxni faqat raqamlarda yozing:")
        return
    await state.update_data(price=int(message.text))
    await message.answer("📋 Mahsulot haqida chiroyli ta'rif (tavsif) yozing:")
    await state.set_state(AdminAddProduct.description)

@dp.message(AdminAddProduct.description, F.text)
async def add_prod_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("📸 Endi mahsulot rasmlarini (birma-bir) yuboring.\nBarcha rasmlarni yuborib bo'lgach, <b>TAYYOR</b> deb yozing.", parse_mode="HTML")
    await state.set_state(AdminAddProduct.photos)

@dp.message(AdminAddProduct.photos, F.photo)
async def add_prod_photos(message: types.Message, state: FSMContext):
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
                data['photos'].append("https://telegra.ph" + res[0]['src'])
                await state.update_data(photos=data['photos'])
                await message.answer(f"✅ Rasm qabul qilindi. Jami: {len(data['photos'])} ta.\nYana rasm yuboring yoki tugatish uchun <b>TAYYOR</b> deb yozing.", parse_mode="HTML")
    except: await message.answer("❌ Rasm yuklashda xato.")

@dp.message(AdminAddProduct.photos, F.text.lower() == "tayyor")
async def add_prod_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    images_str = "|".join(data['photos']) if data['photos'] else ""
    add_product(data['category'], data['name'], data['price'], data['description'], images_str)
    await message.answer(f"🎉 <b>{data['name']}</b> muvaffaqiyatli qo'shildi!", parse_mode="HTML")
    await state.clear()

# 3. MAHSULOT O'CHIRISH
@dp.message(F.text == "🗑 Mahsulotni o'chirish")
async def start_del_prod(message: types.Message):
    if str(message.from_user.id) == ADMIN_ID:
        prods = get_products_by_category(None)
        if not prods:
            await message.answer("Bazada mahsulot yo'q.")
            return
        btn_list = []
        for p in prods:
            btn_list.append([InlineKeyboardButton(text=f"❌ {p[1]}", callback_data=f"del_{p[0]}")])
        await message.answer("O'chirish uchun mahsulotni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btn_list))

@dp.callback_query(F.data.startswith("del_"))
async def del_prod_handler(callback: types.CallbackQuery):
    pid = callback.data.split("_")[1]
    delete_product(pid)
    await callback.message.edit_text("✅ Mahsulot muvaffaqiyatli o'chirildi!")


# ==========================================
#          API SERVER (WEB APP UCHUN)
# ==========================================
def set_cors(): return {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"}
async def handle_options(request): return web.Response(headers=set_cors())

async def api_categories(request): return web.json_response(get_all_categories(), headers=set_cors())

async def api_products(request):
    cat = request.query.get('category')
    prods = get_products_by_category(cat)
    res = []
    for p in prods:
        imgs = p[4].split('|') if p[4] else []
        res.append({"id": p[0], "name": p[1], "price": p[2], "description": p[3], "images": imgs})
    return web.json_response(res, headers=set_cors())

# 1. KOD YUBORISH API
async def api_send_code(request):
    uid, phone = request.query.get('uid'), request.query.get('phone')
    code = random.randint(1000, 9999) 
    try:
        await bot.send_message(chat_id=uid, text=f"🔐 <b>FIRDAVS GROUP</b>\nTasdiqlash kodi: <b>{code}</b>", parse_mode="HTML")
        return web.json_response({"success": True, "code": code}, headers=set_cors())
    except: return web.json_response({"error": "Bot xatosi"}, status=500, headers=set_cors())

# 2. ADMINGA BUYURTMA YUBORISH API
async def api_create_order(request):
    data = await request.json()
    text = f"🛍 <b>YANGI BUYURTMA (FIRDAVS GROUP)</b>\n\n"
    text += f"👤 Mijoz ID: <code>{data.get('uid', 'Noma\'lum')}</code>\n"
    text += f"📞 Telefon: {data.get('phone', 'Kiritilmagan')}\n"
    text += f"📦 Mahsulotlar: {data.get('items', 'Kiritilmagan')}\n"
    text += f"💰 Umumiy narx: <b>{data.get('total', '0')} UZS</b>\n"
    text += f"💳 To'lov turi: {data.get('payment', 'Naqd')}\n"
    text += f"📍 Manzil: {data.get('address', 'Kiritilmagan')}\n"
    
    if data.get('lat') and data.get('lng'):
        text += f"🗺 GPS: <a href='https://yandex.ru/maps/?pt={data.get('lng')},{data.get('lat')}&z=18&l=map'>Xaritada ko'rish</a>\n"
        
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML", disable_web_page_preview=True)
        return web.json_response({"success": True}, headers=set_cors())
    except: return web.json_response({"error": "Xato"}, status=500, headers=set_cors())
async def main():
    init_db()
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Firdavs Group API OK"))
    app.router.add_get('/api/categories', api_categories) 
    app.router.add_get('/api/products', api_products)
    app.router.add_get('/api/send_code', api_send_code) 
    
    app.router.add_post('/api/create_order', api_create_order)
    app.router.add_options('/api/create_order', handle_options)
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    
    # 🛑 MANA SHU KOD BARCHA CONFLICT XATOLARINI YO'Q QILADI:
    await bot.delete_webhook(drop_pending_updates=True)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
