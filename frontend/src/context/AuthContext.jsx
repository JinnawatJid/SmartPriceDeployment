// src/context/AuthContext.jsx
import { createContext, useState, useEffect } from 'react';
import api from '../services/api';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [employee, setEmployee] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // (Optional) ควรมีการ verify token กับ backend
      // แต่ในที่นี้ เราจะแค่ดึงข้อมูลพนักงานจาก localStorage ถ้ามี
      const storedEmp = localStorage.getItem('employee');
      if (storedEmp) {
        setEmployee(JSON.parse(storedEmp));
      }
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, [token]);

  const login = async (employeeCode) => {
    const response = await api.post('/api/login', { employeeCode });
    const { token, employee } = response.data;
    setToken(token);
    setEmployee(employee);
    localStorage.setItem('token', token);
    localStorage.setItem('employee', JSON.stringify(employee));
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  const logout = () => {
    setToken(null);
    setEmployee(null);
    localStorage.removeItem('token');
    localStorage.removeItem('employee');
    delete api.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ employee, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};