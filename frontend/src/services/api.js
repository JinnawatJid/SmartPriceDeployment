// frontend/src/services/api.js
import axios from "axios";

// 🔧 ตั้งค่า baseURL
// 1. ถ้ามี VITE_API_BASE_URL ใน .env ให้ใช้ค่า่นั้น
// 2. ถ้าไม่มี (Production/Docker/Native) ให้ใช้ relative path ("") เพื่อให้ยิงไปที่ host/port เดียวกับที่เปิดหน้าเว็บ
//    - Docker: Nginx proxy /api -> backend:8000
//    - Native: Backend (8000) serve frontend + api
//    - Dev: Vite proxy /api -> backend:8000
const api = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || "",
  timeout: 3000000,
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

export default api;
