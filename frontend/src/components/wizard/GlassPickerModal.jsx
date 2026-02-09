import { useEffect, useState } from "react";
import api from "../../services/api";
import CustomDropdown from "../common/CustomDropdown";
import { useSelectedStatus } from "../../hooks/useSelectedStatus";

// Component สำหรับแสดงแถวของกระจกในตาราง
function GlassTableRow({ item, isActive, onClick }) {
  const sku = item.sku;
  const variantCode = item.variantCode || null;
  const sqft = 0; // กระจกใน list ยังไม่มีขนาดเฉพาะ
  const isSelected = useSelectedStatus(sku, variantCode, sqft);

  return (
    <tr
      className={`grid grid-cols-12 gap-2 items-center cursor-pointer
        hover:bg-blue-50 transition
        ${isActive ? "bg-blue-100" : ""}
      `}
      onClick={onClick}
    >
      <td className="col-span-2 p-2 truncate">{item.sku}</td>
      <td className={`col-span-4 p-2 truncate ${isSelected ? 'text-blue-600 font-semibold' : ''}`}>
        {isSelected && <span className="mr-1">✓</span>}
        {item.description}
      </td>
      <td className="col-span-2 p-2 truncate">{item.subGroupName}</td>
      <td className="col-span-2 p-2 text-center whitespace-nowrap">
        {item.width} × {item.height}
      </td>
      <td className="col-span-1 p-2 text-center">{item.thickness}</td>
      <td className="col-span-1 p-2 text-center font-semibold">{item.inventory}</td>
    </tr>
  );
}

export default function GlassPickerModal({ open, onClose, onConfirm }) {
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [glassList, setGlassList] = useState([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

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

  // FILTER OPTIONS
  const [filterOptions, setFilterOptions] = useState({
    brands: [],
    types: [],
    subGroups: [],
    colors: [],
    thicknesses: [],
  });

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
      case "cm":
        return val / 2.54;
      case "mm":
        return val / 25.4;
      case "ft":
        return val * 12;
      default:
        return val;
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
  // LOAD GLASS LIST (with pagination)
  // -------------------------
  const loadGlass = async (reset = false, searchQuery = "") => {
    if (!hasMore && !reset) return;

    // แยก loading state
    if (reset) {
      setLoading(true);
    } else {
      if (loadingMore) return;
      setLoadingMore(true);
    }

    const currentOffset = reset ? 0 : offset;

    try {
      const params = {
        limit: 10,
        offset: currentOffset,
      };

      // เพิ่ม filters
      if (brandFilter) params.brand = brandFilter;
      if (typeFilter) params.type = typeFilter;
      if (subGroupFilter) params.subGroup = subGroupFilter;
      if (colorFilter) params.color = colorFilter;
      if (thickFilter) params.thickness = thickFilter;
      if (searchQuery && searchQuery.trim()) params.search = searchQuery.trim();
      if (variantOnly) params.isVariant = true;

      const res = await api.get("/api/glass/list", { params });
      
      const newItems = res.data.items || [];
      const totalCount = res.data.total || 0;

      setGlassList((prev) => (reset ? newItems : [...prev, ...newItems]));
      setTotal(totalCount);

      const newOffset = currentOffset + newItems.length;
      setOffset(newOffset);
      setHasMore(newOffset < totalCount);

      if (reset) {
        const loadTime = performance.now();
        console.log(`✅ Glass list loaded (${newItems.length}/${totalCount} items)`);
      }
    } catch (err) {
      console.error("Error loading glass:", err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // -------------------------
  // EFFECT 1: LOAD INITIAL
  // -------------------------
  useEffect(() => {
    if (!open) return;

    setGlassList([]);
    setOffset(0);
    setHasMore(true);
    setTotal(0);
    setSelectedItem(null);
    setSearch("");

    loadGlass(true);
  }, [open]);

  // -------------------------
  // EFFECT 2: RELOAD ON FILTER CHANGE
  // -------------------------
  useEffect(() => {
    if (!open) return;

    setGlassList([]);
    setOffset(0);
    setHasMore(true);
    loadGlass(true, search);
  }, [brandFilter, typeFilter, subGroupFilter, colorFilter, thickFilter, variantOnly]);

  // -------------------------
  // EFFECT 3: RELOAD ON SEARCH (debounced)
  // -------------------------
  useEffect(() => {
    if (!open) return;

    const timer = setTimeout(() => {
      setGlassList([]);
      setOffset(0);
      setHasMore(true);
      loadGlass(true, search);
    }, 300);

    return () => clearTimeout(timer);
  }, [search]);

  // -------------------------
  // EFFECT: RESET calcResult WHEN sku changes
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
  // EFFECT: AUTO-CALCULATE
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

  // -------------------------
  // LOAD FILTER OPTIONS
  // -------------------------
  useEffect(() => {
    if (!open) return;

    const loadFilterOptions = async () => {
      try {
        const res = await api.get("/api/glass/filter-options");
        setFilterOptions(res.data);
      } catch (err) {
        console.error("Error loading filter options:", err);
      }
    };

    loadFilterOptions();
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
    const skuSqft = ((selectedItem.width * selectedItem.height) / 144) * qtySku;

    // 2) เลือก sqft ที่ต้องใช้คิดราคา
    const sqftToCharge = priceMode === "actual" ? calcResult.actualSqft : skuSqft;

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

      product_group: selectedItem.product_group ?? null,
      product_sub_group: selectedItem.product_sub_group ?? null,

      // --- quantity / area ---
      qty: Number(qtyCustomer), // จำนวนแผ่น
      sqft_sheet: Number(sqftPerPiece),
      skuSqft,
      unit: "แผ่น", // sqft ตาม SKU (เผื่อ audit)

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

  // ⚡ backend กรองให้แล้ว ไม่ต้องกรองฝั่ง client
  const filteredList = glassList;

  const isVariantReady = () => {
    if (!isVariant) return true; // non-variant พร้อมเสมอ
    return variantCode && width && height;
  };

  const brandDropdownOptions = filterOptions.brands;
  const typeDropdownOptions = filterOptions.types;
  const subGroupDropdownOptions = filterOptions.subGroups;
  const colorDropdownOptions = filterOptions.colors;
  const thicknessDropdownOptions = filterOptions.thicknesses;

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 ">
      <div className="bg-white w-[900px] max-h-[90vh] rounded-xl shadow-lg p-8 overflow-y-auto">
        {/* HEADER */}
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold">เลือกสินค้ากระจก</h2>
          <button className="text-red-600 font-bold" onClick={onClose}>
            X
          </button>
        </div>

        {/* SEARCH */}
        <input
          className="w-full border p-2 rounded my-3"
          placeholder="ค้นหา SKU / ชื่อสินค้า / SubGroup..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        {/* FILTERS */}
        <div className="flex items-end gap-3 mb-4">
          <CustomDropdown
            label="Brand"
            value={brandFilter || null}
            options={brandDropdownOptions}
            onChange={(v) => setBrandFilter(v || "")}
            width={160}
          />

          <CustomDropdown
            label="Group"
            value={typeFilter || null}
            options={typeDropdownOptions}
            onChange={(v) => setTypeFilter(v || "")}
            width={160}
          />

          <CustomDropdown
            label="SubGroup"
            value={subGroupFilter || null}
            options={subGroupDropdownOptions}
            onChange={(v) => setSubGroupFilter(v || "")}
            width={240}
          />

          <CustomDropdown
            label="Color"
            value={colorFilter || null}
            options={colorDropdownOptions}
            onChange={(v) => setColorFilter(v || "")}
            width={120}
          />

          <CustomDropdown
            label="Thickness"
            value={thickFilter || null}
            options={thicknessDropdownOptions}
            onChange={(v) => setThickFilter(v || "")}
            width={120}
          />
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
        <div 
          className="border rounded-lg p-2 max-h-[260px] overflow-y-auto mb-4"
          onScroll={(e) => {
            const el = e.currentTarget;
            const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 50;

            if (nearBottom && hasMore && !loadingMore) {
              loadGlass(false, search);
            }
          }}
        >
          {loading && glassList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mb-3"></div>
              <p className="text-sm text-gray-600">กำลังโหลดข้อมูลกระจก...</p>
            </div>
          ) : filteredList.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>ไม่พบสินค้าที่ตรงกับเงื่อนไข</p>
            </div>
          ) : (
            <>
              <table className="w-full text-sm">
                <thead className="bg-gray-100 sticky top-0 z-10">
                  <tr className="grid grid-cols-12 gap-2 text-gray-700 font-semibold">
                    <th className="col-span-2 p-2 text-left">SKU</th>
                    <th className="col-span-4 p-2 text-left">ชื่อสินค้า</th>
                    <th className="col-span-2 p-2 text-left">SubGroup</th>
                    <th className="col-span-2 p-2 text-center">ขนาด (นิ้ว)</th>
                    <th className="col-span-1 p-2 text-center">หนา</th>
                    <th className="col-span-1 p-2 text-center">สต๊อก</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredList.map((item, idx) => (
                    <GlassTableRow
                      key={`${item.sku}-${idx}`}
                      item={item}
                      isActive={selectedItem?.sku === item.sku}
                      onClick={() => setSelectedItem(item)}
                    />
                  ))}
                </tbody>
              </table>

              {/* Loading indicator สำหรับโหลดเพิ่ม */}
              {loadingMore && (
                <div className="flex justify-center py-3">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    กำลังโหลดเพิ่ม...
                  </div>
                </div>
              )}

              {/* แสดงว่าโหลดครบแล้ว */}
              {!hasMore && filteredList.length > 0 && (
                <div className="text-xs text-gray-400 text-center py-3 border-t mt-2">
                  โหลดครบแล้ว
                </div>
              )}
            </>
          )}
          
          {/* แสดงจำนวนผลลัพธ์ */}
          {!loading && filteredList.length > 0 && (
            <div className="text-xs text-gray-500 text-center mt-2 pt-2 border-t">
              แสดง {filteredList.length} รายการ
              {total > 0 && ` จากทั้งหมด ${total} รายการ`}
            </div>
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

            <p>
              ขนาดปัดลงฟุตแล้ว: {calcResult.width} × {calcResult.height} นิ้ว
            </p>
            <p>พื้นที่ต่อแผ่น: {calcResult.sqft.toFixed(2)} ตารางฟุต</p>
            <p className="font-bold ">
              พื้นที่รวม ({qtyCustomer} แผ่น): {(calcResult.sqft * qtyCustomer).toFixed(2)} ตารางฟุต
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
