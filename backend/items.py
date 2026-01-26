# items_mssql.py
from fastapi import APIRouter, Query, HTTPException
from services.sku_enricher import enrich_by_category
from config.db_mssql import get_mssql_conn

router = APIRouter(prefix="/items", tags=["items"])

TABLE_NAME = "Items_Test"


# ======================================================
# Helper: Convert DB row → API item (🔥 SHAPE เดิม)
# ======================================================
def row_to_item(row) -> dict:
    return {
        "sku": row.No,
        "sku2": row.No_2,
        "name": row.Description,
        "inventory": int(row.Inventory or 0),
        "unit": row.Base_Unit_of_Measure,
        "category": row.Inventory_Posting_Group,
        "isVariant": str(row.Variant_Mandatory_if_Exists).strip().upper() == "YES",
        "prices": {
            "R1": row.R1 or 0,
            "R2": row.R2 or 0,
            "W1": row.W1 or 0,
            "W2": row.W2 or 0,
        },
        "pkg_size": row.Package_Size or 1,
        "product_weight": row.Product_Weight or 0,
        "sqft_sheet": row.Sqft_Sheet,
        "product_group": row.Product_Group,
        "product_sub_group": row.Product_Sub_Group,
        "alternate_names": row.AlternateName,
    }


# ======================================================
# GET /items/categories/list  (เหมือนเดิม)
# ======================================================
@router.get("/categories/list")
def get_item_categories():
    conn = get_mssql_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            Inventory_Posting_Group AS name,
            COUNT(*) AS count
        FROM Items_Test
        GROUP BY Inventory_Posting_Group
    """)

    rows = cursor.fetchall()
    conn.close()

    return [{"name": r.name, "count": r.count} for r in rows]


# ======================================================
# ✅ NEW: GET /items/categories/{category}/list
# 👉 LIGHT LIST (เร็วมาก)
# ======================================================
@router.get("/categories/{category_name}/list")
def get_items_list_light(category_name: str):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    sql = """
        SELECT
            No          AS sku,
            No_2        AS sku2,
            Description AS name,
            Inventory   AS inventory
        FROM Items_Test
        WHERE Inventory_Posting_Group = ?
        ORDER BY No
    """

    cursor.execute(sql, category_name.upper())
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "sku": r.sku,
            "sku2": r.sku2,
            "name": r.name,
            "inventory": int(r.inventory or 0),
        }
        for r in rows
    ]


# ======================================================
# ❗ ของเดิม: GET /items/categories/{category}
# (ยังอยู่ แต่ช้า — แนะนำให้ FE เลิกใช้)
# ======================================================
@router.get("/categories/{category_name}")
def get_items_by_category(category_name: str):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    sql = f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE Inventory_Posting_Group = ?
    """

    cursor.execute(sql, category_name.upper())
    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        item = row_to_item(row)
        extra = enrich_by_category(item["category"], item["sku"]) or {}
        item.update(extra)
        items.append(item)

    return items


# ======================================================
# ✅ NEW: GET /items/{sku}
# 👉 FULL DETAIL + enrich (ตอนกด dropdown)
# ======================================================
@router.get("/{sku}")
def get_item_detail(sku: str):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    sql = f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE No = ?
    """

    cursor.execute(sql, sku)
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, "Item not found")

    item = row_to_item(row)

    # ⭐ enrich เฉพาะตอนนี้
    extra = enrich_by_category(item["category"], item["sku"]) or {}
    item.update(extra)

    return item


# ======================================================
# GET /items/search (ยังใช้ได้ แต่ LIMIT ไว้)
# ======================================================
@router.get("/search")
def full_text_search_items(q: str = Query(..., min_length=3)):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    q_like = f"%{q.strip()}%"

    sql = f"""
        SELECT TOP 50 *
        FROM {TABLE_NAME}
        WHERE
            No LIKE ?
            OR No_2 LIKE ?
            OR Description LIKE ?
            OR AlternateName LIKE ?
    """

    cursor.execute(sql, q_like, q_like, q_like, q_like)
    rows = cursor.fetchall()
    conn.close()

    return [row_to_item(r) for r in rows]
