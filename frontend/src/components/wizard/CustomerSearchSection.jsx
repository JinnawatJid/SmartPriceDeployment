// src/components/wizard/CustomerSearchSection.jsx
import React, { useState } from "react";
import api from "../../services/api.js";
import Loader from "../Loader.jsx";
import { useEffect } from "react";


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
  const [results, setResults] = useState([]);
  const [openDropdown, setOpenDropdown] = useState(false);
  const [selectedFromDropdown, setSelectedFromDropdown] = useState(false);


  const currentCustomer = customer;
  const loadCustomerFull = async (customerId) => {
    try {
      const res = await api.get(`/api/customer/search?code=${customerId}`);
      onCustomerChange(res.data); // ⭐ ตัวนี้คือ object เต็ม
    } catch {
      setError("โหลดข้อมูลลูกค้าไม่สำเร็จ");
    }
  };


  useEffect(() => {
    // ❗ ถ้าเพิ่งเลือกจาก dropdown → ไม่ต้อง search
    if (selectedFromDropdown) {
      setSelectedFromDropdown(false);
      return;
    }

    if (!searchTerm.trim()) {
      setResults([]);
      setOpenDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      setError("");

      try {
        const encoded = encodeURIComponent(searchTerm.trim());
        const res = await api.get(`/api/customer/search-list?q=${encoded}`);
        setResults(res.data);
        setOpenDropdown(true);
      } catch {
        setResults([]);
        setOpenDropdown(false);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);



  return (
    <div className="w-full rounded-lg bg-gray-50 px-10 py-4">
      <p className="text-lg font-bold text-gray-800">ข้อมูลลูกค้า</p>
      {/* ส่วนค้นหา */}
      <div className="mx-auto max-w-lg space-y-3">
        <p className=" text-gray-600">
          ค้นหาข้อมูลลูกค้าด้วยรหัส, เบอร์โทรศัพท์, หรือชื่อ
        </p>
        <div className="relative w-full">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="กรอกรหัส, เบอร์โทร, หรือชื่อ..."
            className="w-full rounded-lg border border-gray-300 p-3 text-sm shadow-sm"

            
          />

          {openDropdown && results.length > 0 && (
            <div className="relative">
              <ul
                className="
                  absolute z-20 mt-1 w-full
                  rounded-md border bg-white shadow-lg
                  max-h-[220px] overflow-y-auto
                "
              >
                {results.map((c) => (
                  <li
                    key={c.id}
                    className="cursor-pointer px-3 py-2 hover:bg-blue-50"
                    onClick={() => {
                      setSelectedFromDropdown(true); // ⭐ สำคัญ
                      onCustomerChange(c);
                      setOpenDropdown(false);
                      setResults([]);
                      setSearchTerm(c.name);
                      loadCustomerFull(c.id);
                  }}
                  >
                    <p className="text-sm font-medium text-gray-800">{c.name}</p>
                    <p className="text-xs text-gray-500">{c.phone}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}


          
          


        </div>
          {customer && (
            <button
              type="button"
              title="“ยกเลิกการเลือกลูกค้า ระบบจะบันทึกเป็นผู้ไม่ประสงค์ออกนาม”"
              onClick={() => {
                onCustomerChange(null);

                // ⭐ reset search state
                setSearchTerm("");
                setResults([]);
                setOpenDropdown(false);
              }}
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
