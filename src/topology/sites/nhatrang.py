"""
topology/sites/nhatrang.py
NHA TRANG — 3-Tier Network
=============================================
Topology vật lý:
                       NT-CORE (OVS)
                      /             \
              NT-DIST01              NT-DIST02
              (FRR+VRRP Master)      (FRR+VRRP Backup)
             / | \                  / | \
          ACC01 ACC02 ACC03      ACC04 ACC05 ACC06

ACC01 → VLAN 110 ADMIN   (3 PC)
ACC02 → VLAN 120 SALES   (3 PC)
ACC03 → VLAN 130 ACC     (3 PC)
ACC04 → VLAN 140 HR      (3 PC)
ACC05 → VLAN 150 CUST    (3 PC)
ACC06 → VLAN 160/170/175/180/190  IT+IoT+CCTV+WiFi+Voice

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
    os.system(f'ovs-vsctl set port {port_name} tag={vlan_id}')


def _set_trunk_port(port_name, vlan_ids=None):
    os.system(f'ovs-vsctl clear port {port_name} tag')


def _set_stp_priority(sw_name, priority):
    os.system(f'ovs-vsctl set bridge {sw_name} other-config:stp-priority={priority} other-config:stp-forward-delay=2 2>/dev/null')


# Access switch VLAN assignment (từ CT.md section 4)
ACC_VLANS = {
    'NT_ACC01': [110],
    'NT_ACC02': [120],
    'NT_ACC03': [130],
    'NT_ACC04': [140],
    'NT_ACC05': [150],
    'NT_ACC06': [160, 170, 175, 180, 190],
}

# Mỗi host thuộc ACC switch nào
HOST_TO_ACC = {
    'NT_ADM01': 'NT_ACC01', 'NT_ADM02': 'NT_ACC01', 'NT_ADM03': 'NT_ACC01',
    'NT_SAL01': 'NT_ACC02', 'NT_SAL02': 'NT_ACC02', 'NT_SAL03': 'NT_ACC02',
    'NT_ACC01':   'NT_ACC03', 'NT_ACC02':   'NT_ACC03', 'NT_ACC03':   'NT_ACC03',
    'NT_HR01':    'NT_ACC04', 'NT_HR02':    'NT_ACC04', 'NT_HR03':    'NT_ACC04',
    'NT_CUS01':  'NT_ACC05', 'NT_CUS02':  'NT_ACC05', 'NT_CUS03':  'NT_ACC05',
    'NT_IT01':    'NT_ACC06', 'NT_IT02':    'NT_ACC06', 'NT_IT03':    'NT_ACC06',
    'NT_PRN01':      'NT_ACC06', 'NT_PRN02':      'NT_ACC06',
    'NT_CAM01':      'NT_ACC06', 'NT_CAM02':      'NT_ACC06', 'NT_CAM03':      'NT_ACC06',
    'NT_AP01':       'NT_ACC06',
    'NT_PHN01':    'NT_ACC06', 'NT_PHN02':    'NT_ACC06',
}


def build_nhatrang(net):
    """
    Thêm toàn bộ NT site vào Mininet net.

    Returns
    -------
    dict:
        'core'   : NT-CORE switch
        'dist'   : { 'NT-DIST01': host, 'NT-DIST02': host }
        'acc'    : { 'NT-ACC01': switch, ..., 'NT-ACC06': switch }
        'hosts'  : { hostname: host }
    """
    vlan_cfg, _ = _load_configs()
    nt = vlan_cfg['nhatrang']

    nodes = {}

    # ── Core switch ───────────────────────────────────────
    core = net.addSwitch('NT_CORE', cls=OVSSwitch, failMode='standalone', stp=True, dpid='0000000000000002')
    nodes['core'] = core

    # ── Distribution routers (chạy FRR OSPF + keepalived VRRP) ────────────────────────────
    dist1 = net.addHost('NT_DIST01', ip=None)
    dist2 = net.addHost('NT_DIST02', ip=None)
    nodes['dist'] = {'NT_DIST01': dist1, 'NT_DIST02': dist2}

    # Kết nối DIST → CORE (uplink trunk)
    lk_d1 = net.addLink(dist1, core)
    lk_d2 = net.addLink(dist2, core)
    dist1.uplink_intf  = lk_d1.intf1.name   # phía dist1
    dist1.core_intf    = lk_d1.intf2.name   # phía core
    dist2.uplink_intf  = lk_d2.intf1.name
    dist2.core_intf    = lk_d2.intf2.name

    # ── Access switches ───────────────────────────────────
    acc_switches = {}
    dpid_counter = 0x0000000000000100
    for acc_name in ACC_VLANS:
        acc_name_underscore = acc_name.replace('-', '_')
        acc_sw = net.addSwitch(acc_name_underscore, cls=OVSSwitch, failMode='standalone', stp=True, dpid=f'{dpid_counter:016x}')
        acc_switches[acc_name] = acc_sw
        dpid_counter += 1

        # ACC → DIST01 (primary uplink)
        lk = net.addLink(acc_sw, dist1)
        acc_sw.uplink_dist1 = lk.intf1.name

        # ACC → DIST02 (redundant uplink, RSTP akan block salah satu)
        lk2 = net.addLink(acc_sw, dist2)
        acc_sw.uplink_dist2 = lk2.intf1.name

    nodes['acc'] = acc_switches

    # ── End hosts ─────────────────────────────────────────
    hosts = {}
    host_cfg_map = {h['name']: h for h in nt['hosts']}

    for hname, h_cfg in host_cfg_map.items():
        acc_name = HOST_TO_ACC.get(hname, 'NT-ACC06')
        acc_sw = acc_switches[acc_name]

        h = net.addHost(
            hname,
            ip=h_cfg['ip'],
            defaultRoute=f"via {h_cfg['gw']}"
        )
        hosts[hname] = h

        lk = net.addLink(h, acc_sw)
        h.vlan = h_cfg['vlan']
        h.link_intf = lk.intf2.name   # phía switch

    nodes['hosts'] = hosts

    # ── DIST → WAN uplink (placeholder, Phase 9) ──────────
    # Sẽ kết nối WAN switch trong enterprise_topo.py

    print(f'[NT] Đã thêm: 1 CORE, 2 DIST, 6 ACC switches, {len(hosts)} end hosts')
    return nodes


def configure_nhatrang(nt_nodes):
    """
    Cấu hình VLAN + STP priority sau net.start().
    """
    vlan_cfg, _ = _load_configs()
    nt_vlan = vlan_cfg['nhatrang']
    host_cfg_map = {h['name']: h for h in nt_vlan['hosts']}
    all_vlans = list(nt_vlan['vlans'].keys())

    # STP priorities
    _set_stp_priority('NT_CORE', 4096)           # Root bridge
    for acc_name in ACC_VLANS:
        acc_name_underscore = acc_name.replace('-', '_')
        _set_stp_priority(acc_name_underscore, 32768)

    print('[NT] Cấu hình VLAN ports...')

    # Trunk: CORE ↔ DIST1 và CORE ↔ DIST2
    dist1 = nt_nodes['dist']['NT_DIST01']
    dist2 = nt_nodes['dist']['NT_DIST02']
    _set_trunk_port(dist1.core_intf, all_vlans)
    _set_trunk_port(dist2.core_intf, all_vlans)

    # Trunk: DIST ↔ ACC (tất cả VLAN mà ACC đó phục vụ)
    acc_switches = nt_nodes['acc']
    for acc_name, vlans in ACC_VLANS.items():
        acc_sw = acc_switches[acc_name]
        _set_trunk_port(acc_sw.uplink_dist1, vlans)
        _set_trunk_port(acc_sw.uplink_dist2, vlans)

    # Access ports: host → ACC
    for hname, h in nt_nodes['hosts'].items():
        h_cfg = host_cfg_map[hname]
        _set_access_port(h.link_intf, h_cfg['vlan'])

    # Cấu hình IP trên DIST hosts
    _configure_dist_interfaces(dist1, 'NT_DIST01', vlan_cfg)
    _configure_dist_interfaces(dist2, 'NT_DIST02', vlan_cfg)

    print('[NT] ✓ VLAN configuration done')


def _configure_dist_interfaces(dist_host, dist_name, vlan_cfg):
    """
    Tạo Linux bridge 'br0' (VLAN-aware) gộp tất cả LAN interfaces của DIST host,
    sau đó tạo sub-interfaces VLAN br0.VLAN với IP gateway.
    DIST01 dùng .2 (primary), DIST02 dùng .3 (backup) theo VRRP config.
    """
    is_dist1 = '01' in dist_name
    nt_vlans = vlan_cfg['nhatrang']['vlans']

    dist_host.cmd('sysctl -w net.ipv4.ip_forward=1')

    # Lấy tất cả LAN interfaces (trừ lo và WAN links)
    lan_intfs = [intf.name for intf in dist_host.intfList() if intf.name != 'lo' and '_w' not in intf.name]
    for intf_name in lan_intfs:
        dist_host.cmd(f'ip link set {intf_name} up')

    # Tạo Linux bridge br0 gộp các LAN interfaces với VLAN filtering
    dist_host.cmd('ip link add name br0 type bridge 2>/dev/null')
    dist_host.cmd('ip link set dev br0 type bridge vlan_filtering 1 2>/dev/null')
    dist_host.cmd('bridge vlan add dev br0 vid 2-4094 self 2>/dev/null')
    for intf_name in lan_intfs:
        dist_host.cmd(f'ip link set {intf_name} master br0 2>/dev/null')
        dist_host.cmd(f'bridge vlan add dev {intf_name} vid 2-4094 2>/dev/null')
    dist_host.cmd('ip link set br0 up')

    for vlan_id, vinfo in nt_vlans.items():
        sub_intf = f'br0.{vlan_id}'
        subnet = vinfo['subnet']
        prefix = subnet.split('/')[1]
        # DIST01 → .2, DIST02 → .3 (VIP .1 từ keepalived/primary)
        octet = '2' if is_dist1 else '3'
        ip_addr = vinfo['gateway'].rsplit('.', 1)[0] + f'.{octet}'
        gw_vip = vinfo['gateway']

        dist_host.cmd(f'ip link add link br0 name {sub_intf} type vlan id {vlan_id} 2>/dev/null')
        dist_host.cmd(f'ip addr add {ip_addr}/{prefix} dev {sub_intf} 2>/dev/null')
        if is_dist1:
            dist_host.cmd(f'ip addr add {gw_vip}/{prefix} dev {sub_intf} 2>/dev/null')
        dist_host.cmd(f'ip link set {sub_intf} up')

    print(f'  [{dist_name}] Sub-interfaces configured on br0')




def start_vrrp_nhatrang(nt_nodes):
    """
    Khởi động keepalived VRRP trên NT-DIST01 và NT-DIST02.
    Yêu cầu: keepalived đã cài (`apt install keepalived`).
    Config được generate bởi scripts/generate_keepalived_conf.py
    """
    dist1 = nt_nodes['dist']['NT_DIST01']
    dist2 = nt_nodes['dist']['NT_DIST02']

    if not os.path.exists('/tmp/keepalived_NT_DIST01.conf'):
        try:
            from scripts.generate_keepalived_conf import main as gen_ka
            gen_ka()
        except Exception:
            pass

    dist1.cmd('keepalived -f /tmp/keepalived_NT_DIST01.conf -p /tmp/ka_dist01.pid')
    dist2.cmd('keepalived -f /tmp/keepalived_NT_DIST02.conf -p /tmp/ka_dist02.pid')
    print('[NT] keepalived VRRP started on DIST01 and DIST02')


def start_frr_nhatrang(nt_nodes):
    """
    Khởi động FRR OSPF trên NT-DIST01 và NT-DIST02.
    """
    for dist_name, dist_host in nt_nodes['dist'].items():
        router_id = '10.20.10.2' if '01' in dist_name else '10.20.10.3'
        dist_host.cmd('/usr/lib/frr/zebra -d 2>/dev/null || /usr/libexec/frr/zebra -d 2>/dev/null || service frr start')
        dist_host.cmd('/usr/lib/frr/ospfd -d 2>/dev/null || /usr/libexec/frr/ospfd -d 2>/dev/null')
        dist_host.cmd(
            f'vtysh -c "configure terminal" '
            f'-c "router ospf" '
            f'-c "router-id {router_id}" '
            f'-c "network 10.20.0.0/16 area 0" '
            f'-c "network 192.168.20.0/30 area 0" '
            f'-c "exit" -c "exit"'
        )
        print(f'  [{dist_name}] FRR OSPF started, router-id={router_id}')

