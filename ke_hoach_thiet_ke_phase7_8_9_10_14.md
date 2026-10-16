# KẾ HOẠCH THIẾT KẾ CHI TIẾT: PHASE 7, 8, 9, 10 VÀ 14
## Mục tiêu: Hoàn thiện Enterprise Topology (Topology Layer hoàn chỉnh)

> **Trạng thái đầu vào:** Phase 0–6 đã hoàn thành  
> → Topology + VLAN + RSTP + OSPF + VRRP + DHCP/DNS/NTP đang chạy  
> **Mục tiêu ra:** Phase 7→8→9→10→14 → Topology có đủ Security, DC Services, WAN thật sự, SD-WAN, SDN Controller để các Phase AI (15–21) có thể test end-to-end

---

## TỔNG QUAN 5 PHASE

```
Phase 7  │ ACL + Firewall         │ iptables rules trên Host Routers
Phase 8  │ DC Services (HAProxy)  │ Load balancing WEB01/02
Phase 9  │ WAN Transport (5 path) │ OVS WAN switches + tc netem
Phase 10 │ SD-WAN Controller      │ Python controller chọn đường WAN
Phase 14 │ SDN Controller (Faucet)│ OpenFlow điều khiển LAN switches
```

**Thứ tự bắt buộc:** `7 → 8 → 9 → 10 → (11,12,13 song song) → 14`  
Phase 9 là prerequisite của Phase 10 và Phase 14 (vì cần WAN path thật để SDN test reroute).

---

## PHASE 7 – ACL + Firewall + Network Segmentation

### Mục tiêu
Áp dụng chính sách bảo mật dùng `iptables` trên các Host Router (BL_GW, NT_DIST01/02, HCM_DIST01/02, DC_SP_GW).  
**Lý do quan trọng:** Đây là nền tảng để sau này AI có thể enforce/relax policy khi recovery.

### 7.1 ACL Rules Matrix

| Nguồn | Đích | Port | Action |
|-------|------|------|--------|
| USER VLAN (10.x.10.0/24) | WEB Server (10.100.10.0/24) | TCP 80,443 | ALLOW |
| WEB | APP Server (10.100.20.0/24) | TCP 8080 | ALLOW |
| APP | DB Server (10.100.30.0/24) | TCP 3306,5432 | ALLOW |
| USER | APP Server | TCP 8080 | ALLOW |
| CCTV (*.35.0/24) | DB Server | ANY | **DENY** |
| IoT (*.30.0/24) | USER VLAN | ANY | **DENY** |
| VOICE (*.90.0/24) | SIP Server (10.100.20.11) | TCP/UDP 5060 | ALLOW |
| ANY | ANY | ANY | DROP (default) |

### 7.2 Firewall Zones trên DC_SP_GW

```
Zone: WAN → DMZ (VLAN 310 WEB)
  - ALLOW TCP 80, 443 inbound
Zone: DMZ → APP (VLAN 320)
  - ALLOW TCP 8080 from 10.100.10.0/24
Zone: APP → DB (VLAN 330)
  - ALLOW TCP 3306, 5432 from 10.100.20.0/24
Zone: WAN → Internal
  - DENY default
```

### 7.3 Files cần tạo

```
src/
├── config/
│   └── acl_rules.yaml          # (MỚI) Định nghĩa rules dạng YAML
├── scripts/
│   └── configure_acl.py        # (MỚI) Script apply iptables rules
└── tests/
    └── phase_checks/
        └── check_phase7.py     # (MỚI) Test script
```

**Sửa:**
- `src/topology/enterprise_topo.py`: Thêm `phase 7` block gọi `configure_acl()`

### 7.4 Cấu trúc `config/acl_rules.yaml`

```yaml
# acl_rules.yaml
version: "1.0"
default_policy: DROP

# Zones
zones:
  user: ["10.10.10.0/24", "10.20.10.0/24", "10.30.10.0/24"]
  iot:  ["10.10.30.0/24", "10.20.70.0/24", "10.30.90.0/24"]
  cctv: ["10.10.35.0/24", "10.20.75.0/24", "10.30.95.0/24"]
  voice: ["10.10.40.0/24", "10.20.90.0/24", "10.30.97.0/24"]
  dc_web: ["10.100.10.0/24"]
  dc_app: ["10.100.20.0/24"]
  dc_db:  ["10.100.30.0/24"]

rules:
  - id: ACL_01
    name: "USER_to_WEB"
    src_zone: user
    dst_zone: dc_web
    proto: tcp
    dport: [80, 443]
    action: ACCEPT

  - id: ACL_02
    name: "WEB_to_APP"
    src_zone: dc_web
    dst_zone: dc_app
    proto: tcp
    dport: [8080]
    action: ACCEPT

  - id: ACL_03
    name: "APP_to_DB"
    src_zone: dc_app
    dst_zone: dc_db
    proto: tcp
    dport: [3306, 5432]
    action: ACCEPT

  - id: ACL_04
    name: "DENY_CCTV_to_DB"
    src_zone: cctv
    dst_zone: dc_db
    proto: any
    action: DROP
    log: true

  - id: ACL_05
    name: "DENY_IoT_to_USER"
    src_zone: iot
    dst_zone: user
    proto: any
    action: DROP

  - id: ACL_06
    name: "ALLOW_VOICE_SIP"
    src_zone: voice
    dst_zone: dc_app
    proto: [tcp, udp]
    dport: [5060, 10000-20000]
    action: ACCEPT

  - id: ACL_07
    name: "ALLOW_OSPF_MGMT"
    proto: [ospf, icmp]
    src: any
    dst: any
    action: ACCEPT

  # Monitoring phải thông
  - id: ACL_08
    name: "ALLOW_MGMT_MONITORING"
    dst_zone: ["10.100.50.0/24", "10.100.60.0/24"]
    proto: [tcp, icmp]
    action: ACCEPT
```

### 7.5 Skeleton `scripts/configure_acl.py`

```python
"""
configure_acl.py
Phase 7 - Áp dụng ACL rules dùng iptables trên Host Routers
"""
import yaml, os, subprocess

def load_rules(config_path='config/acl_rules.yaml'):
    with open(config_path) as f:
        return yaml.safe_load(f)

def _iptables(host, rule: str):
    """Thực thi iptables command trong namespace của host"""
    host.cmd(f'iptables {rule}')

def apply_acl_rules(router_host, rules_cfg, router_role='dist'):
    """
    Áp dụng ACL rules trên 1 Host Router.
    
    router_role: 'dist' | 'gw' | 'dc_gw'
    """
    host = router_host
    
    # Flush existing rules
    _iptables(host, '-F FORWARD')
    _iptables(host, '-P FORWARD ACCEPT')  # Default ACCEPT trước
    
    # Enable IP forwarding
    host.cmd('sysctl -w net.ipv4.ip_forward=1')
    
    for rule in rules_cfg['rules']:
        action = rule['action']  # ACCEPT hoặc DROP
        
        if rule.get('proto') == 'any':
            proto_flags = ''
        elif isinstance(rule.get('proto'), list):
            # Multiple protocols → multiple rules
            protos = rule['proto']
        else:
            protos = [rule.get('proto', 'tcp')]
        
        for src in rule.get('src_zone', ['0.0.0.0/0']):
            for dst in rule.get('dst_zone', ['0.0.0.0/0']):
                base = f'-A FORWARD -s {src} -d {dst}'
                if rule.get('dport'):
                    for port in rule['dport']:
                        _iptables(host, f'{base} -p tcp --dport {port} -j {action}')
                else:
                    _iptables(host, f'{base} -j {action}')
        
        if rule.get('log'):
            _iptables(host, f'-A FORWARD -s {src} -d {dst} -j LOG --log-prefix "ACL_{rule["id"]}: "')

def configure_all_acl(topo_nodes):
    """Gọi từ enterprise_topo.py phase 7"""
    rules_cfg = load_rules()
    
    # Apply trên BL_GW
    apply_acl_rules(topo_nodes['bl_nodes']['gw'], rules_cfg, 'gw')
    
    # Apply trên NT DIST01/02
    for dist in topo_nodes['nt_nodes']['dist'].values():
        apply_acl_rules(dist, rules_cfg, 'dist')
    
    # Apply trên HCM DIST01/02
    for dist in topo_nodes['hcm_nodes']['dist'].values():
        apply_acl_rules(dist, rules_cfg, 'dist')
    
    # Apply firewall zone trên DC_SP_GW
    apply_acl_rules(topo_nodes['dc_nodes']['gw'], rules_cfg, 'dc_gw')
    
    print('[PHASE 7] ✓ ACL + Firewall rules applied on all routers')
```

### 7.6 Tích hợp vào `enterprise_topo.py`

```python
# Thêm vào build_network() sau phase 6:
if phase >= 7:
    info('\n[PHASE 7] Áp dụng ACL + Firewall rules...\n')
    from scripts.configure_acl import configure_all_acl
    configure_all_acl({
        'bl_nodes': topo.bl_nodes,
        'nt_nodes': topo.nt_nodes,
        'hcm_nodes': topo.hcm_nodes,
        'dc_nodes': topo.dc_nodes,
    })
    info('[PHASE 7] ✓ ACL done\n')
    if phase < 8:
        return topo
```

### 7.7 Checkpoint kiểm tra

```bash
# Test ACL_04: CCTV không ping được DB
mininet> BL_CAM01 ping -c 3 10.100.30.11  # → 100% packet loss

# Test ACL_05: IoT không ping được USER VLAN
mininet> BL_PRN01 ping -c 3 10.20.10.11   # → 100% packet loss

# Test ACL_01: PC vẫn ping được WEB server
mininet> BL_ADM01 ping -c 3 10.100.10.11  # → 0% packet loss

# Test log: kiểm tra DROP bị log
mininet> DC_SP_GW dmesg | grep "ACL_04"
```

**Thời gian ước tính:** 3-5 ngày

---

## PHASE 8 – Data Center Services (Load Balancing + HAProxy)

### Mục tiêu
Triển khai HAProxy load balancer cho WEB servers. Đây là điều kiện cho scenario **F11 (WEB server failure)** trong Phase 19.

### 8.1 Kiến trúc Load Balancing

```
Client (HCM-ADMIN-PC01)
         ↓ HTTP GET www.enterprise.local
    DNS: 10.100.10.10 (VIP HAProxy)
         ↓
  DC_APP01 chạy HAProxy
  ┌───────────────────────┐
  │  HAProxy (port 80)    │
  │  VIP: 10.100.10.10    │
  │  Backend pool:        │
  │  → DC_WEB01 :80 (10.100.10.11) weight 1 │
  │  → DC_WEB02 :80 (10.100.10.12) weight 1 │
  │  Health: HTTP GET /health every 2s      │
  └───────────────────────┘
```

> **Lý do dùng DC_APP01 làm LB:** DC_APP01 có IP 10.100.20.11, cần thêm alias IP 10.100.10.10 (VIP).  
> Hoặc cần tạo thêm node `DC_LB01` dùng riêng. Khuyến nghị dùng DC_APP01 để tiết kiệm RAM.

### 8.2 Files cần tạo

```
src/
├── config/
│   └── haproxy.cfg.j2          # (MỚI) Jinja2 template HAProxy config
├── scripts/
│   ├── configure_haproxy.py    # (MỚI) Sinh config + start HAProxy
│   └── setup_webservers.py     # (MỚI) Start simple HTTP servers trên WEB01/02
└── tests/
    └── phase_checks/
        └── check_phase8.py     # (MỚI)
```

**Sửa:**
- `src/config/vlan.yaml`: Thêm VIP `10.100.10.10` vào DNS records (dc section)
- `src/topology/enterprise_topo.py`: Thêm phase 8 block

### 8.3 HAProxy Config Template

```
# /tmp/haproxy.cfg (sinh động trong namespace DC_APP01)
global
    log /dev/log local0
    maxconn 4096
    daemon

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms
    option  httpchk GET /health

frontend web_frontend
    bind 10.100.10.10:80
    default_backend web_backend

backend web_backend
    balance roundrobin
    option  httpchk GET /health HTTP/1.1\r\nHost:\ health
    server  web01 10.100.10.11:80 check inter 2s fall 3 rise 2
    server  web02 10.100.10.12:80 check inter 2s fall 3 rise 2

listen stats
    bind 10.100.10.10:8404
    stats enable
    stats uri /stats
    stats refresh 10s
```

### 8.4 Skeleton `scripts/configure_haproxy.py`

```python
"""
configure_haproxy.py
Phase 8 - Khởi động HAProxy load balancer trong namespace DC_APP01
"""
import os, time

HAPROXY_CFG = """
global
    maxconn 4096
    daemon

defaults
    mode http
    timeout connect 5s
    timeout client 50s
    timeout server 50s
    option httpchk GET /health

frontend web_frontend
    bind {vip}:80
    default_backend web_backend

backend web_backend
    balance roundrobin
    server web01 {web01_ip}:80 check inter 2s fall 3 rise 2
    server web02 {web02_ip}:80 check inter 2s fall 3 rise 2

listen stats
    bind {vip}:8404
    stats enable
    stats uri /stats
"""

SIMPLE_HTTP_SERVER = """#!/usr/bin/env python3
import http.server, socketserver, threading

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Hello from {hostname}')
    def log_message(self, *a): pass

with socketserver.TCPServer(('0.0.0.0', 80), Handler) as srv:
    srv.serve_forever()
"""

def start_web_servers(dc_nodes):
    """Khởi động simple HTTP servers trên WEB01 và WEB02."""
    for name in ['DC_WEB01', 'DC_WEB02']:
        host = dc_nodes['hosts'][name]
        script = SIMPLE_HTTP_SERVER.format(hostname=name)
        host.cmd(f"echo '{script}' > /tmp/webserver_{name}.py")
        host.cmd(f"python3 /tmp/webserver_{name}.py &")
    time.sleep(1)
    print('[PHASE 8] ✓ HTTP servers started on DC_WEB01, DC_WEB02')

def configure_haproxy(dc_nodes):
    """
    Khởi động HAProxy trên DC_APP01.
    VIP 10.100.10.10 được gán alias trên DC_APP01.
    """
    app01 = dc_nodes['hosts']['DC_APP01']
    vip = '10.100.10.10'
    
    # Gán VIP alias IP trên interface của DC_APP01
    app01_intf = [i.name for i in app01.intfList() if i.name != 'lo'][0]
    app01.cmd(f'ip addr add {vip}/24 dev {app01_intf} 2>/dev/null')
    
    # Sinh HAProxy config
    cfg = HAPROXY_CFG.format(
        vip=vip,
        web01_ip='10.100.10.11',
        web02_ip='10.100.10.12',
    )
    app01.cmd(f"cat > /tmp/haproxy.cfg << 'EOCFG'\n{cfg}\nEOCFG")
    
    # Khởi động HAProxy
    app01.cmd('haproxy -f /tmp/haproxy.cfg -p /tmp/haproxy.pid -D')
    time.sleep(2)
    print(f'[PHASE 8] ✓ HAProxy started on DC_APP01 (VIP: {vip}:80)')
    print(f'[PHASE 8]   Stats: http://{vip}:8404/stats')

def configure_dc_services_phase8(dc_nodes):
    """Entry point từ enterprise_topo.py"""
    start_web_servers(dc_nodes)
    configure_haproxy(dc_nodes)
```

### 8.5 Cập nhật DNS (generate_dnsmasq_configs.py)

Thêm record:
```
www.enterprise.local → 10.100.10.10  (HAProxy VIP, không đổi khi WEB01 down)
```

### 8.6 Checkpoint kiểm tra

```bash
# Test 1: Basic LB hoạt động
mininet> HCM_DIST01 curl http://10.100.10.10/health
# → OK

# Test 2: Failover
mininet> DC_WEB01 kill $(cat /tmp/webserver_pid)
# Đợi 6 giây (2s interval × 3 falls)
mininet> HCM_DIST01 curl http://10.100.10.10/
# → Vẫn trả về response từ DC_WEB02

# Test 3: HAProxy stats
mininet> DC_APP01 curl http://10.100.10.10:8404/stats
```

**Thời gian ước tính:** 3-4 ngày

---

## PHASE 9 – WAN Transport Emulation (5 Paths)

### Mục tiêu  
**Đây là phase quan trọng nhất về topology.** Thay thế direct links bằng 5 OVS WAN Switch với đặc tính khác nhau (emulate bằng `tc netem`).

### 9.1 Kiến trúc WAN sau Phase 9

```
                  ┌─ WAN_SW_MPLS ─┐
                  ├─ WAN_SW_INET  ─┤
BL_GW ─────────── ├─ WAN_SW_LTE   ─┤ ─────────── DC_SP_GW
NT_DIST01 ──────── ├─ WAN_SW_5G    ─┤ ─────────── (cũng kết nối NT, HCM)
HCM_DIST01 ─────── └─ WAN_SW_VPN  ─┘
```

**Nguyên lý:** Mỗi `WAN_SW_*` là OVS Switch L2. Các branch GW kết nối vào WAN switch. `tc netem` áp dụng trên interface của WAN switch.

### 9.2 Đặc tính 5 WAN Paths

| Path | Delay | Jitter | Loss | BW | DSCP Priority |
|------|-------|--------|------|----|----------------|
| MPLS | 20ms | 2ms | 0.1% | 100Mbps | Cao nhất |
| 5G | 15ms | 5ms | 0.3% | 200Mbps | Cao |
| Internet | 40ms | 10ms | 0.5% | 100Mbps | Trung bình |
| VPN | 50ms | 8ms | 0.8% | 50Mbps | Thấp |
| LTE | 60ms | 15ms | 1.0% | 30Mbps | Thấp nhất |

### 9.3 Sơ đồ kết nối chi tiết

```
BL_GW:
  eth-mpls  → WAN_SW_MPLS (port 1)
  eth-inet  → WAN_SW_INET (port 1)
  eth-lte   → WAN_SW_LTE  (port 1)
  eth-5g    → WAN_SW_5G   (port 1)
  eth-vpn   → WAN_SW_VPN  (port 1)

NT_DIST01:
  eth-mpls  → WAN_SW_MPLS (port 2)
  eth-inet  → WAN_SW_INET (port 2)
  ...

HCM_DIST01:
  eth-mpls  → WAN_SW_MPLS (port 3)
  ...

DC_SP_GW:
  eth-mpls  → WAN_SW_MPLS (port 4)
  ...
```

**IP Addressing WAN (mở rộng từ Phase 1-6):**

```
MPLS path (172.16.10.0/24):
  BL_GW:      172.16.10.1/24
  NT_DIST01:  172.16.10.2/24
  HCM_DIST01: 172.16.10.3/24
  DC_SP_GW:   172.16.10.4/24

Internet path (172.16.20.0/24):
  BL_GW:      172.16.20.1/24
  NT_DIST01:  172.16.20.2/24
  HCM_DIST01: 172.16.20.3/24
  DC_SP_GW:   172.16.20.4/24

LTE path (172.16.30.0/24): .1/.2/.3/.4
5G path  (172.16.40.0/24): .1/.2/.3/.4
VPN path (172.16.50.0/24): .1/.2/.3/.4
```

### 9.4 Files cần tạo/sửa

```
src/
├── topology/
│   └── wan/
│       ├── wan_links.py        # (SỬA TOÀN BỘ) Replace stub bằng 5-path WAN
│       └── wan_topo.py         # (MỚI) Định nghĩa 5 WAN switch + connections
├── scripts/
│   └── configure_wan.py        # (MỚI) Apply tc netem characteristics
├── config/
│   └── wan_paths.yaml          # (MỚI) Đặc tính từng path
└── tests/
    └── phase_checks/
        └── check_phase9.py     # (MỚI)
```

### 9.5 Skeleton `topology/wan/wan_topo.py`

```python
"""
wan_topo.py
Phase 9 - 5 WAN transport paths trong Mininet
Mỗi path = 1 OVS Switch riêng + tc netem trên interfaces
"""
from mininet.node import OVSSwitch

# Đặc tính 5 path
WAN_PATH_PROFILES = {
    'MPLS': {
        'delay': '20ms', 'jitter': '2ms', 'loss': '0.1%',
        'rate': '100mbit', 'subnet': '172.16.10'
    },
    '5G': {
        'delay': '15ms', 'jitter': '5ms', 'loss': '0.3%',
        'rate': '200mbit', 'subnet': '172.16.40'
    },
    'INET': {
        'delay': '40ms', 'jitter': '10ms', 'loss': '0.5%',
        'rate': '100mbit', 'subnet': '172.16.20'
    },
    'VPN': {
        'delay': '50ms', 'jitter': '8ms', 'loss': '0.8%',
        'rate': '50mbit', 'subnet': '172.16.50'
    },
    'LTE': {
        'delay': '60ms', 'jitter': '15ms', 'loss': '1.0%',
        'rate': '30mbit', 'subnet': '172.16.30'
    },
}

# IP cuối octet cho từng site
SITE_OCTET = {
    'BL':  1,
    'NT':  2,
    'HCM': 3,
    'DC':  4,
}

def build_wan_topology(net):
    """
    Tạo 5 OVS WAN switches.
    Trả về dict: {'WAN_SW_MPLS': sw, 'WAN_SW_5G': sw, ...}
    """
    wan_switches = {}
    dpid_base = 0xAA00
    
    for i, path_name in enumerate(WAN_PATH_PROFILES.keys()):
        sw_name = f'WAN_SW_{path_name}'
        dpid = f'{dpid_base + i:016x}'
        sw = net.addSwitch(
            sw_name,
            cls=OVSSwitch,
            failMode='standalone',
            stp=False,          # WAN switch không cần STP
            dpid=dpid
        )
        wan_switches[sw_name] = sw
    
    return wan_switches

def connect_sites_to_wan(net, wan_switches, bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """
    Kết nối 4 site GW vào 5 WAN switches.
    Mỗi site GW có 5 interfaces (1 per path).
    
    Returns: dict với tất cả link objects và interface names
    """
    site_gws = {
        'BL':  bl_nodes['gw'],
        'NT':  nt_nodes['dist']['NT_DIST01'],
        'HCM': hcm_nodes['dist']['HCM_DIST01'],
        'DC':  dc_nodes['gw'],
    }
    
    wan_links = {}  # Lưu link objects để configure tc netem sau
    
    for path_name, profile in WAN_PATH_PROFILES.items():
        sw_name = f'WAN_SW_{path_name}'
        sw = wan_switches[sw_name]
        subnet = profile['subnet']
        
        path_links = {}
        for site_code, gw_host in site_gws.items():
            octet = SITE_OCTET[site_code]
            
            # Tên interface (max 15 chars)
            gw_intf_name = f'{gw_host.name[:8]}_{path_name[:4].lower()}'
            sw_intf_name = f'sw_{path_name[:4].lower()}_{site_code.lower()}'
            
            lk = net.addLink(
                gw_host, sw,
                intfName1=gw_intf_name,
                intfName2=sw_intf_name
            )
            
            # Lưu để configure IP và tc netem sau start()
            path_links[site_code] = {
                'link': lk,
                'gw_intf': lk.intf1.name,
                'sw_intf': lk.intf2.name,
                'gw_ip': f'{subnet}.{octet}/24',
                'gw_host': gw_host,
                'sw': sw,
            }
        
        wan_links[path_name] = path_links
    
    return wan_links

def configure_wan_ips_and_netem(wan_links, wan_switches):
    """
    Sau net.start(): gán IP + apply tc netem trên mỗi path.
    Chạy trong Phase 9 (sau configure_baoloc, configure_nhatrang, v.v.)
    """
    for path_name, path_links in wan_links.items():
        profile = WAN_PATH_PROFILES[path_name]
        
        for site_code, link_info in path_links.items():
            gw_host = link_info['gw_host']
            gw_intf = link_info['gw_intf']
            gw_ip   = link_info['gw_ip']
            sw_intf = link_info['sw_intf']
            sw      = link_info['sw']
            
            # Gán IP cho GW interface
            gw_host.cmd(f'ip addr add {gw_ip} dev {gw_intf} 2>/dev/null')
            gw_host.cmd(f'ip link set {gw_intf} up')
            
            # Apply tc netem trên interface của WAN switch (egress từ GW)
            # Áp dụng trên cả 2 chiều bằng cách tc trên gw_intf và sw_intf
            delay  = profile['delay']
            jitter = profile['jitter']
            loss   = profile['loss']
            rate   = profile['rate']
            
            # tc trên GW → WAN_SW direction
            gw_host.cmd(f'tc qdisc del dev {gw_intf} root 2>/dev/null')
            gw_host.cmd(
                f'tc qdisc add dev {gw_intf} root handle 1: '
                f'netem delay {delay} {jitter} loss {loss} rate {rate}'
            )
            
            # tc trên WAN_SW → GW direction (reverse path)
            sw.cmd(f'tc qdisc del dev {sw_intf} root 2>/dev/null')
            sw.cmd(
                f'tc qdisc add dev {sw_intf} root handle 1: '
                f'netem delay {delay} {jitter} loss {loss} rate {rate}'
            )
        
        print(f'[WAN] {path_name}: delay={profile["delay"]}, '
              f'loss={profile["loss"]}, rate={profile["rate"]} ✓')

def get_active_path(path_name):
    """Helper: kiểm tra WAN path có active không (dùng trong SD-WAN)."""
    import subprocess
    sw_name = f'WAN_SW_{path_name}'
    result = subprocess.run(
        ['ovs-vsctl', 'get', 'bridge', sw_name, 'datapath_id'],
        capture_output=True, text=True
    )
    return result.returncode == 0
```

### 9.6 Sửa `wan_links.py` để gọi wan_topo.py

```python
"""
wan_links.py - Phase 9 Full Implementation
Thay thế stub cũ hoàn toàn
"""
from topology.wan.wan_topo import (
    build_wan_topology, connect_sites_to_wan,
    configure_wan_ips_and_netem
)

def connect_sites_wan(net, bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """Phase 9: Tạo 5 WAN switches + kết nối 4 sites."""
    print('[WAN] Phase 9: Building 5-path WAN topology...')
    
    # Bước 1: Tạo 5 WAN switches
    wan_switches = build_wan_topology(net)
    
    # Bước 2: Kết nối sites vào WAN switches
    wan_links = connect_sites_to_wan(
        net, wan_switches,
        bl_nodes, nt_nodes, hcm_nodes, dc_nodes
    )
    
    return {
        'wan_switches': wan_switches,
        'wan_links': wan_links,
    }

def configure_wan_ips(wan_info, bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """Phase 9: Gán IP + apply tc netem."""
    configure_wan_ips_and_netem(
        wan_info['wan_links'],
        wan_info['wan_switches']
    )
    
    # Thêm OSPF routes cho WAN networks
    _configure_ospf_wan_routes(wan_info, bl_nodes, nt_nodes, hcm_nodes, dc_nodes)
    
    print('[WAN] ✓ WAN 5-path topology configured')

def _configure_ospf_wan_routes(wan_info, bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """Thêm WAN subnets vào OSPF để route qua WAN paths."""
    gws = {
        'BL': bl_nodes['gw'],
        'NT': nt_nodes['dist']['NT_DIST01'],
        'HCM': hcm_nodes['dist']['HCM_DIST01'],
        'DC': dc_nodes['gw'],
    }
    
    wan_subnets = ['172.16.10.0/24', '172.16.20.0/24',
                   '172.16.30.0/24', '172.16.40.0/24', '172.16.50.0/24']
    
    for site_code, gw in gws.items():
        for subnet in wan_subnets:
            # Thêm vào OSPF nếu FRR đang chạy
            gw.cmd(
                f'vtysh -c "conf t" -c "router ospf" '
                f'-c "network {subnet} area 0" -c "end" 2>/dev/null'
            )
```

### 9.7 Tích hợp vào `enterprise_topo.py`

```python
# Thay đổi trong build_network():
# Phase 9: Thay đổi tham số args của connect_sites_wan và configure_wan_ips

# Trong phase >= 9 block:
if phase >= 9:
    info('\n[PHASE 9] Cấu hình WAN 5-path emulation...\n')
    # wan_links đã được tạo trong build phase, configure sau start()
    configure_wan_ips(topo.wan_links, ...)
    info('[PHASE 9] ✓ WAN 5-path done\n')
```

> **Lưu ý:** `connect_sites_wan()` vẫn được gọi trong phase 1 (build phase, trước net.start()).  
> `configure_wan_ips()` gọi sau net.start() với tc netem.

### 9.8 OSPF cập nhật cho 5 WAN paths

Mỗi GW cần advertise WAN subnets qua OSPF để các site biết route:
```
BL_GW advertises:
  10.10.0.0/16 (LAN)
  172.16.10.1, 172.16.20.1, ... (WAN interfaces)

NT_DIST01 advertises:
  10.20.0.0/16 (LAN)
  172.16.10.2, 172.16.20.2, ...
```

SD-WAN Controller (Phase 10) sẽ cài route tĩnh đúng path thay vì để OSPF quyết định.

### 9.9 Checkpoint kiểm tra

```bash
# Test MPLS path (delay ~20ms)
mininet> BL_ADM01 ping -c 10 -W 1 172.16.10.4  # Đến DC qua MPLS
# → RTT ~20ms

# Test LTE path (delay ~60ms)
mininet> BL_ADM01 ping -c 10 172.16.30.4
# → RTT ~60ms

# Kiểm tra tc qdisc
mininet> BL_GW tc qdisc show

# Test link down/up (fault inject)
mininet> WAN_SW_MPLS ip link set WAN_SW_MPLS-eth1 down
mininet> BL_ADM01 ping -c 5 172.16.10.4  # → Fail
mininet> WAN_SW_MPLS ip link set WAN_SW_MPLS-eth1 up  # → Recover
```

**Thời gian ước tính:** 5-7 ngày

---

## PHASE 10 – SD-WAN Controller (Python tự viết)

### Mục tiêu  
Xây dựng SD-WAN Controller có khả năng **tự động chọn đường WAN tốt nhất** dựa trên policy và health của 5 paths. Đây là **đóng góp khoa học của luận văn**.

### 10.1 Kiến trúc SD-WAN Controller

```
src/controller/sdwan/
├── __init__.py
├── sdwan_controller.py      # Main controller + REST API server
├── path_monitor.py          # Monitor 5 WAN paths realtime
├── policy_engine.py         # Đọc policy YAML → quyết định path
├── traffic_steerer.py       # Thực thi: cài ip route trên GW hosts
├── probes/
│   ├── __init__.py
│   └── wan_prober.py        # ICMP probe + iperf3 probe
└── models/
    ├── __init__.py
    ├── path_state.py        # Dataclass PathState
    └── traffic_class.py     # Enum TrafficClass
```

### 10.2 Datamodel

```python
# models/path_state.py
from dataclasses import dataclass, field
from enum import Enum
import time

class PathStatus(Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"  # UP nhưng không đạt SLA

@dataclass
class PathState:
    name: str           # 'MPLS', '5G', 'INET', 'VPN', 'LTE'
    status: PathStatus = PathStatus.UP
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    loss_pct: float = 0.0
    bandwidth_mbps: float = 0.0
    last_probe: float = field(default_factory=time.time)
    
    def meets_sla(self, max_latency, max_loss, max_jitter) -> bool:
        return (
            self.status == PathStatus.UP and
            self.latency_ms <= max_latency and
            self.loss_pct <= max_loss and
            self.jitter_ms <= max_jitter
        )

# models/traffic_class.py
class TrafficClass(Enum):
    VOIP = "voip"
    DATABASE = "database"
    WEB = "web"
    BULK = "bulk"
    CCTV = "cctv"
    BACKUP = "backup"

# SLA requirements per traffic class
SLA_REQUIREMENTS = {
    TrafficClass.VOIP:     {'max_latency': 50,  'max_loss': 1.0,  'max_jitter': 10},
    TrafficClass.DATABASE: {'max_latency': 100, 'max_loss': 0.5,  'max_jitter': 20},
    TrafficClass.WEB:      {'max_latency': 200, 'max_loss': 2.0,  'max_jitter': 50},
    TrafficClass.BULK:     {'max_latency': 500, 'max_loss': 5.0,  'max_jitter': 100},
    TrafficClass.CCTV:     {'max_latency': 300, 'max_loss': 2.0,  'max_jitter': 50},
    TrafficClass.BACKUP:   {'max_latency': 1000,'max_loss': 10.0, 'max_jitter': 200},
}

# Priority order per traffic class (fallback order)
PATH_PRIORITY = {
    TrafficClass.VOIP:     ['MPLS', '5G', 'INET', 'VPN', 'LTE'],
    TrafficClass.DATABASE: ['MPLS', '5G', 'INET', 'VPN', 'LTE'],
    TrafficClass.WEB:      ['MPLS', 'INET', '5G', 'VPN', 'LTE'],
    TrafficClass.BULK:     ['INET', 'LTE', '5G', 'VPN', 'MPLS'],
    TrafficClass.CCTV:     ['INET', 'LTE', '5G', 'VPN', 'MPLS'],
    TrafficClass.BACKUP:   ['LTE', 'VPN', 'INET', '5G', 'MPLS'],
}
```

### 10.3 Skeleton `path_monitor.py`

```python
"""
path_monitor.py
Monitor 5 WAN paths bằng ICMP probe mỗi 3 giây.
Update PathState cho policy_engine sử dụng.
"""
import threading, time, subprocess, statistics
from models.path_state import PathState, PathStatus

# Probe targets: IP của DC_SP_GW trên mỗi path
PATH_PROBE_TARGETS = {
    'MPLS': '172.16.10.4',
    'INET': '172.16.20.4',
    'LTE':  '172.16.30.4',
    '5G':   '172.16.40.4',
    'VPN':  '172.16.50.4',
}

class PathMonitor:
    def __init__(self, probe_interval=3.0, probe_count=5):
        self.probe_interval = probe_interval
        self.probe_count = probe_count
        self.path_states: dict[str, PathState] = {
            name: PathState(name=name) for name in PATH_PROBE_TARGETS
        }
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self.on_state_change = None  # Callback khi path thay đổi
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print('[PathMonitor] Started monitoring 5 WAN paths')
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def get_state(self, path_name) -> PathState:
        with self._lock:
            return self.path_states[path_name]
    
    def get_all_states(self) -> dict:
        with self._lock:
            return dict(self.path_states)
    
    def _monitor_loop(self):
        while self._running:
            for path_name, target_ip in PATH_PROBE_TARGETS.items():
                old_status = self.path_states[path_name].status
                new_state = self._probe_path(path_name, target_ip)
                
                with self._lock:
                    self.path_states[path_name] = new_state
                
                # Trigger callback nếu trạng thái thay đổi
                if old_status != new_state.status and self.on_state_change:
                    self.on_state_change(path_name, old_status, new_state.status)
            
            time.sleep(self.probe_interval)
    
    def _probe_path(self, path_name: str, target_ip: str) -> PathState:
        """Probe 1 path bằng ping, trả về PathState mới."""
        state = PathState(name=path_name)
        
        try:
            result = subprocess.run(
                ['ping', '-c', str(self.probe_count), '-W', '2', target_ip],
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode != 0:
                state.status = PathStatus.DOWN
                state.loss_pct = 100.0
                return state
            
            # Parse ping output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'packet loss' in line:
                    # "5 packets transmitted, 5 received, 0% packet loss"
                    parts = line.split(',')
                    loss_str = [p for p in parts if 'loss' in p][0]
                    state.loss_pct = float(loss_str.strip().split('%')[0])
                
                if 'rtt min/avg/max/mdev' in line:
                    # "rtt min/avg/max/mdev = 19.2/20.1/21.3/0.8 ms"
                    nums = line.split('=')[1].strip().split('/')
                    state.latency_ms = float(nums[1])   # avg
                    state.jitter_ms  = float(nums[3].split()[0])  # mdev
            
            # Đánh dấu DEGRADED nếu loss > 0 nhưng < 100
            if state.loss_pct > 5.0:
                state.status = PathStatus.DEGRADED
            else:
                state.status = PathStatus.UP
        
        except (subprocess.TimeoutExpired, Exception) as e:
            state.status = PathStatus.DOWN
            state.loss_pct = 100.0
        
        state.last_probe = time.time()
        return state
```

### 10.4 Skeleton `policy_engine.py`

```python
"""
policy_engine.py
Đọc policy YAML → quyết định path tốt nhất cho mỗi traffic class.
"""
import yaml
from models.path_state import PathStatus
from models.traffic_class import TrafficClass, SLA_REQUIREMENTS, PATH_PRIORITY

class PolicyEngine:
    def __init__(self, policy_path='config/sdwan_policy.yaml'):
        self.policy_path = policy_path
        self.policy = self._load_policy()
    
    def _load_policy(self):
        try:
            with open(self.policy_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}  # Dùng default SLA
    
    def select_best_path(
        self,
        traffic_class: TrafficClass,
        available_paths: dict  # {name: PathState}
    ) -> str | None:
        """
        Chọn path tốt nhất cho traffic_class.
        Returns: tên path ('MPLS', '5G', v.v.) hoặc None nếu không có path thỏa mãn.
        """
        sla = SLA_REQUIREMENTS[traffic_class]
        priority_order = PATH_PRIORITY[traffic_class]
        
        # Lọc paths đang UP và đạt SLA
        candidates = [
            name for name in priority_order
            if name in available_paths and
               available_paths[name].meets_sla(
                   sla['max_latency'],
                   sla['max_loss'],
                   sla['max_jitter']
               )
        ]
        
        if not candidates:
            # Fallback: chọn path UP có latency thấp nhất
            up_paths = [
                (name, state) for name, state in available_paths.items()
                if state.status == PathStatus.UP
            ]
            if not up_paths:
                return None
            return min(up_paths, key=lambda x: x[1].latency_ms)[0]
        
        return candidates[0]  # Candidate đầu tiên = priority cao nhất đạt SLA
    
    def evaluate_all_traffic(self, available_paths: dict) -> dict:
        """Đánh giá path cho tất cả traffic classes."""
        return {
            tc: self.select_best_path(tc, available_paths)
            for tc in TrafficClass
        }
```

### 10.5 Skeleton `traffic_steerer.py`

```python
"""
traffic_steerer.py
Thực thi path switching: thay đổi ip route trên GW hosts.
"""
import subprocess
from wan_topo import WAN_PATH_PROFILES, SITE_OCTET

# IP routing table prefix → path mapping
SITE_DESTINATIONS = {
    'BL':  '10.10.0.0/16',
    'NT':  '10.20.0.0/16',
    'HCM': '10.30.0.0/16',
    'DC':  '10.100.0.0/16',
}

class TrafficSteerer:
    def __init__(self, mininet_nodes):
        """
        mininet_nodes: dict với GW host objects
        {
          'BL': bl_gw_host,
          'NT': nt_dist01_host,
          'HCM': hcm_dist01_host,
          'DC': dc_sp_gw_host,
        }
        """
        self.gws = mininet_nodes
        self.current_paths = {}  # site → current active path name
    
    def steer_traffic(self, from_site: str, to_site: str, path_name: str):
        """
        Chuyển traffic từ from_site đến to_site qua path_name.
        Cập nhật ip route trên from_site GW.
        """
        gw = self.gws[from_site]
        dst_subnet = SITE_DESTINATIONS[to_site]
        profile = WAN_PATH_PROFILES[path_name]
        to_octet = SITE_OCTET[to_site]
        via_ip = f"{profile['subnet']}.{to_octet}"
        
        # Xóa route cũ
        gw.cmd(f'ip route del {dst_subnet} 2>/dev/null')
        
        # Cài route mới qua path được chọn
        gw.cmd(f'ip route add {dst_subnet} via {via_ip}')
        
        old_path = self.current_paths.get((from_site, to_site), 'None')
        self.current_paths[(from_site, to_site)] = path_name
        
        print(f'[Steerer] {from_site}→{to_site}: {old_path} → {path_name} (via {via_ip})')
    
    def steer_all_to_best(self, path_decisions: dict):
        """
        Áp dụng path decisions cho tất cả site pairs.
        path_decisions: {TrafficClass: path_name}
        """
        for (from_site, to_site), best_path in path_decisions.items():
            if best_path:
                self.steer_traffic(from_site, to_site, best_path)
```

### 10.6 `sdwan_controller.py` - Main Controller

```python
"""
sdwan_controller.py
SD-WAN Controller chính: orchestrate PathMonitor + PolicyEngine + TrafficSteerer.
Cung cấp REST API để AI Engine và NOC Dashboard tương tác.
"""
import threading, time
from flask import Flask, jsonify, request
from path_monitor import PathMonitor
from policy_engine import PolicyEngine
from traffic_steerer import TrafficSteerer
from models.traffic_class import TrafficClass

class SDWANController:
    def __init__(self, mininet_nodes, probe_interval=3.0, api_port=7070):
        self.monitor = PathMonitor(probe_interval=probe_interval)
        self.policy  = PolicyEngine()
        self.steerer = TrafficSteerer(mininet_nodes)
        self.api_port = api_port
        self._control_loop_thread = None
        self._running = False
        self.events = []  # Log path switching events
        
        # Flask REST API
        self.app = Flask(__name__)
        self._setup_routes()
    
    def start(self):
        """Khởi động controller: monitor + control loop + REST API."""
        self.monitor.start()
        self.monitor.on_state_change = self._on_path_change
        
        self._running = True
        self._control_loop_thread = threading.Thread(
            target=self._control_loop, daemon=True
        )
        self._control_loop_thread.start()
        
        # REST API in background thread
        threading.Thread(
            target=lambda: self.app.run(port=self.api_port, debug=False),
            daemon=True
        ).start()
        
        print(f'[SDWAN] Controller started (API: http://localhost:{self.api_port})')
    
    def _control_loop(self):
        """Main control loop: mỗi 5s đánh giá và steer traffic."""
        while self._running:
            time.sleep(5)
            states = self.monitor.get_all_states()
            decisions = self.policy.evaluate_all_traffic(states)
            
            # Steer all traffic pairs
            for tc, best_path in decisions.items():
                if best_path:
                    for from_site in ['BL', 'NT', 'HCM']:
                        self.steerer.steer_traffic(from_site, 'DC', best_path)
    
    def _on_path_change(self, path_name, old_status, new_status):
        """Callback khi path thay đổi trạng thái."""
        event = {
            'timestamp': time.time(),
            'path': path_name,
            'old_status': old_status.value,
            'new_status': new_status.value,
        }
        self.events.append(event)
        print(f'[SDWAN] Path {path_name}: {old_status.value} → {new_status.value}')
        
        # Trigger immediate re-evaluation
        states = self.monitor.get_all_states()
        decisions = self.policy.evaluate_all_traffic(states)
        for tc, best_path in decisions.items():
            if best_path and best_path != path_name:
                for from_site in ['BL', 'NT', 'HCM']:
                    self.steerer.steer_traffic(from_site, 'DC', best_path)
    
    def _setup_routes(self):
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            states = self.monitor.get_all_states()
            return jsonify({
                name: {
                    'status': s.status.value,
                    'latency_ms': s.latency_ms,
                    'jitter_ms': s.jitter_ms,
                    'loss_pct': s.loss_pct,
                }
                for name, s in states.items()
            })
        
        @self.app.route('/api/steer', methods=['POST'])
        def manual_steer():
            """AI Engine gọi để force chuyển path."""
            data = request.json
            self.steerer.steer_traffic(
                data['from_site'], data['to_site'], data['path']
            )
            return jsonify({'status': 'ok'})
        
        @self.app.route('/api/events', methods=['GET'])
        def get_events():
            return jsonify(self.events[-50:])  # 50 events gần nhất
```

### 10.7 `config/sdwan_policy.yaml`

```yaml
# sdwan_policy.yaml
version: "1.0"

# Override SLA nếu cần (optional, dùng default nếu thiếu)
sla_overrides: {}

# Traffic class → DSCP mapping (dùng khi áp dụng QoS Phase 11)
dscp_marking:
  voip: 46      # EF
  database: 18  # AF21
  web: 10       # AF11
  cctv: 0       # BE
  bulk: 0       # BE
  backup: 0     # BE

# Fallback policy khi tất cả paths đều DOWN
fallback:
  action: alert_noc
  message: "ALL WAN PATHS DOWN - manual intervention required"
```

### 10.8 Checkpoint kiểm tra

```bash
# Khởi động SD-WAN Controller
python3 src/controller/sdwan/sdwan_controller.py

# Test path status API
curl http://localhost:7070/api/status

# Test failover: inject MPLS fault
mininet> WAN_SW_MPLS ip link set WAN_SW_MPLS-eth1 down
# Sau 3s (probe interval):
curl http://localhost:7070/api/status
# → MPLS: DOWN; traffic đã chuyển sang 5G

# Test manual steer
curl -X POST http://localhost:7070/api/steer \
  -H 'Content-Type: application/json' \
  -d '{"from_site":"HCM","to_site":"DC","path":"5G"}'

# Kiểm tra route table sau steer
mininet> HCM_DIST01 ip route show
```

**Thời gian ước tính:** 7-10 ngày

---

## PHASE 14 – SDN Controller (Faucet + OpenFlow)

### Mục tiêu
Tích hợp Faucet SDN Controller để điều khiển **LAN switches** qua OpenFlow. Phase 14 là nền tảng để AI Engine cài flow rules vào switch (Phase 18).

### 14.1 Kiến trúc SDN trong Mininet

```
Faucet Controller (:6653 OpenFlow)
         ↕ OpenFlow 1.3
    ┌────────────────────────────────┐
    │  NT_CORE (dpid=0x01)           │
    │  HCM_CORE (dpid=0x02)          │
    │  BL_SW (dpid=0x03)             │
    │  NT_ACC01..06 (dpid=0x11..16)  │
    │  HCM_ACC01..06 (dpid=0x21..26) │
    └────────────────────────────────┘
```

> **Lưu ý quan trọng:** DIST01/02 là Mininet Host Router (không phải OVS Switch), nên **không** kết nối với Faucet. Chỉ CORE và ACC switches kết nối Faucet.

### 14.2 Phương án triển khai

**Phương án A: Faucet standalone** (khuyến nghị cho luận văn)
- Cài Faucet trên host Linux (ngoài Mininet)
- OVS switches kết nối về Faucet qua TCP 6653
- Faucet cung cấp REST API tại port 9302

**Phương án B: Ryu Controller** (tự viết)
- Viết Ryu app xử lý OpenFlow
- Linh hoạt hơn nhưng phức tạp hơn
- Phù hợp nếu muốn custom OpenFlow pipeline

**→ Chọn Phương án A (Faucet) vì có REST API sẵn, ổn định hơn.**

### 14.3 Files cần tạo

```
src/
├── config/
│   └── faucet.yaml             # (MỚI) Faucet topology config
├── controller/
│   └── sdn/
│       ├── __init__.py         # (SỬA) Cập nhật exports
│       ├── faucet_controller.py    # (MỚI) Wrapper quản lý Faucet process
│       ├── flow_manager.py         # (MỚI) CRUD flow rules qua Faucet REST API
│       └── openflow_agent.py       # (MỚI) Agent giao tiếp Faucet REST API
└── tests/
    └── phase_checks/
        └── check_phase14.py    # (MỚI)
```

**Sửa:**
- `src/topology/enterprise_topo.py`: Thêm phase 14 block (switch OVS sang Faucet mode)

### 14.4 `config/faucet.yaml`

```yaml
# faucet.yaml - Faucet SDN Controller topology config
# Chỉ định nghĩa CORE và ACC switches (không phải DIST vì DIST là Host Router)

vlans:
  # Bảo Lộc VLANs
  vlan10:  {vid: 10,  description: "BL USER"}
  vlan30:  {vid: 30,  description: "BL IoT"}
  vlan35:  {vid: 35,  description: "BL CCTV"}
  vlan50:  {vid: 50,  description: "BL WIFI"}
  # Nha Trang VLANs
  vlan110: {vid: 110, description: "NT ADMIN"}
  vlan120: {vid: 120, description: "NT SALES"}
  vlan130: {vid: 130, description: "NT ACCOUNTING"}
  vlan140: {vid: 140, description: "NT HR"}
  vlan150: {vid: 150, description: "NT MARKETING"}
  vlan160: {vid: 160, description: "NT CUSTOMER"}
  vlan170: {vid: 170, description: "NT TECHNICAL"}
  vlan175: {vid: 175, description: "NT IoT"}
  vlan180: {vid: 180, description: "NT CCTV"}
  vlan190: {vid: 190, description: "NT VOICE"}
  # HCM VLANs (210-297)
  vlan210: {vid: 210, description: "HCM ADMIN"}
  vlan220: {vid: 220, description: "HCM SALES"}
  # ... (tương tự)

dps:
  BL_SW:
    dp_id: 0x000000000003
    hardware: "Open vSwitch"
    interfaces:
      # Port 1-16: kết nối hosts (access ports)
      # Port 17: uplink đến BL_GW (trunk)
      1:
        name: to_bl_gw
        description: "Uplink to BL_GW router"
        tagged_vlans: [vlan10, vlan30, vlan35, vlan50]
      # Access ports sẽ được generate tự động
      
  NT_CORE:
    dp_id: 0x000000000001
    hardware: "Open vSwitch"
    interfaces:
      1:
        name: to_nt_dist01
        tagged_vlans: [vlan110, vlan120, vlan130, vlan140, vlan150,
                       vlan160, vlan170, vlan175, vlan180, vlan190]
      2:
        name: to_nt_dist02
        tagged_vlans: [vlan110, vlan120, vlan130, vlan140, vlan150,
                       vlan160, vlan170, vlan175, vlan180, vlan190]
      3:  {name: to_nt_acc01, tagged_vlans: [vlan110]}
      4:  {name: to_nt_acc02, tagged_vlans: [vlan120]}
      5:  {name: to_nt_acc03, tagged_vlans: [vlan130, vlan140]}
      6:  {name: to_nt_acc04, tagged_vlans: [vlan150, vlan160]}
      7:  {name: to_nt_acc05, tagged_vlans: [vlan170, vlan175]}
      8:  {name: to_nt_acc06, tagged_vlans: [vlan180, vlan190]}

  HCM_CORE:
    dp_id: 0x000000000002
    hardware: "Open vSwitch"
    interfaces:
      1:  {name: to_hcm_dist01, tagged_vlans: [vlan210, vlan220]}
      2:  {name: to_hcm_dist02, tagged_vlans: [vlan210, vlan220]}
      # ... tương tự NT_CORE

  NT_ACC01:
    dp_id: 0x000000000011
    hardware: "Open vSwitch"
    interfaces:
      1: {name: uplink_to_core, tagged_vlans: [vlan110]}
      # Ports 2-N: access hosts (VLAN 110)

  # NT_ACC02..06, HCM_ACC01..06 tương tự
```

### 14.5 Skeleton `controller/sdn/faucet_controller.py`

```python
"""
faucet_controller.py
Quản lý Faucet SDN Controller process và kết nối OVS switches.
"""
import subprocess, time, os

FAUCET_CONFIG_PATH = '/tmp/faucet.yaml'
FAUCET_LOG_PATH    = '/tmp/faucet.log'
FAUCET_PORT        = 6653  # OpenFlow
FAUCET_API_PORT    = 9302  # REST API

class FaucetController:
    def __init__(self, config_path='src/config/faucet.yaml'):
        self.config_path = config_path
        self.process = None
    
    def prepare_config(self):
        """Copy faucet.yaml vào /tmp/ để Faucet đọc."""
        import shutil
        shutil.copy(self.config_path, FAUCET_CONFIG_PATH)
        print(f'[Faucet] Config copied to {FAUCET_CONFIG_PATH}')
    
    def start(self):
        """Khởi động Faucet process."""
        self.prepare_config()
        
        env = os.environ.copy()
        env['FAUCET_CONFIG'] = FAUCET_CONFIG_PATH
        env['FAUCET_LOG']    = FAUCET_LOG_PATH
        
        self.process = subprocess.Popen(
            ['faucet', '--ryu-ofp-tcp-listen-port', str(FAUCET_PORT)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)  # Đợi Faucet init
        
        if self.process.poll() is not None:
            raise RuntimeError(f'Faucet failed to start. Check {FAUCET_LOG_PATH}')
        
        print(f'[Faucet] Started (PID={self.process.pid}, port={FAUCET_PORT})')
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            print('[Faucet] Stopped')
    
    def connect_ovs_switches(self, switch_names: list):
        """Kết nối OVS switches với Faucet controller."""
        for sw_name in switch_names:
            subprocess.run([
                'ovs-vsctl', 'set-controller', sw_name,
                f'tcp:127.0.0.1:{FAUCET_PORT}'
            ], check=True)
            # Set OpenFlow version 1.3
            subprocess.run([
                'ovs-vsctl', 'set', 'bridge', sw_name,
                'protocols=OpenFlow13'
            ], check=True)
            print(f'[Faucet] {sw_name} → Controller tcp:127.0.0.1:{FAUCET_PORT}')
    
    def disconnect_ovs_switches(self, switch_names: list):
        """Ngắt kết nối OVS switches khỏi Faucet (về standalone)."""
        for sw_name in switch_names:
            subprocess.run(['ovs-vsctl', 'del-controller', sw_name])
```

### 14.6 Skeleton `controller/sdn/flow_manager.py`

```python
"""
flow_manager.py
CRUD operations cho Faucet flow tables qua REST API.
Được gọi bởi AI Engine khi cần install/modify flow rules.
"""
import requests, json

FAUCET_API_BASE = 'http://localhost:9302'

class FlowManager:
    def __init__(self, api_base=FAUCET_API_BASE):
        self.api_base = api_base
    
    def get_dp_status(self) -> dict:
        """Lấy trạng thái tất cả datapath (switches)."""
        resp = requests.get(f'{self.api_base}/metrics')
        return resp.text
    
    def get_port_status(self, dp_id: str, port: int) -> dict:
        """Lấy trạng thái 1 port trên 1 switch."""
        resp = requests.get(
            f'{self.api_base}/port/status',
            params={'dp_id': dp_id, 'port': port}
        )
        return resp.json()
    
    def set_port_state(self, dp_id: str, port: int, state: bool):
        """
        Enable/disable 1 port (dùng khi AI muốn block/unblock traffic).
        state: True = UP, False = DOWN
        """
        resp = requests.post(
            f'{self.api_base}/port/state',
            json={
                'dp_id': dp_id,
                'port': port,
                'status': 1 if state else 0
            }
        )
        action = 'UP' if state else 'DOWN'
        print(f'[FlowMgr] dp={dp_id} port={port} → {action}')
        return resp.json()
    
    def reload_config(self):
        """Reload Faucet config sau khi thay đổi faucet.yaml."""
        resp = requests.post(f'{self.api_base}/reload')
        return resp.status_code == 200
    
    def get_flow_stats(self, dp_id: str) -> list:
        """Lấy flow statistics của 1 datapath."""
        resp = requests.get(
            f'{self.api_base}/flow_stats',
            params={'dp_id': dp_id}
        )
        return resp.json()
```

### 14.7 Tích hợp vào `enterprise_topo.py`

```python
# Phase 14: Switch sang Faucet SDN Controller
# Chú ý: Phase 14 thay đổi controller mode của OVS switches
# Thực hiện SAU net.start() (Phase 1-13 vẫn dùng standalone mode)

if phase >= 14:
    info('\n[PHASE 14] Khởi động Faucet SDN Controller...\n')
    from controller.sdn.faucet_controller import FaucetController
    
    faucet = FaucetController('config/faucet.yaml')
    faucet.start()
    
    # Danh sách switches kết nối Faucet (CORE + ACC + BL_SW)
    sdn_switches = [
        'NT_CORE', 'HCM_CORE', 'BL_SW',
        'NT_ACC01', 'NT_ACC02', 'NT_ACC03',
        'NT_ACC04', 'NT_ACC05', 'NT_ACC06',
        'HCM_ACC01', 'HCM_ACC02', 'HCM_ACC03',
        'HCM_ACC04', 'HCM_ACC05', 'HCM_ACC06',
    ]
    faucet.connect_ovs_switches(sdn_switches)
    
    topo.faucet = faucet
    info('[PHASE 14] ✓ Faucet SDN Controller connected\n')
    
    if phase < 15:
        return topo
```

### 14.8 Lưu ý khi chạy Phase 14

> **[QUAN TRỌNG]** Phase 14 thay đổi `controller mode` của OVS switches từ `standalone` sang Faucet.  
> Điều này có thể gây mất kết nối tạm thời (1-3s) khi Faucet install flow tables.  
> Chạy Phase 14 cần Faucet được cài sẵn: `sudo pip3 install faucet`

```bash
# Cài Faucet
sudo pip3 install faucet

# Kiểm tra Faucet
faucet --version
```

### 14.9 Checkpoint kiểm tra

```bash
# Test 1: Faucet kết nối được với OVS
sudo ovs-vsctl show
# → Controller "tcp:127.0.0.1:6653" is_connected: true

# Test 2: pingall vẫn hoạt động sau khi Faucet kiểm soát
mininet> pingall
# → < 5% packet loss

# Test 3: FlowManager hoạt động
python3 -c "
from src.controller.sdn.flow_manager import FlowManager
fm = FlowManager()
print(fm.get_dp_status())
"

# Test 4: AI install flow rule qua FlowManager
# → Block port NT_ACC02 (simulate switch failure)
python3 -c "
from src.controller.sdn.flow_manager import FlowManager
fm = FlowManager()
fm.set_port_state('0x000000000011', 1, False)  # NT_ACC01 port 1 DOWN
"

# Test 5: Khi re-enable
python3 -c "
fm.set_port_state('0x000000000011', 1, True)
"
```

**Thời gian ước tính:** 7-10 ngày

---

## TỔNG HỢP: Thứ tự thực hiện và Dependencies

```
Week 1-2:  Phase 7  (ACL/Firewall) → Test xong mới sang Phase 8
Week 2-3:  Phase 8  (HAProxy LB)   → Cần WEB01/02 từ Phase 6 ✓
Week 3-4:  Phase 9  (WAN 5-path)   → Thay thế wan_links.py hoàn toàn
Week 4-5:  Phase 10 (SD-WAN)       → Phụ thuộc Phase 9 WAN paths ✓
Week 8-9:  Phase 14 (Faucet SDN)   → Sau Phase 12 có Prometheus metrics
```

### File map tổng thể (mới cần tạo/sửa)

| File | Hành động | Phase |
|------|-----------|-------|
| `config/acl_rules.yaml` | TẠO MỚI | 7 |
| `scripts/configure_acl.py` | TẠO MỚI | 7 |
| `tests/phase_checks/check_phase7.py` | TẠO MỚI | 7 |
| `config/haproxy.cfg.j2` | TẠO MỚI | 8 |
| `scripts/configure_haproxy.py` | TẠO MỚI | 8 |
| `scripts/setup_webservers.py` | TẠO MỚI | 8 |
| `tests/phase_checks/check_phase8.py` | TẠO MỚI | 8 |
| `topology/wan/wan_topo.py` | TẠO MỚI | 9 |
| `topology/wan/wan_links.py` | SỬA TOÀN BỘ | 9 |
| `config/wan_paths.yaml` | TẠO MỚI | 9 |
| `tests/phase_checks/check_phase9.py` | TẠO MỚI | 9 |
| `controller/sdwan/sdwan_controller.py` | TẠO MỚI | 10 |
| `controller/sdwan/path_monitor.py` | TẠO MỚI | 10 |
| `controller/sdwan/policy_engine.py` | TẠO MỚI | 10 |
| `controller/sdwan/traffic_steerer.py` | TẠO MỚI | 10 |
| `controller/sdwan/probes/wan_prober.py` | TẠO MỚI | 10 |
| `controller/sdwan/models/path_state.py` | TẠO MỚI | 10 |
| `controller/sdwan/models/traffic_class.py` | TẠO MỚI | 10 |
| `config/sdwan_policy.yaml` | TẠO MỚI | 10 |
| `tests/phase_checks/check_phase10.py` | TẠO MỚI | 10 |
| `config/faucet.yaml` | TẠO MỚI | 14 |
| `controller/sdn/faucet_controller.py` | TẠO MỚI | 14 |
| `controller/sdn/flow_manager.py` | TẠO MỚI | 14 |
| `controller/sdn/openflow_agent.py` | TẠO MỚI | 14 |
| `tests/phase_checks/check_phase14.py` | TẠO MỚI | 14 |
| `topology/enterprise_topo.py` | SỬA (thêm phase 7-10, 14 blocks) | 7-10,14 |

### Package dependencies mới cần cài

```bash
sudo apt install -y haproxy iptables
sudo pip3 install faucet flask requests
# Phase 10:
sudo pip3 install pyyaml flask
```

---

## CHECKPOINT TỔNG KẾT

| Phase | Điều kiện PASS |
|-------|---------------|
| 7 | CCTV không ping DB ✓ / IoT không ping USER ✓ / USER ping WEB ✓ |
| 8 | `curl 10.100.10.10` OK ✓ / WEB01 down → failover < 5s ✓ |
| 9 | ping qua MPLS ~20ms ✓ / ping qua LTE ~60ms ✓ / path down/up ✓ |
| 10 | MPLS down → SD-WAN chuyển sang 5G < 3s ✓ / REST API OK ✓ |
| 14 | Faucet connected ✓ / pingall < 5% loss ✓ / FlowManager CRUD ✓ |

---

*Tài liệu tạo lúc: 2026-10-07*  
*Người thực hiện: Antigravity (AI Assistant)*  
*Dự án: KLTN - Self-Healing Enterprise Network*
