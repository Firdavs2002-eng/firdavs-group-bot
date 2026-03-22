import sqlite3

def init_db():
    """Baza va jadvallarni yaratish"""
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    
    # Mahsulotlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            name TEXT,
            description TEXT,
            price INTEGER,
            image_url TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def get_products_by_category(category_name):
    """Tanlangan toifa bo'yicha mahsulotlarni bazadan olish"""
    conn = sqlite3.connect("firdavs_group.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM products WHERE category = ?", (category_name,))
    products = cursor.fetchall()
    conn.close()
    return products

# Dastlabki ishga tushirish uchun
if __name__ == "__main__":
    init_db()
    print("Ma'lumotlar bazasi tayyor!")