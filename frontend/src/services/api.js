// frontend/src/services/api.js
import axios from "axios";

// 🔧 ตั้งค่า baseURL
// ถ้าเป็น PROD (Vite build) ให้ใช้ relative path (ไปที่ host เดียวกัน คือ port 3200)
// ถ้าเป็น DEV ให้ใช้ localhost:4000 ตามเดิม
const baseURL = import.meta.env.PROD
  ? ""
  : (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:4000");

const api = axios.create({
  baseURL: baseURL,
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
