// src/components/wizard/CLinePicker.jsx
import React, { useEffect, useState } from "react";
import api from "../../services/api";
import CustomDropdown from "../common/CustomDropdown";

export default function CLinePicker({ onSelect }) {
  const [brand, setBrand] = useState(null);
  const [group, setGroup] = useState(null);
  const [subGroup, setSubGroup] = useState(null);
  const [color, setColor] = useState(null);
  const [thickness, setThickness] = useState(null);

  const [options, setOptions] = useState({
    brands: [],
    groups: [],
    subGroups: [],
    colors: [],
    thickness: [],
  });

  const fetchOptions = async (filters = {}) => {
    try {
      const res = await api.get("/api/cline/master", { params: filters });
      setOptions({
        brands: res.data.brands || [],
        groups: res.data.groups || [],
        subGroups: res.data.subGroups || [],
        colors: res.data.colors || [],
        thickness: res.data.thickness || [],
      });
    } catch (err) {
      console.error("Load C-Line options failed:", err);
    }
  };

  // โหลดครั้งแรก
  useEffect(() => {
    fetchOptions({});
  }, []);

  // โหลด options ใหม่เมื่อ filter เปลี่ยน
  useEffect(() => {
    fetchOptions({ brand, group, subGroup, color, thickness });
  }, [brand, group, subGroup, color, thickness]);

  const emitFilters = (next) => {
    if (onSelect) onSelect(next);
  };

  const handleBrandChange = (v) => {
    const next = {
      brand: v || null,
      group: null,
      subGroup: null,
      color: null,
      thickness: null,
    };
    setBrand(next.brand);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
    setThickness(null);
    emitFilters(next);
  };

  const handleGroupChange = (v) => {
    const next = {
      brand,
      group: v || null,
      subGroup: null,
      color: null,
      thickness: null,
    };
    setGroup(next.group);
    setSubGroup(null);
    setColor(null);
    setThickness(null);
    emitFilters(next);
  };

  const handleSubGroupChange = (v) => {
    const next = {
      brand,
      group,
      subGroup: v || null,
      color: null,
      thickness: null,
    };
    setSubGroup(next.subGroup);
    setColor(null);
    setThickness(null);
    emitFilters(next);
  };

  const handleColorChange = (v) => {
    const next = {
      brand,
      group,
      subGroup,
      color: v || null,
      thickness: null,
    };
    setColor(next.color);
    setThickness(null);
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

  return (
    <div className="flex items-end justify-between p-3 border rounded-xl bg-gray-50 mt-3">
      <CustomDropdown
        label="Brand"
        value={brand}
        options={options.brands}
        onChange={handleBrandChange}
      />

      <CustomDropdown
        label="Group"
        value={group}
        options={options.groups}
        onChange={handleGroupChange}
      />

      <CustomDropdown
        label="SubGroup"
        value={subGroup}
        options={options.subGroups}
        onChange={handleSubGroupChange}
      />

      <CustomDropdown
        label="Color"
        value={color}
        options={options.colors}
        onChange={handleColorChange}
      />

      <CustomDropdown
        label="Thickness"
        value={thickness}
        options={options.thickness}
        onChange={handleThicknessChange}
      />
    </div>
  );
}
