import React, { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import api from "../services/api";
import ApprovalRequestCard from "../components/special_price_request/ApprovalRequestCard";

const ApprovalRequestsPage = () => {
  const { employee } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    loadRequests();
  }, [employee]);

  const loadRequests = async () => {
    if (!employee?.id) {
      console.log("No employee ID found");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await api.get("/api/special-price-requests", {
        params: {
          status: "all",
          approver_employee_id: employee.id, // ⭐ กรองตามรหัสพนักงาน
          limit: 100,
          offset: 0,
        },
      });
      setRequests(response.data.requests || []);
    } catch (error) {
      console.error("Error loading requests:", error);
      alert("เกิดข้อผิดพลาดในการโหลดข้อมูล");
    } finally {
      setLoading(false);
    }
  };

  const filteredRequests = requests.filter((request) => {
    const matchesSearch =
      searchTerm === "" ||
      request.request_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      request.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      request.customer_code?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === "all" || request.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const getStatusCount = (status) => {
    if (status === "all") return requests.length;
    return requests.filter((r) => r.status === status).length;
  };

  if (loading) {
    return (
      <div className="min-h-screen w-full bg-[#F5F5F5] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">กำลังโหลดข้อมูล...</p>
        </div>
      </div>
    );
  }

  if (!employee?.id) {
    return (
      <div className="min-h-screen w-full bg-[#F5F5F5] flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 text-lg">ไม่พบข้อมูลพนักงาน กรุณาเข้าสู่ระบบใหม่</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#F5F5F5]">
      <main className="mx-auto max-w-7xl p-6 lg:p-10">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">ขออนุมัติราคา</h1>
          <p className="text-gray-600">
            คำขอที่ส่งมาหา: <span className="font-bold">{employee?.name || employee?.id}</span>
          </p>
        </div>

        {/* Search and Filter Section */}
        <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">ค้นหา</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="ค้นหาด้วยเลขที่คำขอ, ชื่อลูกค้า, รหัสลูกค้า"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">สถานะ</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">ทั้งหมด ({getStatusCount("all")})</option>
                <option value="pending">รอดำเนินการ ({getStatusCount("pending")})</option>
                <option value="approved">อนุมัติแล้ว ({getStatusCount("approved")})</option>
                <option value="rejected">ปฏิเสธแล้ว ({getStatusCount("rejected")})</option>
              </select>
            </div>
          </div>

          {/* Refresh Button */}
          <div className="mt-4 flex justify-end">
            <button
              onClick={loadRequests}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
            >
              <img src="/assets/refresh.png" alt="Refresh" className="w-5 h-5" />
              รีเฟรช
            </button>
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-gray-600">
            แสดง <span className="font-bold">{filteredRequests.length}</span> รายการ
          </p>
        </div>

        {/* Cards Grid */}
        {filteredRequests.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-md p-12 text-center">
            <img src="/assets/folder.png" alt="No data" className="w-20 h-20 mx-auto mb-4 opacity-50" />
            <p className="text-gray-500 text-lg">ไม่พบข้อมูลคำขออนุมัติ</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRequests.map((request) => (
              <ApprovalRequestCard key={request.request_number} request={request} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default ApprovalRequestsPage;
