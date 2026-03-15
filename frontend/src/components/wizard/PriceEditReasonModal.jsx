// src/components/wizard/PriceEditReasonModal.jsx
import React, { useState } from "react";

function PriceEditReasonModal({ isOpen, onClose, onConfirm }) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = () => {
    if (!reason.trim()) {
      setError("กรุณาระบุเหตุผลการแก้ไขค่าขนส่ง");
      return;
    }

    onConfirm(reason.trim());
    setReason("");
    setError("");
  };

  const handleClose = () => {
    setReason("");
    setError("");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          เหตุผลการแก้ไขค่าขนส่ง
        </h2>

        <p className="mb-4 text-sm text-gray-600">
          กรุณาระบุเหตุผลในการแก้ไขค่าขนส่ง (บังคับกรอก)
        </p>

        <textarea
          value={reason}
          onChange={(e) => {
            setReason(e.target.value);
            setError("");
          }}
          placeholder="ระบุเหตุผล เช่น ลูกค้าขอส่วนลด, ค่าขนส่งพิเศษ, ฯลฯ"
          className="w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={4}
          autoFocus
        />

        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={handleClose}
            className="rounded-lg bg-gray-200 px-4 py-2 font-semibold text-gray-700 hover:bg-gray-300"
          >
            ยกเลิก
          </button>
          <button
            onClick={handleSubmit}
            className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700"
          >
            ยืนยัน
          </button>
        </div>
      </div>
    </div>
  );
}

export default PriceEditReasonModal;
