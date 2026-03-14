import React, { useState, useEffect } from "react";
import { Building2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import api from "../services/api.js";
import ProjectPriceManagement from "./ProjectPriceManagement";

// รหัสพนักงานที่มีสิทธิ์เข้าถึงหน้า "ราคาโครงการ"
const ALLOWED_PROJECT_PRICE_EMPLOYEES = ['90038', '20061', '11186', '21702', '21367', '20614', '20194', '20785', '20093', '20686', '16647', '20595', '20091', '16053', '16654', '16725', '10011', '20040', '10254', '16646', '16702', '20037', '16723', '20974', '20129', '10073', '20084', '21094', '20813'];

export default function ProjectPrice() {
  const { employee } = useAuth();
  const navigate = useNavigate();
  const [allowedEmployees, setAllowedEmployees] = useState(ALLOWED_PROJECT_PRICE_EMPLOYEES);

  // โหลดสิทธิ์พนักงานจาก backend
  useEffect(() => {
    const fetchEmployeeAccess = async () => {
      try {
        const res = await api.get("/api/admin/employee-access");
        setAllowedEmployees(res.data.allowed_project_price_employees);
      } catch (err) {
        console.error("Failed to fetch employee access:", err);
      }
    };
    fetchEmployeeAccess();
  }, []);

  // ตรวจสอบสิทธิ์เข้าถึง
  useEffect(() => {
    if (employee && !allowedEmployees.includes(employee.id)) {
      // ถ้าไม่ใช่พนักงานที่อนุญาต ให้กลับไปที่ Dashboard
      navigate("/dashboard", { replace: true });
    }
  }, [employee, allowedEmployees, navigate]);

  // ถ้าไม่ใช่พนักงานที่อนุญาต ให้แสดงข้อความ
  if (employee && !allowedEmployees.includes(employee.id)) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h2 className="text-xl font-bold text-red-800 mb-2">ไม่มีสิทธิ์เข้าถึง</h2>
          <p className="text-red-600">ขออภัย คุณไม่มีสิทธิ์เข้าถึงหน้านี้</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <Building2 className="w-8 h-8 text-teal-600" />
        <h1 className="text-2xl font-bold">ราคาโครงการ</h1>
      </div>

      <ProjectPriceManagement />
    </div>
  );
}
