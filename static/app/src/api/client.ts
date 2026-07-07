import axios, { AxiosHeaders } from 'axios'

const readCookie = (name: string) => {
  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${encodeURIComponent(name)}=`))

  return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : undefined
}

export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  withCredentials: true
})

httpClient.interceptors.request.use((config) => {
  const csrfToken = readCookie('csrftoken')

  if (csrfToken) {
    const headers = AxiosHeaders.from(config.headers)
    headers.set('X-CSRFToken', csrfToken)
    config.headers = headers
  }

  return config
})

httpClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
)
