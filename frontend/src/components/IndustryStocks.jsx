import { useEffect, useState } from 'react'
import { fetchIndustryStocks } from '../api/hot'
import './IndustryStocks.css'

/**
 * 產業股票明細元件 — 顯示指定產業的所有股票交易資訊
 *
 * @param {object} props
 * @param {string} props.industry - 產業名稱
 * @param {string} props.date - 查詢日期
 * @param {function} props.onBack - 返回回呼
 * @param {string} props.backLabel - 返回按鈕文字
 */
function IndustryStocks({ industry, date, onBack, backLabel }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchIndustryStocks(date, industry)
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [date, industry])

  const formatNumber = (num) => {
    if (num >= 1e8) return `${(num / 1e8).toFixed(2)} 億`
    if (num >= 1e4) return `${(num / 1e4).toFixed(0)} 萬`
    return num.toLocaleString()
  }

  return (
    <div className="industry-stocks-page">
      <div className="page-header">
        <button className="back-btn" onClick={onBack}>
          &larr; {backLabel || '返回'}
        </button>
        <h2 className="page-title">{industry} - 個股明細</h2>
      </div>

      {data && (
        <div className="industry-stocks-info">
          <span className="info-date">日期：{data.date}</span>
          <span className="info-count">共 {data.stock_count} 檔</span>
        </div>
      )}

      {loading && <p className="status">載入中...</p>}
      {error && <p className="status error">載入失敗：{error}</p>}

      {data && !loading && (
        <div className="industry-stocks-section">
          {data.stocks.length === 0 ? (
            <p className="empty">本日無資料</p>
          ) : (
            <div className="table-wrapper">
              <table className="industry-stocks-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>代碼</th>
                    <th>名稱</th>
                    <th>開盤價</th>
                    <th>收盤價</th>
                    <th>漲跌</th>
                    <th>漲跌幅</th>
                    <th>成交量</th>
                    <th>成交金額</th>
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
                            href={`http://localhost:7938/stock/${s.code}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="stock-link"
                          >
                            {s.name}
                          </a>
                        </td>
                        <td className="cell-num">{s.open_price.toFixed(2)}</td>
                        <td className="cell-num">{s.close_price.toFixed(2)}</td>
                        <td className={`cell-num ${pctClass}`}>
                          {s.price_change > 0 ? '+' : ''}{s.price_change.toFixed(2)}
                        </td>
                        <td className={`cell-num ${pctClass}`}>
                          {s.change_pct > 0 ? '+' : ''}{s.change_pct.toFixed(2)}%
                        </td>
                        <td className="cell-num">{formatNumber(s.trade_volume)}</td>
                        <td className="cell-num">{formatNumber(s.trade_value)}</td>
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

export default IndustryStocks
