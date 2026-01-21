// src/components/wizard/SummaryRow.jsx
import React from "react";

const SummaryRow = ({ label, value, isTotal = false }) => (
  <div className="flex justify-between py-2">
    <span className={`font-semibold ${isTotal ? "text-xl text-gray-900" : "text-gray-600"}`}>
      {label}
    </span>
    <span className={`font-bold ${isTotal ? "text-sm text-blue-600" : "text-gray-800"}`}>
      {value}
    </span>
  </div>
);

export default SummaryRow;
