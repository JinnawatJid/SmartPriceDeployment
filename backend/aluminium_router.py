# aluminium_router.py — SQLite Version (FE-safe)
from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd
from db_sqlite import get_conn

router = APIRouter(prefix="/aluminium", tags=["aluminium"])

# ============================
# SQLite TABLE NAMES
# ============================
ITEMS_TABLE = "Items_Test"
BRAND_TABLE = "Aluminium_Brand"
GROUP_TABLE = "Aluminium_Group"
SUBGROUP_TABLE = "Aluminium_SubGroup"
COLOR_TABLE = "Aluminium_Color"
THICKNESS_TABLE = "Aluminium_Thickness"


# ============================
# LOAD MAPPING TABLE (Brand/Group/…)
# ============================
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


# ============================
# PARSE ALUMINIUM SKU
# ============================
def parse_aluminium_sku(sku: str):
    s = (sku or "").strip().upper()

    # รูปแบบที่ถูกต้อง: A + 2 + 2 + 3 + 2 + 2 = 12 chars (อย่างน้อย)
    if not s.startswith("A") or len(s) < 12:
        return {
            "sku": s,
            "brand": None,
            "group": None,
            "subGroup": None,
            "color": None,
            "thickness": None,
        }

    try:
        brand = s[1:3]
        group = s[3:5]
        sub_group = s[5:8]
        color = s[8:10]
        thickness = s[10:12]
    except:
        brand = group = sub_group = color = thickness = None

    return {
        "sku": s,
        "brand": brand,
        "group": group,
        "subGroup": sub_group,
        "color": color,
        "thickness": thickness,
    }


# ============================
# LOAD ALUMINIUM ITEMS
# ============================
def load_aluminium_items():
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{ITEMS_TABLE}"', conn)
    conn.close()

    df.columns = [c.strip() for c in df.columns]

    # เฉพาะ SKU ขึ้นต้นด้วย A
    df = df[df["No."].astype(str).str.upper().str.startswith("A")].copy()

    
    print("=== [DEBUG] RAW Items_Test (head) ===")
    print(df.head(3))
    print("COLUMNS:", list(df.columns))

    if df.empty:
        return pd.DataFrame()

    df["SKU"] = df["No."].astype(str).str.upper().str.strip()

    parsed = df["SKU"].apply(parse_aluminium_sku)
    parsed_df = pd.json_normalize(parsed)

    out = pd.concat([df.reset_index(drop=True), parsed_df.reset_index(drop=True)], axis=1)

    # On-hand qty
    if "Inventory" in out.columns:
        out["onhand_qty"] = pd.to_numeric(out["Inventory"], errors="coerce").fillna(0).astype(int)
    else:
        out["onhand_qty"] = 0

    return out


# ============================
# FILTER ALUMINIUM
# ============================
def filter_aluminium(df, brand, group, subGroup, color, thickness):
    q = df.copy()

    if brand:
        q = q[q["brand"] == str(brand).zfill(2)]
    if group:
        q = q[q["group"] == str(group).zfill(2)]
    if subGroup:
        q = q[q["subGroup"] == str(subGroup).zfill(3)]
    if color:
        q = q[q["color"] == str(color).zfill(2)]
    if thickness:
        q = q[q["thickness"] == str(thickness).zfill(2)]

    return q


# ============================
# GET OPTIONS (เหมือนเดิม 100%)
# ============================
@router.get("/options")
@router.get("/master")
def aluminium_master(
    brand: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    thickness: Optional[str] = Query(None),
):
    df = load_aluminium_items()

    if df.empty:
        return {
            "source": "sqlite",
            "filters": {},
            "brands": [],
            "groups": [],
            "subGroups": [],
            "colors": [],
            "thickness": [],
        }

    q = filter_aluminium(df, brand, group, subGroup, color, thickness)

    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    subgroup_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)
    thickness_map = load_mapping(THICKNESS_TABLE)

    brands = sorted({x for x in q["brand"].dropna()})
    groups = sorted({x for x in q["group"].dropna()})
    subGroups = sorted({x for x in q["subGroup"].dropna()})
    colors = sorted({x for x in q["color"].dropna()})
    thicknesses = sorted({x for x in q["thickness"].dropna()})

    return {
        "source": "sqlite",
        "filters": {
            "brand": brand,
            "group": group,
            "subGroup": subGroup,
            "color": color,
            "thickness": thickness,
        },
        "brands": [{"code": b, "name": brand_map.get(b, b)} for b in brands],
        "groups": [{"code": g, "name": group_map.get(g, g)} for g in groups],
        "subGroups": [{"code": s, "name": subgroup_map.get(s, s)} for s in subGroups],
        "colors": [{"code": c, "name": color_map.get(c, c)} for c in colors],
        "thickness": [{"code": t, "name": thickness_map.get(t, t)} for t in thicknesses],
    }

@router.get("/items")
def aluminium_items(
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
    thickness: Optional[str] = None,
):
    df = load_aluminium_items()
    if df.empty:
        return []

    # apply filters
    df = filter_aluminium(df, brand, group, subGroup, color, thickness)

    # load mapping tables
    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    subgroup_map = load_mapping(SUBGROUP_TABLE)
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
            "subGroupName": subgroup_map.get(row.get("subGroup"), ""),

            "color": row.get("color"),
            "colorName": color_map.get(row.get("color"), ""),

            "thickness": row.get("thickness"),
            "inventory": row.get("onhand_qty", 0),

            "product_group": row.get("Product Group"),
            "product_sub_group": row.get("Product Sub Group"),
        })

    return items

