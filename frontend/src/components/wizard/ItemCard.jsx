import React, { useState, useEffect } from "react";
import api from "../../services/api";
import { useSelectedStatus } from "../../hooks/useSelectedStatus";

const ItemCard = ({ item, onAdd }) => {
  const [qty, setQty] = useState(1);
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  // ตรวจสอบว่าสินค้าถูกเลือกแล้วหรือไม่
  const sku = item.sku || item.SKU;
  const variantCode = item.variantCode || item.VariantCode || null;
  const sqft = item.sqft_sheet || item.sqft || 0;
  const isSelected = useSelectedStatus(sku, variantCode, sqft);

  // 🔥 โหลด detail เฉพาะตอนเปิด dropdown
  useEffect(() => {
    if (!open || detail) return;

    const loadDetail = async () => {
      try {
        setLoading(true);
        const sku = item.sku || item.SKU;
        const res = await api.get(`/api/items/${sku}`);
        setDetail(res.data);
      } catch (err) {
        console.error("load item detail error:", err);
      } finally {
        setLoading(false);
      }
    };

    loadDetail();
  }, [open, detail, item]);

  const handleAddClick = (e) => {
    e.stopPropagation();
    if (qty <= 0) {
      alert("กรุณาใส่จำนวนที่มากกว่า 0");
      return;
    }

    // ✅ ส่ง full item ถ้ามี
    onAdd(detail || item, qty);
  };

  return (
    <div
      className="rounded-xl border border-gray-200 bg-white shadow-sm
                 hover:shadow-md transition cursor-pointer"
      onClick={() => setOpen((v) => !v)}
    >
      {/* ===== HEADER ===== */}
      <div className="flex gap-3 p-3 items-center">
        <div className="w-16 h-16 rounded-lg border bg-white overflow-hidden">
          <img
            src={item.image_url || "/assets/placeholder.png"}
            alt={item.name}
            className="w-full h-full object-contain"
          />
        </div>

        <div className="flex-grow min-w-0">
          <div className={`font-semibold text-sm truncate ${isSelected ? 'text-red-600 font-semibold' : 'text-gray-900'}`}>
            {isSelected && <span className="mr-1">✓</span>}
            {item.name}
          </div>
          <div className="text-xs text-gray-500 truncate">
            SKU: {item.sku}
          </div>
        </div>

        <button
          onClick={handleAddClick}
          className="text-xs px-3 py-1.5 rounded-lg bg-blue-600 text-white"
        >
          เลือก
        </button>
      </div>

      {/* ===== DROPDOWN ===== */}
      {open && (
        <div className="px-4 pb-4 text-sm text-gray-600 space-y-1 border-t bg-gray-50">
          {loading && (
            <div className="text-xs text-gray-400 mt-2">
              กำลังโหลดรายละเอียด...
            </div>
          )}

          {!loading && detail && (
            <div>
                <p className="mt-3 flex gap-1">
                  <span className="font-medium ">ชื่ออื่น:</span>{" "}
                  <div className="font-bold">{detail.alternate_names || "Name"}</div>
                </p>
              
              <div className="grid grid-cols-2 text-xs gap-y-1">
                <p>
                  <span className="font-medium">Brand:</span>{" "}
                  {detail.brandName || "-"}
                </p>
                <p>
                  <span className="font-medium">Group:</span>{" "}
                  {detail.groupName || "-"}
                </p>
                <p>
                  <span className="font-medium">Sub Group:</span>{" "}
                  {detail.subGroupName || "-"}
                </p>
                <p>
                  <span className="font-medium">SKU 2:</span>{" "}
                  {detail.sku2 || "-"}
                </p>
              </div>

              {/* Stock by branch */}
              {detail.stock && (
                <div className="mt-2 p-2 bg-white rounded border ">
                  <p className="font-semibold text-green-700 text-xs mb-1">
                    สต๊อก 
                  </p>
                  {detail.stock.branches && detail.stock.branches.length > 0 ? (
                    <div className="space-y-1">
                      {detail.stock.branches.map((branch) => (
                        <div key={branch.branch_code} className="flex justify-between text-xs">
                          <span className="text-gray-600">{branch.branch_code}:</span>
                          <span className="font-bold text-lg">{branch.quantity} {detail.unit || ""}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500">ไม่มีข้อมูลสต๊อก</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* QTY */}
          <div className="flex items-center gap-2 pt-1">
            <span className="text-xs">จำนวน</span>
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
