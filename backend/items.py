# items.py — FINAL VERSION FOR YOUR DATABASE
from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from db_sqlite import get_conn

router = APIRouter(prefix="/items", tags=["items"])
TABLE_NAME = "Items_Test"


def load_items_sqlite():
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{TABLE_NAME}"', conn)
    conn.close()

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
            "prices": {
                "R1": row.get("priceR1", 0),
                "R2": row.get("priceR2", 0),
                "W1": row.get("priceW1", 0),
                "W2": row.get("priceW2", 0),
            },
            "pkg_size": row.get("pkg_size", 1),
            "product_weight": row.get("product_weight", 0), 
        })

    return items


@router.get("/")
def search_items(q: str | None = Query(None)):
    df = load_items_sqlite()

    if q:
        q = q.lower()
        df = df[
            df["sku"].astype(str).str.lower().str.contains(q) |
            df["name"].astype(str).str.lower().str.contains(q)
        ]

    return df.to_dict("records")
