# KẾ HOẠCH CHI TIẾT — GIAI ĐOẠN TIẾP THEO (Phase 7 → Phase 21)
## Dự án: Self-Healing Enterprise Network

> **Trạng thái hiện tại:** Phase 0–6 ✅ hoàn thành  
> **Mục tiêu:** Hoàn thiện đầy đủ 21 Phase, kết thúc với bộ đánh giá 12 fault scenarios  
> **Môi trường:** Ubuntu 20.04/22.04 + Mininet + Python 3.9+

---

## TỔNG QUAN LỘ TRÌNH

```
Đã hoàn thành:
Phase 0-6: Hạ tầng mạng enterprise baseline
 ✅ Topology + VLAN + RSTP + OSPF + VRRP + DHCP/DNS/NTP

Còn lại (ước tính 3-5 tháng):
Phase 7:  ACL + Firewall + Segmentation
Phase 8:  Data Center Services (Load Balancing, HAProxy)
Phase 9:  WAN Transport Emulation (5 paths)
Phase 10: SD-WAN Controller
Phase 11: QoS + VoIP (Asterisk/SIP/RTP)
Phase 12: Monitoring + Telemetry (Prometheus)
Phase 12B: NOC Dashboard (Flask + SocketIO)
Phase 13: Event Correlation
Phase 14: SDN Controller (Faucet/Ryu - OpenFlow)
Phase 15: AI Anomaly Detection
Phase 16: AI Root Cause Analysis
Phase 17: Recovery Decision Engine
Phase 18: AI ↔ Controller Integration
Phase 19: Fault Injection Framework
Phase 20: Self-Healing Loop (Full Integration)
Phase 21: Đánh giá + Benchmarking
```

---

## PHASE 7 — ACL + Firewall + Network Segmentation

**Mục tiêu:** Áp dụng chính sách bảo mật. Đây là nền tảng để sau này AI có thể enforce/relax policy khi cần phục hồi.

### Nội dung:
1. **ACL cơ bản (tại DIST routers):**
   ```
   USER → WEB Server    : ALLOW
   WEB  → APP Server    : ALLOW
   APP  → DB Server     : ALLOW
   CCTV → DB Server     : DENY
   IoT  → USER VLAN     : DENY
   ```

2. **Firewall zone (tại DC-SP-GW):**
   ```
   Internet → DMZ (WEB01/02)    : ALLOW port 80, 443
   DMZ      → Internal (APP)   : ALLOW port 8080
   Internal → DB               : ALLOW port 3306, 5432
   Internet → Internal         : DENY (default)
   ```

3. **Implementation trong Mininet:** Dùng `iptables` trên Host Routers (BL_GW, NT_DIST01/02, HCM_DIST01/02, DC_SP_GW).

### Files cần tạo/sửa:
- `src/scripts/configure_acl.py` — Script cài ACL rules
- `src/config/acl_rules.yaml` — Định nghĩa rules
- `src/tests/phase_checks/check_phase7.py` — Test script

### Checkpoint:
- [ ] CCTV không ping được DB Server
- [ ] IoT không ping được USER VLAN
- [ ] PC ping được WEB Server thành công
- [ ] ACL không block traffic hợp lệ

**Ước tính thời gian:** 3-5 ngày

---

## PHASE 8 — Data Center Services (Load Balancing)

**Mục tiêu:** Triển khai HAProxy load balancing cho WEB servers. Đây là điều kiện cho scenario F11 (WEB server failure).

### Nội dung:
1. **HAProxy trên DC-APP01:**
   ```
   VIP: 10.100.10.10
   Backend: DC-WEB01 (10.100.10.11), DC-WEB02 (10.100.10.12)
   Health check: HTTP GET /health mỗi 2s
   ```

2. **Failover logic:**
   ```
   DC-WEB01 DOWN:
   HAProxy health check fails (3 lần)
     ↓
   Remove DC-WEB01 from backend pool
     ↓
   All traffic → DC-WEB02
     ↓
   Recovery trong < 5s
   ```

3. **Kết hợp với DNS:**
   - `www.enterprise.local` → VIP `10.100.10.10` (không đổi ngay cả khi WEB01 down)

### Files cần tạo/sửa:
- `src/scripts/configure_haproxy.py` — Tạo HAProxy config trong namespace DC-APP01
- `src/config/haproxy.cfg` — Template config
- `src/tests/phase_checks/check_phase8.py`

### Checkpoint:
- [ ] `curl http://10.100.10.10` trả về response từ WEB01 hoặc WEB02
- [ ] Kill DC-WEB01 → trong < 5s, HAProxy tự chuyển sang WEB02
- [ ] DNS vẫn resolve đúng VIP

**Ước tính thời gian:** 3-4 ngày

---

## PHASE 9 — WAN Transport Emulation (5 Paths)

**Mục tiêu:** Tạo 5 đường WAN song song với đặc tính khác nhau. Đây là tiền đề cho toàn bộ SD-WAN scenarios.

### Kiến trúc WAN trong Mininet:
```
Branch GW ──── WAN-SW-MPLS ──── DC-SP-GW
           ──── WAN-SW-INET ────
           ──── WAN-SW-LTE  ────
           ──── WAN-SW-5G   ────
           ──── WAN-SW-VPN  ────
```

Mỗi `WAN-SW-*` là một OVS Switch riêng với `tc netem` áp đặt đặc tính:

```bash
# MPLS: delay 20ms, loss 0.1%, bandwidth 100Mbps
tc qdisc add dev wan-mpls-link root handle 1: tbf rate 100mbit burst 32kbit latency 50ms
tc qdisc add dev wan-mpls-link parent 1:1 handle 10: netem delay 20ms loss 0.1%

# Internet: delay 40ms, loss 0.5%, bandwidth 100Mbps
tc qdisc add dev wan-inet-link root netem delay 40ms loss 0.5% rate 100mbit

# LTE: delay 60ms, loss 1.0%, bandwidth 30Mbps
tc qdisc add dev wan-lte-link root netem delay 60ms loss 1.0% rate 30mbit

# 5G: delay 15ms, loss 0.3%, bandwidth 200Mbps
tc qdisc add dev wan-5g-link root netem delay 15ms loss 0.3% rate 200mbit

# VPN: delay 50ms, loss 0.8%, bandwidth 50Mbps
tc qdisc add dev wan-vpn-link root netem delay 50ms loss 0.8% rate 50mbit
```

### Files cần tạo/sửa:
- `src/topology/wan/wan_topo.py` — Định nghĩa 5 WAN path trong Mininet
- `src/scripts/configure_wan.py` — Script áp dụng tc netem
- `src/topology/enterprise_topo.py` — Tích hợp WAN vào topology phase 9+
- `src/tests/phase_checks/check_phase9.py`

### Checkpoint:
- [ ] `ping -c 10` từ HCM-ADMIN-PC01 đến DC-WEB01 qua MPLS: latency ~20ms
- [ ] Khi fault inject MPLS: traffic chuyển sang 5G, latency tăng lên ~15ms (5G nhanh hơn)
- [ ] Mỗi path có thể bật/tắt độc lập bằng `ip link set down`

**Ước tính thời gian:** 5-7 ngày (phần phức tạp nhất về routing)

---

## PHASE 10 — SD-WAN Controller (Python tự viết)

**Mục tiêu:** Xây dựng SD-WAN Controller có khả năng chọn đường WAN và điều hướng traffic theo policy.

### Kiến trúc SD-WAN Controller:
```
src/controller/sdwan/
├── sdwan_controller.py      # Core controller
├── path_monitor.py          # Giám sát 5 WAN paths
├── policy_engine.py         # Đọc policy YAML, ra quyết định chọn đường
├── traffic_steerer.py       # Thực thi: gửi config xuống SD-WAN Edge GW
└── probes/
    └── wan_prober.py        # ICMP/iperf probe đo latency/loss/jitter
```

### Logic Path Selection:
```python
def select_best_path(traffic_class, available_paths):
    """
    traffic_class: 'voip', 'database', 'web', 'bulk', 'backup'
    Trả về: path tốt nhất dựa trên SLA requirement
    """
    sla = SLA_REQUIREMENTS[traffic_class]
    candidates = [p for p in available_paths if p.status == 'UP']
    candidates = [p for p in candidates if p.latency <= sla['max_latency']]
    candidates = [p for p in candidates if p.loss <= sla['max_loss']]
    candidates = [p for p in candidates if p.jitter <= sla['max_jitter']]
    return min(candidates, key=lambda p: p.latency)  # Chọn latency thấp nhất
```

### Files cần tạo:
- `src/controller/sdwan/sdwan_controller.py`
- `src/controller/sdwan/policy_engine.py`
- `src/controller/sdwan/path_monitor.py`
- `src/controller/sdwan/traffic_steerer.py`
- `src/config/sdwan_policy.yaml`

### Checkpoint:
- [ ] SD-WAN Controller khởi động, monitor 5 paths liên tục
- [ ] Fault inject MPLS → Controller detect trong < 3s → Switch traffic sang 5G
- [ ] Policy engine đọc YAML và áp dụng đúng quy tắc traffic class

**Ước tính thời gian:** 7-10 ngày

---

## PHASE 11 — QoS + VoIP (Asterisk/SIP/RTP)

**Mục tiêu:** Triển khai VoIP service và QoS marking để AI có thể đánh giá QoE.

### Nội dung:
1. **Asterisk SIP Server** trên DC-APP01:
   - SIP registrar cho IP Phone tại NT (VLAN 190) và HCM (VLAN 297)
   - RTP media stream giữa các IP Phone

2. **DSCP Marking:**
   ```
   VoIP RTP  → DSCP EF (46) → Priority Queue (WAN)
   VoIP SIP  → DSCP CS3/AF31
   Database  → DSCP AF21
   Web/App   → DSCP AF11
   Bulk/CCTV → DSCP BE (0)
   ```

3. **tc HTB (Hierarchical Token Bucket)** trên WAN links:
   ```
   WAN link 100Mbps:
   ├── VoIP class: min 10Mbps, prio 1
   ├── Business class: min 40Mbps, prio 2
   └── Default class: min 10Mbps, prio 3
   ```

### Files cần tạo:
- `src/scripts/configure_qos.py` — tc HTB + DSCP marking
- `src/scripts/configure_asterisk.py` — Khởi động Asterisk trong DC-APP01 namespace
- `src/config/asterisk/` — Config files cho Asterisk

### Checkpoint:
- [ ] SIP registration thành công từ NT-VOICE-PC01 đến DC-APP01
- [ ] iperf3 UDP test: VoIP traffic không bị drop khi WAN congested
- [ ] DSCP EF packets đi qua Priority Queue, không bị delay

**Ước tính thời gian:** 5-7 ngày

---

## PHASE 12 — Monitoring + Telemetry (Prometheus)

**Mục tiêu:** Xây dựng hệ thống thu thập dữ liệu làm đầu vào cho AI.

### Kiến trúc Telemetry:
```
src/monitoring/
├── telemetry_collector.py   # Orchestrator chính
├── collectors/
│   ├── openflow_collector.py  # Thu thập OpenFlow stats từ Faucet
│   ├── snmp_collector.py      # SNMP polling (CPU, IF utilization)
│   ├── icmp_prober.py         # ICMP probe (latency, loss)
│   ├── iperf_prober.py        # iperf3 (throughput, jitter)
│   ├── ospf_collector.py      # FRR syslog parser (OSPF state)
│   └── vrrp_collector.py      # Keepalived syslog parser
└── prometheus_exporter.py    # Export metrics lên Prometheus :9090
```

### Metrics cần thu thập:
```
# Network metrics
of_port_status{dp, port}             # 0=DOWN, 1=UP
of_errors_total{dp, error_type}      # OpenFlow error count
faucet_dp_status{dp}                 # Datapath status
ospf_neighbor_state{router, neighbor}
vrrp_state{host, vrid}
wan_path_status{site, transport}
wan_latency_ms{site, transport}
wan_loss_percent{site, transport}
wan_jitter_ms{site, transport}
interface_utilization{device, if}    # % bandwidth usage

# System metrics
node_cpu_usage_percent{host}
node_memory_usage_percent{host}
```

### Files cần tạo:
- `src/monitoring/telemetry_collector.py`
- `src/monitoring/collectors/*.py`
- `src/monitoring/prometheus_exporter.py`
- `src/config/prometheus.yml`

### Checkpoint:
- [ ] Prometheus scrape thành công, hiển thị metrics tại `http://localhost:9090`
- [ ] `of_port_status` thay đổi ngay khi fault inject link down
- [ ] `wan_latency_ms` hiển thị đúng giá trị tc netem đã cấu hình

**Ước tính thời gian:** 5-7 ngày

---

## PHASE 12B — NOC Dashboard (Flask + SocketIO)

**Mục tiêu:** Giao diện web thời gian thực để giám sát và trực quan hoá toàn bộ quá trình tự phục hồi.

### Kiến trúc:
```
src/noc/
├── backend/
│   ├── app.py              # Flask + SocketIO server (:5050)
│   ├── data_bridge.py      # Đọc Prometheus → broadcast SocketIO
│   └── routes.py           # REST API endpoints
└── frontend/
    ├── index.html
    ├── css/dashboard.css   # Dark theme
    └── js/
        ├── topology.js     # vis-network topology map
        ├── charts.js       # Chart.js real-time metrics
        └── alerts.js       # AI decision log
```

### Các panel:
1. **Topology Map** (vis-network): Node/Link đổi màu RED(fault)/YELLOW(congested)/GREEN(healthy)
2. **WAN Path Status**: Latency, jitter, loss của 5 paths theo real-time
3. **Metrics Charts**: CPU, memory, interface utilization (cập nhật mỗi 5s)
4. **AI Decision Log**: Anomaly → RCA → Action → Result (MTTR)
5. **Recovery History**: Thống kê MTTR theo scenario

### Checkpoint:
- [ ] Dashboard mở tại `http://localhost:5050`
- [ ] Khi fault inject, topology map tự đổi màu RED
- [ ] AI Decision Log hiển thị đúng chuỗi: Detect → RCA → Action

**Ước tính thời gian:** 7-10 ngày (UI/UX + WebSocket integration)

---

## PHASE 13 — Event Correlation

**Mục tiêu:** Kết hợp nhiều nguồn dữ liệu để AI hiểu bức tranh tổng thể.

### Nội dung:
```
10:00:01  Interface utilization ↑ (85%)
10:00:02  Packet loss ↑ (3%)
10:00:03  OSPF neighbor DOWN (BL-GW ↔ HCM-GW)
10:00:04  Route table changed (BL → HCM via NT)
10:00:05  VoIP jitter ↑ (40ms)
            ↓
Correlation Engine:
"Tất cả 5 event thuộc cùng 1 fault: WAN link BL-HCM failure"
            ↓
Root Cause: Single link failure (không phải 5 sự cố riêng lẻ)
```

### Kỹ thuật:
- **Time-window correlation:** Group events trong cửa sổ 30s
- **Topology-based correlation:** Sự kiện trên cùng một node/link → cùng 1 fault
- **Dependency graph:** Biết NT-ACC02 → NT-DIST01 → NT-CORE → WAN để trace impact

### Files cần tạo:
- `src/ai_engine/event_correlator.py`
- `src/ai_engine/dependency_graph.py`
- `src/config/network_topology_graph.json`

**Ước tính thời gian:** 4-5 ngày

---

## PHASE 14 — SDN Controller (Faucet + OpenFlow)

**Mục tiêu:** Tích hợp Faucet SDN Controller để điều khiển LAN.

### Kiến trúc:
```
Faucet SDN Controller (:6653)
         │
      OpenFlow 1.3
         │
   ┌─────┼─────────┐
   │     │         │
NT-CORE HCM-CORE BL-SW
   │     │
DIST01/02 DIST01/02
   │     │
 ACC01-06 ACC01-06
```

### Faucet Configuration (YAML):
```yaml
vlans:
  vlan110:
    vid: 110
    description: NT ADMIN
dps:
  NT_CORE:
    dp_id: 0x01
    interfaces:
      1: {name: to_dist01, tagged_vlans: [110,120,...]}
      2: {name: to_dist02, tagged_vlans: [110,120,...]}
```

### Files cần tạo/sửa:
- `src/controller/sdn/faucet_controller.py` — Wrapper quản lý Faucet
- `src/controller/sdn/flow_manager.py` — CRUD operations cho Flow Table
- `src/config/faucet.yaml` — Faucet config cho toàn bộ topology
- `src/controller/sdn/openflow_agent.py` — Agent giao tiếp Faucet REST API

### Checkpoint:
- [ ] Faucet khởi động, kết nối với tất cả OVS switches
- [ ] `pingall` vẫn pass khi Faucet kiểm soát
- [ ] `flow_manager.py` có thể install/delete flow rules theo lệnh

**Ước tính thời gian:** 7-10 ngày

---

## PHASE 15 — AI Anomaly Detection

**Mục tiêu:** Phát hiện trạng thái bất thường từ telemetry data.

### Model:
- **Isolation Forest** (scikit-learn): Phát hiện outlier trong không gian đa chiều
- **Dynamic Thresholding**: Ngưỡng tự thích nghi theo trung bình động

### Pipeline:
```python
# Input: 12 features từ Prometheus
features = [
    cpu_util, mem_util,
    if_utilization, packet_loss, latency, jitter,
    ospf_neighbors_up, vrrp_state,
    wan_path_up_count, of_errors, of_port_down_count,
    qoe_score
]

# Normalization
scaler = StandardScaler()
X = scaler.fit_transform(features)

# Anomaly Detection
detector = IsolationForest(contamination=0.05, random_state=42)
anomaly_score = detector.score_samples(X)  # -1 = anomaly, 1 = normal

# Threshold
if anomaly_score < -0.7:
    trigger_rca()
```

### Training data:
- Phase 0-6 logs = "normal" baseline
- Fault injection scenarios = "anomaly" samples
- Semi-supervised: 95% normal, 5% anomaly (realistic ratio)

### Files cần tạo:
- `src/ai_engine/anomaly_detector.py`
- `src/ai_engine/models/isolation_forest_model.pkl` (trained model)
- `src/ai_engine/feature_extractor.py`
- `src/training/train_anomaly_detector.py`

### Checkpoint:
- [ ] Model train xong, accuracy ≥ 90% trên validation set
- [ ] Khi fault inject: anomaly score > threshold trong < 10s
- [ ] Khi mạng bình thường: false positive rate < 5%

**Ước tính thời gian:** 5-7 ngày

---

## PHASE 16 — AI Root Cause Analysis (RCA)

**Mục tiêu:** Xác định nguyên nhân gốc của sự cố, không chỉ triệu chứng.

### Kỹ thuật:
1. **Decision Tree Classifier:** Phân loại root cause từ symptom vector
2. **Causal Chain Analysis:** Truy ngược từ symptom → cause qua dependency graph

### Decision Tree Logic:
```
IF P_down > 0 THEN
    IF dpid ∈ access_switches THEN root_cause = "ACCESS_LINK_FAILURE"
    ELSE root_cause = "DISTRIBUTION_FAILURE"
ELSE IF f_disc > 0 THEN
    root_cause = "CONTROLLER_DISCONNECT"
ELSE IF wan_path_down ≥ 1 THEN
    root_cause = "WAN_LINK_FAILURE"
ELSE IF latency > 150ms AND loss < 1% THEN
    root_cause = "WAN_CONGESTION"
ELSE IF qoe_score < 3.5 AND jitter > 30ms THEN
    root_cause = "VOIP_QUALITY_DEGRADATION"
```

### Files cần tạo:
- `src/ai_engine/rca_engine.py`
- `src/ai_engine/causal_graph.py`
- `src/training/train_rca_classifier.py`

### Checkpoint:
- [ ] RCA Engine phân loại đúng ≥ 85% test scenarios
- [ ] Thời gian RCA < 5s sau khi anomaly được phát hiện
- [ ] Output của RCA đúng format cho Recovery Decision Engine

**Ước tính thời gian:** 5-7 ngày

---

## PHASE 17 — Recovery Decision Engine

**Mục tiêu:** Từ root cause → chọn recovery action tối ưu.

### Hai cơ chế quyết định:

**A. PPO Reinforcement Learning Agent (Reactive - LAN):**
```python
# State vector (8 chiều)
s_t = [C_cpu, C_res_mem, C_virt_mem, f_sent, f_err, f_conn, f_disc, P_down]

# Actions
ACTIONS = {
    0: "no_op",
    1: "reset_port",
    2: "restart_switch_controller",
    3: "bespoke_self_heal_flow"
}

# PPO Agent chọn action dựa trên policy network (MLP)
action = ppo_agent.select_action(s_t)
```

**B. Rule-based Engine (WAN - SD-WAN):**
```python
def wan_recovery_action(root_cause, available_paths, traffic_classes):
    if root_cause == "MPLS_DOWN":
        return steer_traffic(traffic_classes, from_path="MPLS",
                           to_path=best_available(["5G", "Internet", "LTE"]))
    elif root_cause == "WAN_CONGESTION":
        return traffic_preemption(priority_flows=["voip", "database"],
                                 offload_path="5G")
    ...
```

### Files cần tạo:
- `src/ai_engine/decision_engine.py`
- `src/ai_engine/ppo_agent.py` (PPO implementation)
- `src/ai_engine/wan_recovery_rules.py`
- `src/training/train_ppo_agent.py` (RL training loop)

### Checkpoint:
- [ ] PPO Agent train được (reward tăng dần qua episodes)
- [ ] Decision Engine output đúng format Recovery Intent
- [ ] Thời gian quyết định < 2s

**Ước tính thời gian:** 10-14 ngày (phần phức tạp nhất)

---

## PHASE 18 — AI ↔ Controller Integration

**Mục tiêu:** Kết nối AI Engine với SDN Controller và SD-WAN Controller.

### Kiến trúc tích hợp:
```
AI Engine (Recovery Intent)
        │
        ▼
Policy / Safety Layer
        │
   Approved?
   /       \
 YES         NO
  │           │
  ▼           ▼
Global      Alert
Orchestrator  Human
  │
  ├─── LAN Recovery Intent ──→ SDN Controller (Faucet API)
  │         │                        │
  │         └── OpenFlow Port Mod    └── Flow Rule Reinstall
  │
  └─── WAN Recovery Intent ──→ SD-WAN Controller
            │
            └── Path Switch / Traffic Steering
```

### REST API giữa AI và Controller:
```python
# AI gửi Recovery Intent lên Orchestrator
POST /api/recovery
{
    "root_cause": "ACCESS_LINK_FAILURE",
    "target": {"domain": "LAN", "dpid": "s1", "port": 2},
    "action": "reset_port",
    "confidence": 0.97,
    "risk": "low"
}

# Orchestrator gọi SDN Controller
POST http://faucet_controller/api/port_mod
{
    "dp_id": "0x01",
    "port_no": 2,
    "state": "UP"
}
```

### Files cần tạo:
- `src/ai_engine/orchestrator.py`
- `src/ai_engine/policy_safety_layer.py`
- `src/controller/sdn/faucet_api_client.py`
- `src/controller/sdwan/sdwan_api_client.py`

### Checkpoint:
- [ ] AI → Orchestrator → SDN Controller: full chain hoạt động end-to-end
- [ ] Policy Safety Layer từ chối quyết định confidence < 80%
- [ ] Recovery Intent được log và hiển thị trên NOC Dashboard

**Ước tính thời gian:** 5-7 ngày

---

## PHASE 19 — Fault Injection Framework

**Mục tiêu:** Tự động inject các loại sự cố để test self-healing loop.

### Fault Types:
| ID | Loại sự cố | Lệnh inject | Lệnh restore |
| --- | --- | --- | --- |
| F01 | Access link failure | `ip link set NT-ACC02-eth0 down` | `ip link set NT-ACC02-eth0 up` |
| F02 | Distribution failure | `kill $(cat /tmp/ka_dist01.pid)` | Restart keepalived |
| F03 | OSPF link failure | `ip link set BL-GW-eth1 down` | `ip link set up` |
| F04 | MPLS down | `tc qdisc del dev mpls-link root` | Re-add tc qdisc |
| F05 | Internet down | `ip link set wan-inet-link down` | `ip link set up` |
| F09 | WAN congestion | `tc qdisc change netem loss 20% delay 200ms` | Reset tc |
| F10 | VoIP degradation | `tc qdisc change netem jitter 50ms delay 100ms` | Reset tc |

### Automated Fault Injection:
```python
class FaultInjector:
    def inject(self, fault_id, site="HCM"):
        """Inject fault và chờ AI phản ứng"""
        self.timestamp_start = time.time()
        self._execute_fault_cmd(fault_id, site)
        
    def measure_recovery(self):
        """Đo MTTR: từ fault_start đến service_restored"""
        while not self._check_service_restored():
            time.sleep(0.5)
        return time.time() - self.timestamp_start
```

### Files cần tạo:
- `src/fault_injection/fault_injector.py`
- `src/fault_injection/fault_scenarios.yaml`
- `src/fault_injection/recovery_monitor.py`

### Checkpoint:
- [ ] FaultInjector có thể inject và restore tất cả 12 fault types
- [ ] Recovery Monitor đo được MTTR chính xác
- [ ] Log đầy đủ: fault_time, detect_time, rca_time, action_time, recover_time

**Ước tính thời gian:** 4-5 ngày

---

## PHASE 20 — Self-Healing Loop (Full Integration)

**Mục tiêu:** Chạy vòng lặp tự phục hồi hoàn chỉnh, end-to-end.

### Vòng lặp chính:
```python
while True:
    # 1. Thu thập telemetry
    state = telemetry_collector.collect()
    
    # 2. Phát hiện anomaly
    anomaly = anomaly_detector.detect(state)
    
    if anomaly:
        # 3. Root Cause Analysis
        root_cause = rca_engine.analyze(state, anomaly)
        
        # 4. Recovery Decision
        intent = decision_engine.decide(root_cause, state)
        
        # 5. Safety Check
        if safety_layer.approve(intent):
            # 6. Execute Recovery
            orchestrator.execute(intent)
            
            # 7. Verify
            time.sleep(5)
            new_state = telemetry_collector.collect()
            if verify(new_state, root_cause):
                log_success(intent, mttr)
            else:
                log_failure(intent)
                alert_human(root_cause, intent)
    
    # Broadcast to NOC
    noc_socket.broadcast(state, anomaly, intent if anomaly else None)
    
    time.sleep(5)
```

### Checkpoint:
- [ ] Full loop chạy ổn định 30 phút không crash
- [ ] Inject F04 (MPLS down) → AI detect < 10s → recover < 5s
- [ ] NOC Dashboard hiển thị toàn bộ quá trình real-time

**Ước tính thời gian:** 7-10 ngày (integration testing)

---

## PHASE 21 — Đánh giá & Benchmarking

**Mục tiêu:** Đo lường hiệu quả của hệ thống tự phục hồi và so sánh với baseline.

### Metrics đánh giá:

| Metric | Đơn vị | Mục tiêu |
| --- | --- | --- |
| Detection Time | seconds | < 10s |
| RCA Time | seconds | < 5s |
| Decision Time | seconds | < 2s |
| Recovery Time (MTTR) | seconds | < 30s (LAN), < 5s (WAN) |
| Recovery Success Rate | % | > 95% |
| Packet Recovery Rate | % | > 99% |
| Network Availability | % | > 99.9% |
| False Positive Rate | % | < 5% |

### Bộ test cuối cùng (12 scenarios × 5 lần mỗi loại = 60 runs):

```python
scenarios = [F01, F02, F03, F04, F05, F06, F07, F08, F09, F10, F11, F12]

results = []
for scenario in scenarios:
    for run in range(5):
        fault_injector.inject(scenario)
        mttr = recovery_monitor.wait_for_recovery()
        results.append({
            "scenario": scenario,
            "run": run,
            "detection_time": ...,
            "rca_time": ...,
            "decision_time": ...,
            "mttr": mttr,
            "success": mttr < MTTR_THRESHOLD[scenario]
        })

# Export to CSV + plots
export_results(results, "evaluation_results.csv")
plot_mttr_distribution(results)
plot_success_rate_by_scenario(results)
```

### So sánh với baseline:

| Scenario | Flat Network (MTTR) | VRRP/OSPF (MTTR) | Self-Healing (MTTR) | Cải thiện |
| --- | --- | --- | --- | --- |
| F01 (Access failure) | ~120s | ~30s | < 20s | **33% nhanh hơn** |
| F04 (MPLS down) | Manual | ~60s | < 5s | **92% nhanh hơn** |
| F09 (WAN congestion) | Manual | Không tự động | < 10s | **Hoàn toàn tự động** |

### Files cần tạo:
- `src/evaluation/benchmark_runner.py`
- `src/evaluation/metrics_calculator.py`
- `src/evaluation/report_generator.py` (tạo CSV + matplotlib plots)

**Ước tính thời gian:** 7-10 ngày

---

## TIMELINE TỔNG THỂ (Ước tính)

| Phase | Nội dung | Tuần |
| --- | --- | --- |
| 7 | ACL + Firewall | Tuần 1 |
| 8 | Data Center Services | Tuần 1-2 |
| 9 | WAN Transport | Tuần 2-3 |
| 10 | SD-WAN Controller | Tuần 3-4 |
| 11 | QoS + VoIP | Tuần 5 |
| 12 | Monitoring (Prometheus) | Tuần 6 |
| 12B | NOC Dashboard | Tuần 7 |
| 13 | Event Correlation | Tuần 7-8 |
| 14 | SDN Controller | Tuần 8-9 |
| 15 | AI Anomaly Detection | Tuần 9-10 |
| 16 | AI RCA | Tuần 10-11 |
| 17 | Recovery Decision Engine | Tuần 11-13 |
| 18 | AI ↔ Controller Integration | Tuần 13-14 |
| 19 | Fault Injection Framework | Tuần 14 |
| 20 | Self-Healing Loop | Tuần 15-16 |
| 21 | Đánh giá | Tuần 17-18 |

**Tổng: ~18 tuần (4-5 tháng)** từ ngày 2026-09-26

---

## ƯU TIÊN CÔNG VIỆC TIẾP THEO (Tuần tới)

1. **Ưu tiên cao nhất:** Phase 9 (WAN) — nền tảng cho tất cả SD-WAN scenarios
2. **Song song:** Phase 12 (Prometheus) — cần có data để test AI sau này
3. **Sau đó:** Phase 14 (SDN Controller/Faucet) — để tích hợp với PPO Agent

### Thứ tự thực hiện gợi ý:
```
Phase 7 → Phase 8 → Phase 9 → Phase 10 → Phase 12 → Phase 12B
    → Phase 11 → Phase 13 → Phase 14 → Phase 15 → Phase 16
    → Phase 17 → Phase 18 → Phase 19 → Phase 20 → Phase 21
```

---

*Tài liệu cập nhật lần cuối: 2026-09-26*  
*Phase tiếp theo cần bắt đầu: **Phase 7 — ACL + Firewall***
