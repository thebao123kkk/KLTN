# CHI TIẾT 14 KỊCH BẢN SỰ CỐ MẠNG
## Đề tài: Mạng Doanh Nghiệp Tự Phục Hồi Sử Dụng SD-WAN và Cơ Chế Khôi Phục Sự Cố Thông Minh

> **Tài liệu này mô tả chi tiết từng kịch bản sự cố (Fault Scenario) trong bộ 14 test case thử nghiệm hệ thống Self-Healing.**  
> Mỗi kịch bản bao gồm: Mô tả sự cố, Cơ chế phát hiện (Detection), Phân tích nguyên nhân gốc rễ (RCA), Luồng tự phục hồi (Recovery Flow), KPI mục tiêu và Phương pháp tiêm lỗi (Fault Injection).

---

## PHÂN LOẠI TỔNG QUAN

| Nhóm | ID | Tên Kịch Bản | Controller | Cơ Chế | MTTR Mục Tiêu |
|:---:|:---:|:---|:---:|:---:|:---:|
| 🔴 Reactive | F01 | Access Link Failure | SDN | RSTP + Flow Reroute | < 30s |
| 🔴 Reactive | F02 | Distribution Failure (VRRP) | SDN | VRRP Failover + OSPF | < 5s |
| 🔴 Reactive | F03 | OSPF Link Failure | SDN | OSPF Reconvergence | < 40s |
| 🔴 Reactive | F04 | MPLS WAN Down | SD-WAN | Switch to 5G/Internet | < 5s |
| 🔴 Reactive | F05 | Internet WAN Down | SD-WAN | Switch to MPLS/5G | < 5s |
| 🔴 Reactive | F06 | LTE Down | SD-WAN | Switch to 5G/MPLS | < 5s |
| 🔴 Reactive | F07 | 5G Degradation | SD-WAN | Switch back to MPLS | < 5s |
| 🔴 Reactive | F08 | VPN Failure | SD-WAN | Switch to other transport | < 5s |
| 🔴 Reactive | F09 | WAN Congestion | SD-WAN | Traffic Steering + QoS | < 10s |
| 🔴 Reactive | F10 | VoIP Degradation | SD-WAN + QoS | QoE-driven Path Change | < 3s |
| 🔴 Reactive | F11 | Web Server Crash | Load Balancer | HAProxy → WEB02 | < 5s |
| 🔴 Reactive | F12 | Multi-Metric Anomaly | AI Engine | Automated Recovery Chain | < 60s |
| 🟡 Proactive | P1 | Preemptive Traffic Steering | SD-WAN | Holt-Winters Forecast | 0s (trước sự cố) |
| 🟡 Proactive | P2 | Mid-Session QoE Protection | SD-WAN | QoE Regression | 0s (trước vi phạm SLA) |

---

## 🔴 NHÓM SỰ CỐ PHẢN ỨNG (REACTIVE SCENARIOS — F01 ĐẾN F12)

---

### F01 — Access Link Failure (Đứt Liên Kết Tầng Access)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Chi nhánh Nha Trang — Switch tầng Access `NT-ACC02` (phục vụ phòng SALES, VLAN 120).
- **Hiện tượng:** Cáp mạng kết nối giữa Access Switch `NT-ACC02` và Distribution Switch `NT-DIST01` bị đứt đột ngột.
- **Tác động:** Toàn bộ 3 PC thuộc phòng Kinh Doanh (VLAN 120, subnet `10.20.20.0/24`) mất kết nối mạng nội bộ và không truy cập được Data Center.
- **Fault Domain:** Rất nhỏ, chỉ ảnh hưởng 1 phòng ban (SALES), các phòng khác hoạt động bình thường.

#### 🔍 Cơ Chế Phát Hiện (Detection)
```
Prometheus ghi nhận:
  of_port_status{dp="NT_CORE", port="ACC02_port"} = 0  ← Link Down Event
  
OpenFlow port_status message:
  OFPT_PORT_STATUS (reason=DOWN) từ NT-CORE → Faucet Controller

Anomaly Detection trigger:
  Latency VLAN120 traffic → ∞ (No reply)
  Packet Loss VLAN120 → 100%
```

#### 🧠 Phân Tích Nguyên Nhân Gốc Rễ (RCA)
```
RCA Engine:
  Input:  of_port_status{dp="NT_CORE", port="ACC02_port"} = 0
  Phân tích ma trận phụ thuộc:
    NT-CORE.port_ACC02 DOWN
      └─► NT-ACC02 DISCONNECTED
            └─► VLAN 120 (SALES) ISOLATED
                └─► 3 PC [10.20.20.10/11/12] mất mạng

  Kết luận RCA: "NT-ACC02 DOWN → Fault Domain: NT-SALES (VLAN120)"
  Confidence Score: 97%
```

#### 🔄 Luồng Tự Phục Hồi (Recovery Flow)
```
Bước 1: PPO Agent nhận s_t với P_down = 1
         └─► Quyết định a_t = 1 (Reset Port)

Bước 2: Context Parser trích xuất metadata:
         {target_dpid: "NT_CORE", target_port: "ACC02_port"}

Bước 3: Safety Layer kiểm tra:
         ✓ Confidence = 97% ≥ 80%  → PASS
         ✓ Blast Radius = 1/88 = 1.1% ≤ 30%  → PASS
         ✓ Có rollback plan → PASS
         → CHO PHÉP TỰ ĐỘNG THỰC THI

Bước 4: Faucet SDN Controller phát lệnh OpenFlow:
         PORT_MOD: OFPPC_PORT_DOWN → OFPPC_PORT_UP
         Gửi tới: NT-CORE, Port ACC02_port

Bước 5: RSTP tự động tính toán đường dự phòng:
         NT-ACC02 tự bầu lại port Root theo STP
         Traffic reroute qua NT-DIST02 (nếu còn link phụ)

Bước 6: Verify - Prometheus kiểm tra:
         of_port_status{...} = 1 → PASS
         Packet Loss VLAN120 → 0%
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR (Mean Time To Repair) | < 30 giây |
| Fault Domain | 1 phòng ban (SALES) |
| Phương pháp khôi phục | OpenFlow Port Reset + RSTP |
| PPO Action | a_t = 1 (Reset Port) |
| Reward khi thành công | +10 |

#### ⚡ Phương Pháp Tiêm Lỗi (Fault Injection — Mininet)
```python
# Ngắt cổng kết nối NT-ACC02 → NT-CORE
net.get('NT_CORE').cmd('ip link set NT_CORE-eth2 down')
# Hoặc: Dùng tc netem để gây loss 100%
net.get('NT_CORE').cmd('tc qdisc add dev NT_CORE-eth2 root netem loss 100%')
```

---

### F02 — Distribution Failure (Sập Router Tầng Distribution — Kích Hoạt VRRP)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Chi nhánh Nha Trang — Router `NT-DIST01` (VRRP Master, phục vụ VLAN 110/120/130).
- **Hiện tượng:** Router Distribution Master bị sập hoàn toàn (nguồn điện, crash phần mềm).
- **Tác động:** Nhiều phòng ban (ADMIN, SALES, ACCOUNTING tại Nha Trang) mất Default Gateway. VRRP Virtual IP `10.20.x.1` tạm thời không phản hồi cho đến khi VRRP Backup tiếp quản.
- **Fault Domain:** Trung bình — ảnh hưởng nhiều VLAN nhưng chỉ trong 1 chi nhánh.

#### 🔍 Cơ Chế Phát Hiện (Detection)
```
Keepalived VRRP:
  NT-DIST01 ngừng gửi VRRP Advertisement (mỗi 1 giây)
  NT-DIST02 chờ hết Dead Interval (3s) → Chuyển lên MASTER

Prometheus ghi nhận:
  vrrp_state{host="NT_DIST01", vrid="1"} = 0  ← DIST01 DOWN
  vrrp_state{host="NT_DIST02", vrid="1"} = 1  ← DIST02 lên MASTER

FRR Syslog (OSPF):
  "OSPF neighbor DOWN: NT-DIST01 is unreachable"
```

#### 🧠 Phân Tích Nguyên Nhân Gốc Rễ (RCA)
```
RCA Engine:
  Input:  vrrp_state{host="NT_DIST01"} = 0
          ospf_neighbor_state{router="NT_CORE", neighbor="NT_DIST01"} = 0
  
  Phân tích:
    NT-DIST01 DOWN
      ├─► VRRP Master mất → VIP 10.20.x.1 tạm thời không phản hồi
      ├─► VLAN 110 (ADMIN), 120 (SALES), 130 (ACCOUNTING) mất Gateway
      └─► OSPF loại bỏ NT-DIST01 khỏi topology

  Kết luận RCA: "NT-DIST01 CRASH → VRRP Failover to NT-DIST02 → OSPF Reconverge"
  Confidence Score: 95%
```

#### 🔄 Luồng Tự Phục Hồi (Recovery Flow)
```
Giai đoạn 1 — VRRP Failover (Tự động, không cần AI can thiệp):
  NT-DIST01 stop VRRP Advertisement
      ↓
  NT-DIST02 dead timer hết (3s) → Transition: BACKUP → MASTER
      ↓
  NT-DIST02 quảng bá Gratuitous ARP:
    "VIP 10.20.x.1 now at MAC of NT-DIST02"
      ↓
  Tất cả host cập nhật ARP cache → Lưu lượng chuyển qua NT-DIST02
  ⏱️ Thời gian: < 3-5 giây

Giai đoạn 2 — OSPF Reconvergence (Tự động):
  FRR OSPF loại bỏ route qua NT-DIST01
      ↓
  Tính toán Dijkstra SPF → Route mới qua NT-DIST02
      ↓
  Cập nhật Forwarding Information Base (FIB)
  ⏱️ Thời gian: < 30 giây

Giai đoạn 3 — SDN Controller cập nhật Flow Rules:
  Faucet Controller nhận thông báo OSPF topology change
      ↓
  Cài đặt lại Flow Rules phù hợp cho traffic qua NT-DIST02
  ⏱️ Thời gian: < 5 giây
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR (VRRP Failover) | < 5 giây |
| MTTR (OSPF Converge) | < 30 giây |
| Cơ chế chính | VRRP Failover + OSPF Reconvergence |
| PPO Action | Theo dõi + cập nhật flow (hỗ trợ) |
| Fault Domain | 3 VLAN (nhiều phòng ban 1 chi nhánh) |

#### ⚡ Phương Pháp Tiêm Lỗi
```python
# Sập hoàn toàn NT-DIST01
net.get('NT_DIST01').cmd('ifconfig NT_DIST01-eth0 down')
net.get('NT_DIST01').cmd('service keepalived stop')
net.get('NT_DIST01').cmd('service frr stop')
```

---

### F03 — OSPF Link Failure (Đứt Liên Kết L3 Giữa Chi Nhánh)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Liên kết WAN L3 giữa `BL-GW` (Bảo Lộc) và `HCM-GW` (HCM).
- **Hiện tượng:** Đường kết nối OSPF trực tiếp Bảo Lộc — HCM bị ngắt (đứt cáp WAN nhánh phụ). Hai router mất OSPF Neighbor relationship.
- **Tác động:** Traffic từ Bảo Lộc → HCM không còn đường trực tiếp. Phải đi vòng qua Nha Trang hoặc Data Center.
- **Đặc điểm:** Mạng không bị ngắt hoàn toàn (có đường thay thế), nhưng bandwidth và latency tăng lên.

#### 🔍 Cơ Chế Phát Hiện (Detection)
```
FRR Syslog trên BL-GW:
  "OSPF Neighbor DOWN: 10.0.0.2 (HCM-GW) — Dead timer expired"

Prometheus ghi nhận:
  ospf_neighbor_state{router="BL_GW", neighbor="HCM_GW"} = 0
  ospf_neighbor_state{router="HCM_GW", neighbor="BL_GW"} = 0

Anomaly Detection:
  Latency BL → HCM tăng từ 20ms → 60ms (đường vòng)
  Bandwidth BL → HCM giảm (path dài hơn qua NT)
```

#### 🧠 Phân Tích Nguyên Nhân Gốc Rễ (RCA)
```
RCA Engine:
  Input:  ospf_neighbor_state{router="BL_GW", neighbor="HCM_GW"} = 0
  
  Phân tích chuỗi phụ thuộc:
    Link BL-GW ↔ HCM-GW DOWN
      ├─► OSPF route [BL → HCM direct] bị xóa
      └─► Traffic BL → HCM phải đi qua NT-GW (latency +40ms)
      
  Proactive trigger thêm:
    AI ghi nhận: "Bandwidth giảm → preemptive traffic steering"
    
  Kết luận: "OSPF Link BL↔HCM DOWN → Reroute via NT"
  Confidence Score: 96%
```

#### 🔄 Luồng Tự Phục Hồi (Recovery Flow)
```
Bước 1 — OSPF Tự Động Reconverge:
  BL-GW và HCM-GW chạy Dead Timer hết (40s mặc định)
      ↓
  Mỗi router tính toán lại SPF (Dijkstra):
    BL-GW tìm đường mới: BL-GW → NT-GW → HCM-GW
      ↓
  Cập nhật bảng định tuyến (Routing Table)
  ⏱️ Thời gian OSPF: 30-40 giây

Bước 2 — AI Proactive Optimization:
  RCA Engine phát hiện: "Đường mới dài hơn, bandwidth thấp hơn"
      ↓
  AI kích hoạt Traffic Steering chủ động:
    Bulk Data (Backup) → Chuyển sang đường Internet/VPN
    VoIP/ERP (nhạy cảm latency) → Giữ qua MPLS nếu còn BW
      ↓
  SD-WAN Controller cập nhật Policy
  ⏱️ Thời gian AI optimization: < 5 giây

Bước 3 — Verify:
  Prometheus: ospf_route{prefix="10.10.0.0/16"} → via NT_GW = 1
  Ping test BL → HCM: Success (latency ~60ms qua NT)
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR (OSPF Converge) | < 40 giây |
| MTTR (AI Optimization) | < 5 giây |
| Cơ chế chính | OSPF Reconvergence |
| Cơ chế phụ | SD-WAN Traffic Steering |
| Hậu quả chấp nhận được | Latency tăng ~40ms (đường vòng) |

#### ⚡ Phương Pháp Tiêm Lỗi
```bash
# Ngắt link vật lý giữa BL-GW và HCM-GW
ip link set BL_GW-eth1 down   # Trên BL-GW
ip link set HCM_GW-eth2 down  # Trên HCM-GW
```

---

### F04 — MPLS WAN Down (Đứt Đường WAN Chính MPLS)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Đường WAN MPLS kết nối `HCM-GW` → `DC-SP-GW` (Data Center).
- **Hiện tượng:** Kênh MPLS bị đứt hoàn toàn — mô phỏng đứt cáp quang biển hoặc sự cố nhà mạng ISP MPLS.
- **Tác động nghiêm trọng:** Đây là đường WAN ưu tiên nhất (delay 20ms, loss 0.1%). Toàn bộ VoIP và Database traffic đang chạy trên MPLS cần được chuyển ngay sang đường khác.
- **Đây là kịch bản WAN quan trọng nhất** của đề tài — thể hiện rõ nhất sức mạnh SD-WAN.

#### 🔍 Cơ Chế Phát Hiện (Detection)
```
SD-WAN Edge Probe (HCM-GW):
  3 lần gửi probe packets tới DC qua MPLS → Không nhận được reply
  Timeout sau: 3 × 1s = 3 giây

Prometheus ghi nhận:
  wan_path_status{site="HCM", transport="MPLS"} = 0
  wan_path_latency{transport="MPLS"} = NaN (No reply)
  wan_path_loss{transport="MPLS"} = 100%

Telemetry Anomaly:
  Latency VoIP tăng đột biến (MPLS đứt → gói bị drop)
  MOS Score VoIP: 4.2 → 1.0 (Không thể gọi)
```

#### 🧠 Phân Tích Nguyên Nhân Gốc Rễ (RCA)
```
RCA Engine:
  Input:  wan_path_status{transport="MPLS"} = 0
  
  Xác nhận MPLS DOWN (3 probe thất bại liên tiếp)
  
  Đánh giá đường thay thế:
  ┌─────────────┬──────────┬────────┬──────────┐
  │  Transport  │  Delay   │  Loss  │  Status  │
  ├─────────────┼──────────┼────────┼──────────┤
  │  MPLS       │  ——      │ 100%   │  DOWN    │
  │  5G         │  15 ms   │  0.3%  │  UP ✓    │
  │  Internet   │  40 ms   │  0.5%  │  UP ✓    │
  │  LTE        │  60 ms   │  1.0%  │  UP ✓    │
  │  VPN        │  50 ms   │  0.8%  │  UP ✓    │
  └─────────────┴──────────┴────────┴──────────┘
  
  Chọn đường tốt nhất: 5G (delay thấp nhất = 15ms)
  
  Kết luận: "MPLS DOWN → Failover to 5G (primary) + Internet (secondary)"
  Confidence Score: 99%
```

#### 🔄 Luồng Tự Phục Hồi (Recovery Flow)
```
Bước 1: SD-WAN Controller xác nhận MPLS DOWN
         wan_path_status{MPLS} = 0 (3 probe thất bại)
              ↓
Bước 2: SD-WAN Controller tính toán phân phối traffic mới:
    ┌─────────────────────────────────────────────────────┐
    │  Traffic Type  │  Đường cũ  │  Đường mới          │
    ├────────────────┼────────────┼─────────────────────┤
    │  VoIP/SIP      │  MPLS      │  5G (delay 15ms)    │
    │  Database/ERP  │  MPLS      │  5G (nếu BW đủ)     │
    │                │            │  hoặc Internet      │
    │  Web/HTTP      │  Internet  │  Giữ nguyên         │
    │  Bulk Backup   │  VPN       │  Giữ nguyên         │
    └─────────────────────────────────────────────────────┘
              ↓
Bước 3: Safety Layer kiểm tra:
         ✓ Confidence = 99% → PASS
         ✓ Blast Radius: Di chuyển traffic nhưng không ảnh hưởng user cuối
         → TỰ ĐỘNG THỰC THI
              ↓
Bước 4: SD-WAN Controller push config xuống HCM-GW:
         Cập nhật Policy Routing:
           ip route VoIP next-hop 5G_interface
           ip route DB next-hop 5G_interface
              ↓
Bước 5: Verify — Probe check:
         VoIP over 5G: Latency = 15ms, Loss = 0.3% → MOS = 4.0 ✓
         DB over 5G: RTT = 32ms → Application OK ✓
              ↓
⏱️ Tổng MTTR: < 5 giây
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR | < 5 giây |
| Cơ chế | SD-WAN Path Switching |
| Đường thay thế chính | 5G (15ms delay) |
| MOS VoIP sau phục hồi | ≥ 4.0 |
| Packet Loss sau phục hồi | < 1% |

#### ⚡ Phương Pháp Tiêm Lỗi
```python
# Gây mất gói 100% trên MPLS interface
net.get('HCM_GW').cmd('tc qdisc add dev HCM_GW-mpls root netem loss 100%')
# Hoặc ngắt hẳn interface
net.get('HCM_GW').cmd('ip link set HCM_GW-mpls down')
```

---

### F05 — Internet WAN Down (Mất Kênh Internet)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Kênh Internet WAN tại `HCM-GW`.
- **Hiện tượng:** Kênh Internet (100Mbps, delay 40ms) bị mất do ISP sự cố.
- **Tác động:** Toàn bộ traffic Web/Cloud/SaaS đang sử dụng kênh Internet bị gián đoạn. Cần chuyển sang đường WAN khác.

#### 🔍 Cơ Chế Phát Hiện
```
Prometheus:
  wan_path_status{site="HCM", transport="Internet"} = 0
  wan_path_loss{transport="Internet"} = 100%
```

#### 🔄 Luồng Tự Phục Hồi
```
SD-WAN Controller phát hiện Internet DOWN
    ↓
Đánh giá đường thay thế cho Web traffic:
  5G: delay 15ms, loss 0.3% → Tốt nhất còn lại cho Web
  LTE: delay 60ms, loss 1.0% → Dự phòng thứ 2
    ↓
Áp dụng policy mới:
  Web/HTTP traffic → 5G
  Cloud Sync → 5G hoặc LTE (phân chia tải)
    ↓
Verify: HTTP request to external URL → Response OK qua 5G
⏱️ MTTR: < 5 giây
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị |
|:---|:---:|
| MTTR | < 5 giây |
| Đường thay thế | 5G → LTE (theo thứ tự ưu tiên) |
| Lưu lượng ảnh hưởng | Web/HTTP/Cloud |

#### ⚡ Phương Pháp Tiêm Lỗi
```python
net.get('HCM_GW').cmd('tc qdisc add dev HCM_GW-inet root netem loss 100%')
```

---

### F06 — LTE Down (Mất Đường Di Động LTE Backup)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Đường LTE (30Mbps, delay 60ms) — đường dự phòng di động.
- **Hiện tượng:** Sóng LTE mất hoặc SIM card lỗi. Đường LTE không còn sử dụng được.
- **Tác động:** Đường này thường chỉ chứa traffic dự phòng mức thấp. Tác động ít nghiêm trọng hơn F04/F05.

#### 🔄 Luồng Tự Phục Hồi
```
SD-WAN Controller phát hiện LTE DOWN
    ↓
Đường 5G vẫn hoạt động tốt (200Mbps)
    ↓
Chuyển toàn bộ traffic đang qua LTE → 5G
    ↓
Nếu 5G không đủ BW: Phân phối sang Internet
⏱️ MTTR: < 5 giây
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị |
|:---|:---:|
| MTTR | < 5 giây |
| Đường thay thế | 5G (ưu tiên) |
| Fault Domain | Nhỏ — LTE chỉ là backup |

---

### F07 — 5G Degradation (Suy Giảm Chất Lượng Đường 5G)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Kênh 5G — đường nhanh nhất hệ thống (200Mbps, 15ms).
- **Hiện tượng:** Đường 5G bị nhiễu vô tuyến hoặc suy hao tín hiệu, **Packet Loss tăng vượt 5%** — không đứt hoàn toàn nhưng chất lượng không đáp ứng SLA.
- **Điểm đặc biệt:** Link 5G vẫn "UP" về mặt kỹ thuật nhưng chất lượng không đủ — kiểm tra chất lượng thực tế là quan trọng.

#### 🔍 Cơ Chế Phát Hiện
```
SD-WAN Probe:
  wan_path_loss{transport="5G"} = 6% > ngưỡng SLA (5%)
  wan_path_jitter{transport="5G"} = 25ms (tăng cao)
  
Anomaly Detection:
  5G chất lượng = DEGRADED (không phải DOWN)
  → Kích hoạt Quality-based Failover (không phải Link-down Failover)
```

#### 🔄 Luồng Tự Phục Hồi
```
SD-WAN Controller phát hiện 5G DEGRADED (loss > 5%)
    ↓
Đánh giá: Traffic đang qua 5G là gì?
  VoIP Business App → Nhạy cảm với loss
  Database/ERP → Cần reliability
    ↓
Chuyển traffic nhạy cảm:
  VoIP/DB → MPLS (delay 20ms, loss 0.1%) ← Tốt nhất còn lại
  Web traffic → Giữ 5G hoặc Internet (ít nhạy cảm hơn)
    ↓
Tiếp tục monitor 5G:
  Nếu loss về < 2%: Dần dần đưa traffic quay lại 5G
⏱️ MTTR: < 5 giây
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị |
|:---|:---:|
| Ngưỡng kích hoạt | Packet Loss > 5% |
| MTTR | < 5 giây |
| Loại Failover | Quality-based (không phải Link-down) |
| Đường thay thế | MPLS |

#### ⚡ Phương Pháp Tiêm Lỗi
```python
# Gây packet loss 6% trên đường 5G (vẫn còn link UP)
net.get('HCM_GW').cmd('tc qdisc change dev HCM_GW-5g root netem loss 6%')
```

---

### F08 — VPN Failure (Sập Kênh VPN Mã Hóa)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Kênh VPN (50Mbps, delay 50ms, mã hóa).
- **Hiện tượng:** Tunnel VPN bị sập do lỗi Certificate hết hạn, lỗi IKE negotiation, hoặc đứt kết nối VPN endpoint.
- **Tác động:** Traffic bảo mật (Backup mã hóa, dữ liệu nhạy cảm) đang chạy qua VPN bị ngắt. Cần chuyển sang đường bảo mật thay thế.

#### 🔄 Luồng Tự Phục Hồi
```
SD-WAN Controller phát hiện VPN tunnel DOWN
    ↓
Traffic đang qua VPN:
  Bulk Backup (encrypted) → Chuyển sang MPLS (reliability cao)
  Sensitive data → Giảm tốc, chờ VPN recover HOẶC sang MPLS
    ↓
Cảnh báo NOC: "VPN DOWN — Sensitive data may be rerouted via MPLS"
  (NOC có thể override nếu cần)
    ↓
SD-WAN attempt VPN re-negotiation tự động
    ↓
Verify: VPN tunnel UP → Đưa traffic bảo mật quay lại VPN
⏱️ MTTR: < 5 giây (cho traffic steering)
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị |
|:---|:---:|
| MTTR | < 5 giây |
| Cảnh báo NOC | Có (vì liên quan dữ liệu bảo mật) |
| Đường thay thế | MPLS |

---

### F09 — WAN Congestion (Tắc Nghẽn Băng Thông MPLS)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Kênh MPLS (100Mbps) đang bị tắc nghẽn cao — link vẫn UP nhưng quá tải.
- **Hiện tượng:** Utilization MPLS vượt **85%** (85Mbps/100Mbps). Jitter VoIP bắt đầu tăng mạnh.
- **Nguyên nhân điển hình:** Đồng thời có nhiều luồng Business Application + VoIP + Database chạy cùng một lúc vào giờ cao điểm.
- **Phân biệt với F04:** MPLS không đứt, chỉ tắc nghẽn → Cần Traffic Steering chứ không phải Failover hoàn toàn.

#### 🔍 Cơ Chế Phát Hiện
```
Prometheus ghi nhận:
  interface_utilization{link="HCM_MPLS"} = 88%  > ngưỡng 85%
  wan_path_jitter{transport="MPLS"} = 40ms  (tăng từ 5ms)
  wan_path_loss{transport="MPLS"} = 1.5%   (tăng từ 0.1%)

QoE Engine phát hiện:
  MOS_VoIP = 4.2 → 2.8  (dưới ngưỡng SLA 3.5!)
  
Anomaly Detection:
  "MPLS congestion detected — QoE violation imminent"
```

#### 🧠 Phân Tích Nguyên Nhân Gốc Rễ (RCA)
```
RCA Engine:
  Input:  utilization=88%, jitter=40ms, MOS=2.8
  
  Phân tích: Link chưa đứt → không phải Failover
  Nguyên nhân: Quá tải → cần phân tải (Traffic Steering)
  
  Phân loại traffic đang trên MPLS:
    VoIP: 20Mbps (ưu tiên cao — nhạy cảm với jitter)
    ERP/DB: 35Mbps (ưu tiên cao — cần reliability)
    File Transfer: 30Mbps (ưu tiên thấp — có thể chuyển)
  
  Quyết định: Chuyển File Transfer + Bulk data sang Internet/5G
               Giữ VoIP và ERP trên MPLS (với QoS priority tăng)
```

#### 🔄 Luồng Tự Phục Hồi (Recovery Flow)
```
Bước 1: Phát hiện Congestion (utilization > 85%)
              ↓
Bước 2: QoE Engine xác nhận MOS VoIP vi phạm SLA
              ↓
Bước 3: SD-WAN Controller tính toán Traffic Steering plan:
    ┌─────────────────────────────────────────────────────────┐
    │  Traffic         │  Từ       │  Sang     │  Lý do      │
    ├──────────────────┼───────────┼───────────┼─────────────┤
    │  File Transfer   │  MPLS     │  Internet │  Ít nhạy    │
    │  Bulk Backup     │  MPLS     │  VPN/5G   │  Cảm latency│
    │  VoIP            │  MPLS     │  Giữ lại  │  Ưu tiên    │
    │  ERP/DB          │  MPLS     │  Giữ lại  │  Critical   │
    └─────────────────────────────────────────────────────────┘
              ↓
Bước 4: Áp dụng QoS Priority trên MPLS:
    MPLS QoS Class: VoIP → DSCP EF (Expedited Forwarding)
                    ERP → DSCP AF31
                    Other → BE (Best Effort)
              ↓
Bước 5: Verify:
    interface_utilization{MPLS} = 55% (giảm xuống)
    MOS VoIP = 4.1 (khôi phục)
    Jitter = 8ms (bình thường)
⏱️ MTTR: < 10 giây
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR | < 10 giây |
| Utilization MPLS sau xử lý | < 70% |
| MOS VoIP sau xử lý | ≥ 3.5 (SLA) |
| Cơ chế | Traffic Steering + QoS Reprioritization |

---

### F10 — VoIP Quality Degradation (Suy Giảm Chất Lượng Thoại — QoE-driven)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** Luồng VoIP giữa IP Phone `NT-PHN01` (Nha Trang) và `DC-APP01` (SIP Server).
- **Hiện tượng:** Jitter trên đường MPLS tăng từ từ (không đột biến như F09), khiến điểm MOS thoại giảm dần.
- **Điểm đặc biệt:** Đây là kịch bản QoE-driven — không có sự cố vật lý nào rõ ràng, nhưng chất lượng trải nghiệm người dùng đang xấu đi.

#### 🔍 Cơ Chế Phát Hiện
```
QoE Regression Engine:
  Input: Latency=45ms, Jitter=35ms, Loss=0.8%
  
  Tính toán MOS (E-Model formula):
    R_factor = 93.2 - d_delay_impairment - I_eq_impairment
    MOS = 1 + 0.035R + 0.000007R(R-60)(100-R)
    
  MOS_VoIP = 3.2  (tiệm cận ngưỡng SLA = 3.5!)
  Trend: MOS đang giảm dần → Sắp vi phạm SLA

Cảnh báo:
  "VoIP QoE = 3.2/5.0 — SLA threshold 3.5 at risk"
  "Mid-session steering recommended"
```

#### 🔄 Luồng Tự Phục Hồi — Mid-Session Steering
```
Bước 1: QoE Engine phát hiện MOS = 3.2 (ngưỡng cảnh báo)
              ↓
Bước 2: SD-WAN Controller đánh giá đường thay thế cho VoIP:
    5G: Jitter = 3ms, Loss = 0.3% → MOS dự kiến = 4.3 ✓
              ↓
Bước 3: Thực hiện Mid-Session Flow Steering:
    Không reset cuộc gọi!
    Chuyển luồng RTP packets của phiên VoIP đang chạy
    từ MPLS interface → 5G interface
    
    Kỹ thuật: SD-WAN Flow Table update (per-flow steering)
    Cuộc gọi tiếp tục liên tục — người dùng không nghe thấy gì
              ↓
Bước 4: Verify sau 3 giây:
    wan_path_jitter{5G} = 3ms → MOS = 4.3 ✓
    Cuộc gọi vẫn kết nối → MTTR = 0 (user experience)
⏱️ MTTR (User-perceived): 0 giây (cuộc gọi không bị ngắt)
⏱️ MTTR (Technical): < 3 giây
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR (kỹ thuật) | < 3 giây |
| MOS trước steering | 3.2 (sắp vi phạm SLA) |
| MOS sau steering | ≥ 4.0 |
| Người dùng bị ảnh hưởng | 0 (Mid-session, không rớt cuộc gọi) |
| Cơ chế | QoE-driven Mid-Session Flow Steering |

---

### F11 — Web Server Crash (Sập Web Server Tại Data Center)

#### 📌 Mô Tả Sự Cố
- **Vị trí xảy ra:** `DC-WEB01` (10.100.10.11) — Web Server chính tại Data Center.
- **Hiện tượng:** Tiến trình Nginx/Apache trên `DC-WEB01` bị crash hoặc toàn bộ VM/Container bị sập.
- **Tác động:** Mọi HTTP request từ các chi nhánh tới địa chỉ Web Server VIP (`10.100.10.10`) bị trả về lỗi nếu HAProxy không xử lý kịp.
- **Cơ chế phục hồi:** HAProxy Load Balancer tự động phát hiện `WEB01 health check failed` → Loại WEB01 khỏi pool → Chuyển toàn bộ request sang `DC-WEB02`.

#### 🔍 Cơ Chế Phát Hiện
```
HAProxy Health Check (mỗi 2 giây):
  HTTP GET /health → DC-WEB01 (10.100.10.11)
  → Connection refused / Timeout (3 lần liên tiếp)
  → HAProxy: "Server WEB01 is DOWN"

Prometheus ghi nhận:
  haproxy_server_status{backend="web_pool", server="web01"} = 0
  http_requests_total{server="web01", status="5xx"} tăng đột biến
```

#### 🔄 Luồng Tự Phục Hồi
```
Bước 1: HAProxy health check phát hiện WEB01 DOWN (3 lần fail)
              ↓
Bước 2: HAProxy tự động loại WEB01 khỏi backend pool:
    Backend web_pool:
      server web01 10.100.10.11:80  → STATUS: DOWN (marked)
      server web02 10.100.10.12:80  → STATUS: UP  (active)
              ↓
Bước 3: Tất cả HTTP request mới → DC-WEB02 (10.100.10.12)
    VIP 10.100.10.10 vẫn hoạt động bình thường
              ↓
Bước 4: AI Engine ghi nhận:
    Prometheus: haproxy_server_status{server="web02"} = 1
    Thông báo NOC: "WEB01 DOWN — Serving from WEB02 only"
              ↓
Bước 5: Verify:
    HTTP GET http://10.100.10.10/ → 200 OK (từ WEB02)
    Response time: < 50ms
⏱️ MTTR: < 5 giây (HAProxy failover gần như tức thì)
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR | < 5 giây |
| Cơ chế | HAProxy Active/Passive Load Balancing |
| Session Persistence | Giữ (sticky session nếu cấu hình) |
| Ảnh hưởng user | < 5s downtime (trong thời gian health check) |

#### ⚡ Phương Pháp Tiêm Lỗi
```bash
# Crash Nginx trên WEB01
docker exec DC-WEB01 killall nginx
# Hoặc dừng hoàn toàn container
docker stop DC-WEB01
```

---

### F12 — Multi-Metric Anomaly (Lỗi Đa Chỉ Số Phức Tạp — Chuỗi Sự Cố)

#### 📌 Mô Tả Sự Cố
- **Đây là kịch bản phức tạp nhất** trong bộ test — mô phỏng thực tế sự cố cascading (sự cố dây chuyền).
- **Kịch bản cụ thể:** Đồng thời xảy ra:
  1. `HCM-DIST01` báo CPU overload (>90%) — OpenFlow bị chậm
  2. Đường 5G bị degradation (Loss = 4%)
  3. VoIP MOS trên MPLS giảm xuống 3.3 (do jitter tăng nhẹ)
  4. Database connection từ HCM về DC bắt đầu timeout (RTT tăng)
- **Thách thức:** AI phải xác định được sự cố gốc và thứ tự ưu tiên xử lý, tránh can thiệp sai gây đổ vỡ thêm.

#### 🔍 Cơ Chế Phát Hiện
```
Prometheus ghi nhận đồng thời:
  faucet_controller_cpu{host="HCM_DIST01"} = 93%
  wan_path_loss{transport="5G"} = 4%
  voip_mos_score{site="HCM"} = 3.3  < SLA (3.5)
  db_connection_rtt{target="DC_DB01"} = 180ms > ngưỡng (100ms)

AI Anomaly Detection:
  Multi-dimensional anomaly detected!
  Correlation analysis:
    CPU overload → OpenFlow slowdown → Flow Table staleness
    Flow Table staleness → DB packets mis-routed → RTT tăng
    Conclusion: Root cause = CPU overload on HCM-DIST01
```

#### 🔄 Luồng Tự Phục Hồi — Chuỗi Tự Động
```
Bước 1 — RCA xác định Root Cause:
    HCM-DIST01 CPU 93% → Root cause #1 (nguyên phát)
    5G Loss 4% → Hiện tượng độc lập (không liên quan)
    VoIP MOS 3.3 → Hậu quả từ Flow Table staleness
    DB RTT 180ms → Hậu quả từ Flow Table staleness
              ↓
Bước 2 — Lập kế hoạch Recovery Chain:
    Ưu tiên 1: Xử lý CPU overload trên HCM-DIST01
    Ưu tiên 2: Xử lý 5G degradation (độc lập)
    Ưu tiên 3: Verify VoIP và DB sau khi CPU ổn định
              ↓
Bước 3 — Thực thi đồng thời (Safety Layer cho phép):
    [A] PPO Agent → a_t=2 (Restart switch/controller process)
        Faucet reload controller process trên HCM-DIST01
        CPU drop về 40% → Flow Table refresh
        
    [B] SD-WAN Controller:
        5G loss 4% < ngưỡng 5% → Chưa cần Failover
        Tăng cường monitoring 5G
              ↓
Bước 4 — Verify từng bước:
    [A] CPU HCM-DIST01 = 40% → PASS
        DB RTT = 35ms → PASS (tự phục hồi sau Flow Table refresh)
        VoIP MOS = 4.0 → PASS (tự phục hồi)
    [B] 5G Loss = 4% → Monitor tiếp (chưa cần action)
              ↓
Bước 5 — Đóng vòng lặp:
    AI ghi nhận toàn bộ vào Decision Log
    NOC Dashboard hiển thị: "Multi-metric incident RESOLVED"
⏱️ MTTR: < 60 giây (do phức tạp multi-step)
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR | < 60 giây |
| RCA Accuracy | Xác định đúng Root Cause gốc rễ |
| Recovery Chain | Đúng thứ tự ưu tiên |
| False Positive | 0 (không can thiệp nhầm) |
| Cơ chế | AI Multi-step Recovery Chain |

---

## 🟡 NHÓM SỰ CỐ DỰ BÁO CHỦ ĐỘNG (PROACTIVE SCENARIOS — P1 & P2)

---

### P1 — Preemptive Traffic Steering (Dự Báo Tắc Nghẽn Do Lịch Backup Tự Động)

#### 📌 Mô Tả Kịch Bản
- **Bản chất:** Đây là kịch bản **Proactive** — hệ thống hành động TRƯỚC khi sự cố xảy ra.
- **Tình huống:** Vào lúc **02:00:00**, tiến trình Backup tự động từ HCM về Data Center khởi chạy theo lịch định kỳ. Lưu lượng đột ngột tăng vọt 300% trên kênh MPLS.
- **Vấn đề nếu không có AI:** MPLS bị tắc nghẽn → VoIP cuộc gọi bị rớt → ERP/DB bị timeout.
- **Mục tiêu hệ thống:** Phát hiện và xử lý TRƯỚC 02:00:00 → MTTR = 0 giây (người dùng không cảm nhận gì).

#### 📈 Cơ Chế Dự Báo (Holt-Winters / LSTM)
```
Dữ liệu input (Prometheus, mỗi 5 giây):
  01:59:30  bytes_sent{MPLS} = 32 Mbps  (30% utilization)
  01:59:35  bytes_sent{MPLS} = 35 Mbps
  01:59:40  bytes_sent{MPLS} = 42 Mbps  ← Bắt đầu tăng
  01:59:45  bytes_sent{MPLS} = 55 Mbps  ← Tốc độ tăng: +13 Mbps/5s

Holt-Winters Calculation:
  Tính: d(Traffic)/dt = (55 - 42) / 5s = 2.6 Mbps/s
  
  Dự báo tại t+15s (02:00:00):
    Traffic_predict = 55 + 2.6 × 15 = 94 Mbps ≈ 94% utilization
    → MPLS sẽ tắc nghẽn hoàn toàn!

Kết quả dự báo (01:59:45):
  "CẢNH BÁO: MPLS sẽ đạt 94% sau 15 giây nữa!"
  "Khuyến nghị: Preemptive traffic steering ngay bây giờ"
```

#### 🔄 Luồng Xử Lý Chủ Động
```
01:59:45 — Holt-Winters phát hiện Traffic spike sắp xảy ra
              ↓
01:59:46 — Proactive Engine kích hoạt Recovery Plan:
    Phân loại traffic sắp tới:
      Backup data (HCM → DC): ~50 Mbps → Bulk, không nhạy cảm latency
      VoIP ongoing: ~20 Mbps → Nhạy cảm latency/jitter
      ERP/DB: ~15 Mbps → Cần reliability
              ↓
01:59:47 — SD-WAN Controller thực thi TRƯỚC sự tắc nghẽn:
    Backup traffic → Chuyển ngay sang Internet (100Mbps, rộng rãi)
    VoIP traffic → Giữ MPLS (BW vừa giải phóng, chất lượng tốt)
    ERP/DB → Giữ MPLS
              ↓
01:59:48 — Verify:
    bytes_sent{MPLS} = 38 Mbps (35% utilization)
    bytes_sent{Internet} = 52 Mbps (52% — OK)
              ↓
02:00:00 — Backup khởi chạy:
    MPLS utilization: 40% (bình thường — Backup đã trên Internet)
    VoIP MOS: 4.2 (tốt)
    Người dùng: KHÔNG CẢM NHẬN BẤT KỲ SỰ CHẬM NÀO
              ↓
⏱️ MTTR = 0 giây (không có downtime)
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR (User-perceived) | **0 giây** |
| Thời gian dự báo trước | 15 giây |
| MPLS Utilization sau xử lý | < 50% |
| VoIP MOS trong suốt thời gian | ≥ 4.0 |
| Cơ chế | Holt-Winters Time-Series Forecast |
| Baseline so sánh | Mạng truyền thống: MTTR > 120s (sau khi tắc nghẽn xảy ra) |

#### ⚡ Phương Pháp Kiểm Chứng (Validation)
```bash
# Kịch bản: Khởi chạy Bulk Transfer lúc 02:00
at 02:00 << EOF
  iperf3 -c 10.100.30.11 -b 80M -t 120 &  # Simulate backup
EOF

# Theo dõi:
watch -n 1 "curl -s prometheus:9090/api/v1/query?query=bytes_sent"
# Kỳ vọng: MPLS utilization KHÔNG vượt quá 60% trong suốt quá trình backup
```

---

### P2 — Mid-Session QoE Protection (Bảo Vệ Chất Lượng Cuộc Gọi Giữa Phiên)

#### 📌 Mô Tả Kịch Bản
- **Bản chất:** Kịch bản **Proactive** theo hướng QoE — hành động khi chất lượng đang xấu đi, TRƯỚC khi SLA bị vi phạm.
- **Tình huống:** Cuộc họp VoIP đang diễn ra giữa phòng họp HCM và Nha Trang. Đường MPLS đang bị ISP congestion nhẹ từ phía nhà mạng — Jitter tăng từ từ từ 5ms lên 40ms trong vòng 2 phút.
- **Vấn đề nếu không có AI:** MOS tiếp tục giảm → Cuộc gọi bị rè tiếng → Họp bị gián đoạn.
- **Mục tiêu:** Chuyển luồng VoIP sang đường tốt hơn TRONG KHI cuộc gọi vẫn đang diễn ra.

#### 📈 Cơ Chế Dự Báo QoE (Regression Engine)
```
QoE Regression Model (Linear Regression / Decision Tree):
  Input: Latency, Jitter, Packet Loss → Output: MOS Score (1.0 - 5.0)

  Công thức E-Model (ITU-T G.107):
    R = 93.2 - delay_impairment - equipment_impairment
    MOS = f(R)

Timeline của sự suy giảm:
  T+0:00  Jitter=5ms,  Loss=0.1%  → MOS=4.2  (Tốt — đang họp bình thường)
  T+0:30  Jitter=12ms, Loss=0.3%  → MOS=3.9  (Còn OK)
  T+1:00  Jitter=22ms, Loss=0.6%  → MOS=3.6  (Gần ngưỡng SLA 3.5)
  T+1:30  Jitter=35ms, Loss=1.0%  → MOS=3.2  ← CẢNH BÁO! (Dưới SLA)
  T+2:00  Jitter=45ms, Loss=1.5%  → MOS=2.8  ← Giọng nói bị vỡ tiếng

QoE Engine kích hoạt tại T+1:30 (MOS = 3.2):
  "QoE = 3.2/5.0 — SLA threshold (3.5) will be breached in ~15s"
  "Mid-session steering required"
```

#### 🔄 Luồng Mid-Session Steering
```
T+1:30 — QoE Engine phát hiện MOS = 3.2 (Cảnh báo)
              ↓
T+1:31 — SD-WAN Controller đánh giá đường thay thế:
    5G:      Jitter=3ms,  Loss=0.3%  → MOS_predict=4.3 ✓
    Internet: Jitter=8ms, Loss=0.5%  → MOS_predict=3.9 ✓
    → Chọn: 5G (tốt nhất)
              ↓
T+1:32 — Thực hiện Mid-Session Flow Steering:
    KHÔNG reset SIP session (cuộc gọi không bị cắt!)
    Kỹ thuật: SD-WAN per-flow routing update
      Flow ID: SIP/RTP session {src=HCM-PHN, dst=DC-APP01}
      Next-hop: MPLS_interface → 5G_interface
    
    Cơ chế kỹ thuật:
      SD-WAN Edge cập nhật forwarding entry
      Gói RTP tiếp theo được gửi qua 5G
      Không có re-invite SIP (seamless handover)
              ↓
T+1:33 — Cuộc gọi tiếp tục qua 5G:
    Jitter = 3ms, Loss = 0.3% → MOS = 4.3
    Người dùng: Tiếp tục nghe và nói bình thường
              ↓
T+1:35 — Verify:
    voip_mos_score = 4.3 → PASS (SLA compliant)
    voip_session_active = 1 → PASS (không bị rớt cuộc gọi)

⏱️ MTTR (User-perceived): 0 giây
⏱️ MTTR (Technical): < 3 giây
```

#### 📊 KPI Mục Tiêu
| Chỉ số | Giá trị mục tiêu |
|:---|:---:|
| MTTR (User-perceived) | **0 giây** (cuộc gọi không bị ngắt) |
| MOS khi kích hoạt | 3.2 (trước khi vi phạm SLA 3.5) |
| MOS sau steering | ≥ 4.0 |
| Session Drop Rate | 0% |
| Cơ chế | QoE Regression + Mid-Session Flow Steering |
| Baseline so sánh | Mạng truyền thống: Cuộc gọi rớt, phải gọi lại thủ công |

---

## BẢNG SO SÁNH TỔNG HỢP MTTR: TRUYỀN THỐNG vs SELF-HEALING

| ID | Sự Cố | MTTR Truyền Thống | MTTR Self-Healing | Cải Thiện |
|:---:|:---|:---:|:---:|:---:|
| F01 | Access Link Failure | 15-30 phút (thủ công SSH) | < 30 giây | **60x** |
| F02 | Distribution Failure | 5-10 phút | < 5 giây | **60-120x** |
| F03 | OSPF Link Failure | 2-5 phút | < 40 giây | **3-7x** |
| F04 | MPLS WAN Down | 10-30 phút | < 5 giây | **120-360x** |
| F05 | Internet Down | 10-20 phút | < 5 giây | **120-240x** |
| F06 | LTE Down | 5-15 phút | < 5 giây | **60-180x** |
| F07 | 5G Degradation | Không phát hiện được | < 5 giây | **∞** |
| F08 | VPN Failure | 15-30 phút | < 5 giây | **180-360x** |
| F09 | WAN Congestion | 30-60 phút | < 10 giây | **180-360x** |
| F10 | VoIP Degradation | Không phát hiện được | < 3 giây | **∞** |
| F11 | Web Server Crash | 5-15 phút | < 5 giây | **60-180x** |
| F12 | Multi-Metric Anomaly | Không xử lý được | < 60 giây | **∞** |
| P1 | Traffic Spike (Proactive) | Xảy ra sự cố (MTTR>120s) | **0 giây** | **∞** |
| P2 | QoE Degradation (Proactive) | Cuộc gọi rớt (>5 phút) | **0 giây** | **∞** |

---

## GHI CHÚ KỸ THUẬT TRIỂN KHAI

### Môi Trường Mô Phỏng
- **Platform:** Mininet + Open vSwitch (OVS) + FRR (FRRouting)
- **WAN Simulation:** `tc netem` để mô phỏng 5 đường WAN (delay, loss, jitter, bandwidth)
- **Monitoring:** Prometheus + Grafana + Custom OVS Exporters
- **AI Engine:** Python 3.10+ với `stable-baselines3` (PPO), `statsmodels` (Holt-Winters), `scikit-learn` (QoE Regression)
- **Controllers:** Faucet (SDN/LAN) + Custom Python SD-WAN Controller (WAN)
- **Dashboard:** Flask + SocketIO (NOC real-time)

### Quy Trình Chạy Test
```
1. Khởi động môi trường Mininet topology
2. Khởi động Faucet SDN Controller
3. Khởi động SD-WAN Controller (Python)
4. Khởi động AI Engine (Anomaly Detection + PPO Agent + Proactive Engine)
5. Khởi động Prometheus + Grafana
6. Mở NOC Dashboard (Flask:5050)
7. Tiêm lỗi theo từng kịch bản Fx / Px
8. Ghi nhận: Thời gian phát hiện, MTTR thực tế, MOS score, Confidence Score
9. So sánh với mạng truyền thống (không có AI)
```

---

*Tài liệu được tổng hợp từ: `chot_y_tuong.md`, `cau_truc_tu_phuc_hoi_sdwan.md`, `noi_dung_slide_thuyet_trinh.md`*  
*Cập nhật: 2026-10-04*
