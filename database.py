import sqlite3

def init_db():
    """Baza va jadvallarni yaratish"""
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    
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
    conn.commit()
    conn.close()

def add_product(category, name, price, size, color, image_url):
    """Admin tomonidan mahsulot qo'shish"""
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (category, name, price, size, color, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (category, name, price, size, color, image_url))
    conn.commit()
    conn.close()

def get_products_by_category(category_name):
    """Kategoriya bo'yicha mahsulotlarni olish"""
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, size, color, image_url FROM products WHERE category = ?", (category_name,))
    products = cursor.fetchall()
    conn.close()
    return products

if __name__ == "__main__":
    init_db()
    print("Ma'lumotlar bazasi tayyor!")
    
