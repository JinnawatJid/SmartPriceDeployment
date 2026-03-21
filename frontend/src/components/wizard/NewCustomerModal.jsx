import React, { useState } from "react";

export default function NewCustomerModal({ open, onClose, onConfirm }) {
  const [customerId, setCustomerId] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [taxNo, setTaxNo] = useState("");
  const [error, setError] = useState("");

  if (!open) return null;

  const handleConfirm = () => {
    // ✅ ตรวจสอบรหัสลูกค้า
    if (!customerId.trim()) {
      setError("กรุณากรอกรหัสลูกค้า");
      return;
    }

    // ✅ ตรวจสอบชื่อลูกค้า
    if (!name.trim()) {
      setError("กรุณากรอกชื่อลูกค้า");
      return;
    }

    // ✅ ตรวจสอบเบอร์โทรศัพท์
    if (!phone.trim()) {
      setError("กรุณากรอกเบอร์โทรศัพท์");
      return;
    }

    // ✅ ตรวจสอบรูปแบบรหัสลูกค้า (ตัวอักษร, ตัวเลข, ขีดกลาง เท่านั้น)
    const customerIdRegex = /^[A-Za-z0-9\-]+$/;
    if (!customerIdRegex.test(customerId.trim())) {
      setError("รหัสลูกค้าต้องเป็นตัวอักษร ตัวเลข หรือขีดกลางเท่านั้น");
      return;
    }

    // ✅ ตรวจสอบความยาวรหัสลูกค้า (ไม่เกิน 20 ตัวอักษร)
    if (customerId.trim().length > 20) {
      setError("รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร");
      return;
    }

    onConfirm({
      id: customerId.trim(),
      name: name.trim(),
      phone: phone.trim(),
      tax_no: taxNo.trim(),
      isTempCustomer: true,
    });

    // Reset form
    setCustomerId("");
    setName("");
    setPhone("");
    setTaxNo("");
    setError("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h3 className="text-lg font-bold text-gray-800 mb-4">เพิ่มลูกค้าใหม่</h3>
        <div className="text-sm text-red-600 mb-4">
          *กรุณาเพิ่มลูกค้าใหม่ในระบบ Dynamics 365 ก่อน และกรอกชื่อพร้อมรหัสลูกค้าในช่องนี้ให้ตรงกับข้อมูลในระบบทุก*
        </div>

        <div className="space-y-3">
          {/* ✅ รหัสลูกค้า - Required */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              รหัสลูกค้า <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="เช่น CUST-001 หรือ ABC123"
              value={customerId}
              onChange={(e) => {
                // ✅ แปลงเป็นตัวพิมพ์ใหญ่อัตโนมัติ
                setCustomerId(e.target.value.toUpperCase());
                if (error) setError("");
              }}
              className={`w-full rounded-lg border p-3 text-sm uppercase ${
                error && !customerId.trim() ? "border-red-500 bg-red-50" : "border-gray-300"
              }`}
              required
            />
          </div>

          {/* ✅ ชื่อลูกค้า - Required */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ชื่อลูกค้า <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="เช่น บริษัท ABC จำกัด"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (error) setError("");
              }}
              className={`w-full rounded-lg border p-3 text-sm ${
                error && !name.trim() ? "border-red-500 bg-red-50" : "border-gray-300"
              }`}
              required
            />
          </div>

          {/* เบอร์โทรศัพท์ - Required */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              เบอร์โทรศัพท์ <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="เช่น 0812345678"
              value={phone}
              onChange={(e) => {
                setPhone(e.target.value);
                if (error) setError("");
              }}
              className={`w-full rounded-lg border p-3 text-sm ${
                error && !phone.trim() ? "border-red-500 bg-red-50" : "border-gray-300"
              }`}
              required
            />
          </div>

          {/* เลขประจำตัวผู้เสียภาษี - Optional */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              เลขประจำตัวผู้เสียภาษี
            </label>
            <input
              type="text"
              placeholder="เช่น 1234567890123"
              value={taxNo}
              onChange={(e) => {
                setTaxNo(e.target.value);
                if (error) setError("");
              }}
              className="w-full rounded-lg border border-gray-300 p-3 text-sm"
            />
          </div>

          {/* ✅ Error Message */}
          {error && (
            <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600 font-medium">{error}</p>
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-md border border-gray-300 hover:bg-gray-100 font-medium"
          >
            ยกเลิก
          </button>

          <button
            onClick={handleConfirm}
            className="px-4 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 font-medium"
          >
            บันทึก
          </button>
        </div>
      </div>
    </div>
  );
}
