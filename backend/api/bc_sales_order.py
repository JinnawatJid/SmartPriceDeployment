# bc_sales_order.py
import requests
from .bc_client import bc_url, bc_headers, bc_auth

def create_sales_header(customer_no: str, external_doc_no: str):
    payload = {
    "Sell_to_Customer_No": customer_no,
    "External_Document_No": external_doc_no
}

      

    resp = requests.post(
        bc_url("SalesOrders"),
        json=payload,
        headers=bc_headers(),
        auth=bc_auth(),
        timeout=30
    )
    print("BC HEADER STATUS:", resp.status_code)
    print("BC HEADER RESPONSE:", resp.text)
    
    resp.raise_for_status()

    data = resp.json()
    return {
        "documentNo": data["No"],
        "etag": data["@odata.etag"]
    }

def add_sales_line(
    document_no: str,
    item_no: str,
    qty: float,
    unit_price: float | None = None
):
    payload = {
        "Document_No": document_no,
        "Type": "Item",
        "No": item_no,
        "Quantity": qty
    }

    # ใส่ราคาเฉพาะกรณีควบคุม pricing เอง
    if unit_price is not None:
        payload["UnitPrice"] = unit_price

    resp = requests.post(
        bc_url("salesDocumentLines"),
        json=payload,
        headers=bc_headers(),
        auth=bc_auth(),
        timeout=30
    )
    resp.raise_for_status()
    print("BC HEADER STATUS:", resp.status_code)
    print("BC HEADER RESPONSE:", resp.text)

    return resp.json()
