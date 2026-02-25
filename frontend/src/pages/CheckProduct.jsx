import React, { useEffect, useState, useCallback } from "react";
import api from "../services/api";
import Loader from "../components/Loader";

export default function CheckProduct() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

  // Filter state
  const [filter, setFilter] = useState({
    productType: "",
    brand: "",
    category: "",
    subCategory: "",
    color: "",
    thickness: "",
    size: "",
  });

  // ⭐ โหลดข้อมูลแบบ pagination
  const loadItems = useCallback(async (reset = false) => {
    if (!hasMore && !reset) return;

    if (reset) {
      setLoading(true);
    } else {
      if (loadingMore) return;
      setLoadingMore(true);
    }

    const currentOffset = reset ? 0 : offset;

    try {
      const params = {
        limit: 50,
        offset: currentOffset,
      };

      // ⭐ เพิ่ม search parameter
      if (query.trim()) {
        params.search = query.trim();
      }

      // ⭐ เพิ่ม filter parameters
      Object.keys(filter).forEach((key) => {
        if (filter[key] && filter[key].trim()) {
          params[key] = filter[key].trim();
        }
      });

      const res = await api.get("/api/items/list", { params });

      const newItems = res.data.items || [];
      const totalCount = res.data.total || 0;

      setItems((prev) => (reset ? newItems : [...prev, ...newItems]));
      setTotal(totalCount);

      const newOffset = currentOffset + newItems.length;
      setOffset(newOffset);
      setHasMore(newOffset < totalCount);
    } catch (err) {
      console.error("Error loading items:", err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [hasMore, loadingMore, offset, query, filter]);

  // ⭐ โหลดครั้งแรก
  useEffect(() => {
    setItems([]);
    setOffset(0);
    setHasMore(true);
    loadItems(true);
  }, []);

  // ⭐ เมื่อ filter หรือ search เปลี่ยน ให้โหลดใหม่ (debounce 500ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setItems([]);
      setOffset(0);
      setHasMore(true);
      loadItems(true);
    }, 500);

    return () => clearTimeout(timer);
  }, [query, filter]);

  const onFilterChange = (key, value) => {
    setFilter((prev) => ({ ...prev, [key]: value }));
  };

  // ⭐ Infinite scroll handler
  const handleScroll = useCallback(
    (e) => {
      const el = e.currentTarget;
      const nearBottom =
        el.scrollTop + el.clientHeight >= el.scrollHeight - 100;

      if (nearBottom && hasMore && !loadingMore && !loading) {
        loadItems(false);
      }
    },
    [hasMore, loadingMore, loading]
  );

  return (
    <div className="p-8 bg-gray-100 min-h-screen">
      <h1 className="text-3xl font-bold mb-6">ตรวจสอบรายละเอียดสินค้า</h1>

      {/* Search */}
      <div className="flex gap-4 mb-6">
        <input
          type="text"
          className="flex-1 px-4 py-3 rounded-lg border shadow-sm"
          placeholder="ค้นหาสินค้า... (ชื่อ, รหัส)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {total > 0 && (
          <div className="flex items-center px-4 py-3 bg-white rounded-lg border shadow-sm text-gray-700">
            <span className="font-semibold">{items.length}</span>
            <span className="mx-1">/</span>
            <span>{total}</span>
            <span className="ml-1">รายการ</span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-6 mb-8">
        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold">
          เลือกไซส์กระจกกึ่งมาตรฐาน
        </button>
        <button className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 rounded-xl font-semibold">
          น้ำหนักสินค้าอลูมิเนียม
        </button>
      </div>

      {/* Filter + Table */}
      <div className="grid grid-cols-5 gap-6">
        {/* Left Filter Panel */}
        <div className="col-span-1 bg-white rounded-xl shadow p-6">
          <h3 className="text-xl font-semibold mb-4">Filter</h3>

          {[
            ["productType", "เลือกสินค้าทั้งหมด"],
            ["brand", "ยี่ห้อ"],
            ["category", "กลุ่มสินค้า"],
            ["subCategory", "กลุ่มย่อย"],
            ["color", "สี"],
            ["thickness", "ความหนา"],
            ["size", "ขนาด"],
          ].map(([key, label]) => (
            <div key={key} className="mb-4">
              <label className="text-sm text-gray-700">{label}</label>
              <input
                className="w-full px-3 py-2 border rounded-lg mt-1"
                value={filter[key]}
                onChange={(e) => onFilterChange(key, e.target.value)}
                placeholder="ทั้งหมด"
              />
            </div>
          ))}
        </div>

        {/* Product Table */}
        <div className="col-span-4">
          <div className="bg-white rounded-xl shadow flex flex-col h-[calc(100vh-300px)]">
            {/* Header */}
            <div className="bg-red-600 text-white rounded-t-xl">
              <div className="grid grid-cols-5 px-4 py-3 font-semibold">
                <div>รหัสสินค้า</div>
                <div>ชื่อสินค้า</div>
                <div>จำนวน</div>
                <div>หน่วย</div>
                <div>ประเภทสินค้า</div>
              </div>
            </div>

            {/* Body with scroll */}
            <div
              className="flex-1 overflow-y-auto"
              onScroll={handleScroll}
            >
              {/* Loading state */}
              {loading && items.length === 0 && (
                <div className="flex items-center justify-center py-20">
                  <Loader />
                </div>
              )}

              {/* No items */}
              {!loading && items.length === 0 && (
                <div className="text-center py-10 text-gray-500">
                  ไม่พบข้อมูลสินค้า
                </div>
              )}

              {/* Items list */}
              {items.map((item, i) => (
                <div
                  key={`${item.sku}-${i}`}
                  className="grid grid-cols-5 px-4 py-3 border-b hover:bg-gray-50"
                >
                  <div className="text-sm">{item.sku}</div>
                  <div className="text-sm">{item.name}</div>
                  <div className="text-sm">{item.unit || 0}</div>
                  <div className="text-sm">{item.unit2 || "-"}</div>
                  <div className="text-sm">{item.category}</div>
                </div>
              ))}

              {/* Loading more indicator */}
              {loadingMore && (
                <div className="flex justify-center py-4">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    กำลังโหลด...
                  </div>
                </div>
              )}

              {/* End of list */}
              {!hasMore && items.length > 0 && (
                <div className="text-xs text-gray-400 text-center py-4">
                  โหลดครบแล้ว ({total} รายการ)
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
