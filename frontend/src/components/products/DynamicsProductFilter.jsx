import React from "react";
import AluminiumFilter from "./AluminiumFilter.jsx";
import AccessoriesFilter from "./AccessoriesFilter.jsx";
import CLineFilter from "./CLineFilter.jsx";
import SealantFilter from "./SealantFilter.jsx";
import GypsumFilter from "./GypsumFilter.jsx";
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
      return <AluminiumFilter onFilterChange={handleChange} />;

    case "E":
      return <AccessoriesFilter onFilterChange={handleChange} />;

    case "C":
      return <CLineFilter onFilterChange={handleChange} />;

    case "S":
      return <SealantFilter onFilterChange={handleChange} />;

    case "Y":
      return <GypsumFilter onFilterChange={handleChange} />;

    case "G":
      return (
        <>
          <button className="px-4 py-2 border rounded bg-cyan-50 text-cyan-700 font-semibold">
            เลือกสินค้ากระจก
          </button>
        </>
      );

    default:
      return null;
  }
}
