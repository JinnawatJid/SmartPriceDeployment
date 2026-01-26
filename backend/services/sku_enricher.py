# services/sku_enricher.py
# --------------------------------------------------
# SKU Enrichment Layer (Single Source of Truth)
# Support: A / C / E / S / Y / G
# --------------------------------------------------

import pandas as pd
from functools import lru_cache
from config.db_sqlite import get_conn


# ==================================================
# Mapping Loader (cached)
# ==================================================

@lru_cache(maxsize=32)
def load_mapping(table_name: str):
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    conn.close()

    return {
        str(r["Code"]).strip(): str(r["Name"]).strip()
        for _, r in df.iterrows()
    }


# ==================================================
# Glass SubGroup loader (Type + Code → Name) (cached)
# ==================================================

@lru_cache(maxsize=8)
def load_glass_subgroup_mapping():
    conn = get_conn()
    df = pd.read_sql_query('SELECT Type, Code, Name FROM "Glass_SubGroup"', conn)
    conn.close()

    out = {}
    for _, r in df.iterrows():
        t = str(r["Type"]).strip()
        c = str(r["Code"]).strip()
        out[(t, c)] = str(r["Name"]).strip()
    return out


# ==================================================
# Accessories (E)
# SKU: EBBGGSSCCX
# ==================================================

def parse_accessories_sku(sku: str):
    sku = str(sku).strip()
    if not sku.startswith("E") or len(sku) < 8:
        return {}

    return {
        "brand": sku[1:4],
        "group": sku[4:6],
        "subGroup": sku[6:8],
        "color": sku[8:10] if len(sku) >= 10 else None,
        "character": sku[10] if len(sku) >= 11 else None,
    }


def enrich_accessories(sku: str):
    parsed = parse_accessories_sku(sku)
    if not parsed:
        return {}

    brand_map = load_mapping("Accessories_Brand")
    group_map = load_mapping("Accessories_Group")
    sub_map   = load_mapping("Accessories_SubGroup")

    return {
        **parsed,
        "brandName": brand_map.get(parsed.get("brand")),
        "groupName": group_map.get(parsed.get("group")),
        "subGroupName": sub_map.get(parsed.get("subGroup")),
    }


# ==================================================
# Aluminium (A)
# SKU: ABBGGSSSCCDD
# ==================================================

def parse_aluminium_sku(sku: str):
    sku = str(sku).strip()
    if not sku.startswith("A") or len(sku) < 12:
        return {}

    return {
        "brand": sku[1:3],
        "group": sku[3:5],
        "subGroup": sku[5:8],
        "color": sku[8:10],
        "thickness": sku[10:12],
    }


def enrich_aluminium(sku: str):
    parsed = parse_aluminium_sku(sku)
    if not parsed:
        return {}

    brand_map = load_mapping("Aluminium_Brand")
    group_map = load_mapping("Aluminium_Group")
    sub_map   = load_mapping("Aluminium_SubGroup")

    return {
        **parsed,
        "brandName": brand_map.get(parsed.get("brand")),
        "groupName": group_map.get(parsed.get("group")),
        "subGroupName": sub_map.get(parsed.get("subGroup")),
    }


# ==================================================
# C-Line (C)
# SKU: CBBGGSSSCCDD
# ==================================================

def parse_cline_sku(sku: str):
    sku = str(sku).strip()
    if not sku.startswith("C") or len(sku) < 12:
        return {}

    return {
        "brand": sku[1:3],
        "group": sku[3:5],
        "subGroup": sku[5:8],
        "color": sku[8:10],
        "thickness": sku[10:12],
    }


def enrich_cline(sku: str):
    parsed = parse_cline_sku(sku)
    if not parsed:
        return {}

    brand_map = load_mapping("C-Line_Brand")
    group_map = load_mapping("C-Line_Group")
    sub_map   = load_mapping("C-Line_SubGroup")

    return {
        **parsed,
        "brandName": brand_map.get(parsed.get("brand")),
        "groupName": group_map.get(parsed.get("group")),
        "subGroupName": sub_map.get(parsed.get("subGroup")),
    }


# ==================================================
# Sealant (S)
# SKU: SBBGGSSSCC
# ==================================================

def parse_sealant_sku(sku: str):
    sku = str(sku).strip()
    if not sku.startswith("S") or len(sku) < 10:
        return {}

    return {
        "brand": sku[1:3],
        "group": sku[3:5],
        "subGroup": sku[5:8],
        "color": sku[8:10],
    }


def enrich_sealant(sku: str):
    parsed = parse_sealant_sku(sku)
    if not parsed:
        return {}

    brand_map = load_mapping("Sealant_Brand")
    group_map = load_mapping("Sealant_Group")
    sub_map   = load_mapping("Sealant_SubGroup")

    return {
        **parsed,
        "brandName": brand_map.get(parsed.get("brand")),
        "groupName": group_map.get(parsed.get("group")),
        "subGroupName": sub_map.get(parsed.get("subGroup")),
    }


# ==================================================
# Gypsum (Y)
# SKU: YBBGGSSCCC DD ...
# ==================================================

def parse_gypsum_sku(sku: str):
    sku = str(sku).strip()
    if not sku.startswith("Y") or len(sku) < 12:
        return {}

    return {
        "brand": sku[1:3],
        "group": sku[3:5],
        "subGroup": sku[5:7],
        "color": sku[7:10],
        "thickness": sku[10:12],
    }


def enrich_gypsum(sku: str):
    parsed = parse_gypsum_sku(sku)
    if not parsed:
        return {}

    brand_map = load_mapping("Gypsum_Brand")
    group_map = load_mapping("Gypsum_Group")
    sub_map   = load_mapping("Gypsum_SubGroup")

    return {
        **parsed,
        "brandName": brand_map.get(parsed.get("brand")),
        "groupName": group_map.get(parsed.get("group")),
        "subGroupName": sub_map.get(parsed.get("subGroup")),
    }


# ==================================================
# Glass (G)
# SKU: G + Brand(2) + Type(2) + SubGroup(3) ...
# ==================================================

def parse_glass_sku(sku: str):
    sku = str(sku).strip()
    if not sku.startswith("G"):
        return {}

    # ทำให้ consistent กับ glass_router: brand/type/subGroup
    return {
        "brand": sku[1:3] if len(sku) >= 3 else None,
        "group": sku[3:5] if len(sku) >= 5 else None,      # group = type
        "subGroup": sku[5:8] if len(sku) >= 8 else None,   # 3 digits
    }


def enrich_glass(sku: str):
    parsed = parse_glass_sku(sku)
    if not parsed:
        return {}

    brand_map = load_mapping("Glass_Brand")
    group_map = load_mapping("Glass_Group")
    sub_map   = load_glass_subgroup_mapping()  # keyed by (type, code)

    t = parsed.get("group")
    c = parsed.get("subGroup")

    return {
        **parsed,
        "brandName": brand_map.get(parsed.get("brand")),
        "groupName": group_map.get(t),
        "subGroupName": sub_map.get((t, c)),
    }


# ==================================================
# Dispatcher (Public API)
# ==================================================

def enrich_by_category(category: str, sku: str) -> dict:
    """
    category: A / C / E / S / Y / G
    sku: raw SKU string
    """
    if not category or not sku:
        return {}

    category = str(category).upper()

    if category == "E":
        return enrich_accessories(sku)
    if category == "A":
        return enrich_aluminium(sku)
    if category == "C":
        return enrich_cline(sku)
    if category == "S":
        return enrich_sealant(sku)
    if category == "Y":
        return enrich_gypsum(sku)
    if category == "G":
        return enrich_glass(sku)

    return {}
