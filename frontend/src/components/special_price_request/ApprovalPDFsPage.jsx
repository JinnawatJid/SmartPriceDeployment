// src/components/special_price_request/ApprovalPDFsPage.jsx
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../../services/api";

export default function ApprovalPDFsPage() {
  const { requestNumber } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pdfFiles, setPdfFiles] = useState([]);

  useEffect(() => {
    const fetchPDFs = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/api/special-price-requests/${requestNumber}/approval-pdfs`);
        setPdfFiles(response.data.pdf_files || []);
      } catch (err) {
        console.error(err);
        setError("ไม่สามารถโหลดรายการเอกสารได้");
      } finally {
        setLoading(false);
      }
    };

    if (requestNumber) {
      fetchPDFs();
    }
  }, [requestNumber]);

  const handleDownload = (downloadUrl) => {
    window.open(downloadUrl, '_blank');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">กำลังโหลด...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 text-lg">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            ย้อนกลับ
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">เอกสารอนุมัติราคาพิเศษ</h1>
              <p className="text-gray-600 mt-1">คำขอเลขที่: {requestNumber}</p>
            </div>
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              ← ย้อนกลับ
            </button>
          </div>
        </div>

        {/* PDF List */}
        {pdfFiles.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">📄</div>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">ไม่มีเอกสารแนบ</h2>
            <p className="text-gray-500">ผู้อนุมัติยังไม่ได้แนบเอกสารมาพร้อมการอนุมัติ</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800 text-sm">
                <span className="font-semibold">📎 พบเอกสาร {pdfFiles.length} ไฟล์</span>
                <br />
                คลิกที่ไฟล์เพื่อดาวน์โหลดหรือเปิดดู
              </p>
            </div>

            {pdfFiles.map((pdf, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => handleDownload(pdf.download_url)}
              >
                <div className="p-6 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-16 h-16 bg-red-100 rounded-lg flex items-center justify-center">
                        <span className="text-3xl">📄</span>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800">{pdf.filename}</h3>
                      <p className="text-sm text-gray-500 mt-1">เอกสารที่ผู้อนุมัติแนบมา</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(pdf.download_url);
                      }}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2"
                    >
                      <span>📥</span>
                      <span>ดาวน์โหลด</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
