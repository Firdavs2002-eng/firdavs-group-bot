import sqlite3

DB_NAME = "firdavs_group.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # MAHSULOTLAR (Tavsif va ko'p rasmlar uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, name TEXT, price INTEGER,
            description TEXT, images TEXT
        )
    """)
    # SAVAT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, product_id INTEGER,
            quantity INTEGER DEFAULT 1
        )
    """)
    # SEVIMLILAR
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, product_id INTEGER
        )
    """)
    # FOYDALANUVCHILAR
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT, phone TEXT, email TEXT, 
            dob TEXT, gender TEXT, lang TEXT DEFAULT 'uz',
            avatar TEXT
        )
    """)
    # KATEGORIYALAR
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY, image_url TEXT
        )
    """)
    # BUYURTMALAR
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

if __name__ == "__main__":
    init_db()
