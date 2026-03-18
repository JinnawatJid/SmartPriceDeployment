// src/pages/Login.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Login() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleStartUsing = async () => {
    setError("");
    setLoading(true);
    
    try {
      // เรียก Backend ให้อ่าน UXP cookie และสร้าง auth_token
      const response = await api.post("/api/login/init");
      console.log("Login success:", response.data);
      
      // Reload หน้าเพื่อให้ AuthContext อ่าน cookie ใหม่
      window.location.href = "/dashboard";
    } catch (err) {
      console.error("Login error:", err);
      setError(err.response?.data?.detail || "ไม่สามารถเข้าสู่ระบบได้ - กรุณา login ผ่าน UXP Portal ก่อน");
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100">
      <div className="w-full max-w-md rounded-3xl bg-white p-10 shadow-2xl">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <img src="/assets/favicon.png" alt="Smart Pricing Logo" className="h-24" />
        </div>

        {/* หัวข้อ */}
        <h1 className="mb-3 text-center text-3xl font-bold text-gray-800">
          Smart Pricing
        </h1>
        <p className="mb-8 text-center text-gray-600">
          ระบบจัดการใบเสนอราคา
        </p>

        {/* แสดง Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-sm text-red-700 text-center">{error}</p>
          </div>
        )}

        {/* ปุ่มเริ่มใช้งาน */}
        <button
          onClick={handleStartUsing}
          disabled={loading}
          className="w-full rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 py-4 font-bold text-white text-lg shadow-lg transition-all duration-300 hover:from-blue-600 hover:to-blue-700 hover:shadow-xl hover:scale-[1.02] focus:outline-none focus:ring-4 focus:ring-blue-300 disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              กำลังเข้าสู่ระบบ...
            </span>
          ) : (
            "เริ่มใช้งาน"
          )}
        </button>

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-gray-500">
          กดปุ่มเพื่อเข้าสู่ระบบ Smart Pricing
        </p>
      </div>
    </div>
  );
}

export default Login;
