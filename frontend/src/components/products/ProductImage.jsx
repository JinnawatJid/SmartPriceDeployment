// components/products/ProductImage.jsx
import { useState, useEffect } from "react";

export default function ProductImage({ item }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [tried, setTried] = useState(false);

  useEffect(() => {
    if (!item?.sku || tried) return;

    // ลองดึงรูปจาก API ก่อน
    const img = new Image();
    img.onload = () => {
      setImageUrl(`/api/product-images/${item.sku}`);
      setTried(true);
    };
    img.onerror = () => {
      // ถ้าไม่มีรูปจาก API ให้ใช้ imageUrl เดิม
      setImageUrl(item?.imageUrl || null);
      setTried(true);
    };
    img.src = `/api/product-images/${item.sku}`;
  }, [item?.sku, tried]);

  return (
    <div className="border rounded w-full h-[300px] flex items-center justify-center bg-gray-100 shadow">
      {imageUrl ? (
        <img 
          src={imageUrl} 
          alt={item?.name || 'Product'} 
          className="max-h-full object-contain"
        />
      ) : (
        <span className="text-gray-400">No Image</span>
      )}
    </div>
  );
}
