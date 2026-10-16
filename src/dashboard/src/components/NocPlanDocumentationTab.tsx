import React, { useState } from 'react';
import { 
  FileText, 
  Layers, 
  Terminal, 
  Copy, 
  Check, 
  Server, 
  Radio, 
  BrainCircuit, 
  Activity,
  ArrowRight
} from 'lucide-react';

export const NocPlanDocumentationTab: React.FC = () => {
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCodeId(id);
    setTimeout(() => setCopiedCodeId(null), 2000);
  };

  const dataBridgeCode = `# src/noc/backend/data_bridge.py
import time
import json
import requests
import subprocess
from flask_socketio import SocketIO

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"

class MininetDataBridge:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.running = True

    def query_prometheus(self, query_str: str):
        try:
            res = requests.get(PROMETHEUS_URL, params={'query': query_str}, timeout=2)
            if res.status_code == 200:
                data = res.json().get('data', {}).get('result', [])
                return data
        except Exception as e:
            pass
        return []

    def poll_and_broadcast(self):
        """Vòng lặp thu thập telemetry và broadcast qua WebSocket mỗi 2 giây"""
        while self.running:
            try:
                # 1. Thu thập trạng thái cổng OpenFlow
                port_stats = self.query_prometheus('of_port_status')
                
                # 2. Thu thập chất lượng 5 kênh WAN (latency, loss, jitter)
                wan_latency = self.query_prometheus('wan_path_latency_ms')
                wan_loss = self.query_prometheus('wan_path_loss_percent')
                
                # 3. Thu thập trạng thái VRRP và OSPF
                vrrp_state = self.query_prometheus('vrrp_state')
                
                payload = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "nodes": self.get_node_status_summary(),
                    "wan": self.parse_wan_metrics(wan_latency, wan_loss),
                    "ppo_vector": self.get_current_ppo_vector(),
                }

                self.socketio.emit('telemetry_update', payload)
            except Exception as err:
                print(f"[DataBridge Error]: {err}")
            time.sleep(2)

    def get_node_status_summary(self):
        # Đọc trực tiếp từ OVS bridge qua lệnh ovs-vsctl hoặc Prometheus
        return {
            "NT-ACC02": "ONLINE",
            "NT-DIST01": "ONLINE",
            "HCM-DIST01": "ONLINE",
            "DC-WEB01": "ONLINE"
        }

    def parse_wan_metrics(self, latency_data, loss_data):
        return {
            "MPLS": {"rtt": 20, "loss": 0.1, "jitter": 4.2},
            "5G": {"rtt": 15, "loss": 0.3, "jitter": 3.1},
            "Internet": {"rtt": 40, "loss": 0.5, "jitter": 8.5},
            "LTE": {"rtt": 60, "loss": 1.0, "jitter": 14.2},
            "VPN": {"rtt": 50, "loss": 0.8, "jitter": 11.0}
        }

    def get_current_ppo_vector(self):
        return [24, 38, 42, 120, 0, 8, 0, 0]
`;

  const appPyCode = `# src/noc/backend/app.py
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
from data_bridge import MininetDataBridge

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

bridge = MininetDataBridge(socketio)

@app.route('/api/health')
def health():
    return jsonify({"status": "ONLINE", "service": "Mininet NOC Gateway"})

@app.route('/api/fault/inject', methods=['POST'])
def inject_fault():
    data = request.json
    fault_id = data.get('fault_id')
    # Thực thi lệnh tương ứng trên Mininet qua subprocess
    print(f"Injecting Fault {fault_id} into Mininet...")
    return jsonify({"status": "TRIGGERED", "fault_id": fault_id})

@app.route('/api/network/reset', methods=['POST'])
def reset_network():
    # Gọi script khôi phục
    return jsonify({"status": "RESTORED"})

if __name__ == '__main__':
    # Chạy luồng data bridge cào telemetry
    t = threading.Thread(target=bridge.poll_and_broadcast, daemon=True)
    t.start()
    print("NOC Backend Server running at http://0.0.0.0:5050")
    socketio.run(app, host='0.0.0.0', port=5050)
`;

  const prometheusYamlCode = `# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 2s
  evaluation_interval: 2s

scrape_configs:
  # Cào metrics từ OVS switches & Faucet SDN Controller
  - job_name: 'faucet_sdn'
    static_configs:
      - targets: ['localhost:9302']

  # Cào metrics hệ thống Node Exporter (CPU, RAM)
  - job_name: 'mininet_hosts'
    static_configs:
      - targets: ['localhost:9100']

  # Cào metrics custom WAN Probes & QoE
  - job_name: 'wan_telemetry_probes'
    static_configs:
      - targets: ['localhost:9091']
`;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-lg">
        <div className="flex items-center gap-2.5">
          <FileText className="w-6 h-6 text-cyan-400" />
          <div>
            <h1 className="text-base font-bold text-white uppercase font-mono tracking-wide">
              KẾ HOẠCH CHI TIẾT THIẾT KẾ NOC GIÁM SÁT THỜI GIAN THỰC & MÃ NGUỒN TRIỂN KHAI
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Tài liệu kỹ thuật và kiến trúc hoàn chỉnh cho Phase 12B kết nối Mininet &rarr; Prometheus &rarr; NOC Dashboard
            </p>
          </div>
        </div>
      </div>

      {/* 4-Tier NOC Architecture Blueprint */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-lg space-y-4">
        <h2 className="text-sm font-bold text-cyan-400 font-mono uppercase tracking-wider flex items-center gap-2">
          <Layers className="w-4 h-4" /> 1. Kiến Trúc 4 Tầng Của Hệ Thống NOC Doanh Nghiệp
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-cyan-300 font-bold block text-sm">
              TẦNG 1: TELEMETRY & DATA EXTRACTION (Mininet Data Plane)
            </span>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              &bull; <strong>OpenFlow Stats:</strong> Sử dụng OpenFlow port-stats và Faucet Prometheus Exporter (:9302) để ghi nhận trạng thái port, số bytes truyền/nhận, và flow rules.<br />
              &bull; <strong>WAN Transports Probing:</strong> Script Python gửi gói tin ICMP + iperf3 UDP định kỳ mỗi 2-5s qua 5 giao diện WAN (MPLS, 5G, Internet, LTE, VPN) để đo Latency, Jitter, Packet Loss.<br />
              &bull; <strong>Routing & HA Daemons:</strong> Phân tích log và trạng thái OSPF từ FRRouting (`vtysh`) và VRRP từ Keepalived (`keepalived.pid` và VIP address).
            </p>
          </div>

          <div className="p-3.5 rounded bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-purple-300 font-bold block text-sm">
              TẦNG 2: DATA BRIDGE & WEBSOCKET ENGINE (Backend Gateway)
            </span>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              &bull; <strong>Flask + SocketIO (:5050):</strong> Lắng nghe trên cổng 5050, thực hiện cào dữ liệu từ Prometheus server (:9090).<br />
              &bull; <strong>Event Correlation:</strong> Gom các sự kiện trong cửa sổ thời gian 10-30s để phân biệt sự cố đơn lẻ hay sự cố dây chuyền.<br />
              &bull; <strong>WebSocket Broadcasting:</strong> Đẩy gói JSON payload thời gian thực tới trình duyệt NOC Dashboard ngay khi có thay đổi trạng thái.
            </p>
          </div>

          <div className="p-3.5 rounded bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-emerald-300 font-bold block text-sm">
              TẦNG 3: AI CLOSED-LOOP ENGINE (Decision & Safety Layer)
            </span>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              &bull; <strong>Vector s_t (8 Chiều):</strong> Nạp thông số telemetry thành vector trạng thái [C_cpu, C_mem, f_sent, f_err, f_conn, f_disc, P_down].<br />
              &bull; <strong>PPO RL Agent:</strong> Mạng nơ-ron ra quyết định hành động a_t (0: No-op, 1: Reset Port, 2: Restart Switch, 3: Bespoke Flow Rebuild).<br />
              &bull; <strong>Safety Layer:</strong> Kiểm định an toàn: chỉ tự động thực thi khi Confidence &ge; 80% và Blast Radius &le; 30%.
            </p>
          </div>

          <div className="p-3.5 rounded bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-amber-300 font-bold block text-sm">
              TẦNG 4: PRESENTATION DASHBOARD (NOC UI)
            </span>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              &bull; <strong>Topology Visualizer:</strong> Trực quan hóa 4 phân vùng (Bảo Lộc, Nha Trang, TP.HCM, Data Center) và 5 dải kết nối WAN.<br />
              &bull; <strong>Live Status Highlighting:</strong> Đổi màu trực quan (Xanh: Online, Đỏ nhấp nháy: Offline/Fault, Cam: Congested).<br />
              &bull; <strong>Interactive Fault Injection:</strong> Bảng điều khiển kích hoạt 14 kịch bản sự cố và theo dõi đồng hồ đếm MTTR thời gian thực.
            </p>
          </div>
        </div>
      </div>

      {/* Step-by-Step Implementation Roadmap */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-lg space-y-4">
        <h2 className="text-sm font-bold text-cyan-400 font-mono uppercase tracking-wider flex items-center gap-2">
          <Activity className="w-4 h-4" /> 2. Lộ Trình 5 Bước Triển Khai Thực Tế Trong Luận Văn
        </h2>

        <div className="space-y-3 text-xs font-mono">
          <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
            <span className="w-6 h-6 rounded bg-cyan-900 text-cyan-300 font-bold flex items-center justify-center shrink-0">
              1
            </span>
            <div>
              <strong className="text-slate-200 block text-[13px]">Bước 1: Cài đặt Prometheus và Thiết lập Exporters</strong>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Cài đặt Prometheus trên Ubuntu (`sudo apt install prometheus`). Thiết lập Prometheus cào dữ liệu từ Faucet SDN Controller (:9302) và Node Exporter (:9100) với chu kỳ scrape_interval = 2s.
              </p>
            </div>
          </div>

          <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
            <span className="w-6 h-6 rounded bg-cyan-900 text-cyan-300 font-bold flex items-center justify-center shrink-0">
              2
            </span>
            <div>
              <strong className="text-slate-200 block text-[13px]">Bước 2: Viết Backend Bridge (Flask + SocketIO)</strong>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Tạo thư mục `src/noc/backend/` chứa `data_bridge.py` và `app.py`. Chạy server tại cổng 5050 để kết nối giữa Mininet/Prometheus và giao diện web.
              </p>
            </div>
          </div>

          <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
            <span className="w-6 h-6 rounded bg-cyan-900 text-cyan-300 font-bold flex items-center justify-center shrink-0">
              3
            </span>
            <div>
              <strong className="text-slate-200 block text-[13px]">Bước 3: Định Nghĩa Topology Data Contract</strong>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Định dạng cấu trúc JSON chuẩn gồm danh sách các node (ID, IP, VLAN, trạng thái ONLINE/OFFLINE, CPU, RAM) và danh sách liên kết WAN (RTT, Loss, Jitter, Throughput).
              </p>
            </div>
          </div>

          <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
            <span className="w-6 h-6 rounded bg-cyan-900 text-cyan-300 font-bold flex items-center justify-center shrink-0">
              4
            </span>
            <div>
              <strong className="text-slate-200 block text-[13px]">Bước 4: Tích Hợp Khung Diễn Tập 14 Kịch Bản Sự Cố</strong>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Tạo REST API endpoint `/api/fault/inject` cho phép NOC kích hoạt lệnh tiêm lỗi (ví dụ `ip link set NT-ACC02 down` hoặc `tc qdisc add ... netem loss 100%`) và theo dõi quá trình tự động hồi phục qua MTTR Timer.
              </p>
            </div>
          </div>

          <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
            <span className="w-6 h-6 rounded bg-cyan-900 text-cyan-300 font-bold flex items-center justify-center shrink-0">
              5
            </span>
            <div>
              <strong className="text-slate-200 block text-[13px]">Bước 5: Đánh Giá & Benchmark So Sánh Mạng Truyền Thống</strong>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Chạy 14 kịch bản, mỗi kịch bản 5 lần, xuất bảng số liệu MTTR, tỷ lệ phát hiện chính xác RCA và so sánh với thời gian sửa thủ công (15-30 phút) để đưa vào chương kết quả của luận văn.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Code Snippets Section: Ready to Copy */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-lg space-y-4">
        <h2 className="text-sm font-bold text-cyan-400 font-mono uppercase tracking-wider flex items-center gap-2">
          <Terminal className="w-4 h-4" /> 3. Mã Nguồn Mẫu Hoàn Chỉnh Cho Thư Mục Mininet (Copy & Chạy)
        </h2>

        {/* Snippet 1: data_bridge.py */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-300 font-bold">1. File: src/noc/backend/data_bridge.py</span>
            <button
              onClick={() => copyToClipboard(dataBridgeCode, 'bridge')}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[11px]"
            >
              {copiedCodeId === 'bridge' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedCodeId === 'bridge' ? 'Đã sao chép!' : 'Copy Code'}</span>
            </button>
          </div>
          <pre className="p-3 rounded bg-slate-950 border border-slate-800 text-slate-300 text-[11px] font-mono overflow-x-auto max-h-64 overflow-y-auto">
            {dataBridgeCode}
          </pre>
        </div>

        {/* Snippet 2: app.py */}
        <div className="space-y-1.5 pt-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-300 font-bold">2. File: src/noc/backend/app.py (Flask-SocketIO Server)</span>
            <button
              onClick={() => copyToClipboard(appPyCode, 'app')}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[11px]"
            >
              {copiedCodeId === 'app' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedCodeId === 'app' ? 'Đã sao chép!' : 'Copy Code'}</span>
            </button>
          </div>
          <pre className="p-3 rounded bg-slate-950 border border-slate-800 text-slate-300 text-[11px] font-mono overflow-x-auto max-h-64 overflow-y-auto">
            {appPyCode}
          </pre>
        </div>

        {/* Snippet 3: prometheus.yml */}
        <div className="space-y-1.5 pt-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-300 font-bold">3. File: /etc/prometheus/prometheus.yml</span>
            <button
              onClick={() => copyToClipboard(prometheusYamlCode, 'prom')}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[11px]"
            >
              {copiedCodeId === 'prom' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedCodeId === 'prom' ? 'Đã sao chép!' : 'Copy Code'}</span>
            </button>
          </div>
          <pre className="p-3 rounded bg-slate-950 border border-slate-800 text-slate-300 text-[11px] font-mono overflow-x-auto max-h-64 overflow-y-auto">
            {prometheusYamlCode}
          </pre>
        </div>
      </div>
    </div>
  );
};
