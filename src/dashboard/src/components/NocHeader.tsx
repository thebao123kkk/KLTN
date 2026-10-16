import React from 'react';
import { 
  Radio, 
  Clock, 
  ShieldCheck, 
  Palette
} from 'lucide-react';

export type ThemePalette = 'cyan' | 'blue' | 'emerald';

interface NocHeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onlineCount: number;
  totalNodes: number;
  activeFaultsCount: number;
  averageMttr: number;
  slaPercent: number;
  themeColor: ThemePalette;
  setThemeColor: (theme: ThemePalette) => void;
}

export const NocHeader: React.FC<NocHeaderProps> = ({
  activeTab,
  setActiveTab,
  onlineCount,
  totalNodes,
  activeFaultsCount,
  averageMttr,
  slaPercent,
  themeColor,
  setThemeColor,
}) => {
  const [timeStr, setTimeStr] = React.useState<string>('');

  React.useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('vi-VN', { hour12: false }) + ' UTC+7');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'topology', label: 'Bản Vẽ Topology Kiến Trúc (Blueprint)' },
    { id: 'scenarios', label: 'Trực Quan Hóa 14 Kịch Bản (Topology Gặp Lỗi & Hồi Phục)' },
    { id: 'wan', label: 'Giám Sát 5 Kênh WAN' },
    { id: 'ai-engine', label: 'Bộ Não AI & PPO RL Agent' },
    { id: 'logs', label: 'Nhật Ký Tự Phục Hồi' },
  ];

  const getAccentText = () => {
    switch (themeColor) {
      case 'blue': return 'text-blue-400';
      case 'emerald': return 'text-emerald-400';
      case 'cyan':
      default: return 'text-cyan-400';
    }
  };

  const getActiveTabStyle = (isActive: boolean) => {
    if (!isActive) return 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50';
    switch (themeColor) {
      case 'blue': return 'border-blue-500 text-blue-300 bg-blue-950/30';
      case 'emerald': return 'border-emerald-500 text-emerald-300 bg-emerald-950/30';
      case 'cyan':
      default: return 'border-cyan-400 text-cyan-300 bg-cyan-950/20';
    }
  };

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/95 backdrop-blur sticky top-0 z-40">
      {/* Top tier: Brand, Clock, Metrics & Theme Selector */}
      <div className="flex flex-wrap items-center justify-between px-4 lg:px-6 py-2.5 border-b border-slate-800/60 gap-3">
        {/* Brand Zone */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 flex items-center justify-center text-slate-950 font-black shadow-lg shadow-cyan-950/50">
            <Radio className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-white uppercase font-mono">
                MININET ENTERPRISE NOC
              </span>
              <span className="text-slate-600">·</span>
              <span className={`text-xs font-semibold font-mono tracking-wider ${getAccentText()}`}>
                SDN & SD-WAN AI MESH
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Giám sát thời gian thực 3 Chi nhánh + Data Center · Closed-Loop Self-Healing
            </p>
          </div>
        </div>

        {/* System telemetry quick metrics */}
        <div className="hidden xl:flex items-center gap-5 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-slate-400">Node Online:</span>
            <span className="text-emerald-400 font-bold tabular-nums">
              {onlineCount}/{totalNodes} (88 Endpoints)
            </span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${activeFaultsCount > 0 ? 'bg-rose-500 animate-pulse' : 'bg-slate-600'}`} />
            <span className="text-slate-400">Sự cố đang xảy ra:</span>
            <span className={`font-bold tabular-nums ${activeFaultsCount > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
              {activeFaultsCount}
            </span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="flex items-center gap-2">
            <Clock className={`w-3.5 h-3.5 ${getAccentText()}`} />
            <span className="text-slate-400">MTTR Trung Bình:</span>
            <span className={`font-bold tabular-nums ${getAccentText()}`}>
              {averageMttr.toFixed(1)}s
            </span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">SLA:</span>
            <span className="text-emerald-400 font-bold tabular-nums">
              {slaPercent}%
            </span>
          </div>
        </div>

        {/* Right Zone: Custom Color Theme Selector & Clock */}
        <div className="flex items-center gap-3">
          {/* Custom Theme Selector */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono">
            <Palette className="w-3.5 h-3.5 text-slate-400 mr-1" />
            <span className="text-[10px] text-slate-400 mr-1">Theme:</span>
            <button
              onClick={() => setThemeColor('cyan')}
              className={`w-3.5 h-3.5 rounded-full bg-cyan-400 transition-transform ${
                themeColor === 'cyan' ? 'ring-2 ring-white scale-110' : 'opacity-60 hover:opacity-100'
              }`}
              title="Cyan Cyberpunk Theme"
            />
            <button
              onClick={() => setThemeColor('blue')}
              className={`w-3.5 h-3.5 rounded-full bg-blue-500 transition-transform ${
                themeColor === 'blue' ? 'ring-2 ring-white scale-110' : 'opacity-60 hover:opacity-100'
              }`}
              title="Cisco Sapphire Blue Theme"
            />
            <button
              onClick={() => setThemeColor('emerald')}
              className={`w-3.5 h-3.5 rounded-full bg-emerald-400 transition-transform ${
                themeColor === 'emerald' ? 'ring-2 ring-white scale-110' : 'opacity-60 hover:opacity-100'
              }`}
              title="Matrix Emerald Green Theme"
            />
          </div>

          {/* Clock */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
            <span className={`w-1.5 h-1.5 rounded-full ${themeColor === 'blue' ? 'bg-blue-400' : themeColor === 'emerald' ? 'bg-emerald-400' : 'bg-cyan-400'}`} />
            <span>{timeStr}</span>
          </div>
        </div>
      </div>

      {/* Nav Navigation Tab Bar */}
      <div className="flex items-center px-4 lg:px-6 overflow-x-auto border-t border-slate-900 bg-slate-950">
        <nav className="flex space-x-1 py-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`px-3.5 py-2 text-xs font-medium transition-colors whitespace-nowrap border-b-2 flex items-center gap-1.5 ${getActiveTabStyle(isActive)}`}
              >
                <span>{item.label}</span>
                {item.id === 'scenarios' && activeFaultsCount > 0 && (
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
