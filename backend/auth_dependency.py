# auth_dependency.py
from fastapi import Header, Request
import jwt
import os
import logging

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-this")
JWT_ALG = "HS256"


def get_branch_code(request: Request, authorization: str = Header(None)) -> str:
    """
    Extract branch code from JWT token in cookies or Authorization header.
    
    Returns:
        Branch code from token, or "00TR" as default if no token provided
    """
    token = request.cookies.get("auth_token")
    if not token and authorization:
        token = authorization.replace("Bearer ", "").strip()

    if not token:
        logger.info("No auth_token cookie or Authorization header provided, using default branch 00TR")
        return "00TR"  # Default branch
    
    try:
        
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        
        # Get branchId from payload
        branch_id = payload.get("branchId")
        
        if not branch_id:
            logger.warning("No branchId in token, using default branch 00TR")
            return "00TR"  # Default if no branchId in token
        
        logger.info(f"Extracted branch code from token: {branch_id}")
        return branch_id
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired, using default branch 00TR")
        return "00TR"  # Don't raise error, just use default
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}, using default branch 00TR")
        return "00TR"  # Don't raise error, just use default
    except Exception as e:
        logger.error(f"Error extracting branch code: {e}, using default branch 00TR")
        return "00TR"  # Default on any error


def get_employee_info(request: Request, authorization: str = Header(None)) -> dict:
    """
    Extract employee information from JWT token in cookies or Authorization header.
    
    Returns:
        Dictionary with employee_id, name, branch_code, role, and region
    """
    default_info = {
        "employee_id": "UNKNOWN",
        "name": "Unknown User",
        "branch_code": "00TR",
        "role": "Sales",
        "region": "Unknown"
    }
    
    token = request.cookies.get("auth_token")
    if not token and authorization:
        token = authorization.replace("Bearer ", "").strip()

    if not token:
        logger.info("No auth_token cookie or Authorization header provided, using default employee info")
        return default_info
    
    try:
        
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        
        # Debug: print all payload keys
        print(f"[JWT DEBUG] Payload keys: {list(payload.keys())}")
        print(f"[JWT DEBUG] Payload: {payload}")
        print(f"[JWT DEBUG] payload.get('sub') = {payload.get('sub')}")
        print(f"[JWT DEBUG] Type of sub: {type(payload.get('sub'))}")
        
        # Extract employee information from token
        # Try different possible field names
        # Note: Use explicit None check to avoid issues with falsy values like 0 or empty string
        employee_id = payload.get("sub")  # JWT standard field for user ID
        if not employee_id:
            employee_id = payload.get("employeeId")
        if not employee_id:
            employee_id = payload.get("employee_id")
        if not employee_id:
            employee_id = payload.get("id")
        if not employee_id:
            employee_id = payload.get("userId")
        if not employee_id:
            employee_id = "UNKNOWN"
        
        # Convert to string if it's not already
        employee_id = str(employee_id) if employee_id != "UNKNOWN" else "UNKNOWN"
        
        name = (
            payload.get("name") or 
            payload.get("username") or 
            payload.get("fullName") or 
            "Unknown User"
        )
        
        branch_code = (
            payload.get("branchId") or 
            payload.get("branch_code") or 
            payload.get("branch") or 
            "00TR"
        )
        
        role = (
            payload.get("role") or 
            payload.get("position") or 
            "Sales"
        )
        
        region = (
            payload.get("region") or 
            "Unknown"
        )
        
        employee_info = {
            "employee_id": employee_id,
            "name": name,
            "branch_code": branch_code,
            "role": role,
            "region": region
        }
        
        print(f"[JWT DEBUG] Extracted employee_id={employee_info['employee_id']}, name={employee_info['name']}, branch={employee_info['branch_code']}, role={employee_info['role']}")
        return employee_info
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired, using default employee info")
        return default_info
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}, using default employee info")
        return default_info
    except Exception as e:
        logger.error(f"Error extracting employee info: {e}, using default employee info")
        return default_info
