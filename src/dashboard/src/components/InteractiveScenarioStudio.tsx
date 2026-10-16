import React, { useState, useEffect, useRef } from 'react';
import { FaultScenario, FaultId, NodeStatus } from '../types/network';
import { 
  Play, 
  Pause,
  RotateCcw, 
  StepForward, 
  CheckCircle2, 
  Clock, 
  Terminal, 
  Zap, 
  ArrowRight, 
  Activity, 
  Layers, 
  Sparkles,
  Info,
  SlidersHorizontal,
  ChevronRight
} from 'lucide-react';

interface InteractiveScenarioStudioProps {
  scenarios: FaultScenario[];
  activeScenarioId?: FaultId;
  onInjectFault: (scenario: FaultScenario) => void;
  onResetNetwork: () => void;
  themeColor?: 'cyan' | 'blue' | 'emerald';
}

export const InteractiveScenarioStudio: React.FC<InteractiveScenarioStudioProps> = ({
  scenarios,
  activeScenarioId,
  onInjectFault,
  onResetNetwork,
  themeColor = 'cyan',
}) => {
  const [selectedScenario, setSelectedScenario] = useState<FaultScenario>(scenarios[0]);
  const [activeGroup, setActiveGroup] = useState<'reactive' | 'proactive'>('reactive');

  // 4 States of Topology Fault-to-Recovery:
  // 1 = Normal (Mạng bình thường)
  // 2 = Fault (Gặp sự cố)
  // 3 = Healing (AI can thiệp & Reroute)
  // 4 = Restored (Đã hồi phục hoàn toàn)
  const [topoPhase, setTopoPhase] = useState<1 | 2 | 3 | 4>(1);
  const [isAutoPlaying, setIsAutoPlaying] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(0.75); // Chậm rãi mặc định
  const [stopwatchMs, setStopwatchMs] = useState<number>(0);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [animTick, setAnimTick] = useState<number>(0);

  const autoPlayTimers = useRef<any[]>([]);

  // Animation ticker for packet particles
  useEffect(() => {
    const timer = setInterval(() => {
      setAnimTick((prev) => (prev + 1) % 100);
    }, 45);
    return () => clearInterval(timer);
  }, []);

  const filteredList = scenarios.filter((s) =>
    activeGroup === 'reactive' ? s.type === 'Reactive' : s.type === 'Proactive'
  );

  // Stopwatch timer when simulating
  useEffect(() => {
    let timer: any;
    if (isAutoPlaying && !isPaused && topoPhase >= 2 && topoPhase <= 3) {
      timer = setInterval(() => {
        setStopwatchMs((prev) => prev + 50);
      }, 50);
    }
    return () => clearInterval(timer);
  }, [isAutoPlaying, isPaused, topoPhase]);

  // Clear pending timers helper
  const clearAllTimers = () => {
    autoPlayTimers.current.forEach((t) => clearTimeout(t));
    autoPlayTimers.current = [];
  };

  // Start Slow and Smooth Fault-to-Recovery Sequence
  const startFaultToRecoverySequence = () => {
    clearAllTimers();
    setTopoPhase(1);
    setStopwatchMs(0);
    setProgressPercent(0);
    setIsAutoPlaying(true);
    setIsPaused(false);

    // Dynamic durations based on speed multiplier (Base: 14s total)
    const baseUnit = 1000 / speedMultiplier;
    const tFault = baseUnit * 3.5;    // Phase 1 -> 2: 3.5s
    const tHealing = baseUnit * 7.5;  // Phase 2 -> 3: 7.5s
    const tRestored = baseUnit * 12.0;// Phase 3 -> 4: 12.0s
    const tFinished = baseUnit * 15.0;// End: 15.0s

    // Interval progress updater
    const progInterval = setInterval(() => {
      setProgressPercent((prev) => {
        if (prev >= 100) {
          clearInterval(progInterval);
          return 100;
        }
        return Math.min(prev + 100 / (tFinished / 100), 100);
      });
    }, 100);
    autoPlayTimers.current.push(progInterval);

    // 1 -> 2: Topology Gặp Lỗi
    const timer1 = setTimeout(() => {
      setTopoPhase(2);
      onInjectFault(selectedScenario);
    }, tFault);
    autoPlayTimers.current.push(timer1);

    // 2 -> 3: AI Can Thiệp & Nắn Tuyến
    const timer2 = setTimeout(() => {
      setTopoPhase(3);
    }, tHealing);
    autoPlayTimers.current.push(timer2);

    // 3 -> 4: Hồi Phục Hoàn Toàn
    const timer3 = setTimeout(() => {
      setTopoPhase(4);
    }, tRestored);
    autoPlayTimers.current.push(timer3);

    // Complete Sequence
    const timer4 = setTimeout(() => {
      setIsAutoPlaying(false);
      setProgressPercent(100);
    }, tFinished);
    autoPlayTimers.current.push(timer4);
  };

  const handlePauseResume = () => {
    setIsPaused(!isPaused);
  };

  const handleReset = () => {
    clearAllTimers();
    setTopoPhase(1);
    setStopwatchMs(0);
    setProgressPercent(0);
    setIsAutoPlaying(false);
    setIsPaused(false);
    onResetNetwork();
  };

  const phaseNames = [
    { id: 1, label: '1. Mạng Bình Thường', sub: 'Healthy State', color: 'text-emerald-400' },
    { id: 2, label: '2. Topology Gặp Lỗi', sub: 'Fault & Drop', color: 'text-rose-400' },
    { id: 3, label: '3. AI Ra Lệnh Can Thiệp', sub: 'PPO & SD-WAN', color: 'text-cyan-400' },
    { id: 4, label: '4. Topology Đã Hồi Phục', sub: 'Restored & Rerouted', color: 'text-emerald-400' },
  ];

  return (
    <div className="space-y-4">
      {/* Top Banner: Studio Controls */}
      <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              TRỰC QUAN HÓA TOPOLOGY GẶP LỖI & HỒI PHỤC (14 SCENARIOS TOPOLOGY STUDIO)
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Quan sát trực quan toàn bộ quá trình: Mạng bình thường &rarr; Gặp lỗi đứt gãy &rarr; AI can thiệp nắn tuyến &rarr; Hồi phục hoàn toàn
          </p>
        </div>

        {/* Group Filter Tabs */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="flex items-center bg-slate-950 p-1 rounded border border-slate-800">
            <button
              onClick={() => {
                setActiveGroup('reactive');
                setSelectedScenario(scenarios[0]);
                handleReset();
              }}
              className={`px-3 py-1 rounded transition-colors ${
                activeGroup === 'reactive'
                  ? 'bg-cyan-950 text-cyan-200 border border-cyan-800 font-bold'
                  : 'text-slate-400'
              }`}
            >
              12 Reactive (F01 - F12)
            </button>
            <button
              onClick={() => {
                setActiveGroup('proactive');
                setSelectedScenario(scenarios[12]);
                handleReset();
              }}
              className={`px-3 py-1 rounded transition-colors ${
                activeGroup === 'proactive'
                  ? 'bg-amber-950 text-amber-200 border border-amber-800 font-bold'
                  : 'text-slate-400'
              }`}
            >
              2 Proactive (P1, P2)
            </button>
          </div>
        </div>
      </div>

      {/* Main Studio Workspace: 14 Scenarios on Left (4 cols), Topology Visualizer on Right (8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: 14 Scenario Cards Grid (4 cols) */}
        <div className="lg:col-span-4 space-y-2 max-h-[760px] overflow-y-auto pr-1">
          {filteredList.map((sc) => {
            const isSelected = selectedScenario.id === sc.id;
            return (
              <div
                key={sc.id}
                onClick={() => {
                  setSelectedScenario(sc);
                  handleReset();
                }}
                className={`p-3 rounded-lg border text-xs font-mono cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-cyan-950/60 border-cyan-500 shadow-[0_0_12px_rgba(6,182,212,0.3)]'
                    : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-1.5 py-0.5 rounded font-bold text-[11px] ${
                        sc.type === 'Proactive'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800'
                          : 'bg-slate-800 text-cyan-300'
                      }`}
                    >
                      {sc.id}
                    </span>
                    <span className="font-bold text-slate-200 truncate">{sc.name}</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                    MTTR: {sc.targetMttr}
                  </span>
                </div>

                <div className="mt-1.5 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Đối tượng: <strong className="text-slate-300">{sc.targetDevice}</strong></span>
                  <span>Miền: <strong className="text-slate-300">{sc.category}</strong></span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Scenario Topology Visualizer (8 cols) */}
        <div className="lg:col-span-8 p-4 bg-slate-900/80 border border-slate-800 rounded-lg space-y-4 flex flex-col justify-between">
          {/* Top Bar of Scenario & Slow/Smooth Play Controls */}
          <div>
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-base font-bold text-cyan-400">
                    [{selectedScenario.id}] {selectedScenario.name}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {selectedScenario.category}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Mục tiêu MTTR: <strong className="text-emerald-400">{selectedScenario.targetMttr}</strong> · Bộ điều khiển: <strong className="text-slate-200">{selectedScenario.controller}</strong>
                </p>
              </div>

              {/* Player Controls (Chậm rãi, có chọn tốc độ) */}
              <div className="flex items-center gap-2 font-mono">
                {/* Tốc độ thực hiện (Speed control) */}
                <div className="flex items-center gap-1 bg-slate-950 p-1 rounded border border-slate-800 text-[10px]">
                  <span className="text-slate-400 px-1">Tốc độ:</span>
                  {[0.5, 0.75, 1.0].map((s) => (
                    <button
                      key={s}
                      onClick={() => setSpeedMultiplier(s)}
                      className={`px-1.5 py-0.5 rounded transition-colors ${
                        speedMultiplier === s ? 'bg-cyan-950 text-cyan-300 font-bold border border-cyan-700' : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      {s === 0.5 ? '0.5x (Rất Chậm)' : s === 0.75 ? 'Chậm' : '1x'}
                    </button>
                  ))}
                </div>

                <button
                  onClick={startFaultToRecoverySequence}
                  disabled={isAutoPlaying && !isPaused}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs shadow-lg transition-colors whitespace-nowrap"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{isAutoPlaying ? 'Đang Diễn Tập...' : 'Xem Quá Trình (Chậm)'}</span>
                </button>

                {isAutoPlaying && (
                  <button
                    onClick={handlePauseResume}
                    className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 transition-colors"
                    title={isPaused ? 'Tiếp tục' : 'Tạm dừng để giải thích'}
                  >
                    {isPaused ? <Play className="w-4 h-4 fill-current" /> : <Pause className="w-4 h-4" />}
                  </button>
                )}

                <button
                  onClick={handleReset}
                  className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                  title="Reset về bình thường"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Smooth Progress Bar & 4 Phase Selector Buttons */}
            <div className="my-3 space-y-2 font-mono">
              {isAutoPlaying && (
                <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 via-amber-400 to-emerald-400 transition-all duration-300"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              )}

              <div className="grid grid-cols-4 gap-2 text-[11px]">
                {phaseNames.map((p) => {
                  const isActive = topoPhase === p.id;
                  return (
                    <button
                      key={p.id}
                      onClick={() => {
                        setTopoPhase(p.id as 1 | 2 | 3 | 4);
                        if (p.id === 2) onInjectFault(selectedScenario);
                      }}
                      className={`p-2.5 rounded border text-center transition-all ${
                        isActive
                          ? 'bg-slate-950 border-cyan-400 text-white ring-2 ring-cyan-400/50 shadow-xl'
                          : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <div className="font-bold flex items-center justify-center gap-1.5">
                        {isActive && <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />}
                        {p.label}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">{p.sub}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* ════════ KHU VỰC VẼ TOPOLOGY THỰC THỤ GIỐNG HỆT BẢN VẼ LỚN ════════ */}
          <div className="p-3 bg-[#070b14] border border-slate-800 rounded-xl relative overflow-hidden shadow-2xl">
            {/* Status Header */}
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/80 text-xs font-mono">
              <div className="flex items-center gap-2">
                <span
                  className={`w-3 h-3 rounded-full ${
                    topoPhase === 1
                      ? 'bg-emerald-400'
                      : topoPhase === 2
                      ? 'bg-rose-500 animate-ping'
                      : topoPhase === 3
                      ? 'bg-amber-400 animate-pulse'
                      : 'bg-emerald-400'
                  }`}
                />
                <span className="font-bold text-white uppercase tracking-wider">
                  TOPOLOGY SUB-SYSTEM: {phaseNames[topoPhase - 1].label.toUpperCase()}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-slate-400">
                <span>Đồng hồ MTTR: <strong className="text-cyan-300">{(stopwatchMs / 1000).toFixed(2)}s</strong></span>
                {isPaused && <span className="text-amber-400 font-bold bg-amber-950/80 px-1.5 py-0.5 rounded border border-amber-700">[TẠM DỪNG]</span>}
              </div>
            </div>

            {/* SVG Canvas Topology - Vẽ chuẩn giống hình Topology lớn với Node tròn, icon, hạt flow, cáp đứt */}
            <div className="w-full h-[340px] flex items-center justify-center relative">
              {renderAuthenticTopologyDiagram(selectedScenario, topoPhase, animTick)}
            </div>

            {/* Explanation of Current Topology State */}
            <div className="mt-3 p-3 rounded-lg bg-slate-950/90 border border-slate-800 text-xs font-mono">
              <div className="flex items-center justify-between text-slate-300 font-bold mb-1">
                <span className="text-cyan-300">
                  Diễn Biến Topology Ở Trạng Thái Này:
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                  {selectedScenario.controller}
                </span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {getPhaseExplanation(selectedScenario, topoPhase)}
              </p>
            </div>
          </div>

          {/* Bottom: Mininet Command & MTTR Benchmark */}
          <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
            <div className="flex items-center gap-2 text-slate-400">
              <Terminal className="w-4 h-4 text-cyan-400" />
              <span>Mininet Command:</span>
              <code className="text-emerald-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-[11px]">
                {selectedScenario.commandSnippet}
              </code>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-slate-400">Mạng truyền thống: <strong className="text-rose-400 line-through">1800s (30m)</strong></span>
              <span className="text-slate-600">|</span>
              <span className="text-emerald-400 font-bold">
                Tự phục hồi: {selectedScenario.targetMttr}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // ════════ VẼ SƠ ĐỒ TOPOLOGY CHUẨN XÁC GIỐNG HỆT BẢN VẼ TOPOLOGY LỚN ════════
  function renderAuthenticTopologyDiagram(sc: FaultScenario, phase: 1 | 2 | 3 | 4, tick: number) {
    const isFault = phase === 2;
    const isHealing = phase === 3;
    const isRestored = phase === 4;

    const tProg = (tick % 100) / 100;

    // KỊCH BẢN 1: F01 - Access Link Failure (NT-ACC02 Down)
    if (sc.id === 'F01') {
      return (
        <svg className="w-full h-full" viewBox="0 0 680 320">
          <defs>
            <filter id="sim-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <rect width="680" height="320" fill="#070b14" rx="8" />

          {/* Blueprint Grid lines */}
          <line x1="40" y1="90" x2="640" y2="90" stroke="#1e293b" strokeDasharray="4 4" strokeWidth="1" />
          <line x1="40" y1="180" x2="640" y2="180" stroke="#1e293b" strokeDasharray="4 4" strokeWidth="1" />
          <line x1="40" y1="260" x2="640" y2="260" stroke="#1e293b" strokeDasharray="4 4" strokeWidth="1" />

          {/* ── CORE LAYER: NT-CORE (Root STP) ── */}
          {renderRoundNode(340, 50, 'NT-CORE', 'Root STP 4096', 22, '#06b6d4', 'ONLINE')}

          {/* ── DISTRIBUTION LAYER: NT-DIST01 & NT-DIST02 ── */}
          {renderRoundNode(210, 140, 'NT-DIST01', 'VRRP Master', 19, '#6366f1', 'ONLINE', 'MASTER')}
          {renderRoundNode(470, 140, 'NT-DIST02', 'VRRP Backup', 19, '#6366f1', 'ONLINE', 'BACKUP')}

          {/* Heartbeat line between DIST01 and DIST02 */}
          <line x1="235" y1="140" x2="445" y2="140" stroke="#4f46e5" strokeWidth="2" strokeDasharray="4 3" />
          <text x="340" y="135" fill="#818cf8" fontSize="8" fontFamily="monospace" textAnchor="middle">VRRP Heartbeat</text>

          {/* Trunk links from Core to Dist */}
          <line x1="322" y1="65" x2="225" y2="125" stroke="#334155" strokeWidth="2" />
          <line x1="358" y1="65" x2="455" y2="125" stroke="#334155" strokeWidth="2" />

          {/* ── ACCESS LAYER: NT-ACC01, NT-ACC02 (Target), NT-ACC03 ── */}
          {renderRoundNode(120, 230, 'NT-ACC01', 'Admin (VLAN 110)', 15, '#10b981', 'ONLINE')}
          {renderRoundNode(
            340,
            230,
            'NT-ACC02',
            'Sales (VLAN 120)',
            17,
            isFault ? '#f43f5e' : isHealing ? '#22d3ee' : '#10b981',
            isFault ? 'OFFLINE' : isHealing ? 'RECOVERING' : 'ONLINE'
          )}
          {renderRoundNode(560, 230, 'NT-ACC03', 'Acc (VLAN 130)', 15, '#10b981', 'ONLINE')}

          {/* Normal Link: NT-DIST01 -> NT-ACC01 */}
          <line x1="195" y1="155" x2="135" y2="215" stroke="#334155" strokeWidth="1.8" />
          {/* Normal Link: NT-DIST02 -> NT-ACC03 */}
          <line x1="485" y1="155" x2="545" y2="215" stroke="#334155" strokeWidth="1.8" />

          {/* ── TARGET LINK: NT-DIST01 <-> NT-ACC02 ── */}
          <line
            x1="225"
            y1="155"
            x2="325"
            y2="218"
            stroke={isFault ? '#f43f5e' : isRestored ? '#10b981' : '#06b6d4'}
            strokeWidth={isFault ? 3.5 : 2.5}
            strokeDasharray={isFault ? '6 4' : 'none'}
          />

          {/* ── BACKUP RSTP LINK: NT-DIST02 <-> NT-ACC02 ── */}
          <line
            x1="455"
            y1="155"
            x2="355"
            y2="218"
            stroke={isRestored || isHealing ? '#22d3ee' : '#334155'}
            strokeWidth={isRestored || isHealing ? 3 : 1.5}
            strokeDasharray={isRestored ? 'none' : '4 4'}
          />

          {/* Endpoints: SALES PC Group */}
          <g transform="translate(340, 290)">
            <rect x="-65" y="-10" width="130" height="20" rx="4" fill="#0f172a" stroke="#475569" strokeWidth="1.2" />
            <text x="0" y="4" fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">
              3 PC SALES (10.20.20.0/24)
            </text>
          </g>
          <line x1="340" y1="247" x2="340" y2="280" stroke="#334155" strokeWidth="1.5" />

          {/* ── VISUAL ANNOTATION & SPARK ── */}
          {isFault && (
            <g transform="translate(275, 185)">
              <circle cx="0" cy="0" r="16" fill="#450a0a" stroke="#f43f5e" strokeWidth="2" className="animate-pulse" />
              <text x="0" y="4" fill="#f43f5e" fontSize="12" textAnchor="middle">⚡</text>
              <rect x="-70" y="16" width="140" height="18" rx="4" fill="#090d16" stroke="#f43f5e" />
              <text x="0" y="28" fill="#fda4af" fontSize="8" fontFamily="monospace" textAnchor="middle">
                OFPT_PORT_STATUS: DOWN (100% Drop)
              </text>
            </g>
          )}

          {/* Healing Action */}
          {isHealing && (
            <g transform="translate(275, 185)">
              <rect x="-75" y="-10" width="150" height="20" rx="4" fill="#083344" stroke="#22d3ee" />
              <text x="0" y="3" fill="#a5f3fc" fontSize="8" fontFamily="monospace" textAnchor="middle">
                FAUCET: OFPPC_PORT_UP & RSTP
              </text>
            </g>
          )}

          {/* Restored Success Tag */}
          {isRestored && (
            <g transform="translate(275, 185)">
              <rect x="-60" y="-10" width="120" height="20" rx="4" fill="#064e3b" stroke="#10b981" />
              <text x="0" y="3" fill="#a7f3d0" fontSize="8" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                ✓ PORT UP & RECOVERED
              </text>
            </g>
          )}

          {/* Flow Particles */}
          {(phase === 1 || isRestored) && (
            <circle cx={225 + 100 * tProg} cy={155 + 63 * tProg} r={3.5} fill="#34d399" filter="url(#sim-glow)" />
          )}
          {(isRestored || isHealing) && (
            <circle cx={455 - 100 * tProg} cy={155 + 63 * tProg} r={3.5} fill="#22d3ee" filter="url(#sim-glow)" />
          )}
        </svg>
      );
    }

    // KỊCH BẢN 2: F02 - Distribution Failure VRRP Failover
    if (sc.id === 'F02') {
      return (
        <svg className="w-full h-full" viewBox="0 0 680 320">
          <rect width="680" height="320" fill="#070b14" rx="8" />

          {/* Core Switch */}
          {renderRoundNode(340, 50, 'NT-CORE', 'Root STP 4096', 22, '#06b6d4', 'ONLINE')}

          {/* DIST01 (VRRP Master - crashing) */}
          {renderRoundNode(
            210,
            140,
            'NT-DIST01',
            isFault ? 'CRASHED / DEAD' : 'VRRP Master (VIP .1)',
            20,
            isFault ? '#f43f5e' : '#6366f1',
            isFault ? 'OFFLINE' : 'ONLINE',
            isFault ? 'DEAD' : 'MASTER'
          )}

          {/* DIST02 (VRRP Backup - becoming Master) */}
          {renderRoundNode(
            470,
            140,
            'NT-DIST02',
            isFault || isHealing || isRestored ? 'MASTER (VIP .1 TIẾP QUẢN)' : 'VRRP Backup',
            20,
            isFault || isHealing || isRestored ? '#22d3ee' : '#6366f1',
            'ONLINE',
            isFault || isHealing || isRestored ? 'MASTER' : 'BACKUP'
          )}

          {/* Trunk from Core to Dist */}
          <line x1="322" y1="65" x2="225" y2="125" stroke={isFault ? '#f43f5e' : '#334155'} strokeWidth="2" strokeDasharray={isFault ? '4 4' : 'none'} />
          <line x1="358" y1="65" x2="455" y2="125" stroke="#334155" strokeWidth="2" />

          {/* VRRP Heartbeat failed */}
          <line x1="235" y1="140" x2="445" y2="140" stroke={isFault ? '#f43f5e' : '#4f46e5'} strokeWidth={2} strokeDasharray="4 3" />
          <text x="340" y="133" fill={isFault ? '#f43f5e' : '#818cf8'} fontSize="8" fontFamily="monospace" textAnchor="middle">
            {isFault ? 'HEARTBEAT LOST (DEAD TIMER 3s)' : 'VRRP Heartbeat (1s)'}
          </text>

          {/* Access Switch at Bottom */}
          {renderRoundNode(340, 240, 'NT-ACCESS', 'Access Switch Layer (VLANs 110-190)', 17, '#10b981', 'ONLINE')}

          {/* Links to Access switch */}
          <line
            x1="210"
            y1="160"
            x2="330"
            y2="228"
            stroke={isFault || isHealing || isRestored ? '#f43f5e' : '#22c55e'}
            strokeWidth={isFault || isHealing || isRestored ? 2 : 3}
            strokeDasharray={isFault || isHealing || isRestored ? '5 5' : 'none'}
          />
          <line
            x1="470"
            y1="160"
            x2="350"
            y2="228"
            stroke={isFault || isHealing || isRestored ? '#22d3ee' : '#334155'}
            strokeWidth={isFault || isHealing || isRestored ? 3.5 : 1.5}
          />

          {/* Failover Gratuitous ARP Notification */}
          {(isHealing || isRestored) && (
            <g transform="translate(340, 185)">
              <rect x="-85" y="-12" width="170" height="24" rx="4" fill="#083344" stroke="#22d3ee" strokeWidth="1.5" />
              <text x="0" y="4" fill="#67e8f9" fontSize="8" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                GRATUITOUS ARP: VIP &rarr; NT-DIST02
              </text>
            </g>
          )}

          {/* Active Flow particle */}
          <circle
            cx={isFault || isHealing || isRestored ? 350 + 120 * tProg : 330 - 120 * tProg}
            cy={228 - 68 * tProg}
            r={3.5}
            fill="#ffffff"
          />
        </svg>
      );
    }

    // KỊCH BẢN 3: F04 (MPLS Down -> 5G Failover) & CÁC SỰ CỐ WAN
    return (
      <svg className="w-full h-full" viewBox="0 0 680 320">
        <defs>
          <filter id="wan-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <rect width="680" height="320" fill="#070b14" rx="8" />

        {/* ── 3 THIẾT BỊ CORE CHI NHÁNH Ở PHÍA TRÁI (BL-GW, NT-CORE, HCM-CORE) ── */}
        {/* 1. Chi Nhánh Bảo Lộc Core */}
        {renderRoundNode(80, 75, 'BL-GW', 'Core BL-GW', 18, '#10b981', 'ONLINE')}
        {/* 2. Chi Nhánh Nha Trang Core */}
        {renderRoundNode(80, 160, 'NT-CORE', 'Core Nha Trang', 18, '#06b6d4', 'ONLINE')}
        {/* 3. Chi Nhánh TP.HCM Core */}
        {renderRoundNode(80, 245, 'HCM-CORE', 'Core TP.HCM', 18, '#818cf8', 'ONLINE')}

        {/* Cột nhãn 3 Core chi nhánh */}
        <text x="80" y="295" fill="#38bdf8" fontSize="8.5" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          3 CORE CHI NHÁNH ➔ DC
        </text>

        {/* ── DATA CENTER GATEWAY Ở PHÍA PHẢI: DC-SP-GW ── */}
        {renderRoundNode(590, 160, 'DC-SP-GW', 'Data Center Gateway', 24, '#a855f7', 'ONLINE')}
        <g transform={`translate(590, 235)`}>
          <rect x="-70" y="-10" width="140" height="20" rx="4" fill="#0f172a" stroke="#334155" />
          <text x="0" y="4" fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">
            HAProxy VIP 10.100.10.10
          </text>
        </g>
        <line x1="590" y1="184" x2="590" y2="225" stroke="#334155" strokeWidth="1.5" />
        <text x="590" y="275" fill="#c084fc" fontSize="8.5" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          DATA CENTER HUB (TẬP TRUNG)
        </text>

        {/* ── CÁC TUYẾN DẪN TỪ 3 CORE VÀO WAN BUS ── */}
        {/* Từ BL-GW vào điểm rẽ WAN (160, 160) */}
        <line x1="98" y1="80" x2="160" y2="140" stroke="#10b981" strokeWidth={1.8} strokeDasharray="3 3" opacity={0.7} />
        {/* Từ NT-CORE vào điểm rẽ WAN (160, 160) */}
        <line x1="98" y1="160" x2="160" y2="160" stroke="#06b6d4" strokeWidth={1.8} opacity={0.7} />
        {/* Từ HCM-CORE vào điểm rẽ WAN (160, 160) */}
        <line x1="98" y1="240" x2="160" y2="180" stroke="#818cf8" strokeWidth={1.8} strokeDasharray="3 3" opacity={0.7} />

        {/* ── 1. MPLS PATH (PRIMARY WAN - CẢ 3 CHI NHÁNH ĐỔ VỀ DC) ── */}
        <path
          d="M 160 140 C 270 65, 470 65, 566 145"
          fill="none"
          stroke={isFault && sc.id === 'F04' ? '#f43f5e' : isFault && sc.id === 'F09' ? '#f59e0b' : '#10b981'}
          strokeWidth={isFault && sc.id === 'F04' ? 4 : 3}
          strokeDasharray={isFault && sc.id === 'F04' ? '7 4' : 'none'}
        />
        <g transform="translate(365, 80)">
          <rect
            x="-110"
            y="-14"
            width="220"
            height="26"
            rx="5"
            fill="#090d16"
            stroke={isFault && sc.id === 'F04' ? '#f43f5e' : '#10b981'}
            strokeWidth={1.5}
          />
          <text
            x="0"
            y="2"
            fill={isFault && sc.id === 'F04' ? '#f43f5e' : '#10b981'}
            fontSize={8.5}
            fontWeight="bold"
            fontFamily="monospace"
            textAnchor="middle"
          >
            {isFault && sc.id === 'F04'
              ? '❌ MPLS DOWN: 3 CHI NHÁNH MẤT ROUTE DC'
              : isFault && sc.id === 'F09'
              ? '⚠️ MPLS NGHẼN 88% (3 CHI NHÁNH)'
              : 'MPLS: 3 CHI NHÁNH ➔ DATA CENTER (100M)'}
          </text>
        </g>

        {/* ── 2. 5G PATH (BACKUP / FAILOVER - ĐIỀU HƯỚNG TẤT CẢ VỀ DC) ── */}
        <path
          d="M 160 180 C 270 255, 470 255, 566 175"
          fill="none"
          stroke={isRestored || isHealing ? '#06b6d4' : '#334155'}
          strokeWidth={isRestored || isHealing ? 4 : 1.8}
          strokeDasharray={isRestored ? 'none' : '5 4'}
        />
        <g transform="translate(365, 240)">
          <rect
            x="-115"
            y="-14"
            width="230"
            height="26"
            rx="5"
            fill="#090d16"
            stroke={isRestored || isHealing ? '#06b6d4' : '#475569'}
            strokeWidth={1.5}
          />
          <text
            x="0"
            y="2"
            fill={isRestored || isHealing ? '#38bdf8' : '#94a3b8'}
            fontSize={8.5}
            fontWeight="bold"
            fontFamily="monospace"
            textAnchor="middle"
          >
            {isRestored || isHealing
              ? '⚡ 5G FAILOVER: CẢ 3 CHI NHÁNH ĐỔ VỀ DC'
              : '5G BACKUP DỰ PHÒNG (200M · 15ms)'}
          </text>
        </g>

        {/* Traffic packet on MPLS when normal */}
        {(phase === 1 && sc.id === 'F04') && (
          <circle cx={160 + 406 * tProg} cy={140 - Math.sin(tProg * Math.PI) * 60} r={4} fill="#34d399" filter="url(#wan-glow)" />
        )}

        {/* Rerouted packet on 5G when healed */}
        {(isRestored || isHealing) && (
          <circle cx={160 + 406 * tProg} cy={180 + Math.sin(tProg * Math.PI) * 60} r={4.5} fill="#22d3ee" filter="url(#wan-glow)" />
        )}

        {/* SD-WAN Steering Policy Badge */}
        {(isHealing || isRestored) && (
          <g transform="translate(365, 160)">
            <rect x="-120" y="-14" width="240" height="28" rx="6" fill="#083344" stroke="#22d3ee" strokeWidth={1.5} />
            <text x="0" y="4" fill="#a5f3fc" fontSize="8.5" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
              SD-WAN: CHUYỂN TẤT CẢ CHI NHÁNH SANG 5G ➔ DC
            </text>
          </g>
        )}
      </svg>
    );
  }

  // Helper to render Authentic Round Nodes (giống hệt bản vẽ lớn)
  function renderRoundNode(
    x: number,
    y: number,
    id: string,
    sub: string,
    radius: number,
    strokeCol: string,
    status: NodeStatus,
    vrrpBadge?: string
  ) {
    const isDown = status === 'OFFLINE';
    const isRecovering = status === 'RECOVERING';

    return (
      <g transform={`translate(${x}, ${y})`}>
        {isDown && (
          <circle cx="0" cy="0" r={radius + 10} fill="none" stroke="#f43f5e" strokeWidth="2" opacity="0.8" className="animate-ping" />
        )}

        {/* Base circle */}
        <circle
          cx="0"
          cy="0"
          r={radius}
          fill={isDown ? '#450a0a' : isRecovering ? '#083344' : '#0f172a'}
          stroke={isDown ? '#f43f5e' : isRecovering ? '#22d3ee' : strokeCol}
          strokeWidth={2.5}
        />

        {/* Center dot */}
        <circle cx="0" cy="0" r={3.5} fill={isDown ? '#f43f5e' : isRecovering ? '#22d3ee' : '#34d399'} />

        {/* Name underneath */}
        <text
          x="0"
          y={radius + 13}
          fill={isDown ? '#f43f5e' : '#f8fafc'}
          fontSize={10}
          fontWeight="bold"
          fontFamily="monospace"
          textAnchor="middle"
        >
          {id}
        </text>

        {/* Subtitle */}
        <text x="0" y={radius + 24} fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">
          {sub}
        </text>

        {/* VRRP Badge if any */}
        {vrrpBadge && (
          <g transform={`translate(0, ${-radius - 10})`}>
            <rect
              x="-26"
              y="-7"
              width="52"
              height="14"
              rx="3"
              fill={vrrpBadge === 'MASTER' ? '#312e81' : '#1e293b'}
              stroke={vrrpBadge === 'MASTER' ? '#818cf8' : '#475569'}
              strokeWidth="1"
            />
            <text x="0" y="3" fill={vrrpBadge === 'MASTER' ? '#c7d2fe' : '#94a3b8'} fontSize="7" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
              {vrrpBadge}
            </text>
          </g>
        )}
      </g>
    );
  }

  // Explanation generator for the 4 phases
  function getPhaseExplanation(sc: FaultScenario, phase: 1 | 2 | 3 | 4): string {
    switch (phase) {
      case 1:
        return `Trạng thái 1 (Bình thường): Toàn bộ các luồng ứng dụng và tuyến mạng đang hoạt động danh nghĩa theo chính sách ban đầu.`;
      case 2:
        return `Trạng thái 2 (Gặp sự cố): Sự cố ${sc.id} xảy ra trên ${sc.targetDevice}. Cáp bị ngắt, gói tin bị rơi rụng (100% Drop), đường truyền chuyển màu đỏ rực.`;
      case 3:
        return `Trạng thái 3 (AI can thiệp): Bộ não AI (PPO Agent / SD-WAN Controller) phát hiện sự cố, Safety Layer phê duyệt và kích hoạt tuyến dự phòng (${sc.ppoAction}).`;
      case 4:
      default:
        return `Trạng thái 4 (Hồi phục hoàn toàn): Lưu lượng đã được chuyển tiếp trơn tru sang tuyến mới (${sc.recoveryFlow}). Không làm rớt cuộc gọi hay gián đoạn dịch vụ của doanh nghiệp!`;
    }
  }
};
