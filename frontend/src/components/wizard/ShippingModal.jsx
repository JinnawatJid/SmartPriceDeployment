// src/components/wizard/ShippingModal.jsx
import React, { useEffect, useRef, useState } from "react";
import api from "../../services/api"; // Import centralized api service

const TruckIcon = () => (
  <img src="/assets/fast-delivery.png" alt="Truck Icon" className="w-8 h-8 object-contain" />
);

export default function ShippingModal({ open = false, initial = {}, onClose, onConfirm }) {
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

      // Use centralized api service (automatically handles baseURL)
      const res = await api.post("/api/shipping/calculate", payload);

      onConfirm?.({
        ...res.data, // Access data property from axios response
        vehicleType,
        distanceKm: distanceKm,
        unloadHours,
        staffCount,
      });
      // ส่งผลลัพธ์ที่ได้กลับไปให้หน้า Step6
    } catch (err) {
      console.error("Error calculating shipping:", err);
      // More robust error message handling
      const msg = err.response?.data?.detail || err.message || "เกิดข้อผิดพลาดในการคำนวณค่าขนส่ง";
      alert(msg);
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
        className="relative z-10 w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl"
      >
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
            <TruckIcon />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">ข้อมูลรถ</h3>
            <p className="text-xs text-gray-500">กรอกรายละเอียดสำหรับการจัดส่ง</p>
          </div>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {/* ข้อมูลรถ */}
          <div>
            <label className="mb-1 block text-sm font-semibold text-gray-700">
              เลือกประเภทรถ
            </label>
            <select
              className="w-48 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
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

          {/* รายละเอียดการขนส่ง */}
          <div>
            <h4 className="mb-2 text-sm font-bold text-gray-800">รายละเอียดการขนส่ง</h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-semibold text-gray-700">
                  ระยะทาง (กม.)
                </label>
                <input
                  inputMode="decimal"
                  type="number"
                  min="0"
                  step="0.1"
                  placeholder="เช่น 12.5"
                  value={distanceKm}
                  onChange={(e) => setDistanceKm(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-gray-700">
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
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-gray-700">
                  จำนวนพนักงาน
                </label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  placeholder="เช่น 2"
                  value={staffCount}
                  onChange={(e) => setStaffCount(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-5 flex justify-between gap-3">
          <button
            onClick={onClose}
            className="w-32 rounded-lg bg-gray-100 px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-200"
          >
            ยกเลิก
          </button>
          <button
            onClick={handleConfirm}
            className="w-32 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-blue-700"
          >
            ยืนยัน
          </button>
        </div>
      </div>
    </div>
  );
}
