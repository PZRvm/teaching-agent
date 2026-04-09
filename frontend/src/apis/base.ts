// frontend/src/apis/base.ts
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail ?? error.message
    throw new Error(detail)
  },
)
