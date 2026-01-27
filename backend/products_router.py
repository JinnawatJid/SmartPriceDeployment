# products_router.py — Unified Routers (Clean) + Keep ALL endpoints & response keys the same
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Dict, Any, List, Callable

import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from config.db_sqlite import get_conn
from services.sku_enricher import enrich_by_category

# ==========================================================
# ROOT ROUTER (include only this in main.py)
# ==========================================================
api_router = APIRouter()


# ==========================================================
# SHARED: SQLite helpers
# ==========================================================
ITEMS_TABLE_NAME = "Items_Test"


def _read_table(table: str) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
    conn.close()
    df.columns = [c.strip() for c in df.columns]
    return df


@lru_cache(maxsize=256)
def load_code_name_mapping(table_name: str) -> dict:
    """
    Cached mapping loader: table must have Code, Name
    """
    df = _read_table(table_name)
    if "Code" not in df.columns or "Name" not in df.columns:
        return {}
    out = {}
    for _, r in df.iterrows():
        out[str(r["Code"]).strip()] = str(r["Name"]).strip()
    return out


def _zfill(v: Optional[str], n: int) -> Optional[str]:
    if v is None or v == "":
        return None
    return str(v).zfill(n)


def _parse_by_slices(sku: str, slices: Dict[str, slice], prefix: str, min_len: int) -> Dict[str, Optional[str]]:
    s = (sku or "").strip().upper()
    if not s.startswith(prefix) or len(s) < min_len:
        # return keys with None to keep downstream stable
        return {k: None for k in slices.keys()}
    out = {}
    for k, sl in slices.items():
        try:
            out[k] = s[sl]
        except Exception:
            out[k] = None
    return out


def _load_items_by_prefix(prefix: str) -> pd.DataFrame:
    df = _read_table(ITEMS_TABLE_NAME)
    if "No." not in df.columns:
        return pd.DataFrame()
    q = df[df["No."].astype(str).str.upper().str.startswith(prefix)].copy()
    if q.empty:
        return pd.DataFrame()
    q["SKU"] = q["No."].astype(str).str.upper().str.strip()
    q["Inventory"] = pd.to_numeric(q.get("Inventory", 0), errors="coerce").fillna(0)
    return q


def _apply_filters(df: pd.DataFrame, filters: Dict[str, Optional[str]], pad: Dict[str, int]) -> pd.DataFrame:
    q = df
    for k, v in filters.items():
        if not v:
            continue
        if k not in q.columns:
            continue
        want = str(v)
        if k in pad:
            want = _zfill(want, pad[k])
        q = q[q[k].astype(str) == want]
    return q


def _unique_sorted(df: pd.DataFrame, col: str) -> List[str]:
    if col not in df.columns or df.empty:
        return []
    s = df[col].dropna().astype(str)
    s = s[s != ""]
    return sorted(set(s.tolist()))


def _list_code_name(codes: List[str], mapping: dict) -> List[dict]:
    return [{"code": c, "name": mapping.get(c, c)} for c in codes]


# ==========================================================
# GENERIC SKU CATEGORY SPEC
# ==========================================================
@dataclass(frozen=True)
class SkuCategorySpec:
    prefix: str
    min_len: int
    slices: Dict[str, slice]          # parsed columns
    pad: Dict[str, int]               # zfill for filtering

    # mapping tables
    map_brand: Optional[str] = None
    map_group: Optional[str] = None
    map_subgroup: Optional[str] = None
    map_color: Optional[str] = None
    map_thickness: Optional[str] = None
    map_character: Optional[str] = None  # accessories

    # output keys (must match your original response)
    master_keys: Dict[str, str] = None   # parsed_col -> response_list_key (e.g. "subGroup" -> "subGroups")


def _build_master_response(
    spec: SkuCategorySpec,
    df: pd.DataFrame,
    filters: Dict[str, Optional[str]],
    include_source_filters: bool = False,
) -> Dict[str, Any]:
    """
    Build master/options response with key names matching original.
    """
    # mappings
    brand_map = load_code_name_mapping(spec.map_brand) if spec.map_brand else {}
    group_map = load_code_name_mapping(spec.map_group) if spec.map_group else {}
    sub_map = load_code_name_mapping(spec.map_subgroup) if spec.map_subgroup else {}
    color_map = load_code_name_mapping(spec.map_color) if spec.map_color else {}
    thick_map = load_code_name_mapping(spec.map_thickness) if spec.map_thickness else {}
    char_map = load_code_name_mapping(spec.map_character) if spec.map_character else {}

    out: Dict[str, Any] = {}
    if include_source_filters:
        out["source"] = "sqlite"
        out["filters"] = filters

    # for each list we must return with original key name
    for parsed_col, resp_key in spec.master_keys.items():
        codes = _unique_sorted(df, parsed_col)
        if resp_key == "brands":
            out[resp_key] = _list_code_name(codes, brand_map)
        elif resp_key == "groups":
            out[resp_key] = _list_code_name(codes, group_map)
        elif resp_key == "subGroups":
            out[resp_key] = _list_code_name(codes, sub_map)
        elif resp_key == "colors":
            out[resp_key] = _list_code_name(codes, color_map)
        elif resp_key == "thickness":
            out[resp_key] = _list_code_name(codes, thick_map)
        elif resp_key == "characters":
            out[resp_key] = _list_code_name(codes, char_map)
        else:
            # fallback
            out[resp_key] = _list_code_name(codes, {})
    return out


# ==========================================================
# 1) ITEMS ROUTER (from items.py) — keep outputs the same
# ==========================================================
items_router = APIRouter(prefix="/items", tags=["items"])


def load_items_sqlite() -> pd.DataFrame:
    df = _read_table(ITEMS_TABLE_NAME)

    # rename important columns (match your response usage)
    rename_map = {"No.": "sku", "Description": "name", "Package Size": "pkg_size"}
    df = df.rename(columns={old: new for old, new in rename_map.items() if old in df.columns})

    # category
    if "Inventory Posting Group" not in df.columns:
        raise HTTPException(500, "❌ Missing Inventory Posting Group in Items_Test")
    df["category"] = df["Inventory Posting Group"].astype(str).str.upper().str.strip()

    # prices (keep keys priceR1..W2 same, just normalize numeric once)
    for col, out_col in [("R1", "priceR1"), ("R2", "priceR2"), ("W1", "priceW1"), ("W2", "priceW2")]:
        if col in df.columns:
            df[out_col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[out_col] = 0

    # cost
    if "RE" in df.columns:
        df["cost"] = pd.to_numeric(df["RE"], errors="coerce").fillna(0)
    else:
        df["cost"] = 0

    # product_weight
    if "Product Weight" in df.columns:
        df["product_weight"] = pd.to_numeric(df["Product Weight"], errors="coerce").fillna(0)
    else:
        df["product_weight"] = 0

    # pkg_size fallback
    if "pkg_size" not in df.columns:
        df["pkg_size"] = 1

    # Variant flag
    if "Variant Mandatory if Exists" in df.columns:
        df["isVariant"] = df["Variant Mandatory if Exists"].astype(str).str.strip().str.upper().eq("YES")
    else:
        df["isVariant"] = False

    # Product Group/Sub Group
    df["product_group"] = df["Product Group"].astype(str).str.strip() if "Product Group" in df.columns else None
    df["product_sub_group"] = df["Product Sub Group"].astype(str).str.strip() if "Product Sub Group" in df.columns else None

    # Alternate Names
    df["alternate_names"] = df["AlternateName"].astype(str).str.strip() if "AlternateName" in df.columns else None

    # No. 2
    df["sku2"] = df["No. 2"].astype(str).str.strip() if "No. 2" in df.columns else None

    return df


@items_router.get("/categories/list")
def get_item_categories():
    df = load_items_sqlite()
    grouped = df.groupby("category").size().reset_index(name="count").rename(columns={"category": "name"})
    return grouped.to_dict("records")


@items_router.get("/categories/{category_name}")
def get_items_by_category(category_name: str):
    df = load_items_sqlite()
    filtered = df[df["category"] == category_name.upper()]

    items = []
    for _, row in filtered.iterrows():
        extra = enrich_by_category(row["category"], row["sku"]) or {}
        items.append({
            "sku": row["sku"],
            "name": row["name"],
            "inventory": row.get("Inventory", 0),
            "unit": row.get("Base Unit Measure", ""),
            "category": row["category"],
            "isVariant": bool(row.get("isVariant", False)),
            "prices": {
                "R1": row.get("priceR1", 0),
                "R2": row.get("priceR2", 0),
                "W1": row.get("priceW1", 0),
                "W2": row.get("priceW2", 0),
            },
            "pkg_size": row.get("pkg_size", 1),
            "product_weight": row.get("product_weight", 0),
            "sqft_sheet": row.get("Sqft_Sheet"),
            "product_group": row.get("product_group"),
            "product_sub_group": row.get("product_sub_group"),
            "alternate_names": row.get("alternate_names"),
            "sku2": row.get("sku2"),
            **extra,
        })
    return items


@items_router.get("/search")
def full_text_search_items(q: str = Query(..., min_length=3)):
    df = load_items_sqlite()
    q = q.strip().lower()

    def contains(series: pd.Series) -> pd.Series:
        return series.astype(str).str.lower().str.contains(q, na=False)

    mask = contains(df["sku"]) | contains(df["name"])
    if "sku2" in df.columns: mask |= contains(df["sku2"])
    if "Inventory Posting Group" in df.columns: mask |= contains(df["Inventory Posting Group"])
    if "Base Unit Measure" in df.columns: mask |= contains(df["Base Unit Measure"])
    if "alternate_names" in df.columns: mask |= contains(df["alternate_names"])

    return df[mask].head(50).to_dict("records")


# ==========================================================
# 2) SKU BASED ROUTERS (ALU / CL / SEA / GYP / ACC)
# ==========================================================

# ---------- ALUMINIUM ----------
aluminium_router = APIRouter(prefix="/aluminium", tags=["aluminium"])
ALU = SkuCategorySpec(
    prefix="A",
    min_len=12,
    slices={"brand": slice(1, 3), "group": slice(3, 5), "subGroup": slice(5, 8), "color": slice(8, 10), "thickness": slice(10, 12)},
    pad={"brand": 2, "group": 2, "subGroup": 3, "color": 2, "thickness": 2},
    map_brand="Aluminium_Brand",
    map_group="Aluminium_Group",
    map_subgroup="Aluminium_SubGroup",
    map_color="Aluminium_Color",
    map_thickness="Aluminium_Thickness",
    master_keys={"brand": "brands", "group": "groups", "subGroup": "subGroups", "color": "colors", "thickness": "thickness"},
)


def _load_parsed_items(spec: SkuCategorySpec) -> pd.DataFrame:
    df = _load_items_by_prefix(spec.prefix)
    if df.empty:
        return df
    parsed = pd.json_normalize(df["SKU"].apply(lambda x: _parse_by_slices(x, spec.slices, spec.prefix, spec.min_len)))
    out = pd.concat([df.reset_index(drop=True), parsed.reset_index(drop=True)], axis=1)
    out["onhand_qty"] = pd.to_numeric(out.get("Inventory", 0), errors="coerce").fillna(0).astype(int)
    return out


@aluminium_router.get("/options")
@aluminium_router.get("/master")
def aluminium_master(
    brand: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    thickness: Optional[str] = Query(None),
):
    df = _load_parsed_items(ALU)
    if df.empty:
        return {"source": "sqlite", "filters": {}, "brands": [], "groups": [], "subGroups": [], "colors": [], "thickness": []}

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color, "thickness": thickness}
    q = _apply_filters(df, filters, ALU.pad)

    return _build_master_response(ALU, q, filters, include_source_filters=True)


@aluminium_router.get("/items")
def aluminium_items(
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
    thickness: Optional[str] = None,
):
    df = _load_parsed_items(ALU)
    if df.empty:
        return []

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color, "thickness": thickness}
    q = _apply_filters(df, filters, ALU.pad)

    brand_map = load_code_name_mapping("Aluminium_Brand")
    group_map = load_code_name_mapping("Aluminium_Group")
    sub_map = load_code_name_mapping("Aluminium_SubGroup")
    color_map = load_code_name_mapping("Aluminium_Color")

    items = []
    for _, row in q.iterrows():
        items.append({
            "sku": row["SKU"],
            "name": row.get("Description", ""),
            "brand": row.get("brand"),
            "brandName": brand_map.get(row.get("brand"), ""),
            "group": row.get("group"),
            "groupName": group_map.get(row.get("group"), ""),
            "subGroup": row.get("subGroup"),
            "subGroupName": sub_map.get(row.get("subGroup"), ""),
            "color": row.get("color"),
            "colorName": color_map.get(row.get("color"), ""),
            "thickness": row.get("thickness"),
            "inventory": row.get("onhand_qty", 0),
            "product_group": row.get("Product Group"),
            "product_sub_group": row.get("Product Sub Group"),
        })
    return items


# ---------- C-LINE ----------
cline_router = APIRouter(prefix="/cline", tags=["cline"])
CL = SkuCategorySpec(
    prefix="C",
    min_len=12,
    slices={"brand": slice(1, 3), "group": slice(3, 5), "subGroup": slice(5, 8), "color": slice(8, 10), "thickness": slice(10, 12)},
    pad={"brand": 2, "group": 2, "subGroup": 3, "color": 2, "thickness": 2},
    map_brand="C-ผLine_Brand",
    map_group="C-Line_Group",
    map_subgroup="C-Line_SubGroup",
    map_color="C-Line_Color",
    map_thickness="C-Line_Thickness",
    master_keys={"brand": "brands", "group": "groups", "subGroup": "subGroups", "color": "colors", "thickness": "thickness"},
)


@cline_router.get("/items")
def get_cline_items(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    thickness: str = None
):
    df = _load_parsed_items(CL)
    if df.empty:
        return []

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color, "thickness": thickness}
    q = _apply_filters(df, filters, CL.pad)

    brand_map = load_code_name_mapping("C-Line_Brand")
    group_map = load_code_name_mapping("C-Line_Group")
    sub_map = load_code_name_mapping("C-Line_SubGroup")
    color_map = load_code_name_mapping("C-Line_Color")
    thick_map = load_code_name_mapping("C-Line_Thickness")

    results = []
    for _, row in q.iterrows():
        results.append({
            "sku": str(row["No."]).strip(),
            "name": str(row.get("Description", "")).strip(),
            "brand": row.get("brand"),
            "group": row.get("group"),
            "subGroup": row.get("subGroup"),
            "color": row.get("color"),
            "thickness": row.get("thickness"),
            "brandName": brand_map.get(row.get("brand"), row.get("brand")),
            "groupName": group_map.get(row.get("group"), row.get("group")),
            "subGroupName": sub_map.get(row.get("subGroup"), row.get("subGroup")),
            "colorName": color_map.get(row.get("color"), row.get("color")),
            "thicknessName": thick_map.get(row.get("thickness"), row.get("thickness")),
            "inventory": int(row.get("Inventory", 0) or 0),
            "unit": row.get("Base Unit of Measure", "") or "",
            "pkg_size": int(row.get("Package Size", 1) or 1),
            "product_weight": float(row.get("Product Weight", 0) or 0),
            "product_group": row.get("Product Group"),
            "product_sub_group": row.get("Product Sub Group"),
        })
    return results


@cline_router.get("/master")
def cline_master(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    thickness: str = None
):
    df = _load_parsed_items(CL)
    if df.empty:
        return {"brands": [], "groups": [], "subGroups": [], "colors": [], "thickness": []}

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color, "thickness": thickness}
    q = _apply_filters(df, filters, CL.pad)

    return _build_master_response(CL, q, filters, include_source_filters=False)


@cline_router.get("/options")
def cline_options():
    # keep same response shape as before
    def mapping_to_list(mapping: dict):
        return [{"code": k, "name": v} for k, v in mapping.items()]

    return {
        "brands": mapping_to_list(load_code_name_mapping("C-Line_Brand")),
        "groups": mapping_to_list(load_code_name_mapping("C-Line_Group")),
        "subGroups": mapping_to_list(load_code_name_mapping("C-Line_SubGroup")),
        "colors": mapping_to_list(load_code_name_mapping("C-Line_Color")),
        "thickness": mapping_to_list(load_code_name_mapping("C-Line_Thickness")),
    }


# ---------- ACCESSORIES ----------
accessories_router = APIRouter(prefix="/accessories", tags=["accessories"])
ACC = SkuCategorySpec(
    prefix="E",
    min_len=11,  # to safely read char position
    slices={
        "brand": slice(1, 4),
        "group": slice(4, 6),
        "subGroup": slice(6, 8),
        "color": slice(8, 10),
        "character": slice(10, 11),
    },
    pad={},  # accessories ไม่ได้ zfill ในโค้ดเดิม
    map_brand="Accessories_Brand",
    map_group="Accessories_Group",
    map_subgroup="Accessories_SubGroup",
    map_color="Accessories_Color",
    map_character="Character",
    master_keys={"brand": "brands", "group": "groups", "subGroup": "subGroups", "color": "colors", "character": "characters"},
)


@accessories_router.get("/items")
def get_accessories_items(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    character: str = None
):
    df = _load_parsed_items(ACC)
    if df.empty:
        return []

    df["inventory"] = pd.to_numeric(df.get("Inventory", 0), errors="coerce").fillna(0).astype(int)
    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color, "character": character}
    q = _apply_filters(df, filters, ACC.pad)

    brand_map = load_code_name_mapping("Accessories_Brand")
    group_map = load_code_name_mapping("Accessories_Group")
    sub_map = load_code_name_mapping("Accessories_SubGroup")
    color_map = load_code_name_mapping("Accessories_Color")
    char_map = load_code_name_mapping("Character")

    results = []
    for _, row in q.iterrows():
        results.append({
            "sku": row["No."],
            "name": row["Description"],
            "alternateName": row.get("AlternateName"),
            "brand": row.get("brand"),
            "brandName": brand_map.get(row.get("brand"), ""),
            "group": row.get("group"),
            "groupName": group_map.get(row.get("group"), ""),
            "subGroup": row.get("subGroup"),
            "subGroupName": sub_map.get(row.get("subGroup"), ""),
            "color": row.get("color"),
            "colorName": color_map.get(row.get("color"), ""),
            "character": row.get("character"),
            "characterName": char_map.get(row.get("character"), ""),
            "inventory": row.get("inventory", 0),
            "product_group": row.get("Product Group"),
            "product_sub_group": row.get("Product Sub Group"),
        })
    return results


@accessories_router.get("/master")
def accessories_master(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    character: str = None
):
    df = _load_parsed_items(ACC)
    if df.empty:
        return {"brands": [], "groups": [], "subGroups": [], "colors": [], "characters": []}

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color, "character": character}
    q = _apply_filters(df, filters, ACC.pad)

    return _build_master_response(ACC, q, filters, include_source_filters=False)


@accessories_router.get("/options")
def accessories_options(
    brand: str = None,
    group: str = None,
    subGroup: str = None,
    color: str = None,
    character: str = None
):
    return accessories_master(brand=brand, group=group, subGroup=subGroup, color=color, character=character)


# ---------- SEALANT ----------
sealant_router = APIRouter(prefix="/sealant", tags=["sealant"])
SEA = SkuCategorySpec(
    prefix="S",
    min_len=10,
    slices={"brand": slice(1, 3), "group": slice(3, 5), "subGroup": slice(5, 8), "color": slice(8, 10)},
    pad={"brand": 2, "group": 2, "subGroup": 3, "color": 2},
    map_brand="Sealant_Brand",
    map_group="Sealant_Group",
    map_subgroup="Sealant_SubGroup",
    map_color="Sealant_Color",
    master_keys={"brand": "brands", "group": "groups", "subGroup": "subGroups", "color": "colors"},
)


@sealant_router.get("/master")
def sealant_master(
    brand: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
):
    df = _load_parsed_items(SEA)
    if df.empty:
        return {"brands": [], "groups": [], "subGroups": [], "colors": []}

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color}
    q = _apply_filters(df, filters, SEA.pad)

    return _build_master_response(SEA, q, filters, include_source_filters=False)


@sealant_router.get("/options")
def sealant_options(
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
):
    return sealant_master(brand=brand, group=group, subGroup=subGroup, color=color)


@sealant_router.get("/items")
def sealant_items(
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
):
    df = _load_parsed_items(SEA)
    if df.empty:
        return []

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color}
    q = _apply_filters(df, filters, SEA.pad)

    brand_map = load_code_name_mapping("Sealant_Brand")
    group_map = load_code_name_mapping("Sealant_Group")
    sub_map = load_code_name_mapping("Sealant_SubGroup")
    color_map = load_code_name_mapping("Sealant_Color")

    items = []
    for _, row in q.iterrows():
        items.append({
            "sku": row["SKU"],
            "name": row.get("Description", ""),
            "brand": row.get("brand"),
            "brandName": brand_map.get(row.get("brand"), ""),
            "group": row.get("group"),
            "groupName": group_map.get(row.get("group"), ""),
            "subGroup": row.get("subGroup"),
            "subGroupName": sub_map.get(row.get("subGroup"), ""),
            "color": row.get("color"),
            "colorName": color_map.get(row.get("color"), ""),
            "inventory": row.get("onhand_qty", 0),
            "product_group": row.get("Product Group"),
            "product_sub_group": row.get("Product Sub Group"),
        })
    return items


# ---------- GYPSUM ----------
gypsum_router = APIRouter(prefix="/gypsum", tags=["gypsum"])
GYP = SkuCategorySpec(
    prefix="Y",
    min_len=18,
    slices={
        "brand": slice(1, 3),
        "group": slice(3, 5),
        "subGroup": slice(5, 7),
        "color": slice(7, 10),
        "thickness": slice(10, 12),
        "sizeCode": slice(12, 18),
    },
    pad={"brand": 2, "group": 2, "subGroup": 2, "color": 3, "thickness": 2},
    map_brand="Gypsum_Brand",
    map_group="Gypsum_Group",
    map_subgroup="Gypsum_SubGroup",
    map_color="Gypsum_Color",
    map_thickness="Gypsum_Thickness",
    master_keys={"brand": "brands", "group": "groups", "subGroup": "subGroups", "color": "colors", "thickness": "thickness"},
)


@gypsum_router.get("/master")
def gypsum_master(
    brand: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    thickness: Optional[str] = Query(None),
):
    df = _load_parsed_items(GYP)
    if df.empty:
        return {"brands": [], "groups": [], "subGroups": [], "colors": [], "thickness": []}

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color, "thickness": thickness}
    q = _apply_filters(df, filters, GYP.pad)

    return _build_master_response(GYP, q, filters, include_source_filters=False)


@gypsum_router.get("/options")
def gypsum_options(
    brand: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    thickness: Optional[str] = Query(None),
):
    return gypsum_master(brand=brand, group=group, subGroup=subGroup, color=color, thickness=thickness)


@gypsum_router.get("/items")
def gypsum_items(
    brand: Optional[str] = None,
    group: Optional[str] = None,
    subGroup: Optional[str] = None,
    color: Optional[str] = None,
    thickness: Optional[str] = None,
):
    df = _load_parsed_items(GYP)
    if df.empty:
        return []

    filters = {"brand": brand, "group": group, "subGroup": subGroup, "color": color, "thickness": thickness}
    q = _apply_filters(df, filters, GYP.pad)

    brand_map = load_code_name_mapping("Gypsum_Brand")
    group_map = load_code_name_mapping("Gypsum_Group")
    sub_map = load_code_name_mapping("Gypsum_SubGroup")
    color_map = load_code_name_mapping("Gypsum_Color")
    thick_map = load_code_name_mapping("Gypsum_Thickness")

    items = []
    for _, row in q.iterrows():
        items.append({
            "sku": row["SKU"],
            "name": row.get("Description", ""),
            "brand": row.get("brand"),
            "brandName": brand_map.get(row.get("brand"), ""),
            "group": row.get("group"),
            "groupName": group_map.get(row.get("group"), ""),
            "subGroup": row.get("subGroup"),
            "subGroupName": sub_map.get(row.get("subGroup"), ""),
            "color": row.get("color"),
            "colorName": color_map.get(row.get("color"), ""),
            "thickness": row.get("thickness"),
            "inventory": row.get("onhand_qty", 0),
            "unit": row.get("Base Unit of Measure", "") or "",
            "pkg_size": int(row.get("Package Size", 1) or 1),
            "product_weight": float(row.get("Product Weight", 0) or 0),
            "product_group": row.get("Product Group"),
            "product_sub_group": row.get("Product Sub Group"),
        })
    return items


# ==========================================================
# 7) GLASS ROUTER (keep logic as-is, only minor tidy)
# ==========================================================
glass_router = APIRouter(prefix="/glass", tags=["glass"])


def parse_glass_sku(sku: str):
    return {
        "brand": sku[1:3],
        "type": sku[3:5],
        "subGroup": sku[5:8],
        "color": sku[8:10],
        "thickness": sku[10:12],
        "width": int(sku[12:15]),
        "height": int(sku[15:18]),
    }


@glass_router.get("/list")
def get_glass_list(
    brand: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    subGroup: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    thickness: Optional[str] = Query(None)
):
    conn = get_conn()
    cur = conn.cursor()

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

        if brand and parsed["brand"] != brand: continue
        if type and parsed["type"] != type: continue
        if subGroup and parsed["subGroup"] != subGroup: continue
        if color and parsed["color"] != color: continue
        if thickness and parsed["thickness"] != thickness: continue

        is_variant = str(vmand or "").strip().upper() == "YES"

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
            "group": parsed["type"],
            "groupName": typeName,
            "subGroup": parsed["subGroup"],
            "subGroupName": subGroupName,
            "color": parsed["color"],
            "colorName": colorName,
            "thickness": parsed["thickness"],
            "width": parsed["width"],
            "height": parsed["height"],
            "product_group": product_group,
            "product_sub_group": product_sub_group,
        })

    conn.close()
    return {"items": result}


class GlassCalcRequest(BaseModel):
    sku: str
    widthRaw: float
    heightRaw: float
    widthRounded: float
    heightRounded: float
    sqftRaw: float
    sqftRounded: float
    qty: int


@glass_router.post("/calc")
def calc_glass(req: GlassCalcRequest):
    parsed = parse_glass_sku(req.sku)

    conn = get_conn()
    cur = conn.cursor()

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

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT R2 FROM Items_Test WHERE [No.] = ?""", (req.sku,))
    row = cur.fetchone()
    price_r2 = row[0] if row and row[0] else 0
    conn.close()

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


# ==========================================================
# INCLUDE ALL SUB-ROUTERS INTO api_router
# ==========================================================
api_router.include_router(items_router)
api_router.include_router(aluminium_router)
api_router.include_router(cline_router)
api_router.include_router(accessories_router)
api_router.include_router(sealant_router)
api_router.include_router(gypsum_router)
api_router.include_router(glass_router)
