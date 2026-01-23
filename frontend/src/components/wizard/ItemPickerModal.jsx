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

  // ---------------- Add to summary (แทนการปิด modal) ----------------
  const handleAdd = (item, qty) => {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div
        className="w-full max-w-5xl bg-white rounded-xl shadow-xl p-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center pb-3 border-b">
          <h2 className="text-xl font-bold">เลือกสินค้า: {category}</h2>
          <button onClick={onClose}>✕</button>
        </div>

        <div className="mt-4 space-y-4">
          <input
            type="search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={`ค้นหาในหมวด ${category}`}
            className="w-full rounded-lg border p-3"
          />

          {category === "A" && <AluminiumPicker onSelect={setAluFilter} />}
          {category === "C" && <CLinePicker onSelect={setClineFilter} />}
          {category === "E" && <AccessoriesPicker onSelect={setAccFilter} />}
          {category === "S" && <SealantPicker onSelect={setSealantFilter} />}
          {category === "Y" && <GypsumPicker onSelect={setGypsumFilter} />}

          {loading && <Loader />}

          {!loading && (
            <div className="max-h-[480px] overflow-y-auto">
              <div className="grid grid-cols-2 gap-4">
                {filteredItems.map((item, idx) => (
                  <ItemCard
                    key={`${item.sku || item.SKU}-${idx}`}
                    item={item}
                    onAdd={handleAdd}
                  />
                ))}
              </div>
            </div>
          )}

          {/* ⭐ Summary Bar */}
          {selectedItems.length > 0 && (
            <div className="pt-3 border-t flex justify-between items-center">
              <div className="text-sm text-gray-700">
                เลือกแล้ว {selectedItems.length} รายการ • รวม{" "}
                {selectedItems.reduce((s, x) => s + x.qty, 0)} หน่วย
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedItems([])}
                  className="px-3 py-2 border rounded-lg"
                >
                  ล้าง
                </button>
                <button
                  onClick={handleConfirmAll}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg"
                >
                  ยืนยันรายการ
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ItemPickerModal;
