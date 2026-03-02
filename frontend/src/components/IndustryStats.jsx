import './IndustryStats.css'

function IndustryStats({ stats, type }) {
  if (!stats || stats.length === 0) return null

  const maxCount = stats[0]?.count || 1

  return (
    <div className="industry-stats">
      <h3 className="stats-title">產業分布</h3>
      <div className="stats-bars">
        {stats.map((s) => (
          <div key={s.industry} className="bar-row">
            <span className="bar-label">{s.industry}</span>
            <div className="bar-track">
              <div
                className={`bar-fill ${type === 'up' ? 'bar-up' : 'bar-down'}`}
                style={{ width: `${(s.count / maxCount) * 100}%` }}
              />
            </div>
            <span className="bar-count">{s.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default IndustryStats
