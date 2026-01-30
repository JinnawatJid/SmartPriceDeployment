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
  cart = [], // ⭐ เพิ่ม cart สำหรับส่งไปยัง modal
  customer = {}, // ⭐ เพิ่ม customer
  specialPriceStatus = null,
  specialPriceRequestNumber = null, // ⭐ เพิ่ม request number
  onEdit,
  onDelete,
  onRequestSpecialPrice, // ⭐ เพิ่ม callback สำหรับขอราคาพิเศษ
}) {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col  rounded-2xl border border-gray-200 bg-white shadow-md transition-shadow">
      {/* Header */}
      <div className="border-b border-gray-200 px-5 py-3">
        <div className="flex items-start justify-between gap-2">
          {/* เลขที่ใบเสนอราคา */}
          <div className="flex-1">
            <p className="text-xl font-extrabold text-[#0084FF]">{quoteNo}</p>
          </div>

          {/* ปุ่มส่ง LINE */}
          <button
            type="button"
            className="flex items-center gap-2 rounded-lg bg-[#06b64c] font-medium  text-white px-3 py-1 text-xs shadow-md  hover:text-white hover:bg-[#05a445] "
            title="ส่งใบเสนอราคาทาง LINE"
          >
            <img src="/assets/Line_logo.png" alt="LINE" className="h-6 w-6  rounded-md shadow-md" />
            <span>ส่งใบเสนอราคา</span>
          </button>
        </div>
        
        {/* ⭐ แสดงสถานะการขอราคาพิเศษ - ย้ายมาด้านล่างปุ่ม LINE */}
        {specialPriceStatus && (
          <div className="mt-2 space-y-2">
            {specialPriceStatus === "pending" && (
              <div className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">
                <span>⏳</span>
                <span>รอการอนุมัติราคาพิเศษ</span>
              </div>
            )}
            {specialPriceStatus === "approved" && (
              <>
                <div className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                  <span>✅</span>
                  <span>ราคาพิเศษอนุมัติแล้ว</span>
                </div>
                {/* ปุ่มดาวน์โหลด PDF ที่ผู้อนุมัติแนบมา */}
                {specialPriceRequestNumber && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/approval-pdfs/${specialPriceRequestNumber}`);
                    }}
                    className="ml-2 inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded hover:bg-blue-200"
                    title="ดาวน์โหลดเอกสารที่ผู้อนุมัติแนบมา"
                  >
                    <span>📎</span>
                    <span>ดูเอกสารอนุมัติ</span>
                  </button>
                )}
              </>
            )}
            {specialPriceStatus === "rejected" && (
              <div className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
                <span>❌</span>
                <span>ราคาพิเศษถูกปฏิเสธ</span>
              </div>
            )}
          </div>
        )}

        <p className="mt-1 font-semibold text-gray-800">{customerName}</p>
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
        {/* ⭐ ปุ่มขอราคาพิเศษ - แสดงเฉพาะเมื่อยังไม่มีการขอราคา หรือถูกปฏิเสธ */}
        {(!specialPriceStatus || specialPriceStatus === 'rejected') && onRequestSpecialPrice && (
          <button
            type="button"
            onClick={onRequestSpecialPrice}
            className="flex-1 py-2 text-sm font-semibold text-white bg-yellow-500 hover:bg-yellow-600 rounded-bl-2xl"
          >
            ขอราคาพิเศษ
          </button>
        )}
        
        <button
          type="button"
          onClick={onEdit}
          className={`flex-1 py-2 text-sm font-semibold text-white bg-[#0084FF] hover:bg-blue-700 ${(!specialPriceStatus || specialPriceStatus === 'rejected') && onRequestSpecialPrice ? '' : 'rounded-bl-2xl'}`}
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
