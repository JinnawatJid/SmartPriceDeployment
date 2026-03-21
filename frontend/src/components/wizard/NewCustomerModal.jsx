import React, { useState } from "react";

export default function NewCustomerModal({ open, onClose, onConfirm }) {
  const [customerId, setCustomerId] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [taxNo, setTaxNo] = useState("");
  const [error, setError] = useState("");

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h3 className="text-lg font-bold text-gray-800 mb-4">เพิ่มลูกค้าใหม่</h3>

        <div className="space-y-3">
          <input
            type="text"
            placeholder="รหัสลูกค้า (Customer ID)"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="w-full rounded-lg border border-gray-300 p-3 text-sm"
          />

          <input
            type="text"
            placeholder="ชื่อลูกค้า"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-gray-300 p-3 text-sm"
          />

          <div>
            <input
              type="text"
              placeholder="เบอร์โทรศัพท์ *"
              value={phone}
              onChange={(e) => {
                setPhone(e.target.value);
                if (error) setError("");
              }}
              className={`w-full rounded-lg border p-3 text-sm ${
                error ? "border-red-500" : "border-gray-300"
              }`}
              required
            />
            {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
          </div>

          <input
            type="text"
            placeholder="เลขประจำตัวผู้เสียภาษี (Tax No.) "
            value={taxNo}
            onChange={(e) => setTaxNo(e.target.value)}
            className="w-full rounded-lg border border-gray-300 p-3 text-sm"
          />
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-md border hover:bg-gray-100"
          >
            ยกเลิก
          </button>

          <button
            onClick={() => {
              if (!phone.trim()) {
                setError("กรุณากรอกเบอร์โทรศัพท์");
                return;
              }
              
              onConfirm({
                id: customerId || "",
                name,
                phone,
                tax_no: taxNo,
                isTempCustomer: true,
              });
              setCustomerId("");
              setName("");
              setPhone("");
              setTaxNo("");
              setError("");
              onClose();
            }}
            className="px-4 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700"
          >
            บันทึก
          </button>
        </div>
      </div>
    </div>
  );
}
