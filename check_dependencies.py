#!/usr/bin/env python3
"""
Script สำหรับตรวจสอบว่าติดตั้ง dependencies ครบหรือไม่
รันด้วย: python check_dependencies.py
"""

import sys

def check_module(module_name, package_name=None):
    """ตรวจสอบว่ามี module หรือไม่"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {package_name} - ติดตั้งแล้ว")
        return True
    except ImportError:
        print(f"❌ {package_name} - ยังไม่ได้ติดตั้ง (รัน: pip install {package_name})")
        return False

def main():
    print("=" * 60)
    print("🔍 ตรวจสอบ Python Dependencies")
    print("=" * 60)
    print()
    
    # รายการ dependencies ที่ต้องการ
    dependencies = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("selenium", "selenium"),
        ("playwright", "playwright"),  # optional
        ("pydantic", "pydantic"),
        ("sqlalchemy", "sqlalchemy"),
        ("pymssql", "pymssql"),
        ("pandas", "pandas"),
        ("openpyxl", "openpyxl"),
        ("requests", "requests"),
        ("python-dotenv", "python-dotenv"),
        ("jinja2", "jinja2"),
        ("weasyprint", "weasyprint"),
    ]
    
    missing = []
    installed = []
    
    for module, package in dependencies:
        if check_module(module, package):
            installed.append(package)
        else:
            missing.append(package)
    
    print()
    print("=" * 60)
    print("📊 สรุปผลการตรวจสอบ")
    print("=" * 60)
    print(f"✅ ติดตั้งแล้ว: {len(installed)} packages")
    print(f"❌ ยังไม่ได้ติดตั้ง: {len(missing)} packages")
    print()
    
    if missing:
        print("🔧 คำสั่งติดตั้ง packages ที่ขาด:")
        print(f"   pip install {' '.join(missing)}")
        print()
        print("หรือติดตั้งจาก requirements.txt:")
        print("   pip install -r backend/requirements.txt")
        return 1
    else:
        print("🎉 ติดตั้ง dependencies ครบถ้วนแล้ว!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
