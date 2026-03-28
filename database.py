import sqlite3

DB_NAME = "firdavs_group.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. MAHSULOTLAR (Tavsif va ko'p rasmlar bilan)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, name TEXT, price INTEGER,
            description TEXT, images TEXT
        )
    """)
    # 2. SAVAT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, product_id INTEGER,
            quantity INTEGER DEFAULT 1
        )
    """)
    # 3. SEVIMLILAR
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, product_id INTEGER
        )
    """)
    # 4. FOYDALANUVCHILAR (3 ta til va iCloud profil uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT, phone TEXT, email TEXT, 
            dob TEXT, gender TEXT, lang TEXT DEFAULT 'uz',
            avatar TEXT
        )
    """)
    # 5. KATEGORIYALAR (8 ta asosiy toifa uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY, image_url TEXT
        )
    """)
    # 6. BUYURTMALAR (Xarita va to'lov turlari uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id TEXT, items TEXT, total_price REAL, 
            delivery_address TEXT, payment_method TEXT, 
            status TEXT DEFAULT 'Kutilmoqda', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ==========================================
#    KATEGORIYALAR VA MAHSULOTLAR
# ==========================================
def get_all_categories():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, image_url FROM categories")
    cats = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "image_url": row[1]} for row in cats]

def set_category_image(name, image_url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO categories (name, image_url) VALUES (?, ?)", (name, image_url))
    conn.commit()
    conn.close()

def get_products_by_category(category_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if category_name:
        cursor.execute("SELECT id, name, price, description, images FROM products WHERE category = ?", (category_name,))
    else:
        cursor.execute("SELECT id, name, price, description, images FROM products")
    res = cursor.fetchall()
    conn.close()
    return res

def add_product(category, name, price, description, images):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (category, name, price, description, images)
        VALUES (?, ?, ?, ?, ?)
    """, (category, name, price, description, images))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

# ==========================================
#     FOYDALANUVCHILAR VA TIL
# ==========================================
def set_user_lang(user_id, lang):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, lang) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang", (user_id, lang))
    conn.commit()
    conn.close()

def get_user_lang(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (str(user_id),))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 'uz'

def save_user_data(user_id, name, phone, email, dob, gender, avatar=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO users (user_id, name, phone, email, dob, gender, avatar) 
                      VALUES (?, ?, ?, ?, ?, ?, ?) 
                      ON CONFLICT(user_id) DO UPDATE SET 
                      name=excluded.name, phone=excluded.phone, email=excluded.email, 
                      dob=excluded.dob, gender=excluded.gender, avatar=excluded.avatar''', 
                   (str(user_id), name, phone, email, dob, gender, avatar))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, phone, email, dob, gender, lang, avatar FROM users WHERE user_id=?", (str(user_id),))
    res = cursor.fetchone()
    conn.close()
    if res:
        return {"name": res[0], "phone": res[1], "email": res[2], "dob": res[3], "gender": res[4], "lang": res[5], "avatar": res[6]}
    return None

if __name__ == "__main__":
    init_db()
