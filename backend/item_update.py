from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from datetime import datetime
from config.db_sqlite import get_conn


router = APIRouter(prefix="/item-update", tags=["item-update"])


# ==============================
# 1) Upload Excel → create DRAFT version
# ==============================
@router.post("/upload")
def upload_price_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Only .xlsx is supported")

    df = pd.read_excel(file.file)
    df.columns = df.columns.str.strip()

    required_cols = {"No.","No. 2", "R1", "R2", "W1", "W2", "AlternateName"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            400,
            f"Missing columns: {required_cols - set(df.columns)}"
        )

    conn = get_conn()
    cur = conn.cursor()

    version_name = f"UPLOAD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    now = datetime.now().isoformat(timespec="seconds")

    cur.execute("""
        INSERT INTO Item_Update_Version
        (version_name, update_type, uploaded_by, job_title, uploaded_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        version_name,
        "MIXED",
        "system",          # 🔒 later replace with auth
        "MANAGER",
        now,
        "DRAFT"
    ))

    version_id = cur.lastrowid

    # ---- loop each SKU ----
    for _, row in df.iterrows():
        sku = str(row["No."]).strip()

        item = conn.execute(
            'SELECT R1,R2,W1,W2,AlternateName,"No. 2" FROM Items_Test WHERE "No." = ?',
            (sku,)
        ).fetchone()

        if not item:
            continue

        cur.execute("""
            INSERT INTO Item_Update_Version_Detail (
                version_id, sku,
                new_R1, new_R2, new_W1, new_W2,
                old_R1, old_R2, old_W1, old_W2,
                new_alternate_name, old_alternate_name,
                new_no2, old_no2,
                change_price_flag, change_altname_flag
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            version_id, sku,
            row["R1"], row["R2"], row["W1"], row["W2"],
            item["R1"], item["R2"], item["W1"], item["W2"],
            row["AlternateName"], item["AlternateName"],
            row["No. 2"], item["No. 2"],
            1, 1
        ))

    conn.commit()
    conn.close()
    return {
        "version_id": version_id,
        "version_name": version_name
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
        params=(version_id,)
    )
    conn.close()

    return df.to_dict("records")


# ==============================
# 3) Activate version
# ==============================
@router.post("/activate/{version_id}")
def activate_version(version_id: int):
    conn = get_conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT * FROM Item_Update_Version_Detail
        WHERE version_id = ?
    """, (version_id,)).fetchall()

    for r in rows:
        cur.execute("""
            UPDATE Items_Test
            SET
              R1 = ?, R2 = ?, W1 = ?, W2 = ?,
              AlternateName = ?,"No. 2" = ?
            WHERE "No." = ?
        """, (
            r["new_R1"], r["new_R2"], r["new_W1"], r["new_W2"],
            r["new_alternate_name"],
            r["new_no2"],
            r["sku"]
        ))

    cur.execute("""
        UPDATE Item_Update_Version
        SET status = 'ACTIVE'
        WHERE version_id = ?
    """, (version_id,))

    conn.commit()
    conn.close()

    return {"status": "activated"}