// frontend/src/services/api.js
import axios from "axios";

// 🔧 ตั้งค่า baseURL จาก .env ถ้ามี (Vite) หรือ fallback เป็น localhost:4000
const api = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || "http://127.0.0.1:4000",
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
    } catch {
      // เงียบไว้
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
