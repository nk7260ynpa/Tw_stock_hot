import { useEffect, useState } from 'react'
import { fetchIndustryChange, fetchAvailableDates } from '../api/hot'
import './IndustryRank.css'

function IndustryRank({ onBack, onSelectIndustry }) {
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
    fetchIndustryChange(selectedDate || undefined)
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [selectedDate])

  const maxPct = data?.industries?.length
    ? Math.max(...data.industries.map((i) => Math.abs(i.avg_change_pct)), 0.01)
    : 1

  return (
    <div className="industry-rank-page">
      <div className="page-header">
        <button className="back-btn" onClick={onBack}>← 返回首頁</button>
        <h2 className="page-title">產業漲幅排行</h2>
      </div>

      <div className="date-picker">
        <label htmlFor="industry-date-select">交易日期：</label>
        <select
          id="industry-date-select"
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
        <div className="industry-rank-section">
          <p className="industry-rank-note">僅統計 TWSE 上市股票（TPEX 無產業分類資料）</p>
          {data.industries.length === 0 ? (
            <p className="empty">本日無資料</p>
          ) : (
            <div className="industry-bars">
              {data.industries.map((item, idx) => {
                const isPositive = item.avg_change_pct >= 0
                const barWidth = (Math.abs(item.avg_change_pct) / maxPct) * 100
                return (
                  <div key={item.industry} className="industry-bar-row">
                    <span className="industry-bar-rank">{idx + 1}</span>
                    <span
                      className="industry-bar-name industry-clickable"
                      onClick={() => onSelectIndustry && onSelectIndustry(item.industry, data.date)}
                    >
                      {item.industry}
                    </span>
                    <div className="industry-bar-track">
                      <div
                        className={`industry-bar-fill ${isPositive ? 'bar-positive' : 'bar-negative'}`}
                        style={{ width: `${Math.max(barWidth, 2)}%` }}
                      />
                    </div>
                    <span className={`industry-bar-pct ${isPositive ? 'text-red' : 'text-green'}`}>
                      {isPositive ? '+' : ''}{item.avg_change_pct.toFixed(2)}%
                    </span>
                    <span className="industry-bar-count">{item.stock_count} 檔</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default IndustryRank
