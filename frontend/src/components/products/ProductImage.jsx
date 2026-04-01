// components/products/ProductImage.jsx
import { useState, useEffect } from "react";

export default function ProductImage({ item }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!item?.sku) {
      setImageUrl(null);
      setLoading(false);
      return;
    }

    // Reset state เมื่อเปลี่ยนสินค้า
    setLoading(true);
    setImageUrl(null);

    // ลองดึงรูปจาก API ก่อน
    const img = new Image();
    img.onload = () => {
      setImageUrl(`/api/product-images/${item.sku}?t=${Date.now()}`);
      setLoading(false);
    };
    img.onerror = () => {
      // ถ้าไม่มีรูปจาก API ให้ใช้ imageUrl เดิม
      setImageUrl(item?.imageUrl || null);
      setLoading(false);
    };
    img.src = `/api/product-images/${item.sku}?t=${Date.now()}`;
  }, [item?.sku]); // ⭐ ลบ tried ออกจาก dependency

  return (
    <div className="border rounded w-full h-[300px] flex items-center justify-center bg-gray-100 shadow">
      {loading ? (
        <span className="text-gray-400">Loading...</span>
      ) : imageUrl ? (
        <img 
          src={imageUrl} 
          alt={item?.name || 'Product'} 
          className="max-h-full max-w-full object-contain"
        />
      ) : (
        <span className="text-gray-400">No Image</span>
      )}
    </div>
  );
}
