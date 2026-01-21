import React, { useEffect, useMemo, useState } from "react";
import api from "../../services/api.js";

const defaultFilters = {
  brand: "",
  type: "",
  subType: "",
  color: "",
  thickness: "",
};

export default function GlassSemiSizeModal({
  isOpen,
  onClose,
  branchCode,
  defaultBrand,
  defaultType,
  defaultSubType,
  defaultColor,
  defaultThickness,
}) {
  const [filters, setFilters] = useState(defaultFilters);
  const [sizes, setSizes] = useState([]);
  const [selectedSkus, setSelectedSkus] = useState([]);
  const [loading, setLoading] = useState(false); // โหลดรายการไซส์ semi
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // master สำหรับ dropdown (เหมือน GlassPicker แต่ย่อส่วน)
  const [master, setMaster] = useState({
    brands: [],
    types: [],
    subTypes: [],
    colors: [],
    thickness: [],
  });
  const [masterErr, setMasterErr] = useState("");

  // -------------------------
  // 1) ตั้งค่า default filters เมื่อ modal เปิด
  // -------------------------
  useEffect(() => {
    if (!isOpen) return;

    setFilters({
      brand: defaultBrand || "",
      type: defaultType || "",
      subType: defaultSubType || "",
      color: defaultColor || "",
      thickness: defaultThickness ? String(defaultThickness) : "",
    });
    setError("");
    setSizes([]);
    setSelectedSkus([]);
  }, [isOpen, defaultBrand, defaultType, defaultSubType, defaultColor, defaultThickness]);

  // -------------------------
  // 2) โหลด master options จาก /api/glass/master สำหรับ dropdown
  //    จะยิงทุกครั้งที่เปลี่ยน filter หลัก (เหมือน GlassPicker)
  // -------------------------
  useEffect(() => {
    if (!isOpen) return;

    const run = async () => {
      try {
        setMasterErr("");
        const params = {};
        if (filters.brand) params.brand = filters.brand;
        if (filters.type) params.type = filters.type;
        if (filters.subType) params.subType = filters.subType;
        if (filters.color) params.color = filters.color;
        if (filters.thickness) params.thickness = Number(filters.thickness) || undefined;

        const { data } = await api.get("/api/glass/master", { params });

        setMaster({
          brands: data.brands || [],
          types: data.types || [],
          subTypes: data.subTypes || [],
          colors: data.colors || [],
          thickness: data.thickness || [],
        });
      } catch (e) {
        console.error("Failed to load glass master for semi modal", e);
        setMasterErr("โหลดตัวเลือกกระจกไม่สำเร็จ");
      }
    };

    run();
  }, [isOpen, filters.brand, filters.type, filters.subType, filters.color, filters.thickness]);

  // -------------------------
  // 3) โหลดไซส์จาก backend ตาม filter (semi options)
  //    logic เดิมยังใช้เหมือนเดิม ไม่แตะต้อง
  // -------------------------
  useEffect(() => {
    if (!isOpen) return;
    if (!branchCode) {
      setError("กรุณาระบุรหัสสาขา (branchCode)");
      return;
    }

    // ต้องมีอย่างน้อย brand + type + thickness ก่อน ถึงจะยิงเรียก
    if (!filters.brand || !filters.type || !filters.thickness) {
      return;
    }

    const controller = new AbortController();
    const fetchSizes = async () => {
      try {
        setLoading(true);
        setError("");
        const params = {
          branchCode,
          brand: filters.brand || undefined,
          type: filters.type || undefined,
          subType: filters.subType || undefined,
          color: filters.color || undefined,
          thickness: filters.thickness ? Number(filters.thickness) : undefined,
        };
        const res = await api.get("/api/glass/semi/options", {
          params,
          signal: controller.signal,
        });
        const data = res.data || {};
        const list = Array.isArray(data.sizes) ? data.sizes : [];
        setSizes(list);

        // pre-select semi items
        const semiSkus = list.filter((s) => s.isSemi).map((s) => s.sku);
        setSelectedSkus(semiSkus);
      } catch (err) {
        if (controller.signal.aborted) return;
        console.error("Failed to load semi size options", err);
        setError("ไม่สามารถโหลดรายการไซส์ได้");
      } finally {
        setLoading(false);
      }
    };

    fetchSizes();
    return () => controller.abort();
  }, [
    isOpen,
    branchCode,
    filters.brand,
    filters.type,
    filters.subType,
    filters.color,
    filters.thickness,
  ]);

  // -------------------------
  // 4) handlers
  // -------------------------
  const handleToggleSku = (sku) => {
    setSelectedSkus((prev) => {
      if (prev.includes(sku)) {
        return prev.filter((x) => x !== sku);
      }
      return [...prev, sku];
    });
  };

  const handleClearSelected = () => {
    setSelectedSkus([]);
  };

  const handleSave = async () => {
    if (!branchCode) {
      setError("ไม่ทราบรหัสสาขา");
      return;
    }
    if (!selectedSkus.length) {
      const ok = window.confirm("ยังไม่ได้เลือกไซส์กึ่งมาตรฐานเลย ต้องการดำเนินการต่อหรือไม่?");
      if (!ok) return;
    }

    try {
      setSaving(true);
      setError("");
      await api.post("/api/glass/semi/save", {
        branchCode,
        skus: selectedSkus,
      });
      // ไม่ปิด modal อัตโนมัติ เผื่ออยากเลือกต่อ
    } catch (err) {
      console.error("Failed to save semi sizes", err);
      setError("บันทึกข้อมูลไม่สำเร็จ");
    } finally {
      setSaving(false);
    }
  };

  const visible = isOpen;

  const selectedSizeObjects = useMemo(() => {
    const map = new Map();
    sizes.forEach((s) => {
      map.set(s.sku, s);
    });
    return selectedSkus.map((sku) => map.get(sku)).filter(Boolean);
  }, [sizes, selectedSkus]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold">เลือกไซส์กึ่งมาตรฐาน</h2>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 rounded-full text-sm border border-gray-300 hover:bg-gray-100"
          >
            ปิด
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto flex">
          {/* Left: Filters */}
          <div className="w-72 border-r border-gray-200 p-4 space-y-3">
            {masterErr && <div className="mb-2 text-[11px] text-red-600">{masterErr}</div>}

            {/* Brand */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">ยี่ห้อ (Brand)</label>
              <select
                className="w-full border rounded-lg p-3 text-sm"
                value={filters.brand}
                onChange={(e) =>
                  setFilters((f) => ({
                    ...f,
                    brand: e.target.value || "",
                    type: "",
                    subType: "",
                    color: "",
                    thickness: "",
                  }))
                }
              >
                <option value="">-- เลือกยี่ห้อ --</option>
                {master.brands.map((b) => (
                  <option key={b.code} value={b.code}>
                    {b.name} ({b.nameEn})
                  </option>
                ))}
              </select>
            </div>

            {/* Type */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">ประเภท (Type)</label>
              <select
                className="w-full border rounded-lg p-3 text-sm"
                value={filters.type}
                onChange={(e) =>
                  setFilters((f) => ({
                    ...f,
                    type: e.target.value || "",
                    subType: "",
                    color: "",
                    thickness: "",
                  }))
                }
              >
                <option value="">-- เลือกประเภท --</option>
                {master.types.map((t) => (
                  <option key={t.code} value={t.code}>
                    {t.name} ({t.nameEn})
                  </option>
                ))}
              </select>
            </div>

            {/* SubType */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                กลุ่มย่อย (SubType)
              </label>
              <select
                className="w-full border rounded-lg p-3 text-sm"
                value={filters.subType}
                onChange={(e) =>
                  setFilters((f) => ({
                    ...f,
                    subType: e.target.value || "",
                  }))
                }
              >
                <option value="">-- เลือกกลุ่มย่อย --</option>
                {master.subTypes.map((st) => (
                  <option key={st.code} value={st.code}>
                    {st.name ? `${st.name} (${st.code})` : st.code}
                  </option>
                ))}
              </select>
            </div>

            {/* Color */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">สี (Color)</label>
              <select
                className="w-full border rounded-lg p-3 text-sm"
                value={filters.color}
                onChange={(e) =>
                  setFilters((f) => ({
                    ...f,
                    color: e.target.value || "",
                  }))
                }
              >
                <option value="">-- เลือกสี --</option>
                {master.colors.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Thickness */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                ความหนา (Thickness)
              </label>
              <select
                className="w-full border rounded-lg p-3 text-sm"
                value={filters.thickness}
                onChange={(e) =>
                  setFilters((f) => ({
                    ...f,
                    thickness: e.target.value || "",
                  }))
                }
              >
                <option value="">-- เลือกความหนา --</option>
                {master.thickness.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <p className="text-[11px] text-gray-500 pt-2">
              * ระบบจะโหลดไซส์กึ่งมาตรฐานอัตโนมัติเมื่อระบุ{" "}
              <strong>ยี่ห้อ + ประเภท + ความหนา</strong> ครบ
            </p>
          </div>

          {/* Right: Size grid + selected list */}
          <div className="flex-1 flex flex-col">
            {/* Size grid */}
            <div className="p-4 border-b border-gray-200">
              {loading ? (
                <div className="text-sm text-gray-500">กำลังโหลดรายการไซส์...</div>
              ) : sizes.length === 0 ? (
                <div className="text-sm text-gray-500">ยังไม่มีข้อมูลไซส์จากเงื่อนไขนี้</div>
              ) : (
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
                  {sizes.map((s) => {
                    const isSelected = selectedSkus.includes(s.sku);
                    return (
                      <button
                        key={s.sku}
                        type="button"
                        onClick={() => handleToggleSku(s.sku)}
                        className={[
                          "px-3 py-2 rounded-xl border text-sm text-center flex flex-col items-center justify-center",
                          "transition-colors duration-150",
                          isSelected
                            ? "bg-blue-600 text-white border-blue-600"
                            : "bg-white text-gray-800 border-gray-300 hover:bg-gray-50",
                        ].join(" ")}
                      >
                        <span className="font-medium">{s.label}</span>
                        <span className="mt-1 text-[11px] text-white/90">
                          {s.isStandard
                            ? "มาตรฐานบริษัท"
                            : s.isSemi
                              ? "กึ่งมาตรฐาน (ตั้งไว้แล้ว)"
                              : "\u00A0"}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-xs text-red-600 h-4">{error || "\u00A0"}</div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleClearSelected}
              className="px-4 py-2 rounded-xl border border-gray-300 text-sm hover:bg-gray-100"
            >
              ล้างทั้งหมด
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-60"
            >
              {saving ? "กำลังบันทึก..." : "ยืนยันการเลือก"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
