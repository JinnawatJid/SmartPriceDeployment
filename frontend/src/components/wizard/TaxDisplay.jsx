// src/components/wizard/TaxDisplay.jsx
import React from "react";
import { useQuote } from "../../hooks/useQuote.js";

const TaxDisplay = () => {
  const { state, dispatch } = useQuote();

  const taxLabel = state.needsTax ? "รับใบกำกับภาษี" : "ไม่รับ";
  const deliveryLabel = state.deliveryType === "DELIVERY" ? "จัดส่ง" : "รับเอง";

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h4 className="text-lg font-bold text-gray-900">ข้อมูลการชำระเงิน</h4>
      </div>
      <p className="text-sm text-gray-600">
        <span className="font-medium">ใบกำกับภาษี:</span> {taxLabel}
      </p>
      <p className="text-sm text-gray-600">
        <span className="font-medium">การจัดส่ง:</span> {deliveryLabel}
      </p>
    </div>
  );
};

export default TaxDisplay;
