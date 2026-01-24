import React, { useState, useEffect, useMemo } from "react";
import api from "../../services/api.js";
import Loader from "../Loader.jsx";
import ItemCard from "./ItemCard.jsx";
import AluminiumPicker from "./AluminiumPicker.jsx";
import CLinePicker from "./CLinePicker.jsx";
import AccessoriesPicker from "./AccessoriesPicker.jsx";
import SealantPicker from "./SealantPicker.jsx";
import GypsumPicker from "./GypsumPicker.jsx";

function ItemPickerModal({ open, category, onClose, onConfirm }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  // ⭐ state สำหรับ multi-add summary
  const [selectedItems, setSelectedItems] = useState([]);
  // ⭐ item ที่ user คลิกอยู่
  const [activeItem, setActiveItem] = useState(null);


  // ---------------- Filters ----------------
  const [aluFilter, setAluFilter] = useState({
    brand: null,
    group: null,
    subGroup: null,
    color: null,
    thickness: null,
  });

  const [clineFilter, setClineFilter] = useState({
    brand: null,
    group: null,
    subGroup: null,
    color: null,
    thickness: null,
  });

  const [accFilter, setAccFilter] = useState({
    brand: null,
    group: null,
    subGroup: null,
    color: null,
    character: null,
  });

  const [sealantFilter, setSealantFilter] = useState({
    brand: null,
    group: null,
    subGroup: null,
    color: null,
  });

  const [gypsumFilter, setGypsumFilter] = useState({
    brand: null,
    group: null,
    subGroup: null,
    color: null,
    thickness: null,
  });

  // ---------------- SKU Parsers ----------------
  const parseAluminiumSku = (skuRaw) => {
    const sku = String(skuRaw || "").toUpperCase().trim();
    if (!sku.startsWith("A") || sku.length < 12) {
      return { brand: null, group: null, subGroup: null, color: null, thickness: null };
    }
    return {
      brand: sku.slice(1, 3),
      group: sku.slice(3, 5),
      subGroup: sku.slice(5, 8),
      color: sku.slice(8, 10),
      thickness: sku.slice(10, 12),
    };
  };

  const parseCLineSku = (skuRaw) => {
    const sku = String(skuRaw || "").toUpperCase().trim();
    if (!sku.startsWith("C") || sku.length < 12) {
      return { brand: null, group: null, subGroup: null, color: null, thickness: null };
    }
    return {
      brand: sku.slice(1, 3),
      group: sku.slice(3, 5),
      subGroup: sku.slice(5, 8),
      color: sku.slice(8, 10),
      thickness: sku.slice(10, 12),
    };
  };

  const parseAccessoriesSku = (skuRaw) => {
    const sku = String(skuRaw || "").toUpperCase().trim();
    if (!sku.startsWith("E") || sku.length < 11) {
      return { brand: null, group: null, subGroup: null, color: null, character: null };
    }
    return {
      brand: sku.slice(1, 4),
      group: sku.slice(4, 6),
      subGroup: sku.slice(6, 8),
      color: sku.slice(8, 10),
      character: sku.slice(10, 11),
    };
  };

  const parseSealantSku = (skuRaw) => {
    const sku = String(skuRaw || "").toUpperCase().trim();
    if (!sku.startsWith("S") || sku.length < 10) {
      return { brand: null, group: null, subGroup: null, color: null };
    }
    return {
      brand: sku.slice(1, 3),
      group: sku.slice(3, 5),
      subGroup: sku.slice(5, 8),
      color: sku.slice(8, 10),
    };
  };

  const parseGypsumSku = (skuRaw) => {
    const sku = String(skuRaw || "").toUpperCase().trim();
    if (!sku.startsWith("Y") || sku.length < 18) {
      return { brand: null, group: null, subGroup: null, color: null, thickness: null };
    }
    return {
      brand: sku.slice(1, 3),
      group: sku.slice(3, 5),
      subGroup: sku.slice(5, 7),
      color: sku.slice(7, 10),
      thickness: sku.slice(10, 12),
    };
  };

  // ---------------- Load items ----------------
  useEffect(() => {
    if (!open || !category) return;

    const loadItems = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/api/items/categories/${category}`);
        setItems(res.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadItems();
  }, [open, category]);

  // ---------------- Filtered items ----------------
  const filteredItems = useMemo(() => {
    let base = items;

    if (category === "A") {
      base = base.filter((it) => {
        const p = parseAluminiumSku(it.sku || it.SKU);
        if (aluFilter.brand && p.brand !== aluFilter.brand) return false;
        if (aluFilter.group && p.group !== aluFilter.group) return false;
        if (aluFilter.subGroup && p.subGroup !== aluFilter.subGroup) return false;
        if (aluFilter.color && p.color !== aluFilter.color) return false;
        if (aluFilter.thickness && p.thickness !== aluFilter.thickness) return false;
        return true;
      });
    } else if (category === "C") {
      base = base.filter((it) => {
        const p = parseCLineSku(it.sku || it.SKU);
        if (clineFilter.brand && p.brand !== clineFilter.brand) return false;
        if (clineFilter.group && p.group !== clineFilter.group) return false;
        if (clineFilter.subGroup && p.subGroup !== clineFilter.subGroup) return false;
        if (clineFilter.color && p.color !== clineFilter.color) return false;
        if (clineFilter.thickness && p.thickness !== clineFilter.thickness) return false;
        return true;
      });
    } else if (category === "E") {
      base = base.filter((it) => {
        const p = parseAccessoriesSku(it.sku || it.SKU);
        if (accFilter.brand && p.brand !== accFilter.brand) return false;
        if (accFilter.group && p.group !== accFilter.group) return false;
        if (accFilter.subGroup && p.subGroup !== accFilter.subGroup) return false;
        if (accFilter.color && p.color !== accFilter.color) return false;
        if (accFilter.character && p.character !== accFilter.character) return false;
        return true;
      });
    } else if (category === "S") {
      base = base.filter((it) => {
        const p = parseSealantSku(it.sku || it.SKU);
        if (sealantFilter.brand && p.brand !== sealantFilter.brand) return false;
        if (sealantFilter.group && p.group !== sealantFilter.group) return false;
        if (sealantFilter.subGroup && p.subGroup !== sealantFilter.subGroup) return false;
        if (sealantFilter.color && p.color !== sealantFilter.color) return false;
        return true;
      });
    } else if (category === "Y") {
      base = base.filter((it) => {
        const p = parseGypsumSku(it.sku || it.SKU);
        if (gypsumFilter.brand && p.brand !== gypsumFilter.brand) return false;
        if (gypsumFilter.group && p.group !== gypsumFilter.group) return false;
        if (gypsumFilter.subGroup && p.subGroup !== gypsumFilter.subGroup) return false;
        if (gypsumFilter.color && p.color !== gypsumFilter.color) return false;
        if (gypsumFilter.thickness && p.thickness !== gypsumFilter.thickness) return false;
        return true;
      });
    }

    if (!searchTerm) return base;
    const term = searchTerm.toLowerCase();

    return base.filter((it) =>
      String(it.name || "").toLowerCase().includes(term) ||
      String(it.sku || it.SKU || "").toLowerCase().includes(term) ||
      String(it.alternate_names || "").toLowerCase().includes(term)
    );
  }, [
    items,
    searchTerm,
    category,
    aluFilter,
    clineFilter,
    accFilter,
    sealantFilter,
    gypsumFilter,
  ]);

  const relatedItems = useMemo(() => {
    if (!activeItem?.product_group) return [];

    return items.filter((it) => {
      if ((it.sku || it.SKU) === (activeItem.sku || activeItem.SKU)) return false;
      return it.product_group === activeItem.product_group;
    });
  }, [activeItem, items]);

  // ---------------- Add to summary (แทนการปิด modal) ----------------
  const handleAdd = (item, qty) => {
    setActiveItem(item);
    const normalizedItem = {
      ...item,
      unit: item.unit || item["Base Unit Measure"] || item.saleUnit || item.uom || "-",
      pkg_size: item.pkg_size ?? item.pkgSize ?? 1,
      product_weight: item.product_weight ?? item.ProductWeight ?? 0,
      product_group: item.product_group ?? null,
      product_sub_group: item.product_sub_group ?? null,
    };

    const sku = normalizedItem.sku || normalizedItem.SKU;

    setSelectedItems((prev) => {
      const exist = prev.find((x) => x.sku === sku);
      if (exist) {
        return prev.map((x) =>
          x.sku === sku ? { ...x, qty: x.qty + qty } : x
        );
      }
      return [...prev, { sku, item: normalizedItem, qty }];
    });
  };

  // ---------------- Remove one from summary ----------------
  const handleRemoveSelected = (sku) => {
    setSelectedItems((prev) => prev.filter((x) => x.sku !== sku));
  };

  // ---------------- Clear all (and reset related) ----------------
  const handleClearAll = () => {
    setSelectedItems([]);
    setActiveItem(null);
  };


  // ---------------- Confirm all ----------------
  const handleConfirmAll = () => {
    if (!onConfirm || selectedItems.length === 0) return;

    selectedItems.forEach(({ item, qty }) => {
      onConfirm(item, qty); // ⭐ interface เดิม
    });

    setSelectedItems([]);
    onClose();
  };

  if (!open) return null;

  return (
  <div className="fixed inset-0 z-50 bg-black/50 p-4 flex">
    <div
        className="w-full max-w-6xl bg-white rounded-2xl shadow-2xl
                  max-h-[90vh] flex flex-col p-6
                  mx-auto "
        onClick={(e) => e.stopPropagation()}
      >

      {/* ================= HEADER ================= */}
      <div className="flex justify-between items-center pb-4 border-b shrink-0">
        <h2 className="text-xl font-bold">
          เลือกสินค้า <span className="text-gray-400">({category})</span>
        </h2>
        <button
          onClick={() => {
            handleClearAll();
            onClose();
          }}

          className="text-gray-500 hover:text-black"
        >
          ✕
        </button>
      </div>

      {/* ================= BODY ================= */}
      <div className="mt-4 flex-1 min-h-0 flex flex-col gap-4">
        {/* SEARCH */}
        <input
          type="search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={`ค้นหาในหมวด ${category}`}
          className="w-full rounded-xl border px-4 py-3
                     focus:ring-2 focus:ring-blue-200 outline-none"
        />

        {/* FILTERS */}
        <div className="shrink-0">
          {category === "A" && <AluminiumPicker onSelect={setAluFilter} />}
          {category === "C" && <CLinePicker onSelect={setClineFilter} />}
          {category === "E" && <AccessoriesPicker onSelect={setAccFilter} />}
          {category === "S" && <SealantPicker onSelect={setSealantFilter} />}
          {category === "Y" && <GypsumPicker onSelect={setGypsumFilter} />}
        </div>

        {/* CONTENT */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {loading && <Loader />}

          {!loading && (
            <div className="grid grid-cols-2 gap-5 h-full min-h-0 overflow-hidden">
              {/* ================= LEFT ================= */}
              <div className="flex flex-col bg-gray-50 rounded-xl border overflow-hidden">
                <div className="px-4 py-2 text-sm font-semibold text-gray-700 border-b bg-white">
                  รายการสินค้า
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                  <div className="grid grid-cols-1 gap-4">
                    {filteredItems.map((item, idx) => (
                      <ItemCard
                        key={`${item.sku || item.SKU}-${idx}`}
                        item={item}
                        onAdd={handleAdd}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* ================= RIGHT ================= */}
              <div className="flex flex-col bg-gray-50 rounded-xl border overflow-hidden">
                <div className="px-4 py-2 text-sm font-semibold text-gray-700 border-b bg-white">
                  สินค้าในกลุ่มเดียวกัน
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                  {!activeItem && (
                    <div className="text-sm text-gray-400 text-center mt-10">
                      เลือกสินค้าเพื่อดูรายการที่เกี่ยวข้อง
                    </div>
                  )}

                  {activeItem && relatedItems.length === 0 && (
                    <div className="text-sm text-gray-400 text-center mt-10">
                      ไม่พบสินค้าใน Product Group เดียวกัน
                    </div>
                  )}

                  <div className="grid grid-cols-1 gap-4">
                    {relatedItems.map((item, idx) => (
                      <ItemCard
                        key={`related-${item.sku || item.SKU}-${idx}`}
                        item={item}
                        onAdd={handleAdd}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ================= ADDED ITEMS LIST ================= */}
      {selectedItems.length > 0 && (
        <div className="border rounded-xl bg-gray-50">
          <div className="px-4 py-2 border-b bg-white rounded-t-xl flex items-center justify-between">
            <div className="text-sm font-semibold text-gray-700">
              รายการที่เพิ่มแล้ว ({selectedItems.length})
            </div>
            <button
              onClick={handleClearAll}
              className="text-xs px-3 py-1 border rounded-lg hover:bg-gray-50"
            >
              ล้างทั้งหมด
            </button>
          </div>

          <div className="max-h-[160px] overflow-y-auto p-3 space-y-2">
            {selectedItems.map(({ sku, item, qty }) => (
              <div
                key={sku}
                className="flex items-center justify-between bg-white border rounded-lg px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">
                    {item?.name || "-"}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    SKU: {sku} • Qty: {qty} {item?.unit ? item.unit : ""}
                  </div>
                </div>

                <button
                  onClick={() => handleRemoveSelected(sku)}
                  className="ml-3 text-sm px-3 py-1 border rounded-lg hover:bg-red-50 hover:border-red-200"
                  title="ลบรายการนี้"
                >
                  ลบ
                </button>
              </div>
            ))}
          </div>
        </div>
      )}


      {/* ================= SUMMARY BAR ================= */}
      {selectedItems.length > 0 && (
        <div className="pt-4 border-t flex justify-between items-center shrink-0 bg-white">
          <div className="text-sm text-gray-700">
            เลือกแล้ว {selectedItems.length} รายการ • รวม{" "}
            {selectedItems.reduce((s, x) => s + x.qty, 0)} หน่วย
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleClearAll}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              ล้าง
            </button>
            <button
              onClick={handleConfirmAll}
              className="px-5 py-2 bg-green-600 text-white rounded-lg
                         hover:bg-green-700 shadow"
            >
              ยืนยันรายการ
            </button>
          </div>
        </div>
      )}
    </div>
  </div>
);


}

export default ItemPickerModal;
