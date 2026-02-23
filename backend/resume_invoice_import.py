"""
สคริปต์สำหรับบันทึก Invoice ต่อจากที่ค้างไว้
ดึงและบันทึกทันทีทีละหน้า (200 รายการ) เหมือน init_invoice_table.py
"""
import pyodbc
import requests
from datetime import datetime
from config.db_mssql import get_mssql_conn
from config.config_external_api import INVOICE_API_URL, INVOICE_API_HEADERS


def get_existing_count():
    """นับจำนวนรายการที่มีอยู่แล้วในฐานข้อมูล"""
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM dbo.Invoice")
        count = cursor.fetchone()[0]
        return count
    finally:
        cursor.close()
        conn.close()


def resume_import():
    """ดึงข้อมูลต่อและบันทึกทันทีทีละหน้า"""
    existing_count = get_existing_count()
    print(f"\n📊 มีข้อมูลอยู่แล้ว: {existing_count:,} รายการ")
    
    # คำนวณหน้าเริ่มต้นจากจำนวนที่มีอยู่
    start_page = (existing_count // 200) + 1
    print(f"📥 กำลังดึงข้อมูล Invoice ต่อจากหน้า {start_page}...")
    
    page = start_page
    size = 200
    max_page = 3000
    total_inserted = 0
    
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    # ⚡ เปิด fast_executemany เพื่อเพิ่มความเร็ว
    cursor.fast_executemany = True
    
    insert_sql = """
    INSERT INTO dbo.Invoice (
        Document_No, Order_No, customer_code, Sell_to_Customer_Name,
        Posting_Date, sku, Description, Variant_Code, Quantity,
        Unit_of_Measure, Unit_Price, Line_Amount, Line_Amount_Include_VAT
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        while True:
            # ดึงข้อมูล 1 หน้า
            payload = {"page": page, "size": size}
            
            # ⚡ Retry logic สำหรับ timeout
            max_retries = 3
            retry_count = 0
            items = None
            
            while retry_count < max_retries:
                try:
                    if retry_count > 0:
                        print(f"\n  🔄 ลองใหม่ครั้งที่ {retry_count}...", end=" ")
                    else:
                        print(f"  📄 กำลังดึงหน้า {page}...", end=" ")
                    
                    resp = requests.post(
                        INVOICE_API_URL,
                        json=payload,
                        headers=INVOICE_API_HEADERS,
                        timeout=60,  # เพิ่ม timeout เป็น 60 วินาที
                    )
                    
                    resp.raise_for_status()
                    data = resp.json()
                    items = data.get("data") or []
                    break  # สำเร็จ ออกจาก retry loop
                    
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"\n❌ Timeout หลังจากลอง {max_retries} ครั้ง - ข้ามหน้านี้")
                        items = []
                        break
                    print(f"⏱️ Timeout", end=" ")
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"\n❌ Error หลังจากลอง {max_retries} ครั้ง: {e}")
                        print(f"  ⏭️ ข้ามไปหน้าถัดไป...")
                        items = []
                        break
                    print(f"⚠️ Error: {e}", end=" ")
            
            if items is None:
                items = []
            
            if not items:
                if retry_count > 0:
                    # Error หรือ Timeout - ลองหน้าถัดไป
                    print(f"  ⏭️ ข้ามหน้า {page} ไปหน้าถัดไป")
                    page += 1
                    if page > max_page:
                        print(f"  ⚠️ ถึงขีดจำกัด {max_page} หน้าแล้ว")
                        break
                    continue
                else:
                    # ไม่มีข้อมูลจริงๆ
                    print("(ไม่มีข้อมูล)")
                    break
            
            # ✅ มีข้อมูล - บันทึกลงฐานข้อมูล
            print(f"✓ ได้ {len(items)} รายการ", end=" ")
            
            # เตรียมข้อมูลทั้งหมดก่อน insert
            batch_values = []
            for inv in items:
                try:
                    posting_date = inv.get("Posting_Date") or inv.get("Posting Date")
                    if posting_date:
                        try:
                            posting_date = datetime.fromisoformat(posting_date.replace('Z', '+00:00')).date()
                        except:
                            posting_date = None
                    
                    values = (
                        inv.get("Document_No") or inv.get("Document No."),
                        inv.get("Order_No") or inv.get("Order No."),
                        inv.get("customer_code"),
                        inv.get("Sell_to_Customer_Name") or inv.get("Sell-to Customer Name"),
                        posting_date,
                        inv.get("sku"),
                        inv.get("Description"),
                        inv.get("Variant_Code") or inv.get("Variant Code"),
                        float(inv.get("Quantity") or 0),
                        inv.get("Unit_of_Measure") or inv.get("Unit of Measure"),
                        float(inv.get("Unit_Price") or inv.get("Unit Price") or 0),
                        float(inv.get("Line_Amount") or inv.get("Amount") or 0),
                        float(inv.get("Line_Amount_Include_VAT") or inv.get("Amount Including VAT") or 0),
                    )
                    
                    batch_values.append(values)
                    
                except Exception as e:
                    if len(batch_values) == 0:
                        print(f"\n  ⚠️ Error preparing data: {e}")
            
            # ⚡ Insert ทั้ง batch ในครั้งเดียว (เร็วกว่ามาก!)
            if batch_values:
                cursor.executemany(insert_sql, batch_values)
                success_count = len(batch_values)
            else:
                success_count = 0
            
            # Commit ทันทีหลังบันทึกแต่ละหน้า
            conn.commit()
            total_inserted += success_count
            print(f"→ บันทึกแล้ว {success_count} รายการ (รวม: {existing_count + total_inserted:,})")
            
            # ถ้าได้น้อยกว่า size แสดงว่าหมดแล้ว
            if len(items) < size:
                print(f"  ✅ ดึงข้อมูลครบแล้ว (หน้าสุดท้าย)")
                break
            
            page += 1
            if page > max_page:
                print(f"  ⚠️ ถึงขีดจำกัด {max_page} หน้าแล้ว")
                break
        
        final_count = get_existing_count()
        print(f"\n✅ ดึงและบันทึกข้อมูลเสร็จสิ้น")
        print(f"📊 จำนวนรายการทั้งหมด: {final_count:,}")
        print(f"📈 เพิ่มขึ้น: {total_inserted:,} รายการ")
        return total_inserted
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️ ถูกหยุดโดยผู้ใช้")
        final_count = get_existing_count()
        print(f"📊 ข้อมูลที่บันทึกไปแล้ว: {final_count:,} รายการ")
        conn.commit()  # Commit ข้อมูลที่เหลือ
        return total_inserted
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Resume Invoice Import")
    print("=" * 60)
    
    try:
        # ดึงต่อจากที่ค้างไว้
        resume_import()
        
        print("\n" + "=" * 60)
        print("✅ เสร็จสิ้น!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        print(f"📊 ข้อมูลปัจจุบัน: {get_existing_count():,} รายการ")
