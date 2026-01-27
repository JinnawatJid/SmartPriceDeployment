import React, { useEffect, useState } from "react";
import api from "../../services/api";
import CustomDropdown from "../common/CustomDropdown";

export default function CLineFilter({ onFilterChange }) {
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

  const fetchOptions = async () => {
    try {
      const res = await api.get("/api/items/categories/C/filter-options", {
        params: { brand, group, subGroup, color, thickness },
      });
      setOptions({
        brand: res.data.brand || [],
        group: res.data.group || [],
        subGroup: res.data.subGroup || [],
        color: res.data.color || [],
        thickness: res.data.thickness || [],
      });
    } catch (err) {
      console.error("Load cline filter options failed:", err);
    }
  };

  useEffect(() => {
    fetchOptions();
  }, []);

  useEffect(() => {
    fetchOptions();
  }, [brand, group, subGroup, color, thickness]);

  useEffect(() => {
    if (onFilterChange) {
      onFilterChange({ brand, group, subGroup, color, thickness });
    }
  }, [brand, group, subGroup, color, thickness]);

  const handleClearAll = () => {
    setBrand(null);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
    setThickness(null);
  };

  return (
    <div className="flex items-end justify-between gap-2 p-3 border rounded-xl bg-gray-50">
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
        width={240}
      />

      <CustomDropdown
        label="SubGroup"
        value={subGroup}
        options={options.subGroup}
        onChange={setSubGroup}
        width={360}
      />

      <CustomDropdown
        label="Color"
        value={color}
        options={options.color}
        onChange={setColor}
      />

      <CustomDropdown
        label="Thickness"
        value={thickness}
        options={options.thickness}
        onChange={setThickness}
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
