/**
 * 台股熱度 API 呼叫
 */

export async function fetchLimitStocks(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(`/api/hot/limit${params}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchAvailableDates(limit = 30) {
  const res = await fetch(`/api/hot/dates?limit=${limit}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchTopVolume(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(`/api/hot/top-volume${params}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchTopValue(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(`/api/hot/top-value${params}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchIndustryChange(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(`/api/hot/industry-change${params}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchIndustryRatio(date) {
  const params = date ? `?date=${date}` : ''
  const res = await fetch(`/api/hot/industry-ratio${params}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
