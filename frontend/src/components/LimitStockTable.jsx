import './LimitStockTable.css'

function LimitStockTable({ stocks, type }) {
  if (!stocks || stocks.length === 0) {
    return <p className="empty">無資料</p>
  }

  return (
    <div className="table-wrapper">
      <table className="stock-table">
        <thead>
          <tr>
            <th>#</th>
            <th>代碼</th>
            <th>名稱</th>
            <th>產業</th>
            <th>收盤價</th>
            <th>漲跌</th>
            <th>漲跌幅</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((s, i) => (
            <tr key={s.code}>
              <td className="cell-num">{i + 1}</td>
              <td className="cell-code">{s.code}</td>
              <td>{s.name}</td>
              <td className="cell-industry">{s.industry || '-'}</td>
              <td className="cell-num">{s.close_price.toFixed(2)}</td>
              <td className={`cell-num ${type === 'up' ? 'text-red' : 'text-blue'}`}>
                {s.price_change > 0 ? '+' : ''}{s.price_change.toFixed(2)}
              </td>
              <td className={`cell-num ${type === 'up' ? 'text-red' : 'text-blue'}`}>
                {s.change_pct > 0 ? '+' : ''}{s.change_pct.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default LimitStockTable
