// src/components/wizard/CustomerInfoTab.jsx
import React, { useState, useEffect } from "react";
import api from "../../services/api.js";
import { formatDateThai } from "../../utils/dateFormatter.js";

const CustomerInfoTab = ({ customer, customerCode }) => {
  const [customerData, setCustomerData] = useState(null);
  const [creditData, setCreditData] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creditLoading, setCreditLoading] = useState(false);
  const [invoiceLoading, setInvoiceLoading] = useState(false);
  const [error, setError] = useState(null);

  // โหลดข้อมูลลูกค้า
  useEffect(() => {
    const fetchCustomerData = async () => {
      if (!customerCode || customerCode.toUpperCase() === "N/A") {
        setCustomerData(null);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const res = await api.get(`/api/customer/search`, {
          params: { code: customerCode }
        });
        setCustomerData(res.data);
      } catch (err) {
        console.error("Error loading customer data:", err);
        setError("ไม่สามารถโหลดข้อมูลลูกค้าได้");
      } finally {
        setLoading(false);
      }
    };

    fetchCustomerData();
  }, [customerCode]);

  // โหลดข้อมูลเครดิต
  useEffect(() => {
    const loadCreditData = async () => {
      if (!customerCode || customerCode.toUpperCase() === "N/A") {
        setCreditData(null);
        return;
      }

      setCreditLoading(true);
      try {
        const res = await api.get(`/api/credit-status/${customerCode}`);
        console.log("✅ Credit API response:", res.data);
        setCreditData(res.data);
      } catch (err) {
        console.error("❌ Load credit data error:", err);
        setCreditData(null);
      } finally {
        setCreditLoading(false);
      }
    };

    loadCreditData();
  }, [customerCode]);

  // โหลดประวัติการซื้อจาก Invoice
  useEffect(() => {
    const loadInvoices = async () => {
      if (!customerCode || customerCode.toUpperCase() === "N/A") {
        setInvoices([]);
        return;
      }

      setInvoiceLoading(true);
      try {
        // ใช้ endpoint /api/invoice/list กับ filter customer_no
        const res = await api.get(`/api/invoice/list`, {
          params: {
            customer_no: customerCode,
            limit: 5
          }
        });
        
        console.log("✅ Invoices loaded:", res.data);
        
        // เรียงตามวันที่ล่าสุดก่อน
        const sortedInvoices = (res.data || [])
          .sort((a, b) => {
            const dateA = new Date(a["Posting Date"] || a.posting_date || 0);
            const dateB = new Date(b["Posting Date"] || b.posting_date || 0);
            return dateB - dateA;
          })
          .slice(0, 5);
        
        setInvoices(sortedInvoices);
      } catch (err) {
        console.error("❌ Load invoices error:", err);
        setInvoices([]);
      } finally {
        setInvoiceLoading(false);
      }
    };

    loadInvoices();
  }, [customerCode]);

  if (loading || creditLoading || invoiceLoading) {
    return (
      <div className="flex items-center justify-center h-64 border-t-4 border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-500">กำลังโหลดข้อมูลลูกค้า...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 border-t-4 border-gray-200">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (!customerData) {
    return (
      <div className="flex items-center justify-center h-64 border-t-4 border-gray-200">
        <p className="text-gray-500">กรุณาเลือกลูกค้าก่อน</p>
      </div>
    );
  }


  const formatCurrency = (amount) => {
    return Number(amount || 0).toLocaleString("th-TH", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
  };

  const creditPercentage = creditData 
    ? ((creditData.credit_limit - (creditData.credit_available || 0)) / creditData.credit_limit) * 100
    : 0;

  // ใช้ข้อมูลจาก API ถ้ามี ไม่งั้นใส่ 0 (สำหรับลูกค้าเงินสด)
  const displayCredit = creditData ? {
    creditLimit: creditData.credit_limit || 0,
    creditUsed: (creditData.credit_limit || 0) - (creditData.credit_available || 0),
    creditAvailable: creditData.credit_available || 0,
    paymentTerm: creditData.status || "-",
    creditDaysGA: creditData.credit_terms?.gs || 0,
    creditDaysYC: creditData.credit_terms?.yc || 0,
    creditDaysAL: creditData.credit_terms?.ae || 0,
    lastUpdate: creditData.updated_at || null,
  } : {
    creditLimit: 0,
    creditUsed: 0,
    creditAvailable: 0,
    paymentTerm: "เงินสด",
    creditDaysGA: 0,
    creditDaysYC: 0,
    creditDaysAL: 0,
    lastUpdate: null,
  };

  return (
    <div className="border-t-4 border-gray-200 pt-6">
      <div className="grid grid-cols-3 gap-6">
        {/* คอลัมน์ซ้าย: ข้อมูลลูกค้า */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-base font-bold text-gray-700 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
            ข้อมูลลูกค้า
          </h3>
          <div className="space-y-3">
            <InfoField 
              label="รหัสลูกค้า" 
              value={customerData?.id || customerData?.code || customerCode} 
              bold 
            />
            <InfoField 
              label="วันที่เริ่มเป็นลูกค้า" 
              value={customerData?.customer_date ? formatDateThai(customerData.customer_date) : "-"} 
            />
            <InfoField 
              label="ชื่อบริษัท/ร้านค้า/ลูกค้า" 
              value={customerData?.name || "-"} 
            />
            <InfoField 
              label="เลขที่ผู้เสียภาษี" 
              value={customerData?.tax_id || customerData?.tax_number || "-"} 
            />
            <InfoField 
              label="ผู้ติดต่อ" 
              value={customerData?.contact_person || customerData?.name || "-"} 
            />
            <InfoField 
              label="เบอร์โทรศัพท์" 
              value={customerData?.phone || "-"} 
            />
          </div>
        </div>

        {/* คอลัมน์กลาง: ประวัติการซื้อ */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-base font-bold text-gray-700 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
            </svg>
            ประวัติการซื้อ
          </h3>
          
          <div className="text-center mb-4">
            <p className="text-xs text-gray-500 mb-1">ยอดซื้อเฉลี่ย 6 เดือน</p>
            <p className="text-3xl font-bold text-gray-800">
              {formatCurrency(customerData?.accum_6m || 0)} บาท
            </p>
          </div>

          {/* ตารางประวัติ */}
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">เลขที่ใบเสร็จ</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">วันที่</th>
                  <th className="px-3 py-2 text-right font-semibold text-gray-600">มูลค่า</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {invoiceLoading ? (
                  <tr>
                    <td colSpan="3" className="px-3 py-4 text-center text-gray-500">
                      กำลังโหลด...
                    </td>
                  </tr>
                ) : invoices.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="px-3 py-4 text-center text-gray-500">
                      ไม่มีประวัติการซื้อ
                    </td>
                  </tr>
                ) : (
                  invoices.map((invoice, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-3 py-2">{invoice["Document No."] || invoice.document_no || "-"}</td>
                      <td className="px-3 py-2">
                        {invoice["Posting Date"] 
                          ? new Date(invoice["Posting Date"]).toLocaleDateString('th-TH', { 
                              day: '2-digit', 
                              month: '2-digit', 
                              year: 'numeric' 
                            })
                          : "-"}
                      </td>
                      <td className="px-3 py-2 text-right">
                        {formatCurrency(invoice["Amount Including VAT"] || invoice.amount_including_vat || 0)} บาท
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* คอลัมน์ขวา: ข้อมูลเครดิต */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-base font-bold text-gray-700 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
              <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
            </svg>
            ข้อมูลเครดิต
            {creditLoading && (
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            )}
          </h3>

          <div className="space-y-3 mb-4">
            <CreditRow 
              label="การใช้เครดิต" 
              value={`${creditPercentage.toFixed(0)}%`}
              percentage={creditPercentage}
            />
            <CreditRow 
              label="วงเงินเครดิต" 
              value={`${formatCurrency(displayCredit.creditLimit)} บาท`}
              color="text-blue-600"
            />
            <CreditRow 
              label="คงเหลือ" 
              value={`${formatCurrency(displayCredit.creditAvailable)} บาท`}
              color="text-green-600"
            />
            <CreditRow 
              label="ใช้ไป" 
              value={`${formatCurrency(displayCredit.creditUsed)} บาท`}
              color="text-orange-600"
            />
          </div>

          {/* สถานะเครดิต */}
          {creditPercentage > 80 ? (
            <div className="bg-red-100 border border-red-300 rounded-lg p-3 flex items-start gap-2">
              <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm font-bold text-red-800">สถานะเครดิต</p>
                <p className="text-xs text-red-700">⚠️ NPL: เร่งรัดชำระ</p>
              </div>
            </div>
          ) : (
            <div className="bg-green-100 border border-green-300 rounded-lg p-3 flex items-start gap-2">
              <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm font-bold text-green-800">สถานะเครดิต</p>
                <p className="text-xs text-green-700">✓ {displayCredit.paymentTerm}</p>
              </div>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-600 mb-2">วงเงินเครดิต</p>
            <p className="text-lg font-bold text-gray-800">
              {displayCredit.creditDaysGA || displayCredit.creditDaysAL || displayCredit.creditDaysYC || 30}/60 วัน
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const InfoField = ({ label, value, bold = false }) => (
  <div className="space-y-1">
    <p className="text-xs text-gray-500">{label}</p>
    <p className={`text-sm ${bold ? "font-bold" : "font-semibold"} text-gray-800`}>
      {value || "-"}
    </p>
  </div>
);

const CreditRow = ({ label, value, color = "text-gray-800", percentage }) => (
  <div>
    <div className="flex justify-between items-center mb-1">
      <span className="text-xs text-gray-600">{label}</span>
      <span className={`text-sm font-bold ${color}`}>{value}</span>
    </div>
    {percentage !== undefined && (
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${
            percentage > 80 ? "bg-red-500" : "bg-blue-500"
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        ></div>
      </div>
    )}
  </div>
);

const InfoRow = ({ label, value, highlight = false, valueClass = "" }) => (
  <div className="flex justify-between items-center">
    <span className="text-sm text-gray-600">{label}:</span>
    <span className={`text-sm font-semibold ${
      highlight 
        ? "text-blue-600 bg-blue-50 px-3 py-1 rounded-md" 
        : valueClass || "text-gray-800"
    }`}>
      {value || "-"}
    </span>
  </div>
);

export default CustomerInfoTab;
