import React, { useEffect, useState } from "react";
import api from "../../services/api";

export default function AluminiumPicker({ onSelect }) {
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

  // ---- โหลด options จาก backend ----
  const fetchOptions = async (filters = {}) => {
    try {
      const res = await api.get("/api/aluminium/master", { params: filters });
      setOptions({
        brands: res.data.brands || [],
        groups: res.data.groups || [],
        subGroups: res.data.subGroups || [],
        colors: res.data.colors || [],
        thickness: res.data.thickness || [],
      });
    } catch (err) {
      console.error("Load aluminium options failed:", err);
    }
  };

  // โหลดครั้งแรก
  useEffect(() => {
    fetchOptions({});
  }, []);

  // โหลดใหม่ทุกครั้งที่ filter เปลี่ยน
  useEffect(() => {
    fetchOptions({
      brand,
      group,
      subGroup,
      color,
      thickness,
    });
  }, [brand, group, subGroup, color, thickness]);

  // helper ส่งค่ากลับ parent
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

  // ------------- UI Component -----------------
  const Dropdown = ({ label, value, onChange, items }) => (
    <div className="flex flex-col w-full">
      <label className="text-sm font-medium mb-1">{label}</label>
      <select
        value={value || ""}
        onChange={(e) => onChange(e.target.value || null)}
        className="w-[180px] border rounded-md p-2 bg-white"
      >
        <option value="">-- เลือก {label} --</option>
        {items.map((item) => (
          <option key={item.code || item.value} value={item.code || item.value}>
            {item.name || item.label}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="flex p-3 space-x-1  border rounded-xl bg-gray-50 mt-3">

      <Dropdown
        label="Brand"
        value={brand}
        onChange={handleBrandChange}
        items={options.brands}
      />

      <Dropdown
        label="Group"
        value={group}
        onChange={handleGroupChange}
        items={options.groups}
      />

      <Dropdown
        label="SubGroup"
        value={subGroup}
        onChange={handleSubGroupChange}
        items={options.subGroups}
      />

      <Dropdown
        label="Color"
        value={color}
        onChange={handleColorChange}
        items={options.colors}
      />

      <Dropdown
        label="Thickness"
        value={thickness}
        onChange={handleThicknessChange}
        items={options.thickness}
      />
    </div>
  );
}
