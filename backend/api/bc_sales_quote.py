# bc_sales_quote.py
"""
Business Central Sales Quote API Integration
ทดสอบการสร้าง Sales Quote ใน BC
"""
import requests
from .bc_client import bc_url, bc_headers, bc_auth


def create_sales_quote(customer_no: str, external_doc_no: str = ""):
    """
    สร้าง Sales Quote Header ใน Business Central
    
    Args:
        customer_no: รหัสลูกค้าใน BC (เช่น "C00001")
        external_doc_no: เลขที่เอกสารอ้างอิง (เช่น QuoteNo จากระบบ)
    
    Returns:
        dict: {"documentNo": "SQ-xxxxx", "etag": "..."}
    """
    payload = {
        "Document_Type": "Quote",  # สำคัญ! ต้องระบุเป็น Quote
        "Sell_to_Customer_No": customer_no,
        "External_Document_No": external_doc_no or "",
    }

    try:
        # ใช้ endpoint SalesQuote (ตามที่เห็นจาก BC ของคุณ)
        resp = requests.post(
            bc_url("SalesQuote"),  # ไม่มี 's' ท้าย
            json=payload,
            headers=bc_headers(),
            auth=bc_auth(),
            timeout=30
        )
        
        print("=" * 60)
        print("BC SALES QUOTE - CREATE HEADER")
        print("=" * 60)
        print(f"URL: {bc_url('SalesQuote')}")
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        print("=" * 60)
        
        resp.raise_for_status()
        
        data = resp.json()
        return {
            "documentNo": data.get("No", ""),
            "documentType": data.get("Document_Type", ""),
            "status": data.get("Status", ""),
            "etag": data.get("@odata.etag", "")
        }
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def add_quote_line(
    document_no: str,
    item_no: str,
    qty: float,
    unit_price: float | None = None,
    description: str = ""
):
    """
    เพิ่มรายการสินค้าใน Sales Quote
    
    Args:
        document_no: เลขที่ Sales Quote (จาก create_sales_quote)
        item_no: รหัสสินค้าใน BC
        qty: จำนวน
        unit_price: ราคาต่อหน่วย (ถ้าไม่ระบุจะใช้ราคาจาก BC)
        description: รายละเอียดเพิ่มเติม
    """
    payload = {
        "Document_Type": "Quote",
        "Document_No": document_no,
        "Type": "Item",
        "No": item_no,
        "Quantity": qty,
    }
    
    if description:
        payload["Description"] = description
    
    # ใส่ราคาเฉพาะกรณีต้องการ override
    if unit_price is not None:
        payload["Unit_Price"] = unit_price

    try:
        resp = requests.post(
            bc_url("SalesQuotesLine"),  # ใช้ endpoint ที่เห็นจากภาพ
            json=payload,
            headers=bc_headers(),
            auth=bc_auth(),
            timeout=30
        )
        
        print("=" * 60)
        print("BC SALES QUOTE - ADD LINE")
        print("=" * 60)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        print("=" * 60)
        
        resp.raise_for_status()
        return resp.json()
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def get_sales_quote(document_no: str):
    """
    ดึงข้อมูล Sales Quote จาก BC
    """
    try:
        resp = requests.get(
            bc_url(f"SalesQuote('{document_no}')"),  # ไม่มี 's' ท้าย
            headers=bc_headers(),
            auth=bc_auth(),
            timeout=30
        )
        
        print(f"GET Sales Quote Status: {resp.status_code}")
        resp.raise_for_status()
        
        return resp.json()
        
    except Exception as e:
        print(f"❌ Error getting quote: {e}")
        raise


def list_available_endpoints():
    """
    ตรวจสอบ endpoints ที่มีใน BC OData
    """
    try:
        resp = requests.get(
            bc_url(""),  # เรียก base URL
            headers=bc_headers(),
            auth=bc_auth(),
            timeout=30
        )
        
        print("=" * 60)
        print("BC AVAILABLE ENDPOINTS")
        print("=" * 60)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if "value" in data:
                print("\nAvailable entities:")
                for item in data["value"]:
                    name = item.get("name", "")
                    if "sales" in name.lower() or "quote" in name.lower():
                        print(f"  ✓ {name}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
