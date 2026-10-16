"""
topology/wan/wan_links.py
WAN Links - Phase 9 Full Implementation (5 Transport Paths)
=============================================
Phase 1-8:  direct link stub (192.168.x.x/30), không tc netem
Phase 9+:   5 OVS WAN switches với tc netem (MPLS/5G/INET/VPN/LTE)

Hàm này được gọi từ enterprise_topo.py:
  - connect_sites_wan():  gọi ở build phase (trước net.start())
  - configure_wan_ips():  gọi ở configure phase (sau net.start())
"""

import os
import sys
from mininet.log import info

_WAN_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(_WAN_DIR, '..', '..')
sys.path.insert(0, _SRC_DIR)


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def connect_sites_wan(net, bl_nodes, nt_nodes, hcm_nodes, dc_nodes,
                      phase: int = 9):
    """
    Kết nối 4 site qua WAN.

    Phase 1-8: Direct links đơn giản (192.168.x.x/30)
    Phase 9+:  5 OVS WAN switches (MPLS/5G/INET/VPN/LTE)

    Trả về: dict wan_info để configure_wan_ips() dùng tiếp.
    """
    if phase < 9:
        return _connect_direct_links(net, bl_nodes, nt_nodes, hcm_nodes, dc_nodes)
    else:
        return _connect_wan_5path(net, bl_nodes, nt_nodes, hcm_nodes, dc_nodes)


def configure_wan_ips(wan_info, bl_nodes, nt_nodes, hcm_nodes, dc_nodes,
                      phase: int = 9):
    """
    Cấu hình IP + tc netem cho WAN interfaces.

    Phase 1-8: IP point-to-point đơn giản
    Phase 9+:  IP + tc netem cho từng path
    """
    if isinstance(wan_info, dict) and wan_info.get('_phase', 9) < 9:
        _configure_direct_ips(wan_info, bl_nodes, nt_nodes, hcm_nodes, dc_nodes)
    else:
        _configure_5path_ips(wan_info, bl_nodes, nt_nodes, hcm_nodes, dc_nodes)


# ─────────────────────────────────────────────────────────────
# Phase 1-8: Direct links (backward compatibility)
# ─────────────────────────────────────────────────────────────

def _mk_ifname(node, suffix: str) -> str:
    """Tạo tên interface hợp lệ (max 15 chars)."""
    base = getattr(node, 'name', str(node)).replace('-', '_')
    maxlen = 15 - len('_') - len(suffix)
    return f'{base[:maxlen]}_{suffix}'


def _connect_direct_links(net, bl_nodes, nt_nodes, hcm_nodes, dc_nodes) -> dict:
    """Phase 1-8: direct link stub."""
    info('[WAN] Phase 1-8: Building direct WAN links (stub)\n')

    bl_gw  = bl_nodes['gw']
    hcm_d1 = hcm_nodes['dist']['HCM_DIST01']
    nt_d1  = nt_nodes['dist']['NT_DIST01']
    dc_gw  = dc_nodes['gw']

    lk1 = net.addLink(bl_gw,  hcm_d1, intfName1=_mk_ifname(bl_gw,  'w1'),
                                        intfName2=_mk_ifname(hcm_d1, 'w1'))
    bl_gw.wan_intf   = lk1.intf1.name
    hcm_d1.wan_intf  = lk1.intf2.name

    lk2 = net.addLink(nt_d1,  hcm_d1, intfName1=_mk_ifname(nt_d1,  'w2'),
                                        intfName2=_mk_ifname(hcm_d1, 'w2'))
    nt_d1.wan_intf   = lk2.intf1.name
    hcm_d1.wan_intf2 = lk2.intf2.name

    lk3 = net.addLink(hcm_d1, dc_gw,  intfName1=_mk_ifname(hcm_d1, 'w3'),
                                        intfName2=_mk_ifname(dc_gw,  'w3'))
    hcm_d1.wan_intf3 = lk3.intf1.name
    dc_gw.wan_intf   = lk3.intf2.name

    return {
        '_phase': 1,
        'bl_hcm_link': lk1,
        'nt_hcm_link': lk2,
        'hcm_dc_link': lk3,
    }


def _configure_direct_ips(wan_info: dict, bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """Phase 1-8: IP point-to-point."""
    bl_gw  = bl_nodes['gw']
    nt_d1  = nt_nodes['dist']['NT_DIST01']
    hcm_d1 = hcm_nodes['dist']['HCM_DIST01']
    dc_gw  = dc_nodes['gw']

    bl_gw.cmd(f'ip addr add 192.168.10.1/30 dev {bl_gw.wan_intf}')
    bl_gw.cmd(f'ip link set {bl_gw.wan_intf} up')
    hcm_d1.cmd(f'ip addr add 192.168.10.2/30 dev {hcm_d1.wan_intf}')
    hcm_d1.cmd(f'ip link set {hcm_d1.wan_intf} up')

    nt_d1.cmd(f'ip addr add 192.168.20.1/30 dev {nt_d1.wan_intf}')
    nt_d1.cmd(f'ip link set {nt_d1.wan_intf} up')
    hcm_d1.cmd(f'ip addr add 192.168.20.2/30 dev {hcm_d1.wan_intf2}')
    hcm_d1.cmd(f'ip link set {hcm_d1.wan_intf2} up')

    hcm_d1.cmd(f'ip addr add 192.168.30.1/30 dev {hcm_d1.wan_intf3}')
    hcm_d1.cmd(f'ip link set {hcm_d1.wan_intf3} up')
    dc_gw.cmd(f'ip addr add 192.168.30.2/30 dev {dc_gw.wan_intf}')
    dc_gw.cmd(f'ip link set {dc_gw.wan_intf} up')

    info('[WAN] Direct link IPs configured (Phase 1-8)\n')


# ─────────────────────────────────────────────────────────────
# Phase 9: 5-Path WAN
# ─────────────────────────────────────────────────────────────

def _connect_wan_5path(net, bl_nodes, nt_nodes, hcm_nodes, dc_nodes) -> dict:
    """Phase 9: Tạo 5 WAN switches + kết nối."""
    info('[WAN] Phase 9: Building 5-path WAN topology...\n')

    from topology.wan.wan_topo import build_wan_topology, connect_sites_to_wan

    wan_switches = build_wan_topology(net)
    wan_links    = connect_sites_to_wan(
        net, wan_switches,
        bl_nodes, nt_nodes, hcm_nodes, dc_nodes
    )

    info('[WAN] 5-path WAN topology built (5 switches x 4 sites = 20 links)\n')

    return {
        '_phase':       9,
        'wan_switches': wan_switches,
        'wan_links':    wan_links,
    }


def _configure_5path_ips(wan_info: dict, bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """Phase 9: Gán IP + tc netem + OSPF routes."""
    from topology.wan.wan_topo import configure_wan_ips_and_netem, _load_wan_config

    wan_links = wan_info['wan_links']

    # Step 1: IP + tc netem
    configure_wan_ips_and_netem(wan_links)

    # Step 2: Thêm WAN subnets vào OSPF
    _configure_ospf_wan_routes(bl_nodes, nt_nodes, hcm_nodes, dc_nodes)

    # Step 3: Default route → MPLS primary
    _configure_default_wan_routes(wan_links, bl_nodes, nt_nodes, hcm_nodes, dc_nodes)

    info('[WAN] 5-path WAN configured (IP + netem + OSPF + routes)\n')


def _configure_ospf_wan_routes(bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """Thêm WAN subnets (172.16.x.x/24) vào OSPF trên tất cả GW routers."""
    from topology.wan.wan_topo import _load_wan_config
    wan_cfg = _load_wan_config()
    wan_subnets = [f'{p["subnet"]}.0/24' for p in wan_cfg['paths'].values()]

    gws = {
        'BL_GW':     bl_nodes['gw'],
        'NT_DIST01': nt_nodes['dist']['NT_DIST01'],
        'HCM_DIST01': hcm_nodes['dist']['HCM_DIST01'],
        'DC_SP_GW':  dc_nodes['gw'],
    }

    for name, gw in gws.items():
        for subnet in wan_subnets:
            gw.cmd(
                f'vtysh -c "conf t" -c "router ospf" '
                f'-c "network {subnet} area 0" -c "end" 2>/dev/null'
            )
        info(f'  [{name}] OSPF: WAN subnets advertised\n')


def _configure_default_wan_routes(wan_links: dict,
                                   bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """Default route: mỗi site → DC via MPLS. SD-WAN sẽ override."""
    from topology.wan.wan_topo import _load_wan_config
    wan_cfg = _load_wan_config()
    mpls_subnet = wan_cfg['paths']['MPLS']['subnet']
    site_octets = wan_cfg['site_octets']

    dc_mpls_ip = f'{mpls_subnet}.{site_octets["DC"]}'

    for site_code, gw in {
        'BL':  bl_nodes['gw'],
        'NT':  nt_nodes['dist']['NT_DIST01'],
        'HCM': hcm_nodes['dist']['HCM_DIST01'],
    }.items():
        gw.cmd(f'ip route add 10.100.0.0/16 via {dc_mpls_ip} 2>/dev/null || '
               f'ip route replace 10.100.0.0/16 via {dc_mpls_ip}')

    info(f'[WAN] Default routes: all sites → DC via MPLS ({dc_mpls_ip})\n')


# ─────────────────────────────────────────────────────────────
# Public helpers
# ─────────────────────────────────────────────────────────────

def get_wan_links(wan_info: dict) -> dict:
    """Trả về wan_links dict nếu phase 9+."""
    if wan_info.get('_phase', 1) >= 9:
        return wan_info.get('wan_links', {})
    return {}


def get_wan_switches(wan_info: dict) -> dict:
    """Trả về wan_switches dict nếu phase 9+."""
    if wan_info.get('_phase', 1) >= 9:
        return wan_info.get('wan_switches', {})
    return {}
