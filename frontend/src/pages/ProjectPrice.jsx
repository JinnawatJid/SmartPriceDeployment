import React from "react";
import { Building2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import ProjectPriceManagement from "./ProjectPriceManagement";

// รหัสพนักงานที่มีสิทธิ์เข้าถึงหน้า "ราคาโครงการ"
const ALLOWED_PROJECT_PRICE_EMPLOYEES = ['90038', '20061', '11186', '21702', '21367'];

export default function ProjectPrice() {
  const { employee } = useAuth();
  const navigate = useNavigate();

  // ตรวจสอบสิทธิ์เข้าถึง
  React.useEffect(() => {
    if (employee && !ALLOWED_PROJECT_PRICE_EMPLOYEES.includes(employee.id)) {
      // ถ้าไม่ใช่พนักงานที่อนุญาต ให้กลับไปที่ Dashboard
      navigate("/dashboard", { replace: true });
    }
  }, [employee, navigate]);

  // ถ้าไม่ใช่พนักงานที่อนุญาต ให้แสดงข้อความ
  if (employee && !ALLOWED_PROJECT_PRICE_EMPLOYEES.includes(employee.id)) {
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
