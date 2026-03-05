import { useEffect, useState } from 'react'
import { fetchIndustryRatio, fetchAvailableDates } from '../api/hot'
import './IndustryRatioRank.css'

function IndustryRatioRank({ onBack, onSelectIndustry }) {
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
    fetchIndustryRatio(selectedDate || undefined)
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
    ? Math.max(...data.industries.map((i) => Math.abs(i.ratio_pct)), 0.01)
    : 1

  return (
    <div className="industry-ratio-page">
      <div className="page-header">
        <button className="back-btn" onClick={onBack}>&larr; 返回首頁</button>
        <h2 className="page-title">產業漲幅佔比排行</h2>
      </div>

      <div className="date-picker">
        <label htmlFor="ratio-date-select">交易日期：</label>
        <select
          id="ratio-date-select"
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
        <div className="ratio-section">
          <p className="ratio-note">
            僅統計 TWSE 上市股票（TPEX 無產業分類資料）&emsp;|&emsp;
            佔比公式：(漲的公司數 - 跌的公司數) / 產業總公司數
          </p>
          {data.industries.length === 0 ? (
            <p className="empty">本日無資料</p>
          ) : (
            <div className="ratio-table-wrapper">
              <table className="ratio-table">
                <thead>
                  <tr>
                    <th className="col-rank">#</th>
                    <th className="col-name">產業</th>
                    <th className="col-bar">漲幅佔比</th>
                    <th className="col-pct">佔比(%)</th>
                    <th className="col-num">漲</th>
                    <th className="col-num">跌</th>
                    <th className="col-num">總計</th>
                  </tr>
                </thead>
                <tbody>
                  {data.industries.map((item, idx) => {
                    const isPositive = item.ratio_pct >= 0
                    const barWidth = (Math.abs(item.ratio_pct) / maxPct) * 100
                    return (
                      <tr key={item.industry}>
                        <td className="col-rank">{idx + 1}</td>
                        <td
                          className="col-name industry-ratio-clickable"
                          onClick={() => onSelectIndustry && onSelectIndustry(item.industry, data.date)}
                        >
                          {item.industry}
                        </td>
                        <td className="col-bar">
                          <div className="ratio-bar-track">
                            <div
                              className={`ratio-bar-fill ${isPositive ? 'bar-positive' : 'bar-negative'}`}
                              style={{ width: `${Math.max(barWidth, 2)}%` }}
                            />
                          </div>
                        </td>
                        <td className={`col-pct ${isPositive ? 'text-red' : 'text-green'}`}>
                          {isPositive ? '+' : ''}{item.ratio_pct.toFixed(2)}%
                        </td>
                        <td className="col-num text-red">{item.up_count}</td>
                        <td className="col-num text-green">{item.down_count}</td>
                        <td className="col-num">{item.total_count}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default IndustryRatioRank
