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
    brands: [],
    groups: [],
    subGroups: [],
    colors: [],
  });

  const fetchOptions = async (filters = {}) => {
    try {
      const res = await api.get("/api/sealant/master", { params: filters });
      setOptions({
        brands: res.data.brands || [],
        groups: res.data.groups || [],
        subGroups: res.data.subGroups || [],
        colors: res.data.colors || [],
      });
    } catch (err) {
      console.error("Load sealant options failed:", err);
    }
  };

  // โหลดครั้งแรก
  useEffect(() => {
    fetchOptions({});
  }, []);

  // โหลดใหม่เมื่อ filter เปลี่ยน
  useEffect(() => {
    fetchOptions({ brand, group, subGroup, color });
  }, [brand, group, subGroup, color]);

  const emitFilters = (next) => {
    onSelect && onSelect(next);
  };

  const handleBrandChange = (v) => {
    const next = {
      brand: v || null,
      group: null,
      subGroup: null,
      color: null,
    };
    setBrand(next.brand);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
    emitFilters(next);
  };

  const handleGroupChange = (v) => {
    const next = {
      brand,
      group: v || null,
      subGroup: null,
      color: null,
    };
    setGroup(next.group);
    setSubGroup(null);
    setColor(null);
    emitFilters(next);
  };

  const handleSubGroupChange = (v) => {
    const next = {
      brand,
      group,
      subGroup: v || null,
      color: null,
    };
    setSubGroup(next.subGroup);
    setColor(null);
    emitFilters(next);
  };

  const handleColorChange = (v) => {
    const next = {
      brand,
      group,
      subGroup,
      color: v || null,
    };
    setColor(next.color);
    emitFilters(next);
  };

  return (
    <div className="flex justify-between p-3 border rounded-xl bg-gray-50 mt-3">

      <CustomDropdown
        label="Brand"
        value={brand}
        options={options.brands}
        onChange={handleBrandChange}
        width={200}
      />

      <CustomDropdown
        label="Group"
        value={group}
        options={options.groups}
        onChange={handleGroupChange}
        width={240}
      />

      <CustomDropdown
        label="SubGroup"
        value={subGroup}
        options={options.subGroups}
        onChange={handleSubGroupChange}
        width={240}
      />

      <CustomDropdown
        label="Color"
        value={color}
        options={options.colors}
        onChange={handleColorChange}
        width={200}   
      />

    </div>
  );
}
