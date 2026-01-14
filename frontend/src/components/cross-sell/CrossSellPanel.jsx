import { useQuote } from "../../hooks/useQuote";
import { useCrossSell } from "./useCrossSell";
import CrossSellItem from "./CrossSellItem";

export default function CrossSellPanel({ onAddRequest }) {
  const { state } = useQuote();

  const products = state.cart.map(it => ({
    productGroup: it.product_group ?? null,
    productSubGroup: it.product_sub_group ?? null,
  }));


  const { items, loading } = useCrossSell(products);

  if (loading) {
    return <div className="text-sm text-gray-400">กำลังโหลดสินค้าแนะนำ…</div>;
  }

  if (!items.length) return null;

  return (
    <div className="border rounded p-3 bg-gray-50 mt-4">
      <div className="font-semibold text-sm mb-2">
        สินค้าแนะนำ
      </div>

      <div
        className="space-y-2 overflow-y-auto"
        style={{
          maxHeight: "180px", // ~ 3 items (ปรับได้)
        }}
      >
        {items.map((it, idx) => (
          <CrossSellItem
            key={`${it.displayName}-${idx}`}
            item={it}
            onAdd={onAddRequest}
          />
        ))}
      </div>
    </div>
  );
}
