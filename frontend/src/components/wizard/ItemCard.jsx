// src/components/wizard/ItemCard.jsx
import React, { useState } from 'react';

const ItemCard = ({ item, onAdd }) => {
  // ใช้ Local state สำหรับจำนวน
  const [qty, setQty] = useState(1);

  const handleAddClick = () => {
    if (qty <= 0) {
      alert('กรุณาใส่จำนวนที่มากกว่า 0');
      return;
    }
    onAdd(item, qty);
  };

  return (
    <div className="flex flex-row rounded-xl border border-gray-200 bg-white shadow-md transition-all duration-300 hover:shadow-lg w-full p-4 gap-4">
      {/* ส่วนเนื้อหา */}
      <div className="flex-shrink-0 w-28 h-28 rounded-lg overflow-hidden bg-white border">
        <img
          src={item.image_url || "/assets/placeholder.png"}
          alt={item.name}
          className="w-full h-full object-contain"
        />
      </div>

      <div className="flex-grow space-y-1 py-2 min-w-0">
        <h4 className="text-lg font-semibold text-gray-800 max-h-[3rem] overflow-hidden">{item.name}</h4>
        <p className="mt-1 text-sm text-gray-500">รหัส: {item.sku}</p>
        <p className="text-sm text-gray-500">{item.description}</p>
        {item.inventory !== undefined && (
          <p className="mt-1 text-sm font-semibold text-green-600">
            มีในสต๊อก: {item.inventory} {item.unit || ""}
          </p>
        )}
      </div>

      {/* ส่วนปุ่ม Add */}
      <div className="flex flex-shrink-0 gap-4 items-center p-4">
        <input
          type="number"
          value={qty}
          onChange={(e) => setQty(Math.max(1, Number(e.target.value)))}
          className="w-20 rounded-lg border border-gray-300 p-2 text-center text-lg font-bold shadow-sm"
          min="1"
        />
        <button
          onClick={handleAddClick}
          className=" whitespace-nowrap rounded-lg bg-blue-600 px-4 py-2 text-sm  text-white shadow-sm hover:bg-blue-700"
        >
          เลือกสินค้า
        </button>
      </div>
    </div>
  );
};

export default ItemCard;