from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
import os

load_dotenv()

products_data = [
    # NORMAL (5 products)
    {
        "name": "Hydrating Gentle Cleanser",
        "brand": "Glowtica Essentials",
        "category": "Cleanser",
        "description": "Daily non-foaming cleanser that maintains skin balance without stripping moisture.",
        "skin_type": "normal",
    },
    {
        "name": "Daily Balance Facial Moisturizer",
        "brand": "PureBotanics",
        "category": "Moisturizer",
        "description": "Lightweight lotion infused with green tea extract and ceramides.",
        "skin_type": "normal",
    },
    {
        "name": "Radiance Vitamin C Serum",
        "brand": "LumiGlow",
        "category": "Serum",
        "description": "Antioxidant boost to brighten complexion and protect against daily pollution.",
        "skin_type": "normal",
    },
    {
        "name": "Invisible Shield Sunscreen SPF 50",
        "brand": "SunGuard",
        "category": "Sunscreen",
        "description": "Broad-spectrum UV protection with an invisible, non-greasy finish.",
        "skin_type": "normal",
    },
    {
        "name": "Nourishing Night Cream",
        "brand": "VelvetSkin",
        "category": "Night Care",
        "description": "Overnight moisture replenishment with peptides and botanical extracts.",
        "skin_type": "normal",
    },

    # OILY (5 products)
    {
        "name": "Clarifying Salicylic Cleansing Gel",
        "brand": "DermaClear",
        "category": "Cleanser",
        "description": "Foaming BHA cleanser that unclogs pores and eliminates excess oil.",
        "skin_type": "oily",
    },
    {
        "name": "Oil-Free Water Gel Moisturizer",
        "brand": "AquaMatte",
        "category": "Moisturizer",
        "description": "Ultra-light hydration gel with hyaluronic acid that leaves a matte finish.",
        "skin_type": "oily",
    },
    {
        "name": "10% Niacinamide + Zinc Serum",
        "brand": "PureClarify",
        "category": "Serum",
        "description": "Minimizes visible pores and regulates sebum production.",
        "skin_type": "oily",
    },
    {
        "name": "Matte Finish Fluid Sunscreen SPF 50",
        "brand": "SunGuard",
        "category": "Sunscreen",
        "description": "Shine-control mineral sunscreen that absorbs excess surface oil.",
        "skin_type": "oily",
    },
    {
        "name": "Pore Tightening Toner",
        "brand": "PoreRefine",
        "category": "Toner",
        "description": "Witch hazel and tea tree toner that refines skin texture.",
        "skin_type": "oily",
    },

    # DRY (5 products)
    {
        "name": "Rich Cream Cleanser",
        "brand": "HydraDew",
        "category": "Cleanser",
        "description": "Soothing cream cleanser enriched with oat extracts and omega oils.",
        "skin_type": "dry",
    },
    {
        "name": "Barrier Restore Intense Cream",
        "brand": "CeramideRepair",
        "category": "Moisturizer",
        "description": "Deeply hydrating barrier cream enriched with 5 essential ceramides.",
        "skin_type": "dry",
    },
    {
        "name": "Hyaluronic Acid Intense Hydrator",
        "brand": "MoistureSurge",
        "category": "Serum",
        "description": "Multi-depth hydration serum that locks in moisture all day.",
        "skin_type": "dry",
    },
    {
        "name": "Nourishing Facial Oil",
        "brand": "FloraGlow",
        "category": "Oil",
        "description": "Blend of jojoba, squalane, and rosehip oils to soothe dry patches.",
        "skin_type": "dry",
    },
    {
        "name": "Dewy Glow Moisture Sunscreen SPF 50",
        "brand": "SunGuard",
        "category": "Sunscreen",
        "description": "Rich hydrating sunscreen that prevents sun-induced dryness.",
        "skin_type": "dry",
    },

    # COMBINATION (5 products)
    {
        "name": "Balancing Gel Cleanser",
        "brand": "Harmonize",
        "category": "Cleanser",
        "description": "pH-balanced gentle cleanser targeting dry cheeks and oily T-zones.",
        "skin_type": "combination",
    },
    {
        "name": "Adaptive Light Lotion",
        "brand": "DualCare",
        "category": "Moisturizer",
        "description": "Smart moisturizer that hydrates dry areas while controlling T-zone shine.",
        "skin_type": "combination",
    },
    {
        "name": "Gentle AHA/BHA Exfoliating Serum",
        "brand": "ClearBalance",
        "category": "Serum",
        "description": "Dual-action exfoliant for smooth texture and even tone.",
        "skin_type": "combination",
    },
    {
        "name": "Hydrating Essence Toner",
        "brand": "LumiGlow",
        "category": "Toner",
        "description": "Lightweight prep essence that balances skin moisture levels.",
        "skin_type": "combination",
    },
    {
        "name": "Weightless Daily UV Fluid SPF 50",
        "brand": "SunGuard",
        "category": "Sunscreen",
        "description": "Air-light sunscreen suitable for mixed skin zone needs.",
        "skin_type": "combination",
    },

    # SENSITIVE (5 products)
    {
        "name": "Calming Centella Foam Cleanser",
        "brand": "CicaSoothe",
        "category": "Cleanser",
        "description": "Ultra-gentle hypoallergenic cleanser enriched with Centella Asiatica.",
        "skin_type": "sensitive",
    },
    {
        "name": "Redness Relief Soothing Cream",
        "brand": "CalmDerm",
        "category": "Moisturizer",
        "description": "Fragrance-free soothing cream that calms irritation and flushing.",
        "skin_type": "sensitive",
    },
    {
        "name": "Soothing Panthenol & B5 Serum",
        "brand": "PureCalm",
        "category": "Serum",
        "description": "Concentrated B5 serum designed to strengthen reactive skin barriers.",
        "skin_type": "sensitive",
    },
    {
        "name": "100% Mineral Physical Sunscreen SPF 50",
        "brand": "SunGuard",
        "category": "Sunscreen",
        "description": "Gentle zinc oxide sunscreen ideal for sensitive, easily inflamed skin.",
        "skin_type": "sensitive",
    },
    {
        "name": "Overnight Recovery Mask",
        "brand": "CicaSoothe",
        "category": "Night Care",
        "description": "Fragrance-free barrier repair mask for irritated or stressed skin.",
        "skin_type": "sensitive",
    },
]


def seed_recommended_products():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI is missing in environment.")

    client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
    db = client["glowtica"]
    collection = db["recommended_products"]

    # Clear existing and insert 25 seed products
    collection.delete_many({})
    result = collection.insert_many(products_data)
    print(f"Successfully seeded {len(result.inserted_ids)} recommended products into MongoDB.")


if __name__ == "__main__":
    seed_recommended_products()
