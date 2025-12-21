// src/components/wizard/SelectionButton.jsx
import React from 'react';

// ไอคอน Check ที่ใช้ภายใน
const CheckmarkIcon = () => (
  <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
  </svg>
);

const SelectionButton = ({ icon, title, description, selected, onClick }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative flex items-center mr-4 space-x-2 rounded-lg  p-2 text-left transition-all ${
        selected
          ? ' bg-blue-50 '
          : ' bg-white'
      }`}
    >
      {/* วงกลม Checkbox ด้านขวา */}
      <div 
        className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border-2 ${
          selected ? 'border-blue-600 bg-blue-600' : 'border-gray-300 bg-white'
        }`}
      >
        {selected && <CheckmarkIcon />}
      </div>

      {/* ไอคอนและข้อความ */}
      <div className="flex-shrink-0 text-blue-600">{icon}</div>
      <div className="flex-1">
        <h4 className="text-sm font-bold text-gray-900">{title}</h4>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
    </button>
  );
};

export default SelectionButton;