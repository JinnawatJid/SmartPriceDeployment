# backend/sealant_router.py (SQLite Version)
from fastapi import APIRouter, Query
import pandas as pd
from typing import Optional
from db_sqlite import get_conn

router = APIRouter(prefix="/sealant", tags=["sealant"])

# === SQLite TABLES ===
ITEMS_TABLE = "Items_Test"
BRAND_TABLE = "Sealant_Brand"
GROUP_TABLE = "Sealant_Group"
SUBGROUP_TABLE = "Sealant_SubGroup"
COLOR_TABLE = "Sealant_Color"


# -------------------------------------------------------
# Load mapping table from SQLite
# -------------------------------------------------------
def load_mapping(table_name: str):
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    conn.close()

    df.columns = [c.strip() for c in df.columns]

    mapping = {}
    for _, row in df.iterrows():
        code = str(row["Code"]).strip()
        name = str(row["Name"]).strip()
        mapping[code] = name

    return mapping


# -------------------------------------------------------
# Load Sealant items (SKU เริ่มด้วย S)
# -------------------------------------------------------
def load_sealant_items():
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{ITEMS_TABLE}"', conn)
    conn.close()

    df.columns = [c.strip() for c in df.columns]

    df = df[df["No."].astype(str).str.upper().str.startswith("S")].copy()

    if df.empty:
        return pd.DataFrame()

    df["SKU"] = df["No."].astype(str).str.upper().str.strip()

    parsed = df["SKU"].apply(parse_sealant_sku)
    parsed_df = pd.json_normalize(parsed)

    out = pd.concat([df.reset_index(drop=True), parsed_df.reset_index(drop=True)], axis=1)

    if "Inventory" in out.columns:
        out["onhand_qty"] = pd.to_numeric(out["Inventory"], errors="coerce").fillna(0).astype(int)
    else:
        out["onhand_qty"] = 0

    return out


# -------------------------------------------------------
# Parse SKU Sealant (S...)
# -------------------------------------------------------
def parse_sealant_sku(sku: str):
    s = (sku or "").strip().upper()

    if not s.startswith("S") or len(s) < 10:
        return {
            "sku": s,
            "brand": None,
            "group": None,
            "subGroup": None,
            "color": None,
        }

    try:
        brand = s[1:3]
        group = s[3:5]
        sub_group = s[5:8]
        color = s[8:10]
    except:
        brand = group = sub_group = color = None

    return {
        "sku": s,
        "brand": brand,
        "group": group,
        "subGroup": sub_group,
        "color": color,
    }


# -------------------------------------------------------
# Filtering
# -------------------------------------------------------
def filter_sealant(df, brand, group, subGroup, color):
    q = df.copy()

    if brand:
        q = q[q["brand"] == str(brand).zfill(2)]
    if group:
        q = q[q["group"] == str(group).zfill(2)]
    if subGroup:
        q = q[q["subGroup"] == str(subGroup).zfill(3)]
    if color:
        q = q[q["color"] == str(color).zfill(2)]

    return q


# -------------------------------------------------------
# GET /api/sealant/master (สำหรับ Selector)
# -------------------------------------------------------
@router.get("/master")
def sealant_master(
    brand: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
):
    df = load_sealant_items()

    if df.empty:
        return {
            "brands": [],
            "groups": [],
            "subGroups": [],
            "colors": [],
        }

    q = filter_sealant(df, brand, group, subGroup, color)

    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    subgroup_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)

    brands = sorted({x for x in q["brand"].dropna()})
    groups = sorted({x for x in q["group"].dropna()})
    subGroups = sorted({x for x in q["subGroup"].dropna()})
    colors = sorted({x for x in q["color"].dropna()})

    return {
        "brands": [{"code": b, "name": brand_map.get(b, b)} for b in brands],
        "groups": [{"code": g, "name": group_map.get(g, g)} for g in groups],
        "subGroups": [{"code": s, "name": subgroup_map.get(s, s)} for s in subGroups],
        "colors": [{"code": c, "name": color_map.get(c, c)} for c in colors],
    }


# -------------------------------------------------------
# Alias: /api/sealant/options
# -------------------------------------------------------
@router.get("/options")
def sealant_options(
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
):
    return sealant_master(
        brand=brand,
        group=group,
        subGroup=subGroup,
        color=color,
    )

@router.get("/items")
def sealant_items(
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
):
    df = load_sealant_items()
    if df.empty:
        return []

    df = filter_sealant(df, brand, group, subGroup, color)

    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    sub_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)

    items = []
    for _, row in df.iterrows():
        items.append({
            "sku": row["SKU"],
            "name": row.get("Description", ""),

            "brand": row.get("brand"),
            "brandName": brand_map.get(row.get("brand"), ""),

            "group": row.get("group"),
            "groupName": group_map.get(row.get("group"), ""),

            "subGroup": row.get("subGroup"),
            "subGroupName": sub_map.get(row.get("subGroup"), ""),

            "color": row.get("color"),
            "colorName": color_map.get(row.get("color"), ""),

            "inventory": row.get("onhand_qty", 0),

            "product_group": row.get("Product Group"),
            "product_sub_group": row.get("Product Sub Group"),

        })

    return items
