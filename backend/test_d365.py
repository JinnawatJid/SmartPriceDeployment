# test_d365.py
from config.config_external_api import CUSTOMER_API_URL, CUSTOMER_API_HEADERS
import requests

r = requests.post(
    CUSTOMER_API_URL,
    json={"page": 1, "size": 1},
    headers=CUSTOMER_API_HEADERS,
    timeout=10,
)

print(r.status_code)
print(r.text)
