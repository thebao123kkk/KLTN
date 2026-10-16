"""
topology/sites/datacenter.py
DATA CENTER — Spine_Leaf Architecture
=============================================
Topology vật lý:
            DC_SPINE01          DC_SPINE02
           / |  \              / |  \
      LEAF01 LEAF02          LEAF03 LEAF04
         │      │                │      │
         └──────┴────────────────┴──────┘
                          │
                       Servers:
            DC_WEB01/02, DC_APP01/02, DC_DB01/02,
            DC_DNS01, DC_DHCP01, DC_MON01, DC_MGMT01

Distribution:
  LEAF01 → WEB tier (VLAN 310)
  LEAF02 → APP tier (VLAN 320)
  LEAF03 → DB tier  (VLAN 330)
  LEAF04 → INFRA/MON/MGMT (VLAN 340/350/360)

Phase coverage: Phase 1 (topology), Phase 2 (VLAN+IP), Phase 6 (DHCP/DNS/NTP services)

DHCP HA Architecture (Phase 6):
  Centralized DHCP HA tại DC + Dual Relay tại tất cả Branch.
  DC_DHCP01 (Primary) 10.100.40.12 + DC_DHCP02 (Backup) 10.100.40.13
  Mỗi Branch Gateway (BL_GW, NT_DIST01/02, HCM_DIST01/02) relay
  đồng thời đến cả 2 server → configure_dhcp_relay.py
"""

import os
import yaml
from mininet.node import OVSSwitch


_CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')


def _load_configs():
    with open(os.path.join(_CONFIG_DIR, 'vlan.yaml')) as f:
        vlan_cfg = yaml.safe_load(f)
    with open(os.path.join(_CONFIG_DIR, 'services.yaml')) as f:
        svc_cfg = yaml.safe_load(f)
    return vlan_cfg, svc_cfg


def _set_access_port(port_name, vlan_id):
    os.system(f'ovs-vsctl set port {port_name} vlan_mode=access tag={vlan_id}')


def _set_trunk_port(port_name, vlan_ids=None):
    os.system(f'ovs-vsctl set port {port_name} vlan_mode=trunk')


def _set_stp_priority(sw_name, priority):
    os.system(f'ovs-vsctl set bridge {sw_name} other-config:stp-priority={priority}')


# Server → LEAF assignment
SERVER_TO_LEAF = {
    'DC_WEB01':   'DC_LEAF01', 'DC_WEB02':   'DC_LEAF01',
    'DC_APP01':   'DC_LEAF02', 'DC_APP02':   'DC_LEAF02',
    'DC_DB01':    'DC_LEAF03', 'DC_DB02':    'DC_LEAF03',
    'DC_DNS01':   'DC_LEAF04', 'DC_DHCP01':  'DC_LEAF04',
    'DC_DHCP02':  'DC_LEAF04', 'DC_MON01':   'DC_LEAF04',
    'DC_MGMT01':  'DC_LEAF04',
}

# LEAF → VLANs served
LEAF_VLANS = {
    'DC_LEAF01': [310],
    'DC_LEAF02': [320],
    'DC_LEAF03': [330],
    'DC_LEAF04': [340, 350, 360],
}


def build_datacenter(net):
    """
    Thêm toàn bộ DC site vào Mininet net (Spine_Leaf).

    Returns
    _______
    dict:
        'spines'  : { 'DC_SPINE01': sw, 'DC_SPINE02': sw }
        'leaves'  : { 'DC_LEAF01': sw, ..., 'DC_LEAF04': sw }
        'gw'      : DC_SPINE_GW host (FRR router)
        'hosts'   : { hostname: host }
    """
    vlan_cfg, svc_cfg = _load_configs()
    dc = vlan_cfg['datacenter']

    nodes = {}

    # ── Spine switches ────────────────────────────────────
    spine1 = net.addSwitch('DC_SPINE01', cls=OVSSwitch, failMode='standalone', stp=True, dpid='0000000000000004')
    spine2 = net.addSwitch('DC_SPINE02', cls=OVSSwitch, failMode='standalone', stp=True, dpid='0000000000000005')
    nodes['spines'] = {'DC_SPINE01': spine1, 'DC_SPINE02': spine2}

    # Inter_spine link
    net.addLink(spine1, spine2)

    # ── Gateway host (chạy FRR) ───────────────────────────
    gw = net.addHost('DC_SP_GW', ip=None)
    lk_gw1 = net.addLink(gw, spine1)
    lk_gw2 = net.addLink(gw, spine2)
    gw.spine1_intf = lk_gw1.intf1.name
    gw.spine2_intf = lk_gw2.intf1.name
    nodes['gw'] = gw

    # ── Leaf switches ─────────────────────────────────────
    leaf_switches = {}
    dpid_counter = 0x0000000000000300
    for leaf_name in LEAF_VLANS:
        leaf_name_underscore = leaf_name.replace('_', '_')
        leaf_sw = net.addSwitch(leaf_name_underscore, cls=OVSSwitch, failMode='standalone', stp=True, dpid=f'{dpid_counter:016x}')
        leaf_switches[leaf_name] = leaf_sw
        dpid_counter += 1

        # Leaf → Spine1 và Spine2 (đa đường, STP block 1)
        lk_s1 = net.addLink(leaf_sw, spine1)
        lk_s2 = net.addLink(leaf_sw, spine2)
        leaf_sw.uplink_spine1 = lk_s1.intf1.name
        leaf_sw.uplink_spine2 = lk_s2.intf1.name

    nodes['leaves'] = leaf_switches

    # ── Server hosts ──────────────────────────────────────
    hosts = {}
    host_cfg_map = {h['name']: h for h in dc['hosts']}

    for hname, h_cfg in host_cfg_map.items():
        leaf_name = SERVER_TO_LEAF.get(hname, 'DC_LEAF04')
        leaf_sw   = leaf_switches[leaf_name]

        h = net.addHost(
            hname,
            ip=h_cfg['ip'],
            defaultRoute=f"via {h_cfg['gw']}"
        )
        hosts[hname] = h

        lk = net.addLink(h, leaf_sw)
        h.vlan      = h_cfg['vlan']
        h.link_intf = lk.intf2.name
        h.role      = h_cfg.get('role', 'generic')

    nodes['hosts'] = hosts

    print(f'[DC] Đã thêm: 2 SPINE, 4 LEAF switches, 1 GW, {len(hosts)} servers')
    return nodes


def configure_datacenter(dc_nodes):
    """
    Cấu hình VLAN + STP sau net.start().
    """
    vlan_cfg, _ = _load_configs()
    dc_vlan = vlan_cfg['datacenter']
    host_cfg_map = {h['name']: h for h in dc_vlan['hosts']}
    all_vlans = list(dc_vlan['vlans'].keys())

    # STP priorities — SPINE01 là root
    _set_stp_priority('DC_SPINE01', 4096)
    _set_stp_priority('DC_SPINE02', 8192)
    for leaf_name in LEAF_VLANS:
        _set_stp_priority(leaf_name, 32768)

    print('[DC] Cấu hình VLAN ports...')

    # Trunk Spine ↔ Leaf
    for leaf_name, leaf_sw in dc_nodes['leaves'].items():
        _set_trunk_port(leaf_sw.uplink_spine1, all_vlans)
        _set_trunk_port(leaf_sw.uplink_spine2, all_vlans)

    # Access ports: server → leaf
    for hname, h in dc_nodes['hosts'].items():
        h_cfg = host_cfg_map[hname]
        _set_access_port(h.link_intf, h_cfg['vlan'])

    # GW sub_interfaces
    _configure_gw_interfaces(dc_nodes['gw'], dc_vlan)

    print('[DC] ✓ VLAN configuration done')


def _configure_gw_interfaces(gw_host, dc_vlan):
    """IP sub_interfaces trên DC_SP_GW — gộp LAN ports vào br0 (VLAN-aware)."""
    gw_host.cmd('sysctl -w net.ipv4.ip_forward=1')

    # Lấy tất cả LAN interfaces (trừ lo và WAN links)
    # WAN interfaces của DC_SP_GW có tên dạng 'dcgw_*' (kết nối vào WAN switch)
    lan_intfs = [
        intf.name for intf in gw_host.intfList()
        if intf.name != 'lo'
        and '_w' not in intf.name
        and not intf.name.startswith('dcgw_')
    ]
    for intf_name in lan_intfs:
        gw_host.cmd(f'ip link set {intf_name} up')

    # Tạo Linux bridge br0 gộp các LAN interfaces với VLAN filtering
    gw_host.cmd('ip link add name br0 type bridge 2>/dev/null')
    gw_host.cmd('ip link set dev br0 type bridge vlan_filtering 1 2>/dev/null')
    for intf_name in lan_intfs:
        gw_host.cmd(f'ip link set {intf_name} master br0 2>/dev/null')
        gw_host.cmd(f'bridge vlan add dev {intf_name} vid 2-4094 2>/dev/null')
    gw_host.cmd('bridge vlan add dev br0 vid 2-4094 self 2>/dev/null')
    gw_host.cmd('ip link set br0 up')

    for vlan_id, vinfo in dc_vlan['vlans'].items():
        sub_intf = f'br0.{vlan_id}'
        gw_ip = vinfo['gateway']
        prefix = vinfo['subnet'].split('/')[1]

        gw_host.cmd(f'ip link add link br0 name {sub_intf} type vlan id {vlan_id} 2>/dev/null')
        gw_host.cmd(f'ip addr add {gw_ip}/{prefix} dev {sub_intf} 2>/dev/null')
        gw_host.cmd(f'ip link set {sub_intf} up')

    print('  [DC_SPINE_GW] Sub-interfaces configured on br0')



def start_dhcp_ha(dc_nodes):
    """
    Khởi động cặp DHCP Server HA tại Data Center.

    Kiến trúc: Centralized DHCP HA + Dual Relay
      DC_DHCP01 (Primary)  — 10.100.40.12
      DC_DHCP02 (Backup)   — 10.100.40.13

    Cả 2 dnsmasq instance chia sẻ cùng Pool config (được generate bởi
    scripts/generate_dnsmasq_configs.py) nhưng có pid/lease file riêng
    để tránh xung đột khi chạy đồng thời.

    Lý do HA:
      - Nếu DHCP01 sập, Branch Relay tự động nhận Offer từ DHCP02
      - Không cần failover protocol phức tạp vì dùng Dual Relay
    """
    hosts = dc_nodes['hosts']

    # Bước 1: Generate config files cho cả 2 DHCP servers
    # (gọi từ scripts/generate_dnsmasq_configs.py — nên chạy trước)
    _gen_dhcp_configs()

    # Bước 2: Khởi động DHCP Primary Server (DC_DHCP01)
    if 'DC_DHCP01' in hosts:
        dhcp_host1 = hosts['DC_DHCP01']
        dhcp_host1.cmd('kill $(cat /tmp/dnsmasq_dhcp.pid 2>/dev/null) 2>/dev/null; true')
        result1 = dhcp_host1.cmd(
            'dnsmasq --conf-file=/tmp/dnsmasq_dhcp.conf '
            '--pid-file=/tmp/dnsmasq_dhcp.pid '
            '--leasefile-ro 2>/dev/null || '
            'dnsmasq --conf-file=/tmp/dnsmasq_dhcp.conf '
            '--pid-file=/tmp/dnsmasq_dhcp.pid'
        )
        print(f'[DC_DHCP01] dnsmasq Primary DHCP server started (PID: {dhcp_host1.cmd("cat /tmp/dnsmasq_dhcp.pid 2>/dev/null").strip()})')

    # Bước 3: Khởi động DHCP Backup Server (DC_DHCP02)
    if 'DC_DHCP02' in hosts:
        dhcp_host2 = hosts['DC_DHCP02']
        dhcp_host2.cmd('kill $(cat /tmp/dnsmasq_dhcp2.pid 2>/dev/null) 2>/dev/null; true')
        dhcp_host2.cmd(
            'dnsmasq --conf-file=/tmp/dnsmasq_dhcp2.conf '
            '--pid-file=/tmp/dnsmasq_dhcp2.pid '
            '--leasefile-ro 2>/dev/null || '
            'dnsmasq --conf-file=/tmp/dnsmasq_dhcp2.conf '
            '--pid-file=/tmp/dnsmasq_dhcp2.pid'
        )
        print(f'[DC_DHCP02] dnsmasq Backup DHCP server started (HA standby)')

    return {
        'primary': hosts.get('DC_DHCP01'),
        'backup': hosts.get('DC_DHCP02'),
        'primary_ip': '10.100.40.12',
        'backup_ip': '10.100.40.13',
    }


def _gen_dhcp_configs():
    """Generate dnsmasq config files (Primary + Backup) nếu chưa có."""
    if not os.path.exists('/tmp/dnsmasq_dhcp.conf'):
        try:
            import sys
            scripts_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts')
            sys.path.insert(0, scripts_dir)
            from generate_dnsmasq_configs import main as gen_configs
            gen_configs()
        except Exception as e:
            print(f'  [WARN] generate_dnsmasq_configs failed: {e}')
            print('  [WARN] Ensure scripts/generate_dnsmasq_configs.py chạy trước topology start')


def start_services_datacenter(dc_nodes):
    """
    Khởi động các dịch vụ Phase 6:
      - dnsmasq DHCP HA: DC_DHCP01 (Primary) + DC_DHCP02 (Backup)
      - dnsmasq DNS trên DC_DNS01
      - chrony NTP trên DC_MGMT01

    Lưu ý: DHCP Relay trên Branch Gateway được cấu hình riêng bởi
    scripts/configure_dhcp_relay.py thông qua apply_dhcp_relay(gw_nodes).
    """
    # ── DHCP HA (Primary + Backup) ────────────────────────
    start_dhcp_ha(dc_nodes)

    # ── DNS Server ────────────────────────────────────────
    hosts = dc_nodes['hosts']
    dns_host = hosts['DC_DNS01']
    dns_host.cmd('kill $(cat /tmp/dnsmasq_dns.pid 2>/dev/null) 2>/dev/null; true')
    dns_host.cmd('dnsmasq --conf-file=/tmp/dnsmasq_dns.conf --pid-file=/tmp/dnsmasq_dns.pid')
    print('[DC_DNS01] dnsmasq DNS server started')

    # ── NTP Server ────────────────────────────────────────
    ntp_host = hosts['DC_MGMT01']
    chrony_conf = (
        'server 0.pool.ntp.org iburst\n'
        'server 1.pool.ntp.org iburst\n'
        'allow 10.0.0.0/8\n'
        'local stratum 2\n'
    )
    ntp_host.cmd(f'printf "{chrony_conf}" > /tmp/chrony.conf')
    ntp_host.cmd('chronyd -f /tmp/chrony.conf -p /tmp/chrony.pid 2>/dev/null || chronyd -f /tmp/chrony.conf')
    print('[DC_MGMT01] chrony NTP server started')


def start_frr_datacenter(dc_nodes):
    """Khởi động FRR OSPF trên DC_SPINE_GW với socket riêng."""
    gw = dc_nodes['gw']
    hname = getattr(gw, 'name', 'DC_SP_GW')
    run_dir = f'/tmp/frr_{hname}'
    gw.cmd(f'mkdir -p {run_dir}')
    gw.cmd(f'chmod 777 {run_dir}')
    gw.cmd(f'chown frr:frr {run_dir} 2>/dev/null; true')
    # Tắt integrated-vtysh-config trong /etc/frr/frr.conf để tránh bị override
    gw.cmd("sed -i 's/^service integrated-vtysh-config/no service integrated-vtysh-config/' /etc/frr/frr.conf 2>/dev/null; true")

    conf_file  = f'{run_dir}/frr.conf'
    zebra_conf = f'{run_dir}/zebra.conf'
    ospfd_conf = f'{run_dir}/ospfd.conf'

    # Tìm WAN interface name — Phase 9: tên dạng 'dcgw_mpls_g', 'dcgw_lte_g'
    wan_intfs = [
        intf.name for intf in gw.intfList()
        if intf.name.startswith('dcgw_')
    ]
    # Fallback: tìm theo '_w' (Phase 1-8 naming)
    if not wan_intfs:
        wan_intfs = [intf.name for intf in gw.intfList() if '_w' in intf.name]

    passive_lines = " passive-interface default\n"
    for wi in wan_intfs:
        passive_lines += f" no passive-interface {wi}\n"

    # zebra.conf: chỉ cấu hình daemon-level, không có router ospf
    zebra_content = (
        f"frr version 8\n"
        f"frr defaults traditional\n"
        f"no service integrated-vtysh-config\n"
        f"hostname {hname}\n"
        f"log file {run_dir}/frr.log\n"
        "line vty\n"
    )
    # ospfd.conf: chỉ cấu hình OSPF
    ospfd_content = (
        f"frr version 8\n"
        f"frr defaults traditional\n"
        f"no service integrated-vtysh-config\n"
        f"hostname {hname}\n"
        f"log file {run_dir}/frr.log\n"
        "router ospf\n"
        " ospf router-id 10.100.99.1\n"
        " network 10.100.0.0/16 area 0\n"
        " network 192.168.30.0/30 area 0\n"
        " network 172.16.0.0/12 area 0\n"
        f"{passive_lines}"
        " redistribute connected\n"
        "line vty\n"
    )
    gw.cmd(f'printf "{zebra_content}" > {zebra_conf}')
    gw.cmd(f'printf "{ospfd_content}" > {ospfd_conf}')
    # giữ frr.conf để tương thích
    gw.cmd(f'cp {ospfd_conf} {conf_file}')

    gw.cmd(f'kill -9 $(cat {run_dir}/zebra.pid 2>/dev/null) 2>/dev/null; true')
    gw.cmd(f'kill -9 $(cat {run_dir}/ospfd.pid 2>/dev/null) 2>/dev/null; true')
    # Đảm bảo kill đúng process theo socket path (tránh PID file outdated)
    gw.cmd(f'pkill -9 -f "zebra.*{run_dir}" 2>/dev/null; true')
    gw.cmd(f'pkill -9 -f "ospfd.*{run_dir}" 2>/dev/null; true')
    gw.cmd(f'rm -f {run_dir}/zebra.pid {run_dir}/ospfd.pid {run_dir}/zserv.api 2>/dev/null; true')
    gw.cmd('sleep 1')

    gw.cmd(
        f'/usr/lib/frr/zebra -d -f {zebra_conf} '
        f'-i {run_dir}/zebra.pid -z {run_dir}/zserv.api '
        f'--vty_socket {run_dir} 2>{run_dir}/zebra.err '
        f'|| /usr/libexec/frr/zebra -d -f {zebra_conf} '
        f'-i {run_dir}/zebra.pid -z {run_dir}/zserv.api '
        f'--vty_socket {run_dir} 2>{run_dir}/zebra.err'
    )
    gw.cmd('sleep 1')
    gw.cmd(
        f'/usr/lib/frr/ospfd -d -f {ospfd_conf} '
        f'-i {run_dir}/ospfd.pid -z {run_dir}/zserv.api '
        f'--vty_socket {run_dir} 2>{run_dir}/ospfd.err '
        f'|| /usr/libexec/frr/ospfd -d -f {ospfd_conf} '
        f'-i {run_dir}/ospfd.pid -z {run_dir}/zserv.api '
        f'--vty_socket {run_dir} 2>{run_dir}/ospfd.err'
    )
    print('[DC_SPINE_GW] FRR OSPF started (isolated sockets in /tmp/frr_DC_SP_GW)')


