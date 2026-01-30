# ============================================
# email_config.py
# Email Configuration
# ============================================

import os
from pathlib import Path
from dotenv import load_dotenv

# โหลด .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# โหลดจาก environment variables หรือใช้ค่า default
EMAIL_CONFIG = {
    # SMTP Configuration (สำหรับส่ง Email)
    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_user": os.getenv("SMTP_USER", "noreply@company.com"),
    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
    "smtp_use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
    
    # IMAP Configuration (สำหรับรับ Email Reply)
    "imap_host": os.getenv("IMAP_HOST", "imap.gmail.com"),
    "imap_port": int(os.getenv("IMAP_PORT", "993")),
    "imap_user": os.getenv("IMAP_USER", "noreply@company.com"),
    "imap_password": os.getenv("IMAP_PASSWORD", ""),
    
    # Email Settings
    "from_email": os.getenv("FROM_EMAIL", "noreply@company.com"),
    "from_name": os.getenv("FROM_NAME", "ระบบใบเสนอราคา"),
    
    # Retry Settings
    "max_retries": int(os.getenv("EMAIL_MAX_RETRIES", "3")),
    "retry_delay": int(os.getenv("EMAIL_RETRY_DELAY", "60")),  # seconds
}

# PDF Storage Path
PDF_STORAGE_PATH = Path(__file__).parent.parent / "data" / "special_price_pdfs"
PDF_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# Export individual variables for easier import
SMTP_SERVER = EMAIL_CONFIG["smtp_host"]
SMTP_PORT = EMAIL_CONFIG["smtp_port"]
SMTP_USE_TLS = EMAIL_CONFIG["smtp_use_tls"]
EMAIL_ADDRESS = EMAIL_CONFIG["smtp_user"]
EMAIL_PASSWORD = EMAIL_CONFIG["smtp_password"]

IMAP_SERVER = EMAIL_CONFIG["imap_host"]
IMAP_PORT = EMAIL_CONFIG["imap_port"]

FROM_EMAIL = EMAIL_CONFIG["from_email"]
FROM_NAME = EMAIL_CONFIG["from_name"]

MAX_RETRIES = EMAIL_CONFIG["max_retries"]
RETRY_DELAY = EMAIL_CONFIG["retry_delay"]
