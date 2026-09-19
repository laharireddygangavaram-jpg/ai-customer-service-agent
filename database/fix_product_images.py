import sqlite3

DB_PATH = "database/customer_support.db"

# General image URLs based on product category
IMAGE_MAP = {
    "headphone": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
    "earbud": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df",
    "laptop": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853",
    "phone": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
    "smartphone": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
    "watch": "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
    "smart band": "https://images.unsplash.com/photo-1551816230-ef5deaed4a2d",
    "keyboard": "https://images.unsplash.com/photo-1587829741301-dc798b83add3",
    "mouse": "https://images.unsplash.com/photo-1527814050087-3793815479db",
    "speaker": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1",
    "camera": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32",
    "tablet": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0",
    "tv": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1",
    "charger": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0",
    "power bank": "https://images.unsplash.com/photo-1609592424690-72a9d7d9d5c1",

    # Kitchen
    "air fryer": "https://images.unsplash.com/photo-1648134700081-9b5f7f3f3f2a",
    "coffee maker": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085",
    "kettle": "https://images.unsplash.com/photo-1594213114663-d94db9b171f3",
    "mixer": "https://images.unsplash.com/photo-1570222094114-d054a817e56b",

    # Food
    "rice": "https://images.unsplash.com/photo-1586201375761-83865001e31c",
    "flour": "https://images.unsplash.com/photo-1509440159596-0249088772ff",
    "honey": "https://images.unsplash.com/photo-1471943311424-646960669fbc",
    "coffee": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085",
    "tea": "https://images.unsplash.com/photo-1544787219-7f47ccb76574",
    "dry fruits": "https://images.unsplash.com/photo-1599599810769-bcde5a160d32",
    "chocolate": "https://images.unsplash.com/photo-1549007994-cb92caebd54b",
    "cookies": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e",
    "oats": "https://images.unsplash.com/photo-1517673132405-a56a62b18caf",
    "peanut butter": "https://images.unsplash.com/photo-1599599810694-b5ac4dd3d4b7",

    # Clothes
    "t-shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab",
    "shirt": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf",
    "jeans": "https://images.unsplash.com/photo-1542272604-787c3835535d",
    "kurti": "https://images.unsplash.com/photo-1583391733956-6c78276477e2",
    "dress": "https://images.unsplash.com/photo-1595777457583-95e059d581b8",
    "saree": "https://images.unsplash.com/photo-1610030469983-98e550d6193c",
    "hoodie": "https://images.unsplash.com/photo-1556821840-3a63f95609a7",
    "jacket": "https://images.unsplash.com/photo-1551028719-00167b16eac5",
    "leggings": "https://images.unsplash.com/photo-1506629905607-d9c297d2e4e0",
    "pants": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80",

    # Shoes
    "sneakers": "https://images.unsplash.com/photo-1542291026-7eec264c27a1",
    "shoes": "https://images.unsplash.com/photo-1542291026-7eec264c27a1",
    "sandals": "https://images.unsplash.com/photo-1603487742131-4160ec999306",
    "heels": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2",
    "flip flops": "https://images.unsplash.com/photo-1603487742131-4160ec999306",

    # Beauty
    "face wash": "https://images.unsplash.com/photo-1556228578-8c89e6adf883",
    "moisturizer": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be",
    "lipstick": "https://images.unsplash.com/photo-1586495777744-4413f21062fa",
    "sunscreen": "https://images.unsplash.com/photo-1556228720-195a672e8a03",
    "serum": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be",
    "perfume": "https://images.unsplash.com/photo-1541643600914-78b084683601",
    "lotion": "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b",
    "makeup": "https://images.unsplash.com/photo-1512496015851-a90fb38ba796",

    # Bags
    "backpack": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62",
    "laptop bag": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62",
    "handbag": "https://images.unsplash.com/photo-1584917865442-de89df76afd3",
    "wallet": "https://images.unsplash.com/photo-1627123424574-724758594e93",

    # Other
    "sunglasses": "https://images.unsplash.com/photo-1511499767150-a48a237f0083",
    "bedsheet": "https://images.unsplash.com/photo-1616627561950-9f746e330187",
    "cushion": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2",
    "water bottle": "https://images.unsplash.com/photo-1602143407151-7111542de6e8",
    "clock": "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c",
}


def find_image(product_name):
    name = product_name.lower()

    # Check longer/more specific names first
    keywords = sorted(IMAGE_MAP.keys(), key=len, reverse=True)

    for keyword in keywords:
        if keyword in name:
            return IMAGE_MAP[keyword]

    # Generic image if no category matched
    return "https://images.unsplash.com/photo-1523275335684-37898b6baf30"


connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("""
    SELECT id, name, image_url
    FROM products
""")

products = cursor.fetchall()

updated = 0
already_good = 0

print("\n==============================================")
print("FIXING PRODUCT IMAGES")
print("==============================================")

for product_id, name, current_url in products:

    # Only fix broken/placeholder/missing images
    if (
        current_url is None
        or current_url == ""
        or "placeholder.com" in current_url
    ):

        new_url = find_image(name)

        cursor.execute("""
            UPDATE products
            SET image_url = ?
            WHERE id = ?
        """, (new_url, product_id))

        updated += 1

        print(f"UPDATED -> {name}")

    else:
        already_good += 1


connection.commit()

# Verify
cursor.execute("""
    SELECT COUNT(*)
    FROM products
    WHERE image_url IS NULL
       OR image_url = ''
       OR image_url LIKE '%placeholder.com%'
""")

remaining = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM products
""")

total = cursor.fetchone()[0]

connection.close()

print("\n==============================================")
print("IMAGE UPDATE COMPLETE")
print("==============================================")
print(f"Total products       : {total}")
print(f"Images updated       : {updated}")
print(f"Already working      : {already_good}")
print(f"Broken images left   : {remaining}")
print("==============================================")