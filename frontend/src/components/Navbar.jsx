// src/components/Navbar.jsx
import React from "react";
import { useAuth } from "../hooks/useAuth.js";
import { Link } from "react-router-dom";

function Navbar() {
  const { employee, logout } = useAuth();

  // ดึงชื่อย่อ (ตัวอักษรแรก)
  const userInitial = employee?.name ? employee.name[0] : "?";

  return (
    <nav className="sticky top-0 z-10 w-full bg-white shadow-md">
      <div className="mx-auto flex h-[75px] max-w-full items-center justify-between px-6 lg:px-10">
        {/* ส่วนโลโก้ */}
        <Link to="/dashboard" className="flex items-center" aria-label="ไปหน้าหลัก">
          <img src="/assets/favicon.png" className="h-16 w-auto" />
        </Link>

        {/* ส่วนผู้ใช้งาน */}
        <div className="flex items-center space-x-4">
          <Link to="/dashboard" className="text-sm font-bold text-gray-700 hover:text-blue-600">
            หน้าหลัก
          </Link>
          <div className="h-6 w-px bg-gray-300"></div>

          {/* Avatar */}
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-600 text-xl font-bold text-white">
            {userInitial}
          </div>

          {/* ชื่อและรหัส */}
          <div className="hidden md:block">
            <div className="text-xs font-bold text-gray-800">{employee?.name || "Loading..."}</div>
            <div className="text-xs font-bold text-gray-500">{employee?.id || "..."}</div>
          </div>

          {/* ปุ่ม Logout */}
          <button
            onClick={logout}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white shadow-sm transition-all hover:bg-red-700"
          >
            ออกจากระบบ
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
