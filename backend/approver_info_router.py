"""
Approver Information Router

Provides endpoints to get information about who holds what position at which branch.
This helps the frontend display who will approve special price requests.
"""

from fastapi import APIRouter, Depends, HTTPException
from auth_dependency import get_employee_info
from employee_position_mapper import (
    find_zm_at_branch,
    find_rm_in_region,
    find_sdm,
    resolve_approver_position,
    get_all_zms,
    get_all_rms
)
from branch_region_mapping import get_region_from_branch

router = APIRouter(prefix="/api/approver-info", tags=["approver-info"])


@router.get("/my-approvers")
async def get_my_approvers(employee_info: dict = Depends(get_employee_info)):
    """
    Get information about who will approve requests from the current user.
    Returns ZM, RM, and SDM information based on user's branch.
    """
    branch_code = employee_info.get('branch_code')
    region = employee_info.get('region')
    
    if not branch_code:
        raise HTTPException(status_code=400, detail="Branch code not found in token")
    
    # If region not in token, derive it from branch
    if not region:
        region = get_region_from_branch(branch_code)
    
    result = {}
    
    # Find ZM at user's branch
    zm = find_zm_at_branch(branch_code)
    if zm:
        result['zone_manager'] = {
            'employee_id': zm.get('employee_id'),
            'branch': zm.get('branch'),
            'region': zm.get('region'),
            'role': zm.get('role'),
            'position_id': f"ZM_{branch_code}"
        }
    
    # Find RM in user's region
    rm = find_rm_in_region(region)
    if rm:
        result['regional_manager'] = {
            'employee_id': rm.get('employee_id'),
            'branch': rm.get('branch'),
            'region': rm.get('region'),
            'role': rm.get('role'),
            'position_id': f"RM_{region}"
        }
    
    # Find SDM
    sdm = find_sdm()
    if sdm:
        result['sales_director_manager'] = {
            'employee_id': sdm.get('employee_id'),
            'branch': sdm.get('branch'),
            'region': sdm.get('region'),
            'role': sdm.get('role'),
            'position_id': "SDM_GLOBAL"
        }
    
    return result


@router.get("/resolve/{position_id}")
async def resolve_position(position_id: str):
    """
    Resolve a position ID (like ZM_03TS, RM_BE) to actual employee information.
    
    Example:
        GET /api/approver-info/resolve/ZM_03TS
        Returns: {"employee_id": "20785", "branch": "03TS", "region": "BE", "role": "ZM"}
    """
    employee = resolve_approver_position(position_id)
    
    if not employee:
        raise HTTPException(
            status_code=404,
            detail=f"No employee found for position: {position_id}"
        )
    
    return employee


@router.get("/all-zms")
async def get_all_zone_managers():
    """Get all Zone Managers in the system"""
    zms = get_all_zms()
    return {"zone_managers": zms}


@router.get("/all-rms")
async def get_all_regional_managers():
    """Get all Regional Managers in the system"""
    rms = get_all_rms()
    return {"regional_managers": rms}


@router.get("/zm-at-branch/{branch_code}")
async def get_zm_at_branch(branch_code: str):
    """Get Zone Manager at a specific branch"""
    zm = find_zm_at_branch(branch_code)
    
    if not zm:
        raise HTTPException(
            status_code=404,
            detail=f"No Zone Manager found at branch: {branch_code}"
        )
    
    return zm


@router.get("/rm-in-region/{region_code}")
async def get_rm_in_region(region_code: str):
    """Get Regional Manager in a specific region"""
    rm = find_rm_in_region(region_code)
    
    if not rm:
        raise HTTPException(
            status_code=404,
            detail=f"No Regional Manager found in region: {region_code}"
        )
    
    return rm
