import React, { useState, useEffect } from "react";
import { Tag } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import UploadPriceExcel from "../components/updatePrice/UploadPriceExcel";
import PromotionManagement from "./PromotionManagement";

// รหัสพนักงานที่มีสิทธิ์เข้าถึงหน้า "เพิ่ม/อัปเดตราคา"
const ALLOWED_PRICE_UPDATE_EMPLOYEES = ['90038', '20061', '11186', '21702', '21367', '20614', '20194', '20785', '20093', '20686', '16647', '20595', '20091', '16053', '16654', '16725', '10011', '20040', '10254', '16646', '16702', '20037', '16723', '20974', '20129', '10073', '20084', '21094', '20813'];

export default function UpdatePrice() {
  const { employee } = useAuth();
  const navigate = useNavigate();
  const [allowedEmployees, setAllowedEmployees] = useState(ALLOWED_PRICE_UPDATE_EMPLOYEES);
  const [uploadResult, setUploadResult] = useState(null);
  const [activeTab, setActiveTab] = useState("price"); // "price" | "promotion" | "project"

  // ตรวจสอบสิทธิ์เข้าถึง
  useEffect(() => {
    const fetchEmployeeAccess = async () => {
      try {
        const res = await api.get("/api/admin/employee-access");
        setAllowedEmployees(res.data.allowed_price_update_employees);
      } catch (err) {
        console.error("Failed to fetch employee access:", err);
      }
    };
    fetchEmployeeAccess();
  }, []);

  useEffect(() => {
    if (employee && !allowedEmployees.includes(employee.id)) {
      // ถ้าไม่ใช่พนักงานที่อนุญาต ให้กลับไปที่ Dashboard
      navigate("/dashboard", { replace: true });
    }
  }, [employee, allowedEmployees, navigate]);

  const handleUploadComplete = (result) => {
    setUploadResult(result);
    // Clear result after 5 seconds
    setTimeout(() => setUploadResult(null), 5000);
  };

  // ถ้าไม่ใช่พนักงานที่อนุญาต ให้แสดงข้อความ
  if (employee && !allowedEmployees.includes(employee.id)) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h2 className="text-xl font-bold text-red-800 mb-2">ไม่มีสิทธิ์เข้าถึง</h2>
          <p className="text-red-600">ขออภัย คุณไม่มีสิทธิ์เข้าถึงหน้านี้</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Update Data (Manager)</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab("price")}
            className={`px-6 py-3 font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "price"
                ? "border-red-500 text-red-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <Tag className="w-5 h-5" />
            อัปเดตราคา (Update Price)
          </button>

          <button
            onClick={() => setActiveTab("promotion")}
            className={`px-6 py-3 font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "promotion"
                ? "border-red-500 text-red-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
            </svg>
            จัดการโปรโมชั่น
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "price" && (
        <div>
          <UploadPriceExcel onUploaded={handleUploadComplete} />

          {/* Success/Error Message */}
          {uploadResult && (
            <div className={`mt-4 p-4 rounded-lg ${
              uploadResult.errors > 0 ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'
            }`}>
              <div className="flex items-start gap-3">
                <span className="text-2xl">
                  {uploadResult.errors > 0 ? '⚠️' : '✅'}
                </span>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-2">
                    {uploadResult.errors > 0 ? 'อัปโหลดเสร็จสิ้น (มีข้อผิดพลาดบางรายการ)' : 'อัปโหลดสำเร็จ!'}
                  </h3>
                  <div className="text-sm text-gray-700 space-y-1">
                    <p>ทั้งหมด: {uploadResult.total_rows} รายการ</p>
                    <p className="text-green-600">สำเร็จ: {uploadResult.successful_updates} รายการ</p>
                    {uploadResult.errors > 0 && (
                      <p className="text-red-600">ข้อผิดพลาด: {uploadResult.errors} รายการ</p>
                    )}
                  </div>
                  
                  {/* Error Details */}
                  {uploadResult.error_details && uploadResult.error_details.length > 0 && (
                    <details className="mt-3">
                      <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                        ดูรายละเอียดข้อผิดพลาด
                      </summary>
                      <ul className="mt-2 text-xs text-red-600 space-y-1 pl-4 list-disc">
                        {uploadResult.error_details.map((error, idx) => (
                          <li key={idx}>{error}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "promotion" && (
        <PromotionManagement />
      )}
    </div>
  );
}
