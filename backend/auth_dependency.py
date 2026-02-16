# auth_dependency.py
from fastapi import Header
import jwt
import os
import logging

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-this")
JWT_ALG = "HS256"


def get_branch_code(authorization: str = Header(None)) -> str:
    """
    Extract branch code from JWT token in Authorization header.
    
    Returns:
        Branch code from token, or "00TR" as default if no token provided
    """
    if not authorization:
        logger.info("No Authorization header provided, using default branch 00TR")
        return "00TR"  # Default branch
    
    try:
        # Remove "Bearer " prefix if present
        token = authorization.replace("Bearer ", "").strip()
        
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
