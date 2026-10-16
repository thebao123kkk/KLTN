## **1. Quy ước chung**
Mỗi site dùng một dải IP riêng để dễ nhận diện:

| Site | Network |
| --- | --- |
| Bảo Lộc | 10.10.0.0/16 |
| Nha Trang | 10.20.0.0/16 |
| HCM | 10.30.0.0/16 |
| Data Center | 10.100.0.0/16 |

Quy tắc VLAN:
USER       → mạng phòng ban
```text
IOT        → Printer / sensor
CCTV       → Camera
WIFI       → WiFi users
VOICE      → VoIP
MGMT       → quản trị thiết bị
SERVER     → Data Center
```
**Lưu ý:** Vì Bảo Lộc là mạng phẳng, ta không cần tạo VLAN riêng cho từng phòng ban. Hai site lớn mới tận dụng VLAN để thể hiện segmentation.

## **2. Bảo Lộc — Flat Network**
### **2.1 Phòng ban và host**

| Phòng ban | Host |
| --- | --- |
| Hành chính | BL-ADMIN-PC01 – PC03 |
| Kinh doanh | BL-SALES-PC01 – PC03 |
| Kế toán | BL-ACC-PC01 – PC03 |
| CNTT | BL-IT-PC01 – PC03 |

→ **12 PC**
Thiết bị bổ sung:

| Loại | Host |
| --- | --- |
| Printer | BL-PRN01, BL-PRN02 |
| Camera | BL-CAM01, BL-CAM02 |
| WiFi | BL-AP01 |

### **2.2 VLAN Bảo Lộc**
Dù gọi là **Flat Network**, mình vẫn tách các **loại thiết bị** quan trọng để có security/fault domain.

| VLAN | Tên | Subnet | Gateway |
| --- | --- | --- | --- |
| 10 | USER | 10.10.10.0/24 | 10.10.10.1 |
| 30 | IoT | 10.10.30.0/24 | 10.10.30.1 |
| 35 | CCTV | 10.10.35.0/24 | 10.10.35.1 |
| 50 | WIFI | 10.10.50.0/24 | 10.10.50.1 |
| 99 | MGMT | 10.10.99.0/24 | 10.10.99.1 |

### **Host IP**
BL-ADMIN-PC01  10.10.10.11
BL-ADMIN-PC02  10.10.10.12
BL-ADMIN-PC03  10.10.10.13

BL-SALES-PC01  10.10.10.21
BL-SALES-PC02  10.10.10.22
BL-SALES-PC03  10.10.10.23

BL-ACC-PC01    10.10.10.31
BL-ACC-PC02    10.10.10.32
BL-ACC-PC03    10.10.10.33

BL-IT-PC01     10.10.10.41
BL-IT-PC02     10.10.10.42
BL-IT-PC03     10.10.10.43
IoT:
BL-PRN01       10.10.30.11
BL-PRN02       10.10.30.12
CCTV:
BL-CAM01       10.10.35.11
BL-CAM02       10.10.35.12

## **3. Nha Trang — 3-Tier**
Nha Trang có **6 phòng ban**.

| Phòng ban | PC |
| --- | --- |
| Hành chính | 3 |
| Kinh doanh | 3 |
| Kế toán | 3 |
| Nhân sự | 3 |
| CSKH | 3 |
| CNTT | 3 |
| Tổng | 18 |

Thêm:
2 Printer
3 Camera
1 AP
2 IP Phone
→ **26 host đại diện**

### **3.1 VLAN Nha Trang**
Ở đây mình đề xuất **mỗi phòng ban một VLAN**.

| VLAN | Phòng ban | Subnet |
| --- | --- | --- |
| 110 | ADMIN | 10.20.10.0/24 |
| 120 | SALES | 10.20.20.0/24 |
| 130 | ACCOUNTING | 10.20.30.0/24 |
| 140 | HR | 10.20.40.0/24 |
| 150 | CUSTOMER | 10.20.50.0/24 |
| 160 | IT | 10.20.60.0/24 |
| 170 | IoT | 10.20.70.0/24 |
| 175 | CCTV | 10.20.75.0/24 |
| 180 | WIFI | 10.20.80.0/24 |
| 190 | VOICE | 10.20.90.0/24 |
| 199 | MGMT | 10.20.99.0/24 |

Gateway luôn là .1.
### Ví dụ:
NT-ADMIN-PC01
10.20.10.11
VLAN 110
GW 10.20.10.1
NT-SALES-PC01
10.20.20.11
VLAN 120
GW 10.20.20.1
NT-ACC-PC01
10.20.30.11
VLAN 130
GW 10.20.30.1

## **4. Nha Trang — phân bổ Access Switch**
Đây là phần rất quan trọng.
NT-CORE
```text
                   /          \
             NT-DIST01       NT-DIST02
             /  |  \          / |  \
            /   |   \        /  |   \
         ACC01 ACC02 ACC03 ACC04 ACC05 ACC06
Phân bổ:
```

| Switch | Phòng ban |
| --- | --- |
| NT-ACC01 | ADMIN |
| NT-ACC02 | SALES |
| NT-ACC03 | ACCOUNTING |
| NT-ACC04 | HR |
| NT-ACC05 | CUSTOMER |
| NT-ACC06 | IT + IoT/CCTV/WiFi |

Như vậy khi:
NT-ACC02
bị lỗi, AI có thể suy luận:
Phòng Kinh doanh Nha Trang bị ảnh hưởng.
Đây chính là **fault domain** rất đẹp cho luận văn.

## **5. HCM — 3-Tier**
HCM có **8 phòng ban**:

| Phòng ban | PC |
| --- | --- |
| Hành chính | 3 |
| Kinh doanh | 3 |
| Kế toán | 3 |
| Nhân sự | 3 |
| Marketing | 3 |
| CSKH | 3 |
| Kỹ thuật | 3 |
| CNTT | 3 |
| Tổng | 24 |

Thêm:
3 Printer
4 Camera
2 AP
2 IP Phone
→ **35 host đại diện**

## **6. VLAN HCM**

| VLAN | Phòng ban | Subnet |
| --- | --- | --- |
| 210 | ADMIN | 10.30.10.0/24 |
| 220 | SALES | 10.30.20.0/24 |
| 230 | ACCOUNTING | 10.30.30.0/24 |
| 240 | HR | 10.30.40.0/24 |
| 250 | MARKETING | 10.30.50.0/24 |
| 260 | CUSTOMER | 10.30.60.0/24 |
| 270 | TECHNICAL | 10.30.70.0/24 |
| 280 | IT | 10.30.80.0/24 |
| 290 | IoT | 10.30.90.0/24 |
| 295 | CCTV | 10.30.95.0/24 |
| 296 | WIFI | 10.30.96.0/24 |
| 297 | VOICE | 10.30.97.0/24 |
| 299 | MGMT | 10.30.99.0/24 |

## **7. HCM Access Layer**
HCM-CORE
```text
                     /        \
               DIST01          DIST02
              / |  \           / |  \
             /  |   \         /  |   \
          ACC01 ACC02 ACC03 ACC04 ACC05 ACC06
Phân bổ:
ACC01 → ADMIN
ACC02 → SALES
ACC03 → ACCOUNTING
ACC04 → HR
ACC05 → MARKETING + CUSTOMER
```
ACC06 → TECHNICAL + IT + IoT/CCTV/WiFi/Voice
Nếu muốn topology đẹp hơn, ta có thể dùng **8 Access Switch**, mỗi phòng ban một switch, nhưng với Mininet thì **6 switch là hợp lý hơn**.

## **8. Data Center — 10 server**
Data Center:
DC-SPINE01
```text
                  /    |     \
                 /     |      \
             LEAF01  LEAF02  LEAF03
                \      |      /
                 \     |     /
                  DC-SPINE02
                       │
                    Servers
Tôi vẫn giữ:
```

| Server | IP | VLAN |
| --- | --- | --- |
| DC-WEB01 | 10.100.10.11 | 310 |
| DC-WEB02 | 10.100.10.12 | 310 |
| DC-APP01 | 10.100.20.11 | 320 |
| DC-APP02 | 10.100.20.12 | 320 |
| DC-DB01 | 10.100.30.11 | 330 |
| DC-DB02 | 10.100.30.12 | 330 |
| DC-DNS01 | 10.100.40.11 | 340 |
| DC-DHCP01 | 10.100.40.12 | 340 |
| DC-MON01 | 10.100.50.11 | 350 |
| DC-MGMT01 | 10.100.60.11 | 360 |

## **9. Tổng bảng host**

| Site | PC | Printer | Camera | AP | IP Phone | Server |
| --- | --- | --- | --- | --- | --- | --- |
| Bảo Lộc | 12 | 2 | 2 | 1 | 0 | 0 |
| Nha Trang | 18 | 2 | 3 | 1 | 2 | 0 |
| HCM | 24 | 3 | 4 | 2 | 2 | 0 |
| Data Center | 0 | 0 | 0 | 0 | 0 | 10 |
| Tổng | 54 | 7 | 9 | 4 | 4 | 10 |

→ **88 host/network endpoint đại diện.**
Nhưng đây là điểm quan trọng:
**88 host không có nghĩa Mininet bắt buộc phải chạy 88 traffic generator.**
Ta có thể có 88 node nhưng chỉ khoảng **15–25 node tạo traffic tích cực**.

## **10. Các loại traffic**
Để phục vụ AI, mình sẽ định nghĩa traffic như sau:
PC → Web Server
PC → Application Server
PC → Database

Printer → Management/Application

Camera → Monitoring Server

WiFi → Web/Application

IP Phone → SIP/RTP Server

Monitoring → Network Devices
Đặc biệt:
VOICE
SIP  → signaling
RTP  → real-time media
DSCP EF → high priority

## **11. QoS**
Có thể thiết kế policy:

| Traffic | DSCP | Priority |
| --- | --- | --- |
| VoIP RTP | EF (46) | Very High |
| VoIP SIP | CS3/AF31 | High |
| Database | AF21 | High |
| Web/App | AF11 | Medium |
| CCTV | AF21 | Medium |
| File Transfer | BE | Low |

Khi WAN congestion:
WAN CONGESTION
```text
                     │
          ┌──────────┼──────────┐
          │          │          │
        VoIP       Web        File
          │          │          │
        HIGH       MEDIUM      LOW
          │          │          │
          └──────────┴──────────┘
                     │
               QoS Scheduler
```

## **12. Fault domain**
Đây là phần mình nghĩ bạn **nên đưa vào thiết kế ngay từ đầu**.
### Ví dụ:
**Fault 1 — Access**
NT-ACC02 DOWN
```text
      ↓
NT-SALES affected
      ↓
AI RCA
      ↓
SDN Controller
      ↓
Alternative path
Fault 2 — Distribution
NT-DIST01 DOWN
       ↓
Multiple departments affected
       ↓
AI identifies common dependency
       ↓
Reroute via DIST02
Fault 3 — WAN
HCM ─── MPLS ─── DC
          ↓
       DEGRADED
          ↓
         AI
          ↓
     SD-WAN Controller
          ↓
      Internet VPN
Fault 4 — QoS
WAN congestion
      ↓
VoIP latency/jitter ↑
      ↓
AI detects QoS anomaly
      ↓
Traffic steering
      +
QoS priority
```

## **13. Toàn bộ mapping cuối cùng**
AI
```text
                     │
          ┌──────────┴──────────┐
          │                     │
        SDN                   SD-WAN
          │                     │
          ▼                     ▼
      ┌────────┐          ┌───────────┐
      │  LAN   │          │    WAN    │
      └────┬───┘          └─────┬─────┘
           │                    │
     ┌─────┴──────┐             │
     │            │             │
    USER         IoT            │
     │            │             │
   VLAN          VLAN            │
     │            │             │
 PC/Dept     Printer/CCTV       │
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                 Bảo Lộc     Nha Trang      HCM
                  Flat         3-Tier       3-Tier
                    │           │           │
                    └───────────┼───────────┘
                                │
                                ▼
                          DATA CENTER
                          Spine / Leaf
                                │
                      WEB / APP / DB / INFRA
Đây là baseline mình khuyên chốt
Bảo Lộc
4 phòng ban
12 PC
IoT + CCTV + WiFi
Flat
Nha Trang
6 phòng ban
18 PC
IoT + CCTV + WiFi + Voice
3-Tier
HCM
8 phòng ban
24 PC
IoT + CCTV + WiFi + Voice
3-Tier
Data Center
Spine-Leaf
10 server
Web / App / DB / Infrastructure / Monitoring
```
**Điểm quan trọng:** ta không chỉ thiết kế topology mà còn định nghĩa ngay **fault domain, VLAN, IP, loại host và loại traffic**. Như vậy khi chuyển sang Mininet, gần như chỉ còn việc **code topology + routing + OpenFlow + traffic generator + fault injection**, chứ không phải thiết kế lại từ đầu.

---

## **14. Ghi chú kỹ thuật - Các thay đổi đã áp dụng (cập nhật 2026-09-26)**

### **14.1 Cấu trúc Mininet Host Router (thay OVS Switch)**

Từ Phase 4/5 trở đi, các Distribution node của Nha Trang và HCM đã được chuyển từ **OVS Switch → Mininet Host Router** để hỗ trợ:
- Sub-interface VLAN (NT_DIST01-eth0.110, HCM_DIST01-eth0.210, ...)
- OSPF/VRRP daemon chạy trong network namespace riêng biệt

| Node | Trước | Sau |
| --- | --- | --- |
| NT_DIST01, NT_DIST02 | 
et.addSwitch(OVSSwitch) | 
et.addHost(ip=None) |
| HCM_DIST01, HCM_DIST02 | 
et.addSwitch(OVSSwitch) | 
et.addHost(ip=None) |
| BL_GW, DC_SP_GW | OVS | Mininet Host Router |

### **14.2 Naming Convention cho interfaces**

| Mô tả | Sai (cũ) | Đúng (mới) |
| --- | --- | --- |
| BL_GW base interface | BL-GW-eth0 | {gw_host.name}-eth0 = BL_GW-eth0 |
| NT DIST base interface | {dist_name}-eth0 | {dist_host.name}-eth0 |
| Keepalived interface | eth0.{vlan_id} | {clean_node_name}-eth0.{vlan_id} |
| HCM DIST parameter | HCM-DIST01 (dấu -) | HCM_DIST01 (dấu _) |

### **14.3 FRR (Free Range Routing) khởi động**

Thay vì dùng service frr start (khởi động toàn hệ thống), mỗi Host Router khởi động daemon riêng trong namespace:

\\\ash
# Zebra (core routing daemon)
/usr/lib/frr/zebra -d --vty_socket /tmp/zebra_{name}.sock

# OSPF daemon
/usr/lib/frr/ospfd -d --vty_socket /tmp/ospfd_{name}.sock
\\\

### **14.4 Linux Bridge VLAN Filtering**

Để 802.1Q tags đi qua bridge r0 trên Distribution Routers:

\\\ash
# Kích hoạt VLAN filtering
ip link set dev br0 type bridge vlan_filtering 1

# Cho phép tất cả VLAN đi qua interface
bridge vlan add dev <intf> vid 2-4094

# Nạp kernel module 802.1Q
modprobe 8021q
\\\

### **14.5 OVS Controller Mode**

Tất cả OVS Switch hoạt động **Standalone L2 MAC Learning** (không kết nối controller):

\\\python
net = Mininet(..., controller=None)
# Không gọi net.addController('c0')
\\\

Lý do: OVS gửi gói ARP/Ping lên controller không tồn tại → gói bị drop. Standalone mode hoạt động ngay lập tức.

### **14.6 STP/RSTP trên Linux Bridge**

Để tránh broadcast storm giữa 2 Distribution Routers (cùng nối vào br0):

\\\ash
ip link set dev br0 type bridge vlan_filtering 1 stp_state 1 forward_delay 200
\\\

OVS STP forward-delay giảm từ 30s → 4s:
\\\
ovs-vsctl set bridge {sw} other-config:stp-forward-delay=2
\\\

### **14.7 WAN Connectivity (Phase 1-6)**

Trong Phase 1-6, các site kết nối qua **direct link** (192.168.x.x/30), chưa có 	c netem.  
Phase 9 sẽ thêm 5 OVS Switch WAN với đặc tính MPLS/Internet/LTE/5G/VPN.

**Địa chỉ WAN link giữa các site:**

| Link | Subnet |
| --- | --- |
| BL ↔ HCM | 192.168.10.0/30 |
| HCM ↔ DC | 192.168.20.0/30 |
| DC ↔ NT | 192.168.30.0/30 |
| NT ↔ BL | 192.168.40.0/30 |
