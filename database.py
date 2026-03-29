import sqlite3

DB_NAME = "firdavs_group.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # MAHSULOTLAR
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, name TEXT, price INTEGER,
            description TEXT, images TEXT
        )
    """)
    # FOYDALANUVCHILAR
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            lang TEXT DEFAULT 'uz',
            phone TEXT
        )
    """)
    # KATEGORIYALAR
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY, image_url TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_product(category, name, price, description, images):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (category, name, price, description, images)
        VALUES (?, ?, ?, ?, ?)
    """, (category, name, price, description, images))
    conn.commit()
    conn.close()

def get_products_by_category(category_name=None):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Natijani lug'at (dict) shaklida olish uchun
    cursor = conn.cursor()
    if category_name and category_name != 'Barchasi >':
        cursor.execute("SELECT * FROM products WHERE category = ?", (category_name,))
    else:
        cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_product(product_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def set_user_lang(user_id, lang):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, lang) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang", (str(user_id), lang))
    conn.commit()
    conn.close()

def get_user_lang(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (str(user_id),))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 'uz'

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

if __name__ == "__main__":
    init_db()
