// src/config.js
export const CONFIG = {
  // Set VITE_GOOGLE_CLIENT_ID in frontend/.env.local
  GOOGLE_CLIENT_ID: import.meta.env.VITE_GOOGLE_CLIENT_ID || "",
  // Relative path — Vite proxy forwards /api → http://localhost:8000/api
  API_BASE: "/api/v1",
};
