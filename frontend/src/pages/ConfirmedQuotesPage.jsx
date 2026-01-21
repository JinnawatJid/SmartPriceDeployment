import React, { useState, useEffect } from "react";
import api from "../services/api";
import { useNavigate } from "react-router-dom";

export default function ConfirmedQuotesPage() {
  const navigate = useNavigate();
  const [quotes, setQuotes] = useState([]);
  const [search, setSearch] = useState("");
  const [filterDate, setFilterDate] = useState("");
  const [filterMonth, setFilterMonth] = useState("");

  const fetchData = async () => {
    try {
      const res = await api.get("/api/quotation?status=complete");
      setQuotes(res.data || []);
    } catch (err) {
      console.error("Error loading confirmed quotations:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fmtDate = (d) =>
    new Date(d).toLocaleDateString("th-TH", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });

  const filtered = quotes.filter((q) => {
    const matchSearch =
      q.number?.toLowerCase().includes(search.toLowerCase()) ||
      q.customer?.name?.toLowerCase().includes(search.toLowerCase()) ||
      q.customer?.phone?.includes(search);

    const matchDate = filterDate ? q.createdAt?.slice(0, 10) === filterDate : true;

    const matchMonth = filterMonth ? q.createdAt?.slice(0, 7) === filterMonth : true;

    return matchSearch && matchDate && matchMonth;
  });

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">ใบเสนอราคาที่ยืนยันแล้ว</h1>

      {/* ฟิลเตอร์ */}
      <div className="bg-white p-5 rounded-xl shadow-md mb-6">
        <div className="grid grid-cols-3 gap-4">
          {/* ค้นหา */}
          <div>
            <label className="text-gray-700 font-medium">ค้นหา</label>
            <input
              className="mt-1 w-full rounded-lg border px-4 py-2"
              placeholder="เลขที่ใบเสนอราคา / ชื่อลูกค้า / เบอร์โทร"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {/* ฟิลเตอร์ตามวันที่ */}
          <div>
            <label className="text-gray-700 font-medium">ค้นหาตามวันที่ยืนยัน</label>
            <input
              type="date"
              className="mt-1 w-full rounded-lg border px-4 py-2"
              value={filterDate}
              onChange={(e) => {
                setFilterDate(e.target.value);
                setFilterMonth(""); // clear month filter
              }}
            />
          </div>

          {/* ฟิลเตอร์ตามเดือน */}
          <div>
            <label className="text-gray-700 font-medium">ค้นหาตามเดือน</label>
            <input
              type="month"
              className="mt-1 w-full rounded-lg border px-4 py-2"
              value={filterMonth}
              onChange={(e) => {
                setFilterMonth(e.target.value);
                setFilterDate(""); // clear date filter
              }}
            />
          </div>
        </div>
      </div>

      {/* ตาราง */}
      <div className="bg-white rounded-xl shadow-md p-4">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-100">
            <tr>
              {[
                "เลขที่ใบเสนอราคา",
                "รหัสลูกค้า",
                "ชื่อลูกค้า",
                "พนักงานขาย",
                "วันยืนยัน",
                "มูลค่า (บาท)",
                "จัดการ",
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-bold uppercase text-gray-600"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-100">
            {filtered.length === 0 && (
              <tr>
                <td colSpan="7" className="text-center py-6 text-gray-500">
                  ไม่พบข้อมูลใบเสนอราคาที่ค้นหา
                </td>
              </tr>
            )}

            {filtered.map((q) => (
              <tr key={q.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-blue-600 font-medium">{q.quoteNo}</td>
                <td className="px-4 py-3">{q.customer?.id}</td>
                <td className="px-4 py-3">{q.customer?.name}</td>
                <td className="px-4 py-3">{q.employee?.name}</td>
                <td className="px-4 py-3">{fmtDate(q.createdAt)}</td>
                <td className="px-4 py-3 text-green-600 font-semibold">
                  ฿ {Number(q.totals?.grandTotal || 0).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <button
                    className="px-4 py-1.5 rounded-lg bg-blue-600 text-white text-sm shadow hover:bg-blue-700"
                    onClick={() => navigate(`/order/${encodeURIComponent(q.quoteNo)}`)}
                  >
                    ดูรายละเอียด
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
