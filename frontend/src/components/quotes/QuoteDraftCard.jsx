// src/components/quotes/QuoteDraftCard.jsx
import React from "react";
import { useNavigate } from "react-router-dom";

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
  specialPriceRequest,
  onEdit,
  onDelete,
}) {
  const navigate = useNavigate();
  
  // ตรวจสอบสถานะ special price request
  const sprStatus = specialPriceRequest?.status;
  const isApproved = sprStatus === 'APPROVED';
  const isPending = sprStatus && ['SUBMITTED', 'PENDING_ZM', 'PENDING_RM'].includes(sprStatus);
  const isRejected = sprStatus === 'REJECTED';
  
  const getStatusBadge = () => {
    if (isApproved) {
      return (
        <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-semibold">
          <span>✓</span>
          <span>ราคาพิเศษอนุมัติแล้ว</span>
        </div>
      );
    }
    if (isPending) {
      return (
        <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 text-xs font-semibold">
          <span>⏳</span>
          <span>รอการอนุมัติ</span>
        </div>
      );
    }
    if (isRejected) {
      return (
        <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-semibold">
          <span>✗</span>
          <span>ราคาพิเศษถูกปฏิเสธ</span>
        </div>
      );
    }
    return null;
  };
  
  return (
    <div className="flex flex-col   rounded-2xl border border-gray-200 bg-white shadow-md transition-shadow">
      {/* Header */}
      <div className="border-b border-gray-200 px-5 py-3">
        <div className="flex items-start justify-between gap-2">
          {/* เลขที่ใบเสนอราคา */}
          <div className="flex-1">
            <p className="text-xl font-extrabold text-[#0084FF]">{quoteNo}</p>
            {/* แสดงสถานะ special price request */}
            <div className="mt-1">
              {getStatusBadge()}
            </div>
          </div>
        </div>

        <p className="mt-2 font-semibold text-gray-800">{customerName}</p>
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
          <span className="font-semibold text-emerald-600">฿ {formatNumber(totalAmount)}</span>
        </div>

        {/* รายการสินค้า */}
        <div className="space-y-1 max-h-24 overflow-y-auto pr-1">
          {items.map((it, idx) => {
            const qty = Number(it.qty ?? 0);
            const unitPrice = Number(it.price ?? 0); // ✅ ราคาต่อหน่วย
            const lineTotal = it.lineTotal != null ? Number(it.lineTotal) : unitPrice * qty; // backup เผื่อไม่มี lineTotal

            return (
              <div key={idx} className="grid grid-cols-4 items-center text-xs font-semibold">
                <div className="flex-1 pr-2 text-gray-700 truncate">{it.name}</div>

                <div className="flex col-span-2 justify-center text-right mx-1 text-gray-500">
                  <div>฿{formatNumber(unitPrice)} </div> {/* ✅ ราคาต่อชิ้น */}
                  <div>x{formatNumber(qty)}</div>
                </div>

                <div className="flex justify-end text-emerald-600 font-semibold">
                  ฿{formatNumber(lineTotal)} {/* ✅ ยอดรวม */}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer buttons */}
      <div className="flex border-t border-gray-200">
        {isApproved ? (
          <>
            <button
              type="button"
              onClick={onEdit}
              className="flex-1 py-2 text-sm font-semibold text-white bg-green-600 hover:bg-green-700 rounded-bl-2xl"
            >
              ใช้ราคาที่อนุมัติ
            </button>
            <button
              type="button"
              onClick={onDelete}
              className="flex-1 py-2 text-sm font-semibold text-white bg-[#FF0000] hover:bg-red-700 rounded-br-2xl"
            >
              ลบ
            </button>
          </>
        ) : (
          <>
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
          </>
        )}
      </div>
    </div>
  );
}
