/**
 * 漲跌停 API 呼叫
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
