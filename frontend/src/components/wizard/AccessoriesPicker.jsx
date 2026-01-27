import React, { useEffect, useState } from "react";
import api from "../../services/api";
import CustomDropdown from "../common/CustomDropdown";

export default function AccessoriesPicker({ onSelect }) {
  const [brand, setBrand] = useState(null);
  const [group, setGroup] = useState(null);
  const [subGroup, setSubGroup] = useState(null);
  const [color, setColor] = useState(null);
  const [character, setCharacter] = useState(null);

  const [options, setOptions] = useState({
    brand: [],
    group: [],
    subGroup: [],
    color: [],
    character: [],
  });

  const fetchOptions = async () => {
    try {
      const res = await api.get("/api/items/categories/E/filter-options", {
        params: { brand, group, subGroup, color, character },
      });
      setOptions({
        brand: res.data.brand || [],
        group: res.data.group || [],
        subGroup: res.data.subGroup || [],
        color: res.data.color || [],
        character: res.data.character || [],
      });
    } catch (err) {
      console.error("Load accessories options failed:", err);
    }
  };

  useEffect(() => {
    fetchOptions();
  }, []);

  useEffect(() => {
    fetchOptions();
  }, [brand, group, subGroup, color, character]);

  const emitFilters = (next) => {
    onSelect && onSelect(next);
  };

  const handleBrandChange = (v) => {
    const next = { brand: v || null, group, subGroup, color, character };
    setBrand(next.brand);
    emitFilters(next);
  };

  const handleGroupChange = (v) => {
    const next = { brand, group: v || null, subGroup, color, character };
    setGroup(next.group);
    emitFilters(next);
  };

  const handleSubGroupChange = (v) => {
    const next = { brand, group, subGroup: v || null, color, character };
    setSubGroup(next.subGroup);
    emitFilters(next);
  };

  const handleColorChange = (v) => {
    const next = { brand, group, subGroup, color: v || null, character };
    setColor(next.color);
    emitFilters(next);
  };

  const handleCharacterChange = (v) => {
    const next = { brand, group, subGroup, color, character: v || null };
    setCharacter(next.character);
    emitFilters(next);
  };

  const handleClearAll = () => {
    setBrand(null);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
    setCharacter(null);
    emitFilters({ brand: null, group: null, subGroup: null, color: null, character: null });
  };

  return (
    <div className="flex items-end justify-between p-3 border rounded-xl bg-gray-50 mt-3">
      <CustomDropdown
        label="Brand"
        value={brand}
        options={options.brand}
        onChange={handleBrandChange}
      />

      <CustomDropdown
        label="Group"
        value={group}
        options={options.group}
        onChange={handleGroupChange}
        width={300}
      />

      <CustomDropdown
        label="SubGroup"
        value={subGroup}
        options={options.subGroup}
        onChange={handleSubGroupChange}
      />

      <CustomDropdown
        label="Color"
        value={color}
        options={options.color}
        onChange={handleColorChange}
      />

      <CustomDropdown
        label="Character"
        value={character}
        options={options.character}
        onChange={handleCharacterChange}
        width={100}
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
