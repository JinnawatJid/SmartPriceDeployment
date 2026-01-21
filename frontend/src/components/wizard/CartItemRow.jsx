// src/components/wizard/CartItemRow.jsx
import { useState } from "react";
import { useItemPriceHistory } from "../../hooks/useItemPriceHistory";

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

const TrashIcon = () => (
  <img src="/assets/delete.png" alt="delete" className="h-5 w-5 mr-4 mt-1 object-contain" />
);

export default function CartItemRow({ item, index, calculatedItem, dispatch, customerCode }) {
  const [editingDesc, setEditingDesc] = useState(false);
  const [descDraft, setDescDraft] = useState(item.name || "");
  const [openPriceHistory, setOpenPriceHistory] = useState(false);

  const { prices, loading } = useItemPriceHistory({
    sku: item.sku,
    customerCode,
    enabled: openPriceHistory,
  });

  const displayUnitPrice =
    calculatedItem?.price_per_sheet ??
    calculatedItem?.UnitPrice ??
    item.price_per_sheet ??
    item.UnitPrice ??
    item.price ??
    0;

  const displayLineTotal =
    calculatedItem?._LineTotal ?? item.lineTotal ?? displayUnitPrice * item.qty ?? 0;

  const handleQtyChange = (e) => {
    dispatch({
      type: "UPDATE_CART_QTY",
      payload: {
        sku: item.sku,
        qty: Math.max(1, Number(e.target.value)),
        variantCode: item.variantCode ?? null,
        sqft_sheet: item.sqft_sheet ?? item.sqft ?? 0,
        from: "cart",
      },
    });
  };

  const handleRemove = () => {
    const key = `${item.sku}__${item.variantCode ?? ""}__${Number(
      item.sqft_sheet ?? item.sqft ?? 0
    )}`;
    dispatch({ type: "REMOVE_ITEM", payload: key });
  };

  const commitDescription = () => {
    dispatch({
      type: "UPDATE_ITEM_DESCRIPTION",
      payload: {
        sku: item.sku,
        variantCode: item.variantCode ?? null,
        sqft_sheet: Number(item.sqft_sheet ?? item.sqft ?? 0),
        name: descDraft.trim(),
      },
    });
    setEditingDesc(false);
  };

  return (
    <>
      {/* ===== MAIN ROW ===== */}
      <tr className="border-b bg-white hover:bg-gray-50">
        <td className="px-4 py-3 text-sm text-gray-600">{index + 1}</td>

        <td className="px-4 py-3">
          {editingDesc ? (
            <input
              autoFocus
              value={descDraft}
              onChange={(e) => setDescDraft(e.target.value)}
              onBlur={commitDescription}
              onKeyDown={(e) => {
                if (e.key === "Enter") commitDescription();
                if (e.key === "Escape") {
                  setDescDraft(item.name || "");
                  setEditingDesc(false);
                }
              }}
              className="w-full rounded border px-2 py-1 text-xs"
            />
          ) : (
            <p
              className="font-semibold text-xs cursor-pointer hover:underline"
              onDoubleClick={() => setEditingDesc(true)}
              title="ดับเบิลคลิกเพื่อแก้ไขชื่อสินค้า"
            >
              {item.name}
            </p>
          )}
          <p className="text-xs text-gray-500">{item.sku}</p>
        </td>

        <td className="px-2 py-3">
          <input
            type="number"
            value={item.qty}
            min="1"
            onChange={handleQtyChange}
            className="w-14 rounded border p-1 text-center"
          />
        </td>

        <td className="px-2 py-3 text-sm">
          <button
            onClick={() => setOpenPriceHistory((v) => !v)}
            className="font-semibold text-blue-700 hover:underline flex items-center gap-1"
          >
            {Number(displayUnitPrice).toLocaleString("th-TH")}
            <span className={`transition-transform ${openPriceHistory ? "rotate-90" : ""}`}>❯</span>
          </button>
        </td>

        <td className="px-2 text-sm py-3 font-semibold">
          {Number(displayLineTotal).toLocaleString("th-TH")}
        </td>

        <td className="text-start mr-4">
          <button onClick={handleRemove}>
            <TrashIcon />
          </button>
        </td>
      </tr>

      {/* ===== EXPAND ROW ===== */}
      {openPriceHistory && (
        <tr className="bg-gray-100">
          <td colSpan={6} className="px-6 py-3">
            {loading && <div className="text-sm text-gray-500">กำลังโหลดประวัติราคา...</div>}

            {!loading && prices.length === 0 && (
              <div className="text-sm text-gray-500">ไม่พบประวัติราคา</div>
            )}

            {!loading && prices.length > 0 && (
              <div className="rounded-lg border bg-white">
                <div className="px-4 py-2 font-semibold text-sm bg-gray-50">ประวัติราคา</div>

                <div className="divide-y">
                  {prices.slice(0, 2).map((p, i) => (
                    <div key={i} className="flex justify-between px-4 py-2 text-sm">
                      <div>
                        <div className="text-gray-600">{formatThaiDate(p.date)}</div>
                        <div className="text-xs text-gray-500">#{p.invoiceNo}</div>
                      </div>

                      <div className="text-right">
                        <div className="font-semibold text-emerald-600">
                          ฿{" "}
                          {Number(p.price).toLocaleString("th-TH", {
                            minimumFractionDigits: 2,
                          })}
                        </div>

                        <div className="text-xs text-gray-500">
                          จำนวน {Number(p.qty || 0).toLocaleString("th-TH")} {p.unit || ""}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
