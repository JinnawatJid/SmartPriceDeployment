# config_external_api.py
import os
from dotenv import load_dotenv

load_dotenv()

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


print("BASE_URL =", BASE_URL)
print("CUSTOMER_API_KEY LOADED =", bool(CUSTOMER_API_KEY))
print("INVOICE_API_KEY LOADED =", bool(INVOICE_API_KEY))
print("CREDIT_API_KEY LOADED =", bool(CREDIT_API_KEY))
print("EMP_API_KEY LOADED =", bool(EMP_API_KEY))
print("CUSTOMER API HEADERS =", CUSTOMER_API_HEADERS)

