import { useEffect, useState } from "react";
import api from "../../services/api";

export default function GlassPickerModal({ open, onClose, onConfirm }) {
  
  const [loading, setLoading] = useState(false);
  const [glassList, setGlassList] = useState([]);

  // FILTERS
  const [search, setSearch] = useState("");
  const [variantOnly, setVariantOnly] = useState(false);
  const [brandFilter, setBrandFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [subGroupFilter, setSubGroupFilter] = useState("");
  const [colorFilter, setColorFilter] = useState("");
  const [thickFilter, setThickFilter] = useState("");

  // SELECTION
  const [selectedItem, setSelectedItem] = useState(null);
  const [variantCode, setVariantCode] = useState("");


  // SIZE INPUTS
  const [width, setWidth] = useState("");
  const [height, setHeight] = useState("");
  const [unitW, setUnitW] = useState("inch");
  const [unitH, setUnitH] = useState("inch");
  

  // RESULT
  const [calcResult, setCalcResult] = useState(null);

  // NEW VARIABLES
  const [qtyCustomer, setQtyCustomer] = useState(1);
  const [qtySku, setQtySku] = useState(1);
  const [priceMode, setPriceMode] = useState("actual");

  // STEP SIZE
  const STEPS = [12, 18, 24, 30, 36, 42, 48, 60, 72, 84, 96, 120, 144];

  const isVariant = !!selectedItem?.isVariant;

  


  // -------------------------
  // FUNCTIONS
  // -------------------------
  function convertToInch(val, unit) {
    if (!val) return 0;
    val = Number(val);
    switch (unit) {
      case "cm": return val / 2.54;
      case "mm": return val / 25.4;
      case "ft": return val * 12;
      default: return val;
    }
  }

  function roundSize(inchVal) {
    if (inchVal > 144) return inchVal;
    for (let s of STEPS) {
      if (inchVal <= s) return s;
    }
    return inchVal;
  }

  // -------------------------
  // EFFECT 1: LOAD GLASS LIST
  // -------------------------
  useEffect(() => {
    if (!open) return;

    const loadGlass = async () => {
      setLoading(true);
      try {
        const res = await api.get("/api/glass/list");
        setGlassList(res.data.items || []);
      } catch (err) {
        console.error("Error loading glass:", err);
      }
      setLoading(false);
    };

    loadGlass();
  }, [open]);

  // -------------------------
  // EFFECT 2: RESET calcResult WHEN sku changes
  // -------------------------
  useEffect(() => {
    setCalcResult(null);
  }, [selectedItem]);

  useEffect(() => {
    setVariantCode("");
    setWidth("");
    setHeight("");
  }, [selectedItem]);


  // -------------------------
  // EFFECT 3: AUTO-CALCULATE
  // -------------------------
  // -------------------------
 useEffect(() => {
  if (!selectedItem) return;

  if (isVariant) {
    if (!width || !height) return;
  }

  handleCalculate();
}, [selectedItem, width, height, qtyCustomer, unitW, unitH, isVariant]);




  useEffect(() => {
    if (open) {
      setSelectedItem(null);
      setWidth("");
      setHeight("");
      setQtyCustomer(1);
      setQtySku(1);
      setCalcResult(null);
      setPriceMode("actual");
    }
  }, [open]);

  async function handleCalculate() {
  if (!selectedItem) return;

  let wRawInch, hRawInch;
  let wRound, hRound;

  // -------------------------
  // 1️⃣ แยก Variant / Non-Variant
  // -------------------------
  if (isVariant) {
    // 🔹 Variant: ใช้ขนาดที่กรอก
    wRawInch = convertToInch(width, unitW);
    hRawInch = convertToInch(height, unitH);

    wRound = roundSize(wRawInch);
    hRound = roundSize(hRawInch);
  } else {
    // 🔹 Non-Variant: ใช้ขนาดจาก SKU
    wRawInch = Number(selectedItem.width);
    hRawInch = Number(selectedItem.height);

    // ขนาด SKU ถือว่าเป็นขนาดปัดแล้ว
    wRound = wRawInch;
    hRound = hRawInch;
  }

  // -------------------------
  // 2️⃣ คำนวณพื้นที่
  // -------------------------
  const sqftRaw = (wRawInch * hRawInch) / 144;
  const sqftRounded = (wRound * hRound) / 144;

  const actualSqft = sqftRounded * qtyCustomer; // ✅ คิดแบบปัดตามที่คุณต้องการ

  // -------------------------
  // 3️⃣ payload ส่งไป backend (ใช้รูปแบบเดียวกัน)
  // -------------------------
  const payload = {
    sku: selectedItem.sku,
    widthRaw: wRawInch,
    heightRaw: hRawInch,
    widthRounded: wRound,
    heightRounded: hRound,
    sqftRaw,
    sqftRounded,
    qty: 1,
  };

  try {
    const res = await api.post("/api/glass/calc", payload);

    setCalcResult({
      ...res.data,
      actualSqft,
    });
  } catch (err) {
    console.error("CALC ERROR:", err);
  }
}

  // -------------------------
  // CONFIRM
  // -------------------------
  function handleConfirm() {
  if (!calcResult || !selectedItem) return;

  const sqftPerPiece = Number(calcResult.sqft || 0);

  // 1) คำนวณพื้นที่ตาม SKU × จำนวนแผ่น
  const skuSqft =
    ((selectedItem.width * selectedItem.height) / 144) * qtySku;

  // 2) เลือก sqft ที่ต้องใช้คิดราคา
  const sqftToCharge =
    priceMode === "actual"
      ? calcResult.actualSqft
      : skuSqft;


  // 🔑 4) สร้างชื่อใหม่ (Variant / Non-Variant)
  const finalName =
    isVariant && variantCode
      ? `${selectedItem.description} ${variantCode}`
      : selectedItem.description;

  // 5) ส่งกลับ Step6
onConfirm({
  // --- identity ---
  sku: selectedItem.sku,
  name: finalName,
  category: "G",
  isGlass: true,
  isVariant,

  // --- quantity / area ---
  qty: Number(qtyCustomer),          // จำนวนแผ่น
  sqft_sheet: Number(sqftPerPiece),
  skuSqft,   
  unit: "แผ่น",                         // sqft ตาม SKU (เผื่อ audit)

  // --- cut / variant meta ---
  variantCode: isVariant ? variantCode : null,
  widthRaw: calcResult.widthRaw,
  heightRaw: calcResult.heightRaw,
  widthRounded: calcResult.widthRounded,
  heightRounded: calcResult.heightRounded,

  // --- flags ---
  priceMode,  
  isDraftItem: false,                       
});

  onClose();
}



  // -------------------------
  // RENDER UI
  // -------------------------
  if (!open) return null;

  const filteredList = glassList.filter((item) => {
    if (search) {
      const s = search.toLowerCase();
      const combined =
        `${item.sku} ${item.subGroupName} ${item.brandName} ${item.typeName}`.toLowerCase();
      if (!combined.includes(s)) return false;
    }
    if (brandFilter && item.brand !== brandFilter) return false;
    if (typeFilter && item.type !== typeFilter) return false;
    if (subGroupFilter && item.subGroup !== subGroupFilter) return false;
    if (colorFilter && item.color !== colorFilter) return false;
    if (thickFilter && String(item.thickness) !== String(thickFilter)) return false;
    if (variantOnly && !item.isVariant) return false;
    return true;
  });

  const isVariantReady = () => {
    if (!isVariant) return true; // non-variant พร้อมเสมอ
    return (
      variantCode &&
      width &&
      height
    );
  };


  const brandOptions = [...new Set(glassList.map((i) => i.brand))];
  const typeOptions = [...new Set(glassList.filter((i) => !brandFilter || i.brand === brandFilter).map((i) => i.type))];
  const subGroupOptions = [...new Set(glassList.filter((i) =>
    (!brandFilter || i.brand === brandFilter) &&
    (!typeFilter || i.type === typeFilter)
  ).map((i) => i.subGroup))];
  const colorOptions = [...new Set(glassList.filter((i) =>
    (!brandFilter || i.brand === brandFilter) &&
    (!typeFilter || i.type === typeFilter) &&
    (!subGroupFilter || i.subGroup === subGroupFilter)
  ).map((i) => i.color))];
  const thicknessOptions = [...new Set(glassList.filter((i) =>
    (!brandFilter || i.brand === brandFilter) &&
    (!typeFilter || i.type === typeFilter) &&
    (!subGroupFilter || i.subGroup === subGroupFilter) &&
    (!colorFilter || i.color === colorFilter)
  ).map((i) => i.thickness))];

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 ">
      <div className="bg-white w-[900px] max-h-[90vh] rounded-lg shadow-lg p-4 overflow-y-auto">

        {/* HEADER */}
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold">เลือกสินค้ากระจก</h2>
          <button className="text-red-600 font-bold" onClick={onClose}>X</button>
        </div>

        {/* SEARCH */}
        <input
          className="w-full border p-2 rounded my-3"
          placeholder="ค้นหา SKU / ชื่อสินค้า / SubGroup..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        {/* FILTERS */}
        <div className="grid grid-cols-5 gap-2 mb-4">
          <select className="border p-2 rounded" value={brandFilter} onChange={(e) => setBrandFilter(e.target.value)}>
            <option value="">แบรนด์ทั้งหมด</option>
            {brandOptions.map((code) => {
              const label = glassList.find((x) => x.brand === code)?.brandName || code;
              return <option key={code} value={code}>{label}</option>;
            })}
          </select>

          <select className="border p-2 rounded" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="">ชนิดทั้งหมด</option>
            {typeOptions.map((code) => {
              const label = glassList.find((x) => x.type === code)?.typeName || code;
              return <option key={code} value={code}>{label}</option>;
            })}
          </select>

          <select className="border p-2 rounded" value={subGroupFilter} onChange={(e) => setSubGroupFilter(e.target.value)}>
            <option value="">กลุ่มย่อยทั้งหมด</option>
            {subGroupOptions.map((code) => {
              const label = glassList.find((x) => x.subGroup === code)?.subGroupName || code;
              return <option key={code} value={code}>{label}</option>;
            })}
          </select>

          <select className="border p-2 rounded" value={colorFilter} onChange={(e) => setColorFilter(e.target.value)}>
            <option value="">สีทั้งหมด</option>
            {colorOptions.map((code) => {
              const label = glassList.find((x) => x.color === code)?.colorName || code;
              return <option key={code} value={code}>{label}</option>;
            })}
          </select>

          <select className="border p-2 rounded" value={thickFilter} onChange={(e) => setThickFilter(e.target.value)}>
            <option value="">ความหนา</option>
            {thicknessOptions.map((t) => (
              <option key={t} value={t}>{t} มม.</option>
            ))}
          </select>
        </div>

                
        {/* VARIANT CHECKBOX (เพิ่มใหม่) */}
        <div className="mb-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={variantOnly}
              onChange={(e) => setVariantOnly(e.target.checked)}
            />
            แสดงเฉพาะสินค้า รหัสกลุ่ม
          </label>
        </div>

        {/* SKU TABLE */}
        <div className="border rounded p-2 max-h-[250px] overflow-y-auto mb-4">
          {loading ? (
            <p>กำลังโหลดข้อมูล...</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="p-1">SKU</th>
                  <th className="p-1">ชื่อสินค้า</th>
                  <th className="p-1">SubGroup</th>
                  <th className="p-1">ขนาด (นิ้ว)</th>
                  <th className="p-1">หนา</th>
                  <th className="p-1">สต๊อก</th>
                </tr>
              </thead>
              <tbody>
                {filteredList.map((item) => (
                  <tr
                    key={item.sku}
                    className={`cursor-pointer hover:bg-blue-50 ${
                      selectedItem?.sku === item.sku ? "bg-blue-100" : ""
                    }`}
                    onClick={() => setSelectedItem(item)}
                  >
                    <td className="p-1">{item.sku}</td>
                    <td className="p-1">{item.description}</td>
                    <td className="p-1">{item.subGroupName}</td>
                    <td className="p-1">{item.width} × {item.height}</td>
                    <td className="p-1">{item.thickness} มม.</td>
                    <td className="p-1">{item.inventory}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* SIZE SECTION */}
        {selectedItem && isVariant && (
          <div className="border rounded p-3 mb-3">
            <div className="grid grid-cols-2 gap-4">

              {/* VARIANT CODE */}
              <div className="col-span-2">
                <label>Variant Code</label>
                <input
                  className="border p-1 w-full"
                  placeholder="เช่น 1000x1050MM"
                  value={variantCode}
                  onChange={(e) => setVariantCode(e.target.value)}
                />
              </div>

              {/* WIDTH */}
              <div>
                <label>กว้าง</label>
                <div className="flex gap-2">
                  <input
                    className="border p-1 w-full"
                    value={width}
                    onChange={(e) => setWidth(e.target.value)}
                  />
                  <select
                    className="border p-1"
                    value={unitW}
                    onChange={(e) => setUnitW(e.target.value)}
                  >
                    <option value="inch">inch</option>
                    <option value="cm">cm</option>
                    <option value="mm">mm</option>
                    <option value="ft">ft</option>
                  </select>
                </div>
              </div>

              {/* HEIGHT */}
              <div>
                <label>ยาว</label>
                <div className="flex gap-2">
                  <input
                    className="border p-1 w-full"
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                  />
                  <select
                    className="border p-1"
                    value={unitH}
                    onChange={(e) => setUnitH(e.target.value)}
                  >
                    <option value="inch">inch</option>
                    <option value="cm">cm</option>
                    <option value="mm">mm</option>
                    <option value="ft">ft</option>
                  </select>
                </div>
              </div>

              {/* QTY CUSTOMER */}
              <div className="col-span-2">
                <label>จำนวนแผ่น</label>
                <input
                  className="border p-1 w-full"
                  type="number"
                  min={1}
                  value={qtyCustomer}
                  onChange={(e) => setQtyCustomer(e.target.value)}
                />
              </div>

            </div>
          </div>
        )}

      {/* ---------- NON-VARIANT ---------- */}
      {selectedItem && !isVariant && (
        <div className="border rounded p-3 mb-3">
          <div>
            <label>จำนวนแผ่น</label>
            <input
              className="border p-1 w-full"
              type="number"
              min={1}
              value={qtyCustomer}
              onChange={(e) => setQtyCustomer(e.target.value)}
            />
          </div>
        </div>
      )}
       


        {/* RESULT SECTION */}
        {calcResult && (
          <div className="p-3 border rounded bg-green-50 mb-3">
            <h3 className="font-bold text-green-700 mb-2">ผลการคำนวณ</h3>

            <p>ขนาดปัดลงฟุตแล้ว: {calcResult.width} × {calcResult.height} นิ้ว</p>
            <p>
              พื้นที่ต่อแผ่น: {calcResult.sqft.toFixed(2)} ตารางฟุต
            </p>
            <p className="font-bold ">
              พื้นที่รวม ({qtyCustomer} แผ่น):{" "}
              {(calcResult.sqft * qtyCustomer).toFixed(2)} ตารางฟุต
            </p>


             {/* CONFIRM ACTION */}
        {selectedItem && (
          <div className=" bg-green-50 mt-3">
            <button
              onClick={handleConfirm}
              disabled={!isVariantReady()}
              className={`px-4 py-2 rounded text-white ${
                isVariantReady()
                  ? "bg-green-600 hover:bg-green-700"
                  : "bg-gray-400 cursor-not-allowed"
              }`}
            >
              เพิ่มลงใบเสนอราคา
            </button>

            {isVariant && !isVariantReady() && (
              <div className="text-xs text-gray-600 mt-2">
                * กรุณากรอก Variant Code และขนาดให้ครบก่อน
              </div>
            )}
          </div>
        )}
            
          </div>
        )}

      </div>
    </div>
  );
}
