// src/components/wizard/PriceEditModal.jsx
import { useState } from "react";

// ฟังก์ชันปัดราคาให้ลง .50 หรือ .00
function roundUp050(x) {
  if (x < 1) {
    return Math.round(x * 100) / 100;
  }
  return Math.ceil(x * 2) / 2;
}

export default function PriceEditModal({ item, calculatedItem, onClose, onSave }) {
  const cat = (item.category || String(item.sku || "").slice(0, 1)).toUpperCase();
  const isGlass = cat === "G";
  const isAluminium = cat === "A";

  // ⭐ ดึงราคา W1 (ราคาอ้างอิงจากระบบ)
  const w1Price = Number(item.Price_System || calculatedItem?.UnitPrice || item.UnitPrice || item.price || 0);

  // สำหรับกระจก
  const currentSqft = Number(item.sqft_sheet ?? item.sqft ?? 0);
  const currentPricePerSheet =
    item.priceSource === "manual"
      ? Number(item.price_per_sheet ?? Number(item.UnitPrice ?? 0) * currentSqft)
      : Number(calculatedItem?.price_per_sheet ?? item.price_per_sheet ?? 0);

  // ถ้ามี pricePerSqft เก็บไว้แล้ว ให้ใช้ค่านั้น ไม่งั้นคำนวณจาก pricePerSheet / sqft
  const currentPricePerSqft =
    item.priceSource === "manual" && item.pricePerSqft
      ? Number(item.pricePerSqft)
      : currentSqft > 0 
        ? currentPricePerSheet / currentSqft 
        : 0;

  const [pricePerSqft, setPricePerSqft] = useState(currentPricePerSqft);
  const [showW1Warning, setShowW1Warning] = useState(false); // ⭐ สถานะแสดงคำเตือน

  // สำหรับอลูมิเนียม
  const currentUnitPrice =
    item.priceSource === "manual"
      ? Number(item.UnitPrice ?? item.price ?? 0)
      : Number(calculatedItem?.UnitPrice ?? item.UnitPrice ?? item.price ?? 0);

  const currentWeight = Number(item.weight ?? item.product_weight ?? calculatedItem?.product_weight ?? 0);

  // คำนวณราคาต่อกิโลกรัมจากราคาต่อเส้น
  // ถ้ามี pricePerKg เก็บไว้แล้ว ให้ใช้ค่านั้น ไม่งั้นคำนวณจาก unitPrice / weight
  const currentPricePerKg = 
    item.priceSource === "manual" && item.pricePerKg
      ? Number(item.pricePerKg)
      : currentWeight > 0 
        ? currentUnitPrice / currentWeight 
        : 0;

  const [pricePerKg, setPricePerKg] = useState(currentPricePerKg);
  const [weight, setWeight] = useState(currentWeight);

  // สำหรับสินค้าอื่นๆ (ไม่ใช่กระจกหรืออลู)
  const otherProductUnitPrice =
    item.priceSource === "manual"
      ? Number(item.UnitPrice ?? item.price ?? 0)
      : Number(calculatedItem?.UnitPrice ?? item.UnitPrice ?? item.price ?? 0);

  const [otherPrice, setOtherPrice] = useState(otherProductUnitPrice);

  // คำนวณราคาใหม่ (พร้อมปัด)
  const calculatedPricePerSheet = roundUp050(pricePerSqft * currentSqft);
  const calculatedPricePerLine = roundUp050(pricePerKg * weight);

  // ⭐ ตรวจสอบว่าราคาที่แก้ต่ำกว่า W1 หรือไม่
  const checkBelowW1 = () => {
    let newPrice = 0;
    
    if (isGlass) {
      newPrice = calculatedPricePerSheet;
    } else if (isAluminium) {
      newPrice = calculatedPricePerLine;
    } else {
      newPrice = otherPrice;
    }

    return newPrice < w1Price;
  };

  const handleSave = () => {
    // ⭐ ตรวจสอบก่อนบันทึก
    if (checkBelowW1()) {
      setShowW1Warning(true);
      return;
    }

    if (isGlass) {
      // บันทึกราคาต่อแผ่น (จากการคำนวณ)
      onSave({
        unitPrice: calculatedPricePerSheet,
        pricePerSqft: pricePerSqft,
      });
    } else if (isAluminium) {
      // บันทึกราคาต่อเส้น (จากการคำนวณ) และน้ำหนัก
      onSave({
        unitPrice: calculatedPricePerLine,
        pricePerKg: pricePerKg,
        weight: weight,
      });
    } else {
      // สินค้าอื่นๆ
      onSave({
        unitPrice: otherPrice,
      });
    }
  };

  // ⭐ ยืนยันบันทึกแม้ราคาต่ำกว่า W1
  const handleConfirmBelowW1 = () => {
    setShowW1Warning(false);
    
    if (isGlass) {
      onSave({
        unitPrice: calculatedPricePerSheet,
        pricePerSqft: pricePerSqft,
      });
    } else if (isAluminium) {
      onSave({
        unitPrice: calculatedPricePerLine,
        pricePerKg: pricePerKg,
        weight: weight,
      });
    } else {
      onSave({
        unitPrice: otherPrice,
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      {/* ⭐ Modal คำเตือนราคาต่ำกว่า W1 */}
      {showW1Warning && (
        <div className="absolute inset-0 bg-black bg-opacity-70 flex items-center justify-center z-10">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="text-center">
              <div className="text-5xl mb-4">⚠️</div>
              <h3 className="text-xl font-bold text-red-600 mb-2">
                ราคาต่ำกว่า W1
              </h3>
              <p className="text-gray-700 mb-4">
                ราคาที่คุณกำหนดต่ำกว่าราคา W1 (฿{w1Price.toLocaleString()})
              </p>
              <p className="text-gray-600 mb-6">
                กรุณาขอราคาพิเศษจากผู้อนุมัติก่อนดำเนินการต่อ
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowW1Warning(false)}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  แก้ไขราคา
                </button>
                <button
                  onClick={handleConfirmBelowW1}
                  className="flex-1 px-4 py-2 text-white bg-yellow-500 rounded-lg hover:bg-yellow-600"
                >
                  ดำเนินการต่อ (ต้องขอราคา)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-800">แก้ไขราคา</h3>
          <p className="text-sm text-gray-600 mt-1">{item.name}</p>
          <p className="text-xs text-gray-500">{item.sku}</p>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {isGlass ? (
            // ฟอร์มสำหรับกระจก
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ขนาด (ตารางฟุต)
                </label>
                <input
                  type="number"
                  value={currentSqft}
                  disabled
                  className="w-full px-3 py-2 border rounded-lg bg-gray-50 text-gray-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ราคาต่อตารางฟุต (บาท/ตร.ฟุต)
                </label>
                <input
                  type="number"
                  value={pricePerSqft}
                  onChange={(e) => setPricePerSqft(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  step="0.01"
                  min="0"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="text-sm text-gray-700 mb-2">การคำนวณ:</div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>
                    {currentSqft.toLocaleString("th-TH", { minimumFractionDigits: 2 })} ตร.ฟุต
                    × {pricePerSqft.toLocaleString("th-TH", { minimumFractionDigits: 2 })} บาท/ตร.ฟุต
                  </div>
                  <div className="text-lg font-semibold text-blue-700 mt-2">
                    = {calculatedPricePerSheet.toLocaleString("th-TH", { minimumFractionDigits: 2 })} บาท/แผ่น
                  </div>
                </div>
              </div>
            </>
          ) : isAluminium ? (
            // ฟอร์มสำหรับอลูมิเนียม
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  น้ำหนัก (กก./เส้น)
                </label>
                <input
                  type="number"
                  value={weight}
                  onChange={(e) => setWeight(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  step="0.01"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ราคาต่อกิโลกรัม (บาท/กก.)
                </label>
                <input
                  type="number"
                  value={pricePerKg}
                  onChange={(e) => setPricePerKg(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  step="0.01"
                  min="0"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="text-sm text-gray-700 mb-2">การคำนวณ:</div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>
                    {weight.toLocaleString("th-TH", { minimumFractionDigits: 2 })} กก./เส้น
                    × {pricePerKg.toLocaleString("th-TH", { minimumFractionDigits: 2 })} บาท/กก.
                  </div>
                  <div className="text-lg font-semibold text-blue-700 mt-2">
                    = {calculatedPricePerLine.toLocaleString("th-TH", { minimumFractionDigits: 2 })} บาท/เส้น
                  </div>
                </div>
              </div>
            </>
          ) : (
            // ฟอร์มสำหรับสินค้าอื่นๆ
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ราคาต่อหน่วย (บาท)
              </label>
              <input
                type="number"
                value={otherPrice}
                onChange={(e) => setOtherPrice(Number(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                step="0.01"
                min="0"
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            ยกเลิก
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            ยืนยัน
          </button>
        </div>
      </div>
    </div>
  );
}
