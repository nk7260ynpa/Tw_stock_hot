import { useEffect, useState } from 'react'
import { fetchAvailableDates } from '../api/hot'
import './RankTable.css'

/**
 * 通用排行表格元件 — 用於交易量/交易金額 TOP 10
 *
 * @param {object} props
 * @param {string} props.title - 頁面標題
 * @param {function} props.fetchData - API 呼叫函數（接收 date 參數）
 * @param {string} props.rankField - 排行依據欄位名（trade_volume 或 trade_value）
 * @param {string} props.rankLabel - 排行欄位顯示標籤
 * @param {function} props.onBack - 返回首頁回呼
 */
function RankTable({ title, fetchData, rankField, rankLabel, onBack }) {
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
    fetchData(selectedDate || undefined)
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [selectedDate, fetchData])

  const formatNumber = (num) => {
    if (num >= 1e8) return `${(num / 1e8).toFixed(2)} 億`
    if (num >= 1e4) return `${(num / 1e4).toFixed(0)} 萬`
    return num.toLocaleString()
  }

  return (
    <div className="rank-page">
      <div className="page-header">
        <button className="back-btn" onClick={onBack}>← 返回首頁</button>
        <h2 className="page-title">{title}</h2>
      </div>

      <div className="date-picker">
        <label htmlFor="rank-date-select">交易日期：</label>
        <select
          id="rank-date-select"
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
        <div className="rank-section">
          {data.stocks.length === 0 ? (
            <p className="empty">本日無資料</p>
          ) : (
            <div className="table-wrapper">
              <table className="rank-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>代碼</th>
                    <th>名稱</th>
                    <th>產業</th>
                    <th>市場</th>
                    <th>{rankLabel}</th>
                    <th>收盤價</th>
                    <th>漲跌幅</th>
                  </tr>
                </thead>
                <tbody>
                  {data.stocks.map((s, i) => {
                    const pctClass = s.change_pct > 0 ? 'text-red' : s.change_pct < 0 ? 'text-green' : ''
                    return (
                      <tr key={s.code}>
                        <td className="cell-rank">{i + 1}</td>
                        <td className="cell-code">{s.code}</td>
                        <td>
                          <a
                            href={`http://localhost:7938/?code=${s.code}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="stock-link"
                          >
                            {s.name}
                          </a>
                        </td>
                        <td className="cell-industry">{s.industry || '-'}</td>
                        <td className="cell-market">{s.market}</td>
                        <td className="cell-num">{formatNumber(s[rankField])}</td>
                        <td className="cell-num">{s.close_price.toFixed(2)}</td>
                        <td className={`cell-num ${pctClass}`}>
                          {s.change_pct > 0 ? '+' : ''}{s.change_pct.toFixed(2)}%
                        </td>
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

export default RankTable
