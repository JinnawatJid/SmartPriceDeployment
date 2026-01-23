# config_external_api.py
import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# Customer API (D365)
# =========================
CUSTOMER_API_URL = os.getenv(
    "CUSTOMER_API_URL",
    "http://192.192.0.37:8280/customer/1.0.0",
)
CUSTOMER_API_KEY = os.getenv("CUSTOMER_API_KEY")

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
INVOICE_API_KEY = os.getenv("INVOICE_API_KEY")

INVOICE_API_HEADERS = {
    "apikey": INVOICE_API_KEY,
    "Content-Type": "application/json",
}


print("CUSTOMER_API_KEY LOADED =", bool(CUSTOMER_API_KEY))
print("INVOICE_API_KEY LOADED =", bool(INVOICE_API_KEY))
print("CUSTOMER API HEADERS =", CUSTOMER_API_HEADERS)

