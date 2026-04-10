# config_external_api.py
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# =========================
# Base URL for Email Links
# =========================
BASE_URL = os.getenv(
    "BASE_URL",
    "http://localhost:8000",  # Default สำหรับ development
)

# =========================
# Customer API (D365)
# =========================
CUSTOMER_API_URL = os.getenv(
    "CUSTOMER_API_URL",
    "http://192.192.0.37:8280/customer/1.0.0",
)
CUSTOMER_API_KEY = os.getenv("CUSTOMER_API_KEY", "").strip()

CUSTOMER_API_HEADERS = {
    "apikey": CUSTOMER_API_KEY,
    "Content-Type": "application/json",
}


# =========================
# Invoice API (D365)
# =========================
INVOICE_API_URL = os.getenv(
    "INVOICE_API_URL",
    "http://192.192.0.37:8280/invoice-sp681/1.0.0",
)
INVOICE_API_KEY = os.getenv("INVOICE_API_KEY", "").strip()

INVOICE_API_HEADERS = {
    "apikey": INVOICE_API_KEY,
    "Content-Type": "application/json",
}


# =========================
# Credit API
# =========================
CREDIT_API_URL = os.getenv(
    "CREDIT_API_URL",
    "http://192.192.0.37:3000",
)
CREDIT_API_KEY = os.getenv("CREDIT_API_KEY", "").strip()

CREDIT_API_HEADERS = {
    "X-API-KEY": CREDIT_API_KEY,
    "Content-Type": "application/json",
}


# =========================
# Employee API (D365)
# =========================
EMP_API_URL = os.getenv(
    "EMP_API_URL",
    "http://192.192.0.37:8280/employee-dynamic/1.0.0",
)
EMP_API_KEY = os.getenv("EMP_API_KEY", "").strip()

EMP_API_HEADERS = {
    "apikey": EMP_API_KEY,
    "Content-Type": "application/json",
}

# Employee Query by Role API (UXP Auth Service)
EMP_QUERY_API_URL = os.getenv(
    "EMP_QUERY_API_URL",
    "http://localhost:52683/auth/get-user-by-role",  # Default from your screenshot
)
EMP_QUERY_API_KEY = os.getenv("EMP_QUERY_API_KEY", "").strip()

EMP_QUERY_API_HEADERS = {
    "apikey": EMP_QUERY_API_KEY,
    "Content-Type": "application/json",
} if EMP_QUERY_API_KEY else {
    "Content-Type": "application/json",
}

# ⭐ Location API (ดึงข้อมูลสาขา/location)
LOCATION_API_URL = os.getenv(
    "LOCATION_API_URL",
    "http://192.192.0.37:8280/silver_location_/1.0.0",
)
LOCATION_API_KEY = os.getenv("LOCATION_API_KEY", "").strip()

LOCATION_API_HEADERS = {
    "apikey": LOCATION_API_KEY,
    "Content-Type": "application/json",
}


# =========================
# Item Cost API (D365)
# =========================
ITEMCOST_API_URL = os.getenv(
    "ITEMCOST_API_URL",
    "http://192.192.0.37:8280/silver_itemcostbylocation_dx/1.0.0",
)
ITEM_COST_API_KEY = os.getenv("ITEM_COST_API_KEY", "").strip()

ITEMCOST_API_HEADERS = {
    "apikey": ITEM_COST_API_KEY,
    "Content-Type": "application/json",
}


# =========================
# Special Price Request Configuration
# =========================
SDM_THRESHOLD_PRICE = float(os.getenv("SDM_THRESHOLD_PRICE", "50000"))
# ราคาขั้นต่ำที่ต้องส่งให้ SDM อนุมัติ
# ถ้าราคา < SDM_THRESHOLD_PRICE จะส่งให้ PM แทน


# =========================
# Remaining Credit API (D365)
# =========================
REMAININGCREDIT_URL = os.getenv(
    "REMAININGCREDIT_URL",
    "http://192.192.0.37:8280/silver_customerremainingcredit/1.0.0",
)
# ⭐ ลองใช้ CUSTOMER_API_KEY ก่อน เพราะเป็น API เกี่ยวกับข้อมูลลูกค้า
# ถ้าไม่ได้ ให้ขอ API key ใหม่ที่มีสิทธิ์เข้าถึง silver_customerremainingcredit
REMAININGCREDIT_KEY = os.getenv("REMAININGCREDIT_KEY", "").strip()
if not REMAININGCREDIT_KEY:
    REMAININGCREDIT_KEY = CUSTOMER_API_KEY
    logger.warning("⚠️ REMAININGCREDIT_KEY not found, using CUSTOMER_API_KEY instead")

# ⭐ API นี้ใช้ header "apikey" (ตัวเล็กทั้งหมด) เหมือน API อื่นๆ
REMAININGCREDIT_HEADERS = {
    "apikey": REMAININGCREDIT_KEY,
    "Content-Type": "application/json",
}
