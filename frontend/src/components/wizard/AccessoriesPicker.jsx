import React, { useEffect, useState } from "react";
import api from "../../services/api";

export default function AccessoriesPicker({ onSelect }) {
  const [brand, setBrand] = useState(null);
  const [group, setGroup] = useState(null);
  const [subGroup, setSubGroup] = useState(null);
  const [color, setColor] = useState(null);
  const [character, setCharacter] = useState(null);

  const [options, setOptions] = useState({
    brands: [],
    groups: [],
    subGroups: [],
    colors: [],
    characters: [],
  });

  const fetchOptions = async (filters = {}) => {
    try {
      const res = await api.get("/api/accessories/master", { params: filters });
      setOptions({
        brands: res.data.brands || [],
        groups: res.data.groups || [],
        subGroups: res.data.subGroups || [],
        colors: res.data.colors || [],
        characters: res.data.characters || [],
      });
    } catch (err) {
      console.error("Load accessories options failed:", err);
    }
  };

  // โหลดครั้งแรก
  useEffect(() => {
    fetchOptions({});
  }, []);

  // โหลดใหม่เมื่อ filter เปลี่ยน
  useEffect(() => {
    fetchOptions({ brand, group, subGroup, color, character });
  }, [brand, group, subGroup, color, character]);

  const emitFilters = (next) => {
    onSelect && onSelect(next);
  };

  const handleBrandChange = (v) => {
    const next = {
      brand: v || null,
      group: null,
      subGroup: null,
      color: null,
      character: null,
    };
    setBrand(next.brand);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
    setCharacter(null);
    emitFilters(next);
  };

  const handleGroupChange = (v) => {
    const next = {
      brand,
      group: v || null,
      subGroup: null,
      color: null,
      character: null,
    };
    setGroup(next.group);
    setSubGroup(null);
    setColor(null);
    setCharacter(null);
    emitFilters(next);
  };

  const handleSubGroupChange = (v) => {
    const next = {
      brand,
      group,
      subGroup: v || null,
      color: null,
      character: null,
    };
    setSubGroup(next.subGroup);
    setColor(null);
    setCharacter(null);
    emitFilters(next);
  };

  const handleColorChange = (v) => {
    const next = {
      brand,
      group,
      subGroup,
      color: v || null,
      character: null,
    };
    setColor(next.color);
    setCharacter(null);
    emitFilters(next);
  };

  const handleCharacterChange = (v) => {
    const next = {
      brand,
      group,
      subGroup,
      color,
      character: v || null,
    };
    setCharacter(next.character);
    emitFilters(next);
  };

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
    <div className="flex p-3 space-x-1  border rounded-xl bg-gray-50 mt-33">
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
        label="Character"
        value={character}
        onChange={handleCharacterChange}
        items={options.characters}
      />
    </div>
  );
}
