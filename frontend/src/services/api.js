// frontend/src/services/api.js
import axios from "axios";

// ใช้ environment variable หรือ fallback ไปใช้ host ปัจจุบัน
const getBaseURL = () => {
  // ถ้ามี VITE_API_URL ใน .env ให้ใช้ค่านั้น (สำหรับ production)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // ถ้าไม่มี ให้ใช้ host ปัจจุบันแต่เปลี่ยน port เป็น 8000 อัตโนมัติ
  const protocol = window.location.protocol; // http: or https:
  const hostname = window.location.hostname; // localhost, 192.168.1.x, etc.
  return `${protocol}//${hostname}:8000`;
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 3000000,
  withCredentials: true,  // สำคัญ! ต้องส่ง Cookie ไปด้วยทุก request
});

// แนบ token (ถ้ามี) ในทุก request
api.interceptors.request.use(
  (config) => {
    try {
      const raw = localStorage.getItem("auth");
      if (raw) {
        const { token } = JSON.parse(raw) || {};
        if (token) config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {}
    return config;
  },
  (error) => Promise.reject(error)
);

// Helper function สำหรับดึงข้อมูล stock
export const getItemStock = async (sku) => {
  try {
    const response = await api.get(`/api/items/${sku}/stock`);
    return response.data;
  } catch (error) {
    console.error("Error fetching stock:", error);
    return null;
  }
};

export default api;
