import React, { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const sections = ['Dashboard', 'Markets', 'Crypto', 'TON', 'NFT', 'Portfolio', 'Education', 'News', 'Settings']

const palette = ['#00B894', '#0984E3', '#6C5CE7', '#E17055', '#D63031', '#fdcb6e', '#55efc4']

const safeGet = async (path: string, fallback: any) => {
  try {
    const res = await api.get(path)
    return res.data
  } catch {
    return fallback
  }
}

const Card: React.FC<{ title: string; subtitle?: string; children: React.ReactNode }> = ({ title, subtitle, children }) => (
  <div className="card">
    <div className="card-head">
      <div>
        <h3>{title}</h3>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
    </div>
    {children}
  </div>
)

export default function App() {
  const [active, setActive] = useState('Dashboard')
  const [dashboard, setDashboard] = useState<any>(null)
  const [marketsStocks, setMarketsStocks] = useState<any>(null)
  const [marketsEtfs, setMarketsEtfs] = useState<any>(null)
  const [marketsForex, setMarketsForex] = useState<any>(null)
  const [cryptoTop, setCryptoTop] = useState<any>(null)
  const [tonPrice, setTonPrice] = useState<any>(null)
  const [tonProjects, setTonProjects] = useState<any>(null)
  const [tonCollections, setTonCollections] = useState<any>(null)
  const [nftCollections, setNftCollections] = useState<any>(null)
  const [nftFloors, setNftFloors] = useState<any>(null)
  const [portfolio, setPortfolio] = useState<any>(null)
  const [portfolioItems, setPortfolioItems] = useState<any>(null)
  const [lessons, setLessons] = useState<any>(null)
  const [glossary, setGlossary] = useState<any>(null)
  const [newsHeadlines, setNewsHeadlines] = useState<any>(null)
  const [profile, setProfile] = useState<any>(null)

  useEffect(() => {
    const load = async () => {
      const [
        dash,
        stocksTop,
        etfsTop,
        forexTop,
        cryptoTopRes,
        tonPriceRes,
        tonProjectsRes,
        tonCollectionsRes,
        nftCollectionsRes,
        nftFloorsRes,
        portfolioRes,
        portfolioItemsRes,
        lessonsRes,
        glossaryRes,
        newsRes,
        profileRes
      ] = await Promise.all([
        safeGet('/api/dashboard', {}),
        safeGet('/api/markets/stocks/top?sort=gainers', {}),
        safeGet('/api/markets/etfs/top?sort=volume', {}),
        safeGet('/api/markets/forex/top?sort=gainers', {}),
        safeGet('/api/crypto/top?limit=10', {}),
        safeGet('/api/ton/price', {}),
        safeGet('/api/ton/projects?limit=8', {}),
        safeGet('/api/ton/nft/collections', {}),
        safeGet('/api/nft/collections', {}),
        safeGet('/api/nft/floors', {}),
        safeGet('/api/portfolio', {}),
        safeGet('/api/portfolio/items', {}),
        safeGet('/api/education/lessons', {}),
        safeGet('/api/education/glossary', {}),
        safeGet('/api/news/headlines', {}),
        safeGet('/api/user/profile', {})
      ])
      setDashboard(dash)
      setMarketsStocks(stocksTop)
      setMarketsEtfs(etfsTop)
      setMarketsForex(forexTop)
      setCryptoTop(cryptoTopRes)
      setTonPrice(tonPriceRes)
      setTonProjects(tonProjectsRes)
      setTonCollections(tonCollectionsRes)
      setNftCollections(nftCollectionsRes)
      setNftFloors(nftFloorsRes)
      setPortfolio(portfolioRes)
      setPortfolioItems(portfolioItemsRes)
      setLessons(lessonsRes)
      setGlossary(glossaryRes)
      setNewsHeadlines(newsRes)
      setProfile(profileRes)
    }
    load()
  }, [])

  const allocation = portfolio?.allocation || { Crypto: 2, Stocks: 3 }
  const allocationData = Object.keys(allocation).map((k) => ({ name: k, value: Number(allocation[k]) || 1 }))

  const chartData = useMemo(() => ([
    { name: 'Mon', value: 400 },
    { name: 'Tue', value: 300 },
    { name: 'Wed', value: 500 },
    { name: 'Thu', value: 450 },
    { name: 'Fri', value: 520 }
  ]), [])

  return (
    <div className="app">
      <header className="header">
        <div className="brand">InvestHub Mini</div>
        <div className="sub">Unified Telegram + Discord Investing Hub</div>
        <nav className="nav">
          {sections.map((s) => (
            <button key={s} className={s === active ? 'tab active' : 'tab'} onClick={() => setActive(s)}>
              {s}
            </button>
          ))}
        </nav>
      </header>

      <main className="content">
        {active === 'Dashboard' && (
          <section className="grid">
            <Card title="Highlights" subtitle="Market pulse & quick stats">
              <div className="list">
                {dashboard?.highlights?.map((h: any, i: number) => (
                  <div key={i} className="list-row">
                    <span>{h.label}</span>
                    <strong>{h.value}</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Market Pulse" subtitle="Weekly activity (demo)">
              <div className="chart">
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={chartData}>
                    <XAxis dataKey="name" stroke="#CAD3F5" />
                    <YAxis stroke="#CAD3F5" />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#00B894" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card title="Quick Prices" subtitle="Top crypto tickers">
              <div className="list">
                {dashboard?.prices && Object.keys(dashboard.prices).map((k: string) => (
                  <div key={k} className="list-row">
                    <span>{k.toUpperCase()}</span>
                    <strong>{dashboard.prices[k]}</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Allocation" subtitle="Your portfolio mix">
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie dataKey="value" data={allocationData} innerRadius={40} outerRadius={70}>
                    {allocationData.map((_, i) => (
                      <Cell key={i} fill={palette[i % palette.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </section>
        )}

        {active === 'Markets' && (
          <section className="grid">
            <Card title="Top Stocks" subtitle="Gainers right now">
              <div className="list">
                {marketsStocks?.items?.slice(0, 6).map((s: any) => (
                  <div key={s.symbol} className="list-row">
                    <span>{s.symbol}</span>
                    <strong>${Number(s.price || 0).toFixed(2)}</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Top ETFs" subtitle="Sorted by volume">
              <div className="list">
                {marketsEtfs?.items?.slice(0, 6).map((s: any) => (
                  <div key={s.symbol} className="list-row">
                    <span>{s.symbol}</span>
                    <strong>${Number(s.price || 0).toFixed(2)}</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Forex Top Pairs" subtitle="Major FX moves">
              <div className="list">
                {marketsForex?.items?.slice(0, 6).map((s: any) => (
                  <div key={s.pair} className="list-row">
                    <span>{s.pair}</span>
                    <strong>{Number(s.rate || 0).toFixed(5)}</strong>
                  </div>
                ))}
              </div>
            </Card>
          </section>
        )}

        {active === 'Crypto' && (
          <section className="grid">
            <Card title="Top Crypto" subtitle="Ranked by market cap">
              <div className="list">
                {cryptoTop?.items?.map((c: any) => (
                  <div key={c.symbol} className="list-row">
                    <span>#{c.rank} {c.symbol}</span>
                    <strong>${Number(c.price || 0).toFixed(2)}</strong>
                  </div>
                ))}
              </div>
            </Card>
          </section>
        )}

        {active === 'TON' && (
          <section className="grid">
            <Card title="TON Price" subtitle="Live price & 24h change">
              <div className="list">
                {tonPrice?.price && Object.keys(tonPrice.price).map((k: string) => (
                  <div key={k} className="list-row">
                    <span>{k}</span>
                    <strong>{tonPrice.price[k]}</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="TON Projects" subtitle="Top jettons">
              <div className="list">
                {tonProjects?.items?.slice(0, 8).map((j: any, idx: number) => (
                  <div key={`${j.address || idx}`} className="list-row">
                    <span>{j.metadata?.name || j.name || 'Jetton'}</span>
                    <strong>{j.symbol || j.metadata?.symbol || '—'}</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="TON NFT Collections" subtitle="Trending collections">
              <div className="list">
                {tonCollections?.collections?.map((c: any, i: number) => (
                  <div key={i} className="list-row">
                    <span>{c}</span>
                    <strong>Hot</strong>
                  </div>
                ))}
              </div>
            </Card>
          </section>
        )}

        {active === 'NFT' && (
          <section className="grid">
            <Card title="Top Collections" subtitle="OpenSea trending">
              <div className="list">
                {nftCollections?.collections?.map((c: string, i: number) => (
                  <div key={`${c}-${i}`} className="list-row">
                    <span>{c}</span>
                    <strong>Top</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Floor Prices" subtitle="Selected collections">
              <div className="list">
                {nftFloors?.floors && Object.keys(nftFloors.floors).map((k: string) => (
                  <div key={k} className="list-row">
                    <span>{k}</span>
                    <strong>{nftFloors.floors[k]}</strong>
                  </div>
                ))}
              </div>
            </Card>
          </section>
        )}

        {active === 'Portfolio' && (
          <section className="grid">
            <Card title="Holdings" subtitle="Your assets">
              <div className="list">
                {portfolioItems?.items?.map((i: any, idx: number) => (
                  <div key={`${i.symbol}-${idx}`} className="list-row">
                    <span>{i.symbol} · {i.asset_type}</span>
                    <strong>{i.amount}</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Allocation" subtitle="By asset type">
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie dataKey="value" data={allocationData} innerRadius={40} outerRadius={70}>
                    {allocationData.map((_, i) => (
                      <Cell key={i} fill={palette[i % palette.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </section>
        )}

        {active === 'Education' && (
          <section className="grid">
            <Card title="Mini Lessons" subtitle="Bite-sized learning">
              <div className="list">
                {lessons?.lessons?.map((l: string, i: number) => (
                  <div key={i} className="list-row">
                    <span>{l}</span>
                    <strong>2 min</strong>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Glossary" subtitle="Key terms">
              <div className="list">
                {glossary?.glossary?.map((g: string, i: number) => (
                  <div key={i} className="list-row">
                    <span>{g}</span>
                    <strong>Term</strong>
                  </div>
                ))}
              </div>
            </Card>
          </section>
        )}

        {active === 'News' && (
          <section className="grid">
            <Card title="Headlines" subtitle="Market news">
              <div className="list">
                {newsHeadlines?.items?.map((n: any, i: number) => (
                  <div key={i} className="news-row">
                    <a href={n.url} target="_blank" rel="noreferrer">{n.title}</a>
                    <span className="muted">{n.source}</span>
                  </div>
                ))}
              </div>
            </Card>
          </section>
        )}

        {active === 'Settings' && (
          <section className="grid">
            <Card title="Profile" subtitle="Telegram-linked account">
              <div className="list">
                <div className="list-row">
                  <span>User</span>
                  <strong>{profile?.username || '—'}</strong>
                </div>
                <div className="list-row">
                  <span>Tier</span>
                  <strong>{profile?.tier || 'free'}</strong>
                </div>
                <div className="list-row">
                  <span>Badge</span>
                  <strong>{profile?.badge || 'none'}</strong>
                </div>
              </div>
            </Card>
            <Card title="Billing" subtitle="Manage subscription in bot">
              <div className="list">
                <div className="list-row">
                  <span>Upgrade</span>
                  <strong>Use Settings → Subscription in bot</strong>
                </div>
              </div>
            </Card>
          </section>
        )}
      </main>
    </div>
  )
}
