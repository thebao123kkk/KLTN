import React from 'react';
import { PPOStateVector, PPOActionOutput, SafetyLayerAudit } from '../types/network';
import { 
  BrainCircuit, 
  ShieldCheck, 
  ShieldAlert, 
  Layers, 
  Cpu, 
  Activity, 
  Zap, 
  TrendingUp, 
  CheckCircle,
  HelpCircle
} from 'lucide-react';

interface AiClosedLoopPanelProps {
  stateVector: PPOStateVector;
  actionOutput: PPOActionOutput;
  safetyAudit: SafetyLayerAudit;
}

export const AiClosedLoopPanel: React.FC<AiClosedLoopPanelProps> = ({
  stateVector,
  actionOutput,
  safetyAudit,
}) => {
  const actionsList = [
    {
      id: 0,
      name: 'a_t = 0: No-op (Duy trì ổn định)',
      desc: 'Giữ nguyên cấu hình khi mạng bình thường; tránh can thiệp thừa bị phạt -1 điểm.',
      prob: actionOutput.probabilities[0],
      reward: '+1 / step',
    },
    {
      id: 1,
      name: 'a_t = 1: Reset Port (OpenFlow Port Mod)',
      desc: 'Kích hoạt khi P_down > 0; gửi lệnh OFPPC_PORT_UP tới switch và port đích cụ thể.',
      prob: actionOutput.probabilities[1],
      reward: '+10 (Port restore)',
    },
    {
      id: 2,
      name: 'a_t = 2: Restart Switch / Controller Handshake',
      desc: 'Kích hoạt khi f_disc > 0 hoặc C_cpu > 90%; khởi động lại socket kết nối switch.',
      prob: actionOutput.probabilities[2],
      reward: '+20 (Datapath restore)',
    },
    {
      id: 3,
      name: 'a_t = 3: Bespoke Flow Table Flush & Re-inject',
      desc: 'Kích hoạt khi f_err > 0; xóa bỏ luật xung đột cookie cũ và cài đặt luồng sạch.',
      prob: actionOutput.probabilities[3],
      reward: '+15 (Flow restore)',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Top Banner: AI Self-Healing Architecture */}
      <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-purple-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              BỘ NÃO RA QUYẾT ĐỊNH AI: PPO REINFORCEMENT LEARNING & CLOSED-LOOP MAPE-K
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Mạng nơ-ron PPO Policy nhận Vector trạng thái 8 chiều s_t, chọn hành động tối ưu a_t kết hợp Safety Layer thẩm định
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Confidence Score: </span>
            <strong className="text-cyan-300">{(safetyAudit.confidenceScore * 100).toFixed(0)}%</strong>
          </div>
          <div className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Reward Hiện Tại: </span>
            <strong className="text-emerald-400">+{actionOutput.reward} pts</strong>
          </div>
        </div>
      </div>

      {/* Main 3 Columns: State Vector, PPO Policy Network, Safety Layer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Col 1: 8D State Vector s_t (4 cols) */}
        <div className="lg:col-span-4 p-4 bg-slate-900/70 border border-slate-800 rounded-lg space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">
              1. Vector Trạng Thái 8 Chiều (s_t)
            </h3>
            <span className="text-[10px] font-mono text-slate-500">Chu kỳ 10s</span>
          </div>

          <p className="text-[11px] text-slate-400 font-mono">
            s_t = [C_cpu, C_res, C_virt, f_sent, f_err, f_conn, f_disc, P_down]
          </p>

          <div className="space-y-2.5 text-xs font-mono">
            {/* C_cpu */}
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <div className="flex justify-between text-slate-300 mb-1">
                <span>C_cpu (Controller CPU):</span>
                <strong className={stateVector.cpu > 80 ? 'text-rose-400' : 'text-cyan-300'}>
                  {stateVector.cpu}%
                </strong>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded overflow-hidden">
                <div
                  className={`h-full ${stateVector.cpu > 80 ? 'bg-rose-500' : 'bg-cyan-400'}`}
                  style={{ width: `${Math.min(stateVector.cpu, 100)}%` }}
                />
              </div>
            </div>

            {/* C_res_mem */}
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <div className="flex justify-between text-slate-300 mb-1">
                <span>C_res_mem (Resident RAM):</span>
                <strong className="text-slate-200">{stateVector.resMem}%</strong>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded overflow-hidden">
                <div className="h-full bg-indigo-400" style={{ width: `${stateVector.resMem}%` }} />
              </div>
            </div>

            {/* f_sent */}
            <div className="p-2 rounded bg-slate-950 border border-slate-800 flex justify-between">
              <span className="text-slate-400">f_sent (OpenFlow Flow Count):</span>
              <strong className="text-slate-200">{stateVector.flowsSent} rules</strong>
            </div>

            {/* f_err */}
            <div className={`p-2 rounded border flex justify-between ${
              stateVector.flowErrors > 0 ? 'bg-rose-950/40 border-rose-600 text-rose-300' : 'bg-slate-950 border-slate-800 text-slate-300'
            }`}>
              <span>f_err (Flow Errors):</span>
              <strong className={stateVector.flowErrors > 0 ? 'text-rose-400 animate-pulse' : 'text-emerald-400'}>
                {stateVector.flowErrors}
              </strong>
            </div>

            {/* f_conn & f_disc */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">f_conn (Active DP):</span>
                <strong className="text-emerald-400">{stateVector.connections} switches</strong>
              </div>
              <div className={`p-2 rounded border ${
                stateVector.disconnections > 0 ? 'bg-rose-950/40 border-rose-600 text-rose-300' : 'bg-slate-950 border-slate-800'
              }`}>
                <span className="text-[10px] text-slate-400 block">f_disc (Dropped DP):</span>
                <strong className={stateVector.disconnections > 0 ? 'text-rose-400' : 'text-slate-400'}>
                  {stateVector.disconnections}
                </strong>
              </div>
            </div>

            {/* P_down */}
            <div className={`p-2 rounded border flex justify-between ${
              stateVector.portsDown > 0 ? 'bg-rose-950/50 border-rose-600 shadow-[0_0_8px_rgba(244,63,94,0.3)]' : 'bg-slate-950 border-slate-800'
            }`}>
              <span className="text-slate-300">P_down (Ports Down):</span>
              <strong className={stateVector.portsDown > 0 ? 'text-rose-400 text-sm animate-pulse' : 'text-emerald-400'}>
                {stateVector.portsDown} port(s)
              </strong>
            </div>
          </div>
        </div>

        {/* Col 2: PPO Policy Output & Decision Engine (5 cols) */}
        <div className="lg:col-span-5 p-4 bg-slate-900/70 border border-slate-800 rounded-lg space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider font-mono">
              2. PPO Policy Network (Hành Động a_t)
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
              Quyết định: a_{actionOutput.actionId}
            </span>
          </div>

          <div className="space-y-2.5">
            {actionsList.map((act) => {
              const isChosen = actionOutput.actionId === act.id;
              const probPercent = (act.prob * 100).toFixed(1);

              return (
                <div
                  key={act.id}
                  className={`p-2.5 rounded-lg border text-xs font-mono transition-all ${
                    isChosen
                      ? 'bg-purple-950/50 border-purple-500 shadow-[0_0_12px_rgba(168,85,247,0.3)]'
                      : 'bg-slate-950 border-slate-800 opacity-75'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-bold ${isChosen ? 'text-purple-300' : 'text-slate-300'}`}>
                      {act.name}
                    </span>
                    <span className="text-[11px] font-bold text-cyan-400 tabular-nums">
                      {probPercent}%
                    </span>
                  </div>

                  <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">
                    {act.desc}
                  </p>

                  <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                    <div className="w-2/3 bg-slate-800 h-1.5 rounded overflow-hidden">
                      <div
                        className={`h-full ${isChosen ? 'bg-purple-400' : 'bg-slate-600'}`}
                        style={{ width: `${probPercent}%` }}
                      />
                    </div>
                    <span className="text-emerald-400">{act.reward}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action to Micro-Binding indicator */}
          <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-xs font-mono">
            <span className="text-[10px] text-slate-400 block mb-1">
              Ghép nối Hành động Tầng Macro &rarr; Thiết bị Tầng Micro:
            </span>
            <div className="text-slate-300 text-[11px]">
              Target DPID: <strong className="text-cyan-300">{actionOutput.targetDpid || 'All Datapaths'}</strong> · Target Port: <strong className="text-cyan-300">{actionOutput.targetPort || 'None'}</strong>
            </div>
          </div>
        </div>

        {/* Col 3: Safety Layer & Auxiliary Models (3 cols) */}
        <div className="lg:col-span-3 p-4 bg-slate-900/70 border border-slate-800 rounded-lg space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">
              3. Lớp Kiểm Soát An Toàn (Safety Layer)
            </h3>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Thẩm Định Policy:</span>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> PASS
              </span>
            </div>

            <div className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Đánh Giá Rủi Ro:</span>
              <span className="text-emerald-300 font-bold px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-800">
                {safetyAudit.riskLevel} RISK
              </span>
            </div>

            <div className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Bán Kính Tác Động (Blast Radius):</span>
              <span className="text-cyan-300 font-bold">
                {safetyAudit.blastRadiusPercent}% (&le; 30%)
              </span>
            </div>

            <div className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Kế Hoạch Rollback:</span>
              <span className="text-emerald-400 font-bold">SẴN SÀNG</span>
            </div>
          </div>

          {/* Auxiliary Models: Holt-Winters & QoE Regression */}
          <div className="mt-4 pt-3 border-t border-slate-800 space-y-2 text-xs font-mono">
            <span className="text-[10px] text-slate-400 font-bold uppercase block">
              Mô Hình Dự Báo Bổ Trợ (Proactive)
            </span>

            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-amber-400 font-bold block text-[11px]">
                Holt-Winters / LSTM Predictor:
              </span>
              <span className="text-slate-400 text-[10px] block mt-0.5">
                Dự báo bùng nổ lưu lượng trước 15-30s với ngưỡng động d(Traffic)/dt
              </span>
            </div>

            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-cyan-400 font-bold block text-[11px]">
                QoE Regression (E-Model G.107):
              </span>
              <span className="text-slate-400 text-[10px] block mt-0.5">
                Đánh giá MOS điểm thoại trực tiếp từ Latency, Loss, Jitter thời gian thực
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
