# LevelPrice.py (UPDATED - แก้ไข snake_case)
import json
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.special import erf
import sys
import os

# ============== WEIGHTS (รวมกัน = 100) ==============\
W_ACCUM6M = 20.72
W_FREQ    = 28.5
W_TENURE  = 16.84
W_GENBUS  = 33.94
WEIGHT_SUM = 100.0

# ============== MAP คะแนนเป็น Tier ===================
def map_score_to_price_band(score: float) -> str:
    if pd.isna(score):
        return "Unknown"
    s = float(score)
    if 0 <= s < 40:
        return "R2->R1"
    elif 40 <= s < 70:
        return "R1->W2"
    elif 70 <= s <= 100:
        return "W2->W1"
    return "Unknown"

# ============== Helpers ===================
def _pick_col(df: pd.DataFrame, candidates: list[str], default=None):
    for c in candidates:
        if c in df.columns:
            return c
    # ลองจับชื่อแบบ case-insensitive และตัดช่องว่าง
    low_cols = {str(c).strip().lower(): c for c in df.columns}
    for c in candidates:
        key = str(c).strip().lower()
        if key in low_cols:
            return low_cols[key]
    return default

def _z_to_score_fixed(z, mean, sd):
    if mean is None or sd is None or sd == 0:
        return 0.0  # ถ้าไม่มีค่าสถิติ
    
    # คำนวณ Z-score (จัดการค่า NaN)
    z_score = (z - mean) / sd
    
    # แปลง Z-score เป็น % (CDF)
    # (erf(z / sqrt(2)) + 1) / 2
    percentage = (erf(z_score / np.sqrt(2)) + 1) / 2
    
    # map 0-1 (percent) ไปเป็น 0-100 (score)
    score = percentage * 100
    
    # จัดการค่า NaN ที่อาจเกิดจาก z (เช่น pd.NA)
    score = score.fillna(0.0) 
    return score

# ============== โหลดไฟล์สถิติ (mean/sd) ===================
STATS = {}
try:
    if getattr(sys, 'frozen', False):
        # If running as bundled app, use _MEIPASS
        JSON_PATH = Path(sys._MEIPASS) / "mean_sd.json"
    else:
        # Dev mode
        JSON_PATH = Path(__file__).parent / "mean_sd.json"

    with open(JSON_PATH, "r") as f:
        # (ไฟล์ json เดิมเป็น list ที่มี 1 dict)
        STATS = json.load(f)[0] 
except FileNotFoundError:
    print(f"❌ ไม่พบไฟล์ {JSON_PATH} - LevelPrice จะคำนวณ Z-Score ไม่ได้")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดในการอ่าน mean_sd.json: {e}")


# ============== ตัวเลือกคอลัมน์ (CANDIDATES) ===================
# (❗️ FIX: ลดความซ้ำซ้อน เหลือแค่ snake_case ที่เราใช้เป็นมาตรฐาน)
CAND_TENURE  = ["customer_date"] # เรามั่นใจว่า router ส่ง 'customer_date' มา
CAND_ACCUM6M = ["accum_6m"]      # เรามั่นใจว่า router ส่ง 'accum_6m' มา
CAND_FREQ    = ["frequency"]     # เรามั่นใจว่า router ส่ง 'frequency' มา
CAND_GENBUS  = ["gen_bus"]       # เรามั่นใจว่า router ส่ง 'gen_bus' มา

# Mapping Gen Bus
GENBUS_MAP = {"W": 0.15, "R": 0.27, "P": 0.21}

# ============== ฟังก์ชันหลัก ===================
def LevelPrice(df: pd.DataFrame) -> pd.DataFrame:
    
    # --- 1. หาชื่อคอลัมน์ที่จะใช้ ---
    col_tenure  = _pick_col(df, CAND_TENURE)
    col_accum6m = _pick_col(df, CAND_ACCUM6M)
    col_freq    = _pick_col(df, CAND_FREQ)
    col_genbus  = _pick_col(df, CAND_GENBUS)

    # --- 2. คำนวณ Score ของแต่ละปัจจัย (Z-Score) ---
    current_year = datetime.now().year

    # ---------------- Tenure (customer_date) ----------------
    if col_tenure:
        cust_date = pd.to_datetime(df[col_tenure], errors="coerce")
        tenure = current_year - cust_date.dt.year
    else:
        tenure = pd.Series(np.nan, index=df.index)
        
    # (❗️ FIX: อ้างอิง key ใหม่ "tenure_mean", "tenure_sd")
    df["_TenureScore_Z"] = _z_to_score_fixed(
        tenure,
        STATS.get("tenure_mean"),
        STATS.get("tenure_sd")
    )

    # ---------------- Accum6m ----------------
    if col_accum6m:
        accum6m = pd.to_numeric(df[col_accum6m], errors="coerce")
    else:
        accum6m = pd.Series(np.nan, index=df.index)
    df["_Accum6m_ln"] = np.log1p(accum6m) 
    
    
    df["_Accum6mScore_Z"] = _z_to_score_fixed(
        df["_Accum6m_ln"],
        STATS.get("accum_6m_ln_mean"), # ลองหา key (ln) ก่อน
        STATS.get("accum_6m_ln_sd")
    )

    # ---------------- Frequency ----------------
    if col_freq:
        freq = pd.to_numeric(df[col_freq], errors="coerce")
    else:
        freq = pd.Series(np.nan, index=df.index)
    

    df["_FrequencyScore_Z"] = _z_to_score_fixed(
        freq,
        STATS.get("frequency_mean"),
        STATS.get("frequency_sd")
    )

    # ---------------- Gen Bus (map เป็น 0.x) ----------------
    if col_genbus:
        df["_GenBusRaw"] = (
            df[col_genbus].astype(str).str.strip().str.upper()
        )
        # Map ค่า (W=0.5, R=0.2, P=0.0) และ map 0-1 ไป 0-100
        df["_GenBusScore_Z"] = df["_GenBusRaw"].map(GENBUS_MAP).fillna(0.0) * 100
    else:
        df["_GenBusScore_Z"] = 0.0 # ถ้าไม่มีข้อมูล GenBus ให้เป็น 0

    # --- 3. รวมคะแนน (Weighted Average) ---
    df["_Score_Z"] = (
        df["_Accum6mScore_Z"].fillna(0) * W_ACCUM6M +
        df["_FrequencyScore_Z"].fillna(0) * W_FREQ +
        df["_TenureScore_Z"].fillna(0) * W_TENURE +
        df["_GenBusScore_Z"].fillna(0) * W_GENBUS
    ) / WEIGHT_SUM
    
    # --- 4. Map คะแนนรวมเป็น Tier ---
    df["_Tier_Z"] = df["_Score_Z"].apply(map_score_to_price_band)

    return df