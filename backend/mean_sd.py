import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

# โหลดไฟล์
FILE_PATH = r"C:\Users\HP\Desktop\Quetung\Corr\AY\AYUTTHAYA .xlsx"
SHEET_NAME = "AY1-6"
OUTPUT_JSON = Path(__file__).parent / "mean_sd.json" 

try:
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)
except FileNotFoundError:
    print(f"Error: ไม่พบไฟล์ {FILE_PATH}")
    exit()
except Exception as e:
    print(f"Error: ไม่สามารถอ่านไฟล์ Excel: {e}")
    exit()


# --- แปลงข้อมูล ---
# (ใช้ชื่อคอลัมน์จาก Excel ต้นฉบับ)
df["Accum6m"] = pd.to_numeric(df.get("Accum6m"), errors="coerce")
df["Frequency"] = pd.to_numeric(df.get("Frequency"), errors="coerce")
df["Customer Date"] = pd.to_datetime(df.get("Customer Date"), errors="coerce")

# Accum6m ไป ln 
df["Accum6m_ln"] = np.log(df["Accum6m"] + 1)   # +1 กัน log(0)

# แปลง Customer Date → Tenure (ปี)
current_year = datetime.now().year
df["Tenure_Year"] = current_year - df["Customer Date"].dt.year


# --- คำนวณ mean และ sd ---
# (❗️ FIX: เปลี่ยน Key ทั้งหมดเป็น snake_case)
summary = {
    "accum_6m_ln_mean": np.nanmean(df["Accum6m_ln"]),
    "accum_6m_ln_sd": np.nanstd(df["Accum6m_ln"], ddof=0),
    "frequency_mean": np.nanmean(df["Frequency"]),
    "frequency_sd": np.nanstd(df["Frequency"], ddof=0),
    "tenure_mean": np.nanmean(df["Tenure_Year"]),
    "tenure_sd": np.nanstd(df["Tenure_Year"], ddof=0)
}

# --- บันทึกเป็น JSON ---
try:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        # ใส่ [summary] เพื่อให้โครงสร้างเหมือนไฟล์ mean_sd.json เดิม
        json.dump([summary], f, indent=4)
    print(f"บันทึกไฟล์ mean_sd.json (ฉบับแก้ไข) เรียบร้อยที่: {OUTPUT_JSON}")
except Exception as e:
    print(f"Error: ไม่สามารถบันทึกไฟล์ JSON: {e}")