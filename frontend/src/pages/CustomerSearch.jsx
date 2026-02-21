import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function CustomerSearch() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 50,
    total: 0,
    total_pages: 0,
  });

  const skipSearchRef = useRef(false);

  // โหลดลูกค้าตอนเปิดหน้า
  useEffect(() => {
    loadCustomers();
  }, [pagination.page]);

  // Autocomplete search
  useEffect(() => {
    if (skipSearchRef.current) {
      skipSearchRef.current = false;
      return;
    }

    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const encoded = encodeURIComponent(searchQuery.trim());
        const res = await api.post(`/api/customer/search-list?q=${encoded}`);
        setSearchResults(res.data || []);
        setShowDropdown(true);
      } catch (err) {
        console.error("Autocomplete error:", err);
        setSearchResults([]);
        setShowDropdown(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const loadCustomers = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        limit: pagination.limit,
      };

      const res = await api.get("/api/customer/all/customers", { params });

      setCustomers(res.data.customers || []);
      setPagination({
        page: res.data.page,
        limit: res.data.limit,
        total: res.data.total,
        total_pages: res.data.total_pages,
      });
    } catch (err) {
      console.error("Load customers error:", err);
      alert("เกิดข้อผิดพลาดในการโหลดข้อมูล");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFromDropdown = (customer) => {
    skipSearchRef.current = true;
    setSearchQuery("");
    setSearchResults([]);
    setShowDropdown(false);
    navigate(`/customer/${customer.id}`);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // ถ้าไม่มีคำค้นหา ให้โหลดทั้งหมด
      setPagination((prev) => ({ ...prev, page: 1 }));
      loadCustomers();
      return;
    }

    setLoading(true);
    setShowDropdown(false);

    try {
      const res = await api.get("/api/customer/list", {
        params: { q: searchQuery.trim() },
      });

      setCustomers(res.data || []);
      setPagination({
        page: 1,
        limit: 50,
        total: res.data?.length || 0,
        total_pages: 1,
      });
    } catch (err) {
      console.error("Search error:", err);
      alert("เกิดข้อผิดพลาดในการค้นหา");
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleViewDetail = (customerId) => {
    navigate(`/customer/${customerId}`);
  };

  return (
    <div className="min-h-screen w-full bg-[#F5F5F5] p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <button
          onClick={() => navigate(-1)}
          className="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
        >
          ← กลับ
        </button>

        {/* Search Section */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <img src="/assets/magnifier.png" alt="Search" className="w-8 h-8" />
            ค้นหารายละเอียดลูกค้า
          </h2>

          <div className="flex flex-col md:flex-row gap-4">
            {/* Search Input with Autocomplete */}
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="ค้นหาด้วย รหัสลูกค้า, ชื่อ หรือ เบอร์โทร....."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
                className="w-full px-6 py-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-lg"
              />

              {/* Autocomplete Dropdown */}
              {showDropdown && searchResults.length > 0 && (
                <ul className="absolute left-0 right-0 mt-2 bg-white border border-gray-300 rounded-xl shadow-lg max-h-80 overflow-y-auto z-50">
                  {searchResults.map((customer) => (
                    <li
                      key={customer.id}
                      onClick={() => handleSelectFromDropdown(customer)}
                      className="px-6 py-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                    >
                      <div className="font-semibold text-gray-800">{customer.name}</div>
                      <div className="text-sm text-gray-600">
                        รหัส: {customer.id} {customer.phone && `• โทร: ${customer.phone}`}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Search Button */}
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-8 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-400 font-semibold text-lg transition-colors"
            >
              {loading ? "กำลังค้นหา..." : "ค้นหา"}
            </button>
          </div>
        </div>

        {/* Results Section */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">รายการลูกค้า</h3>
            <p className="text-gray-600">
              ทั้งหมด {pagination.total.toLocaleString()} รายการ
            </p>
          </div>

          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : customers.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-lg text-gray-500">ไม่พบข้อมูลลูกค้า</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-red-600 text-white">
                      <th className="px-6 py-4 text-left font-bold rounded-tl-lg">รหัสลูกค้า</th>
                      <th className="px-6 py-4 text-left font-bold">ชื่อลูกค้า</th>
                      <th className="px-6 py-4 text-left font-bold">เบอร์โทรศัพท์</th>
                      <th className="px-6 py-4 text-left font-bold rounded-tr-lg">จัดการ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {customers.map((customer, index) => (
                      <tr
                        key={customer.id}
                        className={`border-b border-gray-200 hover:bg-gray-50 ${
                          index % 2 === 0 ? "bg-white" : "bg-gray-50"
                        }`}
                      >
                        <td className="px-6 py-4 font-semibold">{customer.id || customer.code}</td>
                        <td className="px-6 py-4">{customer.name || "-"}</td>
                        <td className="px-6 py-4">{customer.phone || "-"}</td>
                        <td className="px-6 py-4">
                          <button
                            onClick={() => handleViewDetail(customer.id || customer.code)}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
                          >
                            ดูรายละเอียด
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {pagination.total_pages > 1 && (
                <div className="mt-6 flex justify-center items-center gap-2">
                  <button
                    onClick={() => handlePageChange(pagination.page - 1)}
                    disabled={pagination.page === 1}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    ← ก่อนหน้า
                  </button>

                  <div className="flex gap-2">
                    {[...Array(pagination.total_pages)].map((_, i) => {
                      const pageNum = i + 1;
                      // แสดงเฉพาะหน้าใกล้เคียง
                      if (
                        pageNum === 1 ||
                        pageNum === pagination.total_pages ||
                        (pageNum >= pagination.page - 2 && pageNum <= pagination.page + 2)
                      ) {
                        return (
                          <button
                            key={pageNum}
                            onClick={() => handlePageChange(pageNum)}
                            className={`px-4 py-2 rounded-lg font-medium ${
                              pagination.page === pageNum
                                ? "bg-blue-600 text-white"
                                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      } else if (
                        pageNum === pagination.page - 3 ||
                        pageNum === pagination.page + 3
                      ) {
                        return <span key={pageNum} className="px-2">...</span>;
                      }
                      return null;
                    })}
                  </div>

                  <button
                    onClick={() => handlePageChange(pagination.page + 1)}
                    disabled={pagination.page === pagination.total_pages}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    ถัดไป →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default CustomerSearch;
