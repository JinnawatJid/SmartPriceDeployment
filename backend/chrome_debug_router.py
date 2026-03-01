import subprocess
import os
from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter(prefix="/api/chrome-debug", tags=["Chrome Debug"])


@router.post("/start")
async def start_chrome_debug():
    """
    เปิด Chrome ด้วย remote debugging mode
    """
    try:
        # หา path ของ start_chrome_debug.bat
        bat_file = Path(__file__).parent.parent / "start_chrome_debug.bat"
        
        if not bat_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"ไม่พบไฟล์ start_chrome_debug.bat ที่ {bat_file}"
            )
        
        # รัน bat file แบบ background (ไม่รอให้เสร็จ)
        subprocess.Popen(
            [str(bat_file)],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return {
            "success": True,
            "message": "เปิด Chrome debug mode สำเร็จ"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"เกิดข้อผิดพลาดในการเปิด Chrome: {str(e)}"
        )
