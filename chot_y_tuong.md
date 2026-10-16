# CHỐT Ý TƯỞNG - MẠNG DOANH NGHIỆP TỰ PHỤC HỒI
## Self-Healing Enterprise Network using SD-WAN & Intelligent Failure Recovery

> Tài liệu này chốt toàn bộ kiến trúc, vai trò từng thành phần, và cơ chế tự phục hồi của đề tài KLTN.  
> Đây là **nguồn tham chiếu chính thức** cho thiết kế và triển khai.

---

## PHẦN 1: CẤU TRÚC TỔNG THỂ TOPOLOGY

### 1.1 Kiến trúc tổng quan

Hệ thống mô phỏng một **doanh nghiệp đa chi nhánh thực tế** với 3 chi nhánh + 1 Data Center, kết nối qua mạng WAN đa đường.

```
                        ┌─────────────────────────────────────────────────────┐
                        │              AI SELF-HEALING ENGINE                 │
                        │   Telemetry → Anomaly Detection → RCA → Decision    │
                        └──────────────────────┬──────────────────────────────┘
                                               │
                              ┌────────────────┴────────────────┐
                              │     Global Network Orchestrator  │
                              └────────────┬────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                              │
           ┌────────┴────────┐                        ┌───────────┴──────────┐
           │  SDN Controller  │                        │  SD-WAN Controller   │
           │  (Faucet/Ryu)   │                        │  (Python tự viết)    │
           │   Quản lý LAN   │                        │   Quản lý WAN        │
           └────────┬────────┘                        └───────────┬──────────┘
                    │                                              │
         ┌──────────┴──────────────────────────────────┐         │
         │              LAN DOMAIN                      │         │
         │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │         │
         │  │ Bảo Lộc  │  │Nha Trang │  │   HCM    │  │         │
         │  │  (Flat)  │  │ (3-Tier) │  │ (3-Tier) │  │         │
         │  └────┬─────┘  └────┬─────┘  └────┬─────┘  │         │
         └───────┼─────────────┼──────────────┼────────┘         │
                 └─────────────┼──────────────┘                   │
                               │                                   │
                          WAN DOMAIN ◄────────────────────────────┘
                    ┌──────────┴──────────────────┐
                    │  5 Transport Paths (Phase 9) │
                    │  MPLS / Internet / LTE / 5G / VPN │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │     DATA CENTER      │
                    │   Spine-Leaf Fabric  │
                    │  WEB / APP / DB /    │
                    │  DNS / DHCP / NTP    │
                    └─────────────────────┘
```

---

### 1.2 Chi nhánh Bảo Lộc — Flat Network

**Đặc điểm:** Chi nhánh nhỏ nhất, dùng mạng phẳng (không phân cấp).

```
                          BL-GW (Gateway Router)
                               │
                           BL-SW (OVS Switch - L2)
                        /    |    |    \
                     ADMIN  SALES  ACC   IT
                     VLAN10  VLAN10 VLAN10 VLAN10
                      │      │      │     │
                   3 PC   3 PC   3 PC  3 PC
                     
                     + IoT (VLAN30): BL-PRN01, BL-PRN02
                     + CCTV (VLAN35): BL-CAM01, BL-CAM02
                     + WiFi (VLAN50): BL-AP01
```

| VLAN | Tên | Subnet | Gateway |
| --- | --- | --- | --- |
| 10 | USER | 10.10.10.0/24 | 10.10.10.1 |
| 30 | IoT | 10.10.30.0/24 | 10.10.30.1 |
| 35 | CCTV | 10.10.35.0/24 | 10.10.35.1 |
| 50 | WiFi | 10.10.50.0/24 | 10.10.50.1 |
| 99 | MGMT | 10.10.99.0/24 | 10.10.99.1 |

**Vai trò trong đề tài:** Baseline đơn giản nhất để so sánh và test fault scenario F01 (Access Link Failure) không có VRRP fallback.

---

### 1.3 Chi nhánh Nha Trang — 3-Tier Hierarchy

**Đặc điểm:** Chi nhánh vừa, dùng kiến trúc 3 tầng chuẩn enterprise.

```
                              NT-CORE (OVS - Root Bridge)
                             /                           \
                      NT-DIST01                       NT-DIST02
                   (Host Router)                   (Host Router)
                   VRRP Master                     VRRP Backup
                   /    |    \                    /    |    \
                ACC01 ACC02 ACC03             ACC04 ACC05 ACC06

    Phân bố Access Switch:
    NT-ACC01 → ADMIN    (VLAN 110, 10.20.10.0/24)
    NT-ACC02 → SALES    (VLAN 120, 10.20.20.0/24)
    NT-ACC03 → ACCOUNTING (VLAN 130, 10.20.30.0/24)
    NT-ACC04 → HR       (VLAN 140, 10.20.40.0/24)
    NT-ACC05 → CUSTOMER (VLAN 150, 10.20.50.0/24)
    NT-ACC06 → IT + IoT/CCTV/WiFi/Voice
```

**VLANs:** 110, 120, 130, 140, 150, 160 (IT), 170 (IoT), 175 (CCTV), 180 (WiFi), 190 (Voice), 199 (MGMT)  
**Subnet:** 10.20.x.0/24, Gateway: 10.20.x.1 (VRRP VIP)  
**Tổng host:** 26 endpoint (18 PC + 2 Printer + 3 Camera + 1 AP + 2 IP Phone)

**Fault domain điển hình:**
- `NT-ACC02 DOWN` → chỉ phòng Kinh Doanh bị ảnh hưởng (fault domain rõ ràng)
- `NT-DIST01 DOWN` → nhiều phòng ban bị ảnh hưởng → VRRP failover sang DIST02

---

### 1.4 Chi nhánh HCM — 3-Tier Hierarchy (lớn nhất)

**Đặc điểm:** Chi nhánh lớn nhất, 8 phòng ban, là môi trường test chính cho WAN scenarios.

```
                            HCM-CORE (OVS - Root Bridge)
                           /                              \
                    HCM-DIST01                        HCM-DIST02
                  (Host Router)                     (Host Router)
                  VRRP Master                       VRRP Backup
                 /    |    \                       /    |    \
              ACC01 ACC02 ACC03               ACC04 ACC05 ACC06

    Phân bố:
    HCM-ACC01 → ADMIN + SALES
    HCM-ACC02 → ACCOUNTING + HR
    HCM-ACC03 → MARKETING + CUSTOMER
    HCM-ACC04 → TECHNICAL + IT
    HCM-ACC05 → IoT + CCTV + WiFi
    HCM-ACC06 → Voice (VLAN 297)
```

**VLANs:** 210–299 (ADMIN, SALES, ACCOUNTING, HR, MARKETING, CUSTOMER, TECHNICAL, IT, IoT, CCTV, WiFi, Voice, MGMT)  
**Subnet:** 10.30.x.0/24, Gateway: 10.30.x.1 (VRRP VIP)  
**Tổng host:** 35 endpoint (24 PC + 3 Printer + 4 Camera + 2 AP + 2 IP Phone)

---

### 1.5 Data Center — Spine-Leaf Fabric

**Đặc điểm:** Cung cấp tất cả dịch vụ tập trung, kết nối với tất cả các site qua WAN.

```
                    DC-SP-GW (WAN Gateway Router)
                          │
                  DC-SPINE01 ─────────── DC-SPINE02
                  (Root STP, Priority 4096)
                 /    |    \            /    |    \
             LEAF01 LEAF02 LEAF03  LEAF03 LEAF04 LEAF04
                                    (shared)
                              │
                        10 Servers:
```

| Server | IP | VLAN | Vai trò |
| --- | --- | --- | --- |
| DC-WEB01 | 10.100.10.11 | 310 | Web server (behind HAProxy VIP) |
| DC-WEB02 | 10.100.10.12 | 310 | Web server backup |
| DC-APP01 | 10.100.20.11 | 320 | Application server + SIP (VoIP) |
| DC-APP02 | 10.100.20.12 | 320 | Application server backup |
| DC-DB01 | 10.100.30.11 | 330 | Database primary |
| DC-DB02 | 10.100.30.12 | 330 | Database backup |
| DC-DNS01 | 10.100.40.11 | 340 | DNS server |
| DC-DHCP01 | 10.100.40.12 | 340 | DHCP server (relay target) |
| DC-MON01 | 10.100.50.11 | 350 | Monitoring (Prometheus) |
| DC-MGMT01 | 10.100.60.11 | 360 | NTP + Management |

---

### 1.6 WAN Connectivity — 5 Transport Paths (Phase 9+)

Mỗi chi nhánh kết nối với Data Center qua **5 đường WAN song song**, mô phỏng bằng OVS path riêng + `tc netem`:

| Transport | Bandwidth | Delay | Loss | Ưu tiên |
| --- | --- | --- | --- | --- |
| **MPLS** | 100 Mbps | 20 ms | 0.1% | VoIP/ERP (cao nhất) |
| **Internet** | 100 Mbps | 40 ms | 0.5% | Web/Cloud |
| **LTE** | 30 Mbps | 60 ms | 1.0% | Backup di động |
| **5G** | 200 Mbps | 15 ms | 0.3% | Tốc độ cao |
| **VPN** | 50 Mbps | 50 ms | 0.8% | Backup mã hoá |

**Chính sách định tuyến ban đầu (SD-WAN Policy):**
- Voice/VoIP → MPLS (ưu tiên độ trễ thấp, jitter thấp)
- Database → MPLS (ưu tiên reliability)
- Business App → 5G (hiệu năng cao)
- Web/Cloud → Internet (giá rẻ)
- Backup/Sync → VPN hoặc Internet

---

### 1.7 Tổng bảng host

| Site | PC | Printer | Camera | AP | IP Phone | Server | Tổng |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bảo Lộc | 12 | 2 | 2 | 1 | 0 | 0 | 17 |
| Nha Trang | 18 | 2 | 3 | 1 | 2 | 0 | 26 |
| HCM | 24 | 3 | 4 | 2 | 2 | 0 | 35 |
| Data Center | 0 | 0 | 0 | 0 | 0 | 10 | 10 |
| **Tổng** | **54** | **7** | **9** | **4** | **4** | **10** | **88** |

---

## PHẦN 2: VAI TRÒ CỦA SDN VÀ SD-WAN

### 2.1 SDN — Điều khiển miền LAN

**SDN (Software-Defined Networking)** tách biệt Control Plane khỏi Data Plane. Thay vì mỗi switch tự quyết định chuyển gói, **SDN Controller** có cái nhìn toàn cục và cài đặt luật chuyển tiếp (Flow Rules) xuống từng switch qua **OpenFlow**.

```
                    SDN Controller (Faucet/Ryu)
                           │
                        OpenFlow
                           │
          ┌────────────────┼────────────────┐
          │                │                │
      NT-CORE          HCM-CORE          BL-SW
    (OVS Switch)      (OVS Switch)    (OVS Switch)
          │                │
      DIST01/02        DIST01/02
          │                │
        ACC01-06         ACC01-06
```

**SDN Controller làm được gì trong đề tài này?**

| Tình huống | Hành động SDN Controller |
| --- | --- |
| Access link failure (F01) | Cài Flow Rule mới, chuyển traffic sang path backup |
| Distribution failure (F02) | Phối hợp với VRRP, cập nhật routing table L3 |
| OSPF link failure (F03) | Trigger OSPF reconvergence, cập nhật forwarding table |
| Flow Table lỗi trên Switch | Xóa flow rules hỏng (OFPFC_DELETE), inject lại rules sạch |
| Switch mất kết nối với Controller | Re-handshake datapath, khôi phục kết nối OpenFlow |
| Port bị ngắt | Gửi `OFPPC_PORT_DOWN` → `OFPPC_PORT_UP` để reset port |

**Triết lý SDN trong đề tài:**
> SDN Controller là **"bộ não điều khiển LAN"**. AI không trực tiếp cấu hình switch — AI ra **Recovery Intent**, SDN Controller thực thi.

---

### 2.2 SD-WAN — Điều khiển miền WAN

**SD-WAN (Software-Defined Wide Area Network)** áp dụng triết lý SDN cho mạng WAN. Thay vì WAN cứng nhắc theo topology vật lý, SD-WAN Controller chọn đường tốt nhất dựa trên **chính sách + trạng thái thời gian thực**.

```
                    SD-WAN Controller (Python tự viết)
                           │
                     Policy / API
                           │
              ┌────────────┼────────────────┐
              │            │                │
          BL-GW         NT-GW           HCM-GW
       (SD-WAN Edge) (SD-WAN Edge)   (SD-WAN Edge)
              │            │                │
         ┌────┴─────┐      ...             ...
         │ MPLS     │
         │ Internet │  ← 5 transport paths
         │ LTE      │     per site
         │ 5G       │
         │ VPN      │
         └──────────┘
```

**SD-WAN Controller làm được gì trong đề tài này?**

| Tình huống | Hành động SD-WAN Controller |
| --- | --- |
| MPLS down (F04) | Chuyển tất cả traffic sang Internet + 5G |
| Internet down (F05) | Chuyển sang MPLS/5G theo priority |
| WAN degradation (F09) | Traffic steering: chuyển VoIP sang đường ít jitter hơn |
| VoIP quality degradation (F10) | Kết hợp SD-WAN path change + QoS priority tăng |
| Dự báo congestion (Proactive) | Chuyển trước traffic bulk sang đường phụ TRƯỚC khi tắc |
| QoE Score giảm dưới SLA | Mid-session steering: chuyển flow đang chạy sang kênh mới |

**Triết lý SD-WAN trong đề tài:**
> SD-WAN Controller là **"bộ não điều khiển WAN"**. Không chỉ phản ứng khi đường bị đứt, mà còn **chủ động tối ưu hóa** chất lượng trải nghiệm (QoE) liên tục.

---

### 2.3 Sự khác biệt then chốt giữa SDN và SD-WAN trong đề tài

| | SDN Controller | SD-WAN Controller |
| --- | --- | --- |
| **Phạm vi** | LAN (trong từng site) | WAN (giữa các site) |
| **Giao thức điều khiển** | OpenFlow (Faucet/Ryu) | REST API / Python tự viết |
| **Đối tượng điều khiển** | OVS Switch, Flow Table, Port, VLAN | Edge Router, WAN Path, Traffic Policy |
| **Loại sự cố xử lý** | Access link, Switch crash, Flow error, Port down | MPLS down, WAN congestion, QoE degradation |
| **Cơ chế phục hồi** | Flow reinstall, Port reset, Path reroute (LAN) | Path switching, Traffic steering, QoS adjustment |
| **Thời gian phục hồi** | 20-30s (OpenFlow convergence) | < 5s (SD-WAN policy push) |

---

## PHẦN 3: CƠ CHẾ TỰ PHỤC HỒI — HƯỚNG TỚI DỰ ĐOÁN VÀ TỰ ĐỘNG

### 3.1 Kiến trúc vòng lặp Self-Healing (Closed-Loop)

```
        ┌─────────────────────────────────────────────────┐
        │                                                 │
        ▼                                                 │
  [NETWORK STATE]                                    [VERIFY]
        │                                                 │
     Telemetry                                     New Telemetry
        │                                                 │
        ▼                                                 │
  [DETECT - Anomaly Detection]                           │
        │                                                 │
     Anomaly Found?                                       │
        │                                                 │
        ▼                                                 │
  [ANALYZE - Root Cause Analysis]                        │
        │                                                 │
     Root Cause Identified                               │
        │                                                 │
        ▼                                                 │
  [DECIDE - Recovery Decision Engine]                    │
        │                                                 │
     Recovery Intent                                     │
        │                                                 │
        ▼                                                 │
  [POLICY / SAFETY CHECK]                               │
        │                                                 │
     Approved?                                            │
     /       \                                           │
   YES        NO                                        │
    │          │                                         │
    ▼          ▼                                         │
[EXECUTE]   [Alert Human]                               │
    │                                                    │
    ├──── SDN Controller ──→ LAN Recovery               │
    │                                                    │
    └──── SD-WAN Controller → WAN Recovery ─────────────┘
```

---

### 3.2 Các loại sự cố và cách phục hồi

#### 🔴 F01 — Access Link Failure (Sự cố liên kết Access)

**Mô tả:** NT-ACC02 (SALES switch) bị ngắt kết nối.

**Phát hiện:**
- Prometheus ghi nhận: `of_port_status{dp="NT_CORE", port="ACC02_port"} = 0`
- Telemetry: Latency tăng đột biến cho VLAN 120 traffic

**RCA:** AI xác định: "NT-ACC02 down → SALES department affected → Fault domain: NT-SALES"

**Phục hồi:**
```
PPO Agent → a_t = 1 (Reset Port)
           ↓
SDN Controller (Faucet)
           ↓
OpenFlow PORT_MOD: OFPPC_PORT_DOWN → OFPPC_PORT_UP
           ↓
Kết hợp RSTP: traffic tự động reroute qua đường dự phòng
           ↓
Recovery trong 20-30s
```

---

#### 🔴 F02 — Distribution Failure (Sự cố tầng Distribution)

**Mô tả:** NT-DIST01 (VRRP Master) bị sập.

**Phát hiện:**
- Keepalived: VRRP Master advertisement ngừng
- Prometheus: `vrrp_state{host="NT_DIST01"} = 0`

**RCA:** AI xác định: "NT-DIST01 down → Multiple VLANs affected → VRRP failover needed"

**Phục hồi:**
```
VRRP (tự động): NT-DIST02 nhận Master role sau 3s
           ↓
VIP 10.20.x.1 vẫn hoạt động
           ↓
OSPF reconverge: traffic reroute qua NT-DIST02
           ↓
SDN Controller: cập nhật Flow Rules nếu cần
           ↓
Recovery trong < 5s (VRRP) + < 30s (OSPF)
```

---

#### 🔴 F03 — OSPF Link Failure (Sự cố liên kết WAN nội bộ)

**Mô tả:** Link giữa BL-GW và HCM-GW bị đứt.

**Phát hiện:**
- FRR syslog: "OSPF neighbor DOWN"
- Prometheus: `ospf_neighbor_state{router="BL_GW", neighbor="HCM_GW"} = 0`

**Phục hồi:**
```
OSPF tự động: tìm đường thay thế qua topolog
           ↓
Route BL → HCM đi qua NT hoặc DC
           ↓
Recovery trong 30-40s (OSPF convergence)
           ↓
AI ghi nhận: giảm bandwidth do path dài hơn → preemptive traffic steering
```

---

#### 🔴 F04 — MPLS Down (Sự cố WAN chính)

**Mô tả:** Kênh MPLS (đường WAN chính, ưu tiên nhất) bị đứt.

**Phát hiện:**
- SD-WAN Edge: probe packets MPLS không nhận được reply
- Prometheus: `wan_path_status{site="HCM", transport="MPLS"} = 0`

**Phục hồi:**
```
SD-WAN Controller:
1. Xác nhận MPLS DOWN (3 lần probe thất bại liên tiếp)
2. Tính toán path thay thế: 5G (delay 15ms, loss 0.3%) → tốt nhất
3. Áp dụng chính sách mới:
   - VoIP → 5G
   - Database → 5G (nếu BW đủ) hoặc Internet
   - Web → Internet
4. Gửi config update xuống HCM-GW
           ↓
Recovery trong < 5s
```

---

#### 🔴 F09 — WAN Congestion (Tắc nghẽn WAN)

**Mô tả:** MPLS link bắt đầu tắc nghẽn (utilization > 85%).

**Phát hiện:**
- Prometheus: `interface_utilization{link="HCM_MPLS"} = 88%`
- VoIP jitter tăng từ 5ms → 40ms

**Phục hồi (Reactive):**
```
QoE Engine: MOS VoIP giảm 4.2 → 2.8 (dưới SLA 3.5)
           ↓
SD-WAN Controller: mid-session steering
           ↓
VoIP flows → MPLS (nếu còn BW) HOẶC 5G
Bulk data flows → Internet hoặc VPN
           ↓
MPLS utilization giảm → VoIP MOS hồi phục
```

---

#### 🟡 P1 — Proactive: Dự báo traffic spike (Phòng ngừa chủ động)

**Kịch bản:** Lịch backup tự động lúc 02:00 sẽ làm traffic MPLS tăng vọt.

**Cơ chế dự báo:**
```
Holt-Winters / LSTM (nhẹ):
- Input: bytes_sent từ Prometheus, cập nhật mỗi 5s
- Tính: d(Traffic)/dt (tốc độ tăng)
- Dự báo: "MPLS sẽ đạt 92% trong 15 giây tới"
           ↓
SD-WAN Controller: preemptive steering
           ↓
VoIP/Video flows chuyển trước sang 5G/Broadband
TRƯỚC KHI MPLS tắc nghẽn hoàn toàn
           ↓
User không nhận ra bất kỳ sự gián đoạn nào
```

---

#### 🟡 P2 — Proactive: QoE degradation warning (Cảnh báo suy giảm chất lượng)

**Kịch bản:** Jitter MPLS bắt đầu tăng từ từ (5ms → 20ms) do ISP congestion.

**Cơ chế QoE:**
```
QoE Regression Model (Linear Regression / Decision Tree):
- Input: Latency, Jitter, Packet Loss, App sensitivity
- Output: QoE Score (1.0 - 5.0)

QoE_VoIP = 4.2 → 3.8 → 3.2 (tiệm cận SLA threshold 3.5)
           ↓
Cảnh báo: "QoE sắp vi phạm SLA"
           ↓
Mid-session steering: chuyển VoIP sang WAN2 (5G/Internet)
khi QoE = 3.2, TRƯỚC KHI vi phạm SLA (< 3.0)
           ↓
Cuộc gọi VoIP tiếp tục mượt mà, user không bị rớt cuộc gọi
```

---

### 3.3 PPO Reinforcement Learning Agent — Bộ não ra quyết định

**PPO (Proximal Policy Optimization)** là thuật toán học tăng cường được dùng cho Reactive Self-Healing:

**Vector trạng thái 8 chiều** (input của agent):
```
s_t = [C_cpu, C_res_mem, C_virt_mem, f_sent, f_err, f_conn, f_disc, P_down]^T

C_cpu       = CPU utilization của Controller
C_res_mem   = Memory (resident)
C_virt_mem  = Memory (virtual)
f_sent      = Flow packets sent
f_err       = Flow error count
f_conn      = Controller connections
f_disc      = Controller disconnections
P_down      = Số cổng bị ngắt
```

**4 hành động (output):**
| a_t | Hành động | Khi nào |
| --- | --- | --- |
| 0 | No-op (giữ nguyên) | Mạng ổn định |
| 1 | Reset port | P_down > 0 |
| 2 | Restart Switch/Controller | f_disc > 0 hoặc CPU > 90% |
| 3 | Bespoke self-heal (xóa + inject flow) | f_err > 0 |

**Hệ thống phần thưởng:**
```
Phục hồi thành công:  +10 (port reset), +15 (flow restore), +20 (datapath recover)
Can thiệp không cần thiết: -5 (false alarm)
Không hành động khi cần: -10 (missed fault)
Duy trì ổn định:      +1 (mỗi bước no-op khi mạng OK)
```

---

### 3.4 Hệ thống phòng vệ — Policy/Safety Layer

Trước khi AI ra lệnh thực thi, mọi quyết định phải qua lớp kiểm tra an toàn:

```
AI Decision
     ↓
┌─────────────────────────────────┐
│       POLICY / SAFETY LAYER     │
│                                 │
│ ✓ Policy Validation             │
│ ✓ Risk Assessment               │
│ ✓ AI Confidence Check           │
│ ✓ Blast Radius Estimation       │
│ ✓ Rollback Policy Check         │
└────────────────┬────────────────┘
                 │
         Confidence ≥ 80% AND Risk = LOW?
          /                     \
        YES                      NO
         │                        │
         ▼                        ▼
   Auto Execute             Alert Human
```

**Ví dụ:**
- `Confidence=97%, Risk=Low, Action=Switch WAN Path` → **Tự động thực thi**
- `Confidence=58%, Risk=High, Action=Modify Core Routing` → **Yêu cầu Human Approval**

---

### 3.5 Bộ 12 Test Scenarios tự phục hồi

| ID | Sự cố | Controller | Cơ chế phục hồi | MTTR mục tiêu |
| --- | --- | --- | --- | --- |
| F01 | Access link failure | SDN | RSTP + Alternate Flow | < 30s |
| F02 | Distribution failure (VRRP) | SDN | VRRP Failover + OSPF | < 5s |
| F03 | OSPF link failure | SDN | OSPF Reconvergence | < 40s |
| F04 | MPLS down | SD-WAN | Switch to 5G/Internet | < 5s |
| F05 | Internet down | SD-WAN | Switch to MPLS/5G | < 5s |
| F06 | LTE down | SD-WAN | Switch to 5G/MPLS | < 5s |
| F07 | 5G degradation | SD-WAN | Switch to MPLS | < 5s |
| F08 | VPN failure | SD-WAN | Switch to other transport | < 5s |
| F09 | WAN congestion | SD-WAN | Traffic steering + QoS | < 10s |
| F10 | VoIP degradation | SD-WAN + QoS | QoE-driven path change | < 3s |
| F11 | WEB server failure | Load Balancer | HAProxy → WEB02 | < 5s |
| F12 | Multi-metric anomaly | AI | Automated Recovery Chain | < 60s |
| P1 | Traffic spike (proactive) | SD-WAN | Preemptive steering | 0s (trước sự cố) |
| P2 | QoE degradation (proactive) | SD-WAN | Mid-session steering | 0s (trước vi phạm SLA) |

---

## PHẦN 4: NGUỒN DỮ LIỆU TELEMETRY

AI cần dữ liệu từ nhiều nguồn để hoạt động:

| Loại dữ liệu | Nguồn | Tần suất |
| --- | --- | --- |
| CPU/Memory | Prometheus + Python psutil | 5s |
| Interface utilization | SNMP / OpenFlow port stats | 5s |
| Packet loss, latency, jitter | ICMP probe + iperf3 | 10s |
| Link status | OpenFlow port_status message | Event-driven |
| OSPF neighbor state | FRR syslog + vtysh | Event-driven |
| VRRP state | Keepalived syslog | Event-driven |
| WAN path quality | SD-WAN Edge probe | 5s |
| Flow statistics | OpenFlow flow_stats_reply | 10s |
| Error flows | Prometheus of_errors metric | 5s |

**Pipeline:**
```
Network Devices
      ↓
Telemetry Collector (Prometheus)
      ↓
Feature Engineering + Normalization
      ↓
AI Engine (Anomaly Detection + RCA + PPO Agent)
      ↓ (WebSocket)
NOC Dashboard (Flask + SocketIO :5050)
      ↓ (Recovery Intent)
SDN Controller / SD-WAN Controller
```

---

## PHẦN 5: ĐIỂM SÁNG TẠO CỦA ĐỀ TÀI

1. **Mô phỏng 5 WAN transports thuần Mininet:** MPLS, Internet, LTE, 5G, VPN được mô phỏng bằng OVS path + `tc netem` — không cần GNS3 hay thiết bị vật lý.

2. **SD-WAN Controller tự viết (Python):** Thay vì dùng công cụ thương mại, SD-WAN Controller được tự lập trình — đây là đóng góp khoa học của luận văn.

3. **Kết hợp Proactive + Reactive:** Hệ thống không chỉ phản ứng sau sự cố mà còn **dự báo và phòng ngừa** bằng Holt-Winters + QoE Regression.

4. **PPO RL Agent:** Sử dụng học tăng cường để agent tự học chiến lược phục hồi tối ưu — không phải hard-coded rules.

5. **Closed-Loop với Safety Layer:** AI không có quyền trực tiếp cấu hình thiết bị — mọi quyết định phải qua Policy/Safety Layer trước khi thực thi.

6. **NOC Dashboard thời gian thực:** Trực quan hóa toàn bộ vòng lặp tự phục hồi qua Flask + SocketIO.
