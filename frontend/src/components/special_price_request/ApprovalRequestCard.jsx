import React from "react";
import { useNavigate } from "react-router-dom";

const ApprovalRequestCard = ({ request }) => {
  const navigate = useNavigate();

  const formatDate = (dateString) => {
    if (!dateString) return "-";
    const date = new Date(dateString);
    return date.toLocaleDateString("th-TH", {
      year: "numeric",
      month: "short",
      day: "numeric",
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
      pending: { text: "รอดำเนินการ", bg: "bg-yellow-500", textColor: "text-white" },
      approved: { text: "อนุมัติแล้ว", bg: "bg-green-500", textColor: "text-white" },
      rejected: { text: "ปฏิเสธแล้ว", bg: "bg-red-500", textColor: "text-white" },
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span className={`${config.bg} ${config.textColor} px-3 py-1 rounded-full text-sm font-bold`}>
        {config.text}
      </span>
    );
  };

  const handleViewDetail = () => {
    navigate(`/approval-requests/${request.request_number}`);
  };

  return (
    <div className="bg-white rounded-2xl shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-blue-600">{request.request_number}</h3>
          <p className="text-sm text-gray-600 mt-1">
            รหัสลูกค้า: <span className="font-bold">{request.customer_code || "-"}</span>
          </p>
        </div>
        {getStatusBadge(request.status)}
      </div>

      {/* Customer Info */}
      <div className="mb-4">
        <p className="text-lg font-bold text-gray-800">{request.customer_name || "ลูกค้าทั่วไป"}</p>
        <p className="text-sm text-gray-600">
          ผู้ขอ: <span className="font-medium">{request.requester_name}</span>
        </p>
        {request.approver_employee_id && (
          <p className="text-sm text-gray-600">
            ผู้อนุมัติ: <span className="font-medium">{request.approver_employee_id}</span>
          </p>
        )}
      </div>

      {/* Price Summary */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-gray-500">ราคาเดิม</p>
            <p className="text-lg font-bold text-gray-700">
              {formatCurrency(request.original_total)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">ราคาที่ขอ</p>
            <p className="text-lg font-bold text-green-600">
              {formatCurrency(request.requested_total)}
            </p>
          </div>
        </div>
      </div>

      {/* Items Summary */}
      <div className="mb-4">
        <p className="text-sm font-bold text-gray-700 mb-2">
          รายการสินค้า ({request.items?.length || 0} รายการ)
        </p>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {request.items?.map((item, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {item.item_name}
                  </p>
                  <p className="text-xs text-gray-500">
                    รหัส: {item.item_code} | จำนวน: {item.quantity} {item.unit || "หน่วย"}
                  </p>
                </div>
                {item.is_below_normal && (
                  <span className="bg-red-100 text-red-600 text-xs px-2 py-1 rounded-full font-medium ml-2">
                    ต่ำกว่าราคาปกติ
                  </span>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <p className="text-gray-500">ราคาเดิม</p>
                  <p className="font-bold text-gray-700">{formatCurrency(item.normal_price)}</p>
                </div>
                <div>
                  <p className="text-gray-500">ราคาที่ขอ</p>
                  <p className="font-bold text-green-600">{formatCurrency(item.requested_price)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="flex justify-between items-center pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-600">
          <p>วันที่สร้าง: {formatDate(request.created_at)}</p>
        </div>
        <button
          onClick={handleViewDetail}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          ดูรายละเอียด
        </button>
      </div>
    </div>
  );
};

export default ApprovalRequestCard;
