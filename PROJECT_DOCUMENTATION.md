# เอกสารโครงสร้างโปรเจกต์ Smart Pricing System

## ภาพรวมระบบ

### ระบบทำอะไร
Smart Pricing System เป็นระบบจัดการใบเสนอราคาอัจฉริยะสำหรับธุรกิจจำหน่ายวัสดุก่อสร้าง โดยเฉพาะกระจก อลูมิเนียม ยิปซั่ม และอุปกรณ์ก่อสร้างอื่นๆ ระบบช่วยให้พนักงานขายสามารถ:
- ค้นหาข้อมูลลูกค้าและประวัติการซื้อ
- เลือกสินค้าจากหมวดหมู่ต่างๆ พร้อมระบบกรองแบบ cascading
- คำนวณราคาอัตโนมัติตามเงื่อนไขลูกค้า (ยอดซื้อสะสม, ประเภทลูกค้า)
- คำนวณค่าขนส่งตามระยะทาง ประเภทรถ และกำไรสินค้า
- สร้างและจัดการใบเสนอราคา (Draft/Complete)
- พิมพ์ใบเสนอราคาเป็น PDF
- อัปเดตราคาสินค้าจากไฟล์ Excel (สำหรับผู้จัดการ)

### สถาปัตยกรรมโดยรวม
```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Vite + React 19 + TailwindCSS                        │
│  - Context API (Auth, Quote)                            │
│  - Axios สำหรับเรียก API                                 │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP/REST API
┌────────────────┴────────────────────────────────────────┐
│                 Backend (FastAPI)                        │
│  - Python 3.12 + FastAPI                                │
│  - Pandas สำหรับประมวลผลข้อมูล                          │
│  - WeasyPrint สำหรับสร้าง PDF                           │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────┴──────┐  ┌──────┴────────┐
│   SQLite     │  │  External API │
│  (Local DB)  │  │  (D365 BC)    │
│  - Items     │  │  - Customer   │
│  - Quote     │  │  - Invoice    │
│  - Employee  │  │               │
└──────────────┘  └───────────────┘
```

**การ Deploy:**
- **Development:** Frontend (Vite dev server) + Backend (Uvicorn)
- **Production:** Docker Compose (2 containers: frontend nginx + backend)
- **Native App:** PyInstaller (รวม backend + frontend dist ในไฟล์ .exe เดียว)

---


## Backend (Python/FastAPI)

### โครงสร้างโฟลเดอร์
```
backend/
├── main.py                    # Entry point หลัก
├── requirements.txt           # Dependencies
├── Dockerfile                 # Docker image config
├── .env                       # Environment variables
│
├── api/                       # API Routers สำหรับ Business Central
│   ├── bc_config.py          # การตั้งค่า BC API
│   ├── bc_client.py          # HTTP Client สำหรับ BC
│   ├── bc_sales_order.py     # Sales Order API
│   ├── bc_sales_quote.py     # Sales Quote API
│   └── router_sq.py          # Sales Queue Router
│
├── config/                    # Configuration
│   ├── config_external_api.py # External API config
│   ├── db_sqlite.py          # SQLite connection
│   ├── db_mssql.py           # MS SQL connection
│   └── data/                 # ไฟล์ข้อมูล Excel/SQLite
│
├── schemas/                   # Pydantic Models
│   └── cross_sell.py         # Cross-sell schemas
│
├── services/                  # Business Logic
│   ├── cross_sell_service.py # Cross-sell logic
│   └── sku_enricher.py       # SKU parsing & enrichment
│
├── utils/                     # Utilities
│   ├── baht_text.py          # แปลงตัวเลขเป็นตัวอักษรไทย
│   └── glass_sku.py          # Glass SKU utilities
│
└── [Router Files]             # API Routers (รายละเอียดด้านล่าง)
    ├── customer.py
    ├── items.py
    ├── employees.py
    ├── login.py
    ├── pricing_router.py
    ├── shipping.py
    ├── quotation.py
    ├── cross_sell_router.py
    ├── invoice_router.py
    ├── item_update.py
    ├── customer_analytics.py
    └── products_router.py
```

---


### API Routes (Router Files)

#### 1. **main.py** - Entry Point หลัก
**หน้าที่:** จุดเริ่มต้นของ Backend, รวม routers ทั้งหมด, serve static files

**ฟังก์ชันสำคัญ:**
- `app = FastAPI()` - สร้าง FastAPI application
- `app.include_router()` - รวม routers ทั้งหมด
- `@app.post("/api/print/quotation")` - พิมพ์ใบเสนอราคาเป็น PDF
- `@app.get("/{catchall:path}")` - Serve React SPA (fallback routing)
- `@app.get("/api/health")` - Health check endpoint

**Middleware:**
- CORS: อนุญาตทุก origin (สำหรับ offline/docker)
- Jinja2: โหลด template สำหรับ PDF

**Export:** `app` (FastAPI instance)

---

#### 2. **customer.py** - Customer & Invoice API
**หน้าที่:** จัดการข้อมูลลูกค้าและ Invoice จาก D365 Business Central

**ฟังก์ชันสำคัญ:**

1. `load_customer_from_api()` → `pd.DataFrame`
   - โหลดข้อมูลลูกค้าทั้งหมดจาก D365 API
   - ใช้ pagination (500 รายการ/หน้า)
   - มี cache 15 นาที
   - Return: DataFrame ที่มี columns: Customer, Name, Tel, Gen Bus, Payment Terms Code, Tax No., Customer Date

2. `load_invoice_by_customer_api(customer_code: str)` → `list`
   - โหลด Invoice 6 เดือนย้อนหลังของลูกค้า
   - Filter ด้วย customer_code และ Posting Date
   - Return: list ของ invoice items

3. `classify_group(no: str)` → `str`
   - แยกประเภทสินค้าจากตัวอักษรแรกของ SKU
   - Return: G/A/S/Y/C/E

**API Endpoints:**

| Method | Path | Parameters | Response | หน้าที่ |
|--------|------|-----------|----------|---------|
| GET/POST | `/api/customer/test-connection` | - | `{status, status_code, api_url}` | ทดสอบการเชื่อมต่อ D365 |
| GET/POST | `/api/customer/search` | `code`, `phone`, `name` | `{id, name, tax_no, phone, accum_6m, frequency, sales_g, sales_a, ...}` | ค้นหาลูกค้า + คำนวณยอดขาย 6 เดือน |
| GET/POST | `/api/customer/search-list` | `q` (min 1 char) | `[{id, name, phone, tax_no}]` | Autocomplete dropdown (max 15 รายการ) |

**Cache Strategy:**
- Customer data: 15 นาที (TTL 900s)
- Search results: 1 นาที (max 100 รายการ)

**Export:** `router` (APIRouter with prefix="/api/customer")

---


#### 3. **items.py** - Items API (MS SQL)
**หน้าที่:** จัดการข้อมูลสินค้าจาก MS SQL Server (Items_Test table)

**ฟังก์ชันสำคัญ:**

1. `row_to_item(row)` → `dict`
   - แปลง database row เป็น API response format
   - Return: `{sku, sku2, name, inventory, unit, category, isVariant, prices: {R1, R2, W1, W2}, pkg_size, product_weight, sqft_sheet, product_group, product_sub_group, alternate_names}`

**API Endpoints:**

| Method | Path | Parameters | Response | หน้าที่ |
|--------|------|-----------|----------|---------|
| GET | `/api/items/categories/list` | - | `[{name, count}]` | รายการหมวดหมู่สินค้า |
| GET | `/api/items/categories/{category}/list` | `limit`, `offset`, `brand`, `group`, `subGroup`, `color`, `thickness`, `character`, `search` | `{items: [], limit, offset, count, total}` | รายการสินค้าแบบ light (pagination + filter) |
| GET | `/api/items/{sku}` | - | `{sku, name, prices, ...}` | รายละเอียดสินค้าเต็ม (รองรับทั้ง No. และ No. 2) |
| GET | `/api/items/related/{sku}` | `limit` (default 50) | `{items: [], total, product_group}` | สินค้าที่อยู่ใน Product Group เดียวกัน |
| GET | `/api/items/search` | `q` (min 3 chars) | `[{...}]` | ค้นหาสินค้า (max 50 รายการ) |
| GET | `/api/items/categories/{category}/filter-options` | `brand`, `group`, `subGroup`, `color`, `thickness`, `character` | `{brand: [], group: [], subGroup: [], color: [], thickness: [], character: []}` | ตัวเลือก filter แบบ cascading |

**SKU Pattern Support:**
- **Aluminium (A):** ABBGGSSSCCTT (12 chars)
- **C-Line (C):** CBBGGSSSCCTT (12 chars)
- **Accessories (E):** EBBBGGSSCCX (11 chars)
- **Sealant (S):** SBBGGSSSCC (10 chars)
- **Gypsum (Y):** YBBGGSCCCTT... (18 chars)

**Export:** `router` (APIRouter with prefix="/api/items")

---

#### 4. **employees.py** - Employees API (SQLite)
**หน้าที่:** จัดการข้อมูลพนักงานจาก SQLite

**ฟังก์ชันสำคัญ:**

1. `load_employees_sqlite()` → `pd.DataFrame`
   - โหลดข้อมูลพนักงานจาก SQLite
   - Clean ข้อมูล (ลบ NaN, None)
   - Return: DataFrame ที่มี columns: empCode, empName, branchCode

**API Endpoints:**

| Method | Path | Parameters | Response | หน้าที่ |
|--------|------|-----------|----------|---------|
| GET | `/api/employees` | `q`, `branch`, `page`, `page_size` | `{meta: {page, page_size, total, pages}, data: [{id, name, branchId}]}` | รายการพนักงาน (pagination) |
| GET | `/api/employees/{code}` | - | `{id, name, branchId}` | ข้อมูลพนักงานตามรหัส |

**Export:** `router` (APIRouter with prefix="/api/employees")

---

#### 5. **login.py** - Authentication API (SQLite)
**หน้าที่:** จัดการการ login ด้วย JWT

**ฟังก์ชันสำคัญ:**

1. `load_employee(code: str)` → `dict | None`
   - ค้นหาพนักงานจาก SQLite
   - Return: `{id, name, branchId}` หรือ None

**API Endpoints:**

| Method | Path | Body | Response | หน้าที่ |
|--------|------|------|----------|---------|
| POST | `/api/login` | `{employeeCode}` | `{token, employee: {id, name, branchId}}` | Login และสร้าง JWT token |

**JWT Config:**
- Secret: `JWT_SECRET` (env variable)
- Algorithm: HS256
- Expire: 12 ชั่วโมง

**Export:** `router` (APIRouter with prefix="/api/login")

---


#### 6. **pricing_router.py** - Pricing Calculation API
**หน้าที่:** คำนวณราคาสินค้าตามเงื่อนไขลูกค้า (ยอดซื้อสะสม, ประเภทลูกค้า, payment terms)

**ฟังก์ชันสำคัญ:**

1. `load_items_by_skus(skus: list)` → `pd.DataFrame`
   - โหลดข้อมูลสินค้าจาก MS SQL ตาม SKU list
   - Return: DataFrame ที่มีราคา R1, R2, W1, W2, pkg_size, product_weight

2. `round_up_050(x: float)` → `float`
   - ปัดราคาขึ้นทีละ 0.50 บาท (เช่น 12.3 → 12.5, 12.6 → 13.0)

**Models:**
- `CartItem`: `{sku, qty, name, price, sqft_sheet, pkg_size, cost, category, unit, product_weight, relevantSales}`
- `PricingRequest`: `{customerData, deliveryType, cart: [CartItem]}`

**API Endpoints:**

| Method | Path | Body | Response | หน้าที่ |
|--------|------|------|----------|---------|
| POST | `/api/pricing/calculate` | `PricingRequest` | `{items: [{sku, qty, UnitPrice, price_per_sheet, _LineTotal, _Tier_Z}], totals: {subtotal, vat, product_total, shippingCustomerPay, total, profit}, customer_tier}` | คำนวณราคาทั้งตะกร้า |

**Pricing Logic:**
1. **Default Mode** (ไม่มี customer code):
   - ใช้ราคา R2 โดยตรง
   - Tier_Z = 0

2. **Normal Mode** (มี customer code):
   - ใช้ `LevelPrice.py` คำนวณ tier ตามยอดขาย
   - ใช้ `price.py` คำนวณราคาตาม tier + delivery type + pkg_size
   - รองรับ payment terms (เครดิต)

**Special Cases:**
- **กระจก (G):** ราคาคำนวณเป็น บาท/ตร.ฟุต แต่แสดงเป็น บาท/แผ่น
- **อลูมิเนียม (A):** ราคาคำนวณเป็น บาท/กก. (UnitPrice × product_weight)
- **สินค้าอื่น:** ราคาเป็น บาท/หน่วย

**Export:** `router` (APIRouter with prefix="/api/pricing")

---

#### 7. **shipping.py** - Shipping Cost Calculation API
**หน้าที่:** คำนวณค่าขนส่งตามระยะทาง, ประเภทรถ, และกำไรสินค้า

**ฟังก์ชันสำคัญ:**

1. `load_items_by_skus(skus: list)` → `pd.DataFrame`
   - โหลด cost (RE) จาก MS SQL

2. `compute_profit_from_cart(cart: List[CartLine])` → `(float, bool)`
   - คำนวณกำไรจากตะกร้าสินค้า
   - Return: (profit, has_missing_cost)

3. `_calculate_shipping_cost(...)` → `dict`
   - คำนวณค่าขนส่งตามสูตร:
     - `fuel_cost = (distance / fuel_rate) × fuel_price`
     - `fix_cost = (travel_hours + unload_hours) × fix_cost_per_hour`
     - `labor_cost = (72 + 55 × staff_count) × (travel_hours + unload_hours)`
     - `shipping_cost = fuel_cost + fix_cost + labor_cost`
     - `company_pay = min(shipping_cost, profit × 0.05)`
     - `customer_pay = shipping_cost - company_pay`

**Vehicle Config:**
| ประเภทรถ | fuel_rate (km/L) | avg_speed (km/h) | fix_cost (บาท/ชม.) |
|---------|------------------|------------------|-------------------|
| PICKUP | 10 | 50 | 36 |
| 4 ล้อใหญ่ | 9.5 | 45 | 46 |
| 6 ล้อจิ๋ว | 9.0 | 45 | 58 |
| 6 ล้อเล็ก | 7.0 | 45 | 74 |
| 6 ล้อใหญ่ | 5.0 | 45 | 90 |
| 10 ล้อ | 4.5 | 40 | 148 |

**API Endpoints:**

| Method | Path | Body | Response | หน้าที่ |
|--------|------|------|----------|---------|
| POST | `/api/shipping/calculate` | `{vehicle_type, distance_km, unload_hours, staff_count, profit}` | `{vehicle_type, travel_hours, fuel_cost, fix_cost, labor_cost, shipping_cost, shipping_cap, company_pay, customer_pay}` | คำนวณค่าขนส่งจาก profit ที่ระบุ |
| POST | `/api/shipping/calculate_from_cart` | `{vehicle_type, distance_km, unload_hours, staff_count, cart: [CartLine]}` | `{..., profit_for_shipping, has_missing_cost}` | คำนวณค่าขนส่งจากตะกร้าสินค้า |

**Export:** `router` (APIRouter with prefix="/api/shipping")

---


#### 8. **quotation.py** - Quotation Management API (SQLite)
**หน้าที่:** จัดการใบเสนอราคา (สร้าง, แก้ไข, ลบ, ดูรายการ)

**ฟังก์ชันสำคัญ:**

1. `_generate_quote_no(branch_code: str)` → `str`
   - สร้างเลขที่ใบเสนอราคา format: `BSQT-2502/0001`
   - B = branch code (2 ตัวท้าย), 25 = ปี, 02 = เดือน, 0001 = running number

2. `_build_line_from_payload(item: dict)` → `dict`
   - แปลง item จาก frontend เป็น format สำหรับบันทึก database
   - คำนวณ lineTotal ตาม category (กระจกใช้ sqft_sheet)

**API Endpoints:**

| Method | Path | Body/Params | Response | หน้าที่ |
|--------|------|------------|----------|---------|
| POST | `/api/quotation` | `{employee, customer, cart, totals, deliveryType, needTaxInvoice, note, status}` | `{id, quoteNo, status}` | สร้างใบเสนอราคาใหม่ |
| PUT | `/api/quotation/{quote_no}` | `{...}` (เหมือน POST) | `{id, quoteNo, status}` | แก้ไขใบเสนอราคา |
| GET | `/api/quotation` | `status` (optional) | `[{quoteNo, customer, employee, createdAt, updatedAt, totals, cart}]` | รายการใบเสนอราคาทั้งหมด |
| GET | `/api/quotation/{quote_no}` | - | `{header: {...}, lines: [{...}]}` | รายละเอียดใบเสนอราคา |
| DELETE | `/api/quotation/{quote_no}` | - | `{cancelled: quote_no}` | ยกเลิกใบเสนอราคา (เปลี่ยน status เป็น cancelled) |

**Database Tables:**
- `Quote_Header`: เก็บข้อมูลหัวใบเสนอราคา
- `Quote_Line`: เก็บรายการสินค้าในใบเสนอราคา

**Excel Export:**
- บันทึกลง `QuoteTemplate.xlsx` ทุกครั้งที่สร้าง/แก้ไข (สำหรับ backup)

**Export:** `router` (APIRouter with prefix="/api/quotation")

---

#### 9. **cross_sell_router.py** - Cross-Sell Recommendation API
**หน้าที่:** แนะนำสินค้าเพิ่มเติมตาม Product Group ที่เลือก

**API Endpoints:**

| Method | Path | Body | Response | หน้าที่ |
|--------|------|------|----------|---------|
| POST | `/api/cross-sell` | `{products: [{productGroup, productSubGroup}]}` | `[{displayName, ruleNo, ruleType, ruleGroup}]` | แนะนำสินค้าเพิ่มเติม |

**Logic:**
1. ตรวจสอบ Product Group ในตะกร้า
2. หา rule ที่ match (จาก Rule table)
3. แนะนำสินค้า main ที่ยังไม่มี หรือ sub items

**Export:** `cross_sell_router` (APIRouter with prefix="/api/cross-sell")

---

#### 10. **invoice_router.py** - Invoice API (SQLite)
**หน้าที่:** ดูข้อมูล Invoice และประวัติราคาสินค้า

**API Endpoints:**

| Method | Path | Parameters | Response | หน้าที่ |
|--------|------|-----------|----------|---------|
| GET | `/api/invoice/list` | `document_no`, `customer_no`, `posting_date`, `limit` | `[{...}]` | รายการ Invoice |
| GET | `/api/invoice/{document_no}` | - | `{header: {...}, lines: [{...}]}` | รายละเอียด Invoice |
| GET | `/api/invoice/item-price-history` | `sku`, `customerCode`, `limit` | `[{invoiceNo, date, price, qty, unit}]` | ประวัติราคาสินค้าของลูกค้า |

**Export:** `router` (APIRouter with prefix="/api/invoice")

---

#### 11. **item_update.py** - Item Price Update API (SQLite)
**หน้าที่:** อัปเดตราคาสินค้าจากไฟล์ Excel (สำหรับผู้จัดการ)

**ฟังก์ชันสำคัญ:**

1. `_is_missing_excel_value(row, col)` → `bool`
   - ตรวจสอบว่าคอลัมน์ใน Excel ว่างหรือไม่

**API Endpoints:**

| Method | Path | Body | Response | หน้าที่ |
|--------|------|------|----------|---------|
| POST | `/api/item-update/upload` | `file` (Excel) | `{version_id, version_name, inserted_new_item, inserted_detail, skipped_blank, insert_warnings}` | Upload Excel และสร้าง draft version |
| GET | `/api/item-update/preview/{version_id}` | - | `[{sku, new_R1, new_R2, old_R1, old_R2, ...}]` | ดูตัวอย่างการเปลี่ยนแปลง |
| POST | `/api/item-update/activate/{version_id}` | - | `{status: "activated", version_id}` | Activate version (อัปเดตราคาจริง) |

**Excel Format:**
- Required columns: `No.`, `R1`, `R2`, `W1`, `W2`, `AlternateName`
- Optional: `No. 2`, `Description`, `Base Unit of Measure`, `Package Size`, etc.

**Database Tables:**
- `Item_Update_Version`: เก็บ version ของการอัปเดต
- `Item_Update_Version_Detail`: เก็บรายละเอียดการเปลี่ยนแปลงแต่ละ SKU

**Export:** `router` (APIRouter with prefix="/api/item-update")

---


#### 12. **customer_analytics.py** - Customer Analytics API
**หน้าที่:** วิเคราะห์ข้อมูลลูกค้าจาก Invoice (สำหรับทีมอื่น/เพื่อน)

**ฟังก์ชันสำคัญ:**

1. `load_invoice_by_customer_api(customer_code, months, anchor_date)` → `pd.DataFrame`
   - โหลด Invoice ย้อนหลังตามจำนวนเดือนที่กำหนด

2. `resolve_anchor_and_cutoff(inv, months, anchor_date)` → `(anchor, cutoff)`
   - กำหนดวันที่อ้างอิงและวันที่ตัด

**API Endpoints:**

| Method | Path | Parameters | Response | หน้าที่ |
|--------|------|-----------|----------|---------|
| GET | `/api/customer-analytics/monthly-summary` | `customer_code`, `months`, `anchor_date` | `{customer, anchor_date, months, monthly: [{month, amount}], total}` | ยอดขายรายเดือน |
| GET | `/api/customer-analytics/category-summary` | `customer_code`, `months`, `anchor_date` | `{customer, anchor_date, months, by_category: {G, A, S, Y, C, E}, relevant_category, relevant_sales}` | ยอดขายแยกตามประเภทสินค้า |

**Export:** `router` (APIRouter with prefix="/api/customer-analytics")

---

#### 13. **products_router.py** - Products API (Unified Router)
**หน้าที่:** API สำหรับสินค้าแต่ละประเภท (Aluminium, C-Line, Accessories, Sealant, Gypsum, Glass)

**ฟังก์ชันสำคัญ:**

1. `load_code_name_mapping(table_name)` → `dict`
   - โหลด mapping จาก SQLite (Code → Name) พร้อม cache

2. `_parse_by_slices(sku, slices, prefix, min_len)` → `dict`
   - แยก SKU เป็นส่วนๆ ตาม pattern (brand, group, subGroup, color, thickness)

3. `_apply_filters(df, filters, pad)` → `pd.DataFrame`
   - กรองข้อมูลตาม filter ที่เลือก

**Sub-Routers:**

##### 13.1 Aluminium Router (`/api/aluminium`)
- `GET /options` หรือ `/master`: ตัวเลือก filter (brands, groups, subGroups, colors, thickness)
- `GET /items`: รายการสินค้าอลูมิเนียม (filter ได้)

##### 13.2 C-Line Router (`/api/cline`)
- `GET /master`: ตัวเลือก filter
- `GET /options`: ตัวเลือกทั้งหมด (ไม่ filter)
- `GET /items`: รายการสินค้า C-Line

##### 13.3 Accessories Router (`/api/accessories`)
- `GET /master`: ตัวเลือก filter
- `GET /options`: ตัวเลือกทั้งหมด
- `GET /items`: รายการอุปกรณ์

##### 13.4 Sealant Router (`/api/sealant`)
- `GET /master`: ตัวเลือก filter
- `GET /options`: ตัวเลือกทั้งหมด
- `GET /items`: รายการซีลแลนท์

##### 13.5 Gypsum Router (`/api/gypsum`)
- `GET /master`: ตัวเลือก filter
- `GET /options`: ตัวเลือกทั้งหมด
- `GET /items`: รายการยิปซั่ม

##### 13.6 Glass Router (`/api/glass`)
- `GET /master`: ตัวเลือก filter
- `GET /items`: รายการกระจก
- `GET /semi-standard-sizes`: ขนาดกระจกมาตรฐาน
- มี cache 10 นาที

**Export:** `api_router` (APIRouter with prefix="/api")

---

### Services/Business Logic

#### 1. **services/cross_sell_service.py**
**หน้าที่:** Logic สำหรับแนะนำสินค้าเพิ่มเติม

**ฟังก์ชันสำคัญ:**

1. `match_rule(rule, product)` → `bool`
   - ตรวจสอบว่า product ตรงกับ rule หรือไม่
   - Match ด้วย Product Group และ/หรือ Product Sub Group

2. `get_cross_sell(products)` → `list`
   - รับ products ในตะกร้า
   - หา rule ที่ match
   - Return รายการสินค้าที่แนะนำ

**Export:** `get_cross_sell()`

---

#### 2. **services/sku_enricher.py**
**หน้าที่:** แยก SKU และเติมข้อมูล (brand name, group name, etc.)

**ฟังก์ชันสำคัญ:**

1. `load_mapping(table_name)` → `dict`
   - โหลด mapping table จาก SQLite (cached)

2. `parse_*_sku(sku)` → `dict`
   - แยก SKU ตาม pattern แต่ละประเภท
   - Variants: `parse_accessories_sku`, `parse_aluminium_sku`, `parse_cline_sku`, `parse_sealant_sku`, `parse_gypsum_sku`, `parse_glass_sku`

3. `enrich_*(sku)` → `dict`
   - เติมข้อมูล name จาก mapping
   - Variants: `enrich_accessories`, `enrich_aluminium`, `enrich_cline`, `enrich_sealant`, `enrich_gypsum`, `enrich_glass`

4. `enrich_by_category(category, sku)` → `dict`
   - Dispatcher function: เรียก enrich function ที่เหมาะสมตาม category

**Export:** `enrich_by_category()`, `load_mapping()`

---

### Utilities

#### 1. **utils/baht_text.py**
**หน้าที่:** แปลงตัวเลขเป็นตัวอักษรไทย (สำหรับพิมพ์ใบเสนอราคา)

**ฟังก์ชันสำคัญ:**

1. `baht_text(amount: float)` → `str`
   - แปลงจำนวนเงินเป็นตัวอักษรไทย
   - ตัวอย่าง: `1234.56` → `"หนึ่งพันสองร้อยสามสิบสี่บาทห้าสิบหกสตางค์"`

**Export:** `baht_text()`

---

### Configuration

#### 1. **config/config_external_api.py**
**หน้าที่:** การตั้งค่า External API (D365 Business Central)

**ตัวแปร:**
- `CUSTOMER_API_KEY`: API key สำหรับ Customer API
- `CUSTOMER_API_URL`: URL ของ Customer API
- `CUSTOMER_API_HEADERS`: Headers สำหรับ Customer API
- `INVOICE_API_URL`: URL ของ Invoice API
- `INVOICE_API_HEADERS`: Headers สำหรับ Invoice API

---

#### 2. **config/db_sqlite.py**
**หน้าที่:** SQLite connection

**ฟังก์ชันสำคัญ:**

1. `get_conn()` → `sqlite3.Connection`
   - สร้าง connection ไปยัง SQLite database
   - Database path: `config/data/Quetung.db`

**Export:** `get_conn()`

---

#### 3. **config/db_mssql.py**
**หน้าที่:** MS SQL Server connection

**ฟังก์ชันสำคัญ:**

1. `get_mssql_conn()` → `pyodbc.Connection`
   - สร้าง connection ไปยัง MS SQL Server
   - ใช้ Windows Authentication

**Export:** `get_mssql_conn()`

---


### API สำหรับ Business Central Integration

#### 1. **api/bc_config.py**
**หน้าที่:** การตั้งค่า Business Central API

**ตัวแปร:**
- BC API URL, credentials, headers

---

#### 2. **api/bc_client.py**
**หน้าที่:** HTTP Client สำหรับเรียก BC API

**ฟังก์ชันสำคัญ:**
- `get()`, `post()`, `patch()`, `delete()`: HTTP methods

---

#### 3. **api/bc_sales_order.py**
**หน้าที่:** Sales Order API สำหรับ BC

---

#### 4. **api/bc_sales_quote.py**
**หน้าที่:** Sales Quote API สำหรับ BC

---

#### 5. **api/router_sq.py**
**หน้าที่:** Sales Queue Router (บันทึก quote ก่อนส่งเข้า BC)

**API Endpoints:**

| Method | Path | Body | Response | หน้าที่ |
|--------|------|------|----------|---------|
| POST | `/api/sq/quote` | `{customerNo, quoteNo, items: [{itemNo, qty, price}]}` | `{status: "SUCCESS", sqNo, message}` | สร้าง Sales Queue |

**Database Tables:**
- `sales_queue`: Header
- `sales_queue_line`: Lines

**Export:** `router` (APIRouter with prefix="/api/sq")

---

### Dependencies (requirements.txt)

```
fastapi          # Web framework
uvicorn          # ASGI server
pandas           # Data processing
numpy            # Numerical computing
jinja2           # Template engine
weasyprint       # PDF generation
pydantic         # Data validation
python-multipart # File upload
python-dotenv    # Environment variables
pyjwt            # JWT authentication
scipy            # Scientific computing
openpyxl         # Excel file handling
annotated-types  # Type annotations
requests         # HTTP client
```

---


## Frontend (React/JavaScript)

### โครงสร้างโฟลเดอร์
```
frontend/src/
├── main.jsx                   # Entry point
├── App.jsx                    # Root component + Routing
├── style.css                  # Global styles
│
├── components/                # Reusable components
│   ├── common/               # Common components
│   │   └── CustomDropdown.jsx
│   ├── cross-sell/           # Cross-sell components
│   │   ├── CrossSellItem.jsx
│   │   ├── CrossSellPanel.jsx
│   │   └── useCrossSell.js
│   ├── products/             # Product filter components
│   │   ├── AccessoriesFilter.jsx
│   │   ├── AluminiumFilter.jsx
│   │   ├── CLineFilter.jsx
│   │   ├── DynamicsProductFilter.jsx
│   │   ├── GypsumFilter.jsx
│   │   ├── ProductCategorySelector.jsx
│   │   ├── ProductDetail.jsx
│   │   ├── ProductImage.jsx
│   │   ├── ProductList.jsx
│   │   └── SealantFilter.jsx
│   ├── quotes/               # Quote components
│   │   └── QuoteDraftCard.jsx
│   ├── updatePrice/          # Price update components
│   │   ├── ActivateVersionButton.jsx
│   │   ├── PricePreviewTable.jsx
│   │   └── UploadPriceExcel.jsx
│   ├── wizard/               # Quote wizard components
│   │   ├── AccessoriesPicker.jsx
│   │   ├── AluminiumPicker.jsx
│   │   ├── CartItemRow.jsx
│   │   ├── CategoryCard.jsx
│   │   ├── CLinePicker.jsx
│   │   ├── CustomerDisplay.jsx
│   │   ├── CustomerSearchSection.jsx
│   │   ├── GlassPickerModal.jsx
│   │   ├── GlassSemiSizeModal.jsx
│   │   ├── GypsumPicker.jsx
│   │   ├── ItemCard.jsx
│   │   ├── ItemPickerModal.jsx
│   │   ├── NewCustomerModal.jsx
│   │   ├── OrderHistoryCard.jsx
│   │   ├── PriceEditModal.jsx
│   │   ├── ProgressBar.jsx
│   │   ├── SealantPicker.jsx
│   │   ├── SelectionButton.jsx
│   │   ├── ShippingModal.jsx
│   │   ├── SummaryRow.jsx
│   │   ├── TaxDeliverySection.jsx
│   │   └── TaxDisplay.jsx
│   ├── Loader.jsx
│   ├── Navbar.jsx
│   └── ProtectedRoute.jsx
│
├── context/                   # React Context
│   ├── AuthContext.jsx       # Authentication state
│   └── QuoteContext.jsx      # Quote state management
│
├── hooks/                     # Custom hooks
│   ├── useAuth.js
│   ├── useItemPriceHistory.js
│   ├── useQuote.js
│   └── useSelectedStatus.js
│
├── pages/                     # Page components
│   ├── CreateQuote/
│   │   ├── CreateQuoteWizard.jsx
│   │   ├── Step6_Summary.jsx
│   │   └── utils/
│   ├── CheckProduct.jsx
│   ├── ConfirmedQuotesPage.jsx
│   ├── Dashboard.jsx
│   ├── Login.jsx
│   ├── OrderDetailPage.jsx
│   ├── QuoteDraftListPage.jsx
│   └── UpdatePrice.jsx
│
├── services/                  # API services
│   └── api.js                # Axios instance
│
└── utils/                     # Utilities
    ├── glassSku.js           # Glass SKU utilities
    └── printQuotation.js     # PDF printing
```

---

### Entry Point & Routing

#### 1. **main.jsx**
**ประเภท:** Entry Point

**หน้าที่:** จุดเริ่มต้นของ React application

**Providers:**
- `BrowserRouter`: React Router
- `AuthProvider`: Authentication context
- `QuoteProvider`: Quote state management

**Export:** None (render to DOM)

---

#### 2. **App.jsx**
**ประเภท:** Root Component

**หน้าที่:** กำหนด routing และ layout

**Routes:**
- `/login` → Login page (public)
- `/` → Dashboard (protected)
- `/dashboard` → Dashboard (protected)
- `/update-price` → Update Price page (protected)
- `/quote-drafts` → Draft quotes list (protected)
- `/confirmed-quotes` → Confirmed quotes list (protected)
- `/order/:id` → Order detail (protected)
- `/create` → Create quote wizard (protected)

**Layouts:**
1. `DashboardLayout`: Navbar + content (สำหรับ Dashboard)
2. `WizardLayout`: Navbar + white card container (สำหรับ Wizard)

**Export:** `App` (default)

---


### Context (State Management)

#### 1. **context/AuthContext.jsx**
**ประเภท:** Context Provider

**หน้าที่:** จัดการ authentication state

**State:**
- `employee`: ข้อมูลพนักงาน `{id, name, branchId}`
- `token`: JWT token
- `loading`: สถานะการโหลด

**Functions:**
- `login(employeeCode)`: Login และบันทึก token
- `logout()`: Logout และลบ token

**Storage:** localStorage (`token`, `employee`)

**Export:** `AuthContext`, `AuthProvider`

---

#### 2. **context/QuoteContext.jsx**
**ประเภท:** Context Provider + Reducer

**หน้าที่:** จัดการ quote state (ตะกร้าสินค้า, ลูกค้า, ค่าขนส่ง)

**State:**
```javascript
{
  step: 1,                    // ขั้นตอนปัจจุบัน
  customer: null,             // ข้อมูลลูกค้า
  deliveryAddress: null,      // ที่อยู่จัดส่ง
  vehicle: null,              // ประเภทรถ
  deliveryType: "PICKUP",     // PICKUP | DELIVERY
  cart: [],                   // รายการสินค้า
  shippingDirty: false,       // ต้องคำนวณค่าขนส่งใหม่หรือไม่
  totals: {                   // ยอดรวม
    exVat: 0,
    vat: 0,
    grandTotal: 0,
    shippingRaw: 0,
    shippingCustomerPay: 0
  },
  needsTax: false,            // ต้องการใบกำกับภาษีหรือไม่
  remark: "",                 // หมายเหตุ
  status: "new",              // new | open | complete
  quoteNo: null               // เลขที่ใบเสนอราคา
}
```

**Actions:**
1. `SET_STEP`: เปลี่ยนขั้นตอน
2. `SET_CUSTOMER`: ตั้งค่าลูกค้า
3. `SET_TAX_DELIVERY`: ตั้งค่าภาษีและการจัดส่ง
4. `SET_QUOTE_META`: ตั้งค่า id, quoteNo, status
5. `SET_SHIPPING`: ตั้งค่าข้อมูลการขนส่ง
6. `SET_DELIVERY_ADDRESS`: ตั้งค่าที่อยู่จัดส่ง
7. `SET_VEHICLE`: ตั้งค่าประเภทรถ
8. `ADD_ITEM`: เพิ่มสินค้าลงตะกร้า (รองรับ variant + sqft)
9. `UPDATE_CART_QTY`: แก้ไขจำนวนสินค้า
10. `UPDATE_CART_PRICE`: แก้ไขราคาสินค้า (manual)
11. `REMOVE_ITEM`: ลบสินค้าออกจากตะกร้า
12. `SET_CART`: ตั้งค่าตะกร้าทั้งหมด
13. `SET_TOTALS`: ตั้งค่ายอดรวม
14. `LOAD_DRAFT`: โหลด draft quote
15. `UPDATE_ITEM_DESCRIPTION`: แก้ไขชื่อสินค้า
16. `APPLY_PRICING_RESULT`: นำผลการคำนวณราคามาใช้
17. `RESET_QUOTE`: รีเซ็ตทั้งหมด

**Cart Item Structure:**
```javascript
{
  sku: "G010101010101010101",
  name: "กระจกใส 6mm",
  qty: 10,
  unit: "ตร.ฟุต",
  category: "G",
  
  // ราคา (แยก truth / display)
  UnitPrice: 65,              // บาท/ตร.ฟุต (truth)
  price: 65,                  // บาท/หน่วย (display, non-glass)
  price_per_sheet: 650,       // บาท/แผ่น (display, glass only)
  
  lineTotal: 6500,            // ยอดรวมบรรทัด
  
  // metadata
  sqft_sheet: 10,             // ตร.ฟุต/แผ่น (glass only)
  product_weight: 1.5,        // น้ำหนัก/หน่วย (aluminium)
  variantCode: "V001",        // รหัส variant
  
  // flags
  source: "ui",               // ui | db | draft
  needsPricing: true,         // ต้องคำนวณราคาหรือไม่
  priceSource: "manual",      // manual | auto
  isDraftItem: false          // มาจาก draft หรือไม่
}
```

**Export:** `QuoteContext`, `QuoteProvider`, `useQuote`

---

### Custom Hooks

#### 1. **hooks/useAuth.js**
**ประเภท:** Custom Hook

**หน้าที่:** เข้าถึง AuthContext

**Return:** `{employee, token, loading, login, logout}`

**Export:** `useAuth` (default)

---

#### 2. **hooks/useQuote.js**
**ประเภท:** Custom Hook

**หน้าที่:** เข้าถึง QuoteContext

**Return:** `{state, dispatch}`

**Export:** `useQuote` (default)

---

#### 3. **hooks/useItemPriceHistory.js**
**ประเภท:** Custom Hook

**หน้าที่:** ดึงประวัติราคาสินค้าของลูกค้า

**Parameters:** `{sku, customerCode, enabled}`

**Return:** `{history: [{invoiceNo, date, price, qty, unit}], loading, error}`

**Export:** `useItemPriceHistory` (default)

---

#### 4. **hooks/useSelectedStatus.js**
**ประเภท:** Custom Hook

**หน้าที่:** ตรวจสอบว่าสินค้าถูกเลือกในตะกร้าหรือไม่

**Parameters:** `{sku, variantCode, sqft_sheet}`

**Return:** `{isSelected: boolean}`

**Export:** `useSelectedStatus` (default)

---


### Pages

#### 1. **pages/Login.jsx**
**ประเภท:** Page Component

**หน้าที่:** หน้า Login

**State:**
- `employeeCode`: รหัสพนักงาน
- `error`: ข้อความ error
- `loading`: สถานะการโหลด

**Functions:**
- `handleSubmit(e)`: Login ด้วยรหัสพนักงาน

**Export:** `Login` (default)

---

#### 2. **pages/Dashboard.jsx**
**ประเภท:** Page Component

**หน้าที่:** หน้า Dashboard หลัก

**State:**
- `currentDate`: วันที่ปัจจุบัน (ภาษาไทย)
- `todayCount`: จำนวนใบเสนอราคาวันนี้
- `pendingCount`: จำนวนใบเสนอราคารอดำเนินการ
- `contactCustomerCount`: จำนวนลูกค้าที่ติดต่อวันนี้
- `isSemiModalOpen`: สถานะ modal ขนาดกระจก

**Functions:**
- `handleCreateQuote()`: ไปหน้าสร้างใบเสนอราคา
- `handlePendingQuotes()`: ไปหน้ารายการ draft
- `handleTodayQuotes()`: ไปหน้ารายการใบเสนอราคาวันนี้
- `handleSemiSize()`: เปิด modal ขนาดกระจก

**Components Used:**
- `Navbar`
- `GlassSemiSizeModal`

**Export:** `Dashboard` (default)

---

#### 3. **pages/CreateQuote/CreateQuoteWizard.jsx**
**ประเภท:** Page Component

**หน้าที่:** Wizard สำหรับสร้างใบเสนอราคา

**Logic:**
- โหลด draft จาก `location.state` (ถ้ามี)
- Render `Step6_Summary` (หน้าสรุป)

**Export:** `CreateQuoteWizard` (default)

---

#### 4. **pages/CreateQuote/Step6_Summary.jsx**
**ประเภท:** Page Component

**หน้าที่:** หน้าสรุปใบเสนอราคา (Step 6)

**Features:**
- แสดงข้อมูลลูกค้า
- แสดงตะกร้าสินค้า (CartItemRow)
- เลือกสินค้าเพิ่ม (ItemPickerModal)
- คำนวณราคาอัตโนมัติ
- คำนวณค่าขนส่ง (ShippingModal)
- แก้ไขราคาสินค้า (PriceEditModal)
- Cross-sell recommendations (CrossSellPanel)
- บันทึก draft / ยืนยันใบเสนอราคา
- พิมพ์ PDF

**Export:** `Step6_Summary` (default)

---

#### 5. **pages/QuoteDraftListPage.jsx**
**ประเภท:** Page Component

**หน้าที่:** แสดงรายการใบเสนอราคา draft

**Features:**
- โหลดรายการ draft จาก API
- แสดงเป็น card (QuoteDraftCard)
- คลิกเพื่อแก้ไข draft

**Export:** `QuoteDraftListPage` (default)

---

#### 6. **pages/ConfirmedQuotesPage.jsx**
**ประเภท:** Page Component

**หน้าที่:** แสดงรายการใบเสนอราคาที่ยืนยันแล้ว

**Features:**
- โหลดรายการ complete จาก API
- แสดงเป็นตาราง
- คลิกเพื่อดูรายละเอียด

**Export:** `ConfirmedQuotesPage` (default)

---

#### 7. **pages/OrderDetailPage.jsx**
**ประเภท:** Page Component

**หน้าที่:** แสดงรายละเอียดใบเสนอราคา

**Features:**
- โหลดข้อมูลจาก API
- แสดงข้อมูลลูกค้า
- แสดงรายการสินค้า
- แสดงยอดรวม
- พิมพ์ PDF

**Export:** `OrderDetailPage` (default)

---

#### 8. **pages/UpdatePrice.jsx**
**ประเภท:** Page Component

**หน้าที่:** อัปเดตราคาสินค้าจากไฟล์ Excel (สำหรับผู้จัดการ)

**Features:**
- Upload Excel (UploadPriceExcel)
- Preview การเปลี่ยนแปลง (PricePreviewTable)
- Activate version (ActivateVersionButton)

**Export:** `UpdatePrice` (default)

---


### Components

#### Common Components

##### 1. **components/Navbar.jsx**
**ประเภท:** Component

**หน้าที่:** Navigation bar

**Features:**
- แสดงชื่อพนักงาน
- เมนู: Dashboard, สร้างใบเสนอราคา, รายการ draft, รายการยืนยัน
- ปุ่ม Logout

**Props:** None

**Export:** `Navbar` (default)

---

##### 2. **components/Loader.jsx**
**ประเภท:** Component

**หน้าที่:** Loading spinner

**Props:** None

**Export:** `Loader` (default)

---

##### 3. **components/ProtectedRoute.jsx**
**ประเภท:** Component

**หน้าที่:** Route guard สำหรับหน้าที่ต้อง login

**Logic:**
- ตรวจสอบ token
- ถ้าไม่มี → redirect ไป /login
- ถ้ามี → render `<Outlet />`

**Export:** `ProtectedRoute` (default)

---

##### 4. **components/common/CustomDropdown.jsx**
**ประเภท:** Component

**หน้าที่:** Dropdown component (ใช้ Headless UI)

**Props:**
- `options`: `[{code, name}]`
- `value`: selected value
- `onChange`: callback function
- `placeholder`: placeholder text

**Export:** `CustomDropdown` (default)

---

#### Wizard Components

##### 1. **components/wizard/CustomerSearchSection.jsx**
**ประเภท:** Component

**หน้าที่:** ค้นหาลูกค้า

**Props:**
- `onCustomerSelect`: callback เมื่อเลือกลูกค้า

**Features:**
- Autocomplete search
- แสดงรายการลูกค้า
- เปิด modal ลูกค้าใหม่ (NewCustomerModal)

**State:**
- `query`: คำค้นหา
- `results`: ผลการค้นหา
- `loading`: สถานะการโหลด

**Export:** `CustomerSearchSection` (default)

---

##### 2. **components/wizard/CustomerDisplay.jsx**
**ประเภท:** Component

**หน้าที่:** แสดงข้อมูลลูกค้า

**Props:**
- `customer`: ข้อมูลลูกค้า

**Export:** `CustomerDisplay` (default)

---

##### 3. **components/wizard/ItemPickerModal.jsx**
**ประเภท:** Component

**หน้าที่:** Modal สำหรับเลือกสินค้า

**Props:**
- `isOpen`: สถานะ modal
- `onClose`: callback เมื่อปิด
- `onAddItem`: callback เมื่อเพิ่มสินค้า

**Features:**
- เลือกหมวดหมู่สินค้า (CategoryCard)
- แสดง filter ตามหมวดหมู่
- แสดงรายการสินค้า (ItemCard)
- เพิ่มสินค้าลงตะกร้า

**State:**
- `selectedCategory`: หมวดหมู่ที่เลือก
- `filters`: ตัวกรอง
- `items`: รายการสินค้า
- `loading`: สถานะการโหลด

**Export:** `ItemPickerModal` (default)

---

##### 4. **components/wizard/CartItemRow.jsx**
**ประเภท:** Component

**หน้าที่:** แสดงรายการสินค้าในตะกร้า

**Props:**
- `item`: ข้อมูลสินค้า
- `onUpdateQty`: callback เมื่อแก้ไขจำนวน
- `onRemove`: callback เมื่อลบสินค้า
- `onEditPrice`: callback เมื่อแก้ไขราคา

**Features:**
- แสดงชื่อสินค้า, SKU, จำนวน, ราคา, ยอดรวม
- แก้ไขจำนวน
- แก้ไขราคา (เปิด PriceEditModal)
- ลบสินค้า
- แสดงประวัติราคา (useItemPriceHistory)

**Export:** `CartItemRow` (default)

---

##### 5. **components/wizard/PriceEditModal.jsx**
**ประเภท:** Component

**หน้าที่:** Modal สำหรับแก้ไขราคาสินค้า

**Props:**
- `isOpen`: สถานะ modal
- `onClose`: callback เมื่อปิด
- `item`: ข้อมูลสินค้า
- `onSave`: callback เมื่อบันทึก

**Features:**
- แก้ไขราคาตามประเภทสินค้า:
  - **กระจก:** แก้ไขราคา/ตร.ฟุต หรือ ราคา/แผ่น
  - **อลูมิเนียม:** แก้ไขราคา/กก. หรือ ราคา/เส้น
  - **อื่นๆ:** แก้ไขราคา/หน่วย
- แสดงประวัติราคา

**State:**
- `editedPrice`: ราคาที่แก้ไข
- `pricePerSqft`: ราคา/ตร.ฟุต (กระจก)
- `pricePerKg`: ราคา/กก. (อลูมิเนียม)

**Export:** `PriceEditModal` (default)

---

##### 6. **components/wizard/ShippingModal.jsx**
**ประเภท:** Component

**หน้าที่:** Modal สำหรับคำนวณค่าขนส่ง

**Props:**
- `isOpen`: สถานะ modal
- `onClose`: callback เมื่อปิด
- `cart`: รายการสินค้า
- `onSave`: callback เมื่อบันทึก

**Features:**
- เลือกประเภทรถ
- ระบุระยะทาง
- ระบุเวลาขนของ
- ระบุจำนวนพนักงาน
- คำนวณค่าขนส่ง (เรียก API)
- แสดงรายละเอียดค่าขนส่ง

**State:**
- `vehicleType`: ประเภทรถ
- `distance`: ระยะทาง (km)
- `unloadHours`: เวลาขนของ (ชม.)
- `staffCount`: จำนวนพนักงาน
- `result`: ผลการคำนวณ

**Export:** `ShippingModal` (default)

---

##### 7. **components/wizard/TaxDeliverySection.jsx**
**ประเภท:** Component

**หน้าที่:** เลือกภาษีและการจัดส่ง

**Props:**
- `needsTax`: ต้องการใบกำกับภาษีหรือไม่
- `deliveryType`: PICKUP | DELIVERY
- `onNeedsTaxChange`: callback
- `onDeliveryTypeChange`: callback

**Export:** `TaxDeliverySection` (default)

---

##### 8. **components/wizard/CategoryCard.jsx**
**ประเภท:** Component

**หน้าที่:** การ์ดหมวดหมู่สินค้า

**Props:**
- `category`: `{name, icon, color}`
- `onClick`: callback เมื่อคลิก

**Export:** `CategoryCard` (default)

---

##### 9. **components/wizard/ItemCard.jsx**
**ประเภท:** Component

**หน้าที่:** การ์ดสินค้า

**Props:**
- `item`: ข้อมูลสินค้า
- `onAdd`: callback เมื่อเพิ่มสินค้า
- `isSelected`: สินค้าถูกเลือกแล้วหรือไม่

**Export:** `ItemCard` (default)

---

##### 10. **components/wizard/GlassPickerModal.jsx**
**ประเภท:** Component

**หน้าที่:** Modal สำหรับเลือกกระจก (รองรับการตัดขนาด)

**Props:**
- `isOpen`: สถานะ modal
- `onClose`: callback เมื่อปิด
- `onAddItem`: callback เมื่อเพิ่มสินค้า

**Features:**
- เลือก brand, type, subGroup, color, thickness
- เลือกขนาดมาตรฐาน หรือ ระบุขนาดเอง
- คำนวณตารางฟุต
- เพิ่มกระจกลงตะกร้า

**State:**
- `filters`: ตัวกรอง
- `width`: ความกว้าง (นิ้ว)
- `height`: ความสูง (นิ้ว)
- `sqft`: ตารางฟุต
- `qty`: จำนวน

**Export:** `GlassPickerModal` (default)

---

##### 11. **components/wizard/GlassSemiSizeModal.jsx**
**ประเภท:** Component

**หน้าที่:** Modal สำหรับเลือกกระจกขนาดกึ่งมาตรฐาน

**Props:**
- `isOpen`: สถานะ modal
- `onClose`: callback เมื่อปิด
- `branchCode`: รหัสสาขา

**Features:**
- โหลดขนาดกึ่งมาตรฐานจาก API
- แสดงรายการขนาด
- เลือกขนาดและเพิ่มลงตะกร้า

**Export:** `GlassSemiSizeModal` (default)

---


#### Product Filter Components

##### 1. **components/products/AluminiumFilter.jsx**
**ประเภท:** Component

**หน้าที่:** Filter สำหรับอลูมิเนียม

**Props:**
- `filters`: ตัวกรองปัจจุบัน
- `onFilterChange`: callback เมื่อเปลี่ยนตัวกรอง

**Features:**
- Cascading filter (brand → group → subGroup → color → thickness)
- โหลดตัวเลือกจาก API

**State:**
- `options`: ตัวเลือกทั้งหมด

**Export:** `AluminiumFilter` (default)

---

##### 2. **components/products/CLineFilter.jsx**
**ประเภท:** Component

**หน้าที่:** Filter สำหรับ C-Line

**Props/Features:** เหมือน AluminiumFilter

**Export:** `CLineFilter` (default)

---

##### 3. **components/products/AccessoriesFilter.jsx**
**ประเภท:** Component

**หน้าที่:** Filter สำหรับอุปกรณ์

**Props/Features:** เหมือน AluminiumFilter (มี character แทน thickness)

**Export:** `AccessoriesFilter` (default)

---

##### 4. **components/products/SealantFilter.jsx**
**ประเภท:** Component

**หน้าที่:** Filter สำหรับซีลแลนท์

**Props/Features:** เหมือน AluminiumFilter (ไม่มี thickness)

**Export:** `SealantFilter` (default)

---

##### 5. **components/products/GypsumFilter.jsx**
**ประเภท:** Component

**หน้าที่:** Filter สำหรับยิปซั่ม

**Props/Features:** เหมือน AluminiumFilter

**Export:** `GypsumFilter` (default)

---

##### 6. **components/products/ProductCategorySelector.jsx**
**ประเภท:** Component

**หน้าที่:** เลือกหมวดหมู่สินค้า

**Props:**
- `onSelect`: callback เมื่อเลือกหมวดหมู่

**Export:** `ProductCategorySelector` (default)

---

##### 7. **components/products/ProductList.jsx**
**ประเภท:** Component

**หน้าที่:** แสดงรายการสินค้า

**Props:**
- `items`: รายการสินค้า
- `onAddItem`: callback เมื่อเพิ่มสินค้า

**Export:** `ProductList` (default)

---

##### 8. **components/products/ProductDetail.jsx**
**ประเภท:** Component

**หน้าที่:** แสดงรายละเอียดสินค้า

**Props:**
- `item`: ข้อมูลสินค้า

**Export:** `ProductDetail` (default)

---

##### 9. **components/products/ProductImage.jsx**
**ประเภท:** Component

**หน้าที่:** แสดงรูปภาพสินค้า

**Props:**
- `sku`: รหัสสินค้า
- `alt`: alt text

**Export:** `ProductImage` (default)

---

##### 10. **components/products/DynamicsProductFilter.jsx**
**ประเภท:** Component

**หน้าที่:** Filter แบบ dynamic (ใช้กับหลายหมวดหมู่)

**Props:**
- `category`: หมวดหมู่สินค้า
- `filters`: ตัวกรองปัจจุบัน
- `onFilterChange`: callback

**Export:** `DynamicsProductFilter` (default)

---

#### Cross-Sell Components

##### 1. **components/cross-sell/CrossSellPanel.jsx**
**ประเภท:** Component

**หน้าที่:** แสดงสินค้าแนะนำ

**Props:**
- `cart`: รายการสินค้าในตะกร้า

**Features:**
- เรียก API cross-sell
- แสดงรายการสินค้าแนะนำ (CrossSellItem)

**State:**
- `recommendations`: รายการสินค้าแนะนำ
- `loading`: สถานะการโหลด

**Export:** `CrossSellPanel` (default)

---

##### 2. **components/cross-sell/CrossSellItem.jsx**
**ประเภท:** Component

**หน้าที่:** แสดงสินค้าแนะนำแต่ละรายการ

**Props:**
- `item`: `{displayName, ruleNo, ruleType, ruleGroup}`

**Export:** `CrossSellItem` (default)

---

##### 3. **components/cross-sell/useCrossSell.js**
**ประเภท:** Custom Hook

**หน้าที่:** ดึงสินค้าแนะนำจาก API

**Parameters:** `{products}`

**Return:** `{recommendations: [], loading, error}`

**Export:** `useCrossSell` (default)

---

#### Quote Components

##### 1. **components/quotes/QuoteDraftCard.jsx**
**ประเภท:** Component

**หน้าที่:** การ์ดแสดงใบเสนอราคา draft

**Props:**
- `quote`: ข้อมูลใบเสนอราคา
- `onClick`: callback เมื่อคลิก

**Features:**
- แสดงเลขที่ใบเสนอราคา
- แสดงชื่อลูกค้า
- แสดงยอดรวม
- แสดงวันที่สร้าง

**Export:** `QuoteDraftCard` (default)

---

#### Update Price Components

##### 1. **components/updatePrice/UploadPriceExcel.jsx**
**ประเภท:** Component

**หน้าที่:** Upload ไฟล์ Excel สำหรับอัปเดตราคา

**Props:**
- `onUploadSuccess`: callback เมื่อ upload สำเร็จ

**Features:**
- เลือกไฟล์ Excel
- Upload ไปยัง API
- แสดงผลการ upload

**State:**
- `file`: ไฟล์ที่เลือก
- `uploading`: สถานะการ upload
- `result`: ผลการ upload

**Export:** `UploadPriceExcel` (default)

---

##### 2. **components/updatePrice/PricePreviewTable.jsx**
**ประเภท:** Component

**หน้าที่:** แสดงตัวอย่างการเปลี่ยนแปลงราคา

**Props:**
- `versionId`: version ID

**Features:**
- โหลดข้อมูลจาก API
- แสดงเป็นตาราง (SKU, ราคาเก่า, ราคาใหม่)
- Highlight รายการที่เปลี่ยนแปลง

**State:**
- `data`: ข้อมูลการเปลี่ยนแปลง
- `loading`: สถานะการโหลด

**Export:** `PricePreviewTable` (default)

---

##### 3. **components/updatePrice/ActivateVersionButton.jsx**
**ประเภท:** Component

**หน้าที่:** ปุ่ม Activate version

**Props:**
- `versionId`: version ID
- `onActivateSuccess`: callback เมื่อ activate สำเร็จ

**Features:**
- Activate version (เรียก API)
- แสดง confirmation dialog

**State:**
- `activating`: สถานะการ activate

**Export:** `ActivateVersionButton` (default)

---


### Services

#### **services/api.js**
**ประเภท:** Service

**หน้าที่:** Axios instance สำหรับเรียก API

**Config:**
- `baseURL`: จาก env variable `VITE_API_BASE_URL` (default: "")
- `timeout`: 3000000 ms (50 นาที)

**Interceptors:**
- Request: แนบ JWT token จาก localStorage

**Export:** `api` (default)

---

### Utilities

#### 1. **utils/glassSku.js**
**ประเภท:** Utility

**หน้าที่:** ฟังก์ชันสำหรับจัดการ Glass SKU

**Functions:**
- `parseGlassSku(sku)`: แยก SKU เป็นส่วนๆ
- `buildGlassSku(parts)`: สร้าง SKU จากส่วนต่างๆ
- `calculateSqft(width, height)`: คำนวณตารางฟุต

**Export:** `{parseGlassSku, buildGlassSku, calculateSqft}`

---

#### 2. **utils/printQuotation.js**
**ประเภท:** Utility

**หน้าที่:** พิมพ์ใบเสนอราคาเป็น PDF

**Functions:**
- `printQuotation(quoteData)`: เรียก API `/api/print/quotation` และเปิด PDF ในหน้าต่างใหม่

**Export:** `printQuotation` (default)

---


## การเชื่อมต่อ Backend-Frontend

### API Endpoints ที่ Frontend เรียกใช้

#### Authentication
- `POST /api/login` - Login ด้วยรหัสพนักงาน

#### Customer
- `GET/POST /api/customer/search` - ค้นหาลูกค้า
- `GET/POST /api/customer/search-list` - Autocomplete ลูกค้า

#### Items
- `GET /api/items/categories/list` - รายการหมวดหมู่
- `GET /api/items/categories/{category}/list` - รายการสินค้าแบบ light
- `GET /api/items/{sku}` - รายละเอียดสินค้า
- `GET /api/items/related/{sku}` - สินค้าที่เกี่ยวข้อง
- `GET /api/items/search` - ค้นหาสินค้า
- `GET /api/items/categories/{category}/filter-options` - ตัวเลือก filter

#### Products (แต่ละประเภท)
- `GET /api/aluminium/master` - ตัวเลือก filter อลูมิเนียม
- `GET /api/aluminium/items` - รายการอลูมิเนียม
- `GET /api/cline/master` - ตัวเลือก filter C-Line
- `GET /api/cline/items` - รายการ C-Line
- `GET /api/accessories/master` - ตัวเลือก filter อุปกรณ์
- `GET /api/accessories/items` - รายการอุปกรณ์
- `GET /api/sealant/master` - ตัวเลือก filter ซีลแลนท์
- `GET /api/sealant/items` - รายการซีลแลนท์
- `GET /api/gypsum/master` - ตัวเลือก filter ยิปซั่ม
- `GET /api/gypsum/items` - รายการยิปซั่ม
- `GET /api/glass/master` - ตัวเลือก filter กระจก
- `GET /api/glass/items` - รายการกระจก
- `GET /api/glass/semi-standard-sizes` - ขนาดกระจกกึ่งมาตรฐาน

#### Pricing
- `POST /api/pricing/calculate` - คำนวณราคาทั้งตะกร้า

#### Shipping
- `POST /api/shipping/calculate_from_cart` - คำนวณค่าขนส่งจากตะกร้า

#### Quotation
- `POST /api/quotation` - สร้างใบเสนอราคา
- `PUT /api/quotation/{quote_no}` - แก้ไขใบเสนอราคา
- `GET /api/quotation` - รายการใบเสนอราคา
- `GET /api/quotation/{quote_no}` - รายละเอียดใบเสนอราคา
- `DELETE /api/quotation/{quote_no}` - ยกเลิกใบเสนอราคา

#### Cross-Sell
- `POST /api/cross-sell` - แนะนำสินค้าเพิ่มเติม

#### Invoice
- `GET /api/invoice/item-price-history` - ประวัติราคาสินค้า

#### Item Update
- `POST /api/item-update/upload` - Upload Excel
- `GET /api/item-update/preview/{version_id}` - Preview การเปลี่ยนแปลง
- `POST /api/item-update/activate/{version_id}` - Activate version

#### Print
- `POST /api/print/quotation` - พิมพ์ใบเสนอราคา PDF

---

### Data Flow

#### 1. สร้างใบเสนอราคา (Create Quote)

```
User → CustomerSearchSection → API: /api/customer/search-list
                              ↓
                         แสดงรายการลูกค้า
                              ↓
User เลือกลูกค้า → API: /api/customer/search
                              ↓
                    QuoteContext.SET_CUSTOMER
                              ↓
User เลือกสินค้า → ItemPickerModal → API: /api/items/categories/{category}/list
                                    → API: /api/items/{sku}
                              ↓
                    QuoteContext.ADD_ITEM
                              ↓
User คลิก "คำนวณราคา" → API: /api/pricing/calculate
                              ↓
                    QuoteContext.APPLY_PRICING_RESULT
                              ↓
User เลือก "จัดส่ง" → ShippingModal → API: /api/shipping/calculate_from_cart
                              ↓
                    QuoteContext.SET_SHIPPING
                              ↓
User คลิก "บันทึก Draft" → API: POST /api/quotation (status: "open")
                              ↓
                         บันทึกสำเร็จ
                              ↓
User คลิก "ยืนยัน" → API: POST /api/quotation (status: "complete")
                              ↓
                    สร้างใบเสนอราคาสำเร็จ
                              ↓
User คลิก "พิมพ์" → API: POST /api/print/quotation
                              ↓
                    เปิด PDF ในหน้าต่างใหม่
```

#### 2. แก้ไข Draft

```
User → QuoteDraftListPage → API: GET /api/quotation?status=open
                              ↓
                    แสดงรายการ draft
                              ↓
User คลิก draft → API: GET /api/quotation/{quote_no}
                              ↓
                    QuoteContext.LOAD_DRAFT
                              ↓
                    CreateQuoteWizard (Step6_Summary)
                              ↓
User แก้ไข → (เหมือนสร้างใหม่)
                              ↓
User คลิก "บันทึก" → API: PUT /api/quotation/{quote_no}
                              ↓
                    อัปเดตสำเร็จ
```

#### 3. อัปเดตราคา (Update Price)

```
User → UpdatePrice → UploadPriceExcel → API: POST /api/item-update/upload
                              ↓
                    แสดง version_id และ warnings
                              ↓
                    PricePreviewTable → API: GET /api/item-update/preview/{version_id}
                              ↓
                    แสดงตัวอย่างการเปลี่ยนแปลง
                              ↓
User คลิก "Activate" → ActivateVersionButton → API: POST /api/item-update/activate/{version_id}
                              ↓
                    อัปเดตราคาสำเร็จ
```

---


## ไฟล์ Configuration สำคัญ

### Backend

#### 1. **requirements.txt**
**หน้าที่:** รายการ Python packages ที่ต้องใช้

**Packages หลัก:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pandas` - Data processing
- `numpy` - Numerical computing
- `jinja2` - Template engine
- `weasyprint` - PDF generation
- `pydantic` - Data validation
- `python-multipart` - File upload
- `python-dotenv` - Environment variables
- `pyjwt` - JWT authentication
- `scipy` - Scientific computing
- `openpyxl` - Excel file handling
- `requests` - HTTP client

---

#### 2. **Dockerfile** (backend)
**หน้าที่:** สร้าง Docker image สำหรับ backend

**Steps:**
1. ใช้ Python 3.12 base image
2. ติดตั้ง dependencies จาก requirements.txt
3. Copy source code
4. Expose port 8000
5. Run uvicorn

---

#### 3. **.env**
**หน้าที่:** Environment variables

**Variables:**
- `JWT_SECRET` - Secret key สำหรับ JWT
- `CUSTOMER_API_KEY` - API key สำหรับ D365 Customer API
- `INVOICE_API_KEY` - API key สำหรับ D365 Invoice API
- `MSSQL_SERVER` - MS SQL Server address
- `MSSQL_DATABASE` - Database name

---

### Frontend

#### 1. **package.json**
**หน้าที่:** รายการ npm packages และ scripts

**Dependencies หลัก:**
- `react` (19.1.1) - UI library
- `react-dom` (19.1.1) - React DOM
- `react-router-dom` (7.9.5) - Routing
- `axios` (1.13.2) - HTTP client
- `lucide-react` (0.552.0) - Icons
- `@headlessui/react` (2.2.9) - Headless UI components
- `pdf-lib` (1.17.1) - PDF manipulation

**DevDependencies:**
- `vite` (7.1.7) - Build tool
- `@vitejs/plugin-react` (5.0.4) - React plugin
- `tailwindcss` (3.4.19) - CSS framework
- `eslint` - Linter
- `prettier` - Code formatter

**Scripts:**
- `dev` - รัน development server (Vite)
- `build` - Build production
- `lint` - รัน ESLint
- `preview` - Preview production build

---

#### 2. **vite.config.js**
**หน้าที่:** การตั้งค่า Vite

**Config:**
- `plugins`: React plugin
- `server.port`: 5173
- `server.proxy`: Proxy `/api` ไปยัง `http://127.0.0.1:8000`

---

#### 3. **tailwind.config.js**
**หน้าที่:** การตั้งค่า TailwindCSS

**Config:**
- `content`: ไฟล์ที่ใช้ Tailwind (`./index.html`, `./src/**/*.{js,jsx}`)
- `theme`: Custom theme (ถ้ามี)
- `plugins`: Tailwind plugins

---

#### 4. **Dockerfile** (frontend)
**หน้าที่:** สร้าง Docker image สำหรับ frontend

**Steps:**
1. Build stage: ใช้ Node.js build React app
2. Production stage: ใช้ Nginx serve static files
3. Copy nginx.conf
4. Copy built files จาก build stage
5. Expose port 80

---

#### 5. **nginx.conf**
**หน้าที่:** การตั้งค่า Nginx

**Config:**
- Serve static files จาก `/usr/share/nginx/html`
- Proxy `/api` ไปยัง backend (http://backend:8000)
- Fallback ไปยัง `index.html` (SPA routing)

---

### Root Level

#### 1. **docker-compose.yml**
**หน้าที่:** การตั้งค่า Docker Compose

**Services:**
1. **backend:**
   - Build: `./backend`
   - Image: `smart_pricing_backend`
   - Port: 8000:8000
   - Restart: always

2. **frontend:**
   - Build: `./frontend`
   - Image: `smart_pricing_frontend`
   - Port: 3200:80
   - Depends on: backend
   - Restart: always

---

#### 2. **smart_pricing.spec**
**หน้าที่:** PyInstaller spec file (สำหรับสร้าง .exe)

**Config:**
- Entry point: `backend/main.py`
- Include: frontend/dist, templates, fonts, data
- Output: `smart_pricing.exe`

---


## สรุปโครงสร้างและ Flow หลัก

### 1. Authentication Flow
```
User กรอกรหัสพนักงาน
    ↓
Frontend: POST /api/login {employeeCode}
    ↓
Backend: ตรวจสอบจาก SQLite (Employees table)
    ↓
Backend: สร้าง JWT token (expire 12 ชม.)
    ↓
Frontend: บันทึก token + employee ใน localStorage
    ↓
Frontend: ตั้งค่า Authorization header
    ↓
Redirect ไป Dashboard
```

### 2. Customer Search Flow
```
User พิมพ์ชื่อ/รหัส/เบอร์โทร
    ↓
Frontend: GET /api/customer/search-list?q={query}
    ↓
Backend: โหลดข้อมูลจาก D365 API (cache 15 นาที)
    ↓
Backend: ค้นหาจาก Customer, Name, Tel
    ↓
Backend: Return max 15 รายการ
    ↓
Frontend: แสดง dropdown
    ↓
User เลือกลูกค้า
    ↓
Frontend: GET /api/customer/search?code={code}
    ↓
Backend: โหลด Invoice 6 เดือน
    ↓
Backend: คำนวณ accum_6m, frequency, sales_g/a/s/y/c/e
    ↓
Frontend: บันทึกใน QuoteContext
```

### 3. Item Selection Flow
```
User เปิด ItemPickerModal
    ↓
User เลือกหมวดหมู่ (A/C/E/S/Y/G)
    ↓
Frontend: GET /api/{category}/master (โหลด filter options)
    ↓
User เลือก filter (brand, group, subGroup, etc.)
    ↓
Frontend: GET /api/{category}/items?brand=...&group=...
    ↓
Backend: โหลดจาก MS SQL (Items_Test)
    ↓
Backend: Filter ตาม SKU pattern
    ↓
Frontend: แสดงรายการสินค้า
    ↓
User คลิกสินค้า
    ↓
Frontend: GET /api/items/{sku} (โหลดรายละเอียดเต็ม)
    ↓
Backend: Enrich ด้วย SKU enricher (brand name, group name, etc.)
    ↓
User ระบุจำนวน
    ↓
Frontend: dispatch ADD_ITEM
    ↓
QuoteContext: เพิ่มสินค้าลงตะกร้า (ตรวจสอบซ้ำด้วย sku + variantCode + sqft)
```

### 4. Pricing Calculation Flow
```
User คลิก "คำนวณราคา"
    ↓
Frontend: รวบรวมข้อมูล {customerData, deliveryType, cart}
    ↓
Frontend: POST /api/pricing/calculate
    ↓
Backend: โหลดข้อมูลสินค้าจาก MS SQL (ราคา R1/R2/W1/W2, cost, weight)
    ↓
Backend: ตรวจสอบ customer code
    ↓
    ├─ ถ้าไม่มี → ใช้ราคา R2 (Default Mode)
    │
    └─ ถ้ามี → คำนวณด้วย LevelPrice + Price
                ↓
                LevelPrice: คำนวณ tier ตามยอดขาย
                ↓
                Price: คำนวณราคาตาม tier + delivery + pkg_size
    ↓
Backend: คำนวณ UnitPrice ตามประเภทสินค้า
    ├─ กระจก (G): UnitPrice = บาท/ตร.ฟุต, แสดงเป็น บาท/แผ่น
    ├─ อลูมิเนียม (A): UnitPrice × product_weight
    └─ อื่นๆ: UnitPrice = บาท/หน่วย
    ↓
Backend: คำนวณ lineTotal, subtotal, vat, profit
    ↓
Frontend: dispatch APPLY_PRICING_RESULT
    ↓
QuoteContext: อัปเดตราคาในตะกร้า (เฉพาะ needsPricing = true)
```

### 5. Shipping Calculation Flow
```
User เลือก "จัดส่ง"
    ↓
User เปิด ShippingModal
    ↓
User เลือกประเภทรถ, ระยะทาง, เวลาขนของ, จำนวนพนักงาน
    ↓
Frontend: POST /api/shipping/calculate_from_cart
    ↓
Backend: โหลด cost (RE) จาก MS SQL
    ↓
Backend: คำนวณกำไรจากตะกร้า
    ├─ กระจก: (price_per_sqft - cost) × total_sqft
    ├─ อลูมิเนียม: (price_per_unit - cost × weight) × qty
    └─ อื่นๆ: (price - cost) × qty
    ↓
Backend: คำนวณค่าขนส่ง
    ├─ fuel_cost = (distance / fuel_rate) × fuel_price
    ├─ fix_cost = (travel_hours + unload_hours) × fix_cost_per_hour
    ├─ labor_cost = (72 + 55 × staff_count) × (travel_hours + unload_hours)
    └─ shipping_cost = fuel_cost + fix_cost + labor_cost
    ↓
Backend: คำนวณการแบ่งจ่าย
    ├─ company_pay = min(shipping_cost, profit × 0.05)
    └─ customer_pay = shipping_cost - company_pay
    ↓
Frontend: dispatch SET_SHIPPING
    ↓
QuoteContext: บันทึกข้อมูลการขนส่ง
```

### 6. Save Quote Flow
```
User คลิก "บันทึก Draft" หรือ "ยืนยัน"
    ↓
Frontend: รวบรวมข้อมูลทั้งหมด
    ├─ employee (จาก AuthContext)
    ├─ customer
    ├─ cart
    ├─ totals
    ├─ deliveryType
    ├─ needTaxInvoice
    ├─ note
    └─ status ("open" หรือ "complete")
    ↓
Frontend: POST /api/quotation (ถ้าใหม่) หรือ PUT /api/quotation/{quote_no} (ถ้าแก้ไข)
    ↓
Backend: สร้างเลขที่ใบเสนอราคา (format: BSQT-2502/0001)
    ↓
Backend: บันทึกลง SQLite
    ├─ Quote_Header: ข้อมูลหัว
    └─ Quote_Line: รายการสินค้า
    ↓
Backend: Export ลง Excel (QuoteTemplate.xlsx)
    ↓
Frontend: แสดงข้อความสำเร็จ
    ↓
    ├─ ถ้า Draft → Redirect ไป /quote-drafts
    └─ ถ้า Complete → แสดงปุ่ม "พิมพ์"
```

### 7. Print PDF Flow
```
User คลิก "พิมพ์"
    ↓
Frontend: รวบรวมข้อมูลใบเสนอราคา
    ↓
Frontend: POST /api/print/quotation
    ↓
Backend: แปลงยอดเงินเป็นตัวอักษรไทย (baht_text)
    ↓
Backend: Render HTML จาก Jinja2 template (quotation.html)
    ↓
Backend: แปลง HTML เป็น PDF ด้วย WeasyPrint
    ↓
Backend: Return PDF (Content-Type: application/pdf)
    ↓
Frontend: เปิด PDF ในหน้าต่างใหม่
```

### 8. Update Price Flow
```
User (ผู้จัดการ) เข้าหน้า Update Price
    ↓
User เลือกไฟล์ Excel
    ↓
Frontend: POST /api/item-update/upload (multipart/form-data)
    ↓
Backend: อ่านไฟล์ Excel (pandas)
    ↓
Backend: ตรวจสอบ columns (No., R1, R2, W1, W2, AlternateName)
    ↓
Backend: วนลูปแต่ละ row
    ├─ ถ้า SKU ใหม่ → INSERT ลง Items_Test
    └─ ถ้า SKU เดิม → เก็บ old values
    ↓
Backend: บันทึกลง Item_Update_Version + Item_Update_Version_Detail
    ↓
Backend: Return {version_id, insert_warnings}
    ↓
Frontend: แสดง version_id และ warnings
    ↓
Frontend: GET /api/item-update/preview/{version_id}
    ↓
Backend: Return รายการเปลี่ยนแปลง
    ↓
Frontend: แสดงตาราง (SKU, old price, new price)
    ↓
User คลิก "Activate"
    ↓
Frontend: POST /api/item-update/activate/{version_id}
    ↓
Backend: UPDATE Items_Test ตาม version_detail
    ↓
Backend: UPDATE version status = "ACTIVE"
    ↓
Frontend: แสดงข้อความสำเร็จ
```

---

## สรุปเทคโนโลยีที่ใช้

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Database:** SQLite (local), MS SQL Server (items)
- **External API:** D365 Business Central (Customer, Invoice)
- **PDF Generation:** WeasyPrint + Jinja2
- **Data Processing:** Pandas, NumPy
- **Authentication:** JWT (PyJWT)
- **Excel Handling:** openpyxl

### Frontend
- **Framework:** React 19.1.1
- **Build Tool:** Vite 7.1.7
- **Routing:** React Router DOM 7.9.5
- **HTTP Client:** Axios 1.13.2
- **Styling:** TailwindCSS 3.4.19
- **UI Components:** Headless UI 2.2.9
- **Icons:** Lucide React 0.552.0
- **PDF:** pdf-lib 1.17.1

### DevOps
- **Containerization:** Docker + Docker Compose
- **Web Server:** Nginx (frontend)
- **ASGI Server:** Uvicorn (backend)
- **Native App:** PyInstaller

---

## หมายเหตุสำคัญ

### 1. SKU Pattern
แต่ละประเภทสินค้ามี SKU pattern ที่แตกต่างกัน:
- **Aluminium (A):** ABBGGSSSCCTT (12 ตัวอักษร)
- **C-Line (C):** CBBGGSSSCCTT (12 ตัวอักษร)
- **Accessories (E):** EBBBGGSSCCX (11 ตัวอักษร)
- **Sealant (S):** SBBGGSSSCC (10 ตัวอักษร)
- **Gypsum (Y):** YBBGGSCCCTT... (18 ตัวอักษร)
- **Glass (G):** GBBTTSSSCCCWWWHHH (18 ตัวอักษร)

### 2. Pricing Logic
- **Default Mode:** ใช้ราคา R2 (ไม่มี customer code)
- **Normal Mode:** คำนวณด้วย LevelPrice + Price (มี customer code)
- **กระจก:** ราคาคำนวณเป็น บาท/ตร.ฟุต แต่แสดงเป็น บาท/แผ่น
- **อลูมิเนียม:** ราคาคำนวณเป็น บาท/กก. (UnitPrice × product_weight)

### 3. Cart Item Identity
สินค้าในตะกร้าถือว่าซ้ำกันเมื่อ:
- `sku` เหมือนกัน
- `variantCode` เหมือนกัน (ถ้ามี)
- `sqft_sheet` เหมือนกัน (ถ้ามี)

### 4. Cache Strategy
- **Customer data:** 15 นาที
- **Search results:** 1 นาที
- **Glass data:** 10 นาที
- **Mapping tables:** LRU cache (permanent)

### 5. Database Tables
**SQLite:**
- `Employees` - พนักงาน
- `Items_Test` - สินค้า (backup)
- `Quote_Header` - หัวใบเสนอราคา
- `Quote_Line` - รายการสินค้าในใบเสนอราคา
- `Invoice` - Invoice (backup)
- `Item_Update_Version` - version การอัปเดตราคา
- `Item_Update_Version_Detail` - รายละเอียดการอัปเดต
- `Rule` - กฎ cross-sell
- Mapping tables: `Aluminium_Brand`, `Glass_Color`, etc.

**MS SQL:**
- `Items_Test` - สินค้า (master)

**D365 BC API:**
- Customer API
- Invoice API

---

**เอกสารนี้ครอบคลุมโครงสร้างและการทำงานของระบบ Smart Pricing ทั้งหมด**
**สร้างเมื่อ:** 2025
**เวอร์ชัน:** 1.0.0

