# Kế hoạch & Tài liệu Phase 0–6

> **Dự án:** Mạng Doanh Nghiệp Tự Phục Hồi sử dụng SD-WAN và AI  
> **Công cụ:** Mininet + OVS + FRRouting + keepalived + dnsmasq + chrony  
> **Môi trường chạy:** Ubuntu 20.04 / 22.04 (viết code trên Windows `d:\KLTN\src\`)

---

## 1. Tổng quan kiến trúc mạng

```
                    ┌──────────────────────────────────┐
                    │      NOC WEB DASHBOARD (UI)      │
                    │    Flask + SocketIO :5050         │
                    └──────────────┬───────────────────┘
                                   │ WebSocket Broadcast
                    ┌──────────────┴───────────────────┐
                    │       AI FAULT-RECOVERY           │
                    │  Telemetry → Detect → RCA → Act  │
                    └──────────────┬───────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
       SDN Controller                          SD-WAN Controller
      (Ryu — Phase 14)                    (Python tự viết — Phase 9)
              │                                         │
    ──────────┴──── ENTERPRISE LAN ────────────────────┴──────────
              │                                         │
    ┌─────────┼─────────┐                    ┌──────────┴──────────┐
    │         │         │                    │  5 WAN Transports   │
  Bảo Lộc  Nha Trang  HCM                  │  MPLS│Internet│LTE  │
   Flat     3-Tier    3-Tier                │       │5G│VPN        │
              │                             └──────────────────────┘
              └─────────────────────────────────────┐
                                               DATA CENTER
                                              Spine / Leaf
                                          WEB / APP / DB / INFRA
```

### Các site

| Site | Model | Switch | Hosts | IP Range |
| --- | --- | --- | --- | --- |
| Bảo Lộc (BL) | Flat | 1x BL-SW | 16 endpoints | 10.10.0.0/16 |
| Nha Trang (NT) | 3-Tier | CORE + 2 DIST + 6 ACC | 26 endpoints | 10.20.0.0/16 |
| HCM | 3-Tier | CORE + 2 DIST + 6 ACC | 35 endpoints | 10.30.0.0/16 |
| Data Center (DC) | Spine-Leaf | 2 SPINE + 4 LEAF | 10 servers | 10.100.0.0/16 |
| **Tổng** | | **~22 switches** | **88 endpoints** | |

---

## 2. Cấu trúc thư mục `src/`

```
src/
├── README.md
├── requirements.txt
│
├── topology/                          ← Phase 1–6 (CORE)
│   ├── __init__.py
│   ├── enterprise_topo.py             ← ENTRY POINT chạy toàn bộ mạng
│   ├── sites/
│   │   ├── __init__.py
│   │   ├── baoloc.py                  ← BL flat site
│   │   ├── nhatrang.py                ← NT 3-tier + VRRP + OSPF
│   │   ├── hcm.py                     ← HCM 3-tier + VRRP + OSPF
│   │   └── datacenter.py              ← DC Spine-Leaf + DHCP/DNS/NTP
│   └── wan/
│       ├── __init__.py
│       └── wan_links.py               ← WAN stub (Phase 9 sẽ thêm tc netem)
│
├── config/                            ← Data-driven config (YAML)
│   ├── vlan.yaml                      ← 34 VLAN, 88 hosts, IP plan
│   ├── ospf.yaml                      ← FRR OSPF router config
│   ├── vrrp.yaml                      ← keepalived VRRP groups
│   └── services.yaml                  ← DHCP pools, DNS records, NTP
│
├── scripts/                           ← Code-gen scripts
│   ├── __init__.py
│   ├── generate_keepalived_conf.py    ← Tạo /tmp/keepalived_*.conf
│   └── generate_dnsmasq_configs.py    ← Tạo /tmp/dnsmasq_*.conf
│
├── tests/
│   └── phase_checks/
│       ├── __init__.py
│       ├── check_phase1.py            ← Verify topology + L2 ping
│       ├── check_phase2.py            ← VLAN isolation + IP
│       ├── check_phase3.py            ← RSTP convergence
│       ├── check_phase4.py            ← OSPF neighbors + inter-site
│       ├── check_phase5.py            ← VRRP failover < 5s
│       └── check_phase6.py            ← DHCP/DNS/NTP
│
├── controller/                        ← Phase 14+ (SDN/SD-WAN)
├── ai_engine/                         ← Phase 15+ (AI)
├── noc/                               ← Phase 12B (NOC Dashboard)
├── traffic/                           ← Phase 10 (Traffic generator)
├── fault_injection/                   ← Phase 20 (F01–F12)
├── evaluation/                        ← Phase 21 (Metrics)
└── data/                              ← Training data, models, logs
```

---

## 3. Cài đặt môi trường (Ubuntu 20.04/22.04)

### 3.1 Cài đặt một lần

```bash
# ── Mininet + OVS ────────────────────────────────────────
sudo apt update && sudo apt install -y \
    mininet \
    openvswitch-switch \
    openvswitch-testcontroller

# ── FRRouting (OSPF daemon) ───────────────────────────────
sudo apt install -y frr frr-pythontools
# Bật OSPF daemon
sudo sed -i 's/ospfd=no/ospfd=yes/' /etc/frr/daemons
sudo systemctl restart frr

# ── VRRP ─────────────────────────────────────────────────
sudo apt install -y keepalived

# ── DHCP + DNS ────────────────────────────────────────────
sudo apt install -y dnsmasq

# ── NTP ───────────────────────────────────────────────────
sudo apt install -y chrony

# ── Công cụ đo lường ─────────────────────────────────────
sudo apt install -y iperf3 tcpdump net-tools iproute2

# ── Python dependencies ───────────────────────────────────
pip3 install -r requirements.txt
```

### 3.2 Xác nhận cài đặt

```bash
# Kiểm tra tự động
sudo python3 topology/enterprise_topo.py --phase 0
```

Nếu thấy `✓` tất cả thì môi trường OK.

---

## 4. VLAN & IP Plan

### 4.1 Bảo Lộc — Flat Network

| VLAN | Tên | Subnet | Gateway | Hosts |
| --- | --- | --- | --- | --- |
| 10 | USER | 10.10.10.0/24 | 10.10.10.1 | BL-ADMIN-PC01..03, BL-SALES-PC01..03, BL-ACC-PC01..03, BL-IT-PC01..03 |
| 30 | IoT | 10.10.30.0/24 | 10.10.30.1 | BL-PRN01, BL-PRN02 |
| 35 | CCTV | 10.10.35.0/24 | 10.10.35.1 | BL-CAM01, BL-CAM02 |
| 50 | WIFI | 10.10.50.0/24 | 10.10.50.1 | BL-AP01 |
| 99 | MGMT | 10.10.99.0/24 | 10.10.99.1 | (management) |

**Router:** `BL-GW` (FRR OSPF, router-id: 10.10.99.1)

### 4.2 Nha Trang — 3-Tier

| VLAN | Phòng ban | Subnet | DHCP Pool |
| --- | --- | --- | --- |
| 110 | ADMIN | 10.20.10.0/24 | .100–.200 |
| 120 | SALES | 10.20.20.0/24 | .100–.200 |
| 130 | ACCOUNTING | 10.20.30.0/24 | .100–.200 |
| 140 | HR | 10.20.40.0/24 | .100–.200 |
| 150 | CUSTOMER | 10.20.50.0/24 | .100–.200 |
| 160 | IT | 10.20.60.0/24 | .100–.200 |
| 170 | IoT | 10.20.70.0/24 | — |
| 175 | CCTV | 10.20.75.0/24 | — |
| 180 | WIFI | 10.20.80.0/24 | — |
| 190 | VOICE | 10.20.90.0/24 | — |
| 199 | MGMT | 10.20.99.0/24 | — |

**VRRP:** NT-DIST01 (Master, priority 110) ↔ NT-DIST02 (Backup, priority 100), VIP = x.x.x.1

**Access switch assignment:**

| Switch | VLAN | Phòng ban |
| --- | --- | --- |
| NT-ACC01 | 110 | ADMIN |
| NT-ACC02 | 120 | SALES |
| NT-ACC03 | 130 | ACCOUNTING |
| NT-ACC04 | 140 | HR |
| NT-ACC05 | 150 | CUSTOMER |
| NT-ACC06 | 160,170,175,180,190 | IT+IoT+CCTV+WiFi+Voice |

### 4.3 HCM — 3-Tier (tương tự NT, 13 VLAN)

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

**VRRP:** HCM-DIST01 (Master) ↔ HCM-DIST02 (Backup), VIP = x.x.x.1

### 4.4 Data Center — Spine-Leaf

| VLAN | Tier | Subnet | Server | IP |
| --- | --- | --- | --- | --- |
| 310 | WEB | 10.100.10.0/24 | DC-WEB01, DC-WEB02 | .11, .12 |
| 320 | APP | 10.100.20.0/24 | DC-APP01, DC-APP02 | .11, .12 |
| 330 | DB | 10.100.30.0/24 | DC-DB01, DC-DB02 | .11, .12 |
| 340 | INFRA | 10.100.40.0/24 | DC-DNS01 (.11), DC-DHCP01 (.12) | — |
| 350 | MONITORING | 10.100.50.0/24 | DC-MON01 | .11 |
| 360 | MGMT | 10.100.60.0/24 | DC-MGMT01 (NTP) | .11 |

**LEAF assignment:**

| Leaf | VLAN | Servers |
| --- | --- | --- |
| DC-LEAF01 | 310 | DC-WEB01, DC-WEB02 |
| DC-LEAF02 | 320 | DC-APP01, DC-APP02 |
| DC-LEAF03 | 330 | DC-DB01, DC-DB02 |
| DC-LEAF04 | 340,350,360 | DC-DNS01, DC-DHCP01, DC-MON01, DC-MGMT01 |

---

## 5. OSPF Routing

FRRouting (FRR) chạy trong Mininet host namespace.

### 5.1 Router summary

| Router | Router-ID | Networks quảng bá | OSPF Area |
| --- | --- | --- | --- |
| BL-GW | 10.10.99.1 | 10.10.0.0/16 | 0 |
| NT-DIST01 | 10.20.10.2 | 10.20.0.0/16 | 0 |
| NT-DIST02 | 10.20.10.3 | 10.20.0.0/16 | 0 |
| HCM-DIST01 | 10.30.10.2 | 10.30.0.0/16 | 0 |
| HCM-DIST02 | 10.30.10.3 | 10.30.0.0/16 | 0 |
| DC-SPINE-GW | 10.100.99.1 | 10.100.0.0/16 | 0 |

### 5.2 WAN links (Phase 1–6, direct /30)

```
BL-GW       192.168.10.1/30 ──────── 192.168.10.2/30  HCM-DIST01
NT-DIST01   192.168.20.1/30 ──────── 192.168.20.2/30  HCM-DIST01
HCM-DIST01  192.168.30.1/30 ──────── 192.168.30.2/30  DC-SPINE-GW
```

> **Phase 9:** Thay thế bằng 5 OVS switch WAN với `tc netem` (MPLS/Internet/LTE/5G/VPN)

### 5.3 Kiểm tra OSPF

```bash
# Trong Mininet CLI:
mininet> NT-DIST01 vtysh -c "show ip ospf neighbor"
mininet> NT-DIST01 vtysh -c "show ip route ospf"
mininet> BL-GW vtysh -c "show ip ospf database"
```

---

## 6. VRRP (keepalived)

### 6.1 Nguyên lý

```
PC (default GW = VIP 10.20.10.1)
         │
         ▼
   ┌─────┴─────┐
   │   VIP     │  ← keepalived quản lý
   │10.20.10.1 │
   └─────┬─────┘
         │
    ┌────┴────┐
    │         │
NT-DIST01  NT-DIST02
(Master    (Backup
priority   priority
  110)       100)
```

- **Preempt = true**: Khi DIST01 phục hồi → tự động giành lại MASTER
- **advert_int = 1s**: VRRP advertisement mỗi 1 giây
- **Failover time**: < 3–5 giây (3× advert_int + buffer)

### 6.2 Generate config và chạy

```bash
# Bước 1: Generate keepalived config files
python3 scripts/generate_keepalived_conf.py
# → Tạo: /tmp/keepalived_NT_DIST01.conf
#         /tmp/keepalived_NT_DIST02.conf
#         /tmp/keepalived_HCM_DIST01.conf
#         /tmp/keepalived_HCM_DIST02.conf

# Bước 2: Trong Mininet, các DIST host tự chạy keepalived
# (gọi start_vrrp_nhatrang() và start_vrrp_hcm() trong enterprise_topo.py)
```

### 6.3 Kiểm tra VRRP

```bash
# Trong Mininet CLI:
mininet> NT-DIST01 ip addr show | grep "10.20.10.1"   # VIP có trên DIST01?
mininet> NT-ADMIN-PC01 ping -c 3 10.20.10.1           # VIP respond?

# Fault test thủ công:
mininet> NT-DIST01 kill $(cat /tmp/ka_dist01.pid)      # Kill keepalived
mininet> NT-ADMIN-PC01 ping -c 10 10.20.10.1           # Observe failover
```

---

## 7. DHCP + DNS + NTP (Phase 6)

### 7.1 Sơ đồ dịch vụ

```
Hosts (NT/HCM/BL)
     │
     │ DHCP Discover (broadcast → unicast relay)
     ▼
DIST01/02 (dhcrelay to both 10.100.40.12 & 10.100.40.13)
     │
     ├──────────────────────────┐
     │ Unicast relay            │ Unicast relay
     ▼                          ▼
DC-DHCP01 (10.100.40.12)   DC-DHCP02 (10.100.40.13)
(Primary Active)           (Standby / Failover)
     │
     │ DHCP Offer with: IP + GW + DNS (10.100.40.11) + NTP (10.100.60.11)
     ▼
Host nhận IP + biết địa chỉ DNS và NTP
     │
     ├──► DC-DNS01 (10.100.40.11) ← dnsmasq DNS
     │       Resolve: www.enterprise.local → 10.100.10.11
     │
     └──► DC-MGMT01 (10.100.60.11) ← chrony NTP
             Stratum 2, sync từ pool.ntp.org
```

### 7.2 Generate và chạy

```bash
# Bước 1: Generate dnsmasq config files
python3 scripts/generate_dnsmasq_configs.py
# → Tạo: /tmp/dnsmasq_dhcp.conf
#         /tmp/dnsmasq_dns.conf

# Bước 2: Các service tự start trong datacenter.py khi phase=6
# (gọi start_services_datacenter() trong enterprise_topo.py)
```

### 7.3 DNS Records

| FQDN | IP | Server |
| --- | --- | --- |
| www.enterprise.local | 10.100.10.11 | DC-WEB01 |
| app.enterprise.local | 10.100.20.11 | DC-APP01 |
| db.enterprise.local | 10.100.30.11 | DC-DB01 |
| dns.enterprise.local | 10.100.40.11 | DC-DNS01 |
| monitor.enterprise.local | 10.100.50.11 | DC-MON01 |
| sip.enterprise.local | 10.100.20.11 | DC-APP01 (VoIP) |
| noc.enterprise.local | 127.0.0.1 | NOC Dashboard |

### 7.4 Kiểm tra services

```bash
# DHCP: kiểm tra dnsmasq chạy trên DC-DHCP01
mininet> DC-DHCP01 cat /tmp/dnsmasq_dhcp.pid
mininet> DC-DHCP01 cat /tmp/dnsmasq_dhcp.leases   # Danh sách IP đã cấp

# DNS: resolve từ bất kỳ host
mininet> HCM-ADMIN-PC01 nslookup www.enterprise.local 10.100.40.11
mininet> HCM-ADMIN-PC01 dig @10.100.40.11 app.enterprise.local

# NTP: kiểm tra chrony trên DC-MGMT01
mininet> DC-MGMT01 chronyc tracking
mininet> NT-DIST01 ntpdate -q 10.100.60.11
```

---

## 8. Cách chạy (Step-by-step)

### 8.1 Lần đầu tiên (setup)

```bash
# 1. Copy code lên Linux (từ Windows sang Linux qua scp/git)
git clone <repo> /home/user/kltn
cd /home/user/kltn/src

# 2. Cài dependencies
sudo apt install -y mininet openvswitch-switch frr keepalived dnsmasq chrony iperf3
pip3 install -r requirements.txt

# 3. Bật OSPF trong FRR
sudo sed -i 's/ospfd=no/ospfd=yes/' /etc/frr/daemons
sudo systemctl restart frr

# 4. Kiểm tra môi trường
sudo python3 topology/enterprise_topo.py --phase 0
```

### 8.2 Chạy từng Phase (kiểm tra từng bước)

```bash
# Phase 1 — Chỉ build topology
sudo python3 topology/enterprise_topo.py --phase 1
# → Mininet CLI mở, gõ: pingall

# Phase 2 — + VLAN config
sudo python3 topology/enterprise_topo.py --phase 2

# Phase 3 — + STP (tự động khi --phase 2 vì stp=True trong OVS)
sudo python3 topology/enterprise_topo.py --phase 3

# Phase 4 — + OSPF (FRR)
sudo python3 topology/enterprise_topo.py --phase 4
# → Trong CLI: NT-DIST01 vtysh -c "show ip ospf neighbor"

# Phase 5 — + VRRP (cần generate config trước)
python3 scripts/generate_keepalived_conf.py
sudo python3 topology/enterprise_topo.py --phase 5
# → Trong CLI: NT-ADMIN-PC01 ping 10.20.10.1

# Phase 6 — Full (DHCP + DNS + NTP)
python3 scripts/generate_keepalived_conf.py
python3 scripts/generate_dnsmasq_configs.py
sudo python3 topology/enterprise_topo.py --phase 6
# → Trong CLI: HCM-ADMIN-PC01 nslookup www.enterprise.local 10.100.40.11
```

### 8.3 Chạy nhanh (full Phase 6 + auto test)

```bash
# Generate configs
python3 scripts/generate_keepalived_conf.py
python3 scripts/generate_dnsmasq_configs.py

# Chạy full network + tự động pingall rồi thoát
sudo python3 topology/enterprise_topo.py --phase 6 --test-pingall

# Hoặc chạy không mở CLI (cho script automation)
sudo python3 topology/enterprise_topo.py --phase 6 --no-cli
```

### 8.4 Chạy riêng checkpoint từng phase

```bash
# Các script tự build topo + test + stop
sudo python3 tests/phase_checks/check_phase1.py   # ~30s
sudo python3 tests/phase_checks/check_phase2.py   # ~30s
sudo python3 tests/phase_checks/check_phase3.py   # ~60s (fault test)
sudo python3 tests/phase_checks/check_phase4.py   # ~60s
sudo python3 tests/phase_checks/check_phase5.py   # ~30s (failover test)
sudo python3 tests/phase_checks/check_phase6.py   # ~30s
```

---

## 9. Mininet CLI — Lệnh hữu dụng

```bash
# Xem tất cả nodes
mininet> nodes

# Xem tất cả links
mininet> links

# Ping tất cả (kiểm tra tổng thể)
mininet> pingall

# Ping từ host cụ thể
mininet> HCM-ADMIN-PC01 ping -c 3 10.100.10.11

# Chạy lệnh trên host
mininet> DC-DNS01 cat /tmp/dnsmasq_dns.pid
mininet> NT-DIST01 vtysh -c "show ip route"
mininet> NT-DIST01 ip addr show

# Xem OVS switch info
mininet> sh ovs-vsctl show
mininet> sh ovs-appctl stp/show NT-CORE

# Xem routing table của host
mininet> BL-ADMIN-PC01 ip route

# Dump traffic trên interface
mininet> DC-WEB01 tcpdump -i DC-WEB01-eth0 -n &

# Dừng tcpdump
mininet> DC-WEB01 kill %tcpdump

# Thoát CLI (dọn dẹp Mininet)
mininet> exit
```

---

## 10. Fault Injection thủ công (Preview Phase 20)

### F01 — Access Link Failure (RSTP test)

```bash
# Tắt link NT-ACC02 (SALES bị mất kết nối)
mininet> NT-ACC02 ip link set NT-ACC02-eth0 down

# Quan sát RSTP: traffic chuyển qua path dự phòng
mininet> NT-SALES-PC01 ping -c 10 10.100.10.11

# Khôi phục
mininet> NT-ACC02 ip link set NT-ACC02-eth0 up
```

### F02 — Distribution Failure (VRRP test)

```bash
# Kill DIST01 keepalived (VRRP failover)
mininet> NT-DIST01 kill $(cat /tmp/ka_dist01.pid)

# Quan sát VIP chuyển sang DIST02
mininet> NT-ADMIN-PC01 ping -c 10 10.20.10.1
# → Packet loss trong 1-3 giây, sau đó phục hồi

# Khôi phục DIST01
mininet> NT-DIST01 keepalived -f /tmp/keepalived_NT_DIST01.conf -p /tmp/ka_dist01.pid
```

### F03 — OSPF Link Failure

```bash
# Tắt WAN link BL ↔ HCM
mininet> BL-GW ip link set BL-GW-eth1 down

# Quan sát OSPF reconverge (BL mất route đến DC)
mininet> BL-ADMIN-PC01 ping 10.100.10.11

# Khôi phục
mininet> BL-GW ip link set BL-GW-eth1 up
```

---

## 11. STP Priority Summary

| Switch | STP Priority | Role |
| --- | --- | --- |
| BL-SW | 4096 | Root (single switch) |
| NT-CORE | 4096 | Root Bridge NT |
| NT-DIST01/02 | 8192 | Distribution |
| NT-ACC01..06 | 32768 | Access |
| HCM-CORE | 4096 | Root Bridge HCM |
| HCM-DIST01/02 | 8192 | Distribution |
| HCM-ACC01..06 | 32768 | Access |
| DC-SPINE01 | 4096 | Root Bridge DC |
| DC-SPINE02 | 8192 | Redundant Spine |
| DC-LEAF01..04 | 32768 | Leaf |

---

## 12. Troubleshooting

### Mininet không clean được

```bash
sudo mn -c        # Clean all Mininet state
sudo ovs-vsctl show   # Xem OVS còn bridge nào
```

### FRR không start

```bash
# Kiểm tra daemon config
cat /etc/frr/daemons | grep ospfd   # Phải là: ospfd=yes

# Restart FRR
sudo systemctl restart frr
sudo systemctl status frr

# Log FRR
sudo journalctl -u frr -f
```

### keepalived không start trong namespace

```bash
# Kiểm tra file config
cat /tmp/keepalived_NT_DIST01.conf

# Test keepalived syntax
keepalived -t -f /tmp/keepalived_NT_DIST01.conf

# Xem log
journalctl -u keepalived -n 50
```

### dnsmasq conflict port 53

```bash
# Tắt systemd-resolved (chiếm port 53)
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
```

### Lỗi "Address already in use" khi restart Mininet

```bash
sudo mn -c
sudo fuser -k 6633/tcp   # Kill controller port
```

---

## 13. Checkpoint Summary

| Phase | Nội dung | Checkpoint | File test |
| --- | --- | --- | --- |
| 0 | Kiểm tra môi trường | Tất cả tool cài OK | `--phase 0` |
| 1 | Build topology | Tất cả node up, L2 ping OK | `check_phase1.py` |
| 2 | VLAN + IP | Cùng VLAN ping được, khác VLAN bị chặn | `check_phase2.py` |
| 3 | RSTP | Link down → converge < 30s, không loop | `check_phase3.py` |
| 4 | OSPF | Inter-VLAN + inter-site ping OK, OSPF neighbor Full | `check_phase4.py` |
| 5 | VRRP | VIP .1 trả lời; DIST01 down → failover < 5s | `check_phase5.py` |
| 6 | DHCP/DNS/NTP | PC mới → DHCP IP → DNS resolve → NTP sync | `check_phase6.py` |

---

## 14. Ghi chú quan trọng

> **[QUAN TRỌNG] Code trên Windows → Chạy trên Linux**
> Copy `src/` lên máy Ubuntu qua `git`, `scp`, hoặc shared folder.
> Không chạy Mininet trực tiếp trên Windows.

> **[LƯU Ý] Thứ tự generate config**
> Luôn chạy `generate_keepalived_conf.py` và `generate_dnsmasq_configs.py`
> **trước** khi chạy `enterprise_topo.py --phase 5/6`.
> Các file `/tmp/*.conf` phải tồn tại.

> **[LƯU Ý] WAN Phase 1–6**
> Các site kết nối qua direct link (`192.168.x.x/30`), không có `tc netem`.
> Phase 9 sẽ thêm 5 OVS switch WAN với đặc tính MPLS/Internet/LTE/5G/VPN.

> **[TIP] Tiết kiệm RAM**
> Nếu máy Linux < 8GB RAM, có thể giảm số host bằng cách comment bớt
> host trong `config/vlan.yaml`. Enterprise topology đầy đủ (88 hosts)
> cần khoảng 4–6GB RAM.

---

*Tài liệu này được cập nhật lần cuối: 2026-09-06*  
*Phase tiếp theo: Phase 7 — ACL + Firewall + Segmentation*

