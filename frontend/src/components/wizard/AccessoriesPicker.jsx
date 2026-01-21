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
        label="Character"
        value={character}
        options={options.characters}
        onChange={handleCharacterChange}
      />
    </div>
  );
}
