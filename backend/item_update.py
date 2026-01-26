from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from datetime import datetime
import sqlite3
import math
from config.db_sqlite import get_conn

router = APIRouter(prefix="/item-update", tags=["item-update"])


# -------------------------
# Helpers
# -------------------------
def _has_col(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns


def _get(row: pd.Series, col: str, default=None):
    if col not in row.index:
        return default
    v = row.get(col)
    if pd.isna(v):
        return default
    return v


def _to_str(v, default=None):
    if v is None or (isinstance(v, float) and pd.isna(v)) or pd.isna(v):
        return default
    s = str(v).strip()
    return s if s != "" else default


def _to_float(v, default=None):
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)) or pd.isna(v):
            return default
        return float(v)
    except Exception:
        return default


def _to_int(v, default=None):
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)) or pd.isna(v):
            return default
        return int(float(v))
    except Exception:
        return default


def _eq(a, b) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        if pd.isna(a) and pd.isna(b):
            return True
    except Exception:
        pass
    return str(a) == str(b)


def _is_missing_excel_value(row: pd.Series, col: str) -> bool:
    """
    True เมื่อ:
    - ไม่มีคอลัมน์นั้นในไฟล์ excel
    - หรือมีแต่ค่าเป็นว่าง/NaN
    """
    if col not in row.index:
        return True
    v = row.get(col)
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except Exception:
        pass
    s = str(v).strip()
    return s == ""


# ==============================
# 1) Upload Excel → create DRAFT version
# ==============================
@router.post("/upload")
def upload_price_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Only .xlsx is supported")

    df = pd.read_excel(file.file)
    df.columns = df.columns.str.strip()

    # ✅ No. 2 ไม่บังคับ
    required_cols = {"No.", "R1", "R2", "W1", "W2", "AlternateName"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(400, f"Missing columns: {required_cols - set(df.columns)}")

    has_no2 = _has_col(df, "No. 2")

    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    version_name = f"UPLOAD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    now = datetime.now().isoformat(timespec="seconds")

    cur.execute(
        """
        INSERT INTO Item_Update_Version
        (version_name, update_type, uploaded_by, job_title, uploaded_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            version_name,
            "MIXED",
            "system",
            "MANAGER",
            now,
            "DRAFT",
        ),
    )
    version_id = cur.lastrowid

    # โหลด SKU ที่มีอยู่
    existing = set(
        str(r["No."]).strip()
        for r in cur.execute('SELECT "No." as "No." FROM Items_Test').fetchall()
        if r["No."] is not None
    )

    inserted_detail = 0
    inserted_new_item = 0
    skipped_blank = 0

    # ✅ รายการแจ้งเตือน: SKU ใหม่ที่คอลัมน์สำหรับ INSERT ใหม่ไม่ครบ
    insert_warnings = []

    # ---- loop each row ----
    for _, row in df.iterrows():
        sku = _to_str(_get(row, "No.", None))
        if not sku:
            skipped_blank += 1
            continue

        new_r1 = _to_float(_get(row, "R1", None))
        new_r2 = _to_float(_get(row, "R2", None))
        new_w1 = _to_float(_get(row, "W1", None))
        new_w2 = _to_float(_get(row, "W2", None))
        new_alt = _to_str(_get(row, "AlternateName", None), default=None)

        excel_no2 = _to_str(_get(row, "No. 2", None), default=None) if has_no2 else None

        is_new_item = 0

        # ============================================================
        # CASE A) SKU ใหม่ → INSERT เข้า Items_Test
        # + แจ้งเตือนถ้าคอลัมน์สำหรับ INSERT ใหม่ไม่ครบ
        # ============================================================
        if sku not in existing:
            is_new_item = 1

            # --- ตรวจความครบของคอลัมน์สำหรับ INSERT ใหม่ (ราย SKU) ---
            required_insert_cols = [
                "No.", 
                "No. 2", 
                "Description",
                "RE",
                "SDM",
                "R1", 
                "R2", 
                "W1", 
                "W2",                
                "Inventory",
                "Base Unit of Measure",
                "Package Size",
                "Variant Mandatory if Exists",
                "Product Group",
                "Product Sub Group",
            ]
            missing_cols = [c for c in required_insert_cols if _is_missing_excel_value(row, c)]

            if missing_cols:
                insert_warnings.append({
                    "sku": sku,
                    "missing_columns": missing_cols
                })

            excel_desc = _to_str(_get(row, "Description", None), default=None)
            desc = (
                excel_desc
                or new_alt
                or sku
            )


            # ใส่ค่าจริงจาก Excel ถ้ามี / ถ้าไม่มีใส่ default (แต่ก็จะมี warning ข้างบน)
            base_uom = _to_str(_get(row, "Base Unit of Measure", None), default="PCS")
            pkg_size = _to_int(_get(row, "Package Size", None), default=1)
            variant_mandatory = _to_str(_get(row, "Variant Mandatory if Exists", None), default="NO")
            product_group = _to_str(_get(row, "Product Group", None), default=None)
            product_sub_group = _to_str(_get(row, "Product Sub Group", None), default=None)

            cur.execute(
                """
                INSERT INTO Items_Test (
                    "No.", "No. 2", "Description",
                    "R1", "R2", "W1", "W2",
                    "AlternateName",
                    "Inventory",
                    "Base Unit of Measure",
                    "Package Size",
                    "Variant Mandatory if Exists",
                    "Product Group",
                    "Product Sub Group"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sku,
                    excel_no2,   # ไม่บังคับ
                    desc,
                    new_r1, new_r2, new_w1, new_w2,
                    new_alt,
                    0,

                    base_uom,
                    pkg_size,
                    variant_mandatory,
                    product_group,
                    product_sub_group,
                ),
            )

            existing.add(sku)
            inserted_new_item += 1

            old_r1 = old_r2 = old_w1 = old_w2 = None
            old_alt = None
            old_no2 = None
            new_no2_for_detail = excel_no2

        # ============================================================
        # CASE B) SKU เดิม → ดึง old จาก DB
        # ถ้า Excel ไม่ได้ส่ง No.2 มา → new_no2 = old_no2 (ไม่ทับค่าเดิม)
        # ============================================================
        else:
            old = cur.execute(
                """
                SELECT R1, R2, W1, W2, AlternateName, "No. 2" as no2
                FROM Items_Test
                WHERE "No." = ?
                """,
                (sku,),
            ).fetchone()

            if not old:
                continue

            old_r1, old_r2, old_w1, old_w2 = old["R1"], old["R2"], old["W1"], old["W2"]
            old_alt, old_no2 = old["AlternateName"], old["no2"]

            new_no2_for_detail = excel_no2 if has_no2 else old_no2

        # --- flags ---
        change_price_flag = 1 if (
            is_new_item
            or not _eq(new_r1, old_r1)
            or not _eq(new_r2, old_r2)
            or not _eq(new_w1, old_w1)
            or not _eq(new_w2, old_w2)
        ) else 0

        change_altname_flag = 1 if (is_new_item or not _eq(new_alt, old_alt)) else 0

        cur.execute(
            """
            INSERT INTO Item_Update_Version_Detail (
                version_id, sku,
                new_R1, new_R2, new_W1, new_W2,
                old_R1, old_R2, old_W1, old_W2,
                new_alternate_name, old_alternate_name,
                new_no2, old_no2,
                change_price_flag, change_altname_flag
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                version_id, sku,
                new_r1, new_r2, new_w1, new_w2,
                old_r1, old_r2, old_w1, old_w2,
                new_alt, old_alt,
                new_no2_for_detail, old_no2,
                change_price_flag, change_altname_flag,
            ),
        )

        inserted_detail += 1

    conn.commit()
    conn.close()

    return {
        "version_id": version_id,
        "version_name": version_name,
        "inserted_new_item": inserted_new_item,
        "inserted_detail": inserted_detail,
        "skipped_blank": skipped_blank,
        "has_no2_column_in_excel": has_no2,

        # ✅ แจ้งเตือนที่ขอ
        "insert_warnings": insert_warnings,
        "insert_warnings_count": len(insert_warnings),
    }


# ==============================
# 2) Preview version
# ==============================
@router.get("/preview/{version_id}")
def preview_version(version_id: int):
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM Item_Update_Version_Detail WHERE version_id = ?",
        conn,
        params=(version_id,),
    )
    conn.close()

    # 🔑 สำคัญมาก: แปลง NaN → None ก่อน return
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")



# ==============================
# 3) Activate version
# ==============================
@router.post("/activate/{version_id}")
def activate_version(version_id: int):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT * FROM Item_Update_Version_Detail
        WHERE version_id = ?
        """,
        (version_id,),
    ).fetchall()

    for r in rows:
        cur.execute(
            """
            UPDATE Items_Test
            SET
              R1 = ?, R2 = ?, W1 = ?, W2 = ?,
              AlternateName = ?,
              "No. 2" = ?
            WHERE "No." = ?
            """,
            (
                r["new_R1"], r["new_R2"], r["new_W1"], r["new_W2"],
                r["new_alternate_name"],
                r["new_no2"],
                r["sku"],
            ),
        )

    cur.execute(
        """
        UPDATE Item_Update_Version
        SET status = 'ACTIVE'
        WHERE version_id = ?
        """,
        (version_id,),
    )

    conn.commit()
    conn.close()

    return {"status": "activated", "version_id": version_id}
