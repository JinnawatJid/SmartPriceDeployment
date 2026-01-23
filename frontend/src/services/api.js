// frontend/src/services/api.js
import axios from "axios";

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
