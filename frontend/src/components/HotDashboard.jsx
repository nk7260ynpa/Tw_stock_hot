import './HotDashboard.css'

const cards = [
  {
    key: 'limit',
    icon: '\u26A1',
    title: '\u6F32\u8DCC\u505C\u6392\u884C',
    description: '\u4ECA\u65E5\u4E0A\u5E02\u80A1\u7968\u6F32\u505C\u677F\u8207\u8DCC\u505C\u677F\u6E05\u55AE\u53CA\u7522\u696D\u5206\u5E03',
  },
  {
    key: 'volume',
    icon: '\uD83D\uDCCA',
    title: '\u4EA4\u6613\u91CF TOP 10',
    description: '\u4ECA\u65E5\u6210\u4EA4\u91CF\u6700\u5927\u768410\u6A94\u80A1\u7968',
  },
  {
    key: 'value',
    icon: '\uD83D\uDCB0',
    title: '\u4EA4\u6613\u984D TOP 10',
    description: '\u4ECA\u65E5\u6210\u4EA4\u91D1\u984D\u6700\u9AD8\u768410\u6A94\u80A1\u7968',
  },
  {
    key: 'industry',
    icon: '\uD83C\uDFED',
    title: '\u7522\u696D\u6F32\u5E45\u6392\u884C',
    description: '\u5404\u7522\u696D\u5E73\u5747\u6F32\u8DCC\u5E45\u524D10\u540D\u6392\u884C',
  },
  {
    key: 'industry-ratio',
    icon: '\uD83D\uDCC8',
    title: '\u7522\u696D\u6F32\u5E45\u4F54\u6BD4\u6392\u884C',
    description: '\u5404\u7522\u696D\u6F32\u8DCC\u516C\u53F8\u6578\u4F54\u6BD4\u5206\u6790',
  },
]

function HotDashboard({ onSelectView }) {
  return (
    <>
      <header className="dashboard-header">
        <h1 className="dashboard-title">台股熱度平台</h1>
        <p className="dashboard-subtitle">漲跌停排行 / 交易量排行 / 交易額排行 / 產業漲幅 / 產業佔比</p>
      </header>
      <main>
        <div className="card-grid">
          {cards.map((card) => (
            <div
              key={card.key}
              className="dashboard-card"
              onClick={() => onSelectView(card.key)}
            >
              <span className="card-icon">{card.icon}</span>
              <h3 className="card-title">{card.title}</h3>
              <p className="card-description">{card.description}</p>
            </div>
          ))}
        </div>
      </main>
    </>
  )
}

export default HotDashboard
