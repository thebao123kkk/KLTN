# THIẾT KẾ KỸ THUẬT TOÀN DIỆN MẠNG DOANH NGHIỆP (ENTERPRISE TOPOLOGY)

> **Dự án:** Kiến trúc Mạng Doanh nghiệp Tự Phục hồi Sử dụng SD-WAN và Cơ chế Khôi phục Sự cố Thông minh  
> **Trạng thái hoàn thành:** Phase 1 đến Phase 11, Phase 14 (Topology + Services + Security + WAN 5-Path + SD-WAN Controller + QoS Asterisk PBX + SDN Controller)  
> **Môi trường mô phỏng:** Mininet, Open vSwitch (OVS), FRRouting (FRR), Keepalived, Dnsmasq, HAProxy, Asterisk PBX, Faucet SDN Controller, Python SD-WAN.

---

## 1. TỔNG QUAN KIẾN TRÚC MẠNG DOANH NGHIỆP

Hệ thống mạng doanh nghiệp bao gồm **4 Sites địa lý kết nối đa điểm** qua hạ tầng WAN đa kênh:
1. **Trụ sở chính TP. Hồ Chí Minh (HCM Site):** Mô hình 3-Tier (Core - Distribution - Access) lớn nhất.
2. **Chi nhánh Nha Trang (NT Site):** Mô hình 3-Tier chuẩn enterprise trung bình.
3. **Chi nhánh Bảo Lộc (BL Site):** Mô hình Flat Network tối giản cho văn phòng nhỏ.
4. **Trung tâm Dữ liệu (Data Center - DC Site):** Mô hình Spine-Leaf hiện đại kết nối các dịch vụ cốt lõi.

```
                      ┌───────────────────────────────────────┐
                      │    WAN TRANSPORT EMULATION LAYER      │
                      │  (5 Paths: MPLS, 5G, INET, VPN, LTE)  │
                      └──────────────────┬────────────────────┘
                                         │
        ┌───────────────────┬────────────┴───────────┬───────────────────┐
        │                   │                        │                   │
┌───────┴─────────┐ ┌───────┴─────────┐    ┌─────────┴─────────┐ ┌───────┴─────────┐
│     BL SITE     │ │     NT SITE     │    │     HCM SITE      │ │     DC SITE     │
│ (Flat Network)  │ │ (3-Tier High-Av)│    │ (3-Tier Enterprise│ │   (Spine-Leaf)  │
│ 1 SW, 1 GW Host │ │1 Core, 2 Dist GW│    │1 Core, 2 Dist GW  │ │2 Spine, 4 Leaf  │
│ 16 Endpoints    │ │6 Access, 26 Host│    │6 Access, 35 Host  │ │1 GW, 11 Servers │
└─────────────────┘ └─────────────────┘    └───────────────────┘ └─────────────────┘
```

### Quy mô phần cứng & tài nguyên mô phỏng:
- **Tổng số Switches:** 13 Open vSwitch (OVS) LAN switches + 5 OVS WAN Transport switches.
- **Tổng số Routers:** 6 Mininet Host Routers chạy FRRouting (OSPF) + Keepalived (VRRP).
- **Tổng số Endpoints:** 88 Host Endpoints (PC phòng ban, IP Phone, CCTV, Printer, Servers).
- **Tổng số VLANs:** 30+ VLANs được gắn tag 802.1Q độc lập theo chuẩn quy hoạch IP.

---

## 2. CHI TIẾT CẤU TRÚC 4 SITES

### 2.1 Chi nhánh Bảo Lộc (BL Site) - Flat Network
- **Mô hình:** Flat L2 Network kết nối trực tiếp vào L3 Gateway Host.
- **Thiết bị mạng:**
  - `BL_SW` (dpid: `0x000000000003`): Open vSwitch L2.
  - `BL_GW`: Mininet Host Router đóng vai trò Gateway, OSPF Router, ACL Firewall.
- **Phân vùng VLAN & IP Subnets (`10.10.0.0/16`):**
  - VLAN 10 (USER): `10.10.10.0/24`, Gateway: `10.10.10.1` (12 Hosts: ADM01-03, SAL01-03, ACC01-03, IT01-03)
  - VLAN 30 (IoT): `10.10.30.0/24`, Gateway: `10.10.30.1` (2 Hosts: PRN01, PRN02)
  - VLAN 35 (CCTV): `10.10.35.0/24`, Gateway: `10.10.35.1` (2 Hosts: CAM01, CAM02)
  - VLAN 50 (WIFI): `10.10.50.0/24`, Gateway: `10.10.50.1`
  - VLAN 99 (MGMT): `10.10.99.0/24`, Router-ID OSPF: `10.10.99.1`

### 2.2 Chi nhánh Nha Trang (NT Site) - 3-Tier Network (High Availability)
- **Mô hình:** Hierarchical 3-Tier (Core Switch + Dual Distribution Routers + 6 Access Switches).
- **Thiết bị mạng:**
  - **Core Switch:** `NT_CORE` (dpid: `0x000000000001`) - Trunking 802.1Q nối Dist và Access.
  - **Distribution Routers:** `NT_DIST01` (Master VRRP, OSPF Router-ID `10.20.99.1`), `NT_DIST02` (Backup VRRP, OSPF Router-ID `10.20.99.2`).
  - **Access Switches:** `NT_ACC01` (dpid: `0x11`) đến `NT_ACC06` (dpid: `0x16`).
- **Phân vùng VLAN & IP Subnets (`10.20.0.0/16`):**
  - VLAN 110 (ADMIN): `10.20.10.0/24` (3 Hosts: NT_ADM01-03)
  - VLAN 120 (SALES): `10.20.20.0/24` (3 Hosts: NT_SAL01-03)
  - VLAN 130 (ACCOUNTING): `10.20.30.0/24` (3 Hosts: NT_ACC01-03)
  - VLAN 140 (HR): `10.20.40.0/24` (3 Hosts: NT_HR01-03)
  - VLAN 150 (CUSTOMER): `10.20.50.0/24` (3 Hosts: NT_CUS01-03)
  - VLAN 160 (IT): `10.20.60.0/24` (3 Hosts: NT_IT01-03)
  - VLAN 170 (IoT): `10.20.70.0/24` (2 Printers: NT_PRN01-02)
  - VLAN 175 (CCTV): `10.20.75.0/24` (3 Cameras: NT_CAM01-03)
  - VLAN 180 (WIFI): `10.20.80.0/24` (1 AP: NT_AP01)
  - VLAN 190 (VOICE): `10.20.90.0/24` (2 IP Phones: NT_PHN01-02)

### 2.3 Trụ sở TP. Hồ Chí Minh (HCM Site) - 3-Tier Enterprise
- **Mô hình:** Hierarchical 3-Tier quy mô lớn nhất.
- **Thiết bị mạng:**
  - **Core Switch:** `HCM_CORE` (dpid: `0x000000000002`).
  - **Distribution Routers:** `HCM_DIST01` (Master VRRP, OSPF Router-ID `10.30.99.1`), `HCM_DIST02` (Backup VRRP, OSPF Router-ID `10.30.99.2`).
  - **Access Switches:** `HCM_ACC01` (dpid: `0x21`) đến `HCM_ACC06` (dpid: `0x26`).
- **Phân vùng VLAN & IP Subnets (`10.30.0.0/16`):**
  - VLAN 210 (ADMIN): `10.30.10.0/24` (3 Hosts)
  - VLAN 220 (SALES): `10.30.20.0/24` (3 Hosts)
  - VLAN 230 (ACCOUNTING): `10.30.30.0/24` (3 Hosts)
  - VLAN 240 (HR): `10.30.40.0/24` (3 Hosts)
  - VLAN 250 (MARKETING): `10.30.50.0/24` (3 Hosts)
  - VLAN 260 (CUSTOMER): `10.30.60.0/24` (3 Hosts)
  - VLAN 270 (TECHNICAL): `10.30.70.0/24` (3 Hosts)
  - VLAN 280 (IT): `10.30.80.0/24` (3 Hosts)
  - VLAN 290 (IoT): `10.30.90.0/24` (3 Printers)
  - VLAN 295 (CCTV): `10.30.95.0/24` (4 Cameras)
  - VLAN 296 (WIFI): `10.30.96.0/24` (2 APs)
  - VLAN 297 (VOICE): `10.30.97.0/24` (2 IP Phones)

### 2.4 Data Center (DC Site) - Spine-Leaf Architecture
- **Mô hình:** Spine-Leaf L2/L3 Fabric.
- **Thiết bị mạng:**
  - **Spine Switches:** `DC_SPINE01` (dpid: `0xDC01`), `DC_SPINE02` (dpid: `0xDC02`).
  - **Leaf Switches:** `DC_LEAF01` (WEB), `DC_LEAF02` (APP), `DC_LEAF03` (DB), `DC_LEAF04` (INFRA/MGMT).
  - **DC Gateway:** `DC_SP_GW` (OSPF Router-ID `10.100.99.1`).
- **Phân vùng VLAN & IP Subnets (`10.100.0.0/16`):**
  - VLAN 310 (WEB DMZ): `10.100.10.0/24` → `DC_WEB01` (`.11`), `DC_WEB02` (`.12`)
  - VLAN 320 (APP Tier): `10.100.20.0/24` → `DC_APP01` (`.11`), `DC_APP02` (`.12`)
  - VLAN 330 (DB Tier): `10.100.30.0/24` → `DC_DB01` (`.11`), `DC_DB02` (`.12`)
  - VLAN 340 (INFRA): `10.100.40.0/24` → `DC_DNS01` (`.11`), `DC_DHCP01` (`.12`), `DC_DHCP02` (`.13`)
  - VLAN 350 (MONITORING): `10.100.50.0/24` → `DC_MON01` (`.11`)
  - VLAN 360 (MGMT/NTP): `10.100.60.0/24` → `DC_MGMT01` (`.11`)

---

## 3. CHI TIẾT CẤU HÌNH CÁC LAYER (PHASE 1 - 14)

### Phase 1: Build Base Topology
- Xây dựng sơ đồ Mininet dạng đối tượng lập trình ([enterprise_topo.py](file:///d:/KLTN/src/topology/enterprise_topo.py)).
- Khởi tạo 88 Host endpoints với Network Namespaces độc lập.
- Gán MAC tự động (`autoSetMacs=True`) và liên kết các link L2 giữa Hosts, Access, Core và Distribution Switches.

### Phase 2 & 3: VLAN Segmentation & RSTP Loop Prevention
- **VLAN 802.1Q Tagging:** Cấu hình trunk ports trên các liên kết Switch-to-Switch và access ports trên các cổng nối Host.
- **RSTP (Rapid Spanning Tree Protocol - 802.1w):** 
  - Khởi tạo OVS Switches với `stp=True`.
  - Độ ưu tiên STP được thiết lập sao cho `NT_CORE` và `HCM_CORE` làm Root Bridge cho các vlan tương ứng, ngăn ngừa triệt để hiện tượng Broadcast Storm.

### Phase 4: Dynamic Inter-Site Routing (OSPF Area 0)
- **Công nghệ:** FRRouting (FRR - `zebra` và `ospfd`) chạy trực tiếp trong Namespace của 6 Host Routers:
  - `BL_GW`, `NT_DIST01`, `NT_DIST02`, `HCM_DIST01`, `HCM_DIST02`, `DC_SP_GW`.
- **Cấu hình OSPF:**
  - Area: `0.0.0.0` (Backbone Area).
  - Network Advertising: Quảng bá toàn bộ dải LAN local (`10.x.0.0/16`) và WAN Point-to-Point (`172.16.x.x/24`).
  - Timer: Hello 1s, Dead 4s cho phép hội tụ định tuyến cực nhanh (< 5s).

### Phase 5: Gateway Redundancy (VRRP via Keepalived)
- **Công nghệ:** Keepalived daemon triển khai trên cặp Distribution Routers tại Nha Trang và HCM.
- **Bảng thông số VRRP:**

| Site | Subnet | Virtual IP (VIP) | Master Router (Priority 110) | Backup Router (Priority 100) | VRID |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nha Trang** | `10.20.x.0/24` | `10.20.x.1` | `NT_DIST01` | `NT_DIST02` | `20` |
| **HCM** | `10.30.x.0/24` | `10.30.x.1` | `HCM_DIST01` | `HCM_DIST02` | `30` |

- **Cơ chế Failover:** Khi Master Router lỗi interface hoặc sập process, Backup Router lập tức tiếp quản Virtual IP trong vòng 1-2 giây mà không làm đứt kết nối người dùng.

### Phase 6: Enterprise Core Services (DHCP, DNS, NTP)
Cấu hình chi tiết được quản lý tại [services.yaml](file:///d:/KLTN/src/config/services.yaml) và khởi tạo qua [start_services_datacenter()](file:///d:/KLTN/src/topology/sites/datacenter.py).

#### 6.1 Kiến trúc DHCP — Centralized HA (DHCP01 + DHCP02) + Dual Relay

> **Chốt thiết kế:** Chỉ có **2 DHCP Server đặt tại Data Center**. Các Site chi nhánh (HCM, NT, BL) **không có DHCP Server riêng** — chỉ chạy **DHCP Relay Agent** chuyển tiếp request lên cả 2 server tại DC.

```
  ┌────────────────────────────────────────────────────────────────────┐
  │                   DATA CENTER  (VLAN 340 — 10.100.40.0/24)         │
  │                                                                    │
  │   ┌─────────────────────────┐   ┌─────────────────────────┐       │
  │   │  DC_DHCP01  (Primary)   │   │  DC_DHCP02  (Backup)    │       │
  │   │  IP: 10.100.40.12       │   │  IP: 10.100.40.13       │       │
  │   │  dnsmasq — DHCP Pool    │   │  dnsmasq — cùng Pool    │       │
  │   └──────────┬──────────────┘   └─────────────┬───────────┘       │
  │              └──────────────────┬──────────────┘                  │
  └─────────────────────────────────┼──────────────────────────────────┘
                                    │ WAN / SD-WAN
           ┌─────────────────────── ┼ ───────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
  ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
  │    HCM Site     │     │    NT Site       │     │    BL Site      │
  │  HCM_DIST01     │     │  NT_DIST01       │     │  BL_GW          │
  │  HCM_DIST02     │     │  NT_DIST02       │     │                 │
  │                 │     │                  │     │                 │
  │ [Relay Agent]   │     │ [Relay Agent]    │     │ [Relay Agent]   │
  │  ↳ 10.100.40.12 │     │  ↳ 10.100.40.12  │     │  ↳ 10.100.40.12 │
  │  ↳ 10.100.40.13 │     │  ↳ 10.100.40.13  │     │  ↳ 10.100.40.13 │
  │  (không có DHCP │     │  (không có DHCP  │     │  (không có DHCP │
  │   server riêng) │     │   server riêng)  │     │   server riêng) │
  └────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
           │ VLANs                 │ VLANs                  │ VLANs
        Endpoints               Endpoints               Endpoints
```

**Lý do chốt Centralized DHCP HA (chỉ tại DC):**
1. **Không cần Local DHCP tại Branch:** Đã có 5 kênh WAN dự phòng (MPLS, 5G, INET, VPN, LTE) — xác suất mất hoàn toàn kết nối về DC là cực kỳ thấp.
2. **Tránh xung đột IP Pool:** Nếu có cả Local DHCP và Central DHCP, khi WAN chập chờn dễ xảy ra cấp trùng IP. Chỉ 1 nguồn cấp duy nhất (DC) loại trừ hoàn toàn rủi ro này.
3. **Single Source of Truth:** Toàn bộ Lease DB, Subnet Options (DNS, Gateway, NTP) tập trung tại DC — AI Engine và SDN Controller có thể giám sát, điều phối.
4. **HA bằng Dual Server tại DC:** `DC_DHCP02` là bản sao cấu hình của `DC_DHCP01`. Mỗi Branch Relay agent gửi DHCP Discover đồng thời tới cả 2 IP — nếu DHCP01 sập, DHCP02 tự động trả Offer mà không cần failover protocol.

**Cơ chế Dual Relay (triển khai qua `dhrelay`):**

- Mỗi VLAN interface trên Gateway Router cấu hình **relay đồng thời tới 2 địa chỉ**:
  ```bash
  # Ví dụ trên NT_DIST01 — VLAN 110 (NT ADMIN 10.20.10.0/24)
  ip route add 10.100.40.12 via 172.16.x.4   # Route tới DHCP Primary
  ip route add 10.100.40.13 via 172.16.x.4   # Route tới DHCP Backup
  
  # dhrelay forward đồng thời
  dhrelay -i <vlan_iface> 10.100.40.12 10.100.40.13
  ```
- **Cấu hình chi tiết trong** [services.yaml](file:///d:/KLTN/src/config/services.yaml) `relay_agents` section:
  - Nha Trang: `relay_hosts: [NT_DIST01, NT_DIST02]` → `relay_ips: [10.100.40.12, 10.100.40.13]`
  - HCM: `relay_hosts: [HCM_DIST01, HCM_DIST02]` → `relay_ips: [10.100.40.12, 10.100.40.13]`
  - Bảo Lộc: `relay_hosts: [BL_GW]` → `relay_ips: [10.100.40.12, 10.100.40.13]`
- **Config dnsmasq** cho cả 2 server được tạo tự động bởi [generate_dnsmasq_configs.py](file:///d:/KLTN/src/scripts/generate_dnsmasq_configs.py) — DHCP02 dùng pid/lease file riêng (`dnsmasq_dhcp2.pid`, `dnsmasq_dhcp2.leases`).

**Chi tiết các Subnet DHCP Pools (chia sẻ giữa DHCP01 và DHCP02):**

| Site | VLAN ID | Subnet Network | Range IP Cấp tự động | Default Gateway (Option 3) | DNS Server (Option 6) | NTP Server (Option 42) | Lease Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bảo Lộc** | VLAN 10 | `10.10.10.0/24` | `10.10.10.100 - 10.10.10.200` | `10.10.10.1` | `10.100.40.11` | `10.100.60.11` | 12h |
| **Nha Trang** | VLAN 110 | `10.20.10.0/24` | `10.20.10.100 - 10.20.10.200` | `10.20.10.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **Nha Trang** | VLAN 120 | `10.20.20.0/24` | `10.20.20.100 - 10.20.20.200` | `10.20.20.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **Nha Trang** | VLAN 130 | `10.20.30.0/24` | `10.20.30.100 - 10.20.30.200` | `10.20.30.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **Nha Trang** | VLAN 140 | `10.20.40.0/24` | `10.20.40.100 - 10.20.40.200` | `10.20.40.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **Nha Trang** | VLAN 150 | `10.20.50.0/24` | `10.20.50.100 - 10.20.50.200` | `10.20.50.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **Nha Trang** | VLAN 160 | `10.20.60.0/24` | `10.20.60.100 - 10.20.60.200` | `10.20.60.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **TP. HCM** | VLAN 210 | `10.30.10.0/24` | `10.30.10.100 - 10.30.10.200` | `10.30.10.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **TP. HCM** | VLAN 220 | `10.30.20.0/24` | `10.30.20.100 - 10.30.20.200` | `10.30.20.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **TP. HCM** | VLAN 230 | `10.30.30.0/24` | `10.30.30.100 - 10.30.30.200` | `10.30.30.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **TP. HCM** | VLAN 240 | `10.30.40.0/24` | `10.30.40.100 - 10.30.40.200` | `10.30.40.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **TP. HCM** | VLAN 250 | `10.30.50.0/24` | `10.30.50.100 - 10.30.50.200` | `10.30.50.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **TP. HCM** | VLAN 260 | `10.30.60.0/24` | `10.30.60.100 - 10.30.60.200` | `10.30.60.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **TP. HCM** | VLAN 270 | `10.30.70.0/24` | `10.30.70.100 - 10.30.70.200` | `10.30.70.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |
| **TP. HCM** | VLAN 280 | `10.30.80.0/24` | `10.30.80.100 - 10.30.80.200` | `10.30.80.1` (VIP) | `10.100.40.11` | `10.100.60.11` | 12h |

**Mô-đun triển khai DHCP HA (đã cài đặt đầy đủ):**

| File | Chức năng |
| :--- | :--- |
| [services.yaml](file:///d:/KLTN/src/config/services.yaml) | Khai báo `relay_agents` với `relay_ips: [10.100.40.12, 10.100.40.13]` cho 3 sites |
| [generate_dnsmasq_configs.py](file:///d:/KLTN/src/scripts/generate_dnsmasq_configs.py) | Tạo `dnsmasq_dhcp.conf` (Primary) + `dnsmasq_dhcp2.conf` (Backup) — cùng Pool, pid riêng |
| [configure_dhcp_relay.py](file:///d:/KLTN/src/scripts/configure_dhcp_relay.py) | Chạy `dhrelay -i <vlan_intf> 10.100.40.12 10.100.40.13` trên BL_GW, NT_DIST01/02, HCM_DIST01/02 |
| [datacenter.py `start_dhcp_ha()`](file:///d:/KLTN/src/topology/sites/datacenter.py) | Khởi động song song `dnsmasq` trên DC_DHCP01 và DC_DHCP02 |
| [check_phase6.py](file:///d:/KLTN/src/tests/phase_checks/check_phase6.py) | Test: Primary alive, Backup alive, Relay active, Client receive IP, Failover simulation |



#### 6.2 DNS Service Zone & Records (`DC_DNS01` - `10.100.40.11`)
- **Phần mềm:** `dnsmasq` authoritative DNS server cho domain `enterprise.local`.
- **Cấu hình:** Upstream DNS `8.8.8.8`, Cache size 1000 records.
- **Bảng A-Records & CNAME Mappings:**

| FQDN Domain Name | Mapped IP Address | Host Target / Service | Mục đích phân giải |
| :--- | :--- | :--- | :--- |
| `www.enterprise.local` | `10.100.10.10` | **HAProxy Load Balancer VIP** | Tên miền chính truy cập Web App |
| `www1.enterprise.local` | `10.100.10.11` | `DC_WEB01` | Trực tiếp Web Node 01 |
| `www2.enterprise.local` | `10.100.10.12` | `DC_WEB02` | Trực tiếp Web Node 02 |
| `app.enterprise.local` | `10.100.20.11` | `DC_APP01` | Application Server Node 01 |
| `app2.enterprise.local` | `10.100.20.12` | `DC_APP02` | Application Server Node 02 |
| `db.enterprise.local` | `10.100.30.11` | `DC_DB01` | Database Server Node 01 |
| `db2.enterprise.local` | `10.100.30.12` | `DC_DB02` | Database Server Node 02 |
| `dns.enterprise.local` | `10.100.40.11` | `DC_DNS01` | DNS Infrastructure Server |
| `dhcp.enterprise.local` | `10.100.40.12` | `DC_DHCP01` | Primary DHCP Server |
| `dhcp2.enterprise.local` | `10.100.40.13` | `DC_DHCP02` | Backup DHCP Server |
| `sip.enterprise.local` | `10.100.20.11` | `DC_APP01` | SIP Server (Thoại VoIP) |
| `monitor.enterprise.local` | `10.100.50.11` | `DC_MON01` | Prometheus / Telemetry Server |
| `mgmt.enterprise.local` | `10.100.60.11` | `DC_MGMT01` | NTP Server / Management Node |

#### 6.3 NTP Synchronization Service (`DC_MGMT01` - `10.100.60.11`)
- **Phần mềm:** `chrony` daemon.
- **Stratum:** Stratum 2 Server (kết nối upstream `0.pool.ntp.org`, `1.pool.ntp.org`).
- **Cho phép mạng (Allowed Subnets):** `10.10.0.0/16`, `10.20.0.0/16`, `10.30.0.0/16`, `10.100.0.0/16`.
- **NTP Clients:** Tất cả Routers, Switches, Servers và Hosts đồng bộ thời gian từ `10.100.60.11`.

---

### Phase 7: Security ACL & Zone Firewall
- **File cấu hình chuẩn:** [acl_rules.yaml](file:///d:/KLTN/src/config/acl_rules.yaml)
- **Cơ chế nạp tự động:** [configure_acl.py](file:///d:/KLTN/src/scripts/configure_acl.py) thi hành lệnh `iptables` trên 6 Host Routers (`BL_GW`, `NT_DIST01/02`, `HCM_DIST01/02`, `DC_SP_GW`).
- **Ma trận Bảng ACL Rules Chi Tiết (Full Security Matrix):**

| Rule ID | Rule Name | Source Zone / IP Subnet | Destination Zone / IP Subnet | Protocol | Dst Port | Action | Log Prefix | Mục đích an ninh |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ACL_00_OSPF` | ALLOW_OSPF_ROUTING | `0.0.0.0/0` | `0.0.0.0/0` | OSPF (89) | Any | **ACCEPT** | - | Duy trì bảng định tuyến OSPF |
| `ACL_00_ICMP` | ALLOW_ICMP_ALL | `0.0.0.0/0` | `0.0.0.0/0` | ICMP | Any | **ACCEPT** | - | Cho phép Ping kiểm tra kết nối |
| `ACL_00_MGMT` | ALLOW_MGMT_ACCESS | `it_mgmt` (`*.99.0/24`, `*.80.0`) | `10.0.0.0/8` | ANY | Any | **ACCEPT** | - | IT Admin truy cập quản trị |
| `ACL_00_DC_MON` | ALLOW_MONITORING | `dc_mon` (`10.100.50.0/24`) | `10.0.0.0/8` | TCP/UDP | 9090, 9100, 9302, 7070 | **ACCEPT** | - | Monitoring scrape metrics |
| `ACL_01` | USER_to_WEB | `user` (`10.10.10.0`, `10.20.x.0`, `10.30.x.0`) | `dc_web` (`10.100.10.0/24`) | TCP | 80, 443, 8080 | **ACCEPT** | - | User truy cập Web Server |
| `ACL_02` | USER_to_APP | `user` | `dc_app` (`10.100.20.0/24`) | TCP | 8080, 8443 | **ACCEPT** | - | User gọi Application API |
| `ACL_03` | WIFI_to_WEB | `wifi` (`10.x.50.0/24`, `*.90.0`) | `dc_web` | TCP | 80, 443 | **ACCEPT** | - | Khách WiFi dùng Web |
| `ACL_04` | WEB_to_APP | `dc_web` | `dc_app` | TCP | 8080, 8443 | **ACCEPT** | - | Tier Web gọi Tier App |
| `ACL_05` | APP_to_DB | `dc_app` | `dc_db` (`10.100.30.0/24`) | TCP | 3306, 5432, 27017 | **ACCEPT** | - | Tier App kết nối Database |
| `ACL_06` | ALL_to_INFRA | `10.0.0.0/8` | `dc_infra` (`10.100.40.0/24`) | TCP/UDP | **53 (DNS), 67/68 (DHCP), 123 (NTP)** | **ACCEPT** | - | Toàn mạng sử dụng Dịch vụ Cốt lõi |
| `ACL_07` | VOICE_to_SIP | `voice` (`10.20.90.0`, `10.30.97.0`) | `dc_app` (`10.100.20.11`) | TCP/UDP | 5060, 5061 | **ACCEPT** | - | Đăng ký tổng đài SIP VoIP |
| `ACL_08` | VOICE_RTP | `voice` | `dc_app` | UDP | 10000 - 20000 | **ACCEPT** | - | Truyền luồng âm thanh RTP |
| `ACL_09` | CCTV_to_MON | `cctv` (`10.x.35.0`, `*.75.0`, `*.95.0`) | `dc_mon` (`10.100.50.0/24`) | TCP/UDP | 554, 8554, 1935 | **ACCEPT** | - | Camera truyền luồng RTSP |
| `ACL_10` | DENY_CCTV_DB | `cctv` | `dc_db` | ANY | Any | **DROP** | `BLOCKED_CCTV_DB` | Cách ly Camera không vào DB |
| `ACL_11` | DENY_IoT_USER | `iot` (`10.x.30.0`, `*.75.0`, `*.95.0`) | `user` | ANY | Any | **DROP** | `BLOCKED_IoT_USER` | Ngăn thiết bị IoT quét User LAN |
| `ACL_12` | DENY_IoT_DB | `iot` | `dc_db` | ANY | Any | **DROP** | `BLOCKED_IoT_DB` | Ngăn IoT vào Database |
| `ACL_13` | DENY_CCTV_USER | `cctv` | `user` | ANY | Any | **DROP** | `BLOCKED_CCTV_USER` | Ngăn Camera truy cập User LAN |
| `ACL_14` | DENY_USER_DB | `user` | `dc_db` | TCP | 3306, 5432, 27017 | **DROP** | `BLOCKED_USER_DB` | Chặn User truy cập thẳng DB |
| `ACL_15` | ALLOW_INTER_USER | `user` | `user` | TCP/UDP | 445, 139, 3389, 22 | **ACCEPT** | - | Truyền file SMB / RDP inter-site |
| `ACL_99` | DEFAULT_POLICY | `0.0.0.0/0` | `0.0.0.0/0` | ANY | Any | **ACCEPT** | - | Default Allow (Lab environment) |

#### 6.4 Mẫu lệnh `iptables` Sinh ra và Thực thi trên Firewall Gateway:
```bash
# 1. Flush & Cấu hình Default Forward Policy
iptables -F FORWARD
iptables -P FORWARD ACCEPT

# 2. Quy tắc Ưu tiên: OSPF, ICMP & Quản trị
iptables -A FORWARD -p ospf -j ACCEPT
iptables -A FORWARD -p icmp -j ACCEPT
iptables -A FORWARD -s 10.10.99.0/24 -d 10.0.0.0/8 -j ACCEPT

# 3. Cho phép Dịch vụ Cốt lõi Infrastructure (DNS, DHCP, NTP)
iptables -A FORWARD -d 10.100.40.0/24 -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -d 10.100.40.0/24 -p udp --dport 67:68 -j ACCEPT
iptables -A FORWARD -d 10.100.60.0/24 -p udp --dport 123 -j ACCEPT

# 4. Cho phép Chuỗi ứng dụng Multi-Tier (Web -> App -> DB)
iptables -A FORWARD -s 10.100.10.0/24 -d 10.100.20.0/24 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -s 10.100.20.0/24 -d 10.100.30.0/24 -p tcp --dport 3306 -j ACCEPT
iptables -A FORWARD -s 10.100.20.0/24 -d 10.100.30.0/24 -p tcp --dport 5432 -j ACCEPT

# 5. Quy tắc Chặn & Ghi log Bảo mật (DROP & LOG)
iptables -A FORWARD -s 10.10.35.0/24 -d 10.100.30.0/24 -j LOG --log-prefix "BLOCKED_CCTV_DB: "
iptables -A FORWARD -s 10.10.35.0/24 -d 10.100.30.0/24 -j DROP

iptables -A FORWARD -s 10.10.30.0/24 -d 10.10.10.0/24 -j LOG --log-prefix "BLOCKED_IoT_USER: "
iptables -A FORWARD -s 10.10.30.0/24 -d 10.10.10.0/24 -j DROP

iptables -A FORWARD -s 10.10.10.0/24 -d 10.100.30.0/24 -p tcp --dport 3306 -j LOG --log-prefix "BLOCKED_USER_DB: "
iptables -A FORWARD -s 10.10.10.0/24 -d 10.100.30.0/24 -p tcp --dport 3306 -j DROP
```

### Phase 8: High Availability & Load Balancing (HAProxy)
- **VIP Address:** `10.100.10.10:80` (gán alias trên `DC_APP01`).
- **Load Balancer Backend:** Pool gồm 2 HTTP Server:
  - `DC_WEB01`: `10.100.10.11:80` (Weight 1)
  - `DC_WEB02`: `10.100.10.12:80` (Weight 1)
- **Health Check:** HTTP GET `/health` tần suất 2 giây (`inter 2s fall 3 rise 2`).
- **Stats Dashboard:** `http://10.100.10.10:8404/stats` cho phép theo dõi tải HTTP realtime.

### Phase 9: WAN Transport Emulation (5 Paths with `tc netem`)
Hạ tầng kết nối WAN nối giữa 4 site được thay thế bằng 5 OVS WAN Switches đại diện cho 5 kênh truyền vật lý khác nhau. Mọi thông số được kiểm soát bằng Linux `tc qdisc netem`:

| Path Name | OVS Switch Name | Subnet WAN | Delay (ms) | Jitter (ms) | Loss (%) | Bandwidth (Mbps) | Đặc tính ưu tiên |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MPLS** | `WAN_MPLS` | `172.16.10.0/24` | **20ms** | **2ms** | **0.1%** | **100 Mbps** | Đường thuê riêng SLA cao nhất |
| **5G** | `WAN_FIVEG` | `172.16.40.0/24` | **15ms** | **5ms** | **0.3%** | **200 Mbps** | Băng thông rộng, độ trễ thấp |
| **Internet** | `WAN_INET` | `172.16.20.0/24` | **40ms** | **10ms** | **0.5%** | **100 Mbps** | Đường Internet phổ thông |
| **VPN** | `WAN_VPN` | `172.16.50.0/24` | **50ms** | **8ms** | **0.8%** | **50 Mbps** | Đường hầm mã hóa qua Internet |
| **LTE** | `WAN_LTE` | `172.16.30.0/24` | **60ms** | **15ms** | **1.0%** | **30 Mbps** | Kênh dự phòng di động |

- **Site Octets Mapping:** `BL` (`.1`), `NT` (`.2`), `HCM` (`.3`), `DC` (`.4`).

### Phase 10: Quality-Aware SD-WAN Controller
- **Kiến trúc phần mềm ([src/controller/sdwan/](file:///d:/KLTN/src/controller/sdwan/)):**
  1. `PathMonitor`: Chạy background thread probe ICMP liên tục đến các WAN Endpoint mỗi 3s để đo RTT, Jitter, Packet Loss.
  2. `PolicyEngine`: So sánh chỉ số đo được với yêu cầu SLA của từng Traffic Class:
     - **VoIP:** Max Latency 50ms, Max Loss 1.0%, Max Jitter 10ms → Ưu tiên: `MPLS` → `5G` → `INET`.
     - **Database:** Max Latency 100ms, Max Loss 0.5% → Ưu tiên: `MPLS` → `5G`.
     - **Web Traffic:** Max Latency 200ms → Ưu tiên: `INET` → `MPLS` → `5G`.
     - **Bulk/Backup:** Accept High Latency → Ưu tiên: `LTE` → `VPN` → `INET`.
  3. `TrafficSteerer`: Điều phối luồng bằng cách thay đổi bảng định tuyến `ip route` trên các Gateway Routers mà không gây ngắt kết nối TCP.
  4. `SDWANController REST API`: Flask server lắng nghe tại port `7070` cung cấp các API endpoint:
     - `GET /api/status`: Lấy trạng thái sức khỏe 5 kênh WAN.
     - `POST /api/steer`: Cho phép AI Engine phát lệnh cưỡng bức ép luồng qua Path chỉ định.
     - `GET /api/events`: Lịch sử các sự kiện chuyển mạch đường truyền.

### Phase 11: QoS Traffic Classification & Asterisk VoIP PBX
- **Cấu hình QoS & Phân loại lưu lượng (Traffic Classification):**
  - **File cấu hình:** [qos.yaml](file:///d:/KLTN/src/config/qos.yaml)
  - **Công cụ thực thi:** [configure_qos.py](file:///d:/KLTN/src/scripts/configure_qos.py) thi hành lệnh `iptables -t mangle` và `tc htb` trên các Gateway Routers.
  - **Đánh nhãn DSCP (MANGLE Table iptables):**
    - **VoIP Traffic:** Classify SIP (UDP 5060-5061) và RTP (UDP 10000-20000) → **DSCP EF** (Expedited Forwarding - 46, TOS `0xb8`).
    - **Database Traffic:** Classify MySQL (TCP 3306), PostgreSQL (TCP 5432), MongoDB (TCP 27017) → **DSCP AF21** (Assured Forwarding 21 - 18, TOS `0x48`).
    - **Web Traffic:** Classify HTTP/HTTPS (TCP 80, 443, 8080, 8443) → **DSCP AF11** (Assured Forwarding 11 - 10, TOS `0x28`).
    - **Monitoring & Telemetry:** Classify Prometheus / Metrics (TCP 9090, 9100, 9302, 7070) → **DSCP CS2** (Class Selector 2 - 16, TOS `0x40`).
    - **Default / Bulk / CCTV:** Tất cả lưu lượng còn lại → **DSCP BE** (Best Effort - 0, TOS `0x00`).
  - **Quản lý Hàng chờ Kênh truyền TC HTB (Hierarchical Token Bucket Queuing):**
    - Khởi tạo root qdisc HTB trên 5 kênh WAN interface (`WAN_MPLS`, `WAN_FIVEG`, `WAN_INET`, `WAN_VPN`, `WAN_LTE`).
    - Bảng phân bổ băng thông & độ ưu tiên hàng chờ HTB:

| Class ID | Traffic Class | DSCP / TOS | Guaranteed Rate | Ceiling Rate | Queue Priority | Qdisc Leaf |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `1:10` | **VoIP (Voice)** | `EF` (`0xb8`) | 30% Link BW | 80% Link BW | **1 (Cao nhất)** | `sfq perturb 10` |
| `1:20` | **Database (DB)** | `AF21` (`0x48`) | 30% Link BW | 70% Link BW | **2** | `sfq perturb 10` |
| `1:30` | **Web App** | `AF11` (`0x28`) | 25% Link BW | 90% Link BW | **3** | `sfq perturb 10` |
| `1:40` | **Mgmt / Mon** | `CS2` (`0x40`) | 10% Link BW | 30% Link BW | **4** | `sfq perturb 10` |
| `1:50` | **Default / Bulk**| `BE` (`0x00`) | 5% Link BW | 100% Link BW | **5 (Thấp nhất)** | `sfq perturb 10` |

- **Tổng đài Thoại Doanh nghiệp Asterisk SIP Server:**
  - **File cấu hình:** [sip.conf](file:///d:/KLTN/src/config/asterisk/sip.conf), [extensions.conf](file:///d:/KLTN/src/config/asterisk/extensions.conf)
  - **Công cụ triển khai:** [configure_asterisk.py](file:///d:/KLTN/src/scripts/configure_asterisk.py) chạy trong namespace `DC_APP01` (`10.100.20.11`).
  - **Sơ đồ Số máy lẻ (Dialplan Extension Scheme):**
    - `NT_PHN01` (`10.20.90.11`) → Ext **`1001`** (Nha Trang IP Phone 1)
    - `NT_PHN02` (`10.20.90.12`) → Ext **`1002`** (Nha Trang IP Phone 2)
    - `HCM_PHN01` (`10.30.97.11`) → Ext **`2001`** (HCM IP Phone 1)
    - `HCM_PHN02` (`10.30.97.12`) → Ext **`2002`** (HCM IP Phone 2)
  - **Codec:** Hỗ trợ `ulaw`, `alaw`, `g729`, `gsm` đảm bảo chất lượng thoại qua đường truyền WAN.

### Phase 14: Programmable SDN Controller (Faucet & OpenFlow 1.3)
- **Kiến trúc phần mềm ([src/controller/sdn/](file:///d:/KLTN/src/controller/sdn/)):**
  1. `FaucetController`: Quản lý daemon Faucet SDN Controller, gán OpenFlow Controller (`tcp:127.0.0.1:6653`) và giao thức `OpenFlow13` lên các OVS Switches (`BL_SW`, `NT_CORE`, `HCM_CORE`, `NT_ACC01`, `HCM_ACC01`).
  2. `FlowManager`: Tương tác với Faucet REST/Prometheus API (`http://localhost:9302`) để đọc chỉ số Flow Stats và điều khiển đóng/mở Port động (`set_port_state`).
  3. `OpenFlowAgent`: Cung cấp hàm cấp cao `block_host_port()` và `unblock_host_port()` cho AI Engine phục vụ phản ứng cách ly máy tính bị nhiễm vi-rút/tấn công mạng.

---

## 4. BẢNG MA TRẬN IP / GATEWAY / SERVICE TỔNG HỢP

| Node / Host Name | Site | IP Address / Subnet | Default Gateway | VLAN ID | Chức năng chính |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BL_GW** | BL | `10.10.x.1`, `172.16.x.1` | N/A | 10,30,35,50,99 | Host Gateway, OSPF, ACL Router |
| **BL_ADM01-03** | BL | `10.10.10.11-13/24` | `10.10.10.1` | 10 | PC Phòng Hành chính Bảo Lộc |
| **BL_CAM01-02** | BL | `10.10.35.11-12/24` | `10.10.35.1` | 35 | Camera An ninh Bảo Lộc |
| **NT_DIST01** | NT | `10.20.x.2/24` (`.1` VIP) | N/A | 110-199 | Master VRRP Router, OSPF |
| **NT_DIST02** | NT | `10.20.x.3/24` (`.1` VIP) | N/A | 110-199 | Backup VRRP Router, OSPF |
| **NT_ADM01-03** | NT | `10.20.10.11-13/24` | `10.20.10.1` | 110 | PC Administrative Nha Trang |
| **NT_PHN01-02** | NT | `10.20.90.11-12/24` | `10.20.90.1` | 190 | IP Phone Voip Nha Trang |
| **HCM_DIST01** | HCM | `10.30.x.2/24` (`.1` VIP) | N/A | 210-299 | Master VRRP Router, OSPF |
| **HCM_DIST02** | HCM | `10.30.x.3/24` (`.1` VIP) | N/A | 210-299 | Backup VRRP Router, OSPF |
| **HCM_ADM01-03** | HCM | `10.30.10.11-13/24` | `10.30.10.1` | 210 | PC Administrative HCM |
| **DC_SP_GW** | DC | `10.100.x.1`, `172.16.x.4`| N/A | 310-360 | DC Gateway Router, Firewall |
| **DC_WEB01** | DC | `10.100.10.11/24` | `10.100.10.1` | 310 | Web Server 01 (Backend LB) |
| **DC_WEB02** | DC | `10.100.10.12/24` | `10.100.10.1` | 310 | Web Server 02 (Backend LB) |
| **DC_APP01** | DC | `10.100.20.11/24` | `10.100.20.1` | 320 | App Server + HAProxy VIP (`.10`) + Asterisk SIP (`.11`) |
| **DC_DB01** | DC | `10.100.30.11/24` | `10.100.30.1` | 330 | MySQL / PostgreSQL Database |
| **DC_DNS01** | DC | `10.100.40.11/24` | `10.100.40.1` | 340 | DNS Enterprise Server |
| **DC_DHCP01** | DC | `10.100.40.12/24` | `10.100.40.1` | 340 | Primary DHCP Server |
| **DC_MGMT01** | DC | `10.100.60.11/24` | `10.100.60.1` | 360 | Chrony NTP Time Server |
| **HCM_PHN01-02**| HCM| `10.30.97.11-12/24` | `10.30.97.1` | 297 | IP Phone Voice HCM (Ext 2001-2002) |

---

## 5. QUY TRÌNH KHỞI CHẠY VÀ KIỂM THỬ (EXECUTION & TESTING GUIDE)

### 5.1 Khởi động Topology theo từng Phase
Để chạy thử nghiệm mạng đến một Phase mong muốn, sử dụng câu lệnh:

```bash
# Khởi động toàn bộ mạng đầy đủ đến Phase 14:
sudo python3 src/topology/enterprise_topo.py --phase 14

# Khởi động không mở CLI (dùng cho test tự động):
sudo python3 src/topology/enterprise_topo.py --phase 14 --no-cli
```

### 5.2 Bộ Test Script Kiểm tra Tự động (Phase Check Unit Tests)
Tất cả các phase kiểm tra tự động đã được lập trình trong thư mục [src/tests/phase_checks/](file:///d:/KLTN/src/tests/phase_checks/):

```bash
# Test Phase 1: L2 Topology Build
sudo python3 src/tests/phase_checks/check_phase1.py

# Test Phase 2: VLAN Tagging
sudo python3 src/tests/phase_checks/check_phase2.py

# Test Phase 4: Dynamic OSPF Routing
sudo python3 src/tests/phase_checks/check_phase4.py

# Test Phase 5: VRRP Redundancy
sudo python3 src/tests/phase_checks/check_phase5.py

# Test Phase 7: ACL & Firewall Rules
sudo python3 src/tests/phase_checks/check_phase7.py

# Test Phase 8: HAProxy Load Balancing
sudo python3 src/tests/phase_checks/check_phase8.py

# Test Phase 9: WAN 5-Path Emulation Latency/Loss
sudo python3 src/tests/phase_checks/check_phase9.py

# Test Phase 10: SD-WAN Controller REST API & Steering
sudo python3 src/tests/phase_checks/check_phase10.py

# Test Phase 11: QoS DSCP Marking & Asterisk VoIP Server
sudo python3 src/tests/phase_checks/check_phase11.py

# Test Phase 14: SDN Faucet Controller & OpenFlow Binding
sudo python3 src/tests/phase_checks/check_phase14.py
```

---

## 6. LỘ TRÌNH VÀ KIẾN TRÚC TỰ PHỤC HỒI THÔNG MINH (PHASE 11 - PHASE 21)

Sau khi hoàn thành hạ tầng Topology mạng doanh nghiệp (Phase 1 đến Phase 14), hệ thống sẽ tiến hành tích hợp các Phase tiếp theo để xây dựng **Vòng lặp Tự phục hồi Thông minh (Self-Healing Loop)**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SELF-HEALING CLOSED-LOOP (PHASE 20)                   │
│                                                                             │
│   ┌───────────────────┐    Prometheus / Syslog   ┌──────────────────────┐   │
│   │ Network Topology  │ ───────────────────────> │  Phase 12 / 12B:     │   │
│   │ (Mininet Phase 1-14)                         │  Monitoring & NOC    │   │
│   └─────────▲─────────┘                          └──────────┬───────────┘   │
│             │                                               │               │
│    REST API │ Enforce Policy                      Alerts    │ Telemetry     │
│  (:7070 / :9302)                                            ▼               │
│   ┌─────────┴─────────┐                          ┌──────────────────────┐   │
│   │ Phase 18:         │                          │ Phase 13 / 15 / 16:  │   │
│   │ AI ↔ Controller   │ <─────────────────────── │ AI Anomaly Detection │   │
│   │ Integration       │     Recovery Action      │ & Root Cause (RCA)   │   │
│   └───────────────────┘                          └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Trạng thái các Phase:

#### ✅ Phase 11 — QoS Traffic Classification & Asterisk VoIP PBX `[Đã hoàn thành]`

> Chi tiết kỹ thuật đầy đủ tại: **[Section 3 → Phase 11](#phase-11-qos-traffic-classification--asterisk-voip-pbx)**

**A. QoS DSCP Marking (iptables mangle table trên 4 Gateway Routers):**

| Traffic Class | Giao thức / Port | DSCP | TOS Byte | Ưu tiên |
| :--- | :--- | :--- | :--- | :--- |
| **VoIP** | SIP UDP 5060-5061, RTP UDP 10000-20000 | **EF (46)** | `0xb8` | Cao nhất |
| **Database** | MySQL TCP 3306, PG TCP 5432, Mongo TCP 27017 | **AF21 (18)** | `0x48` | Cao |
| **Web App** | HTTP/HTTPS TCP 80/443/8080/8443 | **AF11 (10)** | `0x28` | Trung bình |
| **Monitoring** | Prometheus TCP 9090/9100/9302/7070 | **CS2 (16)** | `0x40` | Thấp |
| **Bulk/CCTV** | Tất cả còn lại | **BE (0)** | `0x00` | Thấp nhất |

**B. TC HTB Queuing (Hierarchical Token Bucket trên 5 WAN interfaces):**

| HTB Class | Traffic | Guaranteed BW | Ceiling BW | Priority |
| :--- | :--- | :--- | :--- | :--- |
| `1:10` | VoIP | 30% | 80% | **1** (cao nhất) |
| `1:20` | Database | 30% | 70% | **2** |
| `1:30` | Web App | 25% | 90% | **3** |
| `1:40` | Mgmt/Mon | 10% | 30% | **4** |
| `1:50` | Bulk/Default | 5% | 100% | **5** (thấp nhất) |

**C. Asterisk SIP PBX Server (chạy trong namespace `DC_APP01` — `10.100.20.11`):**
- Dialplan: Nha Trang `NT_PHN01/02` → Ext **1001/1002** | HCM `HCM_PHN01/02` → Ext **2001/2002**
- Codec: `ulaw`, `alaw`, `g729`, `gsm`
- DNS: `sip.enterprise.local` → `10.100.20.11`

**Files đã triển khai:**
- [qos.yaml](file:///d:/KLTN/src/config/qos.yaml) · [configure_qos.py](file:///d:/KLTN/src/scripts/configure_qos.py)
- [sip.conf](file:///d:/KLTN/src/config/asterisk/sip.conf) · [extensions.conf](file:///d:/KLTN/src/config/asterisk/extensions.conf) · [configure_asterisk.py](file:///d:/KLTN/src/scripts/configure_asterisk.py)
- [check_phase11.py](file:///d:/KLTN/src/tests/phase_checks/check_phase11.py)

---

#### 🔲 Phase 12 & 12B — Monitoring + Telemetry & NOC Dashboard `[Chưa làm]`
- Cài đặt Node Exporters và Prometheus để cào thông số băng thông, latency, CPU/RAM, flow table realtime.
- Xây dựng NOC Dashboard giao diện Web (Flask + SocketIO) hiển thị sơ đồ mạng động và cảnh báo sự cố.

#### 🔲 Phase 13 — Event Correlation Engine `[Chưa làm]`
- Gom tụ và lọc nhiễu log Syslog/Prometheus alerts, tạo bối cảnh sự cố phục vụ AI.

#### 🔲 Phase 15 — AI Anomaly Detection Engine `[Chưa làm]`
- Xây dựng mô hình Machine Learning (Autoencoder / Isolation Forest) phát hiện sớm suy hao kênh truyền WAN và bất thường băng thông.

#### 🔲 Phase 16 — AI Root Cause Analysis (RCA Engine) `[Chưa làm]`
- Xác định chính xác nguyên nhân gốc rễ (Lỗi cáp vật lý, vỡ đường truyền WAN, đứt link OSPF, hay sập server dịch vụ).

#### 🔲 Phase 17 — Recovery Decision Engine `[Chưa làm]`
- Ma trận quyết định hành động khôi phục (Switch WAN path, Mở/Khóa Port SDN Faucet, Chuyển hướng Load Balancer).

#### 🔲 Phase 18 — AI ↔ Controller Integration `[Chưa làm]`
- Kết nối AI Engine với SD-WAN Controller API (Port `7070`) và SDN Faucet API (Port `9302`).

#### 🔲 Phase 19 — Fault Injection Framework `[Chưa làm]`
- Bộ công cụ giả lập tự động **12 kịch bản sự cố thực tế** (F01–F12: Đứt cáp MPLS, sập WEB01, nghẽn 5G, bão broadcast,...).

#### 🔲 Phase 20 — Full Self-Healing Closed-Loop Integration `[Chưa làm]`
- Khép kín vòng lặp tự động phục hồi end-to-end không cần con người can thiệp.

#### 🔲 Phase 21 — Benchmarking & Evaluation `[Chưa làm]`
- Đánh giá các chỉ số hiệu năng: MTTR (Mean Time To Recovery < 10s), Packet Loss Recovery, Overhead của AI Engine.

---
*Tài liệu kỹ thuật này được tự động cập nhật và đồng bộ theo mã nguồn thực thi của dự án KLTN.*

