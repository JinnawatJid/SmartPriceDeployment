# items.py — FINAL VERSION FOR YOUR DATABASE
from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from config.db_sqlite import get_conn


router = APIRouter(prefix="/items", tags=["items"])
TABLE_NAME = "Items_Test"


def load_items_sqlite():
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{TABLE_NAME}"', conn)
    conn.close()

    # create price columns
    if "R1" in df.columns: df["priceR1"] = pd.to_numeric(df["R1"], errors="coerce").fillna(0)
    if "R2" in df.columns: df["priceR2"] = pd.to_numeric(df["R2"], errors="coerce").fillna(0)
    if "W1" in df.columns: df["priceW1"] = pd.to_numeric(df["W1"], errors="coerce").fillna(0)
    if "W2" in df.columns: df["priceW2"] = pd.to_numeric(df["W2"], errors="coerce").fillna(0)

    # rename important columns
    rename_map = {
        "No.": "sku",
        "Description": "name",
        "Package Size": "pkg_size"
    }
    df = df.rename(columns={old: new for old, new in rename_map.items() if old in df.columns})

    # create category from Inventory Posting Group
    if "Inventory Posting Group" not in df.columns:
        raise HTTPException(500, "❌ Missing Inventory Posting Group in Items_Test")

    df["category"] = df["Inventory Posting Group"].astype(str).str.upper()

    # create price columns
    if "R1" in df.columns: df["priceR1"] = df["R1"]
    if "R2" in df.columns: df["priceR2"] = df["R2"]
    if "W1" in df.columns: df["priceW1"] = df["W1"]
    if "W2" in df.columns: df["priceW2"] = df["W2"]
    if "RE" in df.columns:
        df["cost"] = pd.to_numeric(df["RE"], errors="coerce").fillna(0)
    else:
        df["cost"] = 0
    # --- create product_weight column from Product Weight ---
    if "Product Weight" in df.columns:
        df["product_weight"] = pd.to_numeric(df["Product Weight"], errors="coerce").fillna(0)
    else:
        df["product_weight"] = 0


    # pkg_size fallback
    if "pkg_size" not in df.columns:
        df["pkg_size"] = 1

        # --- Variant flag from "Variant Mandatory if Exists" ---
    if "Variant Mandatory if Exists" in df.columns:
        df["isVariant"] = (
            df["Variant Mandatory if Exists"]
            .astype(str)
            .str.strip()
            .str.upper()
            .eq("YES")
        )
    else:
        df["isVariant"] = False
    
    # --- Product Group / Sub Group ---
    if "Product Group" in df.columns:
        df["product_group"] = df["Product Group"].astype(str).str.strip()
    else:
        df["product_group"] = None

    if "Product Sub Group" in df.columns:
        df["product_sub_group"] = df["Product Sub Group"].astype(str).str.strip()
    else:
        df["product_sub_group"] = None

    # --- Alternate Names ---
    if "AlternateName" in df.columns:
        df["alternate_names"] = (
            df["AlternateName"]
            .astype(str)
            .str.strip()
        )
    else:
        df["alternate_names"] = None
    
    # --- No. 2 (Secondary SKU / Alternate Code) ---
    if "No. 2" in df.columns:
        df["sku2"] = (
            df["No. 2"]
            .astype(str)
            .str.strip()
        )
    else:
        df["sku2"] = None




    return df


@router.get("/categories/list")
def get_item_categories():
    df = load_items_sqlite()
    grouped = (
        df.groupby("category")
          .size()
          .reset_index(name="count")
          .rename(columns={"category": "name"})
    )
    return grouped.to_dict("records")


@router.get("/categories/{category_name}")
def get_items_by_category(category_name: str):
    df = load_items_sqlite()

    filtered = df[df["category"] == category_name.upper()]

    items = []
    for _, row in filtered.iterrows():
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


        })

    return items


@router.get("/search")
def full_text_search_items(q: str = Query(..., min_length=3)):
    df = load_items_sqlite()
    q = q.strip().lower()

    def contains(col):
        if not isinstance(col, pd.Series):
            return False
        return col.astype(str).str.lower().str.contains(q, na=False)

    df = df[
        contains(df["sku"]) |
        contains(df.get("sku2")) |
        contains(df["name"]) |
        contains(df.get("Description")) |
        contains(df.get("Inventory Posting Group")) |
        contains(df.get("Base Unit Measure")) |
        contains(df.get("alternate_names"))
    ]

    return df.head(50).to_dict("records")  # ⭐ limit 5 ที่ backend

 

