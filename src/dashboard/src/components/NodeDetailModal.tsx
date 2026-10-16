import React from 'react';
import { NetworkNode } from '../types/network';
import { 
  X, 
  Server, 
  Router, 
  Layers, 
  Cpu, 
  Laptop, 
  Activity, 
  ShieldCheck, 
  Radio, 
  Terminal, 
  AlertOctagon,
  RefreshCw
} from 'lucide-react';

interface NodeDetailModalProps {
  node: NetworkNode | null;
  onClose: () => void;
  onToggleNodeStatus?: (nodeId: string) => void;
}

export const NodeDetailModal: React.FC<NodeDetailModalProps> = ({
  node,
  onClose,
  onToggleNodeStatus,
}) => {
  if (!node) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-slate-950 border border-slate-800 text-cyan-400">
              {node.role === 'core' || node.role === 'spine' ? (
                <Layers className="w-5 h-5" />
              ) : node.role === 'dist' || node.role === 'gateway' ? (
                <Router className="w-5 h-5" />
              ) : node.role === 'server' ? (
                <Server className="w-5 h-5" />
              ) : (
                <Cpu className="w-5 h-5" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white font-mono">{node.name}</h3>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    node.status === 'ONLINE'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                      : node.status === 'OFFLINE'
                      ? 'bg-rose-950 text-rose-300 border border-rose-700 animate-pulse'
                      : 'bg-amber-950 text-amber-300 border border-amber-700'
                  }`}
                >
                  {node.status}
                </span>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                ID: {node.id} · Phân vùng: {node.site.toUpperCase()}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-4 space-y-4 text-xs font-mono">
          {/* Node Summary Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Địa Chỉ IP</span>
              <strong className="text-slate-200">{node.ip}</strong>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">VLAN ID</span>
              <strong className="text-slate-200">{node.vlan || 'Trunk / L3'}</strong>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">CPU Sử Dụng</span>
              <strong className={node.cpuPercent > 80 ? 'text-rose-400' : 'text-cyan-300'}>
                {node.cpuPercent}%
              </strong>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Bộ Nhớ RAM</span>
              <strong className="text-slate-200">{node.memoryPercent}%</strong>
            </div>
          </div>

          {/* Description */}
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
              Mô Tả Chức Năng Trong Đồ Án
            </span>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              {node.description}
            </p>
          </div>

          {/* Protocol Roles: VRRP / OSPF */}
          {(node.vrrpRole || node.ospfNeighbors) && (
            <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-[10px] text-indigo-400 uppercase font-bold block">
                Trạng Thái Giao Thức L3 / L2 HA
              </span>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                {node.vrrpRole && (
                  <div>
                    <span className="text-slate-400 block">Keepalived VRRP:</span>
                    <strong className="text-indigo-300">
                      Vai trò: {node.vrrpRole} (Độ ưu tiên: {node.vrrpPriority || 100})
                    </strong>
                  </div>
                )}
                {node.ospfNeighbors && (
                  <div>
                    <span className="text-slate-400 block">FRR OSPF Neighbors:</span>
                    <strong className="text-emerald-300">
                      {node.ospfNeighbors.join(', ')} (Full State)
                    </strong>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Interfaces Table */}
          <div className="space-y-1.5">
            <span className="text-[10px] text-slate-400 uppercase font-bold block">
              Danh Sách Giao Diện Mạng (Interfaces & OpenFlow Ports)
            </span>
            <div className="overflow-x-auto rounded border border-slate-800">
              <table className="w-full text-left text-[11px]">
                <thead>
                  <tr className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <th className="p-2">Cổng</th>
                    <th className="p-2">IP Subnet</th>
                    <th className="p-2">Trạng Thái</th>
                    <th className="p-2">Tốc Độ</th>
                    <th className="p-2 text-right">Lưu Lượng (Bytes)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                  {node.interfaces.map((iface, idx) => (
                    <tr key={idx}>
                      <td className="p-2 font-bold text-slate-200">{iface.name}</td>
                      <td className="p-2 text-slate-400">{iface.ip || 'Tagged VLAN'}</td>
                      <td className="p-2">
                        <span
                          className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                            iface.status === 'UP'
                              ? 'bg-emerald-950 text-emerald-300'
                              : 'bg-rose-950 text-rose-300'
                          }`}
                        >
                          {iface.status}
                        </span>
                      </td>
                      <td className="p-2 text-slate-300">{iface.speedMbps} Mbps</td>
                      <td className="p-2 text-right text-slate-400 tabular-nums">
                        RX: {(iface.rxBytes / 1024 / 1024).toFixed(1)}MB · TX: {(iface.txBytes / 1024 / 1024).toFixed(1)}MB
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Simulation Buttons */}
          <div className="pt-2 flex items-center justify-between border-t border-slate-800">
            <span className="text-[11px] text-slate-500">
              Mininet Node Control
            </span>
            <div className="flex items-center gap-2">
              {onToggleNodeStatus && (
                <button
                  onClick={() => onToggleNodeStatus(node.id)}
                  className={`px-3 py-1.5 rounded font-mono font-bold text-xs transition-colors ${
                    node.status === 'ONLINE'
                      ? 'bg-rose-950 text-rose-300 border border-rose-800 hover:bg-rose-900'
                      : 'bg-emerald-950 text-emerald-300 border border-emerald-800 hover:bg-emerald-900'
                  }`}
                >
                  {node.status === 'ONLINE' ? 'Giả Lập Sập Thiết Bị (Down)' : 'Bật Lại Thiết Bị (Up)'}
                </button>
              )}
              <button
                onClick={onClose}
                className="px-3 py-1.5 rounded bg-slate-800 text-slate-300 hover:text-white transition-colors"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
