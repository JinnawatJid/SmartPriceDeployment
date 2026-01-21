// src/pages/Login.jsx (NEW DESIGN)
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";

// ไอคอนสำหรับช่อง Input (เป็น optional แต่ช่วยให้สวยขึ้น)
const UserIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    className="h-5 w-5 text-gray-400"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A1.75 1.75 0 0 1 17.25 22.5h-10.5a1.75 1.75 0 0 1-1.749-2.382Z"
    />
  </svg>
);

function Login() {
  const [employeeCode, setEmployeeCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const auth = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!employeeCode) {
      setError("กรุณากรอกรหัสพนักงาน");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await auth.login(employeeCode);
      navigate("/");
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "รหัสพนักงานไม่ถูกต้อง");
    }
    setLoading(false);
  };

  return (
    // 1. พื้นหลัง Gradient เต็มจอ
    <div className="flex min-h-screen w-full items-center justify-center bg-white">
      {/* 2. การ์ด Login สีขาวตรงกลาง */}
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-2xl">
        {/* 3. ส่วน Logo */}
        <div className="flex justify-center mb-6">
          {/* ❗️ หมายเหตุ: 
            ให้คุณนำไฟล์โลโก้ (เช่น logo.png) ไปไว้ในโฟลเดอร์ /public
            แล้วอ้างอิงตามนี้ครับ
          */}
          <img src="/assets/TANGNAMGLASSy.png" alt="Smart Pricing Logo" className="h-25 " />
        </div>

        {/* 4. หัวข้อ "Login" */}
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-800">Login</h1>

        {/* 5. ฟอร์ม */}
        <form onSubmit={handleSubmit} className="w-full">
          <div>
            <label htmlFor="employeeCode" className="mb-2 block text-sm font-medium text-gray-600">
              Employee Code
            </label>

            {/* 6. ช่อง Input (แบบมีไอคอน) */}
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <UserIcon />
              </span>
              <input
                id="employeeCode"
                type="text"
                value={employeeCode}
                onChange={(e) => setEmployeeCode(e.target.value)}
                placeholder="รหัสพนักงานของคุณ"
                className="w-full rounded-lg border border-gray-300 bg-gray-50 p-3 pl-10 text-gray-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* 7. แสดง Error (ถ้ามี) */}
          {error && <p className="mt-3 text-center text-sm text-red-600">{error}</p>}

          {/* 8. ปุ่ม Login (สี Gradient) */}
          <div className="mt-8">
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 py-3 font-bold text-white shadow-md transition-all duration-300 hover:from-blue-600 hover:to-blue-700 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-70"
            >
              {loading ? "กำลังตรวจสอบ..." : "Login"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Login;
