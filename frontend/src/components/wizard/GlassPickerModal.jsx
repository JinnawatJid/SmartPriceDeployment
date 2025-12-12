import { useEffect, useState } from "react";
import api from "../../services/api";

export default function GlassPickerModal({ open, onClose, onConfirm }) {
  
  const [loading, setLoading] = useState(false);
  const [glassList, setGlassList] = useState([]);

  // FILTERS
  const [search, setSearch] = useState("");
  const [brandFilter, setBrandFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [subGroupFilter, setSubGroupFilter] = useState("");
  const [colorFilter, setColorFilter] = useState("");
  const [thickFilter, setThickFilter] = useState("");

  // SELECTION
  const [selectedItem, setSelectedItem] = useState(null);

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

  // -------------------------
  // EFFECT 3: AUTO-CALCULATE
  // -------------------------
  useEffect(() => {
    if (!selectedItem) return;
    if (!width || !height) return;

    handleCalculate();
  }, [width, height, qtyCustomer, qtySku, unitW, unitH, selectedItem]);


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

    const wRawInch = convertToInch(width, unitW);
    const hRawInch = convertToInch(height, unitH);

    const wRound = roundSize(wRawInch);
    const hRound = roundSize(hRawInch);

    const sqftRaw = (wRawInch * hRawInch) / 144;
    const sqftRounded = (wRound * hRound) / 144;

    const actualSqft = sqftRaw * qtyCustomer;

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
        rawSqftPerPiece: sqftRaw,
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

  // 1) คำนวณพื้นที่ตาม SKU × จำนวนแผ่น
  const skuSqft =
    ((selectedItem.width * selectedItem.height) / 144) * qtySku;

  // 2) เลือก sqft ที่ต้องใช้คิดราคา
  const sqftToCharge =
    priceMode === "actual"
      ? calcResult.actualSqft
      : skuSqft;

  // 3) คำนวณราคา default = R2 × sqft
  const priceFinal = Number(calcResult.priceR2) * Number(sqftToCharge);

  // 4) ส่งกลับ Step6 แบบไม่ซ้ำ key 
  onConfirm({
    name: selectedItem.description,
    sku: selectedItem.sku,
    isGlass: true,

    price: priceFinal,  // ราคาแบบรวมแล้ว (R2 × sqft)
    qty: 1,             // qty = 1 เสมอ
    sqft: sqftToCharge, // ส่งกลับเพื่อแสดงผลใน Step6

    actualSqft: calcResult.actualSqft,
    skuSqft,
    qtyCustomer,
    qtySku,
    priceMode,
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
    return true;
  });

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
          <div className="border rounded p-3 mb-3">
            <div className="grid grid-cols-2 gap-4">

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

              {/* QTY CUSTOMER */}
              <div>
                <label>จำนวนที่ลูกค้าต้องการ</label>
                <input
                  className="border p-1 w-full"
                  type="number"
                  value={qtyCustomer}
                  onChange={(e) => setQtyCustomer(e.target.value)}
                />
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

              {/* QTY SKU */}
              <div>
                <label>จำนวนแผ่นตาม SKU</label>
                <input
                  className="border p-1 w-full"
                  type="number"
                  value={qtySku}
                  onChange={(e) => setQtySku(e.target.value)}
                />
              </div>

            </div>
          </div>
        

        {/* RESULT SECTION */}
        {calcResult && (
          <div className="p-3 border rounded bg-green-50 mb-3">
            <h3 className="font-bold text-green-700 mb-2">ผลการคำนวณ</h3>

            <p>ขนาดปัดแล้ว: {calcResult.width} × {calcResult.height} นิ้ว</p>
            <p>พื้นที่ปัดแล้ว (ไม่ได้ใช้คิดราคา): {calcResult.sqft.toFixed(2)} ตารางฟุต</p>

            <p className="mt-2 text-sm text-gray-700">
              พื้นที่ตามขนาดจริง (ไม่ปัด): {calcResult.actualSqft.toFixed(2)} sqft
            </p>

            <p className="text-sm text-gray-700">
              พื้นที่ตาม SKU × จำนวนแผ่น: {(
                (selectedItem.width * selectedItem.height) / 144 * qtySku
              ).toFixed(2)} sqft
            </p>

            {/* PRICE MODE */}
            <div className="mt-3 space-y-2">
              <label className="font-semibold">เลือกรูปแบบการคิดราคา</label>

              <label className="flex gap-2">
                <input
                  type="radio"
                  value="actual"
                  checked={priceMode === "actual"}
                  onChange={() => setPriceMode("actual")}
                />
                ใช้ขนาดจริงที่ลูกค้าสั่ง
              </label>

              <label className="flex gap-2">
                <input
                  type="radio"
                  value="sku"
                  checked={priceMode === "sku"}
                  onChange={() => setPriceMode("sku")}
                />
                ใช้ขนาดตาม SKU × จำนวนแผ่น
              </label>
            </div>

            {/* CONFIRM */}
            <button
              className="mt-3 bg-green-600 text-white px-4 py-2 rounded"
              onClick={handleConfirm}
            >
              เพิ่มลงใบเสนอราคา
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
