import React, { useState } from "react";
import UploadPriceExcel from "../components/updatePrice/UploadPriceExcel";

export default function UpdatePrice() {
  const [uploadResult, setUploadResult] = useState(null);

  const handleUploadComplete = (result) => {
    setUploadResult(result);
    // Clear result after 5 seconds
    setTimeout(() => setUploadResult(null), 5000);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Update Price (Manager)</h1>

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
  );
}
