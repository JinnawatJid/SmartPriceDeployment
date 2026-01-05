// src/components/wizard/CustomerSearchSection.jsx
import React, { useState } from "react";
import api from "../../services/api.js";
import Loader from "../Loader.jsx";

// ไอคอนเฉพาะส่วนค้นหา/ผลลัพธ์
const SearchIcon = () => (
  <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607z"
    />
  </svg>
);

const CheckCircleIcon = () => (
  <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

/**
 * CustomerSearchSection
 * props:
 *  - customer: object | null   // ลูกค้าปัจจุบัน (จาก state ภายนอก)
 *  - onCustomerChange: (customer|null) => void
 */
function CustomerSearchSection({ customer, onCustomerChange }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError("");

    try {
      const encoded = encodeURIComponent(searchTerm.trim());
      const res = await api.get(
        `/api/customer/search?code=${encoded}&phone=${encoded}&name=${encoded}`
      );
      onCustomerChange?.(res.data);
    } catch (err) {
      setError(err?.response?.data?.detail || "ไม่พบข้อมูลลูกค้า");
      onCustomerChange?.(null);
    } finally {
      setLoading(false);
    }
  };

  const currentCustomer = customer;

  return (
    <div className="w-full rounded-lg bg-gray-50 px-10 py-4">
      <p className="text-lg font-bold text-gray-800">ข้อมูลลูกค้า</p>
      {/* ส่วนค้นหา */}
      <div className="mx-auto max-w-lg space-y-3">
        <p className=" text-gray-600">
          ค้นหาข้อมูลลูกค้าด้วยรหัส, เบอร์โทรศัพท์, หรือชื่อ
        </p>
        <div className="flex space-x-2 w-full">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="กรอกรหัส, เบอร์โทร, หรือชื่อ..."
            className="w-full rounded-lg border border-gray-300 p-3 text-sm shadow-sm"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
            
          />
          
          <button
            onClick={handleSearch}
            disabled={loading}
            className="rounded-lg bg-blue-600 px-5 py-3 text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
          >
            <SearchIcon />
          </button>

        </div>
          {customer && (
            <button
              type="button"
              title = "“ยกเลิกการเลือกลูกค้า ระบบจะบันทึกเป็นผู้ไม่ประสงค์ออกนาม”"
              onClick={() => onCustomerChange(null)}
              className="
                px-3 py-1.5
                text-xs font-semibold
                rounded-md
                bg-red-50
                text-red-600
                hover:bg-red-100
                transition
              "
            >
              ล้างข้อมูลลูกค้า
            </button>
          )}


      </div>

      {/* ส่วนผลลัพธ์ */}
      <div className="mx-auto max-w-lg mt-2">
        {loading && <Loader />}
        {error && <p className="text-center text-red-500">{error}</p>}

        {currentCustomer && (
          <div className="animate-fadeIn rounded-lg border-2 border-green-500 bg-green-50 p-2">
            <div className="flex items-center space-x-3">
              <CheckCircleIcon />
              <h4 className="text-sm font-bold text-green-800">พบข้อมูลลูกค้า</h4>
            </div>
            <div className=" pl-9">
              <p className="text-xs text-gray-700">
                <strong>ชื่อ:</strong> {currentCustomer.name}
              </p>
              <p className="text-xs text-gray-700">
                <strong>เบอร์โทร:</strong> {currentCustomer.phone}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CustomerSearchSection;
