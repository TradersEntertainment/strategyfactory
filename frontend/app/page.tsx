"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Send, Play, BarChart2, Settings, Wallet, Bot, User, Sparkles, TrendingUp, ArrowRight } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// --- Types ---
interface Strategy {
    name: string
    description: string
    market: string
    stats?: {
        winRate: number
        profitFactor: number
        totalPnL: number
    }
}

interface Message {
    role: "user" | "ai"
    text: string
    strategy?: Strategy
}

// --- Mock Data ---
const FEATURED_STRATEGIES: (Strategy & { logicType: string })[] = [
    {
        name: "BitcoinBey Top Tier",
        description: "RSI Double Tap (30/68) + MA99 Trend Filter. Complex Logic.",
        market: "BTC",
        logicType: "BITCOINBEY",
        stats: { winRate: 92, profitFactor: 4.1, totalPnL: 2150 }
    },
    {
        name: "AI Metamorphosis 🦋",
        description: "Adaptive Intelligence. Mutates logic based on market regime (Trend vs Range).",
        market: "BTC",
        logicType: "METAMORPHOSIS",
        stats: { winRate: 92, profitFactor: 5.4, totalPnL: 2400 }
    },
    {
        name: "AI Oracle 🔮 (Cheating)",
        description: "Knows the future. Uses look-ahead info to perfectly buy dips and sell tops. THEORETICAL MAX.",
        market: "ETH",
        logicType: "ORACLE",
        stats: { winRate: 100, profitFactor: 99.9, totalPnL: 1000000 }
    }
]

const generateMockEquity = () => {
    // Legacy mock function, replaced by real API but kept for safety
    return []
}

export default function Home() {
    // --- State ---
    const [strategies, setStrategies] = useState<(Strategy & { logicType: string })[]>(FEATURED_STRATEGIES)

    // API CONFIGURATION - Synchronous to avoid race conditions
    const getApiBaseUrl = () => {
        if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
            return "https://proactive-insight-production-fceb.up.railway.app";
        }
        return "http://localhost:8000";
    };

    console.log("🚀 Debug: API_BASE_URL function would return:", getApiBaseUrl());

    const [isMounted, setIsMounted] = useState(false) // Hydration Fix

    // --- Refs for Robust Interaction ---
    const chartContainerRef = useRef<HTMLDivElement>(null)
    const hoveredPointRef = useRef<{ date: string, price: number } | null>(null)

    const [messages, setMessages] = useState<Message[]>([
        { role: "ai", text: "Hello! Pick a featured strategy below or describe your own logic." }
    ])
    // --- Strategy Factory State ---
    const [factoryMode, setFactoryMode] = useState(false)
    const [markedTrades, setMarkedTrades] = useState<{ date: string, price: number, side: 'BUY' | 'SELL' }[]>([])
    const [inferredStrategy, setInferredStrategy] = useState<any>(null)
    const [marketHistory, setMarketHistory] = useState<any[] | null>(null)
    const [lastHoveredPoint, setLastHoveredPoint] = useState<{ date: string, price: number } | null>(null)



    // --- Native Click Listener ---
    useEffect(() => {
        setIsMounted(true); // Hydration Fix
        const el = chartContainerRef.current;
        if (!el) return;

        const handleClick = (e: MouseEvent) => {
            const point = hoveredPointRef.current;
            if (point && point.date) {
                setMarkedTrades(prev => {
                    const exists = prev.find(p => p.date === point.date);
                    if (exists) {
                        if (exists.side === 'BUY') return prev.map(p => p.date === point.date ? { ...p, side: 'SELL' } : p);
                        return prev.filter(p => p.date !== point.date);
                    }
                    return [...prev, { date: point.date, price: point.price, side: 'BUY' }];
                });
            }
        };

        el.addEventListener('click', handleClick);
        return () => el.removeEventListener('click', handleClick);
    }, []);

    // Load initial chart data for Factory Mode
    useEffect(() => {
        if (factoryMode && !marketHistory) {
            // Fetch baseline data using a dummy strategy just to get benchmark candles
            fetch(`${getApiBaseUrl()}/api/backtest/compare`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ market: "BTC", timeframe: "1h", logic: { type: "HOLD" } })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.benchmark) {
                        setMarketHistory(data.benchmark.map((b: any) => ({ date: b.date, benchmark: b.equity, price: b.price })))
                    }
                })
                .catch(e => console.error(e))
        }
    }, [factoryMode])

    // Keyboard listener for B (BUY) and S (SELL)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!factoryMode || !lastHoveredPoint) return;
            const key = e.key.toLowerCase();
            if (key === 'b' || key === 's') {
                const side: 'BUY' | 'SELL' = key === 'b' ? 'BUY' : 'SELL';
                setMarkedTrades(prev => {
                    const exists = prev.find(p => p.date === lastHoveredPoint.date);
                    if (exists) return prev.filter(p => p.date !== lastHoveredPoint.date);
                    return [...prev, { date: lastHoveredPoint.date, price: lastHoveredPoint.price, side }];
                });
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [factoryMode, lastHoveredPoint]);


    // ... (keep props) ...

    const runScan = async (strategyOverride?: any) => {
        const strat = strategyOverride || activeStrategy
        if (!strat) return
        setIsScanning(true)
        setScanResults(null)

        try {
            const res = await fetch(`${getApiBaseUrl()}/api/backtest/scan`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    market: "BTC",
                    timeframe: "1h",
                    logic: {
                        type: (strat as any).logicType || "TREND",
                        params: (strat as any).params || {}
                    }
                })
            })
            const data = await res.json()
            setScanResults(data)
        } catch (e) { console.error(e) }
        finally { setIsScanning(false) }
    }

    const runOptimize = async () => {
        if (!activeStrategy) return
        setIsOptimizing(true)
        setOptimizationResults(null)
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/backtest/optimize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    market: activeStrategy.market,
                    timeframe: "1h",
                    logic: { type: (activeStrategy as any).logicType || "TREND" }
                })
            })
            const data = await res.json()
            setOptimizationResults(data)
        } catch (e) { console.error(e) }
        finally { setIsOptimizing(false) }
    }

    // ... (previous funcs) ...

    const runTrain = async () => {
        if (!activeStrategy) return
        setIsTraining(true)
        setTrainingResults(null)
        try {
            // 1. Train ON the Oracle behavior
            const res = await fetch(`${getApiBaseUrl()}/api/backtest/train`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    market: activeStrategy.market,
                    timeframe: "1h",
                    logic: { type: "ORACLE" }
                })
            })
            const data = await res.json()
            setTrainingResults(data)

            if (data.learned_params) {
                // 2. Create New Strategy Object
                const newStrat: any = {
                    name: `AI Clone (${new Date().toLocaleTimeString()}) 🧬`,
                    description: `Learned: Buy RSI < ${data.learned_params.rsi_buy}, MACD > ${data.learned_params.macd_buy}`,
                    market: activeStrategy.market,
                    logicType: "LEARNED",
                    params: data.learned_params,
                    stats: { winRate: 0, profitFactor: 0, totalPnL: 0 }
                }

                // 3. Add to List & Activate
                setStrategies(prev => [...prev, newStrat])
                setActiveStrategy(newStrat)

                setMessages(prev => [...prev, {
                    role: "ai",
                    text: `Genetic Cloning Complete! 🧬 I've created "${newStrat.name}" and added it to your list. Now scanning all markets to find where it works best...`
                }])

                // 4. Auto-Run Scan
                await runScan(newStrat)
            }

        } catch (e) { console.error(e) }
        finally { setIsTraining(false) }
    }
    const [input, setInput] = useState("")
    const [loading, setLoading] = useState(false)
    const [activeStrategy, setActiveStrategy] = useState<Strategy | null>(null)
    const [backtestData, setBacktestData] = useState<any[] | null>(null)
    const [isBacktesting, setIsBacktesting] = useState(false)
    const [scanResults, setScanResults] = useState<any>(null)
    const [isScanning, setIsScanning] = useState(false)
    const [optimizationResults, setOptimizationResults] = useState<any>(null)
    const [isOptimizing, setIsOptimizing] = useState(false)
    const [trainingResults, setTrainingResults] = useState<any>(null)
    const [isTraining, setIsTraining] = useState(false)

    const messagesEndRef = useRef<HTMLDivElement>(null)

    // --- Effects ---
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [messages])

    // --- Handlers ---
    const sendMessage = async () => {
        if (!input.trim()) return

        const userMsg = input
        setInput("")
        setMessages(prev => [...prev, { role: "user", text: userMsg }])
        setLoading(true)

        try {
            const res = await fetch(`${getApiBaseUrl()}/api/chat/message`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMsg, wallet_address: "0x123..." })
            })
            const data = await res.json()

            setMessages(prev => [...prev, {
                role: "ai",
                text: data.text,
                strategy: data.strategy
            }])
            if (data.strategy) {
                setActiveStrategy({ ...data.strategy, stats: { winRate: 0, profitFactor: 0, totalPnL: 0 } })
                setBacktestData(null)
            }
        } catch (error) {
            setMessages(prev => [...prev, { role: "ai", text: "Error: Could not connect to HyperQuant Brain." }])
        } finally {
            setLoading(false)
        }
    }

    const selectFeatured = (strat: Strategy) => {
        setActiveStrategy(strat)
        setBacktestData(null)
        setMessages(prev => [...prev, {
            role: "ai",
            text: `Selected "${strat.name}". Check the visualization panel to run a backtest.`,
            strategy: strat
        }])
    }

    const runBacktest = async () => {
        if (!activeStrategy) return

        setIsBacktesting(true)
        setBacktestData(null)

        try {
            const res = await fetch(`${getApiBaseUrl()}/api/backtest/compare`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    market: activeStrategy.market,
                    timeframe: "1h",
                    logic: { type: (activeStrategy as any).logicType || "TREND" }
                })
            })
            const data = await res.json()

            if (data.strategy && data.benchmark) {
                // Merge data for chart
                // benchmark has {date, equity}. strategy.equity_curve has {date, equity, price}.
                // strategy.trades has {date, side, price, type}

                const mergedMap = new Map()

                // 1. Base on Benchmark (Price Action) to ensure full range
                data.benchmark.forEach((b: any) => {
                    mergedMap.set(b.date, { date: b.date, benchmark: b.equity })
                })

                // 2. Overlay Strategy
                data.strategy.equity_curve.forEach((s: any) => {
                    if (mergedMap.has(s.date)) {
                        const existing = mergedMap.get(s.date)
                        mergedMap.set(s.date, { ...existing, strategy: s.equity })
                    }
                })

                // 3. Overlay Trades (Markers)
                data.strategy.trades.forEach((t: any) => {
                    if (mergedMap.has(t.date)) {
                        const existing = mergedMap.get(t.date)
                        // Add marker data. usage: "buyPoint": equity_value if buy
                        if (t.side === 'BUY') {
                            mergedMap.set(t.date, { ...existing, buyPoint: existing.strategy || existing.benchmark })
                        } else if (t.side === 'SELL') {
                            mergedMap.set(t.date, { ...existing, sellPoint: existing.strategy || existing.benchmark })
                        }
                    }
                })

                setBacktestData(Array.from(mergedMap.values()))
            }
        } catch (e) {
            console.error(e)
        } finally {
            setIsBacktesting(false)
        }
    }


    // Custom Shapes for Markers
    const BuyMarker = (props: any) => {
        const { cx, cy, payload } = props;
        if (!payload.buyPoint) return null;
        return (
            <svg x={cx - 6} y={cy - 6} width={12} height={12} viewBox="0 0 24 24" fill="#10b981" stroke="none">
                <path d="M12 2L2 22h20L12 2z" /> {/* Up Triangle */}
            </svg>
        );
    };

    const SellMarker = (props: any) => {
        const { cx, cy, payload } = props;
        if (!payload.sellPoint) return null;
        return (
            <svg x={cx - 6} y={cy - 6} width={12} height={12} viewBox="0 0 24 24" fill="#ef4444" stroke="none">
                <path d="M12 22L2 2h20L12 22z" /> {/* Down Triangle */}
            </svg>
        );
    };

    return (
        <div className="flex h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden">
            {/* Sidebar */}
            <aside className="w-16 flex flex-col items-center py-6 border-r border-zinc-800 bg-zinc-900">
                <div className="mb-8 p-2 bg-emerald-500 rounded-lg shadow-[0_0_15px_rgba(16,185,129,0.4)]">
                    <BarChart2 className="w-6 h-6 text-black" />
                </div>
                <nav className="flex flex-col gap-6">
                    <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-emerald-400 hover:bg-zinc-800/50"><Play className="w-5 h-5" /></Button>
                    <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-emerald-400 hover:bg-zinc-800/50"><BarChart2 className="w-5 h-5" /></Button>

                    {/* FACTORY MODE TOGGLE */}
                    <div onClick={() => setFactoryMode(!factoryMode)} className={`p-2 rounded-lg cursor-pointer transition-all flex justify-center ${factoryMode ? "bg-purple-600 shadow-[0_0_15px_rgba(147,51,234,0.5)]" : "hover:bg-zinc-800"}`}>
                        <Sparkles className={`w-5 h-5 ${factoryMode ? "text-white" : "text-zinc-400"}`} />
                    </div>

                    <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-emerald-400 hover:bg-zinc-800/50"><Settings className="w-5 h-5" /></Button>
                </nav>
                <div className="mt-auto">
                    <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-emerald-400 hover:bg-zinc-800/50"><Wallet className="w-5 h-5" /></Button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col">
                {/* Header */}
                <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-950/50 backdrop-blur">
                    <h1 className="font-bold text-xl tracking-tight text-white">Hyper<span className="text-emerald-400">Quant</span></h1>
                    <div className="flex gap-4">
                        <Button variant="outline" className="text-emerald-400 border-zinc-700 hover:bg-zinc-900 hover:text-emerald-300 hover:border-emerald-500/50 transition-colors">Connect Wallet</Button>
                    </div>
                </header>

                {/* Workspace */}
                <div className="flex-1 flex overflow-hidden">

                    {/* Left: Chat / Builder */}
                    <div className="w-1/2 flex flex-col border-r border-zinc-800 bg-zinc-900/50">
                        {factoryMode ? (
                            <div className="p-4 flex flex-col h-full animate-in fade-in slide-in-from-left-4">
                                <h2 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent mb-1">
                                    Strategy Factory 🏭
                                </h2>
                                <p className="text-xs text-zinc-400 mb-2">
                                    Hover over chart to select a point. CLICK to mark. (1st=BUY, 2nd=SELL, 3rd=Remove)
                                </p>



                                {/* CHART WITH OVERLAY INTERACTIONS */}
                                <div
                                    ref={chartContainerRef}
                                    className="flex-1 min-h-[200px] bg-zinc-950 rounded-xl border border-purple-500/30 p-2 mb-3 relative group cursor-crosshair z-10"
                                >

                                    {/* Hover Indicator */}
                                    {isMounted && lastHoveredPoint && (
                                        <div className="absolute top-2 left-2 z-20 bg-purple-600/90 px-2 py-0.5 rounded text-[10px] text-white font-mono pointer-events-none">
                                            {lastHoveredPoint.date.slice(5, 16)} | ${Math.round(lastHoveredPoint.price)}
                                        </div>
                                    )}

                                    {
                                        isMounted && marketHistory ? (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <LineChart
                                                    data={marketHistory.map((d: any) => {
                                                        const mark = markedTrades.find(m => m.date === d.date);
                                                        if (mark) {
                                                            return { ...d, [mark.side === 'BUY' ? 'buyPoint' : 'sellPoint']: d.price };
                                                        }
                                                        return d;
                                                    })}
                                                    onMouseMove={(e: any) => {
                                                        if (e && e.activeLabel && e.activePayload && e.activePayload[0]) {
                                                            const payload = e.activePayload[0].payload;
                                                            const pt = {
                                                                date: e.activeLabel,
                                                                price: payload.price || 0
                                                            };
                                                            setLastHoveredPoint(pt); // Keep for UI
                                                            hoveredPointRef.current = pt; // Sync for DOM listener
                                                        }
                                                    }}
                                                >
                                                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                                                    <XAxis dataKey="date" stroke="#52525b" fontSize={8} tickLine={false} axisLine={false} minTickGap={60} />
                                                    <YAxis stroke="#52525b" fontSize={8} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                                                    <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#a855f7', borderRadius: '8px' }} itemStyle={{ fontSize: '10px' }} />
                                                    <Line type="monotone" dataKey="price" stroke="#a855f7" strokeWidth={2} dot={false} name="BTC" isAnimationActive={false} />
                                                    <Line dataKey="buyPoint" stroke="none" dot={<BuyMarker />} isAnimationActive={false} legendType="none" />
                                                    <Line dataKey="sellPoint" stroke="none" dot={<SellMarker />} isAnimationActive={false} legendType="none" />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        ) : (
                                            <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
                                                {isMounted ? "Loading chart..." : "Initializing..."}
                                            </div>
                                        )
                                    }
                                </div>

                                {/* MARKED TRADES LIST */}
                                <div className="max-h-20 overflow-y-auto space-y-1 mb-2">
                                    {markedTrades.map((t, i) => (
                                        <div key={i} className="flex justify-between items-center text-xs p-1 bg-zinc-900 rounded border border-zinc-800">
                                            <span className="text-zinc-400 font-mono text-[10px]">{t.date.slice(0, 16)}</span>
                                            <span className={t.side === 'BUY' ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'}>{t.side}</span>
                                        </div>
                                    ))}
                                    {markedTrades.length === 0 && (
                                        <div className="text-center p-2 border border-dashed border-zinc-700 rounded text-zinc-600 text-xs">
                                            No trades marked yet. Hover chart &amp; use buttons above.
                                        </div>
                                    )}
                                </div>

                                {inferredStrategy && (
                                    <div className="bg-purple-900/20 border border-purple-500/30 p-4 rounded-xl mb-4 text-sm">
                                        <div className="font-bold text-purple-300 mb-1">Analysis Complete</div>
                                        <div className="text-zinc-300 mb-2 leading-relaxed">{inferredStrategy.description}</div>
                                        <Button
                                            size="sm"
                                            className="w-full bg-purple-600 hover:bg-purple-500"
                                            onClick={() => {
                                                const newStrat: any = {
                                                    name: "Inferred Strategy 🧠",
                                                    description: inferredStrategy.description,
                                                    market: "BTC",
                                                    logicType: "LEARNED",
                                                    params: inferredStrategy.params,
                                                    stats: { winRate: 0, profitFactor: 0, totalPnL: 0 }
                                                }
                                                setStrategies(prev => [...prev, newStrat])
                                                setActiveStrategy(newStrat)
                                                setFactoryMode(false)
                                            }}
                                        >
                                            Save & Backtest This Logic
                                        </Button>
                                    </div>
                                )}

                                <div className="flex gap-2 mt-4">
                                    <Button
                                        variant="outline"
                                        className="flex-1 border-zinc-700 hover:bg-zinc-800 text-white"
                                        onClick={() => setMarkedTrades([])}
                                    >
                                        Clear
                                    </Button>
                                    <Button
                                        className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white"
                                        onClick={async () => {
                                            if (markedTrades.length < 2) return alert("Mark at least 2 trades")
                                            try {
                                                const res = await fetch(`${getApiBaseUrl()}/api/backtest/infer`, {
                                                    method: "POST", headers: { "Content-Type": "application/json" },
                                                    body: JSON.stringify({ market: "BTC", timeframe: "1h", logic: { marked_trades: markedTrades } })
                                                })
                                                const data = await res.json()
                                                setInferredStrategy(data)
                                            } catch (e) { console.error(e) }
                                        }}
                                        disabled={markedTrades.length < 2}
                                    >
                                        Analyze Pattern 🪄
                                    </Button>
                                </div>
                            </div>
                        ) : (
                            <Tabs defaultValue="chat" className="flex-1 flex flex-col">
                                <div className="px-6 py-2 border-b border-zinc-800">
                                    <TabsList className="bg-zinc-900 border border-zinc-800">
                                        <TabsTrigger value="chat" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-emerald-400">AI Chat</TabsTrigger>
                                        <TabsTrigger value="manual" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-emerald-400">Manual Builder</TabsTrigger>
                                    </TabsList>
                                </div>

                                {/* ... Content ... */}
                                <TabsContent value="chat" className="flex-1 flex flex-col p-0 m-0 relative">
                                    <div className="flex-1 p-6 overflow-y-auto space-y-4 pb-20">

                                        {/* Featured Strategies Widget */}
                                        <div className="grid grid-cols-1 gap-3 mb-6">
                                            <div className="flex items-center gap-2 text-zinc-500 text-xs uppercase font-bold tracking-wider">
                                                <Sparkles className="w-3 h-3 text-emerald-400" /> Featured Strategies
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                                {FEATURED_STRATEGIES.map((s, i) => (
                                                    <div
                                                        key={i}
                                                        onClick={() => selectFeatured(s)}
                                                        className="bg-zinc-900 border border-zinc-800 hover:border-emerald-500/50 hover:bg-zinc-800/50 cursor-pointer p-3 rounded-xl transition-all group"
                                                    >
                                                        <div className="flex justify-between items-start mb-1">
                                                            <span className="text-zinc-200 font-semibold text-sm group-hover:text-emerald-400">{s.name}</span>
                                                            <span className="text-xs bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded">{s.market}</span>
                                                        </div>
                                                        <p className="text-xs text-zinc-500 line-clamp-2 leading-relaxed">{s.description}</p>
                                                        <div className="flex gap-2 mt-2 pt-2 border-t border-zinc-800/50">
                                                            <span className="text-[10px] text-emerald-400 font-medium">WR: {s.stats?.winRate}%</span>
                                                            <span className="text-[10px] text-blue-400 font-medium">PF: {s.stats?.profitFactor}</span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="w-full h-px bg-zinc-800 my-2"></div>

                                        {/* Chat Messages */}
                                        {messages.map((msg, i) => (
                                            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                <div className={`
                                                max-w-[80%] p-4 rounded-2xl text-sm shadow-sm
                                                ${msg.role === 'user'
                                                        ? 'bg-emerald-600/20 border border-emerald-500/30 text-emerald-100 rounded-tr-none'
                                                        : 'bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-tl-none'}
                                            `}>
                                                    <div className="flex items-center gap-2 mb-1 opacity-50 text-xs font-semibold uppercase tracking-wider">
                                                        {msg.role === 'user' ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
                                                        {msg.role === 'user' ? 'You' : 'HyperQuant AI'}
                                                    </div>
                                                    {msg.text}
                                                </div>
                                            </div>
                                        ))}
                                        {loading && (
                                            <div className="flex justify-start">
                                                <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-2xl rounded-tl-none text-zinc-500 text-xs animate-pulse">
                                                    Thinking...
                                                </div>
                                            </div>
                                        )}
                                        <div ref={messagesEndRef} />
                                    </div>

                                    <div className="p-4 border-t border-zinc-800 bg-zinc-900 absolute bottom-0 w-full">
                                        <div className="relative">
                                            <Input
                                                value={input}
                                                onChange={(e) => setInput(e.target.value)}
                                                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                                                disabled={loading}
                                                className="bg-zinc-950 border-zinc-800 text-zinc-200 pr-12 focus-visible:ring-emerald-500/50"
                                                placeholder="Ex: Buy BTC if RSI < 30..."
                                            />
                                            <Button
                                                onClick={sendMessage}
                                                disabled={loading}
                                                size="icon"
                                                className="absolute right-1 top-1 h-8 w-8 bg-emerald-500 hover:bg-emerald-400 text-black">
                                                <Send className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </TabsContent>

                                <TabsContent value="manual" className="p-6">
                                    <div className="grid gap-4">
                                        <Card className="bg-zinc-900 border-zinc-800">
                                            <CardHeader>
                                                <CardTitle className="text-sm font-medium text-zinc-200">Add Indicator</CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                {/* Placeholders for builder inputs */}
                                                <p className="text-xs text-zinc-500">Manual builder form will go here.</p>
                                            </CardContent>
                                        </Card>
                                    </div>
                                </TabsContent>
                            </Tabs>
                        )}
                    </div>

                    {/* Right: Visualization / Status */}
                    <div className="w-1/2 bg-zinc-950 p-6 flex flex-col gap-6">

                        <Card className="bg-zinc-900 border-zinc-800">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-zinc-400">Target Strategy</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {activeStrategy ? (
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <h2 className="text-xl font-bold text-white">{activeStrategy.name}</h2>
                                            <span className="px-2 py-1 bg-emerald-500/10 text-emerald-500 text-xs rounded border border-emerald-500/20">{activeStrategy.market}</span>
                                        </div>
                                        <p className="text-sm text-zinc-500 mb-4">{activeStrategy.description}</p>
                                        <div className="flex gap-3">
                                            <Button
                                                onClick={runBacktest}
                                                disabled={isBacktesting}
                                                className="bg-emerald-500 hover:bg-emerald-600 text-black flex-1"
                                            >
                                                {isBacktesting ? "Running..." : "Run Backtest"}
                                                {!isBacktesting && <Play className="w-4 h-4 ml-2" />}
                                            </Button>
                                            <Button
                                                onClick={runScan}
                                                disabled={isScanning}
                                                variant="outline"
                                                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white flex-1"
                                            >
                                                {isScanning ? "Scanning..." : "Find Best Market"}
                                                {!isScanning && <Sparkles className="w-4 h-4 ml-2 text-yellow-500" />}
                                            </Button>
                                            <Button
                                                onClick={runOptimize}
                                                disabled={isOptimizing}
                                                className="bg-purple-600 hover:bg-purple-500 text-white flex-1"
                                            >
                                                {isOptimizing ? "Optimizing..." : "Improve w/ AI"}
                                                {!isOptimizing && <Sparkles className="w-4 h-4 ml-2" />}
                                            </Button>
                                            <Button
                                                onClick={runTrain}
                                                disabled={isTraining}
                                                className="bg-cyan-600 hover:bg-cyan-500 text-white flex-1"
                                            >
                                                {isTraining ? "Cloning..." : "Clone Oracle 🧬"}
                                                {!isTraining && <Bot className="w-4 h-4 ml-2" />}
                                            </Button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-zinc-500 text-sm italic">
                                        Select a strategy to see details here.
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Training Results */}
                        {trainingResults && (
                            <div className="bg-cyan-900/20 border border-cyan-500/30 p-4 rounded-xl">
                                <h4 className="text-cyan-400 text-sm font-bold flex items-center gap-2 mb-2">
                                    <Bot className="w-4 h-4" /> Oracle Logic Cloned!
                                </h4>
                                <div className="text-xs text-zinc-300 mb-2">{trainingResults.message}</div>
                                <div className="bg-black/40 rounded p-2 text-xs font-mono text-zinc-400">
                                    {JSON.stringify(trainingResults.learned_params)}
                                </div>
                                <Button
                                    size="sm"
                                    onClick={() => alert("Parameters copied! Use them in Manual Builder.")}
                                    className="mt-3 w-full bg-cyan-700 hover:bg-cyan-600 text-white text-xs"
                                >
                                    Apply Cloned Strategy (Manual)
                                </Button>
                            </div>
                        )}

                        {/* Scan Results - Overlay or Section */}
                        {scanResults && (
                            <div className="bg-zinc-900/50 border border-zinc-800 p-3 rounded-lg flex items-center justify-between">
                                <div className="flex flex-col">
                                    <span className="text-xs text-zinc-500">Recommended Asset</span>
                                    <span className="text-lg font-bold text-white flex items-center gap-2">
                                        {scanResults.best_asset.market}
                                        <span className="text-emerald-400 text-sm">(+{scanResults.best_asset.return_pct}%)</span>
                                    </span>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs text-zinc-500 mb-1">Top Performers</div>
                                    <div className="flex gap-2">
                                        {scanResults.all_results.slice(0, 3).map((r: any, i: number) => (
                                            <span key={i} className="text-xs bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-300">
                                                {r.market}: {r.return_pct}%
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Optimization Results */}
                        {optimizationResults && (
                            <div className="bg-purple-900/20 border border-purple-500/30 p-4 rounded-xl">
                                <h4 className="text-purple-400 text-sm font-bold flex items-center gap-2 mb-2">
                                    <Sparkles className="w-4 h-4" /> AI Enhancement Found
                                </h4>
                                <div className="flex justify-between items-center mb-3">
                                    <div>
                                        <div className="text-xs text-zinc-400">Original Return</div>
                                        <div className="text-zinc-300 font-mono">{optimizationResults.original_return}%</div>
                                    </div>
                                    <ArrowRight className="w-4 h-4 text-zinc-500" />
                                    <div>
                                        <div className="text-xs text-zinc-400">Optimized Return</div>
                                        <div className="text-emerald-400 font-bold font-mono text-lg">{optimizationResults.best_return}%</div>
                                    </div>
                                </div>
                                <div className="bg-black/40 rounded p-2 text-xs font-mono text-zinc-400">
                                    <div>Params: {JSON.stringify(optimizationResults.improved_params)}</div>
                                </div>
                                <div className="mt-2 text-[10px] text-zinc-500">
                                    {optimizationResults.improvement_log.length > 0 ? optimizationResults.improvement_log[0] : "No improvement found."}
                                </div>
                            </div>
                        )}

                        {/* Chart Area */}

                        {/* Legend */}
                        {backtestData && (
                            <div className="flex items-center gap-4 text-xs justify-end px-2">
                                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-emerald-500"></div> Strategy</div>
                                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-zinc-500"></div> Buy & Hold</div>
                                <div className="flex items-center gap-1"><div className="w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-b-[8px] border-b-emerald-500"></div> Buy</div>
                                <div className="flex items-center gap-1"><div className="w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[8px] border-t-red-500"></div> Sell</div>
                            </div>
                        )}

                        <div className="flex-1 min-h-0 bg-zinc-900 rounded-xl border border-zinc-800 p-4 relative flex flex-col">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                                    <TrendingUp className="w-4 h-4 text-emerald-500" />
                                    Performance Comparison
                                </h3>
                            </div>

                            <div className="flex-1 w-full min-h-0">
                                {(() => {
                                    const baseData = backtestData || marketHistory;
                                    // Dynamically merge marks into data for visualization
                                    const chartData = baseData?.map((d: any) => {
                                        const mark = markedTrades.find(m => m.date === d.date);
                                        if (mark) {
                                            return {
                                                ...d,
                                                [mark.side === 'BUY' ? 'buyPoint' : 'sellPoint']: d.price || d.benchmark || d.strategy
                                            };
                                        }
                                        return d;
                                    });

                                    return chartData ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart
                                                data={chartData}
                                                onClick={(e: any) => {
                                                    if (factoryMode && e && e.activeLabel) {
                                                        const payload = e.activePayload && e.activePayload[0] ? e.activePayload[0].payload : null
                                                        if (payload) {
                                                            const price = payload.price || payload.benchmark || payload.strategy
                                                            setMarkedTrades(prev => {
                                                                const exists = prev.find(p => p.date === e.activeLabel)
                                                                if (exists) return prev.filter(p => p.date !== e.activeLabel)
                                                                return [...prev, { date: e.activeLabel, price, side: 'BUY' }]
                                                            })
                                                        }
                                                    }
                                                }}
                                                className={factoryMode ? "cursor-crosshair" : "cursor-default"}
                                            >
                                                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                                                <XAxis dataKey="date" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} minTickGap={30} />
                                                <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                                                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '8px' }} itemStyle={{ fontSize: '12px' }} />
                                                <Line type="monotone" dataKey="benchmark" stroke="#71717a" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Buy & Hold" />
                                                <Line type="monotone" dataKey="strategy" stroke="#10b981" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: '#10b981' }} name="Strategy" />
                                                <Line dataKey="buyPoint" stroke="none" dot={<BuyMarker />} isAnimationActive={false} legendType="none" />
                                                <Line dataKey="sellPoint" stroke="none" dot={<SellMarker />} isAnimationActive={false} legendType="none" />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-zinc-600 gap-2">
                                            <BarChart2 className="w-10 h-10 opacity-20" />
                                            <p className="text-sm">Run backtest to see comparison.</p>
                                        </div>
                                    )
                                })()}
                            </div>
                        </div>

                    </div>
                </div>
            </main>
        </div>
    );
}
