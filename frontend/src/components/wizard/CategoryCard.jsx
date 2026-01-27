// src/components/wizard/CategoryCard.jsx (REFACTORED - FIX)
import React from "react";

// --- 1. ไอคอน SVG (ใช้ไอคอนตัวอักษรแทนไอคอนเฉพาะ) ---
const CategoryIcon = ({ letter }) => (
  <span className="text-2xl font-bold">
    {/* ❗️ 1. (แก้ไข) ถ้า letter เป็น null ให้แสดง '?' */}
    {letter || "?"}
  </span>
);
const CATEGORY_LABEL_TH = {
  G: "กระจก",
  A: "อลูมิเนียม",
  S: "กาว",
  Y: "ยิปซัม",
  C: "ซีลายน์",
  E: "อุปกรณ์และอื่นๆ",
};
const getCategoryLabel = (code) => {
  if (!code) return "ไม่ระบุหมวด";
  return CATEGORY_LABEL_TH[code] || code;
};

// --- 2. ฟังก์ชันช่วยเลือกสี ---
const categoryColors = [
  "bg-blue-100 text-blue-700",
  "bg-green-100 text-green-700",
  "bg-yellow-100 text-yellow-700",
  "bg-red-100 text-red-700",
  "bg-purple-100 text-purple-700",
  "bg-pink-100 text-pink-700",
  "bg-indigo-100 text-indigo-700",
];

const getCategoryStyle = (categoryName) => {
  if (!categoryName) {
    return categoryColors[0];
  }

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
        <h3 className="text-xl text-white font-semibold">
          {getCategoryLabel(category)}{" "}
          <span className="text-xl opacity-90">({category})</span>
        </h3>

        {/* Text */}
        <div>
          <p className="text-sm text-white text-center">{count} รายการ</p>
        </div>
      </div>
    </div>
  );
};

export default CategoryCard;
