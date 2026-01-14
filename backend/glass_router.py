# glass_router.py — FULL FIXED VERSION (SQLite + Correct TypeName Mapping)
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from db_sqlite import get_conn

router = APIRouter(prefix="/glass", tags=["glass"])


# ----------------------------------------
# Utility: Parse SKU
# ----------------------------------------
def parse_glass_sku(sku: str):
    """
    SKU Format:
    G + Brand(2) + Type(2) + SubGroup(3)
      + Color(2) + Thickness(2) + Width(3) + Height(3)
    """
    return {
        "brand": sku[1:3],
        "type": sku[3:5],
        "subGroup": sku[5:8],
        "color": sku[8:10],
        "thickness": sku[10:12],
        "width": int(sku[12:15]),
        "height": int(sku[15:18]),
    }


# ----------------------------------------
# GET /glass/list
# ----------------------------------------
@router.get("/list")
def get_glass_list(
    brand: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    thickness: Optional[str] = Query(None)
):
    conn = get_conn()
    cur = conn.cursor()

    # Load items
    cur.execute("""
        SELECT
            [No.],
            Description,
            Inventory,
            [Variant Mandatory if Exists],
            [Product Group],
            [Product Sub Group]
        FROM Items_Test
        WHERE [No.] LIKE 'G%'
        ORDER BY [No.]
    """)

    rows = cur.fetchall()

    # Load mapping tables
    cur.execute("SELECT Code, Name FROM Glass_Brand")
    brand_map = {str(c).zfill(2): n for c, n in cur.fetchall()}

    cur.execute("SELECT Code, Name FROM Glass_Color")
    color_map = {str(c).zfill(2): n for c, n in cur.fetchall()}

    cur.execute("SELECT Code, Name FROM Glass_Group")
    type_map = {str(c).zfill(2): n for c, n in cur.fetchall()}

    cur.execute("SELECT Type, Code, Name FROM Glass_SubGroup")
    subgroup_map = {(str(t).zfill(2), str(c).zfill(3)): n for t, c, n in cur.fetchall()}

    result = []

    for sku, desc, inv, vmand, product_group, product_sub_group in rows:

        parsed = parse_glass_sku(sku)

        # Filtering
        if brand and parsed["brand"] != brand:
            continue
        if type and parsed["type"] != type:
            continue
        if subGroup and parsed["subGroup"] != subGroup:
            continue
        if color and parsed["color"] != color:
            continue
        if thickness and parsed["thickness"] != thickness:
            continue

        is_variant = str(vmand or "").strip().upper() == "YES"

        # Mapping names
        brandName = brand_map.get(parsed["brand"], "")
        colorName = color_map.get(parsed["color"], "")
        typeName = type_map.get(parsed["type"], "")
        subGroupName = subgroup_map.get((parsed["type"], parsed["subGroup"]), "")

        result.append({
            "sku": sku,
            "description": desc,
            "isVariant": is_variant,
            "inventory": inv,

            "brand": parsed["brand"],
            "brandName": brandName,

            "type": parsed["type"],
            "typeName": typeName,

            "subGroup": parsed["subGroup"],
            "subGroupName": subGroupName,

            "color": parsed["color"],
            "colorName": colorName,

            "thickness": parsed["thickness"],

            "width": parsed["width"],
            "height": parsed["height"],

            # ⭐ เพิ่มสำหรับ Cross-sell
            "product_group": product_group,
            "product_sub_group": product_sub_group,


        })

    conn.close()
    return {"items": result}


# ----------------------------------------
# Request model for /glass/calc
# ----------------------------------------
class GlassCalcRequest(BaseModel):
    sku: str
    widthRaw: float
    heightRaw: float
    widthRounded: float
    heightRounded: float
    sqftRaw: float
    sqftRounded: float
    qty: int


# ----------------------------------------
# POST /glass/calc
# ----------------------------------------

@router.post("/calc")
def calc_glass(req: GlassCalcRequest):
    parsed = parse_glass_sku(req.sku)

    conn = get_conn()
    cur = conn.cursor()

    # Load names
    cur.execute("SELECT Name FROM Glass_Brand WHERE Code=?", (parsed["brand"],))
    brandName = (cur.fetchone() or [""])[0]

    cur.execute("SELECT Name FROM Glass_Color WHERE Code=?", (parsed["color"],))
    colorName = (cur.fetchone() or [""])[0]

    cur.execute("SELECT Code, Name FROM Glass_Group")
    type_map = {str(c).zfill(2): n for c, n in cur.fetchall()}

    cur.execute("""
        SELECT Name 
        FROM Glass_SubGroup
        WHERE Type=? AND Code=?
    """, (parsed["type"], parsed["subGroup"]))
    subGroupName = (cur.fetchone() or [""])[0]

    typeName = type_map.get(parsed["type"], "")

    conn.close()

    # --- เพิ่มส่วนโหลดราคา R2 จาก Items_Test ---
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT R2 
        FROM Items_Test
        WHERE [No.] = ?
    """, (req.sku,))
    row = cur.fetchone()
    price_r2 = row[0] if row and row[0] else 0   # default = 0
    conn.close()

    # คำนวณราคาต่อชิ้น (R2 × พื้นที่)
    total_price_r2 = price_r2 * req.sqftRounded


    return {
        "sku": req.sku,

        "brand": parsed["brand"],
        "brandName": brandName,

        "type": parsed["type"],
        "typeName": typeName,

        "subGroup": parsed["subGroup"],
        "subGroupName": subGroupName,

        "color": parsed["color"],
        "colorName": colorName,

        "thickness": parsed["thickness"],

        "width": req.widthRounded,
        "height": req.heightRounded,

        "sqft": req.sqftRounded,
        "qty": req.qty,
        "totalSqft": req.sqftRounded * req.qty,

        "priceR2": price_r2,
        "totalPriceR2": total_price_r2,


    }
