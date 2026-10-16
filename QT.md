# **ROADMAP TRIỂN KHAI MẠNG DOANH NGHIỆP TỰ PHỤC HỒI**
**Kiến trúc cuối cùng**
```text
                               ┌─────────────────────────────┐
                               │  NOC WEB DASHBOARD (UI)     │
                               │  (Flask + SocketIO :5050)   │
                               └──────────────┬──────────────┘
                                              │ WebSocket Broadcast
                               ┌──────────────┴──────────────┐
                               │      AI FAULT-RECOVERY      │
                               │ Telemetry Collector         │
                               │ Anomaly Detection           │
                               │ Root Cause Analysis         │
                               │ Recovery Decision Engine    │
                               └──────────────┬──────────────┘
                                              │
                            ┌─────────────────┴─────────────────┐
                            │                                   │
```
SDN Controller                     SD-WAN Controller
```text
                           │                                   │
                     ──────┴────────────── ENTERPRISE ─────────┴──────
                           │                                   │
                 ┌─────────┼─────────┐                ┌───────┴───────┐
                 │         │         │                │               │
```
Bảo Lộc  Nha Trang    HCM             MPLS         Internet
```text
               Flat      3-Tier     3-Tier            │               │
                 │         │         │             ┌──┴──┐        ┌───┴───┐
                 │         │         │             │     │        │       │
                 └─────────┴─────────┴─────────────┘     │      VPN      │
                                                         │               │
                                                       LTE              5G
                                                         │               │
                                                         └───────┬───────┘
                                                                 │
                                                           DATA CENTER
                                                           Spine / Leaf
                                                                 │
                                                        WEB / APP / DB
```

## **PHASE 0 — Chuẩn hóa môi trường**
### **Mục tiêu**
Tạo môi trường mô phỏng có thể tái lập.
### **Thành phần**
Ubuntu 20.04 / 22.04
```text
├── Mininet 2.3+
├── Open vSwitch 2.13+
├── Python 3.9+
├── iproute2 (tc netem)
├── iperf3
├── tcpdump
├── Wireshark
└── Git
SDN Controller:
└── Ryu SDN Framework
SD-WAN Controller:
└── Python module tự viết (src/controller/sdwan/)
AI:
Python
├── NumPy
├── Pandas
├── Scikit-learn
└── Flask (REST API)
```
### **Kiểm tra**
sudo mn --test pingall
### **Checkpoint:**
Mininet chạy ổn định và topology mẫu có thể khởi tạo/xóa/rebuild tự động.

## **PHASE 1 — Xây dựng Enterprise Topology**
Đây là phase đầu tiên thực sự của mạng.
**Bảo Lộc**
BL
```text
│
└── BL-SW
    ├── ADMIN
    ├── SALES
    ├── ACCOUNTING
    ├── IT
    ├── IoT
    ├── CCTV
    └── WIFI
Nha Trang
                    NT-CORE
                   /       \
              DIST01       DIST02
              / | \         / | \
           ACC01 ACC02 ACC03 ACC04 ...
HCM
                    HCM-CORE
                   /        \
              DIST01        DIST02
             / |  \        / |  \
           ACC01 ACC02 ... ACC06
Data Center
                SPINE01          SPINE02
                / |  \           / |  \
               /  |   \         /  |   \
           LEAF01 LEAF02     LEAF03 LEAF04
               │      │          │      │
               └──────┴──────────┴──────┘
                         │
                    Servers
```
### **Checkpoint**
Topology created
```text
      ↓
All nodes reachable at L2
```

## **PHASE 2 — VLAN + IP Addressing**
**Bảo Lộc**

| VLAN | Mạng |
| --- | --- |
| 10 USER | 10.10.10.0/24 |
| 30 IoT | 10.10.30.0/24 |
| 35 CCTV | 10.10.35.0/24 |
| 50 WIFI | 10.10.50.0/24 |
| 99 MGMT | 10.10.99.0/24 |

**Nha Trang**
110 ADMIN
120 SALES
130 ACCOUNTING
140 HR
150 CUSTOMER
160 IT
170 IoT
175 CCTV
180 WIFI
190 VOICE
199 MGMT
Network:
10.20.x.0/24
**HCM**
210 ADMIN
220 SALES
230 ACCOUNTING
240 HR
250 MARKETING
260 CUSTOMER
270 TECHNICAL
280 IT
290 IoT
295 CCTV
296 WIFI
297 VOICE
299 MGMT
Network:
10.30.x.0/24
**Data Center**
310 WEB
320 APP
330 DB
340 INFRA
350 MONITORING
360 MGMT
Network:
10.100.x.0/24
### **Checkpoint**
Kiểm tra:
Host → Host cùng VLAN
và:
VLAN isolation

## **PHASE 3 — L2 Switching + RSTP**
### Cấu hình:
Access port
Trunk
VLAN
RSTP
Root bridge
STP priority
### Ví dụ:
CORE
```text
 │
 ├──── DIST01
 │       │
 │       └── ACC
 │
 └──── DIST02
         │
         └── ACC
Tạo redundancy.
Fault test
DIST01 ── X ── CORE
```
Kiểm tra RSTP convergence.
### **Checkpoint**
Khi một link L2 bị lỗi, topology không bị loop và kết nối được khôi phục.

## **PHASE 4 — L3 Routing + OSPF**
Triển khai:
Inter-VLAN Routing
```text
        +
OSPF
Ví dụ:
HCM-DIST01
HCM-DIST02
HCM-CORE
OSPF:
Area 0
Các site:
BL ─── HCM ─── DC ─── NT
```
### **Kiểm tra**
show ip route
show ip ospf neighbor
### **Fault**
```text
CORE ── X ── DIST
OSPF phải hội tụ lại.
```

## **PHASE 5 — Gateway Redundancy với VRRP**
Ví dụ Nha Trang:
DIST01
10.20.10.2

DIST02
10.20.10.3

Virtual Gateway
10.20.10.1
PC
```text
 │
 ▼
```
10.20.10.1
```text
 │
 ├── DIST01
 └── DIST02
Nếu DIST01 chết:
DIST01 DOWN
     ↓
DIST02 MASTER
     ↓
Gateway vẫn 10.20.10.1
```
### **Checkpoint**
Gateway vẫn hoạt động khi một thiết bị Distribution bị lỗi.

## **PHASE 6 — DHCP + DNS + NTP**
**DHCP**
Server:
DC-DHCP01
10.100.40.12
Các VLAN dùng DHCP Relay.
### Ví dụ:
HCM-SALES
10.30.20.0/24
Pool:
10.30.20.100 - 10.30.20.200

**DNS**
DC-DNS01
10.100.40.11
Records:
www.enterprise.local
app.enterprise.local
db.enterprise.local
sip.enterprise.local
monitor.enterprise.local

**NTP**
DC-MGMT01
```text
     │
 ┌───┼────┐
 BL  NT   HCM
```
### **Checkpoint**
Một PC mới:
DHCP
```text
 ↓
IP
 ↓
DNS
 ↓
NTP
hoạt động hoàn chỉnh.
```

## **PHASE 7 — ACL + Firewall + Segmentation**
**ACL**
### Ví dụ:
USER → WEB       ALLOW
WEB → APP        ALLOW
APP → DB         ALLOW

CCTV → DB        DENY
IoT → USER       DENY

**Firewall**
Internet:
INTERNET
```text
    │
 FIREWALL
    │
 SD-WAN
Data Center:
SD-WAN
   │
DC FIREWALL
   │
 ├── DMZ
 │    └── WEB
 │
 └── INTERNAL
      ├── APP
      └── DB
```
### **Checkpoint**
Security policy hoạt động đúng.

## **PHASE 8 — Data Center Services**
10 server:
WEB01
WEB02

APP01
APP02

DB01
DB02

DNS01
DHCP01

MON01
MGMT01
**Load Balancing**
VIP
```text
               │
            HAProxy
            /     \
         WEB01   WEB02
Nếu WEB01 chết:
WEB01 DOWN
   ↓
HAProxy
   ↓
WEB02
```
### **Checkpoint**
Service vẫn hoạt động khi một Web Server lỗi.

## **PHASE 9 — WAN Transport Emulation (100% Mininet)**
Thay vì GNS3, mọi WAN transport được mô phỏng bằng **OvS path riêng + tc netem** ngay trong Mininet.

**Mô hình 5 transport path (Branch ↔ DC):**
```text
           ┌──────────────────────────────────┐
           │  MPLS     delay=20ms  loss=0.1%  │
           ├──────────────────────────────────┤
           │  Internet  delay=40ms  loss=0.5%  │
           ├──────────────────────────────────┤
           │  LTE       delay=60ms  loss=1.0%  │
           ├──────────────────────────────────┤
           │  5G        delay=15ms  loss=0.3%  │
           ├──────────────────────────────────┤
           │  VPN       delay=50ms  loss=0.8%  │
           └──────────────────────────────────┘
```

| Transport | Bandwidth | Delay | Loss | Ghi chú |
| --- | --- | --- | --- | --- |
| MPLS | 100 Mbps | 20 ms | 0.1% | Ưu tiên VoIP/ERP |
| Internet | 100 Mbps | 40 ms | 0.5% | Web/Cloud |
| LTE | 30 Mbps | 60 ms | 1.0% | Backup di động |
| 5G | 200 Mbps | 15 ms | 0.3% | Tốc độ cao |
| VPN | 50 Mbps | 50 ms | 0.8% | Backup mã hóa |

**Fault injection WAN đơn giản:**
```bash
# Tắt hoàn toàn MPLS path
tc qdisc del dev mpls-link root
# Suy giảm dần (ISP degrade)
tc qdisc change dev internet-link root netem delay 150ms loss 5%
```

**Đây chỉ là giá trị baseline ban đầu**, điều chỉnh để tạo các scenario DOWN/DEGRADED/CONGESTED khác nhau cho AI học và kiểm thử.

## **PHASE 10 — SD-WAN**
SD-WAN Edge tại từng site:
SD-WAN EDGE
```text
                     │
       ┌─────────────┼─────────────┐
       │             │             │
      MPLS       INTERNET        LTE
       │             │             │
       └─────────────┼─────────────┘
                     │
                    5G
                     │
                    VPN
Controller duy trì trạng thái:
Path
Latency
Jitter
Loss
Bandwidth
Availability
Policy ban đầu
Voice      → MPLS
Database   → MPLS
Business   → 5G
Web        → Internet
Backup     → VPN/Internet
Fault
MPLS DOWN
   ↓
SD-WAN Controller
   ↓
Select 5G / Internet
   ↓
Traffic continues
```

## **PHASE 11 — QoS + VoIP**
Voice VLAN:
NT VLAN 190
HCM VLAN 297
Asterisk:
DC
```text
 │
 └── SIP Server
Traffic:
SIP
RTP
QoS:
RTP
 ↓
DSCP EF
 ↓
Priority Queue
Test
Tạo congestion:
iperf3
 ↓
WAN saturation
Đo:
Latency
Jitter
Packet Loss
Throughput
```

## **PHASE 12 — Monitoring + Telemetry**
Đây là **nguồn dữ liệu của AI**.
Thu thập:
CPU
Memory
Interface utilization
Link status
Latency
Jitter
Packet loss
Throughput
Queue drops
OSPF state
STP state
VRRP state
WAN path state
### Nguồn:
SNMP
OpenFlow
ICMP
iperf3
Syslog
Flow statistics
### Pipeline:
Network
```text
   ↓
Telemetry Collector
   ↓
Time-series data & Logs
   ↓
AI Engine ───(SocketIO Broadcast)───> NOC Dashboard (UI)
```

## **PHASE 12B — NOC Dashboard (Trung tâm Giám sát Tập trung)**
Đây là **giao diện điều hành & giám sát toàn bộ hệ thống** (SDN, SD-WAN, AI Engine) theo thời gian thực (Real-time Operations Center).

### **Thành phần & Công nghệ (src/noc/):**
- **Backend:** Flask + Flask-SocketIO (`src/noc/backend/app.py`, port 5050)
- **Frontend:** HTML5, CSS3 (Dark Theme Dashboard), JavaScript ES6 (`src/noc/frontend/`)
- **Thư viện trực quan hóa (Visualization):**
  - **Chart.js:** Biểu đồ hiển thị Metric thời gian thực (Latency, Loss, Throughput, CPU/RAM utilization)
  - **vis-network:** Sơ đồ Topology tương tác (tự động đổi màu Node/Link khi xảy ra sự cố hoặc tự phục hồi)
- **Luồng dữ liệu Real-time:** Telemetry Collector → AI Engine → Flask-SocketIO (WebSocket Broadcast) → Client Browser

### **Các Panel chức năng chính:**
1. **Topology Interactive Map:** Hiển thị sơ đồ 3 Site (BL, NT, HCM), WAN Links (MPLS, Internet, LTE, 5G, VPN) và Data Center. Node/Link chuyển màu Red (Fault), Yellow (Congested), Green (Healthy).
2. **WAN Path Status Panel:** Trạng thái latency, jitter, loss và RTT từng đường WAN thời gian thực.
3. **Telemetry & Metrics Charts:** Biểu đồ dòng dữ liệu real-time với tùy chỉnh khung thời gian (1m, 5m, 15m).
4. **AI Decision & Alert Log:** Bảng nhật ký thời gian thực ghi lại: Anomaly Detect → RCA (Root Cause) → Action executed (Ryu Flow install / SD-WAN Route switch).
5. **Recovery History & MTTR:** Thống kê thời gian tự phục hồi MTTR (Mean Time To Recovery), tỷ lệ thành công của hệ thống.

### **Chạy NOC Dashboard:**
```bash
python3 src/noc/backend/app.py
# Truy cập: http://localhost:5050
```

### **Checkpoint**
NOC Dashboard mở thành công trên trình duyệt, kết nối WebSocket ổn định, nhận dữ liệu telemetry và phản ánh chính xác trạng thái mạng khi tiến hành Fault Injection.

## **PHASE 13 — Event Correlation**
Kết hợp:
Telemetry
```text
+
Syslog
+
Topology
+
Routing
+
Flow
Ví dụ:
10:00:01 Interface utilization ↑
10:00:02 Packet loss ↑
10:00:03 OSPF neighbor DOWN
10:00:04 Route changed
```
AI nhìn toàn bộ chuỗi này thay vì chỉ nhìn một metric.

## **PHASE 14 — SDN Controller**
SDN Controller điều khiển LAN.
SDN Controller
```text
                    │
                 OpenFlow
                    │
       ┌────────────┼────────────┐
       │            │            │
     HCM SW       NT SW       BL SW
Chức năng:
Flow installation
Flow modification
Flow deletion
Path selection
QoS policy
Ví dụ:
Host A
 ↓
Path 1
bị lỗi:
AI
 ↓
SDN Controller
 ↓
Install Path 2
```

## **PHASE 15 — AI Anomaly Detection**
### Input:
Latency
Jitter
Loss
Throughput
CPU
Memory
Queue
Link state
Model ban đầu:
**Isolation Forest**
### Pipeline:
Telemetry
```text
    ↓
Feature Engineering
    ↓
Normalization
    ↓
Anomaly Detection
    ↓
Anomaly Score
Ví dụ:
Normal = 0.1
Normal = 0.2
Normal = 0.3
Anomaly = 0.94
```

## **PHASE 16 — AI Root Cause Analysis**
AI phải xác định:
**Nguyên nhân nào gây anomaly?**
### Ví dụ:
Latency ↑
Loss ↑
Jitter ↑
Interface utilization = 98%
```text
        ↓
RCA
        ↓
WAN congestion
Hoặc:
10 hosts mất kết nối
        ↓
Tất cả cùng Access Switch
        ↓
Switch link DOWN
        ↓
RCA = Access link failure
```

## **PHASE 17 — Recovery Decision Engine**
AI quyết định hành động.
### Ví dụ:
**LAN**
Link Failure
```text
     ↓
Alternative path available?
     ↓
YES
     ↓
SDN Controller
     ↓
Install alternate flow
WAN
MPLS degraded
      ↓
5G healthy?
      ↓
YES
      ↓
SD-WAN Controller
      ↓
Steer traffic to 5G
QoS
Voice degradation
      ↓
Increase QoS priority
      +
Change WAN path
```

## **PHASE 18 — AI → Controller**
Đây là **điểm nhấn kiến trúc của luận văn**.
AI
```text
                     │
              Recovery Decision
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
   SDN Controller        SD-WAN Controller
          │                     │
       OpenFlow              Policy/API
          │                     │
          ▼                     ▼
         LAN                    WAN
```
AI **không trực tiếp cấu hình switch/router**.
Controller mới là lớp thực thi.

## **PHASE 19 — Fault Injection**
Đây là nơi bắt đầu thực nghiệm.
**F1 — Link failure**
Link DOWN
**F2 — Switch failure**
Switch DOWN
**F3 — OSPF failure**
Neighbor DOWN
**F4 — MPLS failure**
MPLS DOWN
**F5 — Internet failure**
Internet DOWN
**F6 — LTE failure**
LTE DOWN
**F7 — 5G failure**
5G DOWN
**F8 — VPN failure**
VPN DOWN
**F9 — WAN degradation**
Delay ↑
Loss ↑
Jitter ↑
**F10 — Congestion**
Bandwidth saturation
**F11 — VoIP degradation**
Jitter ↑
Packet loss ↑
Latency ↑
**F12 — Server failure**
WEB01 DOWN

## **PHASE 20 — Self-Healing Loop**
Đây là **vòng lặp trung tâm của luận văn**.
```text
                 ┌──────────────────┐
                 │     NETWORK      │
                 └────────┬─────────┘
                          │
                       Telemetry
                          │
                          ▼
                 ┌──────────────────┐
                 │      DETECT      │
                 └────────┬─────────┘
                          │
                       Anomaly
                          │
                          ▼
                 ┌──────────────────┐
                 │       RCA        │
                 └────────┬─────────┘
                          │
                       Root Cause
                          │
                          ▼
                 ┌──────────────────┐
                 │     DECISION     │
                 └────────┬─────────┘
                          │
                 Recovery Action
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
```
SDN Controller            SD-WAN Controller
```text
             │                         │
             ▼                         ▼
           LAN                       WAN
             │                         │
             └────────────┬────────────┘
                          │
                       Recovery
                          │
                          ▼
                    New Telemetry
                          │
                          └───────────────► VERIFY
```

## **PHASE 21 — Đánh giá**
Mỗi scenario phải đo:
**Detection Time**
Fault → AI Detection
**RCA Time**
Detection → Root Cause
**Decision Time**
RCA → Recovery decision
**Recovery Time**
Decision → Service restored
**MTTR**
MTTR =
Fault → Service restored
Ngoài ra đo:
Packet Loss
Latency
Jitter
Throughput
Availability
QoS

**Bộ test case cuối cùng**
Mình khuyên bạn cuối cùng có khoảng **10–12 scenario**:

| ID | Sự cố | Controller | Recovery |
| --- | --- | --- | --- |
| F01 | Access link failure | SDN | Alternate path |
| F02 | Distribution failure | SDN | VRRP/OSPF |
| F03 | OSPF link failure | SDN | Route reconvergence |
| F04 | MPLS down | SD-WAN | Internet |
| F05 | Internet down | SD-WAN | MPLS/5G |
| F06 | LTE down | SD-WAN | 5G/MPLS |
| F07 | 5G degradation | SD-WAN | MPLS |
| F08 | VPN failure | SD-WAN | Other transport |
| F09 | WAN congestion | SD-WAN | Traffic steering |
| F10 | VoIP degradation | SD-WAN + QoS | QoS/path change |
| F11 | WEB server failure | Load Balancer | WEB02 |
| F12 | Multi-metric anomaly | AI | Automated recovery |

**Thứ tự thực hiện thực tế**
Đừng bắt đầu từ AI. Hãy làm đúng thứ tự này:
## 01. Mininet
```text
       ↓
```
## 02. Topology
```text
       ↓
```
## 03. VLAN + IP
```text
       ↓
```
## 04. RSTP
```text
       ↓
```
## 05. OSPF
```text
       ↓
```
## 06. VRRP
```text
       ↓
```
## 07. DHCP + DNS + NTP
```text
       ↓
```
## 08. ACL + Firewall
```text
       ↓
```
## 09. Data Center
```text
       ↓
```
## 10. Load Balancing
```text
       ↓
```
11. 5 WAN transports
```text
       ↓
```
## 12. SD-WAN
```text
       ↓
```
## 13. QoS + VoIP
```text
       ↓
```
## 14. Monitoring
```text
       ↓
```
## 15. Telemetry
```text
       ↓
```
## 15B. NOC Dashboard (Flask + SocketIO Web UI)
```text
       ↓
```
## 16. Syslog + Event Correlation
```text
       ↓
```
## 17. SDN Controller
```text
       ↓
```
## 18. AI Detection
```text
       ↓
```
## 19. AI RCA
```text
       ↓
```
## 20. AI Decision
```text
       ↓
```
## 21. Controller Automation
```text
       ↓
```
## 22. Fault Injection
```text
       ↓
```
## 23. Evaluation
```text
Một điểm mình đặc biệt khuyên chốt: **5 đường MPLS | Internet | LTE | 5G | VPN đặt hoàn toàn trong Mininet thuần** dưới dạng 5 OvS path riêng với đặc tính `tc netem` khác nhau. Đây không phải 5 mạng vật lý mà là 5 transport path trên cùng một hạ tầng — giống hệt cách SD-WAN thực tế hoạt động. SD-WAN Controller tự viết (src/controller/sdwan/) được xem là **đóng góp khoa học của luận văn** — thông minh hơn việc dùng tool thương mại sẵn có.
```
