import { useEffect, useState } from "react";
import api from "../services/api";

export function useItemPriceHistory({ sku, customerCode, enabled }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!enabled || !sku || !customerCode) return;

    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        const res = await api.get("/api/invoice/item-price-history", {
          params: {
            sku,
            customerCode,
            limit: 10,
          },
        });

        if (!cancelled) {
          setData(res.data || []);
        }
      } catch (err) {
        console.error("load price history error", err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [sku, customerCode, enabled]);

  // 🔑 เลือก 2 ราคาล่าสุดที่ "ไม่ซ้ำ"
  const uniqueLast2 = [];
  const seen = new Set();

  for (const r of data) {
    if (!seen.has(r.price)) {
      uniqueLast2.push(r);
      seen.add(r.price);
    }
    if (uniqueLast2.length === 2) break;
  }

  return {
    prices: uniqueLast2,
    loading,
  };
}
