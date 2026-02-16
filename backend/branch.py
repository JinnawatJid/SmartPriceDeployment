"""
Branch Router

This module provides API endpoints for branch data from MSSQL.
"""

from fastapi import APIRouter, HTTPException
from config.db_mssql import get_mssql_conn
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/branches", tags=["branches"])


@router.get("")
def get_branches():
    """
    Get all branches from MSSQL Branch table.
    
    Returns:
        List of branches with Code and Name
    """
    conn = None
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # Query all branches ordered by Code
        cursor.execute("SELECT Code, Name FROM Branch ORDER BY Code")
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        branches = [
            {"Code": row[0], "Name": row[1]}
            for row in rows
        ]
        
        cursor.close()
        
        logger.info(f"Fetched {len(branches)} branches from database")
        
        return {"branches": branches}
    
    except Exception as e:
        logger.error(f"Failed to fetch branches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch branches: {str(e)}"
        )
    
    finally:
        if conn:
            conn.close()


@router.get("/{code}")
def get_branch_by_code(code: str):
    """
    Get specific branch by code.
    
    Args:
        code: Branch code
    
    Returns:
        Branch with Code and Name
    """
    conn = None
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT Code, Name FROM Branch WHERE Code = ?", (code,))
        row = cursor.fetchone()
        
        cursor.close()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Branch with code '{code}' not found"
            )
        
        return {"Code": row[0], "Name": row[1]}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch branch {code}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch branch: {str(e)}"
        )
    
    finally:
        if conn:
            conn.close()
