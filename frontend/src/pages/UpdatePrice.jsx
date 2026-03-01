import React, { useState } from "react";
import { Tag } from "lucide-react";
import UploadPriceExcel from "../components/updatePrice/UploadPriceExcel";
import PromotionManagement from "./PromotionManagement";

export default function UpdatePrice() {
  const [uploadResult, setUploadResult] = useState(null);
  const [activeTab, setActiveTab] = useState("price"); // "price" | "promotion"

  const handleUploadComplete = (result) => {
    setUploadResult(result);
    // Clear result after 5 seconds
    setTimeout(() => setUploadResult(null), 5000);
  };

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
