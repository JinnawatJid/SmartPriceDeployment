# cline_router.py — SQLite Version + API ใหม่ + JSON เดิม (compatible กับ CLinePicker.jsx)

from fastapi import APIRouter
import pandas as pd
from config.db_sqlite import get_conn


router = APIRouter(prefix="/cline", tags=["cline"])

ITEMS_TABLE = "Items_Test"
BRAND_TABLE = "C-Line_Brand"
GROUP_TABLE = "C-Line_Group"
SUBGROUP_TABLE = "C-Line_SubGroup"
COLOR_TABLE = "C-Line_Color"
THICKNESS_TABLE = "C-Line_Thickness"


# -------------------------------------------------------
# โหลด Mapping จาก SQLite (Code → Name)
# -------------------------------------------------------
def load_mapping(table_name: str):
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    conn.close()

    # กันเคสคอลัมน์มี space เช่น " Code"
    df.columns = [c.strip() for c in df.columns]

    mapping = {}
    for _, row in df.iterrows():
        code = str(row["Code"]).strip()
        name = str(row["Name"]).strip()
        mapping[code] = name

    return mapping


def mapping_to_list(mapping: dict):
    """
    แปลง dict {code: name} → list[ {code, name}, ... ]
    เพื่อให้ React ใช้ .map ได้ตรง ๆ
    """
    return [{"code": k, "name": v} for k, v in mapping.items()]

def filter_cline(df, brand=None, group=None, subGroup=None, color=None, thickness=None):
    q = df.copy()

    if brand:
        q = q[q["brand"] == str(brand)]
    if group:
        q = q[q["group"] == str(group)]
    if subGroup:
        q = q[q["subGroup"] == str(subGroup)]
    if color:
        q = q[q["color"] == str(color)]
    if thickness:
        q = q[q["thickness"] == str(thickness)]

    return q



# -------------------------------------------------------
# โหลดสินค้า C-Line จาก Items_Test
# -------------------------------------------------------
def load_cline_items():
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{ITEMS_TABLE}"', conn)
    conn.close()

    df.columns = [c.strip() for c in df.columns]
    df = df[df["No."].astype(str).str.startswith("C")].copy()


    return df


# Parser SKU C-Line: CBBGGSSCCtt...

def parse_cline_sku(sku: str):
    sku = sku.strip()
    if len(sku) < 12:
        return None

    brand = sku[1:3]          # index 1–2 → 2 หลัก
    group = sku[3:5]          # index 3–4 → 2 หลัก  ⭐ แก้ตรงนี้
    sub_group = sku[5:8]      # index 5–7 → 3 หลัก  ⭐ แก้ตรงนี้
    color = sku[8:10]         # index 8–9 → 2 หลัก
    thickness = sku[10:12]    # index 10–11 → 2 หลัก

    return {
        "brand": brand,
        "group": group,
        "subGroup": sub_group,
        "color": color,
        "thickness": thickness,
    }



# -------------------------------------------------------
#  GET /cline/items  → รายการสินค้า C-Line (JSON key เดิม)
# -------------------------------------------------------
@router.get("/items")
def get_cline_items(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    thickness: str = None
):
    df = load_cline_items()
    if df.empty:
        return []

    parsed = df["No."].astype(str).apply(parse_cline_sku)
    parsed_df = pd.json_normalize(parsed)
    df = pd.concat([df.reset_index(drop=True), parsed_df], axis=1)

    # ⭐ ใช้ filter_cline ตรงนี้
    df = filter_cline(df, brand, group, subGroup, color, thickness)

    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    sub_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)
    thick_map = load_mapping(THICKNESS_TABLE)

    results = []
    for _, row in df.iterrows():
        sku = str(row["No."]).strip()

        results.append({
        # ===== identity =====
        "sku": sku,
        "name": str(row.get("Description", "")).strip(),

        # ===== SKU structure =====
        "brand": row["brand"],
        "group": row["group"],
        "subGroup": row["subGroup"],
        "color": row["color"],
        "thickness": row["thickness"],

        "brandName": brand_map.get(row["brand"], row["brand"]),
        "groupName": group_map.get(row["group"], row["group"]),
        "subGroupName": sub_map.get(row["subGroup"], row["subGroup"]),
        "colorName": color_map.get(row["color"], row["color"]),
        "thicknessName": thick_map.get(row["thickness"], row["thickness"]),

        # ===== stock / unit =====
        "inventory": int(row.get("Inventory", 0) or 0),
        "unit": row.get("Base Unit of Measure", "") or "",
        "pkg_size": int(row.get("Package Size", 1) or 1),

        # ===== weight =====
        "product_weight": float(row.get("Product Weight", 0) or 0),

        # ===== ⭐ business grouping (สำคัญ) =====
        "product_group": row.get("Product Group"),
        "product_sub_group": row.get("Product Sub Group"),
    })


    return results



# -------------------------------------------------------
#  GET /cline/master → ใช้ใน CLinePicker.jsx (ต้องคืน array)
# -------------------------------------------------------
@router.get("/master")
def cline_master(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    thickness: str = None
):
    df = load_cline_items()

    parsed = df["No."].astype(str).apply(parse_cline_sku)
    parsed_df = pd.json_normalize(parsed)
    df = pd.concat([df.reset_index(drop=True), parsed_df], axis=1)

    df = filter_cline(df, brand, group, subGroup, color, thickness)

    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    sub_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)
    thick_map = load_mapping(THICKNESS_TABLE)

    brands = sorted(set(df["brand"].dropna()))
    groups = sorted(set(df["group"].dropna()))
    subGroups = sorted(set(df["subGroup"].dropna()))
    colors = sorted(set(df["color"].dropna()))
    thicknesses = sorted(set(df["thickness"].dropna()))

    return {
        "brands": [{"code": b, "name": brand_map.get(b, b)} for b in brands],
        "groups": [{"code": g, "name": group_map.get(g, g)} for g in groups],
        "subGroups": [{"code": s, "name": sub_map.get(s, s)} for s in subGroups],
        "colors": [{"code": c, "name": color_map.get(c, c)} for c in colors],
        "thickness": [{"code": t, "name": thick_map.get(t, t)} for t in thicknesses]
    }



# -------------------------------------------------------
#  GET /cline/options → ถ้าอยากใช้แยกเป็น endpoint อื่นในอนาคต
# -------------------------------------------------------
@router.get("/options")
def cline_options():
    brand_map = load_mapping(BRAND_TABLE)
    group_map = load_mapping(GROUP_TABLE)
    sub_map = load_mapping(SUBGROUP_TABLE)
    color_map = load_mapping(COLOR_TABLE)
    thick_map = load_mapping(THICKNESS_TABLE)

    return {
        "brands": mapping_to_list(brand_map),
        "groups": mapping_to_list(group_map),
        "subGroups": mapping_to_list(sub_map),
        "colors": mapping_to_list(color_map),
        "thickness": mapping_to_list(thick_map),
    }
