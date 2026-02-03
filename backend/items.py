# items_mssql.py
from fastapi import APIRouter, Query, HTTPException
from services.sku_enricher import enrich_by_category, load_mapping
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
# 👉 LIGHT LIST (เร็วมาก) + รองรับ filter
# ======================================================
@router.get("/categories/{category_name}/list")
def get_items_list_light(
    category_name: str,
    limit: int = 10,
    offset: int = 0,
    # ⭐ เพิ่ม filter parameters
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    thickness: str = None,
    character: str = None,
    search: str = None,  # ⭐ เพิ่ม search parameter
):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    # ⭐ สร้าง WHERE clause สำหรับ filter
    where_clauses = ["Inventory_Posting_Group = ?"]
    params = [category_name.upper()]

    # ⭐ Filter by SKU pattern (Aluminium: ABBGGSSSCCTT)
    if category_name.upper() == "A":
        if brand:
            where_clauses.append("SUBSTRING(No, 2, 2) = ?")
            params.append(brand.zfill(2))
        if group:
            where_clauses.append("SUBSTRING(No, 4, 2) = ?")
            params.append(group.zfill(2))
        if subGroup:
            where_clauses.append("SUBSTRING(No, 6, 3) = ?")
            params.append(subGroup.zfill(3))
        if color:
            where_clauses.append("SUBSTRING(No, 9, 2) = ?")
            params.append(color.zfill(2))
        if thickness:
            where_clauses.append("SUBSTRING(No, 11, 2) = ?")
            params.append(thickness.zfill(2))

    # ⭐ Filter by SKU pattern (C-Line: CBBGGSSSCCTT)
    elif category_name.upper() == "C":
        if brand:
            where_clauses.append("SUBSTRING(No, 2, 2) = ?")
            params.append(brand.zfill(2))
        if group:
            where_clauses.append("SUBSTRING(No, 4, 2) = ?")
            params.append(group.zfill(2))
        if subGroup:
            where_clauses.append("SUBSTRING(No, 6, 3) = ?")
            params.append(subGroup.zfill(3))
        if color:
            where_clauses.append("SUBSTRING(No, 9, 2) = ?")
            params.append(color.zfill(2))
        if thickness:
            where_clauses.append("SUBSTRING(No, 11, 2) = ?")
            params.append(thickness.zfill(2))

    # ⭐ Filter by SKU pattern (Accessories: EBBBGGSSCCX)
    elif category_name.upper() == "E":
        if brand:
            where_clauses.append("SUBSTRING(No, 2, 3) = ?")
            params.append(brand.zfill(3))
        if group:
            where_clauses.append("SUBSTRING(No, 5, 2) = ?")
            params.append(group.zfill(2))
        if subGroup:
            where_clauses.append("SUBSTRING(No, 7, 2) = ?")
            params.append(subGroup.zfill(2))
        if color:
            where_clauses.append("SUBSTRING(No, 9, 2) = ?")
            params.append(color.zfill(2))
        if character:
            where_clauses.append("SUBSTRING(No, 11, 1) = ?")
            params.append(character)

    # ⭐ Filter by SKU pattern (Sealant: SBBGGGCC)
    elif category_name.upper() == "S":
        if brand:
            where_clauses.append("SUBSTRING(No, 2, 2) = ?")
            params.append(brand.zfill(2))
        if group:
            where_clauses.append("SUBSTRING(No, 4, 2) = ?")
            params.append(group.zfill(2))
        if subGroup:
            where_clauses.append("SUBSTRING(No, 6, 3) = ?")
            params.append(subGroup.zfill(3))
        if color:
            where_clauses.append("SUBSTRING(No, 9, 2) = ?")
            params.append(color.zfill(2))

    # ⭐ Filter by SKU pattern (Gypsum: YBBGGSCCCTT...)
    elif category_name.upper() == "Y":
        if brand:
            where_clauses.append("SUBSTRING(No, 2, 2) = ?")
            params.append(brand.zfill(2))
        if group:
            where_clauses.append("SUBSTRING(No, 4, 2) = ?")
            params.append(group.zfill(2))
        if subGroup:
            where_clauses.append("SUBSTRING(No, 6, 2) = ?")
            params.append(subGroup.zfill(2))
        if color:
            where_clauses.append("SUBSTRING(No, 8, 3) = ?")
            params.append(color.zfill(3))
        if thickness:
            where_clauses.append("SUBSTRING(No, 11, 2) = ?")
            params.append(thickness.zfill(2))

    # ⭐ เพิ่ม search filter (ค้นหาใน SKU, SKU2, Description, AlternateName)
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        where_clauses.append("(No LIKE ? OR No_2 LIKE ? OR Description LIKE ? OR AlternateName LIKE ?)")
        params.extend([search_term, search_term, search_term, search_term])

    where_sql = " AND ".join(where_clauses)

    # ⭐ นับจำนวนทั้งหมดตาม filter
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM Items_Test
        WHERE {where_sql}
    """
    cursor.execute(count_sql, *params)
    total = cursor.fetchone().total

    # ⭐ ดึงข้อมูลตาม limit/offset + filter
    sql = f"""
        SELECT
            No            AS sku,
            No_2          AS sku2,
            Description   AS name,
            Inventory     AS inventory,
            Base_Unit_of_Measure AS unit,
            Product_Group AS product_group,
            Product_Sub_Group AS product_sub_group,
            AlternateName AS alternate_names
        FROM Items_Test
        WHERE {where_sql}
        ORDER BY No
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
    """

    cursor.execute(sql, *params, offset, limit)
    rows = cursor.fetchall()
    conn.close()

    return {
        "items": [
            {
                "sku": r.sku,
                "SKU": r.sku,  # ⭐ เพิ่ม uppercase version สำหรับ compatibility
                "sku2": r.sku2,
                "name": r.name,
                "inventory": int(r.inventory or 0),
                "unit": r.unit,
                "product_group": r.product_group,
                "product_sub_group": r.product_sub_group,
                "alternate_names": r.alternate_names,
            }
            for r in rows
        ],
        "limit": limit,
        "offset": offset,
        "count": len(rows),
        "total": total,
    }



# ======================================================
# ✅ NEW: GET /items/{sku}
# 👉 FULL DETAIL + enrich (ตอนกด dropdown)
# 👉 รองรับทั้ง SKU (No) และ SKU2 (No_2)
# ======================================================
@router.get("/{sku}")
def get_item_detail(sku: str):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    # ⭐ ลองหาจาก No ก่อน
    sql = f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE No = ?
    """

    cursor.execute(sql, sku)
    row = cursor.fetchone()
    
    # ⭐ ถ้าไม่เจอ ลองหาจาก No_2
    if not row:
        sql = f"""
            SELECT *
            FROM {TABLE_NAME}
            WHERE No_2 = ?
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
    extra = enrich_by_category(item["category"], item["sku"]) or {}
    item.update(extra)

    return item


# ======================================================
# ✅ NEW: GET /items/related/{sku}
# 👉 ดึงสินค้าที่อยู่ใน Product Group เดียวกัน (LIGHT VERSION - เร็ว)
# ======================================================
@router.get("/related/{sku}")
def get_related_items(sku: str, limit: int = 50):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    # ⭐ หา product_group ของ SKU นี้ก่อน (เร็ว)
    sql = f"""
        SELECT Product_Group
        FROM {TABLE_NAME}
        WHERE No = ? OR No_2 = ?
    """
    cursor.execute(sql, sku, sku)
    row = cursor.fetchone()

    if not row or not row.Product_Group:
        conn.close()
        return {"items": [], "total": 0}

    product_group = row.Product_Group

    # ⭐ ดึงสินค้าใน Product Group เดียวกัน (LIGHT - เฉพาะข้อมูลที่จำเป็น)
    sql = f"""
        SELECT TOP {limit}
            No            AS sku,
            No_2          AS sku2,
            Description   AS name,
            Inventory     AS inventory,
            Base_Unit_of_Measure AS unit,
            Product_Group AS product_group,
            Product_Sub_Group AS product_sub_group
        FROM {TABLE_NAME}
        WHERE Product_Group = ?
          AND No != ?
          AND (No_2 IS NULL OR No_2 != ?)
        ORDER BY No
    """
    cursor.execute(sql, product_group, sku, sku)
    rows = cursor.fetchall()
    conn.close()

    return {
        "items": [
            {
                "sku": r.sku,
                "SKU": r.sku,
                "sku2": r.sku2,
                "name": r.name,
                "inventory": int(r.inventory or 0),
                "unit": r.unit,
                "product_group": r.product_group,
                "product_sub_group": r.product_sub_group,
            }
            for r in rows
        ],
        "total": len(rows),
        "product_group": product_group,
    }


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


# ======================================================
# ✅ NEW: GET /items/categories/{category}/filter-options
# 👉 ดึง filter options ที่ปรับตาม filter ที่เลือกแล้ว (cascading)
# ======================================================
@router.get("/categories/{category_name}/filter-options")
def get_filter_options(
    category_name: str,
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    thickness: str = None,
    character: str = None,
):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    # ⭐ สร้าง WHERE clause สำหรับ filter (เหมือนกับ list endpoint)
    where_clauses = ["Inventory_Posting_Group = ?"]
    params = [category_name.upper()]

    # Helper function สำหรับเพิ่ม filter
    def add_filter(field_slice, value, pad_len):
        if value:
            where_clauses.append(f"SUBSTRING(No, {field_slice[0]}, {field_slice[1]}) = ?")
            params.append(value.zfill(pad_len))

    # ⭐ Filter by SKU pattern ตาม category
    if category_name.upper() == "A":
        add_filter((2, 2), brand, 2)
        add_filter((4, 2), group, 2)
        add_filter((6, 3), subGroup, 3)
        add_filter((9, 2), color, 2)
        add_filter((11, 2), thickness, 2)
        
        # Define extraction for each field
        field_extracts = {
            "brand": "SUBSTRING(No, 2, 2)",
            "group": "SUBSTRING(No, 4, 2)",
            "subGroup": "SUBSTRING(No, 6, 3)",
            "color": "SUBSTRING(No, 9, 2)",
            "thickness": "SUBSTRING(No, 11, 2)",
        }

    elif category_name.upper() == "C":
        add_filter((2, 2), brand, 2)
        add_filter((4, 2), group, 2)
        add_filter((6, 3), subGroup, 3)
        add_filter((9, 2), color, 2)
        add_filter((11, 2), thickness, 2)
        
        field_extracts = {
            "brand": "SUBSTRING(No, 2, 2)",
            "group": "SUBSTRING(No, 4, 2)",
            "subGroup": "SUBSTRING(No, 6, 3)",
            "color": "SUBSTRING(No, 9, 2)",
            "thickness": "SUBSTRING(No, 11, 2)",
        }

    elif category_name.upper() == "E":
        add_filter((2, 3), brand, 3)
        add_filter((5, 2), group, 2)
        add_filter((7, 2), subGroup, 2)
        add_filter((9, 2), color, 2)
        if character:
            where_clauses.append("SUBSTRING(No, 11, 1) = ?")
            params.append(character)
        
        field_extracts = {
            "brand": "SUBSTRING(No, 2, 3)",
            "group": "SUBSTRING(No, 5, 2)",
            "subGroup": "SUBSTRING(No, 7, 2)",
            "color": "SUBSTRING(No, 9, 2)",
            "character": "SUBSTRING(No, 11, 1)",
        }

    elif category_name.upper() == "S":
        add_filter((2, 2), brand, 2)
        add_filter((4, 2), group, 2)
        add_filter((6, 3), subGroup, 3)
        add_filter((9, 2), color, 2)
        
        field_extracts = {
            "brand": "SUBSTRING(No, 2, 2)",
            "group": "SUBSTRING(No, 4, 2)",
            "subGroup": "SUBSTRING(No, 6, 3)",
            "color": "SUBSTRING(No, 9, 2)",
        }

    elif category_name.upper() == "Y":
        add_filter((2, 2), brand, 2)
        add_filter((4, 2), group, 2)
        add_filter((6, 2), subGroup, 2)
        add_filter((8, 3), color, 3)
        add_filter((11, 2), thickness, 2)
        
        field_extracts = {
            "brand": "SUBSTRING(No, 2, 2)",
            "group": "SUBSTRING(No, 4, 2)",
            "subGroup": "SUBSTRING(No, 6, 2)",
            "color": "SUBSTRING(No, 8, 3)",
            "thickness": "SUBSTRING(No, 11, 2)",
        }
    else:
        return {}

    where_sql = " AND ".join(where_clauses)

    # ⭐ โหลด mapping tables
    mapping_tables = {
        "A": {
            "brand": "Aluminium_Brand",
            "group": "Aluminium_Group",
            "subGroup": "Aluminium_SubGroup",
            "color": "Aluminium_Color",
            "thickness": "Aluminium_Thickness",
        },
        "C": {
            "brand": "CLine_Brand",
            "group": "CLine_Group",
            "subGroup": "CLine_SubGroup",
            "color": "CLine_Color",
            "thickness": "CLine_Thickness",
        },
        "E": {
            "brand": "Accessories_Brand",
            "group": "Accessories_Group",
            "subGroup": "Accessories_SubGroup",
            "color": "Accessories_Color",
            "character": "Character",  # ⭐ แก้ไขชื่อ table
        },
        "S": {
            "brand": "Sealant_Brand",
            "group": "Sealant_Group",
            "subGroup": "Sealant_SubGroup",
            "color": "Sealant_Color",
        },
        "Y": {
            "brand": "Gypsum_Brand",
            "group": "Gypsum_Group",
            "subGroup": "Gypsum_SubGroup",
            "color": "Gypsum_Color",
            "thickness": "Gypsum_Thickness",
        },
    }

    mappings = {}
    if category_name.upper() in mapping_tables:
        for field, table in mapping_tables[category_name.upper()].items():
            try:
                mappings[field] = load_mapping(table)
            except:
                mappings[field] = {}

    # ⭐ ดึง distinct values สำหรับแต่ละ field
    result = {}
    for field_name, extract_sql in field_extracts.items():
        sql = f"""
            SELECT DISTINCT {extract_sql} AS value
            FROM Items_Test
            WHERE {where_sql}
            ORDER BY value
        """
        cursor.execute(sql, *params)
        rows = cursor.fetchall()
        
        # ⭐ แปลงเป็น {code, name} พร้อม code ขึ้นหน้า
        codes = [r.value for r in rows if r.value]
        mapping = mappings.get(field_name, {})
        result[field_name] = [
            {
                "code": code, 
                "name": f"{code} - {mapping.get(code, code)}" if mapping.get(code) else code
            }
            for code in codes
        ]

    conn.close()
    return result
