import React, { useEffect, useState } from "react";
import api from "../../services/api";
import CustomDropdown from "../common/CustomDropdown";

export default function AluminiumPicker({ onSelect }) {
  const [brand, setBrand] = useState(null);
  const [group, setGroup] = useState(null);
  const [subGroup, setSubGroup] = useState(null);
  const [color, setColor] = useState(null);
  const [thickness, setThickness] = useState(null);

  const [options, setOptions] = useState({
    brand: [],
    group: [],
    subGroup: [],
    color: [],
    thickness: [],
  });

  // ---- โหลด options จาก backend (cascading) ----
  const fetchOptions = async () => {
    try {
      const res = await api.get("/api/items/categories/A/filter-options", {
        params: {
          brand,
          group,
          subGroup,
          color,
          thickness,
        },
      });

      setOptions({
        brand: res.data.brand || [],
        group: res.data.group || [],
        subGroup: res.data.subGroup || [],
        color: res.data.color || [],
        thickness: res.data.thickness || [],
      });
    } catch (err) {
      console.error("Load aluminium options failed:", err);
    }
  };

  // โหลดครั้งแรก
  useEffect(() => {
    fetchOptions();
  }, []);

  // โหลดใหม่ทุกครั้งที่ filter เปลี่ยน
  useEffect(() => {
    fetchOptions();
  }, [brand, group, subGroup, color, thickness]);

  // helper ส่งค่ากลับ parent
  const emitFilters = (next) => {
    if (onSelect) onSelect(next);
  };

  const handleBrandChange = (v) => {
    const next = {
      brand: v || null,
      group,
      subGroup,
      color,
      thickness,
    };
    setBrand(next.brand);
    emitFilters(next);
  };

  const handleGroupChange = (v) => {
    const next = {
      brand,
      group: v || null,
      subGroup,
      color,
      thickness,
    };
    setGroup(next.group);
    emitFilters(next);
  };

  const handleSubGroupChange = (v) => {
    const next = {
      brand,
      group,
      subGroup: v || null,
      color,
      thickness,
    };
    setSubGroup(next.subGroup);
    emitFilters(next);
  };

  const handleColorChange = (v) => {
    const next = {
      brand,
      group,
      subGroup,
      color: v || null,
      thickness,
    };
    setColor(next.color);
    emitFilters(next);
  };

  const handleThicknessChange = (v) => {
    const next = {
      brand,
      group,
      subGroup,
      color,
      thickness: v || null,
    };
    setThickness(next.thickness);
    emitFilters(next);
  };

  // ⭐ ปุ่ม Clear All
  const handleClearAll = () => {
    setBrand(null);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
    setThickness(null);
    emitFilters({
      brand: null,
      group: null,
      subGroup: null,
      color: null,
      thickness: null,
    });
  };

  return (
    <div className="flex items-end justify-between p-3 border rounded-xl bg-gray-50 mt-3">
      <CustomDropdown
        label="Brand"
        value={brand}
        options={options.brand}
        onChange={(v) => handleBrandChange(v)}
        width={200}
      />

      
      <CustomDropdown
        label="Color"
        value={color}
        options={options.color}
        onChange={(v) => handleColorChange(v)}
        width={170}
      />

      <CustomDropdown
        label="Thickness"
        value={thickness}
        options={options.thickness}
        onChange={(v) => handleThicknessChange(v)}
      />


      <CustomDropdown
        label="Group"
        value={group}
        options={options.group}
        onChange={(v) => handleGroupChange(v)}
        width={200}
      />

      <CustomDropdown
        label="SubGroup"
        value={subGroup}
        options={options.subGroup}
        onChange={(v) => handleSubGroupChange(v)}
      />

      <button
        onClick={handleClearAll}
        className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-100"
      >
        Clear All
      </button>
    </div>
  );
}
