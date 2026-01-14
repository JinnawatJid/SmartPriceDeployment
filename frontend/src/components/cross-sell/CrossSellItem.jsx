function toImageName(name = "") {
  return name
    .toLowerCase()
    .trim()
    .replace(/×/g, "x")          // × → x
    .replace(/\s*x\s*/g, "x")    // 60 x 60 → 60x60
    .replace(/ตัว/g, "")         // ตัดคำว่า ตัว
    .replace(/[\/|]/g, "-")      // / | → -
    .replace(/\s+/g, "-")        // space → -
    .replace(/-+/g, "-")         // --- → -
    .replace(/^-|-$/g, "");      // ตัด - หน้า/หลัง
}

export default function CrossSellItem({ item, onAdd }) {
  const imgName = toImageName(item.displayName);
  const imgSrc = `/assets/cross-sell/${imgName}.jpg`;

  return (
    <div className="flex items-center gap-3 border rounded p-2 bg-white">
      <img
        src={imgSrc}
        alt={item.displayName}
        onError={(e) => {
          e.currentTarget.src = "/assets/cross-sell/default.png";
        }}
        className="w-12 h-12 object-contain rounded bg-gray-100"
      />

      <div className="flex-1">
        <div className="font-medium text-sm">
          {item.displayName}
        </div>
        <div className="text-xs text-gray-500">
          {item.ruleType === "main" ? "รายการหลัก" : "อุปกรณ์เสริม"}
        </div>
      </div>
    </div>
  );
}
