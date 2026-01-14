// src/components/wizard/ItemPickerModal.jsx
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

  // ✅ state สำหรับฟิลเตอร์อลูมิเนียม – ต้องอยู่ก่อน useMemo
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


  const parseGypsumSku = (skuRaw) => {
  const sku = String(skuRaw || "").toUpperCase().trim();
  // สมมติรหัสยิปซัมขึ้นต้น J และยาวอย่างน้อย 18 ตัว
  if (!sku.startsWith("Y") || sku.length < 18) {
    return {
      brand: null,
      group: null,
      subGroup: null,
      color: null,
      thickness: null,
      sizeCode: null,
    };
  }

  return {
    brand: sku.slice(1, 3),      // 2-3
    group: sku.slice(3, 5),      // 4-5
    subGroup: sku.slice(5, 7),   // 6-7
    color: sku.slice(7, 10),     // 8-10
    thickness: sku.slice(10, 12),// 11-12
    sizeCode: sku.slice(12, 18), // 13-18
  };
};

  const parseSealantSku = (skuRaw) => {
    const sku = String(skuRaw || "").toUpperCase().trim();
    if (!sku.startsWith("S") || sku.length < 10) {
      return {
        brand: null,
        group: null,
        subGroup: null,
        color: null,
      };
    }
    return {
      brand: sku.slice(1, 3),      // 2-3
      group: sku.slice(3, 5),      // 4-5
      subGroup: sku.slice(5, 8),   // 6-8
      color: sku.slice(8, 10),     // 9-10
    };
  };

  // ✅ ฟังก์ชัน parse SKU อลูมิเนียม – อยู่ก่อน useMemo เช่นกัน
  const parseAluminiumSku = (skuRaw) => {
    const sku = String(skuRaw || "").toUpperCase().trim();
    if (!sku.startsWith("A") || sku.length < 12) {
      return {
        brand: null,
        group: null,
        subGroup: null,
        color: null,
        thickness: null,
      };
    }
    return {
      brand: sku.slice(1, 3),      // 2–3
      group: sku.slice(3, 5),      // 4–5
      subGroup: sku.slice(5, 8),   // 6–8
      color: sku.slice(8, 10),     // 9–10
      thickness: sku.slice(10, 12) // 11–12
    };
  };

  const parseCLineSku = (skuRaw) => {
  const sku = String(skuRaw || "").toUpperCase().trim();
  if (!sku.startsWith("C") || sku.length < 12) {
    return {
      brand: null,
      group: null,
      subGroup: null,
      color: null,
      thickness: null,
    };
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
    return {
      brand: null,
      group: null,
      subGroup: null,
      color: null,
      character: null,
    };
  }
  return {
    brand: sku.slice(1, 4),   // 2–4
    group: sku.slice(4, 6),   // 5–6
    subGroup: sku.slice(6, 8),// 7–8
    color: sku.slice(8, 10),  // 9–10
    character: sku.slice(10, 11), // 11
  };
};



  // โหลดรายการสินค้าเมื่อเปิด modal
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

  // ✅ กรองรายการด้วย search + ฟิลเตอร์อลูมิเนียม
  const filteredItems = useMemo(() => {
  let base = items;

  if (category === "A") {
    base = base.filter((it) => {
      const sku = it.sku || it.SKU || "";
      const parsed = parseAluminiumSku(sku);

      if (aluFilter.brand && parsed.brand !== aluFilter.brand) return false;
      if (aluFilter.group && parsed.group !== aluFilter.group) return false;
      if (aluFilter.subGroup && parsed.subGroup !== aluFilter.subGroup) return false;
      if (aluFilter.color && parsed.color !== aluFilter.color) return false;
      if (aluFilter.thickness && parsed.thickness !== aluFilter.thickness) return false;

      return true;
    });
    } else if (category === "C") {
    base = base.filter((it) => {
      const sku = it.sku || it.SKU || "";
      const parsed = parseCLineSku(sku);

      if (clineFilter.brand && parsed.brand !== clineFilter.brand) return false;
      if (clineFilter.group && parsed.group !== clineFilter.group) return false;
      if (clineFilter.subGroup && parsed.subGroup !== clineFilter.subGroup) return false;
      if (clineFilter.color && parsed.color !== clineFilter.color) return false;
      if (clineFilter.thickness && parsed.thickness !== clineFilter.thickness) return false;

      return true;
    });
    } else if (category === "E") {
    base = base.filter((it) => {
      const sku = it.sku || it.SKU || "";
      const parsed = parseAccessoriesSku(sku);

      if (accFilter.brand && parsed.brand !== accFilter.brand) return false;
      if (accFilter.group && parsed.group !== accFilter.group) return false;
      if (accFilter.subGroup && parsed.subGroup !== accFilter.subGroup) return false;
      if (accFilter.color && parsed.color !== accFilter.color) return false;
      if (accFilter.character && parsed.character !== accFilter.character) return false;

      return true;
    });
    } else if (category === "S") {
    base = base.filter((it) => {
      const sku = it.sku || it.SKU || "";
      const parsed = parseSealantSku(sku);

      if (sealantFilter.brand && parsed.brand !== sealantFilter.brand) return false;
      if (sealantFilter.group && parsed.group !== sealantFilter.group) return false;
      if (sealantFilter.subGroup && parsed.subGroup !== sealantFilter.subGroup) return false;
      if (sealantFilter.color && parsed.color !== sealantFilter.color) return false;

      return true;
    });
    } else if (category === "Y") {   // ✅ ยิปซัม
    base = base.filter((it) => {
      const sku = it.sku || it.SKU || "";
      const parsed = parseGypsumSku(sku);

      if (gypsumFilter.brand && parsed.brand !== gypsumFilter.brand) return false;
      if (gypsumFilter.group && parsed.group !== gypsumFilter.group) return false;
      if (gypsumFilter.subGroup && parsed.subGroup !== gypsumFilter.subGroup) return false;
      if (gypsumFilter.color && parsed.color !== gypsumFilter.color) return false;
      if (gypsumFilter.thickness && parsed.thickness !== gypsumFilter.thickness) return false;

      return true;
    });
  }

  if (!searchTerm) return base;

  return base.filter((it) => {
    const name = String(it.name || it.Name || "").toLowerCase();
    const sku = String(it.sku || it.SKU || "").toLowerCase();
    const term = searchTerm.toLowerCase();
    return name.includes(term) || sku.includes(term);
  });
}, [items, searchTerm, category, aluFilter, clineFilter, accFilter, sealantFilter,gypsumFilter]);


  const handleAdd = (item, qty) => {
    if (!onConfirm) return;

    const normalizedItem = {
      ...item,
      unit:
        item.unit ||
        item["Base Unit Measure"] ||
        item.saleUnit ||
        item.uom ||
        "-",
      pkg_size:
        item.pkg_size ??
        item.pkgSize ??
        item["pkg_size"] ??
        1,
      product_weight:
        item.product_weight ??
        item.ProductWeight ??
        0,
      
      product_group: item.product_group ?? null,
      product_sub_group: item.product_sub_group ?? null,

  };


  onConfirm(normalizedItem, qty);
  onClose();
};


  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4 overflow-y-auto">

  {/* กล่องสีขาว */}
  <div className="w-full max-w-5xl bg-white rounded-xl shadow-xl p-8 animate-fadeIn">

    {/* Header */}
    <div className="flex justify-between items-center pb-3 border-b border-gray-200">
      <h2 className="text-xl font-bold text-gray-800">
        เลือกสินค้า: {category}
      </h2>
      <button
        onClick={onClose}
        className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
      >
        ✕
      </button>
    </div>

    {/* เนื้อหาแบ่งเป็น 4 คอลัมน์ */}
    <div className="mt-4 flex flex-col gap-4">

      
      <div className="space-y-3">
        <input
          type="search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={`ค้นหาในหมวด ${category}`}
          className="w-full rounded-lg border border-gray-300 p-3 shadow-sm"
        />

        {category === "A" && (
          <AluminiumPicker
            onSelect={(filters) => setAluFilter(filters || {})}
          />
        )}
        {category === "C" && (
          <CLinePicker onSelect={(filters) => setClineFilter(filters || {})} />
        )}
        {category === "E" && (
          <AccessoriesPicker onSelect={(filters) => setAccFilter(filters || {})} />
        )}
        {category === "S" && (
          <SealantPicker onSelect={(filters) => setSealantFilter(filters || {})} />
        )}
        {category === "Y" && (
          <GypsumPicker onSelect={(filters) => setGypsumFilter(filters || {})} />
        )}


      </div>

      {/* Items */}
      <div className="col-span-3">
        {loading && <Loader />}

        {!loading && filteredItems.length === 0 && (
          <p className="text-gray-500 text-center">ไม่พบสินค้า</p>
        )}

        <div className="max-h-[480px] overflow-y-auto pr-1">
          <div className="grid grid-cols-1 gap-4">
           {filteredItems.map((item, idx) => (
            <ItemCard
              key={`${item.sku || item.SKU || "item"}-${idx}`}
              item={item}
              onAdd={handleAdd}
            />
          ))}
          </div>
        </div>
      </div>

    </div>
  </div>

</div>

  );
}

export default ItemPickerModal;
