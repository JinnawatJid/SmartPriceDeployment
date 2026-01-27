import React, { useEffect, useState } from "react";
import api from "../../services/api";
import CustomDropdown from "../common/CustomDropdown";

export default function SealantFilter({ onFilterChange }) {
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
      console.error("Load sealant filter options failed:", err);
    }
  };

  useEffect(() => {
    fetchOptions();
  }, []);

  useEffect(() => {
    fetchOptions();
  }, [brand, group, subGroup, color]);

  useEffect(() => {
    if (onFilterChange) {
      onFilterChange({ brand, group, subGroup, color });
    }
  }, [brand, group, subGroup, color]);

  const handleClearAll = () => {
    setBrand(null);
    setGroup(null);
    setSubGroup(null);
    setColor(null);
  };

  return (
    <div className="flex justify-between p-3 border rounded-xl bg-gray-50">
      <CustomDropdown
        label="Brand"
        value={brand}
        options={options.brand}
        onChange={setBrand}
        width={200}
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
        width={240}
      />

      <CustomDropdown
        label="Color"
        value={color}
        options={options.color}
        onChange={setColor}
        width={200}
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
