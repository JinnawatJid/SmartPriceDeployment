import React from "react";

const CATEGORIES = [
  { code: "A", label: "อลูมิเนียม", color: "bg-blue-50 text-blue-700 border-blue-300" },
  { code: "E", label: "อุปกรณ์เสริม", color: "bg-green-50 text-green-700 border-green-300" },
  { code: "G", label: "กระจก", color: "bg-cyan-50 text-cyan-700 border-cyan-300" },
  { code: "C", label: "C-Line / โครงคร่าว", color: "bg-purple-50 text-purple-700 border-purple-300" },
  { code: "Y", label: "ยิปซัม", color: "bg-orange-50 text-orange-700 border-orange-300" },
  { code: "S", label: "กาวยาแนว", color: "bg-red-50 text-red-700 border-red-300" },
];

export default function ProductCategorySelector({ value, onChange }) {
  return (
    <div className="flex flex-col gap-2">
      <label className="font-semibold text-gray-700">
        ประเภทสินค้า
      </label>

      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => {
          const isActive = value === cat.code;

          return (
            <button
              key={cat.code}
              type="button"
              onClick={() => onChange(isActive ? "" : cat.code)}
              className={`
                px-4 py-2 rounded-full border text-sm font-medium
                transition-all
                ${
                  isActive
                    ? `${cat.color} shadow-sm scale-[1.02]`
                    : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
                }
              `}
            >
              {cat.label}
              <span className="ml-1 text-xs opacity-70">
                ({cat.code})
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
