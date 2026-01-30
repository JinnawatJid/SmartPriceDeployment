# Special Price Request Components

คอมโพเนนต์สำหรับจัดการคำขอราคาพิเศษ

## โครงสร้างไฟล์

- `SpecialPriceRequestButton.jsx` - ปุ่มสำหรับเปิด modal ขอราคาพิเศษ
- `SpecialPriceRequestModal.jsx` - Modal เวอร์ชันเก่า (deprecated)
- `SpecialPriceRequestModal_v2.jsx` - Modal เวอร์ชันใหม่ (แบบย่อ ไม่แสดงราคา W1)
- `ApprovalPDFsPage.jsx` - หน้าแสดงรายการ PDF ที่ผู้อนุมัติแนบมา

## การใช้งาน

### SpecialPriceRequestButton
```jsx
import SpecialPriceRequestButton from "../../components/special_price_request/SpecialPriceRequestButton.jsx";

<SpecialPriceRequestButton
  onClick={() => setModalOpen(true)}
  disabled={cart.length === 0}
/>
```

### SpecialPriceRequestModal_v2
```jsx
import SpecialPriceRequestModal from "../../components/special_price_request/SpecialPriceRequestModal_v2.jsx";

<SpecialPriceRequestModal
  isOpen={modalOpen}
  onClose={() => setModalOpen(false)}
  quoteNo="BSQT-2601/0001"
  cart={cart}
  customer={customer}
  onSuccess={() => {
    // Handle success
  }}
/>
```

### ApprovalPDFsPage
```jsx
// Route: /approval-pdfs/:requestNumber
// แสดงรายการ PDF ที่ผู้อนุมัติแนบมา
```
