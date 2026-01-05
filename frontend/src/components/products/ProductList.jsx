// components/products/ProductList.jsx
export default function ProductList({ items, onSelect }) {
  return (
    <div className="border rounded p-2 h-[600px] overflow-y-auto bg-white shadow">
      {items.map((it) => (
        <div
          key={it.sku}
          className="p-2 cursor-pointer border-b hover:bg-gray-100"
          onClick={() => onSelect(it)}
        >
          <div className="font-semibold">{it.name}</div>
          <div className="text-sm text-gray-500">{it.sku}</div>
        </div>
      ))}
    </div>
  );
}
