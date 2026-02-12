import axios from 'axios'
import { getTelegramInitData } from './telegram'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Telegram-Init-Data': getTelegramInitData()
  }
})
