// src/components/wizard/CustomerDisplay.jsx
import React from "react";
import { useQuote } from "../../hooks/useQuote.js";

const CustomerDisplay = () => {
  const { state, dispatch } = useQuote();
  const customer = state.customer;

  if (!customer) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-center">
        <p className="text-gray-500">ยังไม่ได้เลือกข้อมูลลูกค้า</p>
        <button
          onClick={() => dispatch({ type: "SET_STEP", payload: 3 })}
          className="mt-2 text-sm font-semibold text-blue-600 hover:underline"
        >
          ไปที่หน้าเลือกลูกค้า &rarr;
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h4 className="text-lg font-bold text-gray-900">{customer.name}</h4>
      </div>
      <p className="text-sm text-gray-600">รหัส: {customer.id}</p>
      <p className="text-sm text-gray-600">โทร: {customer.phone}</p>
    </div>
  );
};

export default CustomerDisplay;
