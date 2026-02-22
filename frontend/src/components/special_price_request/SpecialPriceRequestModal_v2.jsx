import React, { useState, useEffect } from "react";
import { useAuth } from "../../hooks/useAuth";
import api from "../../services/api";

const SpecialPriceRequestModal = ({
  isOpen,
  onClose,
  cart = [],
  totals = {},
  customer = {},
  quoteNo = "",
  onSubmitSuccess,
}) => {
  const { employee } = useAuth();
  // ⭐ FIX: customer uses 'id' property, not 'code'
  const customerData = customer || { id: "", name: "ลูกค้าทั่วไป" };

  // Debug: ดูข้อมูลที่ได้รับ
  useEffect(() => {
    if (isOpen) {
      console.log("🔍 Customer data:", customer);
      console.log("🔍 Customer id:", customer?.id);
      console.log("🔍 Customer code:", customer?.code);
      console.log("🔍 Customer gen_bus:", customer?.gen_bus);
      console.log("🔍 Employee data:", employee);
      console.log("🔍 Cart data:", cart);
      if (cart && cart.length > 0) {
        console.log("🔍 First item:", cart[0]);
        console.log("🔍 First item Price_System:", cart[0].Price_System);
        console.log("🔍 First item UnitPrice:", cart[0].UnitPrice);
        console.log("🔍 First item price:", cart[0].price);
      }
    }
  }, [isOpen, customer, cart, employee]);

  const [formData, setFormData] = useState({
    requestReason: "",
    approverEmail: "",
    branch: "",
    validFrom: "",
    validTo: "",
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);

  // เมื่อเปิด Modal ให้เลือกสินค้าทั้งหมดโดยอัตโนมัติ
  useEffect(() => {
    if (isOpen && cart && cart.length > 0) {
      setSelectedItems(cart.map((_, index) => index));
    }
  }, [isOpen, cart]);

  // Toggle เลือก/ไม่เลือกสินค้า
  const toggleItemSelection = (index) => {
    setSelectedItems((prev) =>
      prev.includes(index)
        ? prev.filter((i) => i !== index)
        : [...prev, index]
    );
  };

  // Toggle เลือกทั้งหมด
  const toggleSelectAll = () => {
    if (selectedItems.length === cart.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(cart.map((_, index) => index));
    }
  };

  // คำนวณราคารวมของสินค้าที่เลือก
  const calculateTotals = () => {
    let originalTotal = 0;
    let requestedTotal = 0;

    selectedItems.forEach((index) => {
      const item = cart[index];
      if (!item) return;

      // ⭐ FIX: W1 price ไม่มีใน cart, ใช้ Price_System แทน (ซึ่งเป็นราคาอ้างอิงจากระบบ)
      // หรือถ้าไม่มี ให้ใช้ราคาปัจจุบันเป็น fallback
      const w1Price = parseFloat(item.Price_System || item.UnitPrice || item.price || 0);
      const currentPrice = parseFloat(item.price || item.UnitPrice || 0);
      const qty = parseFloat(item.qty || 0);

      originalTotal += w1Price * qty;
      requestedTotal += currentPrice * qty;
    });

    const discountPercentage =
      originalTotal > 0
        ? (((originalTotal - requestedTotal) / originalTotal) * 100).toFixed(2)
        : 0;

    return { originalTotal, requestedTotal, discountPercentage };
  };

  const { originalTotal, requestedTotal, discountPercentage } =
    calculateTotals();

  // Validate form
  const validateForm = () => {
    const newErrors = {};

    if (!formData.requestReason.trim()) {
      newErrors.requestReason = "กรุณากรอกเหตุผลที่ขอ";
    }

    if (!formData.approverEmail.trim()) {
      newErrors.approverEmail = "กรุณากรอก Email ผู้อนุมัติ";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.approverEmail)) {
      newErrors.approverEmail = "รูปแบบ Email ไม่ถูกต้อง";
    }

    if (!formData.branch.trim()) {
      newErrors.branch = "กรุณากรอกสาขา";
    }

    if (!formData.validFrom) {
      newErrors.validFrom = "กรุณาเลือกวันที่เริ่มใช้ราคา";
    }

    if (!formData.validTo) {
      newErrors.validTo = "กรุณาเลือกวันที่สิ้นสุด";
    }

    if (formData.validFrom && formData.validTo) {
      if (new Date(formData.validFrom) > new Date(formData.validTo)) {
        newErrors.validTo = "วันที่สิ้นสุดต้องมากกว่าวันที่เริ่มใช้";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle submit
  const handleSubmit = async (e) => {
    e.preventDefault();

    console.log("🔍 Form data before validation:", formData);

    if (!validateForm()) {
      console.log("❌ Validation failed:", errors);
      return;
    }

    if (selectedItems.length === 0) {
      alert("❌ กรุณาเลือกสินค้าอย่างน้อย 1 รายการ");
      return;
    }

    setIsSubmitting(true);

    try {
      // เตรียมข้อมูลสินค้าที่เลือก
      const items = selectedItems.map((index) => {
        const item = cart[index];
        // ⭐ FIX: ใช้ Price_System เป็นราคาอ้างอิง W1
        const w1Price = parseFloat(item.Price_System || item.UnitPrice || item.price || 0);
        return {
          item_code: item.sku || "",
          item_name: item.name || "",
          quantity: parseFloat(item.qty) || 0,
          unit: item.unit || "",
          w1_price: w1Price,
          requested_price: parseFloat(item.price || item.UnitPrice || 0),
        };
      });

      const payload = {
        quote_no: quoteNo || `DRAFT-${Date.now()}`,
        customer_code: customerData.id || customerData.code || "",
        customer_name: customerData.name || "ลูกค้าทั่วไป",
        customer_type: customerData.gen_bus || "",
        requester_name: employee?.name || employee?.employeeName || "พนักงาน",
        request_reason: formData.requestReason,
        original_total: Number(originalTotal) || 0,
        requested_total: Number(requestedTotal) || 0,
        approver_email: formData.approverEmail,
        branch: formData.branch,
        valid_from: formData.validFrom,
        valid_to: formData.validTo,
        items: items,
      };

      console.log("📤 Sending payload:", payload);
      console.log("🔍 Validation check:");
      console.log("   - approverEmail:", formData.approverEmail);
      console.log("   - requestReason:", formData.requestReason);
      console.log("   - branch:", formData.branch);
      console.log("   - validFrom:", formData.validFrom);
      console.log("   - validTo:", formData.validTo);
      console.log("   - items count:", items.length);

      const response = await api.post("/api/special-price-requests", payload);
      const result = response.data;
      console.log("📥 Response:", result);

      alert(
        `✅ ${result.message}\nเลขที่คำขอ: ${result.request_number}\n\nกรุณาตรวจสอบ Email ของผู้อนุมัติ`
      );
      if (onSubmitSuccess) {
        onSubmitSuccess(result);
      }
      onClose();
    } catch (error) {
      console.error("❌ Error submitting request:", error);
      console.error("❌ Error response:", error.response?.data);
      console.error("❌ Error status:", error.response?.status);
      
      let errorMessage = "เกิดข้อผิดพลาดในการส่งคำขอ";
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ ${errorMessage}\n\nกรุณาตรวจสอบข้อมูลและลองใหม่อีกครั้ง`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-3xl w-full max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-yellow-500 text-white px-6 py-4 flex justify-between items-center sticky top-0">
          <h2 className="text-xl font-bold">ขอราคาพิเศษ</h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-2xl"
            disabled={isSubmitting}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {/* ข้อมูลลูกค้า */}
          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h3 className="font-bold text-lg mb-2">ข้อมูลลูกค้า</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">รหัสลูกค้า</p>
                <p className="font-bold">{customerData.id || customerData.code || "-"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">ชื่อลูกค้า</p>
                <p className="font-bold">{customerData.name || "-"}</p>
              </div>
            </div>
          </div>
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-lg">เลือกสินค้าที่ต้องการขอราคาพิเศษ</h3>
              <button
                type="button"
                onClick={toggleSelectAll}
                className="text-sm text-blue-600 hover:underline"
              >
                {selectedItems.length === cart.length
                  ? "ยกเลิกทั้งหมด"
                  : "เลือกทั้งหมด"}
              </button>
            </div>
            <div className="border rounded-lg max-h-60 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="p-2 text-center w-12">
                      <input
                        type="checkbox"
                        checked={selectedItems.length === cart.length}
                        onChange={toggleSelectAll}
                        className="w-4 h-4"
                      />
                    </th>
                    <th className="p-2 text-left">สินค้า</th>
                    <th className="p-2 text-center">จำนวน</th>
                    <th className="p-2 text-right">ราคาที่ขอ</th>
                  </tr>
                </thead>
                <tbody>
                  {cart.map((item, index) => {
                    const w1Price = parseFloat(
                      item.Price_System || item.UnitPrice || item.price || 0
                    );
                    const requestedPrice = parseFloat(item.price || item.UnitPrice || 0);
                    const qty = parseFloat(item.qty || 0);
                    const isBelowW1 = requestedPrice < w1Price;

                    return (
                      <tr
                        key={index}
                        className={`border-t ${
                          selectedItems.includes(index) ? "bg-yellow-50" : ""
                        } ${isBelowW1 ? "text-red-600" : ""}`}
                      >
                        <td className="p-2 text-center">
                          <input
                            type="checkbox"
                            checked={selectedItems.includes(index)}
                            onChange={() => toggleItemSelection(index)}
                            className="w-4 h-4"
                          />
                        </td>
                        <td className="p-2">
                          <div className="font-medium">{item.name}</div>
                          <div className="text-xs text-gray-500">{item.sku}</div>
                        </td>
                        <td className="p-2 text-center">
                          {qty} {item.unit}
                        </td>
                        <td className="p-2 text-right font-bold">
                          ฿{requestedPrice.toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              เลือกแล้ว {selectedItems.length} จาก {cart.length} รายการ
            </p>
          </div>

          {/* เลือกสินค้า */}
          <div className="mb-6"></div>
          <div className="grid grid-cols-2 gap-4 mb-4">
            {/* สาขา */}
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">
                สาขา <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.branch}
                onChange={(e) =>
                  setFormData({ ...formData, branch: e.target.value })
                }
                className={`w-full px-3 py-2 border rounded-lg ${
                  errors.branch ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="ระบุสาขา"
              />
              {errors.branch && (
                <p className="text-red-500 text-sm mt-1">{errors.branch}</p>
              )}
            </div>

            {/* วันที่เริ่มใช้ราคา */}
            <div>
              <label className="block text-sm font-medium mb-1">
                วันที่เริ่มใช้ราคา <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={formData.validFrom}
                onChange={(e) =>
                  setFormData({ ...formData, validFrom: e.target.value })
                }
                className={`w-full px-3 py-2 border rounded-lg ${
                  errors.validFrom ? "border-red-500" : "border-gray-300"
                }`}
              />
              {errors.validFrom && (
                <p className="text-red-500 text-sm mt-1">{errors.validFrom}</p>
              )}
            </div>

            {/* วันที่สิ้นสุด */}
            <div>
              <label className="block text-sm font-medium mb-1">
                วันที่สิ้นสุด <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={formData.validTo}
                onChange={(e) =>
                  setFormData({ ...formData, validTo: e.target.value })
                }
                className={`w-full px-3 py-2 border rounded-lg ${
                  errors.validTo ? "border-red-500" : "border-gray-300"
                }`}
              />
              {errors.validTo && (
                <p className="text-red-500 text-sm mt-1">{errors.validTo}</p>
              )}
            </div>

            {/* Email ผู้อนุมัติ */}
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">
                Email ผู้อนุมัติ <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                value={formData.approverEmail}
                onChange={(e) =>
                  setFormData({ ...formData, approverEmail: e.target.value })
                }
                className={`w-full px-3 py-2 border rounded-lg ${
                  errors.approverEmail ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="manager@company.com"
              />
              {errors.approverEmail && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.approverEmail}
                </p>
              )}
            </div>
          </div>

          {/* เหตุผลที่ขอ */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-1">
              เหตุผลที่ขอราคาพิเศษ <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.requestReason}
              onChange={(e) =>
                setFormData({ ...formData, requestReason: e.target.value })
              }
              className={`w-full px-3 py-2 border rounded-lg ${
                errors.requestReason ? "border-red-500" : "border-gray-300"
              }`}
              rows="4"
              placeholder="ระบุเหตุผล เช่น ลูกค้าเป็น VIP, สั่งซื้อจำนวนมาก, เพื่อรักษาความสัมพันธ์ ฯลฯ"
            />
            {errors.requestReason && (
              <p className="text-red-500 text-sm mt-1">
                {errors.requestReason}
              </p>
            )}
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              ยกเลิก
            </button>
            <button
              type="submit"
              disabled={isSubmitting || selectedItems.length === 0}
              className="flex-1 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "กำลังส่งคำขอ..." : "ยืนยันส่งคำขอ"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SpecialPriceRequestModal;
