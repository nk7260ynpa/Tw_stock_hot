import { useEffect, useState } from 'react'
import LimitStockTable from './components/LimitStockTable'
import IndustryStats from './components/IndustryStats'
import { fetchLimitStocks, fetchAvailableDates } from './api/hot'
import './App.css'

function App() {
  const [data, setData] = useState(null)
  const [dates, setDates] = useState([])
  const [selectedDate, setSelectedDate] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchAvailableDates()
      .then((res) => setDates(res.dates || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchLimitStocks(selectedDate || undefined)
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [selectedDate])

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">熱門話題</h1>
        <p className="app-subtitle">台股漲跌停排行與產業熱度分析</p>
      </header>

      <div className="date-picker">
        <label htmlFor="date-select">交易日期：</label>
        <select
          id="date-select"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        >
          <option value="">最新交易日</option>
          {dates.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        {data && <span className="current-date">{data.date}</span>}
      </div>

      {loading && <p className="status">載入中...</p>}
      {error && <p className="status error">載入失敗：{error}</p>}

      {data && !loading && (
        <div className="content">
          <div className="section">
            <div className="section-header limit-up-header">
              <h2>漲停板</h2>
              <span className="badge badge-up">{data.limit_up_count} 檔</span>
            </div>
            <div className="section-body">
              <IndustryStats stats={data.limit_up_industry_stats} type="up" />
              <LimitStockTable stocks={data.limit_up} type="up" />
            </div>
          </div>

          <div className="section">
            <div className="section-header limit-down-header">
              <h2>跌停板</h2>
              <span className="badge badge-down">{data.limit_down_count} 檔</span>
            </div>
            <div className="section-body">
              <IndustryStats stats={data.limit_down_industry_stats} type="down" />
              <LimitStockTable stocks={data.limit_down} type="down" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
