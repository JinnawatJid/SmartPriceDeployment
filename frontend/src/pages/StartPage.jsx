// src/pages/StartPage.jsx
import React, { useState } from "react";

function StartPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleStart = async () => {
    setLoading(true);
    setError("");

    try {
      // เรียก API เพื่อเปิด Chrome debug mode
      const response = await fetch("http://localhost:8000/api/chrome-debug/start", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("ไม่สามารถเปิด Chrome debug mode ได้");
      }

      // ปิด tab นี้หลังจาก 2 วินาที (ถ้าเปิดด้วย JavaScript)
      setTimeout(() => {
        window.close();
      }, 2000);

    } catch (err) {
      console.error("Error starting Chrome debug:", err);
      setError("เกิดข้อผิดพลาด: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <div className="w-full max-w-md rounded-2xl bg-white p-10 shadow-2xl">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <img 
            src="/assets/favicon.png" 
            alt="Smart Pricing Logo" 
            className="h-32" 
          />
        </div>

        {/* Title */}
        <h1 className="mb-3 text-center text-3xl font-bold text-gray-800">
          Smart Pricing System
        </h1>
        <p className="mb-8 text-center text-sm text-gray-600">
          ระบบจัดการใบเสนอราคาอัจฉริยะ
        </p>

        {/* Start Button */}
        <button
          onClick={handleStart}
          disabled={loading}
          className="w-full rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 py-4 text-lg font-bold text-white shadow-lg transition-all duration-300 hover:from-blue-600 hover:to-blue-700 hover:shadow-xl hover:scale-105 focus:outline-none focus:ring-4 focus:ring-blue-300 disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg 
                className="animate-spin h-5 w-5 text-white" 
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24"
              >
                <circle 
                  className="opacity-25" 
                  cx="12" 
                  cy="12" 
                  r="10" 
                  stroke="currentColor" 
                  strokeWidth="4"
                />
                <path 
                  className="opacity-75" 
                  fill="currentColor" 
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              กำลังเปิด Chrome...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24" 
                strokeWidth={2.5} 
                stroke="currentColor" 
                className="w-6 h-6"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" 
                />
              </svg>
              เริ่มต้นใช้งาน
            </span>
          )}
        </button>

        {/* Error Message */}
        {error && (
          <div className="mt-4 rounded-lg bg-red-50 border border-red-200 p-3">
            <p className="text-center text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Info */}
        <div className="mt-8 rounded-lg bg-blue-50 border border-blue-200 p-4">
          <p className="text-xs text-blue-800 text-center">
            <span className="font-semibold">💡 คำแนะนำ:</span> เมื่อกดปุ่มเริ่มต้น Chrome จะเปิดขึ้นมาพร้อมระบบ Dynamics 365 และ Smart Pricing
          </p>
        </div>
      </div>
    </div>
  );
}

export default StartPage;
