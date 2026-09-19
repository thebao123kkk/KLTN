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
    lan_intfs = [intf.name for intf in gw_host.intfList() if intf.name != 'lo' and '_w' not in intf.name]
    for intf_name in lan_intfs:
        gw_host.cmd(f'ip link set {intf_name} up')

    # Tạo Linux bridge br0 gộp các LAN interfaces với VLAN filtering
    gw_host.cmd('ip link add name br0 type bridge 2>/dev/null')
    gw_host.cmd('ip link set dev br0 type bridge vlan_filtering 1 2>/dev/null')
    for intf_name in lan_intfs:
        gw_host.cmd(f'ip link set {intf_name} master br0 2>/dev/null')
        gw_host.cmd(f'bridge vlan add dev {intf_name} vid 2-4094 2>/dev/null')
    gw_host.cmd('ip link set br0 up')

    for vlan_id, vinfo in dc_vlan['vlans'].items():
        sub_intf = f'br0.{vlan_id}'
        gw_ip = vinfo['gateway']
        prefix = vinfo['subnet'].split('/')[1]

        gw_host.cmd(f'ip link add link br0 name {sub_intf} type vlan id {vlan_id} 2>/dev/null')
        gw_host.cmd(f'ip addr add {gw_ip}/{prefix} dev {sub_intf} 2>/dev/null')
        gw_host.cmd(f'ip link set {sub_intf} up')

    print('  [DC_SPINE_GW] Sub-interfaces configured on br0')



def start_services_datacenter(dc_nodes):
    """
    Khởi động các dịch vụ Phase 6:
      _ dnsmasq DHCP trên DC_DHCP01
      _ dnsmasq DNS trên DC_DNS01
      _ chrony NTP trên DC_MGMT01
    """
    hosts = dc_nodes['hosts']

    # ── DHCP Primary Server ───────────────────────────────
    if 'DC_DHCP01' in hosts:
        dhcp_host1 = hosts['DC_DHCP01']
        dhcp_host1.cmd('dnsmasq __conf_file=/tmp/dnsmasq_dhcp.conf __pid_file=/tmp/dnsmasq_dhcp.pid')
        print('[DC_DHCP01] dnsmasq Primary DHCP server started')

    # ── DHCP Backup Server ────────────────────────────────
    if 'DC_DHCP02' in hosts:
        dhcp_host2 = hosts['DC_DHCP02']
        dhcp_host2.cmd('dnsmasq __conf_file=/tmp/dnsmasq_dhcp2.conf __pid_file=/tmp/dnsmasq_dhcp2.pid')
        print('[DC_DHCP02] dnsmasq Backup DHCP server started')

    # ── DNS Server ────────────────────────────────────────
    dns_host = hosts['DC_DNS01']
    # dnsmasq config được generate bởi scripts/generate_dnsmasq_dns.py
    dns_host.cmd('dnsmasq __conf_file=/tmp/dnsmasq_dns.conf __pid_file=/tmp/dnsmasq_dns.pid')
    print('[DC_DNS01] dnsmasq DNS server started')

    # ── NTP Server ────────────────────────────────────────
    ntp_host = hosts['DC_MGMT01']
    # Ghi chrony config
    chrony_conf = (
        'server 0.pool.ntp.org iburst\n'
        'server 1.pool.ntp.org iburst\n'
        'allow 10.0.0.0/8\n'
        'local stratum 2\n'
    )
    ntp_host.cmd(f'echo "{chrony_conf}" > /tmp/chrony.conf')
    ntp_host.cmd('chronyd _f /tmp/chrony.conf _p /tmp/chrony.pid')
    print('[DC_MGMT01] chrony NTP server started')


def start_frr_datacenter(dc_nodes):
    """Khởi động FRR OSPF trên DC_SPINE_GW."""
    gw = dc_nodes['gw']
    gw.cmd('/usr/lib/frr/zebra -d 2>/dev/null || /usr/libexec/frr/zebra -d 2>/dev/null || service frr start')
    gw.cmd('/usr/lib/frr/ospfd -d 2>/dev/null || /usr/libexec/frr/ospfd -d 2>/dev/null')
    gw.cmd(
        'vtysh -c "configure terminal" '
        '-c "router ospf" '
        '-c "router-id 10.100.99.1" '
        '-c "network 10.100.0.0/16 area 0" '
        '-c "network 192.168.30.0/30 area 0" '
        '-c "exit" -c "exit"'
    )
    print('[DC_SPINE_GW] FRR OSPF started')

