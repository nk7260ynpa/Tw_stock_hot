import { useState } from 'react'
import HotDashboard from './components/HotDashboard'
import LimitStocks from './components/LimitStocks'
import RankTable from './components/RankTable'
import IndustryRank from './components/IndustryRank'
import { fetchTopVolume, fetchTopValue } from './api/hot'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState('home')

  const handleSelectView = (view) => {
    setCurrentView(view)
  }

  const handleBackToHome = () => {
    setCurrentView('home')
  }

  if (currentView === 'limit') {
    return (
      <div className="app">
        <LimitStocks onBack={handleBackToHome} />
      </div>
    )
  }

  if (currentView === 'volume') {
    return (
      <div className="app">
        <RankTable
          title="交易量 TOP 10"
          fetchData={fetchTopVolume}
          rankField="trade_volume"
          rankLabel="成交量"
          onBack={handleBackToHome}
        />
      </div>
    )
  }

  if (currentView === 'value') {
    return (
      <div className="app">
        <RankTable
          title="交易金額 TOP 10"
          fetchData={fetchTopValue}
          rankField="trade_value"
          rankLabel="成交金額"
          onBack={handleBackToHome}
        />
      </div>
    )
  }

  if (currentView === 'industry') {
    return (
      <div className="app">
        <IndustryRank onBack={handleBackToHome} />
      </div>
    )
  }

  return (
    <div className="app">
      <HotDashboard onSelectView={handleSelectView} />
    </div>
  )
}

export default App
