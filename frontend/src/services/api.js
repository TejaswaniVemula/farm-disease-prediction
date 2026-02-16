import axios from "axios";
const API_BASE = import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000";
export const api = axios.create({ baseURL: API_BASE, timeout: 20000 });
export async function getSymptoms(){ const r=await api.get("/symptoms"); return r.data?.symptoms ?? []; }
export async function predict(payload){ const r=await api.post("/predict", payload); return r.data; }
