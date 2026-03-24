import sqlite3

DB_NAME = "firdavs_group.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. MAHSULOTLAR (O'zingizniki)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, name TEXT, price INTEGER,
            size TEXT, color TEXT, image_url TEXT
        )
    """)
    # 2. SAVAT (O'zingizniki)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    # 3. SEVIMLILAR (O'zingizniki)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, product_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    # 4. FOYDALANUVCHILAR (Til + Profil + Tangalar birlashtirildi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT, 
            phone TEXT, 
            email TEXT, 
            dob TEXT, 
            gender TEXT, 
            coins INTEGER DEFAULT 0,
            lang TEXT DEFAULT 'uz'
        )
    """)
    # 5. KATEGORIYALAR (O'zingizniki)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY,
            image_url TEXT
        )
    """)
    # 6. BUYURTMALAR (Yangi qo'shildi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id TEXT, 
            items TEXT, 
            total_price REAL, 
            delivery_address TEXT, 
            payment_method TEXT, 
            status TEXT DEFAULT 'Kutilmoqda', 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ==========================================
#    KATEGORIYALAR VA MAHSULOTLAR (Eskidek)
# ==========================================
def set_category_image(name, image_url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO categories (name, image_url) VALUES (?, ?)", (name, image_url))
    conn.commit()
    conn.close()

def get_all_categories():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, image_url FROM categories")
    cats = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "image_url": row[1]} for row in cats]

def add_product(category, name, price, size, color, image_url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (category, name, price, size, color, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (category, name, price, size, color, image_url))
    conn.commit()
    conn.close()

def get_products_by_category(category_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, size, color, image_url FROM products WHERE category = ?", (category_name,))
    products = cursor.fetchall()
    conn.close()
    return products

# ==========================================
#        SAVAT VA SEVIMLILAR (Eskidek)
# ==========================================
def add_to_cart(user_id, product_id):
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def toggle_wishlist(user_id, product_id):
    conn = sqlite3.connect(DB_NAME)
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

# ==========================================
#     FOYDALANUVCHILAR, PROFIL VA O'YIN 
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
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 'uz'

def save_user_data(user_id, name, phone, email, dob, gender):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO users (user_id, name, phone, email, dob, gender) 
                      VALUES (?, ?, ?, ?, ?, ?) 
                      ON CONFLICT(user_id) DO UPDATE SET 
                      name=excluded.name, phone=excluded.phone, email=excluded.email, 
                      dob=excluded.dob, gender=excluded.gender''', 
                   (user_id, name, phone, email, dob, gender))
    conn.commit()
    conn.close()

def update_user_coins(user_id, coins):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins=? WHERE user_id=?", (coins, user_id))
    conn.commit()
    conn.close()

# ==========================================
#             BUYURTMALAR (YANGI)
# ==========================================
def create_order(user_id, items, total_price, address, payment_method):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO orders (user_id, items, total_price, delivery_address, payment_method) 
                      VALUES (?, ?, ?, ?, ?)''', 
                   (user_id, items, total_price, address, payment_method))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return order_id

if __name__ == "__main__":
    init_db()
    
