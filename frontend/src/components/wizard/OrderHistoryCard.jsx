// src/components/wizard/OrderHistoryCard.jsx
import React, { useState } from "react";

function formatThaiDate(dt) {
  if (!dt) return "";
  const d = new Date(dt);
  return d.toLocaleString("th-TH", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function OrderHistoryCard({ order, onRepeat }) {
  const [open, setOpen] = useState(false);

  if (!order) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-500">
        ยังไม่มีประวัติการซื้อ
      </div>
    );
  }

  const total = order.totals?.grandTotal ?? order.totals?.total ?? order.totals?.netTotal ?? 0;

  const cart = order.cart || [];

  return (
    <div className="rounded-xl border border-blue-300 bg-gray-100 overflow-hidden">
      {/* แถวบน */}
      <div
        className="flex w-full items-center justify-between px-3 py-2 cursor-pointer"
        onClick={() => setOpen((v) => !v)}
      >
        {/* ซ้าย: icon + วันที่ + เลขที่ */}
        <div className="flex items-center gap-2">
          <span className={"text-lg transition-transform " + (open ? "rotate-90" : "")}>❯</span>
          <div className="flex flex-col text-left">
            <span className="text-xs text-gray-500">
              {formatThaiDate(order.confirmedAt || order.createdAt)}
            </span>
            <span className="font-semibold text-xs text-gray-900">
              #{order.quoteNo || order.id}
            </span>
            <span className="text-sm font-semibold text-emerald-600">
              ฿{" "}
              {Number(total).toLocaleString("th-TH", {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>
        </div>

        {/* ขวา: ปุ่มซื้อซ้ำ */}
        <button
          type="button"
          className="px-3 py-1 rounded-full text-blue-700 text-xs hover:underline hover:underline-offset-2 active:scale-95"
          onClick={(e) => {
            e.stopPropagation(); // กันไม่ให้คลิกแล้วไปพับ/กางแถวล่าง
            onRepeat && onRepeat(order);
          }}
        >
          ซื้อซ้ำ
        </button>
      </div>

      {/* แถวล่าง: รายการสินค้า */}
      {open && (
        <div className="bg-gray-200 px-4 py-2 text-sm">
          <div className="font-semibold mb-1">รายการสินค้า</div>
          {cart.length === 0 ? (
            <div className="text-xs text-gray-500">ไม่พบรายการสินค้าในบิลนี้</div>
          ) : (
            cart.map((item, idx) => (
              <div key={item.sku || item.id || idx} className="flex items-center justify-between">
                <span className="truncate">• {item.name || item.description || item.itemName}</span>
                <span className="ml-2 whitespace-nowrap">
                  x{item.qty || item.quantity || item.Qty}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
