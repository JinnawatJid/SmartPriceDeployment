"""
Role Mapping Module

This module provides mapping from Thai role names (from auth_token) to internal role codes.
The auth_token contains role names in Thai which need to be translated to English codes
for internal use throughout the application.

Role Mappings:
1. พนักงานขาย → Sales
2. ผู้จัดการสาขา (R1-W2) → ZM (Zone Manager)
3. ผู้จัดการภูมิภาค (R1-W2) → RM (Regional Manager)
4. ผู้จัดการฝ่ายขาย (W1-SDM) → SDM (Sales Director Manager)
5. ผู้จัดการผลิตภัณฑ์ (Below SDM) → PM (Product Manager)
6. กรรมการผู้จัดการ → CEO
"""

import logging

logger = logging.getLogger(__name__)

# Thai role name to internal role code mapping
THAI_ROLE_TO_CODE = {
    "พนักงานขาย": "Sales",
    "ผู้จัดการสาขา (R1-W2)": "ZM",  # Zone Manager
    "ผู้จัดการภูมิภาค (R1-W2)": "RM",  # Regional Manager
    "ผู้จัดการฝ่ายขาย (W1-SDM)": "SDM",  # Sales Director Manager
    "ผู้จัดการผลิตภัณฑ์ (Below SDM)": "PM",  # Product Manager
    "กรรมการผู้จัดการ": "CEO",
}

# Valid role codes (for when role is already in English)
VALID_ROLE_CODES = {"Sales", "ZM", "RM", "SDM", "PM", "CEO"}

# Default role when mapping fails
DEFAULT_ROLE = "Sales"


def map_thai_role_to_code(thai_role_name: str) -> str:
    """
    Map Thai role name from auth_token to internal role code.
    Also accepts English role codes directly.
    
    Args:
        thai_role_name: Role name in Thai from auth_token (e.g., "พนักงานขาย")
                       or English role code (e.g., "Sales")
        
    Returns:
        Internal role code (Sales, ZM, RM, SDM, PM, CEO)
        Returns "Sales" as default if role name is not recognized
        
    Example:
        >>> map_thai_role_to_code("พนักงานขาย")
        'Sales'
        >>> map_thai_role_to_code("Sales")
        'Sales'
        >>> map_thai_role_to_code("ผู้จัดการสาขา (R1-W2)")
        'ZM'
        >>> map_thai_role_to_code("Unknown Role")
        'Sales'
    """
    if not thai_role_name:
        logger.warning("Empty thai_role_name provided, returning default role 'Sales'")
        return DEFAULT_ROLE
    
    # Check if it's already a valid English role code
    if thai_role_name in VALID_ROLE_CODES:
        logger.info(f"Role '{thai_role_name}' is already a valid role code")
        return thai_role_name
    
    # Try exact match for Thai role name
    role_code = THAI_ROLE_TO_CODE.get(thai_role_name)
    
    if role_code:
        logger.info(f"Mapped Thai role '{thai_role_name}' to code '{role_code}'")
        return role_code
    else:
        logger.warning(
            f"Unknown Thai role name '{thai_role_name}', returning default role '{DEFAULT_ROLE}'"
        )
        return DEFAULT_ROLE


def get_role_display_name(role_code: str) -> str:
    """
    Get display name for role code.
    
    Args:
        role_code: Internal role code (Sales, ZM, RM, SDM, PM, CEO)
        
    Returns:
        Human-readable role name in English
    """
    role_display_names = {
        "Sales": "Sales",
        "ZM": "Zone Manager",
        "RM": "Regional Manager",
        "SDM": "Sales Director Manager",
        "PM": "Product Manager",
        "CEO": "Chief Executive Officer",
    }
    return role_display_names.get(role_code, role_code)


def get_thai_role_name(role_code: str) -> str:
    """
    Get Thai role name from internal role code (reverse mapping).
    
    Args:
        role_code: Internal role code (Sales, ZM, RM, SDM, PM, CEO)
        
    Returns:
        Thai role name or empty string if not found
    """
    # Create reverse mapping
    code_to_thai = {code: thai for thai, code in THAI_ROLE_TO_CODE.items()}
    return code_to_thai.get(role_code, "")


def is_valid_role_code(role_code: str) -> bool:
    """
    Check if a role code is valid.
    
    Args:
        role_code: Role code to validate
        
    Returns:
        True if role code is valid, False otherwise
    """
    return role_code in VALID_ROLE_CODES


def get_all_role_codes() -> list:
    """
    Get list of all valid role codes.
    
    Returns:
        List of all internal role codes
    """
    return list(VALID_ROLE_CODES)
