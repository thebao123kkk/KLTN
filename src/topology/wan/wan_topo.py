"""
topology/wan/wan_topo.py
Phase 9 - 5 WAN Transport Path Topology

Xây dựng 5 OVS WAN switches và kết nối 4 site GW vào chúng.
Mỗi WAN switch đại diện cho 1 transport path (MPLS/5G/INET/VPN/LTE).
tc netem áp dụng trên interfaces để emulate đặc tính thực.

Kiến trúc:
    BL_GW ─┬─ WAN_SW_MPLS ─┬─ DC_SP_GW
            ├─ WAN_SW_FIVEG ─┤
 NT_DIST01 ─┼─ WAN_SW_INET  ─┤
            ├─ WAN_SW_VPN   ─┤
HCM_DIST01 ─┴─ WAN_SW_LTE  ─┘
"""

import os
import sys
import yaml
from mininet.node import OVSSwitch
from mininet.log import info

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')


def _load_wan_config() -> dict:
    """Đọc config/wan_paths.yaml."""
    config_path = os.path.join(_CONFIG_DIR, 'wan_paths.yaml')
    with open(config_path) as f:
        return yaml.safe_load(f)


def _safe_intf_name(node_name: str, path_code: str, side: str) -> str:
    """
    Tạo tên interface hợp lệ Linux (max 15 chars, không có ký tự đặc biệt).

    node_name: tên Mininet node (VD: 'BL_GW', 'NT_DIST01')
    path_code: mã path ngắn (VD: 'mpls', '5g', 'inet')
    side: 'g' (GW side) hoặc 's' (switch side)
    """
    # Rút gọn node name: chỉ lấy phần cuối và viết tắt
    abbrev = {
        'BL_GW': 'blgw',
        'NT_DIST01': 'ntd1',
        'HCM_DIST01': 'hcmd',
        'DC_SP_GW': 'dcgw',
    }
    node_abbrev = abbrev.get(node_name, node_name[:4].lower().replace('_', ''))
    name = f'{node_abbrev}_{path_code}_{side}'
    return name[:15]


# ─────────────────────────────────────────────────────────────
# Build Phase
# ─────────────────────────────────────────────────────────────

def build_wan_topology(net) -> dict:
    """
    Tạo 5 OVS WAN switches (TRƯỚC net.start()).
    Trả về: {'MPLS': sw_obj, 'FIVEG': sw_obj, 'INET': sw_obj, ...}
    """
    wan_cfg = _load_wan_config()
    wan_switches = {}

    for path_name, profile in wan_cfg['paths'].items():
        sw_name = f'WAN_{path_name}'
        dpid_hex = profile['dpid_suffix']

        # Đảm bảo dpid là 16 hex chars
        dpid_full = dpid_hex.zfill(16)

        sw = net.addSwitch(
            sw_name,
            cls=OVSSwitch,
            failMode='standalone',
            stp=False,          # WAN switch không cần STP
            dpid=dpid_full,
        )
        wan_switches[path_name] = sw
        info(f'  [WAN] Switch {sw_name} created (dpid={dpid_full})\n')

    return wan_switches


def connect_sites_to_wan(net, wan_switches: dict,
                         bl_nodes, nt_nodes, hcm_nodes, dc_nodes) -> dict:
    """
    Kết nối 4 site GW vào 5 WAN switches (TRƯỚC net.start()).

    Mỗi site GW sẽ có 5 interfaces (1 per WAN path).
    Trả về: dict lưu link objects và interface names để configure sau.

    Structure trả về:
    {
      'MPLS': {
        'BL':  {'link': lk, 'gw_intf': 'blgw_mpls_g', 'sw_intf': 'blgw_mpls_s',
                'gw_host': host_obj, 'sw': sw_obj, 'gw_ip': '172.16.10.1/24'},
        'NT':  {...},
        'HCM': {...},
        'DC':  {...},
      },
      'FIVEG': {...},
      ...
    }
    """
    wan_cfg = _load_wan_config()
    site_octets = wan_cfg['site_octets']

    site_gws = {
        'BL':  bl_nodes['gw'],
        'NT':  nt_nodes['dist']['NT_DIST01'],
        'HCM': hcm_nodes['dist']['HCM_DIST01'],
        'DC':  dc_nodes['gw'],
    }

    wan_links = {}

    for path_name, profile in wan_cfg['paths'].items():
        sw      = wan_switches[path_name]
        subnet  = profile['subnet']  # VD: '172.16.10'
        path_code = path_name[:4].lower()  # 'mpls', 'five', 'inet', 'vpn_', 'lte_'
        if path_name == 'FIVEG':
            path_code = '5g'

        path_links = {}

        for site_code, gw_host in site_gws.items():
            octet   = site_octets[site_code]
            gw_ip   = f'{subnet}.{octet}/24'

            # Tên interface (max 15 chars, unique per link)
            gw_intf_name = _safe_intf_name(gw_host.name, path_code, 'g')
            sw_intf_name = _safe_intf_name(gw_host.name, path_code, 's')

            lk = net.addLink(
                gw_host, sw,
                intfName1=gw_intf_name,
                intfName2=sw_intf_name,
            )

            path_links[site_code] = {
                'link':     lk,
                'gw_intf':  lk.intf1.name,
                'sw_intf':  lk.intf2.name,
                'gw_ip':    gw_ip,
                'gw_host':  gw_host,
                'sw':       sw,
            }

            info(f'  [WAN] {gw_host.name} ─{path_name}─ {sw.name} '
                 f'[{gw_intf_name} ↔ {sw_intf_name}]\n')

        wan_links[path_name] = path_links

    return wan_links


# ─────────────────────────────────────────────────────────────
# Configure Phase (sau net.start())
# ─────────────────────────────────────────────────────────────

def configure_wan_ips_and_netem(wan_links: dict):
    """
    Sau net.start(): gán IP + apply tc netem trên tất cả WAN interfaces.
    """
    wan_cfg = _load_wan_config()

    for path_name, path_links in wan_links.items():
        profile = wan_cfg['paths'][path_name]
        delay  = profile['delay_ms']
        jitter = profile['jitter_ms']
        loss   = profile['loss_pct']
        bw     = profile['bandwidth_mbps']
        corr   = profile.get('correlation_pct', 25)

        info(f'[WAN] Configuring {path_name}: '
             f'delay={delay}ms jitter={jitter}ms '
             f'loss={loss}% bw={bw}Mbps\n')

        for site_code, link_info in path_links.items():
            gw_host = link_info['gw_host']
            gw_intf = link_info['gw_intf']
            sw      = link_info['sw']
            sw_intf = link_info['sw_intf']
            gw_ip   = link_info['gw_ip']

            # Gán IP
            gw_host.cmd(f'ip addr add {gw_ip} dev {gw_intf} 2>/dev/null')
            gw_host.cmd(f'ip link set {gw_intf} up')

            # tc netem trên GW egress (gói tin ra khỏi GW → WAN switch)
            # _apply_netem(gw_host, gw_intf, delay, jitter, loss, bw, corr)  # cmt phần tạo lưu lượng ảo / đặc tính mạng

            # tc netem trên WAN switch egress → GW (reverse path)
            # _apply_netem(sw, sw_intf, delay, jitter, loss, bw, corr)  # cmt phần tạo lưu lượng ảo / đặc tính mạng

        info(f'[WAN] {path_name} ✓\n')


def _apply_netem(host, intf: str,
                 delay_ms: int, jitter_ms: int,
                 loss_pct: float, bw_mbps: int,
                 corr_pct: int = 25):
    """
    Áp dụng tc netem + tbf (token bucket filter) trên 1 interface.
    HTB (hierarchy): root tbf → child netem (kết hợp bandwidth limit + delay/loss).
    """
    # Xóa qdisc cũ
    host.cmd(f'tc qdisc del dev {intf} root 2>/dev/null')

    # Áp dụng: netem với bandwidth limit
    # Dùng netem trực tiếp với rate (Linux 4.x+ hỗ trợ rate trong netem)
    cmd = (
        f'tc qdisc add dev {intf} root handle 1: '
        f'netem '
        f'delay {delay_ms}ms {jitter_ms}ms {corr_pct}% '
        f'loss {loss_pct}% '
        f'rate {bw_mbps}mbit'
    )
    result = host.cmd(cmd)

    if 'Error' in result or 'error' in result:
        # Fallback: netem không có rate (kernel cũ)
        host.cmd(
            f'tc qdisc add dev {intf} root handle 1: '
            f'netem delay {delay_ms}ms {jitter_ms}ms '
            f'loss {loss_pct}%'
        )


def get_wan_interface(site_gw_host, path_name: str) -> str | None:
    """
    Tìm tên interface của site GW kết nối vào WAN path.
    Dùng bởi SD-WAN Controller để steeer traffic.
    """
    path_code = path_name[:4].lower()
    if path_name == 'FIVEG':
        path_code = '5g'

    for intf in site_gw_host.intfList():
        if path_code in intf.name and intf.name != 'lo':
            return intf.name
    return None


def apply_fault_to_path(wan_links: dict, path_name: str,
                         fault_preset: str = 'congestion'):
    """
    Inject fault vào 1 WAN path.
    fault_preset: 'congestion' | 'partial_degradation' | 'high_jitter_voip' | 'complete_failure'
    """
    wan_cfg = _load_wan_config()
    preset  = wan_cfg['fault_presets'].get(fault_preset, {})

    if preset.get('action') == 'link_down':
        # Tắt toàn bộ interfaces của path
        for site_code, link_info in wan_links[path_name].items():
            gw_host = link_info['gw_host']
            gw_intf = link_info['gw_intf']
            gw_host.cmd(f'ip link set {gw_intf} down')
        info(f'[WAN FAULT] {path_name}: LINK DOWN\n')
    else:
        # Áp dụng degraded netem
        for site_code, link_info in wan_links[path_name].items():
            gw_host = link_info['gw_host']
            gw_intf = link_info['gw_intf']
            sw      = link_info['sw']
            sw_intf = link_info['sw_intf']

            _apply_netem(
                gw_host, gw_intf,
                preset['delay_ms'], preset['jitter_ms'],
                preset['loss_pct'], preset['bandwidth_mbps']
            )
            _apply_netem(
                sw, sw_intf,
                preset['delay_ms'], preset['jitter_ms'],
                preset['loss_pct'], preset['bandwidth_mbps']
            )
        info(f'[WAN FAULT] {path_name}: {fault_preset} applied\n')


def restore_path(wan_links: dict, path_name: str):
    """Khôi phục WAN path về trạng thái bình thường."""
    wan_cfg = _load_wan_config()
    profile = wan_cfg['paths'][path_name]

    for site_code, link_info in wan_links[path_name].items():
        gw_host = link_info['gw_host']
        gw_intf = link_info['gw_intf']
        sw      = link_info['sw']
        sw_intf = link_info['sw_intf']

        # Bring up nếu bị down
        gw_host.cmd(f'ip link set {gw_intf} up')

        # Restore netem
        _apply_netem(
            gw_host, gw_intf,
            profile['delay_ms'], profile['jitter_ms'],
            profile['loss_pct'], profile['bandwidth_mbps']
        )
        _apply_netem(
            sw, sw_intf,
            profile['delay_ms'], profile['jitter_ms'],
            profile['loss_pct'], profile['bandwidth_mbps']
        )

    info(f'[WAN RESTORE] {path_name}: restored to normal\n')
