import React, { useEffect, useState, useMemo } from "react";
import api from "../services/api";

export default function CheckProduct() {
  const [items, setItems] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [query, setQuery] = useState("");

  // Filter state
  const [filter, setFilter] = useState({
    productType: "",
    brand: "",
    category: "",
    subCategory: "",
    color: "",
    thickness: "",
    size: "",
  });

  // โหลดข้อมูลทั้งหมด
  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get("/api/items/");
        setItems(res.data || []);
        setFiltered(res.data || []);
      } catch (err) {
        console.error("Error loading items:", err);
      }
    };
    load();
  }, []);

  // Filter Logic
  useEffect(() => {
    let result = [...items];

    // Search keyword
    if (query.trim() !== "") {
      result = result.filter(
        (it) =>
          String(it.sku).toLowerCase().includes(query.toLowerCase()) ||
          String(it.name).toLowerCase().includes(query.toLowerCase())
      );
    }

    // Filter each field
    Object.keys(filter).forEach((key) => {
      if (filter[key]) {
        result = result.filter((it) =>
          String(it[key] || "")
            .toLowerCase()
            .includes(filter[key].toLowerCase())
        );
      }
    });

    setFiltered(result);
  }, [query, filter, items]);

  const onFilterChange = (key, value) => {
    setFilter((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="p-8 bg-gray-100 min-h-screen">
      <h1 className="text-3xl font-bold mb-6">ตรวจสอบรายละเอียดสินค้า</h1>

      {/* Search */}
      <div className="flex mb-6">
        <input
          type="text"
          className="flex-1 px-4 py-3 rounded-lg border shadow-sm"
          placeholder="ค้นหาสินค้า... (ชื่อ, ยี่ห้อ, กลุ่ม)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {/* Action Buttons */}
      <div className="flex gap-6 mb-8">
        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold">
          เลือกไซส์กระจกกึ่งมาตรฐาน
        </button>
        <button className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 rounded-xl font-semibold">
          น้ำหนักสินค้าอลูมิเนียม
        </button>
      </div>

      {/* Filter + Table */}
      <div className="grid grid-cols-5 gap-6">
        {/* Left Filter Panel */}
        <div className="col-span-1 bg-white rounded-xl shadow p-6">
          <h3 className="text-xl font-semibold mb-4">Filter</h3>

          {[
            ["productType", "เลือกสินค้าทั้งหมด"],
            ["brand", "ยี่ห้อ"],
            ["category", "กลุ่มสินค้า"],
            ["subCategory", "กลุ่มย่อย"],
            ["color", "สี"],
            ["thickness", "ความหนา"],
            ["size", "ขนาด"],
          ].map(([key, label]) => (
            <div key={key} className="mb-4">
              <label className="text-sm text-gray-700">{label}</label>
              <input
                className="w-full px-3 py-2 border rounded-lg mt-1"
                value={filter[key]}
                onChange={(e) => onFilterChange(key, e.target.value)}
                placeholder="ทั้งหมด"
              />
            </div>
          ))}
        </div>

        {/* Product Table */}
        <div className="col-span-4">
          <div className="bg-white rounded-xl shadow">
            <table className="min-w-full rounded-xl overflow-hidden">
              <thead className="bg-red-600 text-white text-left">
                <tr>
                  <th className="px-4 py-3">รหัสสินค้า</th>
                  <th className="px-4 py-3">ชื่อสินค้า</th>
                  <th className="px-4 py-3">จำนวน</th>
                  <th className="px-4 py-3">หน่วย</th>
                  <th className="px-4 py-3">ประเภทสินค้า</th>
                </tr>
              </thead>

              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan="5" className="text-center py-6 text-gray-500">
                      ไม่พบข้อมูลสินค้า
                    </td>
                  </tr>
                )}

                {filtered.map((item, i) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3">{item.sku}</td>
                    <td className="px-4 py-3">{item.name}</td>
                    <td className="px-4 py-3">{item.unit || 0}</td>
                    <td className="px-4 py-3">{item.unit2 || "-"}</td>
                    <td className="px-4 py-3">{item.category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
