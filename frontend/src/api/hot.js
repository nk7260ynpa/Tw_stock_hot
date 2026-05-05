/**
 * 台股熱度 API 呼叫。
 *
 * 所有呼叫都透過 `apiUrl()` helper 補上 Vite `BASE_URL` 前綴，
 * 讓 Dashboard 反向代理 `/app/hot/*` 能正確轉發到後端。
 */

/**
 * 組合 API URL。
 *
 * 將 Vite `import.meta.env.BASE_URL`（例如 `/app/hot/`）與傳入的相對路徑
 * 結合，產生瀏覽器可正確走回 Dashboard 反向代理的完整路徑。
 *
 * Args:
 *   path: 以 `/` 開頭或不以 `/` 開頭的 API 路徑。
 *
 * Returns:
 *   帶有 BASE_URL 前綴的完整路徑字串。
 */
function apiUrl(path) {
  const base = import.meta.env.BASE_URL || '/'
  return base.replace(/\/$/, '/') + path.replace(/^\//, '')
}

export async function fetchLimitStocks(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(apiUrl(`/api/hot/limit${params}`))
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchAvailableDates(limit = 30) {
  const res = await fetch(apiUrl(`/api/hot/dates?limit=${limit}`))
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchTopVolume(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(apiUrl(`/api/hot/top-volume${params}`))
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchTopValue(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(apiUrl(`/api/hot/top-value${params}`))
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchIndustryChange(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(apiUrl(`/api/hot/industry-change${params}`))
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchIndustryRatio(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(apiUrl(`/api/hot/industry-ratio${params}`))
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchIndustryStocks(date, industry) {
  const params = new URLSearchParams()
  if (date) params.set('date', date)
  params.set('industry', industry)
  const res = await fetch(apiUrl(`/api/hot/industry-stocks?${params.toString()}`))
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
