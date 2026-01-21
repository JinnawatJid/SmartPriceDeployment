// components/products/ProductDetail.jsx
export default function ProductDetail({ item }) {
  if (!item) return <div className="text-gray-500 p-4">เลือกรายการสินค้าเพื่อดูรายละเอียด</div>;

  return (
    <div className="space-y-4 bg-white p-6 rounded shadow">
      {/* ข้อมูลสินค้า */}
      <div>
        <h2 className="text-2xl font-bold">{item.name}</h2>
        {item.alternateName && (
          <div className="text-sm font-semibold text-gray-500">ชื่ออื่น: {item.alternateName}</div>
        )}

        <p className="text-gray-600">SKU: {item.sku}</p>
        {item.brandName && <p>Brand: {item.brandName}</p>}
        {item.groupName && <p>Group: {item.groupName}</p>}
        {item.subGroupName && <p>SubGroup: {item.subGroupName}</p>}
        {item.colorName && <p>Color: {item.colorName}</p>}
        {item.inventory !== undefined && <p>คงเหลือในสต๊อก: {item.inventory}</p>}
      </div>
    </div>
  );
}
