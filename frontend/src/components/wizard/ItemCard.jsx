// src/components/wizard/ItemCard.jsx
import React, { useState } from "react";

const ItemCard = ({ item, onAdd }) => {
  const [qty, setQty] = useState(1);

  const handleAddClick = () => {
    if (qty <= 0) {
      alert("กรุณาใส่จำนวนที่มากกว่า 0");
      return;
    }
    onAdd(item, qty);
  };

  return (
    <div className="flex flex-col rounded-xl border border-gray-200 bg-white shadow-md transition-all duration-300 hover:shadow-lg w-full p-4 gap-4">
      
      {/* ===== แถวบน : รูป + รายละเอียด ===== */}
      <div className="flex flex-row gap-4">
        {/* รูปสินค้า */}
        <div className="flex-shrink-0 w-28 h-28 rounded-lg overflow-hidden bg-white border">
          <img
            src={item.image_url || "/assets/placeholder.png"}
            alt={item.name}
            className="w-full h-full object-contain"
          />
        </div>

        {/* รายละเอียด */}
        <div className="flex-grow space-y-1 py-1 min-w-0">
          <h4 className="text-lg font-semibold text-gray-800 max-h-[3rem] overflow-hidden">
            {item.name}
          </h4>

          {item.alternate_names && (
            <p className="text-sm text-gray-500">
              ชื่ออื่น: {item.alternate_names}
            </p>
          )}

          <p className="text-sm text-gray-500">รหัส: {item.sku}</p>

          {(item.product_group || item.product_sub_group) && (
            <p className="text-xs text-gray-400">
              {item.product_group}
              {item.product_sub_group ? ` / ${item.product_sub_group}` : ""}
            </p>
          )}

          {item.sku2 && (
            <p className="text-xs text-gray-400">
              SKU รอง: {item.sku2}
            </p>
          )}

          {item.inventory !== undefined && (
            <p className="text-sm font-semibold text-green-600">
              มีในสต๊อก: {item.inventory} {item.unit || ""}
            </p>
          )}
        </div>
      </div>

      {/* ===== แถวล่าง : จำนวน + ปุ่ม ===== */}
      <div className="flex items-center justify-end gap-4 pt-2 border-t">
        <input
          type="number"
          value={qty}
          onChange={(e) => setQty(Math.max(1, Number(e.target.value)))}
          className="w-full rounded-lg border border-gray-300 p-2 text-center text-lg font-bold shadow-sm"
          min="1"
        />
        <button
          onClick={handleAddClick}
          className="whitespace-nowrap rounded-lg bg-blue-600 px-5 py-2 text-sm text-white shadow-sm hover:bg-blue-700"
        >
          เลือกสินค้า
        </button>
      </div>
    </div>
  );
};

export default ItemCard;
