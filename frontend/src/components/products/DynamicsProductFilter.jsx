import React from "react";
import AluminiumPicker from "../wizard/AluminiumPicker.jsx";
import AccessoriesPicker from "../wizard/AccessoriesPicker.jsx";
import CLinePicker from "../wizard/CLinePicker.jsx";
import SealantPicker from "../wizard/SealantPicker.jsx";
import GypsumPicker from "../wizard/GypsumPicker.jsx";

export default function DynamicProductFilter({ category, onFilterChange }) {
  if (!category) return null;

  const handleChange = (filters) => {
    onFilterChange(filters);
  };

  switch (category) {
    case "A":
      return <AluminiumPicker onSelect={handleChange} />;

    case "E":
      return <AccessoriesPicker onSelect={handleChange} />;

    case "C":
      return <CLinePicker onSelect={handleChange} />;

    case "S":
      return <SealantPicker onSelect={handleChange} />;

    case "Y":
      return <GypsumPicker onSelect={handleChange} />;

    case "G":
      return (
        <div className="p-4 border rounded bg-white">
          <p className="font-semibold mb-2">ฟิลเตอร์กระจก</p>
        
        </div>
      );

    default:
      return null;
  }
}
