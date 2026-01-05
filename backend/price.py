# price.py (UPDATED - สูตรปลอดภัยขึ้น)
import pandas as pd
import numpy as np
import re
import math

# ===== flexible column picking =====
CAND_QTY      = ["Quantity", "Qty", "จำนวน", "ปริมาณ"]
CAND_E        = ["_RelevantSales"] 
CAND_SHIPMENT = ["DeliveryType", "Shipment Method Code", "shipment", "ขนส่ง", "วิธีรับสินค้า"]
COL_TIER      = "_Tier_Z"  
CAND_SDM      = ["pkg_size", "sdm", "H", "Package Size", "SDM"]

def _pick_col(df: pd.DataFrame, candidates: list[str], default=None):
    for c in candidates:
        if c in df.columns:
            return c
    low_cols = {str(c).strip().lower(): c for c in df.columns}
    for c in candidates:
        key = str(c).strip().lower()
        if key in low_cols:
            return low_cols[key]
    return default

# ===== weights =====
W_QTY   = 0.3382
W_E     = 0.3971
W_SHIP  = 0.2647

# ===== mapping Tier → คอลัมน์ราคาที่ใช้คั่น =====
INTERP_COLS = {
    "R2->R1": ("priceR1", "priceR2"),
    "R1->W2": ("priceW2", "priceR1"),
    "W2->W1": ("priceW1", "priceW2"),
    "W1->P":  ("priceP",  "priceW1"), 
    "P->P":   ("priceP",  "priceP"),
}
DEFAULT_COLS = ("priceR2", "priceR1")

# ---------- 3 score functions (0.0-1.0) ----------

# ❗️ 1. (แก้ไข) เพิ่ม try-except เพื่อดักค่า pkg_size ที่เป็น None/NaN
def _score_qty01(qty: float, pkg_size: float) -> float:
    try:
        qty_f = float(qty)
        pkg_size_f = float(pkg_size)
        
        # (ตรวจสอบ NaN เพิ่มเติม)
        if pd.isna(pkg_size_f) or pkg_size_f == 0:
            return 0.0 
        
        score = qty_f / pkg_size_f
        return min(score, 1.0)
    except (ValueError, TypeError):
        # (ถ้า pkg_size เป็น "" หรือ None แล้ว float() พัง)
        return 0.0 # ❗️❗️ <--- จุดนี้คือจุดที่แก้ Error (คืนค่า 0.0 แทน None)

# ❗️ 2. (แก้ไข) เพิ่ม try-except เพื่อดักค่า e_val ที่เป็น None/NaN
def _score_e01(e_val: float) -> float:
    try:
        e = float(e_val)
        if pd.isna(e):
             return 0.0
        score = np.log1p(e) / 13.0 # 13 คือค่าคงที่
        return min(score, 1.0)
    except (ValueError, TypeError):
        return 0.0 # ❗️❗️ <--- จุดนี้คือจุดที่แก้ Error (คืนค่า 0.0 แทน None)

# ❗️ 3. (แก้ไข) เพิ่ม try-except (เผื่อไว้)
def _score_ship01(ship_val: str) -> float:
    try:
        if str(ship_val).strip() == "1": # 1 = PICKUP
            return 1.0
    except Exception:
        pass # (ไม่เป็นไร เพราะสุดท้ายจะ return 0.0)
    return 0.0 # 0 = DELIVERY (หรือค่า default)

# (ส่ง col_sdm เข้าไป)
def _calc_score01(row, col_qty, col_e, col_ship, col_sdm):
    qty01  = _score_qty01(row.get(col_qty), row.get(col_sdm)) 
    e01    = _score_e01(row.get(col_e))
    ship01 = _score_ship01(row.get(col_ship))
    total  = (qty01 * W_QTY + e01 * W_E + ship01 * W_SHIP) # (ตอนนี้ qty01, e01, ship01 เป็น 0.0)
    return qty01, e01, ship01, total

# ---------- ฟังก์ชันหลัก ----------
def Price(df: pd.DataFrame) -> pd.DataFrame:
    col_qty  = _pick_col(df, CAND_QTY) or CAND_QTY[0]
    col_e    = _pick_col(df, CAND_E) or CAND_E[0]
    col_ship = _pick_col(df, CAND_SHIPMENT) or CAND_SHIPMENT[0]
    col_sdm  = _pick_col(df, CAND_SDM) 

    scores = df.apply(
        lambda r: _calc_score01(r, col_qty, col_e, col_ship, col_sdm),
        axis=1, result_type="expand"
    )
    scores.columns = ["_QtyScore", "_EScore", "_ShipScore", "_Score01"]
    out = pd.concat([df.reset_index(drop=True), scores], axis=1)

    def _interp_price(row):
        score = row["_Score01"]
        
        # normalize tier first
        raw = str(row.get(COL_TIER, ""))

        tier = (
        raw.replace("→", "->")
            .replace("–", "-")
            .replace("—", "-")
            .replace(" ", "")
            .replace("\n", "")
            .replace("\r", "")
            .strip()
            .upper()
        )

        
        # debug
        print("TIER USED:", tier)
        
        col_low, col_high = INTERP_COLS.get(tier, DEFAULT_COLS)

        
        try:
            low_price = float(row.get(col_low))
            high_price = float(row.get(col_high))
            if pd.isna(low_price) or pd.isna(high_price):
                return row.get("price") 
        except Exception:
            return row.get("price") 
            
        new_price = low_price + (high_price - low_price) * (1-score)
        
        if pd.isna(new_price):
            return row.get("price")
            
        return new_price

    out["NewPrice"] = out.apply(_interp_price, axis=1)
    
    def _apply_payment_term_markup(row):
        term = str(row.get("payment_terms") or "").strip().lower()
        base_price = float(row.get("NewPrice", 0))

        # mapping markup %
        term_markup = {
            0:   0.000,  # 0 วัน
            15:  0.003,  # 0.30%
            30:  0.006,  # 0.60%
            45:  0.009,  # 0.90%
            60:  0.012,  # 1.20%
            90:  0.015,  # 1.50%
        }

        # 1) ดึงตัวเลขทั้งหมดในสตริง เช่น "NET 30 DAYS", "30.0", "CREDIT60" → [30], [30,0], [60]
        nums = re.findall(r"\d+", term)
        days = None
        if nums:
            # ใช้ค่ามากสุดเผื่อเคส "30.0" จะได้ 30 แทน 0
            days = max(int(n) for n in nums)
        else:
            # เผื่อเคสที่เขียนว่า "cash", "cod" ให้ถือเป็น 0 วัน
            if any(k in term for k in ["cash", "cod"]):
                days = 0

        pct = term_markup.get(days, 0.0)

        print(
            "[PAYMENT TERM DEBUG]",
            "sku =", row.get("sku"),
            "term =", term,
            "days =", days,
            "base =", base_price,
            "pct =", pct,
            "after =", base_price * (1 + pct),
        )

        return base_price * (1 + pct)
    
    

    
       


    out["NewPrice"] = out.apply(_apply_payment_term_markup, axis=1)
    # ปัดราคาต่อหน่วยลง 2 ทศนิยม (ราคาขายจริง)
    out["NewPrice"] = out["NewPrice"].apply(lambda x: math.ceil(float(x or 0) * 100) / 100)
    # ✅ =============================================

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.expand_frame_repr", False)
    # ===== DEBUG LOG =====
    print("\n=== PRICE SCORE DEBUG ===")
    debug_cols = [
        "sku" if "sku" in out.columns else None,
        COL_TIER,
        "_QtyScore",
        "_EScore",
        "_ShipScore",
        "_Score01",
        "NewPrice",
    ]
    debug_cols = [c for c in debug_cols if c]

    print(out[debug_cols].head(10))
    print("=== END PRICE DEBUG ===\n")

    

    return out