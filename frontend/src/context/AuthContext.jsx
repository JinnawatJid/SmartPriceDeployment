// src/context/AuthContext.jsx
import { createContext, useState, useEffect } from "react";
import api from "../services/api";

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [employee, setEmployee] = useState(null);
  const [loading, setLoading] = useState(true);

  // ตรวจสอบ authentication เมื่อ component mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // เรียก /login/me เพื่อดึงข้อมูลผู้ใช้จาก cookie
      const response = await api.get("/api/login/me");
      setEmployee(response.data.employee);
    } catch (error) {
      console.log("Not authenticated or token expired");
      setEmployee(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (employeeCode) => {
    const response = await api.post("/api/login", { employeeCode });
    const { employee } = response.data;
    setEmployee(employee);
    // Cookie ถูกสร้างโดย backend อัตโนมัติ
  };

  const logout = async () => {
    try {
      await api.post("/api/login/logout");
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      setEmployee(null);
    }
  };

  return (
    <AuthContext.Provider value={{ employee, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};
