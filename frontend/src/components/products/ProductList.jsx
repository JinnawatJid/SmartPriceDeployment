// components/products/ProductList.jsx
export default function ProductList({ 
  items, 
  onSelect, 
  loading, 
  loadingMore, 
  hasMore, 
  total,
  onLoadMore 
}) {
  const handleScroll = (e) => {
    if (!onLoadMore || !hasMore || loadingMore) return;

    const el = e.currentTarget;
    const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 100;

    if (nearBottom) {
      onLoadMore();
    }
  };

  return (
    <div 
      className="border rounded p-2 h-[600px] overflow-y-auto bg-white shadow"
      onScroll={handleScroll}
    >
      {/* Loading state */}
      {loading && items.length === 0 && (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <div className="text-sm text-gray-500">กำลังโหลด...</div>
          </div>
        </div>
      )}

      {/* No items */}
      {!loading && items.length === 0 && (
        <div className="text-center py-10 text-gray-500">
          ไม่พบสินค้า
        </div>
      )}

      {/* Items list */}
      {items.map((it) => (
        <div
          key={it.sku}
          className="p-2 cursor-pointer border-b hover:bg-gray-100"
          onClick={() => onSelect(it)}
        >
          <div className="font-semibold text-sm">{it.name}</div>
          <div className="text-sm text-gray-500">{it.sku}</div>
        </div>
      ))}

      {/* Loading more indicator */}
      {loadingMore && (
        <div className="flex justify-center py-4">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            กำลังโหลดเพิ่ม...
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
  );
}
