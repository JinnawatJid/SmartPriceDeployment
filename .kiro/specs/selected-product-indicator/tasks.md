# แผนการพัฒนา: Selected Product Indicator

## ภาพรวม

แผนนี้จะแบ่งการพัฒนาฟีเจอร์ Selected Product Indicator ออกเป็นขั้นตอนย่อยๆ ที่สามารถทำได้ทีละขั้น โดยเริ่มจากการสร้าง hook สำหรับตรวจสอบสถานะ จากนั้นปรับปรุง ItemCard component และสุดท้ายเพิ่มการทดสอบเพื่อให้มั่นใจในความถูกต้อง

## Tasks

- [x] 1. สร้าง useSelectedStatus Hook
  - สร้างไฟล์ `frontend/src/hooks/useSelectedStatus.js`
  - Implement logic สำหรับตรวจสอบว่าสินค้าถูกเลือกแล้วหรือไม่
  - รองรับการ normalize variantCode (null, undefined, "") และ sqft_sheet
  - รองรับทั้ง field name `sqft_sheet` และ `sqft`
  - จัดการ edge case เมื่อ sku เป็น null/undefined/empty
  - _Requirements: 1.1, 5.1, 5.2, 5.3_

- [ ]* 1.1 เขียน property test สำหรับ useSelectedStatus hook
  - **Property 1: Selection Status Detection**
  - **Validates: Requirements 1.1, 5.1, 5.2**
  - ใช้ fast-check สร้าง random SKU, variantCode, sqft, และ cart
  - ทดสอบว่า hook คืนค่า true ก็ต่อเมื่อสินค้าอยู่ใน cart
  - รัน 100 iterations
  - _Requirements: 1.1, 5.1, 5.2_

- [ ]* 1.2 เขียน property test สำหรับ variant independence
  - **Property 4: Product Identity Matching with Variants**
  - **Validates: Requirements 5.2**
  - ทดสอบว่าสินค้า SKU เดียวกันแต่ variant ต่างกันมีสถานะแยกกัน
  - ทดสอบว่ากระจกขนาดต่างกันมีสถานะแยกกัน
  - รัน 100 iterations
  - _Requirements: 5.2_

- [ ]* 1.3 เขียน unit tests สำหรับ edge cases
  - ทดสอบกรณี SKU เป็น null, undefined, empty string
  - ทดสอบกรณี variantCode เป็น null vs undefined vs ""
  - ทดสอบกรณี sqft_sheet เป็น undefined vs 0
  - _Requirements: 5.3_

- [x] 2. ปรับปรุง ItemCard Component
  - แก้ไขไฟล์ `frontend/src/components/wizard/ItemCard.jsx`
  - Import และใช้ `useSelectedStatus` hook
  - เพิ่ม conditional styling สำหรับสินค้าที่ถูกเลือก (text-blue-600, font-semibold)
  - เพิ่ม visual indicator "✓" สำหรับสินค้าที่ถูกเลือก
  - รักษา functionality เดิมทั้งหมด (onAdd callback)
  - _Requirements: 1.2, 1.3, 2.1, 4.1_

- [ ]* 2.1 เขียน property test สำหรับ visual indicator consistency
  - **Property 2: Visual Indicator Consistency**
  - **Validates: Requirements 1.2, 1.3, 2.1**
  - ทดสอบว่าสินค้าที่ selected มี CSS classes ถูกต้อง
  - ทดสอบว่าสินค้าที่ไม่ selected มี default classes
  - รัน 100 iterations
  - _Requirements: 1.2, 1.3, 2.1_

- [ ]* 2.2 เขียน property test สำหรับ initial state correctness
  - **Property 3: Initial State Correctness**
  - **Validates: Requirements 3.3**
  - ทดสอบว่าเมื่อ render component ครั้งแรก สถานะถูกต้องตาม cart
  - ใช้ random cart state
  - รัน 100 iterations
  - _Requirements: 3.3_

- [ ]* 2.3 เขียน unit tests สำหรับ ItemCard rendering
  - ทดสอบ rendering ของสินค้าที่ selected
  - ทดสอบ rendering ของสินค้าที่ไม่ selected
  - ทดสอบว่ามี indicator "✓" ปรากฏเมื่อ selected
  - ทดสอบว่า onAdd callback ยังทำงานได้ปกติ
  - _Requirements: 1.2, 1.3, 2.1, 4.1_

- [x] 3. Checkpoint - ทดสอบการทำงานพื้นฐาน
  - รัน tests ทั้งหมดให้ผ่าน
  - ทดสอบ manual ใน browser ว่า ItemCard แสดงสถานะถูกต้อง
  - ตรวจสอบว่าไม่มี console errors หรือ warnings
  - ถามผู้ใช้หากมีคำถามหรือพบปัญหา

- [ ]* 4. เขียน integration tests สำหรับ real-time updates
  - ทดสอบการเพิ่มสินค้าเข้า cart และ UI อัพเดททันที
  - ทดสอบการลบสินค้าออกจาก cart และ UI กลับเป็น default
  - ทดสอบการเปิด picker ใหม่และแสดงสถานะถูกต้อง
  - _Requirements: 3.1, 3.2, 3.3_

- [ ]* 4.1 เขียน property test สำหรับ invalid identifier handling
  - **Property 5: Invalid Product Identifier Handling**
  - **Validates: Requirements 5.3**
  - ทดสอบว่าสินค้าที่มี SKU invalid แสดง default styling
  - ทดสอบว่าไม่ throw error
  - รัน 100 iterations
  - _Requirements: 5.3_

- [x] 5. ตรวจสอบความสอดคล้องในทุก Picker
  - ทดสอบ manual ใน ItemPickerModal
  - ทดสอบ manual ใน GlassPickerModal
  - ทดสอบ manual ใน AccessoriesPicker, AluminiumPicker, CLinePicker, GypsumPicker, SealantPicker
  - ตรวจสอบว่าสีและ styling เหมือนกันทุก picker
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 6. Final Checkpoint - ตรวจสอบความสมบูรณ์
  - รัน test suite ทั้งหมดให้ผ่าน
  - ตรวจสอบ code coverage (เป้าหมาย 90%+)
  - ทดสอบ end-to-end flow: เลือกสินค้า → เห็นสถานะ → เพิ่มสินค้า → สถานะอัพเดท
  - ตรวจสอบว่าไม่กระทบ functionality เดิม
  - ถามผู้ใช้หากมีคำถามหรือต้องการปรับปรุง

## หมายเหตุ

- Tasks ที่มีเครื่องหมาย `*` เป็น optional และสามารถข้ามได้เพื่อให้ได้ MVP เร็วขึ้น
- แต่ละ task อ้างอิง requirements เฉพาะเจาะจงเพื่อความชัดเจน
- Checkpoint tasks ช่วยให้มั่นใจว่าแต่ละขั้นตอนทำงานถูกต้อง
- Property tests ตรวจสอบความถูกต้องแบบครอบคลุม
- Unit tests ตรวจสอบกรณีเฉพาะเจาะจงและ edge cases
- Integration tests ตรวจสอบการทำงานร่วมกันของ components
