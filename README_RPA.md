# RPA Script: Click +New in D365 BC Sales Quotes

สคริปต์ RPA สำหรับคลิกปุ่ม "+New" ในหน้า Sales Quotes ของ Dynamics 365 Business Central

**เชื่อมต่อกับแท็บเบราว์เซอร์ที่เปิดอยู่แล้ว ไม่เปิดแท็บใหม่**

## การติดตั้ง

1. ติดตั้ง Python packages:
```bash
pip install -r requirements_rpa.txt
```

2. ติดตั้ง Playwright browsers:
```bash
playwright install chromium
```

## การตั้งค่า

1. คัดลอกไฟล์ `.env.example` เป็น `.env`:
```bash
cp .env.example .env
```

2. (Optional) แก้ไข `.env` ถ้าต้องการเปลี่ยน CDP port:
```
CDP_URL=http://localhost:9222
```

## การใช้งาน

### ขั้นตอนที่ 1: เปิด Chrome ด้วย Remote Debugging

**วิธีที่ 1: ใช้ batch script (แนะนำ)**
```bash
start_chrome_debug.bat
```

**วิธีที่ 2: เปิด Chrome ด้วย command line**
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

### ขั้นตอนที่ 2: เปิดหน้า D365 BC Sales Quotes

เปิดแท็บใน Chrome ที่เพิ่งเปิด แล้วไปที่หน้า Sales Quotes ของคุณ

### ขั้นตอนที่ 3: รันสคริปต์ RPA

```bash
python rpa_click_new_quote.py
```

สคริปต์จะเชื่อมต่อกับแท็บที่เปิดอยู่และคลิกปุ่ม +New ให้อัตโนมัติ

## คุณสมบัติ

- ✅ เชื่อมต่อกับ Chrome ที่เปิดอยู่แล้ว (ไม่เปิดแท็บใหม่)
- ✅ ใช้แท็บปัจจุบันที่คุณเปิดอยู่
- ✅ คลิกปุ่ม "+New" อัตโนมัติ
- ✅ ลอง selector หลายแบบเพื่อหาปุ่ม
- ✅ บันทึก screenshot เมื่อเกิดข้อผิดพลาด
- ✅ แสดงสถานะการทำงานแบบ real-time
- ✅ ไม่ปิดเบราว์เซอร์หลังจากเสร็จ

## การแก้ไขปัญหา

### ❌ Error: "Could not connect to browser"

**สาเหตุ:** Chrome ไม่ได้เปิดด้วย remote debugging mode

**วิธีแก้:**
1. ปิด Chrome ทั้งหมด
2. เปิด Chrome ใหม่ด้วย `start_chrome_debug.bat`
3. รันสคริปต์อีกครั้ง

### ❌ Error: "No pages found"

**สาเหตุ:** ไม่มีแท็บเปิดอยู่ใน Chrome

**วิธีแก้:**
1. เปิดแท็บใหม่ใน Chrome
2. ไปที่หน้า D365 BC Sales Quotes
3. รันสคริปต์อีกครั้ง

### ❌ ถ้าหาปุ่ม +New ไม่เจอ

1. ดู screenshot ที่บันทึกไว้: `debug_screenshot.png`
2. ตรวจสอบ selector ของปุ่มจริงๆ ในหน้าเว็บ (กด F12 เปิด DevTools)
3. เพิ่ม selector ใหม่ใน `new_button_selectors` list ในไฟล์ `rpa_click_new_quote.py`

### 💡 ตรวจสอบว่า Chrome เปิด remote debugging หรือไม่

เปิดเบราว์เซอร์ใหม่และไปที่: `http://localhost:9222/json`

ถ้าเห็น JSON response แสดงว่าเปิดสำเร็จแล้ว

## การปรับแต่ง

### เปลี่ยน CDP port

แก้ไขใน `.env`:
```
CDP_URL=http://localhost:9223
```

และเปิด Chrome ด้วย port ใหม่:
```bash
chrome.exe --remote-debugging-port=9223
```

### เลือกแท็บที่ต้องการ

แก้ไขในไฟล์ `rpa_click_new_quote.py`:

```python
# ใช้แท็บแรก (default)
page = pages[0]

# ใช้แท็บที่ 2
page = pages[1]

# หาแท็บที่มี URL ตรงกับที่ต้องการ
for p in pages:
    if 'Sales%20Quotes' in p.url:
        page = p
        break
```

### เพิ่มความเร็ว

ลด `time.sleep()` ในไฟล์:
```python
time.sleep(0.5)  # เร็วขึ้น
```

## ตัวอย่างการใช้งานขั้นสูง

### รันหลายครั้ง
```python
for i in range(5):
    print(f"Run {i+1}/5")
    click_new_quote()
    time.sleep(10)
```

### เลือกแท็บที่ต้องการโดยอัตโนมัติ

```python
# หาแท็บที่เป็นหน้า Sales Quotes
target_page = None
for p in pages:
    if 'businesscentral' in p.url.lower() and 'sales' in p.url.lower():
        target_page = p
        break

if target_page:
    page = target_page
else:
    print("❌ Could not find Sales Quotes tab")
    return
```
