// src/components/ProtectedRoute.jsx
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Loader from "./Loader";

const ProtectedRoute = () => {
  const { employee, loading } = useAuth();

  // แสดงหน้า loading ขณะที่กำลังตรวจสอบ authentication
  if (loading) {
    return <Loader />;
  }

  // ถ้าไม่มี employee (ไม่ได้ login) ให้ redirect ไปหน้า login
  if (!employee) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
