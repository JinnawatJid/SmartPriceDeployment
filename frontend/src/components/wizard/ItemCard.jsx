// src/components/wizard/ItemCard.jsx
import React, { useState } from "react";

const ItemCard = ({ item, onAdd }) => {
  const [qty, setQty] = useState(1);
  const [open, setOpen] = useState(false); // ⭐ dropdown state

  const handleAddClick = (e) => {
    e.stopPropagation(); // กัน trigger dropdown
    if (qty <= 0) {
      alert("กรุณาใส่จำนวนที่มากกว่า 0");
      return;
    }
    onAdd(item, qty);
  };

  return (
    <div
      className="rounded-xl border border-gray-200 bg-white shadow-sm
                 hover:shadow-md transition cursor-pointer"
      onClick={() => setOpen((v) => !v)}
    >
      {/* ================= HEADER (COMPACT) ================= */}
      <div className="flex gap-3 p-3 items-center">
        {/* รูป */}
        <div className="w-16 h-16 flex-shrink-0 rounded-lg border bg-white overflow-hidden">
          <img
            src={item.image_url || "/assets/placeholder.png"}
            alt={item.name}
            className="w-full h-full object-contain"
          />
        </div>

        {/* ชื่อ + SKU */}
        <div className="flex-grow min-w-0">
          <div className="font-semibold text-sm text-gray-800 truncate">
            {item.name}
          </div>
          <div className="text-xs text-gray-500 truncate">
            SKU: {item.sku}
          </div>
        </div>

        {/* ปุ่มเลือก */}
        <button
          onClick={handleAddClick}
          className="text-xs px-3 py-1.5 rounded-lg
                     bg-blue-600 text-white hover:bg-blue-700
                     whitespace-nowrap"
        >
          เลือก
        </button>
      </div>

      {/* ================= DROPDOWN DETAIL ================= */}
      {open && (
        <div className="px-4 pb-4 text-sm text-gray-600 space-y-1 border-t bg-gray-50 rounded-b-xl shadow-md">
          {item.alternate_names && (
            <p className="mt-2">
              <span className="font-medium">ชื่ออื่น:</span>{" "}
              {item.alternate_names}
            </p>
          )}

          {(item.groupName || item.subGroupName) && (
            <p className="grid grid-cols-2 text-xs text-gray-500 gird ">
              <p>
                <span className="font-medium">Brand:</span>{" "}
                {item.brandName}
              </p>
              <p>
                <span className="font-medium">Group:</span>{" "}
                {item.groupName}
              </p>
              <p>
                <span className="font-medium">Sub Group:</span>{" "}
                {item.subGroupName}
              </p>
              <p>
                {item.sku2 && (
                  <p className="text-xs text-gray-500 fo">SKU2: {item.sku2}</p>
                )}
              </p>
              
              
            </p>
          )}

          {item.inventory !== undefined && (
            <p className="text-green-600 font-semibold">
              สต๊อก: {item.inventory} {item.unit || ""}
            </p>
          )}

          {/* QTY */}
          <div className="flex items-center gap-2 pt-1">
            <span className="text-xs text-gray-500">จำนวน</span>
            <input
              type="number"
              min={1}
              value={qty}
              onChange={(e) => setQty(Number(e.target.value))}
              onClick={(e) => e.stopPropagation()}
              className="w-14 border rounded px-2 py-1 text-sm"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ItemCard;
