import React from 'react';
import { WANPathMetric } from '../types/network';
import { 
  Radio, 
  Activity, 
  ShieldCheck, 
  AlertTriangle, 
  ArrowUpRight, 
  Zap, 
  PhoneCall, 
  Database, 
  Globe, 
  HardDriveDownload,
  Lock
} from 'lucide-react';

interface WanMonitorPanelProps {
  wanMetrics: WANPathMetric[];
  onSteerTrafficManual?: (transport: string, newPath: string) => void;
}

export const WanMonitorPanel: React.FC<WanMonitorPanelProps> = ({ wanMetrics }) => {
  const getTransportIcon = (transport: string) => {
    switch (transport) {
      case 'MPLS':
        return <PhoneCall className="w-4 h-4 text-emerald-400" />;
      case '5G':
        return <Zap className="w-4 h-4 text-cyan-400" />;
      case 'Internet':
        return <Globe className="w-4 h-4 text-amber-400" />;
      case 'LTE':
        return <Radio className="w-4 h-4 text-indigo-400" />;
      case 'VPN':
      default:
        return <Lock className="w-4 h-4 text-purple-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPTIMAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-700">OPTIMAL</span>;
      case 'DEGRADED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 text-amber-300 border border-amber-700 animate-pulse">DEGRADED</span>;
      case 'CONGESTED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950 text-rose-300 border border-rose-700 animate-pulse">CONGESTED (&gt;85%)</span>;
      case 'DOWN':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-900 text-rose-100 border border-rose-500 animate-ping">LINK DOWN</span>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Banner: SD-WAN Dynamic Path Selection Overview */}
      <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              BẢNG ĐIỀU KHIỂN & ĐO LƯỜNG 5 KÊNH WAN (3 CHI NHÁNH ➔ DATA CENTER)
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Hạ tầng 5 kênh WAN kết nối hội tụ từ 3 Chi Nhánh (Bảo Lộc, Nha Trang, TP.HCM) đồng loạt đổ về Data Center · Thu thập chu kỳ 5 giây bằng ICMP Probe, OVS port stats, iperf3 và E-Model ITU-T G.107
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Tổng Dung Lượng: </span>
            <strong className="text-cyan-300">480 Mbps</strong>
          </div>
          <div className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Lưu Lượng Thực: </span>
            <strong className="text-emerald-300">
              {wanMetrics.reduce((acc, curr) => acc + curr.throughputMbps, 0)} Mbps
            </strong>
          </div>
        </div>
      </div>

      {/* 5 WAN Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3.5">
        {wanMetrics.map((wan) => {
          const isDown = wan.status === 'DOWN';
          const isDegraded = wan.status === 'DEGRADED' || wan.status === 'CONGESTED';

          return (
            <div
              key={wan.transport}
              className={`p-3.5 rounded-lg border transition-all flex flex-col justify-between ${
                isDown
                  ? 'bg-rose-950/40 border-rose-600 shadow-[0_0_15px_rgba(225,29,72,0.3)]'
                  : isDegraded
                  ? 'bg-amber-950/30 border-amber-600 shadow-[0_0_12px_rgba(245,158,11,0.2)]'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <div className="p-1 rounded bg-slate-950 border border-slate-800">
                      {getTransportIcon(wan.transport)}
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-white font-mono">{wan.transport}</h3>
                      <span className="text-[10px] text-slate-400 font-mono">{wan.capacityMbps} Mbps Cap</span>
                    </div>
                  </div>
                  {getStatusBadge(wan.status)}
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 gap-2 mt-3 text-xs font-mono">
                  <div className="p-1.5 rounded bg-slate-950/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Độ Trễ (RTT)</span>
                    <span className="font-bold text-slate-200 tabular-nums">
                      {isDown ? 'TIMEOUT' : `${wan.latencyMs} ms`}
                    </span>
                    <span className="text-[9px] text-slate-500 block">Base: {wan.baseLatencyMs}ms</span>
                  </div>

                  <div className="p-1.5 rounded bg-slate-950/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Mất Gói (Loss)</span>
                    <span className={`font-bold tabular-nums ${wan.lossPercent > 1 ? 'text-rose-400' : 'text-slate-200'}`}>
                      {wan.lossPercent}%
                    </span>
                    <span className="text-[9px] text-slate-500 block">Jitter: {wan.jitterMs}ms</span>
                  </div>
                </div>

                {/* QoE MOS Score Display */}
                <div className="mt-2.5 p-2 rounded bg-slate-950/80 border border-slate-800">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[11px] text-slate-400">VoIP QoE MOS:</span>
                    <span
                      className={`font-bold text-xs tabular-nums ${
                        wan.mosVoip >= 4.0
                          ? 'text-emerald-400'
                          : wan.mosVoip >= 3.5
                          ? 'text-amber-300'
                          : 'text-rose-400'
                      }`}
                    >
                      {wan.mosVoip.toFixed(2)} / 5.0
                    </span>
                  </div>
                  <div className="mt-1 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        wan.mosVoip >= 4.0
                          ? 'bg-emerald-400'
                          : wan.mosVoip >= 3.5
                          ? 'bg-amber-400'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${(wan.mosVoip / 5.0) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[9px] text-slate-500 mt-0.5">
                    <span>1.0 (Drop)</span>
                    <span className="text-amber-500">SLA 3.5</span>
                    <span>5.0 (HD)</span>
                  </div>
                </div>

                {/* Bandwidth Utilization Bar */}
                <div className="mt-2.5 text-xs font-mono">
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Tải: {wan.throughputMbps}M / {wan.capacityMbps}M</span>
                    <span className={wan.utilizationPercent > 80 ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                      {wan.utilizationPercent.toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        wan.utilizationPercent > 85
                          ? 'bg-rose-500'
                          : wan.utilizationPercent > 60
                          ? 'bg-amber-400'
                          : 'bg-cyan-400'
                      }`}
                      style={{ width: `${Math.min(wan.utilizationPercent, 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Routed Applications list */}
              <div className="mt-3 pt-2.5 border-t border-slate-800/80">
                <span className="text-[10px] font-mono text-slate-400 block mb-1">
                  Luồng dịch vụ đang định tuyến:
                </span>
                <div className="space-y-1">
                  {wan.routedServices.map((srv, idx) => (
                    <div
                      key={idx}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800/80 truncate"
                    >
                      {srv}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* SD-WAN Dynamic Traffic Steering Policy Matrix */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg">
        <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              BẢNG CHÍNH SÁCH ĐỊNH TUYẾN THÔNG MINH SD-WAN (SLA-AWARE TRAFFIC STEERING)
            </h3>
            <span className="text-[11px] text-slate-400">
              Quy tắc tự động điều hướng luồng khi phát hiện suy giảm chất lượng hoặc tắc nghẽn
            </span>
          </div>
          <span className="text-xs font-mono text-cyan-400">
            Phase 10: Custom Python SD-WAN Controller
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono text-left">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800 bg-slate-950/60">
                <th className="p-2.5">Loại Lưu Lượng (Application Class)</th>
                <th className="p-2.5">QoS DSCP</th>
                <th className="p-2.5">Yêu Cầu SLA (Max RTT / Loss / Jitter)</th>
                <th className="p-2.5">Kênh Ưu Tiên 1</th>
                <th className="p-2.5">Kênh Dự Phòng 2</th>
                <th className="p-2.5">Kênh Dự Phòng 3</th>
                <th className="p-2.5">Hành Động Khi Vi Phạm SLA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              <tr className="hover:bg-slate-900/40">
                <td className="p-2.5 font-bold text-emerald-400 flex items-center gap-1.5">
                  <PhoneCall className="w-3.5 h-3.5" /> VoIP SIP / RTP Audio
                </td>
                <td className="p-2.5 font-bold text-cyan-300">EF (46)</td>
                <td className="p-2.5 text-slate-300">&le; 50ms / &le; 1% / &le; 10ms (MOS &ge; 3.5)</td>
                <td className="p-2.5 font-bold text-emerald-300">MPLS (20ms)</td>
                <td className="p-2.5 text-cyan-300">5G (15ms)</td>
                <td className="p-2.5 text-slate-400">Internet</td>
                <td className="p-2.5 text-amber-300">Mid-session Flow Steering sang 5G (&lt; 3s)</td>
              </tr>

              <tr className="hover:bg-slate-900/40">
                <td className="p-2.5 font-bold text-cyan-400 flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5" /> Database ERP / SAP
                </td>
                <td className="p-2.5 font-bold text-cyan-300">AF31 (26)</td>
                <td className="p-2.5 text-slate-300">&le; 80ms / &le; 0.5% / -</td>
                <td className="p-2.5 font-bold text-emerald-300">MPLS</td>
                <td className="p-2.5 text-cyan-300">5G</td>
                <td className="p-2.5 text-slate-400">Internet</td>
                <td className="p-2.5 text-amber-300">Failover sang 5G hoặc Internet</td>
              </tr>

              <tr className="hover:bg-slate-900/40">
                <td className="p-2.5 font-bold text-indigo-400 flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5" /> High-Speed Cloud SaaS & Video
                </td>
                <td className="p-2.5 font-bold text-cyan-300">AF21 (18)</td>
                <td className="p-2.5 text-slate-300">&le; 100ms / &le; 2% / -</td>
                <td className="p-2.5 font-bold text-cyan-300">5G (200M)</td>
                <td className="p-2.5 text-slate-300">Internet</td>
                <td className="p-2.5 text-slate-400">LTE</td>
                <td className="p-2.5 text-amber-300">Phân tải sang Internet / LTE</td>
              </tr>

              <tr className="hover:bg-slate-900/40">
                <td className="p-2.5 font-bold text-slate-300 flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5" /> Web Browsing & Cloud
                </td>
                <td className="p-2.5 font-bold text-cyan-300">AF11 (10)</td>
                <td className="p-2.5 text-slate-300">&le; 150ms / &le; 3% / -</td>
                <td className="p-2.5 font-bold text-slate-300">Internet</td>
                <td className="p-2.5 text-cyan-300">5G</td>
                <td className="p-2.5 text-slate-400">LTE</td>
                <td className="p-2.5 text-slate-400">Best-effort fallback</td>
              </tr>

              <tr className="hover:bg-slate-900/40">
                <td className="p-2.5 font-bold text-purple-400 flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5" /> Nightly Backup & Archive
                </td>
                <td className="p-2.5 font-bold text-slate-400">BE (0)</td>
                <td className="p-2.5 text-slate-400">Throughput tối đa, không trễ gấp</td>
                <td className="p-2.5 font-bold text-purple-300">VPN</td>
                <td className="p-2.5 text-slate-300">Internet</td>
                <td className="p-2.5 text-slate-400">LTE</td>
                <td className="p-2.5 text-cyan-300">Dự báo Holt-Winters dời tải trước khi nghẽn</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
