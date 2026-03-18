# UXP SSO Integration Setup Guide

## ภาพรวม
SmartPricing รองรับการ login ผ่าน UXP Portal โดยใช้ Cookie-based JWT Authentication

## วิธีการทำงาน

### Flow การ Login:

1. **User คลิกปุ่ม "เข้าสู่ระบบผ่าน UXP"** ใน SmartPricing
   - Redirect ไป: `http://uxp-domain/auth/login?redirect=http://smartpricing-domain&appName=SmartPricing`

2. **User login ที่ UXP Portal**
   - UXP สร้าง JWT token และเก็บใน HTTP Cookie
   - Cookie name: `token`
   - Cookie settings: `httpOnly=true, secure=true, sameSite='Lax'`

3. **UXP redirect กลับมา SmartPricing**
   - ใช้ `window.location.href` redirect กลับ
   - Token อยู่ใน Cookie แล้ว

4. **SmartPricing auto-login**
   - ตรวจสอบว่ามี UXP Cookie หรือไม่
   - ส่ง Cookie ไปให้ backend verify
   - Backend สร้าง SmartPricing token ใหม่
   - Redirect ไป Dashboard

## สิ่งที่ต้องเตรียม

### 1. UXP Public Key
ต้องขอ Public Key (RS256) จากทีม UXP เพื่อใช้ verify JWT token

### 2. Backend Configuration

แก้ไขไฟล์ `backend/.env`:

```env
# ===== UXP SSO Configuration =====
UXP_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----
<PASTE_YOUR_PUBLIC_KEY_HERE>
-----END PUBLIC KEY-----

UXP_ISSUER=CentralPortal
UXP_AUDIENCE=https://localhost:9443/oauth2/token
```

### 3. Frontend Configuration

แก้ไขไฟล์ `frontend/.env`:

```env
VITE_UXP_LOGIN_URL=http://localhost:9443/auth/login
VITE_API_URL=http://localhost:8000
```

### 4. CORS Configuration

ใน `backend/main.py` ต้องตั้งค่า CORS ให้รองรับ UXP domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:9443",  # UXP Portal
        "https://uxp.company.com",  # Production UXP
        "https://smartpricing.company.com",  # Production SmartPricing
    ],
    allow_credentials=True,  # สำคัญ! ต้องเป็น True เพื่อรับ Cookie
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Cookie Domain (Production)

สำหรับ Production ต้องตั้งค่า Cookie domain ให้เหมือนกัน:
- UXP: `uxp.company.com`
- SmartPricing: `smartpricing.company.com`
- Cookie domain: `.company.com` (มีจุดนำหน้า)

## API Endpoints

### POST `/api/auth/uxp-login`
Login ผ่าน UXP token (อ่านจาก Cookie)

**Request:**
- Cookie: `token=<UXP_JWT_TOKEN>`
- Headers: `withCredentials: true`

**Response:**
```json
{
  "token": "SmartPricing_JWT_Token",
  "employee": {
    "id": "employee_id",
    "name": "Employee Name",
    "branchId": "branch_code"
  },
  "source": "UXP"
}
```

### GET `/api/auth/check-uxp-session`
ตรวจสอบว่ามี UXP session อยู่หรือไม่

**Response:**
```json
{
  "hasSession": true,
  "username": "user123",
  "branchCode": "BK01"
}
```

## Testing

### 1. Local Development

```bash
# Terminal 1: Start UXP (port 9443)
cd UXP_Servicebus
npm run dev

# Terminal 2: Start SmartPricing Backend (port 8000)
cd SmartPricingDeployment/backend
python main.py

# Terminal 3: Start SmartPricing Frontend (port 5173)
cd SmartPricingDeployment/frontend
npm run dev
```

### 2. Test Flow

1. เปิด browser ไปที่ `http://localhost:5173`
2. คลิกปุ่ม "เข้าสู่ระบบผ่าน UXP"
3. Login ที่ UXP Portal
4. ควรจะ redirect กลับมาและเข้า Dashboard อัตโนมัติ

### 3. Debug

เปิด DevTools → Application → Cookies:
- ตรวจสอบว่ามี Cookie ชื่อ `token` หรือไม่
- ตรวจสอบ domain ของ Cookie
- ตรวจสอบ httpOnly, secure, sameSite settings

## Troubleshooting

### Error: "ไม่พบ token จาก UXP"

**สาเหตุ:**
- Cookie ไม่ถูกส่งไปกับ request
- Domain ไม่ตรงกัน

**วิธีแก้:**
1. ตรวจสอบ `withCredentials: true` ใน axios config
2. ตรวจสอบ CORS `allow_credentials=True`
3. ตรวจสอบ Cookie domain (ต้องเป็น shared domain)

### Error: "Token ไม่ถูกต้อง"

**สาเหตุ:**
- Public Key ไม่ถูกต้อง
- Token format ผิด

**วิธีแก้:**
1. ตรวจสอบ Public Key ใน `.env`
2. ตรวจสอบว่า token เป็น JWT format
3. ตรวจสอบ issuer และ audience

### Cookie ไม่ถูกส่งไปกับ request

**สาเหตุ:**
- Domain ไม่ตรงกัน (localhost vs 127.0.0.1)
- sameSite policy

**วิธีแก้:**
1. ใช้ domain เดียวกัน (localhost ทั้งคู่)
2. ตั้งค่า Cookie domain เป็น `.company.com` (production)
3. ตรวจสอบ sameSite setting

## Production Deployment

### 1. Domain Setup
```
UXP:           https://uxp.company.com
SmartPricing:  https://smartpricing.company.com
Cookie Domain: .company.com
```

### 2. Environment Variables

**Backend `.env`:**
```env
UXP_PUBLIC_KEY=<production_public_key>
UXP_ISSUER=CentralPortal
UXP_AUDIENCE=https://uxp.company.com/oauth2/token
```

**Frontend `.env`:**
```env
VITE_UXP_LOGIN_URL=https://uxp.company.com/auth/login
VITE_API_URL=https://smartpricing.company.com/api
```

### 3. CORS Configuration
```python
allow_origins=[
    "https://uxp.company.com",
    "https://smartpricing.company.com",
]
```

## Security Checklist

- [ ] ใช้ HTTPS ใน production
- [ ] Public Key ถูกต้อง
- [ ] Cookie httpOnly=true
- [ ] Cookie secure=true (HTTPS only)
- [ ] CORS ตั้งค่าถูกต้อง
- [ ] Token expiration ถูกตรวจสอบ
- [ ] Verify signature ทุกครั้ง

## Dependencies

```bash
# Backend
pip install PyJWT cryptography

# Frontend
npm install axios
```
