# invoice_cache_refresh.py
"""
Invoice Cache Refresh Job
ดึงข้อมูล invoice ทั้งหมดจาก D365 API และเก็บไว้ใน database
รันก่อน customer_cache_refresh เพื่อให้มีข้อมูล invoice พร้อมใช้
"""
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import requests
import pyodbc

from config.config_external_api import (
    INVOICE_API_URL,
    INVOICE_API_HEADERS,
)
from config.db_mssql import get_mssql_conn
from config.cache_config import (
    BATCH_SIZE,
    API_PAGE_SIZE,
    API_TIMEOUT,
)
from jobs.cache_logger import cache_logger


@dataclass
class InvoiceCacheRecord:
    """โครงสร้างข้อมูล invoice สำหรับ cache (ตามตารางที่มีอยู่)"""
    # Required fields (no default)
    document_no: str
    customer_code: str
    posting_date: date
    sku: str
    # Optional fields (with default)
    order_no: Optional[str] = ""
    sell_to_customer_name: Optional[str] = ""
    description: Optional[str] = ""
    variant_code: Optional[str] = ""
    quantity: float = 0.0
    unit_of_measure: Optional[str] = ""
    unit_price: float = 0.0
    line_amount: float = 0.0
    line_amount_include_vat: float = 0.0


@dataclass
class InvoiceJobResult:
    """ผลการรัน invoice cache job"""
    start_time: datetime
    end_time: datetime
    calculation_date: date
    invoices_processed: int = 0
    invoices_inserted: int = 0
    invoices_failed: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()


def load_all_invoices_from_d365(start_date: date, end_date: date) -> List[Dict]:
    """
    ดึงข้อมูล invoice ทั้งหมดจาก D365 API ตามช่วงวันที่
    
    Args:
        start_date: วันที่เริ่มต้น
        end_date: วันที่สิ้นสุด
    
    Returns:
        List of invoice records
    """
    rows = []
    page = 1
    max_page = 1000  # ป้องกัน infinite loop
    
    cache_logger.info(f"📥 Loading invoices from D365 API...")
    cache_logger.info(f"   Date range: {start_date} to {end_date}")
    
    date_from = start_date.isoformat()
    date_to = end_date.isoformat()
    
    while page <= max_page:
        payload = {
            "page": page,
            "size": API_PAGE_SIZE,
            "Posting Date": {"$gte": date_from, "$lte": date_to}
        }
        
        try:
            resp = requests.post(
                INVOICE_API_URL,
                json=payload,
                headers=INVOICE_API_HEADERS,
                timeout=API_TIMEOUT,
            )
            resp.raise_for_status()
            
            data = resp.json()
            items = data.get("data") or []
            
            if not items:
                cache_logger.info(f"  ✓ page={page}: No more data")
                break
            
            rows.extend(items)
            cache_logger.info(f"  ✓ page={page}: Loaded {len(items)} invoices (total: {len(rows)})")
            
            if len(items) < API_PAGE_SIZE:
                cache_logger.info("  ✓ Completed (last page)")
                break
            
            page += 1
            
        except Exception as e:
            cache_logger.error(f"  ❌ Error on page={page}: {e}")
            break
    
    cache_logger.info(f"📊 Total invoices loaded: {len(rows)}")
    return rows


def parse_invoice_record(invoice_data: Dict, calculation_date: date) -> Optional[InvoiceCacheRecord]:
    """
    แปลงข้อมูล invoice จาก API เป็น InvoiceCacheRecord
    
    Args:
        invoice_data: ข้อมูล invoice จาก API
        calculation_date: วันที่คำนวณ
    
    Returns:
        InvoiceCacheRecord หรือ None ถ้าข้อมูลไม่ครบ
    """
    try:
        # ข้อมูลที่จำเป็น (ใช้ field names ใหม่)
        document_no = invoice_data.get('Document No.') or invoice_data.get('document_no')
        customer_code = invoice_data.get('customer_code')  # ✅ NEW
        posting_date_str = invoice_data.get('Posting Date') or invoice_data.get('posting_date')
        sku = invoice_data.get('sku')  # ✅ NEW
        
        if not document_no or not customer_code or not posting_date_str:
            return None
        
        # แปลงวันที่
        try:
            if isinstance(posting_date_str, str):
                posting_date = datetime.fromisoformat(posting_date_str.replace("Z", "+00:00")).date()
            else:
                posting_date = posting_date_str
        except:
            return None
        
        # ข้อมูลเพิ่มเติม (ใช้ field names ใหม่)
        order_no = invoice_data.get('Order No.') or invoice_data.get('order_no') or ""
        sell_to_customer_name = invoice_data.get('Sell_to_Customer_Name') or ""  # ✅ NEW
        description = invoice_data.get('Description') or invoice_data.get('description') or ""
        variant_code = invoice_data.get('Variant_Code') or invoice_data.get('variant_code') or ""  # ✅ NEW
        unit_of_measure = invoice_data.get('Unit of Measure') or invoice_data.get('unit_of_measure') or ""
        
        # ตัวเลข (ใช้ field names ใหม่)
        try:
            quantity = float(invoice_data.get('Quantity') or invoice_data.get('quantity') or 0)
        except:
            quantity = 0.0
        
        try:
            unit_price = float(invoice_data.get('Unit_Price') or invoice_data.get('unit_price') or 0)  # ✅ NEW
        except:
            unit_price = 0.0
        
        try:
            line_amount = float(invoice_data.get('Line_Amount') or invoice_data.get('line_amount') or 0)  # ✅ NEW
        except:
            line_amount = 0.0
        
        try:
            line_amount_vat = float(invoice_data.get('Line_Amount_Include_VAT') or 
                                   invoice_data.get('amount_including_vat') or 0)  # ✅ NEW
        except:
            line_amount_vat = 0.0
        
        return InvoiceCacheRecord(
            document_no=document_no,
            order_no=order_no,
            customer_code=customer_code,
            sell_to_customer_name=sell_to_customer_name,
            posting_date=posting_date,
            sku=sku,
            description=description,
            variant_code=variant_code,
            quantity=quantity,
            unit_of_measure=unit_of_measure,
            unit_price=unit_price,
            line_amount=line_amount,
            line_amount_include_vat=line_amount_vat
        )
        
    except Exception as e:
        cache_logger.warning(f"  ⚠️ Failed to parse invoice: {e}")
        return None


def upsert_invoice_batch(invoices: List[InvoiceCacheRecord], conn: pyodbc.Connection) -> int:
    """
    บันทึก invoice batch ลง database (ใช้ตารางที่มีอยู่แล้ว)
    
    Args:
        invoices: รายการ invoice records
        conn: Database connection
    
    Returns:
        จำนวน records ที่บันทึกสำเร็จ
    """
    if not invoices:
        return 0
    
    cursor = conn.cursor()
    success_count = 0
    
    # ใช้ MERGE เพื่อ upsert (ตามโครงสร้างตารางที่มีอยู่)
    # ตาราง Invoice มี created_at และ updated_at แทน calculation_date และ last_updated
    merge_sql = """
    MERGE INTO Invoice AS target
    USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) 
        AS source (Document_No, Order_No, customer_code, Sell_to_Customer_Name,
                   Posting_Date, sku, Description, Variant_Code, Quantity,
                   Unit_of_Measure, Unit_Price, Line_Amount, Line_Amount_Include_VAT,
                   updated_at)
    ON target.Document_No = source.Document_No AND target.sku = source.sku
    WHEN MATCHED THEN
        UPDATE SET
            Order_No = source.Order_No,
            customer_code = source.customer_code,
            Sell_to_Customer_Name = source.Sell_to_Customer_Name,
            Posting_Date = source.Posting_Date,
            Description = source.Description,
            Variant_Code = source.Variant_Code,
            Quantity = source.Quantity,
            Unit_of_Measure = source.Unit_of_Measure,
            Unit_Price = source.Unit_Price,
            Line_Amount = source.Line_Amount,
            Line_Amount_Include_VAT = source.Line_Amount_Include_VAT,
            updated_at = source.updated_at
    WHEN NOT MATCHED THEN
        INSERT (Document_No, Order_No, customer_code, Sell_to_Customer_Name,
                Posting_Date, sku, Description, Variant_Code, Quantity,
                Unit_of_Measure, Unit_Price, Line_Amount, Line_Amount_Include_VAT,
                created_at, updated_at)
        VALUES (source.Document_No, source.Order_No, source.customer_code,
                source.Sell_to_Customer_Name, source.Posting_Date, source.sku,
                source.Description, source.Variant_Code, source.Quantity,
                source.Unit_of_Measure, source.Unit_Price, source.Line_Amount,
                source.Line_Amount_Include_VAT, source.updated_at, source.updated_at);
    """
    
    for invoice in invoices:
        try:
            cursor.execute(merge_sql, (
                invoice.document_no,
                invoice.order_no or None,
                invoice.customer_code,
                invoice.sell_to_customer_name or None,
                invoice.posting_date,
                invoice.sku,
                invoice.description or None,
                invoice.variant_code or None,
                invoice.quantity,
                invoice.unit_of_measure or None,
                invoice.unit_price,
                invoice.line_amount,
                invoice.line_amount_include_vat,
                datetime.now()
            ))
            success_count += 1
        except Exception as e:
            cache_logger.error(f"  ❌ Failed to upsert invoice {invoice.document_no}: {e}")
    
    conn.commit()
    cursor.close()
    
    return success_count


def run_invoice_cache_refresh(months: int = 6) -> InvoiceJobResult:
    """
    รัน invoice cache refresh job
    
    Args:
        months: จำนวนเดือนย้อนหลังที่ต้องการดึง (default: 6)
    
    Returns:
        InvoiceJobResult
    """
    start_time = datetime.now()
    calculation_date = date.today()
    
    cache_logger.info("=" * 60)
    cache_logger.info("🚀 Starting Invoice Cache Refresh Job")
    cache_logger.info(f"   Start Time: {start_time}")
    cache_logger.info(f"   Calculation Date: {calculation_date}")
    cache_logger.info(f"   Months: {months}")
    cache_logger.info("=" * 60)
    
    result = InvoiceJobResult(
        start_time=start_time,
        end_time=start_time,
        calculation_date=calculation_date
    )
    
    try:
        # คำนวณช่วงวันที่
        end_date = calculation_date
        start_date = calculation_date - timedelta(days=months * 31)
        
        # ดึงข้อมูล invoice
        invoices_data = load_all_invoices_from_d365(start_date, end_date)
        
        if not invoices_data:
            cache_logger.warning("⚠️ No invoices loaded from API")
            result.end_time = datetime.now()
            return result
        
        # แปลงและบันทึกข้อมูล
        conn = get_mssql_conn()
        batch = []
        
        for idx, inv_data in enumerate(invoices_data, 1):
            try:
                invoice_record = parse_invoice_record(inv_data, calculation_date)
                
                if not invoice_record:
                    result.invoices_failed += 1
                    continue
                
                batch.append(invoice_record)
                result.invoices_processed += 1
                
                # บันทึก batch
                if len(batch) >= BATCH_SIZE:
                    success_count = upsert_invoice_batch(batch, conn)
                    result.invoices_inserted += success_count
                    cache_logger.info(f"  ✓ Processed {result.invoices_processed}/{len(invoices_data)} invoices")
                    batch = []
                
            except Exception as e:
                cache_logger.error(f"  ❌ Error processing invoice {idx}: {e}")
                result.invoices_failed += 1
                result.errors.append(f"Invoice {idx}: {str(e)}")
        
        # บันทึก batch สุดท้าย
        if batch:
            success_count = upsert_invoice_batch(batch, conn)
            result.invoices_inserted += success_count
        
        conn.close()
        
    except Exception as e:
        cache_logger.error(f"❌ Critical error: {e}")
        result.errors.append(f"Critical: {str(e)}")
    
    result.end_time = datetime.now()
    
    cache_logger.info("=" * 60)
    cache_logger.info("✅ Invoice Cache Refresh Job Completed")
    cache_logger.info(f"   Duration: {result.duration_seconds:.2f} seconds")
    cache_logger.info(f"   Invoices Processed: {result.invoices_processed}")
    cache_logger.info(f"   Invoices Inserted: {result.invoices_inserted}")
    cache_logger.info(f"   Invoices Failed: {result.invoices_failed}")
    cache_logger.info("=" * 60)
    
    return result
