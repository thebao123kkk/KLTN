"""
topology/sites/hcm.py
HỒ CHÍ MINH — 3-Tier Network (site lớn nhất)
=============================================
Topology vật lý:
                       HCM-CORE (OVS)
                      /              \
              HCM-DIST01              HCM-DIST02
             (FRR+VRRP Master)        (FRR+VRRP Backup)
             / | \                   / | \
          ACC01 ACC02 ACC03       ACC04 ACC05 ACC06

ACC01 → VLAN 210 ADMIN      (3 PC)
ACC02 → VLAN 220 SALES      (3 PC)
ACC03 → VLAN 230 ACCOUNTING (3 PC)
ACC04 → VLAN 240 HR         (3 PC)
ACC05 → VLAN 250 MKT + 260 CUST (6 PC)
ACC06 → VLAN 270/280/290/295/296/297  TECH+IT+IoT+CCTV+WIFI+VOICE

Phase coverage: Phase 1, 2, 3, 4 (OSPF), 5 (VRRP)
"""

import os
import yaml
from mininet.node import OVSSwitch


_CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')


def _load_configs():
    with open(os.path.join(_CONFIG_DIR, 'vlan.yaml')) as f:
        vlan_cfg = yaml.safe_load(f)
    with open(os.path.join(_CONFIG_DIR, 'vrrp.yaml')) as f:
        vrrp_cfg = yaml.safe_load(f)
    return vlan_cfg, vrrp_cfg


def _set_access_port(port_name, vlan_id):
    os.system(f'ovs-vsctl set port {port_name} vlan-mode=access tag={vlan_id}')


def _set_trunk_port(port_name, vlan_ids):
    trunks = ','.join(str(v) for v in vlan_ids)
    os.system(f'ovs-vsctl set port {port_name} vlan-mode=trunk trunks={trunks}')


def _set_stp_priority(sw_name, priority):
    os.system(f'ovs-vsctl set bridge {sw_name} other-config:stp-priority={priority}')


# Access switch VLAN assignment (CT.md section 7)
ACC_VLANS = {
    'HCM-ACC01': [210],
    'HCM-ACC02': [220],
    'HCM-ACC03': [230],
    'HCM-ACC04': [240],
    'HCM-ACC05': [250, 260],
    'HCM-ACC06': [270, 280, 290, 295, 296, 297],
}

HOST_TO_ACC = {
    # ADMIN
    'HCM-ADMIN-PC01': 'HCM-ACC01', 'HCM-ADMIN-PC02': 'HCM-ACC01', 'HCM-ADMIN-PC03': 'HCM-ACC01',
    # SALES
    'HCM-SALES-PC01': 'HCM-ACC02', 'HCM-SALES-PC02': 'HCM-ACC02', 'HCM-SALES-PC03': 'HCM-ACC02',
    # ACCOUNTING
    'HCM-ACC-PC01':  'HCM-ACC03', 'HCM-ACC-PC02':  'HCM-ACC03', 'HCM-ACC-PC03':  'HCM-ACC03',
    # HR
    'HCM-HR-PC01':   'HCM-ACC04', 'HCM-HR-PC02':   'HCM-ACC04', 'HCM-HR-PC03':   'HCM-ACC04',
    # MARKETING + CUSTOMER
    'HCM-MKT-PC01':  'HCM-ACC05', 'HCM-MKT-PC02':  'HCM-ACC05', 'HCM-MKT-PC03':  'HCM-ACC05',
    'HCM-CUST-PC01': 'HCM-ACC05', 'HCM-CUST-PC02': 'HCM-ACC05', 'HCM-CUST-PC03': 'HCM-ACC05',
    # TECHNICAL + IT + IoT/CCTV/WIFI/VOICE
    'HCM-TECH-PC01': 'HCM-ACC06', 'HCM-TECH-PC02': 'HCM-ACC06', 'HCM-TECH-PC03': 'HCM-ACC06',
    'HCM-IT-PC01':   'HCM-ACC06', 'HCM-IT-PC02':   'HCM-ACC06', 'HCM-IT-PC03':   'HCM-ACC06',
    'HCM-PRN01':     'HCM-ACC06', 'HCM-PRN02':     'HCM-ACC06', 'HCM-PRN03':     'HCM-ACC06',
    'HCM-CAM01':     'HCM-ACC06', 'HCM-CAM02':     'HCM-ACC06',
    'HCM-CAM03':     'HCM-ACC06', 'HCM-CAM04':     'HCM-ACC06',
    'HCM-AP01':      'HCM-ACC06', 'HCM-AP02':      'HCM-ACC06',
    'HCM-PHONE01':   'HCM-ACC06', 'HCM-PHONE02':   'HCM-ACC06',
}


def build_hcm(net):
    """
    Thêm toàn bộ HCM site vào Mininet net.

    Returns
    -------
    dict:
        'core'  : HCM-CORE switch
        'dist'  : { 'HCM-DIST01': host, 'HCM-DIST02': host }
        'acc'   : { 'HCM-ACC01': switch, ..., 'HCM-ACC06': switch }
        'hosts' : { hostname: host }
    """
    vlan_cfg, _ = _load_configs()
    hcm_vlan = vlan_cfg['hcm']

    nodes = {}

    # ── Core switch ───────────────────────────────────────
    core = net.addSwitch('HCM_CORE', cls=OVSSwitch, failMode='standalone', stp=True, dpid='0000000000000003')
    nodes['core'] = core

    # ── Distribution switches ───────────────────────────────────────
    dist1 = net.addSwitch('HCM_DIST01', cls=OVSSwitch, failMode='standalone', stp=True, dpid='0000000000000020')
    dist2 = net.addSwitch('HCM_DIST02', cls=OVSSwitch, failMode='standalone', stp=True, dpid='0000000000000021')
    nodes['dist'] = {'HCM_DIST01': dist1, 'HCM_DIST02': dist2}

    lk_d1 = net.addLink(dist1, core)
    lk_d2 = net.addLink(dist2, core)
    dist1.uplink_intf = lk_d1.intf1.name
    dist1.core_intf   = lk_d1.intf2.name
    dist2.uplink_intf = lk_d2.intf1.name
    dist2.core_intf   = lk_d2.intf2.name

    # ── Access switches ───────────────────────────────────
    acc_switches = {}
    dpid_counter = 0x0000000000000200
    for acc_name in ACC_VLANS:
        acc_name_underscore = acc_name.replace('-', '_')
        acc_sw = net.addSwitch(acc_name_underscore, cls=OVSSwitch, failMode='standalone', stp=True, dpid=f'{dpid_counter:016x}')
        acc_switches[acc_name] = acc_sw
        dpid_counter += 1

        lk  = net.addLink(acc_sw, dist1)
        lk2 = net.addLink(acc_sw, dist2)
        acc_sw.uplink_dist1 = lk.intf1.name
        acc_sw.uplink_dist2 = lk2.intf1.name

    nodes['acc'] = acc_switches

    # ── End hosts ─────────────────────────────────────────
    hosts = {}
    host_cfg_map = {h['name']: h for h in hcm_vlan['hosts']}

    for hname, h_cfg in host_cfg_map.items():
        acc_name = HOST_TO_ACC.get(hname, 'HCM-ACC06')
        acc_sw   = acc_switches[acc_name]

        h = net.addHost(
            hname,
            ip=h_cfg['ip'],
            defaultRoute=f"via {h_cfg['gw']}"
        )
        hosts[hname] = h

        lk = net.addLink(h, acc_sw)
        h.vlan      = h_cfg['vlan']
        h.link_intf = lk.intf2.name

    nodes['hosts'] = hosts

    print(f'[HCM] Đã thêm: 1 CORE, 2 DIST, 6 ACC switches, {len(hosts)} end hosts')
    return nodes


def configure_hcm(hcm_nodes):
    """
    Cấu hình VLAN + STP sau net.start().
    """
    vlan_cfg, _ = _load_configs()
    hcm_vlan = vlan_cfg['hcm']
    host_cfg_map = {h['name']: h for h in hcm_vlan['hosts']}
    all_vlans = list(hcm_vlan['vlans'].keys())

    # STP priorities
    _set_stp_priority('HCM_CORE', 4096)
    _set_stp_priority('HCM_DIST01', 8192)
    _set_stp_priority('HCM_DIST02', 8192)
    for acc_name in ACC_VLANS:
        acc_name_underscore = acc_name.replace('-', '_')
        _set_stp_priority(acc_name_underscore, 32768)

    print('[HCM] Cấu hình VLAN ports...')

    # Trunk CORE ↔ DIST
    dist1 = hcm_nodes['dist']['HCM_DIST01']
    dist2 = hcm_nodes['dist']['HCM_DIST02']
    _set_trunk_port(dist1.core_intf, all_vlans)
    _set_trunk_port(dist2.core_intf, all_vlans)

    # Trunk DIST ↔ ACC
    for acc_name, vlans in ACC_VLANS.items():
        acc_sw = hcm_nodes['acc'][acc_name]
        _set_trunk_port(acc_sw.uplink_dist1, vlans)
        _set_trunk_port(acc_sw.uplink_dist2, vlans)

    # Access ports
    for hname, h in hcm_nodes['hosts'].items():
        h_cfg = host_cfg_map[hname]
        _set_access_port(h.link_intf, h_cfg['vlan'])

    # DIST host IP
    _configure_dist_interfaces(dist1, 'HCM-DIST01', vlan_cfg)
    _configure_dist_interfaces(dist2, 'HCM_DIST02', vlan_cfg)

    print('[HCM] ✓ VLAN configuration done')


def _configure_dist_interfaces(dist_host, dist_name, vlan_cfg):
    """Sub-interfaces cho DIST host — cùng pattern với NT."""
    is_dist1 = '01' in dist_name
    base_intf = f'{dist_name}-eth0'
    hcm_vlans = vlan_cfg['hcm']['vlans']

    dist_host.cmd('sysctl -w net.ipv4.ip_forward=1')

    for vlan_id, vinfo in hcm_vlans.items():
        sub_intf = f'{base_intf}.{vlan_id}'
        prefix = vinfo['subnet'].split('/')[1]
        octet = '2' if is_dist1 else '3'
        ip_addr = vinfo['gateway'].rsplit('.', 1)[0] + f'.{octet}'

        dist_host.cmd(f'ip link add link {base_intf} name {sub_intf} type vlan id {vlan_id}')
        dist_host.cmd(f'ip addr add {ip_addr}/{prefix} dev {sub_intf}')
        dist_host.cmd(f'ip link set {sub_intf} up')

    print(f'  [{dist_name}] Sub-interfaces configured')


def start_vrrp_hcm(hcm_nodes):
    """Khởi động keepalived trên HCM-DIST01/02."""
    dist1 = hcm_nodes['dist']['HCM_DIST01']
    dist2 = hcm_nodes['dist']['HCM_DIST02']
    dist1.cmd('keepalived -f /tmp/keepalived_HCM_DIST01.conf -p /tmp/ka_hcm_dist01.pid')
    dist2.cmd('keepalived -f /tmp/keepalived_HCM_DIST02.conf -p /tmp/ka_hcm_dist02.pid')
    print('[HCM] keepalived VRRP started')


def start_frr_hcm(hcm_nodes):
    """Khởi động FRR OSPF trên HCM-DIST01/02."""
    for dist_name, dist_host in hcm_nodes['dist'].items():
        router_id = '10.30.10.2' if '01' in dist_name else '10.30.10.3'
        dist_host.cmd('service frr start')
        dist_host.cmd(
            f'vtysh -c "configure terminal" '
            f'-c "router ospf" '
            f'-c "router-id {router_id}" '
            f'-c "network 10.30.0.0/16 area 0" '
            f'-c "exit" -c "exit"'
        )
        print(f'  [{dist_name}] FRR OSPF started')
