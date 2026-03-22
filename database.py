import sqlite3

def init_db():
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    # Mahsulotlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            name TEXT,
            price INTEGER,
            size TEXT,
            color TEXT,
            image_url TEXT
        )
    """)
    # Savat jadvali (Wildberries mantiqi uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    conn.commit()
    conn.close()

def add_to_cart(user_id, product_id):
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    # Agar savatda bo'lsa sonini oshirish, bo'lmasa qo'shish
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

# Boshqa funksiyalar (add_product, get_products_by_category) o'z holicha qoladi
