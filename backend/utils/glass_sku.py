# backend/glass_sku.py
import re

SKU_RE = re.compile(r"^G(\d{2})(\d{2})(\d{3})(\d{2})(\d{2})(\d{3})(\d{3})$")

def parse_glass_sku(sku: str):
    """
    แยก SKU: G + BB(2) + TT(2) + SSS(3) + CC(2) + TH(2) + WWW(3) + LLL(3)
    ตัวอย่าง: G01010010106024060
    """
    if not sku or not isinstance(sku, str):
        return None
    m = SKU_RE.match(sku.strip())
    if not m:
        return None
    brand, gtype, subtype, color, thick, width, length = m.groups()
    return {
        "brand": brand,
        "type": gtype,
        "subType": subtype,
        "color": color,
        "thickness_mm": int(thick),
        "width_in": int(width),
        "length_in": int(length),
    }

def build_glass_sku(brand, type_, sub_type, color, thickness_mm, width_in, length_in):
    """ประกอบ SKU ตาม format ข้างบน"""
    b = f"{int(brand):02d}"
    t = f"{int(type_):02d}"
    s = f"{int(sub_type):03d}"
    c = f"{int(color):02d}"
    th = f"{int(thickness_mm):02d}"
    w = f"{int(round(width_in)):03d}"
    l = f"{int(round(length_in)):03d}"
    return f"G{b}{t}{s}{c}{th}{w}{l}"
