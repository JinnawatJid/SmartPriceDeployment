# accessories_router.py — เวอร์ชัน SQLite + API ใหม่ + JSON เดิม
from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from db_sqlite import get_conn

router = APIRouter(prefix="/accessories", tags=["accessories"])

ITEMS_TABLE = "Items_Test"
BRAND_TABLE = "Accessories_Brand"
GROUP_TABLE = "Accessories_Group"
SUBGROUP_TABLE = "Accessories_SubGroup"
COLOR_TABLE = "Accessories_Color"
CHAR_TABLE = "Character"


# -------------------------------------------------------
# โหลด Mapping จาก SQLite
# -------------------------------------------------------
def load_mapping(table_name: str):
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    conn.close()

    mapping = {}
    for _, row in df.iterrows():
        code = str(row["Code"]).strip()
        name = str(row["Name"]).strip()
        mapping[code] = name
    return mapping

def filter_accessories(df, brand=None, group=None, subGroup=None, color=None, character=None):
    q = df.copy()

    if brand:
        q = q[q["brand"] == str(brand)]          # 3 digits
    if group:
        q = q[q["group"] == str(group)]          # 2 digits
    if subGroup:
        q = q[q["subGroup"] == str(subGroup)]    # 2 digits
    if color:
        q = q[q["color"] == str(color)]          # 2 digits
    if character:
        q = q[q["character"] == str(character)]  # 1 char

    return q

# -------------------------------------------------------
# โหลดข้อมูลสินค้าจาก Items_Test (เฉพาะ Accessories)
# -------------------------------------------------------
def load_accessories_items():
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{ITEMS_TABLE}"', conn)
    conn.close()

    # clean column names
    df.columns = [c.strip() for c in df.columns]

    # Accessories = SKU เริ่มต้นด้วย "E"
    df = df[df["No."].astype(str).str.startswith("E")].copy()

    return df


# -------------------------------------------------------
# parser SKU accessories: EBBGGSSCCX…
# -------------------------------------------------------
def parse_accessories_sku(sku: str):
    sku = sku.strip()
    if len(sku) < 8:
        return None

    brand = sku[1:4]          # 3 digits
    group = sku[4:6]          # 2 digits
    subGroup = sku[6:8]       # 2 digits
    color = sku[8:10] if len(sku) >= 10 else ""
    char_code = sku[10] if len(sku) >= 11 else ""

    return {
        "brand": brand,
        "group": group,
        "subGroup": subGroup,
        "color": color,
        "character": char_code,
    }



# -------------------------------------------------------
# /accessories/items → คืนสินค้าทั้งหมด (JSON เดิม)
# -------------------------------------------------------
@router.get("/items")
def get_accessories_items(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    character: str = None
):
    df = load_accessories_items()

    parsed = df["No."].astype(str).apply(parse_accessories_sku)
    parsed_df = pd.json_normalize(parsed)
    df = pd.concat([df.reset_index(drop=True), parsed_df], axis=1)
    
    df["inventory"] = (
        pd.to_numeric(df["Inventory"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    df = filter_accessories(df, brand, group, subGroup, color, character)

    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    sub_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)
    char_map = load_mapping(CHAR_TABLE)

    results = []

    
    for _, row in df.iterrows():
        results.append({
            "sku": row["No."],
            "name": row["Description"],
            "alternateName": row.get("AlternateName"),

            "brand": row["brand"],
            "brandName": brand_map.get(row["brand"], ""),

            "group": row["group"],
            "groupName": group_map.get(row["group"], ""),

            "subGroup": row["subGroup"],
            "subGroupName": sub_map.get(row["subGroup"], ""),

            "color": row["color"],
            "colorName": color_map.get(row["color"], ""),

            "character": row["character"],
            "characterName": char_map.get(row["character"], ""),

            "inventory": row["inventory"],

            "product_group": row.get("Product Group"),
            "product_sub_group": row.get("Product Sub Group"),

        })

    return results



# -------------------------------------------------------
# /accessories/master  → รวม brand/group/subgroup/color
# -------------------------------------------------------
@router.get("/master")
def accessories_master(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    character: str = None
):
    df = load_accessories_items()

    # parse SKU ก่อน
    parsed = df["No."].astype(str).apply(parse_accessories_sku)
    parsed_df = pd.json_normalize(parsed)
    df = pd.concat([df.reset_index(drop=True), parsed_df], axis=1)

    df = filter_accessories(df, brand, group, subGroup, color, character)

    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    sub_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)
    char_map = load_mapping(CHAR_TABLE)

    brands = sorted({x for x in df["brand"].dropna()})
    groups = sorted({x for x in df["group"].dropna()})
    subGroups = sorted({x for x in df["subGroup"].dropna()})
    colors = sorted({x for x in df["color"].dropna()})
    characters = sorted({x for x in df["character"].dropna()})

    return {
        "brands": [{"code": b, "name": brand_map.get(b, b)} for b in brands],
        "groups": [{"code": g, "name": group_map.get(g, g)} for g in groups],
        "subGroups": [{"code": s, "name": sub_map.get(s, s)} for s in subGroups],
        "colors": [{"code": c, "name": color_map.get(c, c)} for c in colors],
        "characters": [{"code": c, "name": char_map.get(c, c)} for c in characters],
    }


# -------------------------------------------------------
# /accessories/options → option สำหรับ UI dropdown
# -------------------------------------------------------
@router.get("/options")
def accessories_options(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    character: str = None
):
    return accessories_master(
        brand=brand,
        group=group,
        subGroup=subGroup,
        color=color,
        character=character
    )

