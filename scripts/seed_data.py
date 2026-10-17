from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PRODUCTS_PATH = DATA_DIR / "products.json"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8")) if PRODUCTS_PATH.exists() else []
    if products:
        print(f"Catalog already seeded with {len(products)} products in {PRODUCTS_PATH}")
        return

    sample_products = [
        {
            "id": "rice-basmati-5kg",
            "name": "Basmati Rice",
            "brand": "Shree",
            "category": "Rice",
            "pack_size": 5,
            "unit": "kg",
            "price": "245.00",
            "stock": 18,
            "status": "active",
            "aliases": ["basmati chawal", "rice"],
            "alternatives": [],
        },
        {
            "id": "atta-10kg",
            "name": "Whole Wheat Atta",
            "brand": "Aashirvaad",
            "category": "Atta",
            "pack_size": 10,
            "unit": "kg",
            "price": "330.00",
            "stock": 12,
            "status": "active",
            "aliases": ["atta", "flour", "chakki atta"],
            "alternatives": [],
        },
        {
            "id": "milk-toned-1l",
            "name": "Toned Milk",
            "brand": "Amul",
            "category": "Milk",
            "pack_size": 1,
            "unit": "litre",
            "price": "62.00",
            "stock": 30,
            "status": "active",
            "aliases": ["milk", "toned milk"],
            "alternatives": [],
        },
        {
            "id": "oil-groundnut-1l",
            "name": "Groundnut Oil",
            "brand": "Fortune",
            "category": "Cooking Oil",
            "pack_size": 1,
            "unit": "litre",
            "price": "170.00",
            "stock": 20,
            "status": "active",
            "aliases": ["groundnut oil", "oil"],
            "alternatives": [],
        },
        {
            "id": "sugar-1kg",
            "name": "Sugar",
            "brand": "Madhur",
            "category": "Sugar",
            "pack_size": 1,
            "unit": "kg",
            "price": "52.00",
            "stock": 25,
            "status": "active",
            "aliases": ["sugar", "cheeni"],
            "alternatives": [],
        },
        {
            "id": "tea-250g",
            "name": "Tea",
            "brand": "Brooke Bond",
            "category": "Tea",
            "pack_size": 250,
            "unit": "g",
            "price": "120.00",
            "stock": 16,
            "status": "active",
            "aliases": ["chai", "tea leaves"],
            "alternatives": [],
        },
        {
            "id": "biscuits-200g",
            "name": "Digestive Biscuits",
            "brand": "Parle",
            "category": "Biscuits",
            "pack_size": 200,
            "unit": "g",
            "price": "40.00",
            "stock": 22,
            "status": "active",
            "aliases": ["biscuits", "cookies"],
            "alternatives": [],
        },
        {
            "id": "soap-4pcs",
            "name": "Bathing Soap",
            "brand": "Dettol",
            "category": "Soap",
            "pack_size": 4,
            "unit": "pcs",
            "price": "160.00",
            "stock": 18,
            "status": "active",
            "aliases": ["soap", "bath soap"],
            "alternatives": [],
        },
        {
            "id": "detergent-1kg",
            "name": "Washing Powder",
            "brand": "Surf Excel",
            "category": "Detergent",
            "pack_size": 1,
            "unit": "kg",
            "price": "210.00",
            "stock": 14,
            "status": "active",
            "aliases": ["detergent", "washing powder"],
            "alternatives": [],
        },
        {
            "id": "dal-toor-1kg",
            "name": "Toor Dal",
            "brand": "Tata",
            "category": "Dal",
            "pack_size": 1,
            "unit": "kg",
            "price": "115.00",
            "stock": 17,
            "status": "active",
            "aliases": ["dal", "toor dal", "arhar dal"],
            "alternatives": [],
        },
        {
            "id": "salt-1kg",
            "name": "Iodized Salt",
            "brand": "Tata",
            "category": "Salt",
            "pack_size": 1,
            "unit": "kg",
            "price": "28.00",
            "stock": 30,
            "status": "active",
            "aliases": ["salt", "namak"],
            "alternatives": [],
        },
        {
            "id": "water-1l",
            "name": "Packaged Water",
            "brand": "Bisleri",
            "category": "Packaged Water",
            "pack_size": 1,
            "unit": "litre",
            "price": "30.00",
            "stock": 40,
            "status": "active",
            "aliases": ["water", "mineral water"],
            "alternatives": [],
        },
    ]
    PRODUCTS_PATH.write_text(json.dumps(sample_products, indent=2), encoding="utf-8")
    print(f"Seeded {len(sample_products)} products to {PRODUCTS_PATH}")


if __name__ == "__main__":
    main()
