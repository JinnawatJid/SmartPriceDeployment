import { useState } from "react";

function toImageName(name = "") {
  return name
    .toLowerCase()
    .trim()
    .replace(/×/g, "x")
    .replace(/\s*x\s*/g, "x")
    .replace(/ตัว/g, "")
    .replace(/[\/|]/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

export default function CrossSellItem({ item, onAdd }) {
  const imgName = toImageName(item.displayName);
  const imgSrc = `/assets/cross-sell/${imgName}.jpg`;

  const [imgError, setImgError] = useState(false);

  return (
    <div className="flex items-center gap-3 border rounded p-2 bg-white">
      {/* รูป / fallback */}
      {!imgError ? (
        <img
          src={imgSrc}
          alt={item.displayName}
          onError={() => setImgError(true)}
          className="w-12 h-12 object-contain rounded bg-gray-100"
        />
      ) : (
        <div className="w-12 h-12 flex items-center justify-center rounded bg-gray-100 text-xs text-gray-400">
          ว่าง
        </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm line-clamp-2">{item.displayName}</div>
        <div className="text-xs text-gray-500">
          {item.ruleType === "main" ? "รายการหลัก" : "อุปกรณ์เสริม"}
        </div>
      </div>
    </div>
  );
}
