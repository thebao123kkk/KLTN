import React, { useState } from 'react';
import { 
  NetworkNode, 
  NetworkLink, 
  SiteId, 
  NodeStatus 
} from '../types/network';
import { 
  Server, 
  Router, 
  Layers, 
  Cpu, 
  Laptop, 
  ShieldAlert, 
  CheckCircle, 
  AlertOctagon, 
  Wifi, 
  Activity, 
  Radio,
  ArrowRightLeft,
  Maximize2,
  ZoomIn,
  ZoomOut
} from 'lucide-react';

interface TopologyCanvasProps {
  nodes: NetworkNode[];
  links: NetworkLink[];
  onSelectNode: (node: NetworkNode) => void;
  selectedNodeId?: string;
  activeFaultId?: string;
}

export const TopologyCanvas: React.FC<TopologyCanvasProps> = ({
  nodes,
  links,
  onSelectNode,
  selectedNodeId,
  activeFaultId,
}) => {
  const [filterSite, setFilterSite] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  const filteredNodes = nodes.filter((n) => {
    if (filterSite !== 'all' && n.site !== filterSite) return false;
    if (filterStatus === 'fault' && n.status === 'ONLINE') return false;
    if (filterStatus === 'online' && n.status !== 'ONLINE') return false;
    return true;
  });

  const getStatusColor = (status: NodeStatus) => {
    switch (status) {
      case 'ONLINE':
        return {
          bg: 'bg-emerald-950/40',
          border: 'border-emerald-500/80',
          text: 'text-emerald-400',
          dot: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]',
          glow: 'hover:shadow-[0_0_12px_rgba(16,185,129,0.3)]',
        };
      case 'OFFLINE':
        return {
          bg: 'bg-rose-950/70',
          border: 'border-rose-500 animate-pulse',
          text: 'text-rose-400 font-bold',
          dot: 'bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,1)] animate-ping',
          glow: 'shadow-[0_0_15px_rgba(244,63,94,0.6)]',
        };
      case 'DEGRADED':
        return {
          bg: 'bg-amber-950/60',
          border: 'border-amber-500',
          text: 'text-amber-400',
          dot: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]',
          glow: 'shadow-[0_0_12px_rgba(245,158,11,0.4)]',
        };
      case 'RECOVERING':
        return {
          bg: 'bg-cyan-950/60',
          border: 'border-cyan-400 animate-pulse',
          text: 'text-cyan-300',
          dot: 'bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.9)] animate-spin',
          glow: 'shadow-[0_0_15px_rgba(6,182,212,0.5)]',
        };
    }
  };

  const getNodeIcon = (role: string) => {
    switch (role) {
      case 'core':
      case 'spine':
        return <Layers className="w-4 h-4 text-cyan-400" />;
      case 'dist':
      case 'gateway':
        return <Router className="w-4 h-4 text-indigo-400" />;
      case 'access':
      case 'leaf':
        return <Cpu className="w-4 h-4 text-emerald-400" />;
      case 'server':
        return <Server className="w-4 h-4 text-purple-400" />;
      case 'host':
      default:
        return <Laptop className="w-4 h-4 text-slate-400" />;
    }
  };

  // Group nodes by site for visual partition cards
  const baolocNodes = filteredNodes.filter((n) => n.site === 'baoloc');
  const nhatrangNodes = filteredNodes.filter((n) => n.site === 'nhatrang');
  const hcmNodes = filteredNodes.filter((n) => n.site === 'hcm');
  const dcNodes = filteredNodes.filter((n) => n.site === 'datacenter');

  const wanLinks = links.filter((l) => l.transport !== 'INTERNAL_LAN');

  return (
    <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-lg overflow-hidden">
      {/* Control Toolbar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 gap-3">
        {/* Left: Filter Controls */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Site:</span>
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded border border-slate-800 text-xs">
            {['all', 'baoloc', 'nhatrang', 'hcm', 'datacenter'].map((s) => (
              <button
                key={s}
                onClick={() => setFilterSite(s)}
                className={`px-2.5 py-1 rounded transition-colors whitespace-nowrap capitalize ${
                  filterSite === s
                    ? 'bg-cyan-900/60 text-cyan-200 border border-cyan-700/60 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {s === 'all'
                  ? 'Toàn mạng'
                  : s === 'baoloc'
                  ? 'Bảo Lộc'
                  : s === 'nhatrang'
                  ? 'Nha Trang'
                  : s === 'hcm'
                  ? 'TP.HCM'
                  : 'Data Center'}
              </button>
            ))}
          </div>

          <div className="hidden sm:flex items-center gap-1 bg-slate-950 p-1 rounded border border-slate-800 text-xs ml-2">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-2 py-0.5 rounded ${
                filterStatus === 'all' ? 'bg-slate-800 text-white' : 'text-slate-400'
              }`}
            >
              Tất cả
            </button>
            <button
              onClick={() => setFilterStatus('fault')}
              className={`px-2 py-0.5 rounded ${
                filterStatus === 'fault' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'text-slate-400'
              }`}
            >
              Có sự cố
            </button>
            <button
              onClick={() => setFilterStatus('online')}
              className={`px-2 py-0.5 rounded ${
                filterStatus === 'online' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'text-slate-400'
              }`}
            >
              Online
            </button>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
            <span className="text-slate-300">Online</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)]" />
            <span className="text-slate-300">Offline / Down</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span className="text-slate-300">Degraded / Jitter</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
            <span className="text-slate-300">Recovering</span>
          </div>
        </div>
      </div>

      {/* Main Multi-Region Grid Visualizer */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {/* Top Overlay: 5 WAN Transports Mesh Bar */}
        <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
          <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
              <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                SD-WAN Inter-Site Mesh (5 Transports KLTN Phase 9)
              </span>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Điều hướng động dựa trên SLA và độ trễ
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-2.5">
            {wanLinks.map((wl) => {
              const isDown = wl.status === 'DOWN';
              const isCongested = wl.status === 'CONGESTED' || wl.lossPercent > 5;
              const isSteered = wl.status === 'STEERED';

              return (
                <div
                  key={wl.id}
                  className={`p-2 rounded border text-xs font-mono transition-all ${
                    isDown
                      ? 'bg-rose-950/50 border-rose-600 shadow-[0_0_10px_rgba(225,29,72,0.4)]'
                      : isCongested
                      ? 'bg-amber-950/40 border-amber-600'
                      : isSteered
                      ? 'bg-cyan-950/50 border-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.3)]'
                      : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{wl.transport}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${
                        isDown
                          ? 'bg-rose-900 text-rose-200'
                          : isCongested
                          ? 'bg-amber-900 text-amber-200'
                          : isSteered
                          ? 'bg-cyan-900 text-cyan-200'
                          : 'bg-emerald-950 text-emerald-400'
                      }`}
                    >
                      {wl.status}
                    </span>
                  </div>

                  <div className="mt-1 flex items-center justify-between text-[11px] text-slate-400">
                    <span>
                      RTT: <strong className="text-slate-200">{wl.latencyMs}ms</strong>
                    </span>
                    <span>
                      Loss: <strong className={wl.lossPercent > 1 ? 'text-rose-400' : 'text-slate-200'}>{wl.lossPercent}%</strong>
                    </span>
                  </div>

                  <div className="mt-1.5 w-full bg-slate-800 h-1 rounded overflow-hidden">
                    <div
                      className={`h-full ${
                        wl.utilizationPercent > 80
                          ? 'bg-rose-500'
                          : wl.utilizationPercent > 50
                          ? 'bg-amber-400'
                          : 'bg-emerald-400'
                      }`}
                      style={{ width: `${Math.min(wl.utilizationPercent, 100)}%` }}
                    />
                  </div>
                  <div className="mt-1 flex justify-between text-[10px] text-slate-500">
                    <span>{wl.currentTrafficMbps}M / {wl.bandwidthMbps}M</span>
                    <span>{wl.utilizationPercent.toFixed(0)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 4 Partition Regions */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
          {/* Region 1: BẢO LỘC (Flat) */}
          <div className="p-3 bg-slate-900/40 border border-slate-800 rounded-lg flex flex-col">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
              <div>
                <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">
                  1. Chi Nhánh Bảo Lộc
                </h3>
                <span className="text-[11px] text-slate-400">Flat Network (1 Switch L2, 17 Hosts)</span>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                10.10.0.0/16
              </span>
            </div>

            <div className="space-y-2.5 flex-1">
              {baolocNodes.map((node) => renderNodeCard(node))}
            </div>
          </div>

          {/* Region 2: NHA TRANG (3-Tier) */}
          <div className="p-3 bg-slate-900/40 border border-slate-800 rounded-lg flex flex-col">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
              <div>
                <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">
                  2. Chi Nhánh Nha Trang
                </h3>
                <span className="text-[11px] text-slate-400">3-Tier (Core - 2 Dist VRRP - 6 Access)</span>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                10.20.0.0/16
              </span>
            </div>

            <div className="space-y-2.5 flex-1">
              {nhatrangNodes.map((node) => renderNodeCard(node))}
            </div>
          </div>

          {/* Region 3: TP. HỒ CHÍ MINH (3-Tier & SD-WAN) */}
          <div className="p-3 bg-slate-900/40 border border-slate-800 rounded-lg flex flex-col">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
              <div>
                <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">
                  3. Chi Nhánh TP.HCM
                </h3>
                <span className="text-[11px] text-slate-400">3-Tier + SD-WAN Main Edge Router (35 Hosts)</span>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                10.30.0.0/16
              </span>
            </div>

            <div className="space-y-2.5 flex-1">
              {hcmNodes.map((node) => renderNodeCard(node))}
            </div>
          </div>

          {/* Region 4: DATA CENTER (Spine-Leaf Fabric) */}
          <div className="p-3 bg-slate-900/40 border border-slate-800 rounded-lg flex flex-col">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
              <div>
                <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">
                  4. Data Center Fabric
                </h3>
                <span className="text-[11px] text-slate-400">Spine-Leaf (2 Spine, 4 Leaf, 10 Servers)</span>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                10.100.0.0/16
              </span>
            </div>

            <div className="space-y-2.5 flex-1">
              {dcNodes.map((node) => renderNodeCard(node))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  function renderNodeCard(node: NetworkNode) {
    const isSelected = selectedNodeId === node.id;
    const style = getStatusColor(node.status);

    return (
      <div
        key={node.id}
        onClick={() => onSelectNode(node)}
        className={`p-2.5 rounded-lg border transition-all cursor-pointer ${style.bg} ${
          style.border
        } ${isSelected ? 'ring-2 ring-cyan-400 shadow-lg' : ''} ${style.glow}`}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded bg-slate-900/90 border border-slate-700">
              {getNodeIcon(node.role)}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-white font-mono">{node.name}</span>
                <span className={`w-2 h-2 rounded-full ${style.dot}`} />
              </div>
              <span className="text-[11px] text-slate-400 font-mono block">
                {node.ip}
              </span>
            </div>
          </div>

          <div className="flex flex-col items-end gap-1">
            <span
              className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                node.status === 'ONLINE'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/60'
                  : node.status === 'OFFLINE'
                  ? 'bg-rose-900 text-rose-100 border border-rose-600 animate-pulse'
                  : node.status === 'DEGRADED'
                  ? 'bg-amber-950 text-amber-200 border border-amber-700'
                  : 'bg-cyan-950 text-cyan-200 border border-cyan-700'
              }`}
            >
              {node.status}
            </span>

            {node.vrrpRole && (
              <span
                className={`text-[9px] font-mono px-1 py-0.2 rounded font-bold ${
                  node.vrrpRole === 'MASTER'
                    ? 'bg-indigo-950 text-indigo-300 border border-indigo-700'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                VRRP {node.vrrpRole}
              </span>
            )}
          </div>
        </div>

        {/* Telemetry row */}
        <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <span>CPU: <strong className={node.cpuPercent > 80 ? 'text-rose-400' : 'text-slate-300'}>{node.cpuPercent}%</strong></span>
            <span>·</span>
            <span>RAM: <strong className="text-slate-300">{node.memoryPercent}%</strong></span>
          </div>
          {node.flowCount !== undefined && (
            <span className="text-[10px] text-cyan-400">
              {node.flowCount} flows
            </span>
          )}
        </div>
      </div>
    );
  }
};
