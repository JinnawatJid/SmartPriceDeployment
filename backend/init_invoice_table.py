"""
สคริปต์สำหรับสร้างตาราง Invoice ใน MSSQL และดึงข้อมูลจาก D365 API
ตารางนี้เก็บทุก line item ตามชื่อฟิลด์ที่ API ส่งมา
"""
import pyodbc
import requests
import pandas as pd
from datetime import datetime, timedelta
from config.db_mssql import get_mssql_conn
from config.config_external_api import INVOICE_API_URL, INVOICE_API_HEADERS


def create_invoice_table():
    """สร้างตาราง Invoice ใน MSSQL (เก็บทุก line item)"""
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    # ลบตารางเก่าถ้ามี (ระวัง: จะลบข้อมูลทั้งหมด)
    drop_sql = """
    IF OBJECT_ID('dbo.Invoice', 'U') IS NOT NULL
        DROP TABLE dbo.Invoice;
    """
    
    # สร้างตารางใหม่ - ตามชื่อฟิลด์ที่ API ส่งมา
    create_sql = """
    CREATE TABLE dbo.Invoice (
        id INT IDENTITY(1,1) PRIMARY KEY,
        Document_No NVARCHAR(50) NOT NULL,
        Order_No NVARCHAR(50),
        customer_code NVARCHAR(50),
        Sell_to_Customer_Name NVARCHAR(255),
        Posting_Date DATE,
        sku NVARCHAR(100),
        Description NVARCHAR(500),
        Variant_Code NVARCHAR(50),
        Quantity DECIMAL(18, 2),
        Unit_of_Measure NVARCHAR(20),
        Unit_Price DECIMAL(18, 2),
        Line_Amount DECIMAL(18, 2),
        Line_Amount_Include_VAT DECIMAL(18, 2),
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
    """
    
    # สร้าง index สำหรับการค้นหาที่ใช้ใน router
    index_sql = """
    CREATE INDEX idx_invoice_document_no ON dbo.Invoice(Document_No);
    CREATE INDEX idx_invoice_customer_code ON dbo.Invoice(customer_code);
    CREATE INDEX idx_invoice_posting_date ON dbo.Invoice(Posting_Date);
    CREATE INDEX idx_invoice_sku ON dbo.Invoice(sku);
    CREATE INDEX idx_invoice_sku_customer ON dbo.Invoice(sku, customer_code, Posting_Date);
    """
    
    try:
        print("🗑️  ลบตารางเก่า (ถ้ามี)...")
        cursor.execute(drop_sql)
        conn.commit()
        
        print("📋 สร้างตาราง Invoice...")
        cursor.execute(create_sql)
        conn.commit()
        
        print("🔍 สร้าง indexes...")
        for idx_sql in index_sql.split(';'):
            if idx_sql.strip():
                cursor.execute(idx_sql)
        conn.commit()
        
        print("✅ สร้างตารางสำเร็จ!")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def load_and_insert_invoices():
    """ดึงข้อมูล Invoice และบันทึกทันทีทีละ batch (เร็วขึ้นด้วย executemany)"""
    print(f"\n📥 กำลังดึงและบันทึกข้อมูล Invoice...")
    
    page = 1
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
            
            try:
                print(f"  📄 กำลังดึงหน้า {page}...", end=" ")
                resp = requests.post(
                    INVOICE_API_URL,
                    json=payload,
                    headers=INVOICE_API_HEADERS,
                    timeout=30,
                )
                
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data") or []
                
                if not items:
                    print("(ไม่มีข้อมูล)")
                    break
                
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
                        if len(batch_values) == 0:  # แสดง error แค่รายการแรก
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
                print(f"→ บันทึกแล้ว {success_count} รายการ (รวม: {total_inserted:,})")
                
                # ถ้าได้น้อยกว่า size แสดงว่าหมดแล้ว
                if len(items) < size:
                    print(f"  ✅ ดึงข้อมูลครบแล้ว (หน้าสุดท้าย)")
                    break
                
                page += 1
                if page > max_page:
                    print(f"  ⚠️ ถึงขีดจำกัด {max_page} หน้าแล้ว")
                    break
                    
            except Exception as e:
                print(f"\n❌ Error loading page {page}: {e}")
                break
        
        print(f"\n✅ ดึงและบันทึกข้อมูลเสร็จสิ้น รวม {total_inserted:,} รายการ")
        return total_inserted
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️ ถูกหยุดโดยผู้ใช้")
        print(f"📊 ข้อมูลที่บันทึกไปแล้ว: {total_inserted:,} รายการ")
        conn.commit()  # Commit ข้อมูลที่เหลือ
        return total_inserted
        
    finally:
        cursor.close()
        conn.close()


def insert_invoices_to_db(invoices):
    """บันทึกข้อมูล Invoice ลงฐานข้อมูล (ฟังก์ชันนี้ไม่ใช้แล้ว - ใช้ load_and_insert_invoices แทน)"""
    pass


def verify_data():
    """ตรวจสอบข้อมูลที่บันทึก"""
    print("\n🔍 ตรวจสอบข้อมูลในตาราง...")
    
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        # นับจำนวนรายการทั้งหมด (line items)
        cursor.execute("SELECT COUNT(*) FROM dbo.Invoice")
        total = cursor.fetchone()[0]
        print(f"  📊 จำนวน Line Items ทั้งหมด: {total:,}")
        
        # นับจำนวน Invoice ที่ไม่ซ้ำ
        cursor.execute("SELECT COUNT(DISTINCT Document_No) FROM dbo.Invoice")
        unique_invoices = cursor.fetchone()[0]
        print(f"  📄 จำนวน Invoice ที่ไม่ซ้ำ: {unique_invoices:,}")
        
        # นับจำนวนลูกค้าที่ไม่ซ้ำ
        cursor.execute("SELECT COUNT(DISTINCT customer_code) FROM dbo.Invoice")
        unique_customers = cursor.fetchone()[0]
        print(f"  👥 จำนวนลูกค้าที่ไม่ซ้ำ: {unique_customers:,}")
        
        # นับจำนวน SKU ที่ไม่ซ้ำ
        cursor.execute("SELECT COUNT(DISTINCT sku) FROM dbo.Invoice")
        unique_skus = cursor.fetchone()[0]
        print(f"  📦 จำนวน SKU ที่ไม่ซ้ำ: {unique_skus:,}")
        
        # คำนวณยอดรวมทั้งหมด
        cursor.execute("SELECT SUM(Line_Amount_Include_VAT) FROM dbo.Invoice")
        total_amount = cursor.fetchone()[0] or 0
        print(f"  💰 ยอดรวมทั้งหมด: {total_amount:,.2f} บาท")
        
        # แสดงข้อมูลตัวอย่าง
        cursor.execute("""
            SELECT TOP 5 
                Document_No, Posting_Date, customer_code, 
                sku, Quantity, Unit_Price, Line_Amount_Include_VAT
            FROM dbo.Invoice
            ORDER BY Posting_Date DESC
        """)
        
        print("\n  📋 ตัวอย่างข้อมูล 5 รายการล่าสุด:")
        for row in cursor.fetchall():
            print(f"    {row[0]} | {row[1]} | {row[2]} | {row[3]} | Qty:{row[4]} | Price:{row[5]:,.2f} | Total:{row[6]:,.2f}")
        
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    """ฟังก์ชันหลัก"""
    print("=" * 60)
    print("🚀 เริ่มต้นการสร้างตาราง Invoice และดึงข้อมูล")
    print("=" * 60)
    
    try:
        # 1. สร้างตาราง
        create_invoice_table()
        
        # 2. ดึงและบันทึกทันทีทีละหน้า
        total = load_and_insert_invoices()
        
        # 3. ตรวจสอบข้อมูล
        verify_data()
        
        print("\n" + "=" * 60)
        print("✅ เสร็จสิ้นทุกขั้นตอน!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        raise


if __name__ == "__main__":
    main()
