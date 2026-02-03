// src/components/wizard/SealantPicker.jsx
import React, { useEffect, useState } from "react";
import api from "../../services/api";
import CustomDropdown from "../common/CustomDropdown";

export default function SealantPicker({ onSelect }) {
  const [brand, setBrand] = useState(null);
  const [group, setGroup] = useState(null);
  const [subGroup, setSubGroup] = useState(null);
  const [color, setColor] = useState(null);

  const [options, setOptions] = useState({
    brand: [],
    group: [],
    subGroup: [],
    color: [],
  });

  const fetchOptions = async () => {
    try {
      const res = await api.get("/api/items/categories/S/filter-options", {
        params: { brand, group, subGroup, color },
      });
      setOptions({
        brand: res.data.brand || [],
        group: res.data.group || [],
        subGroup: res.data.subGroup || [],
        color: res.data.color || [],
      });
    } catch (err) {
      console.error("Load sealant options failed:", err);
    }
  };

  useEffect(() => {
    fetchOptions();
  }, []);

  useEffect(() => {
    fetchOptions();
  }, [brand, group, subGroup, color]);

  const emitFilters = (next) => {
    onSelect && onSelect(next);
  };

  const handleBrandChange = (v) => {
    const next = { brand: v || null, group, subGroup, color };
    setBrand(next.brand);
    emitFilters(next);
  };

  const handleGroupChange = (v) => {
    const next = { brand, group: v || null, subGroup, color };
    setGroup(next.group);
    emitFilters(next);
  };

  const handleSubGroupChange = (v) => {
    const next = { brand, group, subGroup: v || null, color };
    setSubGroup(next.subGroup);
    emitFilters(next);
  };

  const handleColorChange = (v) => {
    const next = { brand, group, subGroup, color: v || null };
    setColor(next.color);
    emitFilters(next);
  };

  const handleClearAll = () => {
    setBrand(null);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
    emitFilters({ brand: null, group: null, subGroup: null, color: null });
  };

  return (
    <div className="flex justify-between p-3 border rounded-xl bg-gray-50 mt-3">
      <CustomDropdown
        label="Brand"
        value={brand}
        options={options.brand}
        onChange={handleBrandChange}
        width={200}
      />

      <CustomDropdown
        label="Group"
        value={group}
        options={options.group}
        onChange={handleGroupChange}
        width={240}
      />

      <CustomDropdown
        label="SubGroup"
        value={subGroup}
        options={options.subGroup}
        onChange={handleSubGroupChange}
        width={280}
      />

      <CustomDropdown
        label="Color"
        value={color}
        options={options.color}
        onChange={handleColorChange}
        width={200}
      />

      <button
        onClick={handleClearAll}
        className="px-4 py-2  w-[100px] h-[40px] mt-6 text-sm border rounded-lg hover:bg-gray-100"
      >
        Clear All
      </button>
    </div>
  );
}
