const BASE_URL = import.meta.env.VITE_API_URL

async function apiFetch(path, params = {}) {
  const prefix = path === '/health' ? '' : '/api'
  const url = new URL(`${BASE_URL}${prefix}${path}`)
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(item => url.searchParams.append(key, item))
      } else {
        url.searchParams.set(key, value)
      }
    }
  })
  const res = await fetch(url.toString())
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json()
}

export function getAreas() {
  return apiFetch('/areas')
}

export function getPeriodicos(params = {}) {
  return apiFetch('/periodicos', params)
}

export function getDistribuicao(area) {
  return apiFetch(`/areas/${encodeURIComponent(area)}/distribuicao`)
}