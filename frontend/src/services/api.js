// frontend/src/services/api.js
import axios from "axios";

// ใช้ host ปัจจุบันแต่เปลี่ยน port เป็น 8000 อัตโนมัติ
const getBaseURL = () => {
  const protocol = window.location.protocol; // http: or https:
  const hostname = window.location.hostname; // localhost, 192.168.1.x, etc.
  return `${protocol}//${hostname}:8000`;
};

const api = axios.create({
  baseURL: getBaseURL(),
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
