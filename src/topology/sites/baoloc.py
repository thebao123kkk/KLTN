"""
topology/sites/baoloc.py
BẢO LỘC — Flat Network
=============================================
Topology vật lý:
  BL-GW (host FRR + keepalived)
     |
  BL-SW (OVS switch, VLAN-aware)
  ├── VLAN 10  USER  : 12 PC (BL-ADMIN-PC01..03, BL-SALES-PC01..03,
  │                           BL-ACC-PC01..03, BL-IT-PC01..03)
  ├── VLAN 30  IoT   : BL-PRN01, BL-PRN02
  ├── VLAN 35  CCTV  : BL-CAM01, BL-CAM02
  ├── VLAN 50  WIFI  : BL-AP01
  └── VLAN 99  MGMT  : (management access)

Phase coverage: Phase 1 (topology), Phase 2 (VLAN+IP), Phase 3 (STP)
"""

import os
import yaml
from mininet.node import OVSSwitch


# ── Đường dẫn config ──────────────────────────────────────
_CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')


def _load_vlan_config():
    path = os.path.join(_CONFIG_DIR, 'vlan.yaml')
    with open(path) as f:
        return yaml.safe_load(f)


# ── Helper: cấu hình VLAN trên OVS port ──────────────────
def _set_access_port(sw, port_name, vlan_id):
    """Đặt OVS port thành access port thuộc VLAN vlan_id."""
    os.system(f'ovs-vsctl set port {port_name} vlan-mode=access tag={vlan_id}')


def _set_trunk_port(sw, port_name, vlan_ids):
    """Đặt OVS port thành trunk port cho danh sách VLAN."""
    trunks = ','.join(str(v) for v in vlan_ids)
    os.system(f'ovs-vsctl set port {port_name} vlan-mode=trunk trunks={trunks}')


# ── Helper: cấu hình STP priority ────────────────────────
def _set_stp_priority(sw_name, priority):
    """Đặt STP bridge priority (bội số 4096)."""
    os.system(f'ovs-vsctl set bridge {sw_name} other-config:stp-priority={priority}')


# ── Main builder function ─────────────────────────────────
def build_baoloc(net):
    """
    Thêm toàn bộ BL site vào Mininet net.

    Parameters
    ----------
    net : Mininet
        Instance Mininet đang chạy (đã gọi net = Mininet(...) nhưng chưa net.start())

    Returns
    -------
    dict với keys:
        'sw'     : OVS switch BL-SW
        'gw'     : Mininet host đóng vai router/VRRP (BL-GW)
        'hosts'  : dict { hostname: host_object }
    """
    cfg = _load_vlan_config()
    bl = cfg['baoloc']

    # ── Switch ────────────────────────────────────────────
    # cls=OVSSwitch, failMode='standalone' để switch hoạt động độc lập
    # khi chưa có SDN controller (Phase 1–8)
    sw = net.addSwitch('BL_SW', cls=OVSSwitch, failMode='standalone', stp=True, dpid='0000000000000001')

    # ── Gateway host (chạy FRR + keepalived) ────────────────────────────
    # Không có IP sẵn, sẽ cấu hình qua script FRR
    gw = net.addHost('BL_GW', ip=None)

    # ── Hosts theo config ─────────────────────────────────
    hosts = {}
    for h_cfg in bl['hosts']:
        h = net.addHost(
            h_cfg['name'],
            ip=h_cfg['ip'],
            defaultRoute=f"via {h_cfg['gw']}"
        )
        hosts[h_cfg['name']] = h
        # Kết nối host → switch
        link = net.addLink(h, sw)

        # Lưu thông tin VLAN để cấu hình sau khi net.start()
        h.vlan = h_cfg['vlan']
        h.link_intf = link.intf2.name   # interface phía switch

    # ── Kết nối GW → switch (uplink, trunk tất cả VLAN) ──
    gw_link = net.addLink(gw, sw)
    gw.link_intf = gw_link.intf2.name  # interface phía switch

    print(f'[BL] Đã thêm: 1 switch, 1 GW host, {len(hosts)} end hosts')
    return {'sw': sw, 'gw': gw, 'hosts': hosts, 'gw_link_intf': gw_link.intf2.name}


def configure_baoloc(bl_nodes):
    """
    Cấu hình VLAN/STP trên OVS sau khi net.start() đã chạy.
    Gọi hàm này từ enterprise_topo.py sau net.start().

    Parameters
    ----------
    bl_nodes : dict
        Kết quả trả về từ build_baoloc()
    """
    sw = bl_nodes['sw']
    sw_name = sw.name   # 'BL-SW'
    hosts = bl_nodes['hosts']

    cfg = _load_vlan_config()
    bl = cfg['baoloc']
    host_cfg_map = {h['name']: h for h in bl['hosts']}

    print(f'[BL] Cấu hình VLAN trên {sw_name} ...')

    # STP priority — BL-SW là root (không có redundancy, priority thấp nhất)
    _set_stp_priority(sw_name, priority=4096)

    # Cấu hình access port cho từng host
    for hname, h in hosts.items():
        h_cfg = host_cfg_map[hname]
        vlan = h_cfg['vlan']
        port_intf = h.link_intf
        _set_access_port(sw, port_intf, vlan)
        print(f'  [BL] {hname} → {port_intf} VLAN {vlan}')

    # Cấu hình trunk port cho GW (tất cả VLAN)
    all_vlans = [v for v in bl['vlans'].keys()]
    _set_trunk_port(sw, bl_nodes['gw_link_intf'], all_vlans)
    print(f'  [BL] BL-GW trunk VLANs: {all_vlans}')

    # Enable inter-VLAN routing trên GW host
    _configure_gw_interfaces(bl_nodes['gw'], bl)

    print(f'[BL] ✓ VLAN configuration done')


def _configure_gw_interfaces(gw_host, bl_cfg):
    """
    Cấu hình sub-interfaces và IP trên BL-GW host.
    Mỗi VLAN có 1 sub-interface eth0.VLAN với IP = gateway của VLAN đó.
    Bật IP forwarding.
    """
    base_intf = 'BL-GW-eth0'   # interface chính của host
    gw_host.cmd('sysctl -w net.ipv4.ip_forward=1')

    for vlan_id, vlan_info in bl_cfg['vlans'].items():
        sub_intf = f'{base_intf}.{vlan_id}'
        gw_ip = vlan_info['gateway']
        prefix = vlan_info['subnet'].split('/')[1]

        # Tạo VLAN sub-interface
        gw_host.cmd(f'ip link add link {base_intf} name {sub_intf} type vlan id {vlan_id}')
        gw_host.cmd(f'ip addr add {gw_ip}/{prefix} dev {sub_intf}')
        gw_host.cmd(f'ip link set {sub_intf} up')
        print(f'  [BL-GW] {sub_intf}: {gw_ip}/{prefix}')


def start_frr_baoloc(gw_host):
    """
    Khởi động FRRouting OSPF daemon trên BL-GW host.
    Yêu cầu: frr đã cài trên Ubuntu (`apt install frr`).
    Config file: /etc/frr/frr.conf (tạo bởi generate_frr_config.py)
    """
    gw_host.cmd('service frr start')
    gw_host.cmd('vtysh -c "configure terminal" '
                '-c "router ospf" '
                '-c "router-id 10.10.99.1" '
                '-c "network 10.10.0.0/16 area 0" '
                '-c "exit" '
                '-c "exit"')
    print('[BL-GW] FRR OSPF started')
