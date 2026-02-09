# cache_config.py
# Configuration for Customer Cache System

# =====================================================
# Feature Flags
# =====================================================

# Set to True to use database cache, False to use original API-based implementation
USE_DATABASE_CACHE = True

# =====================================================
# Job Configuration
# =====================================================

# Batch size for database upsert operations
BATCH_SIZE = 100

# API pagination size
API_PAGE_SIZE = 500

# API timeout in seconds
API_TIMEOUT = 60

# Maximum retries for failed operations
MAX_RETRIES = 3

# =====================================================
# Logging Configuration
# =====================================================

# Log file path
LOG_FILE = "logs/customer_cache_refresh.log"

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# Log rotation - keep logs for 30 days
LOG_BACKUP_COUNT = 30
