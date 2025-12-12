// src/components/wizard/ShippingModal.jsx
import React, { useEffect, useRef, useState } from "react";

export default function ShippingModal({
  open = false,
  initial = {},
  onClose,
  onConfirm,
}) {
  const dialogRef = useRef(null);
  const [vehicleType, setVehicleType] = useState(initial.vehicleType || "");
  const [distanceKm, setDistanceKm] = useState(initial.distanceKm ?? "");
  const [unloadHours, setUnloadHours] = useState(initial.unloadHours ?? "");
  const [staffCount, setStaffCount] = useState(initial.staffCount ?? "");
  const [profit, setProfit] = useState(initial.profit ?? ""); // เพิ่มกำไรของบิล

  useEffect(() => {
    if (open) {
      setVehicleType(initial.vehicleType || "");
      setDistanceKm(initial.distanceKm ?? "");
      setUnloadHours(initial.unloadHours ?? "");
      setStaffCount(initial.staffCount ?? "");
      setProfit(initial.profit ?? "");
      setTimeout(() => dialogRef.current?.focus(), 0);
    }
  }, [open]);

  if (!open) return null;

  const handleConfirm = async () => {
    const d = Number(distanceKm);
    if (Number.isNaN(d) || d <= 0) {
      alert("กรุณาระบุระยะทาง (กม.) มากกว่า 0");
      return;
    }

    try {
      const payload = {
        vehicle_type: vehicleType,
        distance_km: Number(distanceKm),
        unload_hours: Number(unloadHours || 0),
        staff_count: Number(staffCount || 0),
        profit: Number(profit || 0),
      };

      const res = await fetch("http://127.0.0.1:4000/api/shipping/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const msg = await res.text();
        throw new Error(`HTTP ${res.status}: ${msg}`);
        }
    const data = await res.json();
    onConfirm?.({
      ...data,
      vehicleType,
      distanceKm: distanceKm,
      unloadHours,
      staffCount,
    });
 // ส่งผลลัพธ์ที่ได้กลับไปให้หน้า Step6
    } catch (err) {
      console.error("Error calculating shipping:", err);
      alert("เกิดข้อผิดพลาดในการคำนวณค่าขนส่ง");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      {/* modal */}
      <div
        role="dialog"
        aria-modal="true"
        ref={dialogRef}
        tabIndex={-1}
        className="relative z-10 w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl"
      >
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
            <svg
              className="h-7 w-7"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 7.5h10.5v7.5H6a3 3 0 00-3 3m9.75-10.5h4.5l3 3v7.5h-2.25m-12 0A2.25 2.25 0 116 21a2.25 2.25 0 01-.75-4.371m10.5 0A2.25 2.25 0 1118 21a2.25 2.25 0 01-.75-4.371"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">ข้อมูลรถ</h3>
            <p className="text-sm text-gray-500">กรอกรายละเอียดสำหรับการจัดส่ง</p>
          </div>
        </div>

        {/* Form */}
        <div className="space-y-6">
          {/* ข้อมูลรถ */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-semibold text-gray-700">
                เลือกประเภทรถ
              </label>
              <select
                className="w-full rounded-lg border border-gray-300 bg-white p-3 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={vehicleType}
                onChange={(e) => setVehicleType(e.target.value)}
              >
                <option value="">— เลือกประเภทรถ —</option>
                <option value="PICKUP">กระบะ Pickup</option>
                <option value="4 ล้อใหญ่">4 ล้อใหญ่</option>
                <option value="6 ล้อจิ๋ว">6 ล้อจิ๋ว</option>
                <option value="6 ล้อเล็ก">6 ล้อเล็ก</option>
                <option value="6 ล้อใหญ่">6 ล้อใหญ่</option>
                <option value="10 ล้อ">10 ล้อ</option>
              </select>
            </div>
            
          </div>

          {/* รายละเอียดการขนส่ง */}
          <div>
            <h4 className="mb-2 text-base font-bold text-gray-800">รายละเอียดการขนส่ง</h4>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-semibold text-gray-700">
                  ระยะทาง (กิโลเมตร)
                </label>
                <input
                  inputMode="decimal"
                  type="number"
                  min="0"
                  step="0.1"
                  placeholder="เช่น 12.5"
                  value={distanceKm}
                  onChange={(e) => setDistanceKm(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white p-3 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-semibold text-gray-700">
                  ชั่วโมงลงสินค้า
                </label>
                <input
                  inputMode="decimal"
                  type="number"
                  min="0"
                  step="0.5"
                  placeholder="เช่น 1.5"
                  value={unloadHours}
                  onChange={(e) => setUnloadHours(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white p-3 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-semibold text-gray-700">
                  จำนวนพนักงาน
                </label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  placeholder="เช่น 2"
                  value={staffCount}
                  onChange={(e) => setStaffCount(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white p-3 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-between gap-3">
          <button
            onClick={onClose}
            className="w-40 rounded-lg bg-gray-100 px-5 py-3 font-semibold text-gray-700 shadow-sm hover:bg-gray-200"
          >
            ยกเลิก
          </button>
          <button
            onClick={handleConfirm}
            className="w-40 rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white shadow-md hover:bg-blue-700"
          >
            ยืนยัน
          </button>
        </div>
      </div>
    </div>
  );
}
