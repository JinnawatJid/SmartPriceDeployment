# ฟีเจอร์: เหตุผลการแก้ไขค่าขนส่ง (Shipping Edit Reason)

## สรุป
เพิ่มฟีเจอร์ Modal สำหรับบังคับให้ผู้ใช้ระบุเหตุผลเมื่อมีการแก้ไขค่าขนส่งในหน้า Step6_Summary ก่อนบันทึกใบเสนอราคา

## ไฟล์ที่เปลี่ยนแปลง

### 1. `frontend/src/components/wizard/PriceEditReasonModal.jsx` (ไฟล์ใหม่)
- สร้าง Modal component สำหรับรับเหตุผลการแก้ไขค่าขนส่ง
- บังคับให้กรอกข้อความก่อนยืนยัน
- มี validation ป้องกันการส่งค่าว่าง

### 2. `frontend/src/pages/CreateQuote/Step6_Summary.jsx`
#### เพิ่ม Import
```javascript
import PriceEditReasonModal from "../../components/wizard/PriceEditReasonModal.jsx";
```

#### เพิ่ม State
```javascript
const [showPriceEditReasonModal, setShowPriceEditReasonModal] = useState(false);
const [priceEditReason, setPriceEditReason] = useState("");
const [pendingSaveStatus, setPendingSaveStatus] = useState(null);
```

#### แก้ไข `buildQuotationPayload`
- เพิ่ม parameter `editReason` เพื่อรับเหตุผลการแก้ไขค่าขนส่ง
- รวมเหตุผลการแก้ไขค่าขนส่งเข้ากับ `note` พร้อม timestamp
- บันทึกลงคอลัมน์ `Remark` ในตาราง `Quote_Header`

#### เพิ่มฟังก์ชัน `hasShippingEdits`
```javascript
const hasShippingEdits = () => {
  return state.deliveryType === "DELIVERY" && editingShippingCost;
};
```
- ตรวจสอบว่ามีการแก้ไขค่าขนส่งหรือไม่

#### แก้ไข `handleSaveQuotation`
- ตรวจสอบว่ามีการแก้ไขค่าขนส่งหรือไม่ก่อนบันทึก
- ถ้ามีการแก้ไขค่าขนส่งและยังไม่ได้ใส่เหตุผล → เปิด Modal
- ถ้ามีเหตุผลแล้ว → บันทึกตามปกติ

#### เพิ่มฟังก์ชัน `handlePriceEditReasonConfirm`
- รับเหตุผลจาก Modal
- ปิด Modal
- เรียก `handleSaveQuotation` ต่อด้วย status ที่รอไว้

#### เพิ่ม Modal Component
```jsx
<PriceEditReasonModal
  isOpen={showPriceEditReasonModal}
  onClose={() => {
    setShowPriceEditReasonModal(false);
    setPendingSaveStatus(null);
  }}
  onConfirm={handlePriceEditReasonConfirm}
/>
```

## การทำงาน

### Flow การบันทึก
1. ผู้ใช้แก้ไขค่าขนส่ง (double-click ที่ช่องค่าขนส่ง)
2. ผู้ใช้กดปุ่ม "Save Draft" หรือ "บันทึก"
3. ระบบตรวจสอบว่ามีการแก้ไขค่าขนส่งหรือไม่
4. ถ้ามีการแก้ไขค่าขนส่ง:
   - เปิด Modal ขอเหตุผล
   - ผู้ใช้ต้องกรอกเหตุผล (บังคับ)
   - กดยืนยัน → บันทึกเหตุผลและดำเนินการบันทึกต่อ
5. ถ้าไม่มีการแก้ไขค่าขนส่ง:
   - บันทึกตามปกติทันที

### รูปแบบการบันทึก Remark
```
[แก้ไขค่าขนส่ง 15/3/2026 14:30:25] ลูกค้าขอส่วนลด 10%
```

- เพิ่มข้อความเหตุผลต่อท้าย `state.remark` เดิม (ถ้ามี)
- มี timestamp แบบ locale ไทย
- แยกบรรทัดด้วย `\n`

## Backend Support
Backend (`backend/quotation.py`) รองรับการบันทึก Remark แล้ว:
- คอลัมน์ `Remark` ในตาราง `Quote_Header`
- รับค่าจาก `payload.get("note", "")`
- บันทึกทั้งตอน CREATE และ UPDATE

## การทดสอบ
1. เปิดหน้า Step6_Summary
2. เพิ่มสินค้าในตะกร้า
3. ตั้งค่าการส่งเป็น "DELIVERY"
4. Double-click ที่ช่องค่าขนส่ง เพื่อแก้ไข
5. เปลี่ยนค่าขนส่งและกดบันทึก
6. กดปุ่ม "Save Draft"
7. ตรวจสอบว่า Modal ขึ้นมาขอเหตุผล
8. ลองกดยืนยันโดยไม่กรอก → ต้องมี error message
9. กรอกเหตุผลและกดยืนยัน → บันทึกสำเร็จ
10. ตรวจสอบในฐานข้อมูลว่าคอลัมน์ `Remark` มีข้อความเหตุผล

## หมายเหตุ
- Modal จะขึ้นเฉพาะเมื่อมีการแก้ไขค่าขนส่ง (ตัวแปร `editingShippingCost` เป็น true)
- ถ้าไม่มีการแก้ไขค่าขนส่ง จะไม่มี Modal ขึ้น
- เหตุผลจะถูกบันทึกพร้อม timestamp ในรูปแบบภาษาไทย
- ใช้ได้เฉพาะเมื่อ `deliveryType === "DELIVERY"` เท่านั้น
