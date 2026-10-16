import React, { useState } from 'react';
import { FaultScenario, FaultId } from '../types/network';
import { 
  Flame, 
  RotateCcw, 
  Terminal, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ShieldCheck, 
  Layers, 
  Cpu, 
  Zap,
  ArrowRight
} from 'lucide-react';

interface FaultScenariosPanelProps {
  scenarios: FaultScenario[];
  activeScenarioId?: FaultId;
  onInjectFault: (scenario: FaultScenario) => void;
  onResetNetwork: () => void;
  executingStage?: string;
  measuredMttr?: number;
}

export const FaultScenariosPanel: React.FC<FaultScenariosPanelProps> = ({
  scenarios,
  activeScenarioId,
  onInjectFault,
  onResetNetwork,
  executingStage,
  measuredMttr,
}) => {
  const [activeTab, setActiveTab] = useState<'reactive' | 'proactive'>('reactive');
  const [selectedScenario, setSelectedScenario] = useState<FaultScenario>(scenarios[0]);
  const [showCliSnippet, setShowCliSnippet] = useState<boolean>(true);

  const filteredScenarios = scenarios.filter((s) =>
    activeTab === 'reactive' ? s.type === 'Reactive' : s.type === 'Proactive'
  );

  return (
    <div className="space-y-4">
      {/* Top Banner: Fault Injection Framework Overview */}
      <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-amber-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              BỘ 14 KỊCH BẢN THỬ NGHIỆM SỰ CỐ & KHÔI PHỤC TỰ ĐỘNG (KLTN PHASE 19 & 20)
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Diễn tập vòng lặp tự phục hồi khép kín: Telemetry &rarr; Anomaly Detection &rarr; RCA &rarr; Safety Layer &rarr; PPO / SD-WAN Execution &rarr; Verify
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-950 p-1 rounded border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setActiveTab('reactive')}
              className={`px-3 py-1 rounded transition-colors ${
                activeTab === 'reactive'
                  ? 'bg-rose-950 text-rose-200 border border-rose-800 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              12 Reactive (F01 - F12)
            </button>
            <button
              onClick={() => setActiveTab('proactive')}
              className={`px-3 py-1 rounded transition-colors ${
                activeTab === 'proactive'
                  ? 'bg-amber-950 text-amber-200 border border-amber-800 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              2 Proactive (P1, P2)
            </button>
          </div>

          <button
            onClick={onResetNetwork}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-slate-800 text-slate-300 hover:text-white rounded border border-slate-700 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Toàn Mạng</span>
          </button>
        </div>
      </div>

      {/* Main Layout: List of Scenarios on Left, Interactive Runner on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Scenario Selector Grid (5 cols) */}
        <div className="lg:col-span-5 space-y-2 max-h-[640px] overflow-y-auto pr-1">
          {filteredScenarios.map((sc) => {
            const isActive = activeScenarioId === sc.id;
            const isSelected = selectedScenario.id === sc.id;

            return (
              <div
                key={sc.id}
                onClick={() => setSelectedScenario(sc)}
                className={`p-3 rounded-lg border text-xs font-mono cursor-pointer transition-all ${
                  isActive
                    ? 'bg-rose-950/60 border-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.4)]'
                    : isSelected
                    ? 'bg-slate-900 border-cyan-500/80'
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
                  <span>Miền: <strong className="text-slate-300">{sc.category}</strong></span>
                  <span>Đích: <strong className="text-slate-300">{sc.targetDevice}</strong></span>
                </div>

                {isActive && (
                  <div className="mt-2 flex items-center gap-1.5 text-rose-400 font-bold text-[11px]">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                    <span>SỰ CỐ ĐANG KÍCH HOẠT - VÒNG LẶP ĐANG XỬ LÝ...</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Right Column: Scenario Detail & Self-Healing Loop Visualizer (7 cols) */}
        <div className="lg:col-span-7 p-4 bg-slate-900/70 border border-slate-800 rounded-lg space-y-4">
          <div className="flex items-start justify-between pb-3 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-cyan-400 font-mono">
                  [{selectedScenario.id}] {selectedScenario.name}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                  {selectedScenario.category}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Bộ điều khiển: <strong className="text-slate-200">{selectedScenario.controller}</strong> · Đối tượng ảnh hưởng: <strong className="text-slate-200">{selectedScenario.targetDevice}</strong>
              </p>
            </div>

            <button
              onClick={() => onInjectFault(selectedScenario)}
              className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 rounded font-mono shadow-lg shadow-rose-950/60 transition-all whitespace-nowrap"
            >
              <Flame className="w-4 h-4 animate-bounce" />
              <span>TIÊM SỰ CỐ NÀY</span>
            </button>
          </div>

          {/* Real-time Closed-Loop Stage Tracker */}
          {activeScenarioId === selectedScenario.id && (
            <div className="p-3.5 bg-slate-950 border border-cyan-800/80 rounded-lg space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                  <span className="text-cyan-300 font-bold uppercase">
                    TIẾN TRÌNH VÒNG LẶP CLOSED-LOOP: {executingStage || 'Đang thực thi...'}
                  </span>
                </div>
                {measuredMttr !== undefined && (
                  <span className="text-emerald-400 font-bold">
                    MTTR Thực Tế: {measuredMttr.toFixed(1)}s
                  </span>
                )}
              </div>

              {/* 5-Stage Stepper Bar */}
              <div className="grid grid-cols-5 gap-1.5 pt-1 text-[10px] font-mono text-center">
                <div className="p-1 rounded bg-cyan-950 border border-cyan-700 text-cyan-300">
                  1. Telemetry Detect
                </div>
                <div className="p-1 rounded bg-cyan-950 border border-cyan-700 text-cyan-300">
                  2. RCA Analysis
                </div>
                <div className="p-1 rounded bg-cyan-950 border border-cyan-700 text-cyan-300">
                  3. Safety Check
                </div>
                <div className="p-1 rounded bg-cyan-950 border border-cyan-700 text-cyan-300">
                  4. PPO / SD-WAN
                </div>
                <div className="p-1 rounded bg-emerald-950 border border-emerald-700 text-emerald-300">
                  5. Recovered
                </div>
              </div>
            </div>
          )}

          {/* 4 Cards: Symptom, Detection, RCA, Recovery */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
            {/* Symptom */}
            <div className="p-3 rounded bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-rose-400 font-bold uppercase block mb-1">
                1. Hiện Tượng & Tác Động (Symptom)
              </span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {selectedScenario.symptom}
              </p>
            </div>

            {/* Detection */}
            <div className="p-3 rounded bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-cyan-400 font-bold uppercase block mb-1">
                2. Cơ Chế Phát Hiện (Detection)
              </span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {selectedScenario.detectionMechanism}
              </p>
            </div>

            {/* RCA */}
            <div className="p-3 rounded bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-purple-400 font-bold uppercase block mb-1">
                3. Nguyên Nhân Gốc Rễ (RCA Engine)
              </span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {selectedScenario.rootCauseAnalysis}
              </p>
            </div>

            {/* Recovery Flow */}
            <div className="p-3 rounded bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-emerald-400 font-bold uppercase block mb-1">
                4. Luồng Tự Phục Hồi (Self-Healing Flow)
              </span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {selectedScenario.recoveryFlow}
              </p>
              <div className="mt-1 pt-1 border-t border-slate-800 text-[10px] text-amber-300">
                Action: {selectedScenario.ppoAction}
              </div>
            </div>
          </div>

          {/* Mininet Fault Injection CLI Snippet */}
          <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-1.5 text-slate-400">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span>Lệnh Mininet Python / Bash để tiêm sự cố này:</span>
              </div>
              <span className="text-[10px] text-slate-500">Copy vào Mininet CLI</span>
            </div>
            <pre className="p-2 rounded bg-slate-900 border border-slate-800 text-emerald-400 text-[11px] font-mono overflow-x-auto whitespace-pre-wrap">
              {selectedScenario.commandSnippet}
            </pre>
          </div>

          {/* MTTR Comparison Table */}
          <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between text-xs font-mono">
            <div>
              <span className="text-slate-400 block text-[11px]">MTTR Mạng Truyền Thống:</span>
              <span className="text-rose-400 font-bold line-through">15 - 30 Phút (Thủ công)</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-600" />
            <div>
              <span className="text-slate-400 block text-[11px]">MTTR Tự Phục Hồi AI (Mục tiêu):</span>
              <span className="text-emerald-400 font-bold text-sm">{selectedScenario.targetMttr}</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-600" />
            <div>
              <span className="text-slate-400 block text-[11px]">Hệ Số Tăng Tốc:</span>
              <span className="text-cyan-300 font-bold text-sm">60x &ndash; 360x Nhanh Hơn</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
