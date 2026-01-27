import React, { useEffect, useState } from "react";
import api from "../../services/api";
import CustomDropdown from "../common/CustomDropdown";

export default function AccessoriesFilter({ onFilterChange }) {
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
      console.error("Load accessories filter options failed:", err);
    }
  };

  useEffect(() => {
    fetchOptions();
  }, []);

  useEffect(() => {
    fetchOptions();
  }, [brand, group, subGroup, color, character]);

  useEffect(() => {
    if (onFilterChange) {
      onFilterChange({ brand, group, subGroup, color, character });
    }
  }, [brand, group, subGroup, color, character]);

  const handleClearAll = () => {
    setBrand(null);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
    setCharacter(null);
  };

  return (
    <div className="flex items-end justify-between p-3 border rounded-xl bg-gray-50">
      <CustomDropdown
        label="Brand"
        value={brand}
        options={options.brand}
        onChange={setBrand}
      />

      <CustomDropdown
        label="Group"
        value={group}
        options={options.group}
        onChange={setGroup}
      />

      <CustomDropdown
        label="SubGroup"
        value={subGroup}
        options={options.subGroup}
        onChange={setSubGroup}
      />

      <CustomDropdown
        label="Color"
        value={color}
        options={options.color}
        onChange={setColor}
      />

      <CustomDropdown
        label="Character"
        value={character}
        options={options.character}
        onChange={setCharacter}
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
