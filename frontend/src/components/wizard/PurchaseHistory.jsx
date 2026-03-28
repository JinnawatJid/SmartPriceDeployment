// frontend/src/components/wizard/PurchaseHistory.jsx
import React, { useState, useEffect } from "react";
import api from "../../services/api.js";

/**
 * PurchaseHistory Component
 * 
 * Displays purchase history grouped by invoice.
 * Shows all invoices for a customer, and when clicked, displays line items with calculated quantities.
 * Calculates quantities based on product type:
 * - Glass: Square feet (ตารางฟุต)
 * - Aluminum: Linear meters (เส้น) and Kilograms (กิโล)
 * - Standard: Pieces (ชิ้น)
 * 
 * Requirements:
 * - 7.1: Fetch invoice data when customer is selected
 * - 7.3: Handle network errors gracefully
 * - 7.4: Cache data to avoid redundant API calls
 * 
 * Props:
 * - customerCode: Customer code to fetch invoices for
 */
const PurchaseHistory = ({ customerCode }) => {
  const [invoiceGroups, setInvoiceGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedInvoice, setExpandedInvoice] = useState(null);
  const [cachedData, setCachedData] = useState({});

  // Fetch and group invoice data when customer changes
  useEffect(() => {
    if (!customerCode || customerCode === "N/A") {
      setInvoiceGroups([]);
      setIsExpanded(false);
      setError(null);
      return;
    }

    // Check cache first (Requirement 7.4)
    if (cachedData[customerCode]) {
      setInvoiceGroups(cachedData[customerCode]);
      setLoading(false);
      return;
    }

    const fetchAndGroupInvoices = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all invoice line items for customer (Requirement 7.1)
        const response = await api.get("/api/invoice/list", {
          params: {
            customer_no: customerCode,
            limit: 500,
            return_line_items: true, // Request line items with calculated quantities
          },
        });

        const invoiceLines = response.data || [];

        // Group by Invoice
        const invoiceMap = {};
        
        for (const line of invoiceLines) {
          const docNo = line["Document No."] || line.document_no;
          if (!docNo) continue;

          if (!invoiceMap[docNo]) {
            invoiceMap[docNo] = {
              document_no: docNo,
              posting_date: line["Posting Date"] || line.posting_date,
              customer_name: line["Sell-to Customer Name"] || line.customer_name,
              items: [],
            };
          }

          // Add line item with calculated quantity
          invoiceMap[docNo].items.push({
            sku: line.sku,
            product_name: line.Description || line.description || "-",
            product_type: line.product_type || "Other",
            quantity: parseFloat(line.Quantity || line.quantity || 0),
            unit: line["Unit of Measure"] || line.unit || "ชิ้น",
            calculated_quantity: line.calculated_quantity || {},
          });
        }

        // Convert to array and sort by posting date descending
        const grouped = Object.values(invoiceMap).sort((a, b) => {
          const dateA = new Date(a.posting_date || 0);
          const dateB = new Date(b.posting_date || 0);
          return dateB - dateA;
        });

        setInvoiceGroups(grouped);

        // Cache the data (Requirement 7.4)
        setCachedData((prev) => ({
          ...prev,
          [customerCode]: grouped,
        }));
      } catch (err) {
        console.error("Error fetching invoices:", err);
        // Handle network errors gracefully (Requirement 7.3)
        setError("ไม่สามารถโหลดประวัติการซื้อได้ กรุณาลองใหม่อีกครั้ง");
        setInvoiceGroups([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAndGroupInvoices();
  }, [customerCode]);

  // Toggle main dropdown
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  // Toggle invoice details
  const toggleInvoiceDetails = (docNo) => {
    setExpandedInvoice(expandedInvoice === docNo ? null : docNo);
  };

  // Format quantity display based on product type
  const formatQuantity = (item) => {
    const calc = item.calculated_quantity || {};
    
    if (item.product_type === "Glass") {
      return `${(calc.total_square_feet || 0).toLocaleString()} ตารางฟุต`;
    } else if (item.product_type === "Aluminum") {
      const meters = (calc.linear_meters || 0).toLocaleString();
      const kg = calc.total_kilograms !== undefined && calc.total_kilograms !== null
        ? `${calc.total_kilograms.toLocaleString()} กิโล` 
        : "- กิโล";
      return (
        <div className="text-right">
          <div>{meters} เส้น</div>
          <div className="text-gray-600 text-xs">{kg}</div>
        </div>
      );
    } else {
      return `${(calc.quantity || 0).toLocaleString()} ${calc.unit || "ชิ้น"}`;
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">ประวัติการซื้อสินค้า</h3>
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">กำลังโหลดประวัติการซื้อ...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">ประวัติการซื้อสินค้า</h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (!invoiceGroups || invoiceGroups.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">ประวัติการซื้อสินค้า</h3>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="mt-2 text-gray-600">ไม่พบประวัติการซื้อ</p>
        </div>
      </div>
    );
  }

  // Display invoices grouped by document number
  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header with toggle button */}
      <div
        onClick={toggleExpanded}
        className="flex justify-between items-center cursor-pointer hover:bg-gray-50 -m-6 p-6 rounded-t-lg transition-colors"
      >
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">ประวัติการซื้อสินค้า</h3>
          <span className="text-sm text-gray-500">
            ({invoiceGroups.length} ใบ)
          </span>
        </div>
        <svg
          className={`w-6 h-6 text-gray-600 transition-transform ${
            isExpanded ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>

      {/* Dropdown content */}
      {isExpanded && (
        <div className="mt-4 border-t pt-4 space-y-2">
          {invoiceGroups.map((invoice) => (
            <div key={invoice.document_no} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* Invoice header */}
              <div
                onClick={() => toggleInvoiceDetails(invoice.document_no)}
                className="flex justify-between items-center p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <svg
                    className={`w-5 h-5 text-gray-600 transition-transform ${
                      expandedInvoice === invoice.document_no ? "rotate-90" : ""
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  <div>
                    <p className="font-semibold text-gray-900">{invoice.document_no}</p>
                    <p className="text-sm text-gray-600">
                      {invoice.posting_date
                        ? new Date(invoice.posting_date).toLocaleDateString("th-TH", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "numeric",
                          })
                        : "-"}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">{invoice.items.length} รายการ</p>
                </div>
              </div>

              {/* Invoice line items */}
              {expandedInvoice === invoice.document_no && (
                <div className="p-4 bg-white">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          SKU
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          ชื่อสินค้า
                        </th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                          จำนวน 
                        </th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                          จำนวนที่คำนวณ
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {invoice.items.map((item, idx) => (
                        <tr key={`${item.sku}-${idx}`} className="hover:bg-gray-50">
                          <td className="px-3 py-2 text-sm font-medium text-gray-900">
                            {item.sku}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-700">
                            {item.product_name}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-600 text-right">
                            {item.quantity.toLocaleString()} {item.unit}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-900 text-right font-medium">
                            {formatQuantity(item)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PurchaseHistory;
