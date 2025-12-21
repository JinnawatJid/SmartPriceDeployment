# gypsum_router.py — SQLite Version + API ใหม่ + JSON เดิม
from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from typing import Optional
from db_sqlite import get_conn

router = APIRouter(prefix="/gypsum", tags=["gypsum"])

# === SQLite TABLES ===
ITEMS_TABLE = "Items_Test"
BRAND_TABLE = "Gypsum_Brand"
GROUP_TABLE = "Gypsum_Group"
SUBGROUP_TABLE = "Gypsum_SubGroup"
COLOR_TABLE = "Gypsum_Color"
THICKNESS_TABLE = "Gypsum_Thickness"


# -------------------------------------------------------
# โหลด mapping จาก SQLite
# -------------------------------------------------------
def load_mapping(table_name: str):
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    conn.close()

    # strip ช่องว่างในชื่อคอลัมน์
    df.columns = [c.strip() for c in df.columns]

    mapping = {}
    for _, row in df.iterrows():
        code = str(row["Code"]).strip()
        name = str(row["Name"]).strip()
        mapping[code] = name
    return mapping


def mapping_to_list(mapping: dict):
    return [{"code": k, "name": v} for k, v in mapping.items()]


# -------------------------------------------------------
# Load Gypsum items (จาก SQLite)
# -------------------------------------------------------
def load_gypsum_items():
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{ITEMS_TABLE}"', conn)
    conn.close()

    df.columns = [c.strip() for c in df.columns]

    # ยิปซัมขึ้นต้นด้วย Y
    df = df[df["No."].astype(str).str.upper().str.startswith("Y")].copy()

    if df.empty:
        return pd.DataFrame()

    df["SKU"] = df["No."].astype(str).str.upper().str.strip()

    # parse SKU
    parsed = df["SKU"].apply(parse_gypsum_sku)
    parsed_df = pd.json_normalize(parsed)

    out = pd.concat([df.reset_index(drop=True), parsed_df.reset_index(drop=True)], axis=1)

    # onhand = Inventory
    if "Inventory" in out.columns:
        out["onhand_qty"] = pd.to_numeric(out["Inventory"], errors="coerce").fillna(0).astype(int)
    else:
        out["onhand_qty"] = 0

    return out


# -------------------------------------------------------
# Parse Gypsum SKU
# -------------------------------------------------------
def parse_gypsum_sku(sku: str):
    s = (sku or "").strip().upper()

    if not s.startswith("Y") or len(s) < 18:
        return {
            "sku": s,
            "brand": None,
            "group": None,
            "subGroup": None,
            "color": None,
            "thickness": None,
            "sizeCode": None,
        }

    try:
        brand = s[1:3]
        group = s[3:5]
        sub_group = s[5:7]
        color = s[7:10]
        thickness = s[10:12]
        size_code = s[12:18]   # 6 digits size
    except:
        brand = group = sub_group = color = thickness = size_code = None

    return {
        "sku": s,
        "brand": brand,
        "group": group,
        "subGroup": sub_group,
        "color": color,
        "thickness": thickness,
        "sizeCode": size_code,
    }


# -------------------------------------------------------
# Filtering
# -------------------------------------------------------
def filter_gypsum(df, brand, group, subGroup, color, thickness):
    q = df.copy()
    if brand:
        q = q[q["brand"] == str(brand).zfill(2)]
    if group:
        q = q[q["group"] == str(group).zfill(2)]
    if subGroup:
        q = q[q["subGroup"] == str(subGroup).zfill(2)]
    if color:
        q = q[q["color"] == str(color).zfill(3)]
    if thickness:
        q = q[q["thickness"] == str(thickness).zfill(2)]
    return q


# -------------------------------------------------------
# GET /gypsum/master (ใช้ใน UI Picker)
# -------------------------------------------------------
@router.get("/master")
def gypsum_master(
    brand: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    thickness: Optional[str] = Query(None),
):
    df = load_gypsum_items()

    if df.empty:
        return {
            "brands": [],
            "groups": [],
            "subGroups": [],
            "colors": [],
            "thickness": [],
        }

    df_f = filter_gypsum(df, brand, group, subGroup, color, thickness)

    # load mapping
    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    sub_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)
    thick_map = load_mapping(THICKNESS_TABLE)

    # unique code lists
    brands = sorted({x for x in df_f["brand"].dropna()})
    groups = sorted({x for x in df_f["group"].dropna()})
    subGroups = sorted({x for x in df_f["subGroup"].dropna()})
    colors = sorted({x for x in df_f["color"].dropna()})
    thicknesses = sorted({x for x in df_f["thickness"].dropna()})

    return {
        "brands": [{"code": b, "name": brand_map.get(b, b)} for b in brands],
        "groups": [{"code": g, "name": group_map.get(g, g)} for g in groups],
        "subGroups": [{"code": s, "name": sub_map.get(s, s)} for s in subGroups],
        "colors": [{"code": c, "name": color_map.get(c, c)} for c in colors],
        "thickness": [{"code": t, "name": thick_map.get(t, t)} for t in thicknesses],
    }


# -------------------------------------------------------
# GET /gypsum/options (ใช้เหมือน master)
# -------------------------------------------------------
@router.get("/options")
def gypsum_options(
    brand: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    thickness: Optional[str] = Query(None),
):
    return gypsum_master(
        brand=brand,
        group=group,
        subGroup=subGroup,
        color=color,
        thickness=thickness,
    )

@router.get("/items")
def gypsum_items(
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
    thickness: Optional[str] = None,
):
    df = load_gypsum_items()
    if df.empty:
        return []

    df = filter_gypsum(df, brand, group, subGroup, color, thickness)

    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    sub_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)
    thick_map = load_mapping(THICKNESS_TABLE)

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

            "thickness": row.get("thickness"),
            "inventory": row.get("onhand_qty", 0)
        })

    return items
