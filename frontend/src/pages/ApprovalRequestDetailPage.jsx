import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import api from "../services/api";

const ApprovalRequestDetailPage = () => {
  const { requestNumber } = useParams();
  const navigate = useNavigate();
  const { employee } = useAuth();
  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    loadRequestDetail();
  }, [requestNumber]);

  const loadRequestDetail = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/special-price-requests/${requestNumber}`);
      const requestData = response.data;
      
      // ตรวจสอบสิทธิ์: ถ้าไม่ใช่ผู้อนุมัติของคำขอนี้ ให้กลับไปหน้ารายการ
      if (requestData.approver_employee_id && employee?.id && 
          requestData.approver_employee_id !== employee.id) {
        alert("คุณไม่มีสิทธิ์เข้าถึงคำขอนี้");
        navigate("/approval-requests");
        return;
      }
      
      setRequest(requestData);
      
      // โหลดรายการไฟล์แนบ
      loadAttachedFiles(requestNumber);
    } catch (error) {
      console.error("Error loading request detail:", error);
      alert("เกิดข้อผิดพลาดในการโหลดข้อมูล");
      navigate("/approval-requests");
    } finally {
      setLoading(false);
    }
  };

  const loadAttachedFiles = async (reqNumber) => {
    try {
      const response = await api.get(`/api/special-price-requests/${reqNumber}/approval-pdfs`);
      const files = response.data.pdf_files || response.data.files || [];
      console.log('📎 Loaded attached files:', files);
      setAttachedFiles(files);
    } catch (error) {
      console.error("Error loading attached files:", error);
      setAttachedFiles([]);
    }
  };

  const [selectedFiles, setSelectedFiles] = useState([]); // ไฟล์ที่เลือกแต่ยังไม่ได้อัปโหลด

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    // เพิ่มไฟล์ใหม่เข้าไปในรายการ
    setSelectedFiles(prev => [...prev, ...files]);
    event.target.value = ''; // Reset input เพื่อให้เลือกไฟล์เดิมได้อีก
  };

  const handleRemoveSelectedFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleFileUpload = async () => {
    if (selectedFiles.length === 0) {
      alert('กรุณาเลือกไฟล์ก่อนอัปโหลด');
      return;
    }

    try {
      setIsUploading(true);
      const formData = new FormData();
      
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await api.post(
        `/api/special-price-requests/${requestNumber}/upload-approval-files`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      // แสดงรายการไฟล์ที่อัปโหลดสำเร็จ
      const uploadedFiles = response.data.files || [];
      alert(`✅ อัปโหลดสำเร็จ ${uploadedFiles.length} ไฟล์`);
      
      setSelectedFiles([]); // ล้างรายการไฟล์ที่เลือก
      loadAttachedFiles(requestNumber); // Reload files
    } catch (error) {
      console.error("Error uploading files:", error);
      const errorMsg = error.response?.data?.detail || "เกิดข้อผิดพลาดในการอัปโหลดไฟล์";
      alert(`❌ ${errorMsg}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownloadFile = async (file) => {
    try {
      // ใช้ download_url ที่ API ส่งมา
      const url = file.download_url;
      window.open(url, '_blank');
    } catch (error) {
      console.error("Error downloading file:", error);
      alert("เกิดข้อผิดพลาดในการดาวน์โหลดไฟล์");
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "-";
    const date = new Date(dateString);
    return date.toLocaleDateString("th-TH", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("th-TH", {
      style: "currency",
      currency: "THB",
      minimumFractionDigits: 0,
    }).format(amount || 0);
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { text: "รอดำเนินการ", bg: "bg-yellow-500" },
      approved: { text: "อนุมัติแล้ว", bg: "bg-green-500" },
      rejected: { text: "ปฏิเสธแล้ว", bg: "bg-red-500" },
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span className={`${config.bg} text-white px-4 py-2 rounded-full text-sm font-bold`}>
        {config.text}
      </span>
    );
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await api.get(`/api/special-price-requests/${requestNumber}/pdf`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${requestNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Error downloading PDF:", error);
      alert("เกิดข้อผิดพลาดในการดาวน์โหลด PDF");
    }
  };

  const handleApprove = async () => {
    if (!window.confirm("คุณต้องการอนุมัติคำขอนี้ใช่หรือไม่?")) {
      return;
    }

    try {
      setIsApproving(true);
      await api.post(`/api/special-price-requests/${requestNumber}/approve`, {
        approved_by: employee?.name || employee?.id || "System User",
      });
      alert("อนุมัติคำขอสำเร็จ");
      loadRequestDetail(); // Reload data
    } catch (error) {
      console.error("Error approving request:", error);
      alert("เกิดข้อผิดพลาดในการอนุมัติ");
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = () => {
    setShowRejectModal(true);
  };

  const confirmReject = async () => {
    if (!rejectionReason.trim()) {
      alert("กรุณาระบุเหตุผลในการปฏิเสธ");
      return;
    }

    try {
      setIsRejecting(true);
      await api.post(`/api/special-price-requests/${requestNumber}/reject`, {
        rejected_by: employee?.name || employee?.id || "System User",
        rejection_reason: rejectionReason,
      });
      alert("ปฏิเสธคำขอสำเร็จ");
      setShowRejectModal(false);
      setRejectionReason("");
      loadRequestDetail(); // Reload data
    } catch (error) {
      console.error("Error rejecting request:", error);
      alert("เกิดข้อผิดพลาดในการปฏิเสธ");
    } finally {
      setIsRejecting(false);
    }
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

  if (!request) {
    return null;
  }

  const discountPercent =
    request.original_total > 0
      ? (((request.original_total - request.requested_total) / request.original_total) * 100).toFixed(2)
      : 0;

  return (
    <div className="min-h-screen w-full bg-[#F5F5F5]">
      <main className="mx-auto max-w-5xl p-6 lg:p-10">
        {/* Back Button */}
        <button
          onClick={() => navigate("/approval-requests")}
          className="mb-6 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
        >
          ย้อนกลับ
        </button>

        {/* Header Card */}
        <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">รายละเอียดรายการสินค้า</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">เลขที่ใบเสนอราคา</p>
              <p className="font-bold text-gray-800">#{request.quote_no}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">วันที่ส่งมือ</p>
              <p className="font-bold text-gray-800">{formatDate(request.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">รหัสลูกค้า</p>
              <p className="font-bold text-gray-800">{request.customer_code || "-"}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">ชื่อลูกค้า</p>
              <p className="font-bold text-gray-800">{request.customer_name || "ลูกค้าทั่วไป"}</p>
            </div>
          </div>
        </div>

        {/* Items Table */}
        <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">รายการสินค้า</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-3 text-center text-sm font-bold text-gray-700">#</th>
                  <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">สินค้า</th>
                  <th className="px-4 py-3 text-center text-sm font-bold text-gray-700">จำนวน</th>
                  <th className="px-4 py-3 text-right text-sm font-bold text-gray-700">ราคา/หน่วย</th>
                  <th className="px-4 py-3 text-right text-sm font-bold text-gray-700">ยอดรวม</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {request.items?.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-center text-sm text-gray-800">{index + 1}</td>
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-gray-800">{item.item_name}</div>
                      <div className="text-xs text-gray-500">{item.item_code}</div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        value={item.quantity}
                        readOnly
                        className="w-20 px-2 py-1 text-center border border-gray-300 rounded bg-gray-50"
                      />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="text-sm text-gray-600">ราคาเดิม:</div>
                      <div className="text-sm font-bold text-blue-600">{formatCurrency(item.normal_price)}</div>
                      <div className="text-sm text-gray-600">ราคาที่ขอ:</div>
                      <div className="text-sm font-bold text-green-600">{formatCurrency(item.requested_price)}</div>
                      <div className="text-sm text-red-600">ส่วนลด: {((1 - item.requested_price / item.normal_price) * 100).toFixed(0)}%</div>
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-gray-800">
                      {formatCurrency(item.requested_price * item.quantity)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Left: Request Reason */}
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">เหตุผลที่ขออนุมัติ</h2>
            <div className="border border-dashed border-gray-300 rounded-lg p-4 min-h-[150px]">
              <p className="text-gray-700 whitespace-pre-wrap">{request.request_reason || "-"}</p>
            </div>
          </div>

          {/* Right: Documents */}
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">เอกสารแนบ</h2>
            <div className="border border-dashed border-gray-300 rounded-lg p-4 min-h-[150px]">
              {/* Upload Button - Only for pending status */}
              {request.status === "pending" && (
                <div className="mb-4">
                  <input
                    type="file"
                    id="file-upload"
                    multiple
                    onChange={handleFileSelect}
                    className="hidden"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                  />
                  <div className="flex gap-2">
                    <label
                      htmlFor="file-upload"
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg cursor-pointer transition-colors"
                    >
                      <span>📎</span>
                      <span>เลือกไฟล์</span>
                    </label>
                    {selectedFiles.length > 0 && (
                      <button
                        onClick={handleFileUpload}
                        disabled={isUploading}
                        className={`inline-flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors ${
                          isUploading ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        <span>⬆️</span>
                        <span>{isUploading ? 'กำลังอัปโหลด...' : `อัปโหลด (${selectedFiles.length})`}</span>
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    รองรับ: PDF, Word, Excel, รูปภาพ
                  </p>
                </div>
              )}

              {/* Selected Files Preview */}
              {selectedFiles.length > 0 && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    ไฟล์ที่เลือก ({selectedFiles.length} ไฟล์)
                  </p>
                  <div className="space-y-2">
                    {selectedFiles.map((file, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 bg-white rounded border border-gray-200">
                        <span className="text-lg">📎</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800 truncate">{file.name}</p>
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024).toFixed(2)} KB
                          </p>
                        </div>
                        <button
                          onClick={() => handleRemoveSelectedFile(index)}
                          className="text-red-500 hover:text-red-700 text-sm font-medium px-2 py-1 rounded hover:bg-red-50 transition-colors"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* File List */}
              <div className="space-y-2">
                {/* PDF ของใบเสนอราคา */}
                <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <span className="text-red-500 text-xl">📄</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">quotation_draft.pdf</p>
                    <p className="text-xs text-gray-500">ใบเสนอราคาหลัก</p>
                  </div>
                  <button
                    onClick={handleDownloadPDF}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium px-3 py-1 rounded hover:bg-blue-50 transition-colors"
                  >
                    ดาวน์โหลด
                  </button>
                </div>

                {/* ไฟล์ที่แนบเพิ่มเติม */}
                {attachedFiles.length > 0 && (
                  <div className="border-t border-gray-200 pt-2 mt-2">
                    <p className="text-xs font-medium text-gray-600 mb-2">
                      เอกสารแนบเพิ่มเติม ({attachedFiles.length} ไฟล์)
                    </p>
                    {attachedFiles.map((file, index) => {
                      const fileExt = file.filename.split('.').pop().toLowerCase();
                      const fileIcon = fileExt === 'pdf' ? '📄' : 
                                      ['doc', 'docx'].includes(fileExt) ? '📝' :
                                      ['xls', 'xlsx'].includes(fileExt) ? '📊' :
                                      ['jpg', 'jpeg', 'png'].includes(fileExt) ? '🖼️' : '📎';
                      
                      return (
                        <div key={index} className="flex items-center gap-2 p-2 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
                          <span className="text-xl">{fileIcon}</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-800 truncate">{file.filename}</p>
                            <p className="text-xs text-gray-500">
                              อัปโหลดแล้ว
                            </p>
                          </div>
                          <button
                            onClick={() => handleDownloadFile(file)}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium px-3 py-1 rounded hover:bg-blue-200 transition-colors"
                          >
                            ดาวน์โหลด
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}

                {attachedFiles.length === 0 && request.status === "pending" && (
                  <div className="text-center py-6">
                    <p className="text-gray-400 text-sm">ยังไม่มีเอกสารแนบเพิ่มเติม</p>
                    <p className="text-gray-400 text-xs mt-1">คลิกปุ่ม "แนบไฟล์" ด้านบนเพื่อเพิ่มเอกสาร</p>
                  </div>
                )}

                {attachedFiles.length === 0 && request.status !== "pending" && (
                  <p className="text-gray-400 text-sm text-center py-4">
                    ไม่มีเอกสารแนบเพิ่มเติม
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons - Only for pending status */}
        {request.status === "pending" && (
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => navigate("/approval-requests")}
              className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
            >
              แบบฟอร์ม
            </button>
            <button
              onClick={handleReject}
              disabled={isRejecting}
              className="px-6 py-3 bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              {isRejecting ? "กำลังปฏิเสธ..." : "REJECT"}
            </button>
            <button
              onClick={handleApprove}
              disabled={isApproving}
              className="px-6 py-3 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              {isApproving ? "กำลังอนุมัติ..." : "APPPROVE"}
            </button>
          </div>
        )}

        {/* Status Display for approved/rejected */}
        {request.status !== "pending" && (
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              {request.status === "approved" ? "ข้อมูลการอนุมัติ" : "ข้อมูลการปฏิเสธ"}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">
                  {request.status === "approved" ? "ผู้อนุมัติ" : "ผู้ปฏิเสธ"}
                </p>
                <p className="font-bold text-gray-800">
                  {request.approved_by || request.rejected_by || "-"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">วันที่</p>
                <p className="font-bold text-gray-800">
                  {formatDate(request.approved_at || request.rejected_at)}
                </p>
              </div>
              {request.rejection_reason && (
                <div className="col-span-2">
                  <p className="text-sm text-gray-600">เหตุผลในการปฏิเสธ</p>
                  <p className="font-bold text-red-600">{request.rejection_reason}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Rejection Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">ปฏิเสธคำขอ</h3>
            <p className="text-gray-600 mb-4">กรุณาระบุเหตุผลในการปฏิเสธ</p>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4"
              rows="4"
              placeholder="ระบุเหตุผล..."
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectionReason("");
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                ยกเลิก
              </button>
              <button
                onClick={confirmReject}
                disabled={!rejectionReason.trim() || isRejecting}
                className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRejecting ? "กำลังปฏิเสธ..." : "ยืนยันปฏิเสธ"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalRequestDetailPage;
