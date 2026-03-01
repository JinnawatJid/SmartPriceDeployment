import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function CustomerPerDay() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [searchName, setSearchName] = useState("");
  const [searchEmployee, setSearchEmployee] = useState("");
  const [currentDate, setCurrentDate] = useState("");

  // โหลดวันที่ปัจจุบัน (ภาษาไทย)
  useEffect(() => {
    const date = new Date();
    const options = {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "Asia/Bangkok",
    };
    const thaiDate = date.toLocaleDateString("th-TH", options);
    const year = date
      .toLocaleDateString("th-TH", { year: "numeric", timeZone: "Asia/Bangkok" })
      .split(" ")[0];
    setCurrentDate(thaiDate.replace(year, `พ.ศ. ${year}`));
  }, []);

  // โหลดข้อมูลลูกค้าที่ติดต่อวันนี้
  useEffect(() => {
    loadCustomersToday();
  }, []);

  const loadCustomersToday = async () => {
    setLoading(true);
    try {
      const res = await api.get("/api/quotation", {
        params: { status: "complete" },
      });
      const completeList = res.data || [];

      // กรองเฉพาะใบเสนอราคาวันนี้
      const today = new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Bangkok" });
      const todayQuotes = completeList.filter((q) =>
        (q.createdAt || "").startsWith(today)
      );

      // สร้างรายการลูกค้าพร้อมข้อมูล
      const customerMap = new Map();
      todayQuotes.forEach((quote) => {
        const customerId = quote.customer?.id;
        if (!customerId) return;

        if (!customerMap.has(customerId)) {
          customerMap.set(customerId, {
            id: customerId,
            name: quote.customer?.name || "-",
            employee: quote.employee?.name || "-",
            quotes: [],
          });
        }
        customerMap.get(customerId).quotes.push(quote);
      });

      // แปลงเป็น array และเรียงตามเวลา
      const customerList = Array.from(customerMap.values()).map((customer) => {
        const sortedQuotes = customer.quotes.sort(
          (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
        );
        return {
          ...customer,
          latestQuote: sortedQuotes[0],
          quoteCount: sortedQuotes.length,
        };
      });

      // เรียงตามเวลาล่าสุด
      customerList.sort(
        (a, b) => new Date(b.latestQuote.createdAt) - new Date(a.latestQuote.createdAt)
      );

      setCustomers(customerList);
    } catch (err) {
      console.error("Load customers error:", err);
    } finally {
      setLoading(false);
    }
  };

  // กรองข้อมูล
  const filteredCustomers = customers.filter((customer) => {
    const matchName = searchName
      ? customer.name.toLowerCase().includes(searchName.toLowerCase())
      : true;
    const matchEmployee = searchEmployee
      ? customer.employee.toLowerCase().includes(searchEmployee.toLowerCase())
      : true;
    return matchName && matchEmployee;
  });

  const formatTime = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleTimeString("th-TH", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Bangkok",
    });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("th-TH", {
      day: "numeric",
      month: "short",
      year: "numeric",
      timeZone: "Asia/Bangkok",
    });
  };

  return (
    <div className="min-h-screen w-full bg-[#F5F5F5] p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate("/dashboard")}
            className="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
          >
            ← กลับหน้าหลัก
          </button>
          <h1 className="text-3xl font-bold text-gray-800">
            ลูกค้าที่ติดต่อวันนี้
          </h1>
          <p className="text-gray-600 mt-2">{currentDate}</p>
        </div>

        {/* Search Section */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <img src="/assets/magnifier.png" alt="Search" className="w-6 h-6" />
            ลูกค้าที่ซื้อของวันนี้
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ค้นหา
              </label>
              <input
                type="text"
                placeholder="ค้นหาด้วย รหัสลูกค้า, ชื่อ หรือ เบอร์โทรเลขบัตรภาษี"
                value={searchName}
                onChange={(e) => setSearchName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                พนักงานขาย
              </label>
              <input
                type="text"
                placeholder="ค้นหาด้วยชื่อพนักงาน"
                value={searchEmployee}
                onChange={(e) => setSearchEmployee(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
          </div>
          <button
            onClick={loadCustomersToday}
            className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium"
          >
            ค้นหา
          </button>
        </div>

        {/* Table Section */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold">รายการลูกค้าที่ซื้อของวันนี้</h2>
          </div>

          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : filteredCustomers.length === 0 ? (
            <div className="text-center py-20 text-gray-500">
              <p className="text-lg">ไม่พบข้อมูลลูกค้า</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-red-600 text-white">
                  <tr>
                    <th className="px-6 py-4 text-left font-bold">เวลา</th>
                    <th className="px-6 py-4 text-left font-bold">รหัสลูกค้า</th>
                    <th className="px-6 py-4 text-left font-bold">ชื่อลูกค้า</th>
                    <th className="px-6 py-4 text-left font-bold">พนักงานขาย</th>
                    <th className="px-6 py-4 text-left font-bold">วันที่สร้าง</th>
                    <th className="px-6 py-4 text-center font-bold">จัดการ</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCustomers.map((customer, idx) => (
                    <tr
                      key={customer.id}
                      className={`border-b border-gray-200 hover:bg-gray-50 ${
                        idx % 2 === 0 ? "bg-white" : "bg-gray-50"
                      }`}
                    >
                      <td className="px-6 py-4 text-blue-600 font-medium">
                        {formatTime(customer.latestQuote.createdAt)}
                      </td>
                      <td className="px-6 py-4 font-medium">
                        {customer.latestQuote.quoteNumber || customer.id}
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium">{customer.name}</div>
                        {customer.quoteCount > 1 && (
                          <div className="text-xs text-gray-500">
                            ({customer.quoteCount} ใบเสนอราคา)
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">{customer.employee}</td>
                      <td className="px-6 py-4">
                        {formatDate(customer.latestQuote.createdAt)}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() =>
                            navigate(`/customer/${customer.id}`)
                          }
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                        >
                          ดูรายละเอียด
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Summary */}
          {!loading && filteredCustomers.length > 0 && (
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                แสดง {filteredCustomers.length} รายการ จากทั้งหมด {customers.length} รายการ
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CustomerPerDay;
