import { useEffect, useState } from "react";
import api from "../../services/api";

export function useCrossSell(products) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!products.length) {
      setItems([]);
      return;
    }

    setLoading(true);

    api
      .post("/api/cross-sell", { products })
      .then(res => setItems(res.data || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [JSON.stringify(products)]);

  return { items, loading };
}
