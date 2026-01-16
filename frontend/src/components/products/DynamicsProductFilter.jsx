import React from "react";
import AluminiumPicker from "../wizard/AluminiumPicker.jsx";
import AccessoriesPicker from "../wizard/AccessoriesPicker.jsx";
import CLinePicker from "../wizard/CLinePicker.jsx";
import SealantPicker from "../wizard/SealantPicker.jsx";
import GypsumPicker from "../wizard/GypsumPicker.jsx";
import GlassPickerModal from "../wizard/GlassPickerModal.jsx";
import { useState } from "react";


export default function DynamicProductFilter({ category, onFilterChange }) {
  const [openGlass, setOpenGlass] = useState(false);
  if (typeof onFilterChange !== "function") return null;
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
        <>
          <button
            className="px-4 py-2 border rounded bg-cyan-50 text-cyan-700 font-semibold"
           
          >
            เลือกสินค้ากระจก
          </button>

          
        </>
      );

    default:
      return null;
  }
}
