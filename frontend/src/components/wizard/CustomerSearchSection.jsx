import React, { useState, useEffect, useRef } from "react";
import api from "../../services/api.js";
import Loader from "../Loader.jsx";
import NewCustomerModal from "./NewCustomerModal.jsx";

// ---------------- Icons ----------------
const CheckCircleIcon = () => (
  <svg
    className="h-5 w-5 text-green-600"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={2}
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

// ---------------- Component ----------------
function CustomerSearchSection({ customer, onCustomerChange }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState([]);
  const [openDropdown, setOpenDropdown] = useState(false);

  const [openNewCustomer, setOpenNewCustomer] = useState(false);

  // ⭐ ใช้ ref กัน search loop
  const skipSearchRef = useRef(false);

  const currentCustomer = customer;

  // โหลดข้อมูลลูกค้าเต็มหลังเลือก
  const loadCustomerFull = async (customerId) => {
    try {
      const res = await api.get(`/api/customer/search?code=${customerId}`);
      onCustomerChange(res.data);
    } catch {
      setError("โหลดข้อมูลลูกค้าไม่สำเร็จ");
    }
  };

  // ---------------- Search Effect ----------------
  useEffect(() => {
    // ⭐ ถ้ามาจากการเลือก dropdown → ข้าม search
    if (skipSearchRef.current) {
      skipSearchRef.current = false;
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
        const res = await api.get(
          `/api/customer/search-list?q=${encoded}`
        );
        setResults(res.data || []);
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

  // ---------------- Render ----------------
  return (
    <>
      <div className="mx-auto max-w-lg rounded-lg bg-gray-50 px-4 py-4">
        <p className="text-lg font-bold text-gray-800 mb-2">ข้อมูลลูกค้า</p>

        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            ค้นหาข้อมูลลูกค้าด้วยรหัส, เบอร์โทรศัพท์, หรือชื่อ
          </p>

          {/* ================= SEARCH ================= */}
          <div className="relative w-full">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="กรอกรหัส, เบอร์โทร, หรือชื่อ..."
              className="w-full rounded-lg border border-gray-300 p-3 text-sm shadow-sm"
            />

            {/* Dropdown */}
            {openDropdown && results.length > 0 && (
              <ul
                className="
                  absolute left-0 right-0 mt-1
                  rounded-lg border bg-white shadow-sm
                  max-h-[220px] overflow-y-auto z-20
                "
              >
                {results.map((c) => (
                  <li
                    key={c.id}
                    className="cursor-pointer px-3 py-2 hover:bg-blue-50"
                    onClick={() => {
                      // ⭐ กัน loop search
                      skipSearchRef.current = true;

                      onCustomerChange(c);
                      setSearchTerm(c.name);

                      setResults([]);
                      setOpenDropdown(false);

                      loadCustomerFull(c.id);
                    }}
                  >
                    <p className="text-sm font-medium text-gray-800">
                      {c.name}
                    </p>
                    <p className="text-xs text-gray-500">{c.phone}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* ================= ACTION ================= */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => {
                setOpenNewCustomer(true);
                setSearchTerm("");
                setResults([]);
                setOpenDropdown(false);
              }}
              className="text-sm bg-blue-600 hover:bg-blue-700 p-2 font-semibold rounded-lg text-white"
            >
              ลูกค้าใหม่
            </button>

            {customer && (
              <button
                type="button"
                onClick={() => {
                  onCustomerChange(null);
                  setSearchTerm("");
                  setResults([]);
                  setOpenDropdown(false);
                }}
                className="text-xs text-red-600 bg-red-50 px-3 py-1.5 rounded-md hover:bg-red-100"
              >
                ล้างข้อมูลลูกค้า
              </button>
            )}
          </div>

          {/* ================= STATUS ================= */}
          {loading && <Loader />}
          {error && <p className="text-sm text-red-500">{error}</p>}

          {currentCustomer && (
            <div className="rounded-lg border border-green-300 bg-green-50 p-3">
              <div className="flex items-center gap-2">
                <CheckCircleIcon />
                <span className="text-sm font-semibold text-green-700">
                  พบข้อมูลลูกค้า
                </span>
              </div>

              <div className="mt-1 pl-7 text-xs text-gray-700 space-y-0.5">
                <p>
                  <strong>รหัส:</strong> {currentCustomer.id}
                </p>
                <p>
                  <strong>ชื่อ:</strong> {currentCustomer.name}
                </p>
                <p>
                  <strong>เบอร์โทร:</strong> {currentCustomer.phone}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ================= NEW CUSTOMER MODAL ================= */}
      <NewCustomerModal
        open={openNewCustomer}
        onClose={() => setOpenNewCustomer(false)}
        onConfirm={(cust) => {
          onCustomerChange(cust);

          // ✅ ไม่ใส่ชื่อในช่อง search
          setSearchTerm("");
          setResults([]);
          setOpenDropdown(false);
        }}
      />
    </>
  );
}

export default CustomerSearchSection;
