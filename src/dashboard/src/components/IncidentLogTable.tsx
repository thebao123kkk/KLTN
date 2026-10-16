import React from 'react';
import { IncidentLog } from '../types/network';
import { 
  History, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  Clock, 
  Search,
  Filter
} from 'lucide-react';

interface IncidentLogTableProps {
  logs: IncidentLog[];
  onClearLogs: () => void;
}

export const IncidentLogTable: React.FC<IncidentLogTableProps> = ({ logs, onClearLogs }) => {
  const [searchTerm, setSearchTerm] = React.useState<string>('');
  const [stageFilter, setStageFilter] = React.useState<string>('all');

  const filteredLogs = logs.filter((log) => {
    if (stageFilter !== 'all' && log.stage !== stageFilter) return false;
    if (
      searchTerm &&
      !log.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !log.message.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-950/60 border-rose-800';
      case 'WARNING':
        return 'text-amber-300 bg-amber-950/60 border-amber-800';
      case 'SUCCESS':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800';
      case 'INFO':
      default:
        return 'text-cyan-300 bg-cyan-950/60 border-cyan-800';
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Bar: Search & Stage Filter */}
      <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              NHẬT KÝ SỰ CỐ & VÒNG LẶP TỰ PHỤC HỒI THỜI GIAN THỰC (AUDIT TRAIL)
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Ghi nhận toàn bộ chuỗi sự kiện từ lúc phát hiện, phân tích nguyên nhân gốc, phê duyệt an toàn đến khôi phục
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Search box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Tìm kiếm sự kiện..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 rounded bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-48"
            />
          </div>

          {/* Stage filter */}
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 focus:outline-none"
          >
            <option value="all">Tất cả giai đoạn</option>
            <option value="DETECT">1. Detect</option>
            <option value="RCA">2. RCA</option>
            <option value="SAFETY">3. Safety</option>
            <option value="EXECUTE">4. Execute</option>
            <option value="RESOLVED">5. Resolved</option>
          </select>

          <button
            onClick={onClearLogs}
            className="px-3 py-1.5 text-xs font-mono rounded bg-slate-800 text-slate-300 hover:text-white transition-colors border border-slate-700 whitespace-nowrap"
          >
            Xóa Nhật Ký
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg overflow-x-auto">
        <table className="w-full text-xs font-mono text-left">
          <thead>
            <tr className="text-slate-400 border-b border-slate-800 bg-slate-950/60">
              <th className="p-2.5">Thời Gian</th>
              <th className="p-2.5">Giai Đoạn</th>
              <th className="p-2.5">Mức Độ</th>
              <th className="p-2.5">Sự Cố</th>
              <th className="p-2.5">Vị Trí / Thiết Bị</th>
              <th className="p-2.5">Nội Dung Chi Tiết Hành Động</th>
              <th className="p-2.5 text-right">MTTR</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-8 text-center text-slate-500">
                  Chưa có sự kiện nào được ghi nhận. Hãy kích hoạt một sự cố để quan sát vòng lặp!
                </td>
              </tr>
            ) : (
              filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-900/50">
                  <td className="p-2.5 text-slate-400 whitespace-nowrap">{log.timestamp}</td>
                  <td className="p-2.5 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-cyan-300 border border-slate-700">
                      {log.stage}
                    </span>
                  </td>
                  <td className="p-2.5 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityStyle(log.severity)}`}>
                      {log.severity}
                    </span>
                  </td>
                  <td className="p-2.5 font-bold text-slate-200 whitespace-nowrap">
                    {log.faultId ? `[${log.faultId}] ` : ''}
                    {log.title}
                  </td>
                  <td className="p-2.5 text-slate-400 whitespace-nowrap">
                    {log.targetSite || 'Global'} / {log.targetDevice || 'N/A'}
                  </td>
                  <td className="p-2.5 text-slate-300 max-w-md">{log.message}</td>
                  <td className="p-2.5 text-right font-bold text-emerald-400 tabular-nums whitespace-nowrap">
                    {log.mttrSec ? `${log.mttrSec.toFixed(1)}s` : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
