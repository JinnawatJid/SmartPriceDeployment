# product_router.py — Unified Product Router (FE-safe)
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Callable
import pandas as pd
from config.db_sqlite import get_conn

router = APIRouter(prefix="/products", tags=["products"])

ITEMS_TABLE = "Items_Test"

# =====================================================
# SKU PARSERS (แยกตามประเภทสินค้า)
# =====================================================

def parse_aluminium(s):
    s = (s or "").upper().strip()
    if not s.startswith("A") or len(s) < 12:
        return {}
    return {
        "brand": s[1:3],
        "group": s[3:5],
        "subGroup": s[5:8],
        "color": s[8:10],
        "thickness": s[10:12],
    }

def parse_cline(s):
    s = (s or "").upper().strip()
    if not s.startswith("C") or len(s) < 12:
        return {}
    return {
        "brand": s[1:3],
        "group": s[3:5],
        "subGroup": s[5:8],
        "color": s[8:10],
        "thickness": s[10:12],
    }

def parse_accessories(s):
    s = (s or "").upper().strip()
    if not s.startswith("E") or len(s) < 11:
        return {}
    return {
        "brand": s[1:4],
        "group": s[4:6],
        "subGroup": s[6:8],
        "color": s[8:10],
        "character": s[10:11],
    }

def parse_sealant(s):
    s = (s or "").upper().strip()
    if not s.startswith("S") or len(s) < 10:
        return {}
    return {
        "brand": s[1:3],
        "group": s[3:5],
        "subGroup": s[5:8],
        "color": s[8:10],
    }

def parse_gypsum(s):
    s = (s or "").upper().strip()
    if not s.startswith("Y") or len(s) < 18:
        return {}
    return {
        "brand": s[1:3],
        "group": s[3:5],
        "subGroup": s[5:7],
        "color": s[7:10],
        "thickness": s[10:12],
    }

PARSERS: Dict[str, Callable] = {
    "A": parse_aluminium,
    "C": parse_cline,
    "E": parse_accessories,
    "S": parse_sealant,
    "Y": parse_gypsum,
}

# =====================================================
# LOAD ITEMS + PARSE SKU
# =====================================================

def load_items(category: str):
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{ITEMS_TABLE}"', conn)
    conn.close()

    df.columns = [c.strip() for c in df.columns]
    df["SKU"] = df["No."].astype(str).str.upper().str.strip()

    df = df[df["SKU"].str.startswith(category)].copy()
    if df.empty:
        return df

    parsed = df["SKU"].apply(PARSERS[category])
    parsed_df = pd.json_normalize(parsed)

    return pd.concat([df.reset_index(drop=True), parsed_df], axis=1)

# =====================================================
# FILTER (ใช้ร่วมทุกประเภท)
# =====================================================

def apply_filters(df, **filters):
    for k, v in filters.items():
        if v:
            df = df[df[k] == str(v).zfill(len(df[k].dropna().iloc[0]))]
    return df

# =====================================================
# MASTER (OPTIONS)
# =====================================================

@router.get("/master")
def product_master(
    category: str = Query(...),
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
    thickness: Optional[str] = None,
    character: Optional[str] = None,
):
    if category not in PARSERS:
        raise HTTPException(400, "Invalid category")

    df = load_items(category)
    if df.empty:
        return {}

    df = apply_filters(
        df,
        brand=brand,
        group=group,
        subGroup=subGroup,
        color=color,
        thickness=thickness,
        character=character,
    )

    def uniq(col):
        return sorted({x for x in df.get(col, []).dropna()})

    return {
        "brands": uniq("brand"),
        "groups": uniq("group"),
        "subGroups": uniq("subGroup"),
        "colors": uniq("color"),
        "thickness": uniq("thickness"),
        "characters": uniq("character"),
    }

# =====================================================
# ITEMS
# =====================================================

@router.get("/items")
def product_items(
    category: str = Query(...),
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
    thickness: Optional[str] = None,
    character: Optional[str] = None,
):
    if category not in PARSERS:
        raise HTTPException(400, "Invalid category")

    df = load_items(category)
    if df.empty:
        return []

    df = apply_filters(
        df,
        brand=brand,
        group=group,
        subGroup=subGroup,
        color=color,
        thickness=thickness,
        character=character,
    )

    return df.fillna("").to_dict(orient="records")
