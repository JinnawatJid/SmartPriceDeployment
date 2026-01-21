// components/products/ProductImage.jsx
export default function ProductImage({ item }) {
  return (
    <div className="border rounded w-full h-[300px] flex items-center justify-center bg-gray-100 shadow">
      {item?.imageUrl ? (
        <img src={item.imageUrl} alt={item.name} className="max-h-full object-contain" />
      ) : (
        <span className="text-gray-400">No Image</span>
      )}
    </div>
  );
}
