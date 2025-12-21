// src/components/quotes/QuoteDraftCard.jsx
import React from "react";


function formatNumber(value) {
  if (value == null) return "-";
  return value.toLocaleString("th-TH");
}

export default function QuoteDraftCard({
  quoteNo,
  customerName,
  customerCode,
  salesName,
  dueDateText,
  totalAmount,
  items = [],
  onEdit,
  onDelete,
}) {
  return (
    <div className="flex flex-col  rounded-2xl border border-gray-200 bg-white shadow-md transition-shadow">
      {/* Header */}
      <div className="border-b border-gray-200 px-5 py-3">
        <p className="text-2xl font-bold text-[#0084FF]">{quoteNo}</p>
        <p className="mt-1 font-semibold text-gray-800">
          {customerName}
        </p>
        <p className="text-xs text-gray-500">รหัสลูกค้า: {customerCode}</p>
      </div>

      {/* Body */}
      <div className="flex-1 px-5 py-3 space-y-2 text-xs md:text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">พนักงานขาย:</span>
          <span className="font-medium text-gray-800">{salesName}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">วันที่สร้าง:</span>
          <span className="font-medium text-gray-800">{dueDateText}</span>
        </div>
        <div className="flex justify-between border-t border-gray-100 pt-2 mt-1">
          <span className="text-gray-500">มูลค่าโดยประมาณ:</span>
          <span className="font-semibold text-emerald-600">
            ฿ {formatNumber(totalAmount)}
          </span>
        </div>

        {/* รายการสินค้า */}
        <div className="space-y-1 max-h-24 overflow-y-auto pr-1">
            {items.map((it, idx) => {
                const qty = Number(it.qty ?? 0);
                const unitPrice = Number(it.price ?? 0);               // ✅ ราคาต่อหน่วย
                const lineTotal =
                it.lineTotal != null
                    ? Number(it.lineTotal)
                    : unitPrice * qty;                                  // backup เผื่อไม่มี lineTotal

                return (
                <div
                    key={idx}
                    className="grid grid-cols-4 items-center text-xs font-semibold"
                >
                    <div className="flex-1 pr-2 text-gray-700 truncate">
                    {it.name}
                    </div>

                    <div className="flex col-span-2 justify-center text-right mx-1 text-gray-500">
                        <div>฿{formatNumber(unitPrice)} </div>    {/* ✅ ราคาต่อชิ้น */}
                        <div>x{formatNumber(qty)}</div>
                    </div>

                    <div className="flex justify-end text-emerald-600 font-semibold">
                    ฿{formatNumber(lineTotal)}                        {/* ✅ ยอดรวม */}
                    </div>
                </div>
                );
            })}
            </div>
      </div>

      {/* Footer buttons */}
      <div className="flex border-t border-gray-200">
        <button
          type="button"
          onClick={onEdit}
          className="flex-1 py-2 text-sm font-semibold text-white bg-[#0084FF] hover:bg-blue-700 rounded-bl-2xl"
        >
          แก้ไข
        </button>
        <button
          type="button"
          onClick={onDelete}
          className="flex-1 py-2 text-sm font-semibold text-white bg-[#FF0000] hover:bg-red-700 rounded-br-2xl"
        >
          ลบ
        </button>
      </div>
    </div>
  );
}
