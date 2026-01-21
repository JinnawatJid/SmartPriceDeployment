import React, { useEffect, useRef, useState, useId } from "react";

export default function CustomDropdown({
  label,
  value,
  options = [],
  onChange,
  placeholder = "เลือกรายการ",
  clearLabel = "-- ค่าเริ่มต้น --", // ⭐ เพิ่ม
  width = 160,
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // cache options ชุดแรก
  const cachedOptionsRef = useRef([]);

  useEffect(() => {
    if (options && options.length > 1) {
      cachedOptionsRef.current = options;
    }
  }, [options]);

  const displayOptions = cachedOptionsRef.current.length > 0 ? cachedOptionsRef.current : options;

  const selected = value == null ? null : displayOptions.find((o) => o.code === value);

  const dropdownId = useId();

  useEffect(() => {
    const onOtherDropdownOpen = (e) => {
      if (e.detail !== dropdownId) {
        setOpen(false);
      }
    };

    window.addEventListener("dropdown-open", onOtherDropdownOpen);
    return () => window.removeEventListener("dropdown-open", onOtherDropdownOpen);
  }, [dropdownId]);

  return (
    <div ref={ref} className="relative text-sm" style={{ width }}>
      {label && <label className="block text-lg font-bold mb-1">{label}</label>}

      {/* Trigger */}
      <button
        type="button"
        onClick={() => {
          if (!open) {
            window.dispatchEvent(
              new CustomEvent("dropdown-open", {
                detail: dropdownId,
              })
            );
          }
          setOpen((o) => !o);
        }}
        className="
            w-full
            h-8
            px-2
            flex items-center justify-between
            border rounded
            bg-white
            hover:bg-gray-50
            focus:outline-none
            focus:ring-1 focus:ring-blue-500
        "
      >
        <span className={selected ? "text-gray-800" : "text-gray-400"}>
          {selected ? selected.name : placeholder}
        </span>
        <span className="text-gray-400 text-xs">▾</span>
      </button>

      {/* Options */}
      {open && (
        <div
          className="
            absolute z-50 mt-1
            w-full
            max-h-56
            overflow-y-auto
            border rounded
            bg-white
            shadow-lg
          "
        >
          {/* ⭐ คืนค่าเริ่มต้น */}
          <div
            onMouseDown={(e) => {
              e.stopPropagation();
              onChange(null); // ⭐ reset
              setOpen(false);
            }}
            className={`
              px-2
              h-7
              flex items-center
              cursor-pointer
              text-sm
              ${value == null ? "bg-blue-600 text-white" : "hover:bg-blue-50"}
            `}
          >
            {clearLabel}
          </div>

          {displayOptions.map((opt) => {
            const active = opt.code === value;
            return (
              <div
                key={opt.code}
                onMouseDown={(e) => {
                  e.stopPropagation();
                  onChange(opt.code);
                  setOpen(false);
                }}
                className={`
                  px-2
                  h-7
                  flex items-center
                  cursor-pointer
                  text-sm
                  ${active ? "bg-blue-600 text-white" : "hover:bg-blue-50"}
                `}
              >
                {opt.name}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
