// src/components/wizard/CategoryCard.jsx (REFACTORED - FIX)
import React from 'react';

// --- 1. ไอคอน SVG (ใช้ไอคอนตัวอักษรแทนไอคอนเฉพาะ) ---
const CategoryIcon = ({ letter }) => (
  <span className="text-2xl font-bold">
    {/* ❗️ 1. (แก้ไข) ถ้า letter เป็น null ให้แสดง '?' */}
    {letter || '?'}
  </span>
);

// --- 2. ฟังก์ชันช่วยเลือกสี ---
const categoryColors = [
  'bg-blue-100 text-blue-700',
  'bg-green-100 text-green-700',
  'bg-yellow-100 text-yellow-700',
  'bg-red-100 text-red-700',
  'bg-purple-100 text-purple-700',
  'bg-pink-100 text-pink-700',
  'bg-indigo-100 text-indigo-700',
];

const getCategoryStyle = (categoryName) => {
  // ❗️❗️ --- จุดที่แก้ไข (นี่คือบรรทัดที่ 19 ของคุณ) --- ❗️❗️
  // 2. เพิ่ม "ตัวป้องกัน" (Guard Clause)
  if (!categoryName) {
    return categoryColors[0]; // คืนสี default (สีฟ้า)
  }
  // --- จบจุดที่แก้ไข ---

  // (โค้ดเดิมจะปลอดภัยแล้ว)
  const charCode = categoryName.charCodeAt(0) || 0;
  const index = charCode % categoryColors.length;
  return categoryColors[index];
};

// --- 3. คอมโพเนนต์การ์ด ---\
const CategoryCard = ({ category, name, count, onClick }) => {
  const style = getCategoryStyle(category);

  return (
    <div
      onClick={() => onClick(category)}
      className="group cursor-pointer rounded-2xl  border border-gray-200 bg-white  shadow-md transition-all duration-300 "
    >
      <div className="flex flex-col items-center justify-center space-y-1 p-2 bg-[#DC2626] rounded-lg">
        {/* Icon */}
        <div
          className={`flex items-center text-white justify-center transition-all duration-300 group-hover:scale-105`}
        >
          <CategoryIcon letter={category ? category[0] : null} />
        </div>
        {/* Text */}
        <div>
          <p className="text-sm text-white text-center">{count} รายการ</p>
        </div>
      </div>
    </div>
  );
};

export default CategoryCard;