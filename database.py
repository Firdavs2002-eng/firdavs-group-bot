import sqlite3

def init_db():
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    
    # 1. Mahsulotlar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, name TEXT, price INTEGER,
            size TEXT, color TEXT, image_url TEXT
        )
    """)
    # 2. Savat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    # 3. Sevimlilar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, product_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    # 4. Foydalanuvchilar (Tilni saqlash uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'uz'
        )
    """)
    conn.commit()
    conn.close()

# --- FOYDALANUVCHILAR VA TIL ---
def set_user_lang(user_id, lang):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, lang) VALUES (?, ?)", (user_id, lang))
    conn.commit()
    conn.close()

def get_user_lang(user_id):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 'uz'

# --- MAHSULOTLAR ---
def add_product(category, name, price, size, color, image_url):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (category, name, price, size, color, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (category, name, price, size, color, image_url))
    conn.commit()
    conn.close()

def get_products_by_category(category_name):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, size, color, image_url FROM products WHERE category = ?", (category_name,))
    products = cursor.fetchall()
    conn.close()
    return products

# --- SAVAT (KORZINA) ---
def add_to_cart(user_id, product_id):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    item = cursor.fetchone()
    if item:
        cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE id = ?", (item[0],))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
    conn.commit()
    conn.close()

def get_cart_items(user_id):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.name, p.price, c.quantity, p.id FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    """, (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def clear_cart(user_id):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- SEVIMLILAR (IZBRANNOYE) ---
def toggle_wishlist(user_id, product_id):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    if cursor.fetchone():
        cursor.execute("DELETE FROM wishlist WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        res = "o'chirildi"
    else:
        cursor.execute("INSERT INTO wishlist (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
        res = "qo'shildi"
    conn.commit()
    conn.close()
    return res

if __name__ == "__main__":
    init_db()
    
