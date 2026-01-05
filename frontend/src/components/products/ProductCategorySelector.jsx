import React from "react";

export default function ProductCategorySelector({ value, onChange }) {
  return (
    <div className="flex items-center gap-3">
      <label className="font-semibold text-gray-700">
        ประเภทสินค้า:
      </label>

      <select
        className="border p-2 rounded-lg"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">-- เลือกประเภทสินค้า --</option>
        <option value="A">อลูมิเนียม (A)</option>
        <option value="E">อุปกรณ์เสริม (E)</option>
        <option value="G">กระจก (G)</option>
        <option value="C">C-Line / โครงคร่าว (C)</option>
        <option value="Y">ยิปซัม (Y)</option>
        <option value="S">กาวยาแนว (S)</option>
      </select>
    </div>
  );
}
