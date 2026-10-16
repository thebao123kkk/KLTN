"""
scripts/configure_qos.py
Phase 11 — QoS: DSCP Marking + tc HTB Queuing trên WAN interfaces.

Mục tiêu:
  1. Đánh dấu DSCP trên tất cả gói tin qua iptables MANGLE table.
  2. Triển khai tc HTB queuing trên WAN interfaces của 4 site GW.
  3. Ưu tiên VoIP/RTP (DSCP EF) qua Priority Queue riêng.

Cách gọi từ enterprise_topo.py (Phase 11):
    from scripts.configure_qos import configure_all_qos
    configure_all_qos(topo_nodes, wan_info)
"""

import os
import sys
import yaml
from mininet.log import info

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR    = os.path.join(_SCRIPT_DIR, '..')
_CONFIG_DIR = os.path.join(_SRC_DIR, 'config')


def _load_qos_config() -> dict:
    """Đọc config/qos.yaml."""
    with open(os.path.join(_CONFIG_DIR, 'qos.yaml')) as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────────────────────
# DSCP Marking via iptables MANGLE
# ─────────────────────────────────────────────────────────────

def _apply_dscp_marking(host, qos_cfg: dict):
    """
    Đánh dấu DSCP trên host bằng iptables -t mangle.
    Gọi trên tất cả GW routers để tất cả outgoing WAN traffic được mark đúng.
    """
    host.cmd('iptables -t mangle -F OUTPUT 2>/dev/null')
    host.cmd('iptables -t mangle -F FORWARD 2>/dev/null')

    for class_name, cfg in qos_cfg['dscp_classes'].items():
        dscp = cfg.get('dscp', 0)
        match = cfg.get('match', {})

        if class_name == 'default':
            continue

        proto_list = match.get('proto', [])
        if isinstance(proto_list, str):
            proto_list = [proto_list]

        dports = match.get('dport', [])
        if isinstance(dports, int):
            dports = [dports]

        dport_range = match.get('dport_range', None)
        src_nets    = match.get('src', [])
        dst_nets    = match.get('dst', [])

        if isinstance(src_nets, str):
            src_nets = [src_nets]
        if isinstance(dst_nets, str):
            dst_nets = [dst_nets]

        for proto in (proto_list if proto_list else ['tcp']):
            if proto == 'ospf':
                continue

            base_rule = f'-t mangle -A FORWARD -p {proto}'

            # Source subnet match
            if src_nets:
                for src in src_nets:
                    src_flag = f'-s {src}' if src else ''
                    _build_dscp_rule(host, base_rule, src_flag, '', dports, dport_range, dscp)
            elif dst_nets:
                for dst in dst_nets:
                    dst_flag = f'-d {dst}' if dst else ''
                    _build_dscp_rule(host, base_rule, '', dst_flag, dports, dport_range, dscp)
            else:
                _build_dscp_rule(host, base_rule, '', '', dports, dport_range, dscp)

    info(f'  [QoS] DSCP marking applied on {host.name}\n')


def _build_dscp_rule(host, base: str, src_flag: str, dst_flag: str,
                     dports: list, dport_range, dscp: int):
    """Helper: sinh 1 iptables mangle DSCP rule và thực thi."""
    if dports:
        for port in dports:
            cmd = f'iptables {base} {src_flag} {dst_flag} --dport {port} -j DSCP --set-dscp {dscp}'
            host.cmd(cmd)
    elif dport_range:
        lo, hi = dport_range
        cmd = f'iptables {base} {src_flag} {dst_flag} --dport {lo}:{hi} -j DSCP --set-dscp {dscp}'
        host.cmd(cmd)
    else:
        cmd = f'iptables {base} {src_flag} {dst_flag} -j DSCP --set-dscp {dscp}'
        host.cmd(cmd)


# ─────────────────────────────────────────────────────────────
# tc HTB Queuing trên WAN Interfaces
# ─────────────────────────────────────────────────────────────

def _apply_htb_queue(gw_host, intf: str, path_name: str, qos_cfg: dict):
    """
    Áp dụng tc HTB hierarchical queue trên 1 WAN interface.

    Cấu trúc HTB:
      root qdisc → HTB class root (1:0)
        ├── class 1:10 — VoIP (Priority 1, Guaranteed BW)
        │   └── sfq (Stochastic Fair Queuing)
        ├── class 1:20 — Business DB/App (Priority 2)
        │   └── sfq
        └── class 1:30 — Default/Bulk (Priority 3)
            └── sfq
    """
    path_cfg = qos_cfg['htb_config']['paths'].get(path_name)
    if not path_cfg:
        info(f'  [QoS] No HTB config for path {path_name}, skipping {intf}\n')
        return

    total_rate = path_cfg['total_rate']
    voip_cfg     = path_cfg['classes']['voip']
    biz_cfg      = path_cfg['classes']['business']
    default_cfg  = path_cfg['classes']['default']

    gw = gw_host

    # Xóa qdisc cũ
    gw.cmd(f'tc qdisc del dev {intf} root 2>/dev/null')

    # Root HTB qdisc (handle 1:0)
    gw.cmd(f'tc qdisc add dev {intf} root handle 1: htb default 30')

    # Root class (1:1) = tổng bandwidth
    gw.cmd(f'tc class add dev {intf} parent 1: classid 1:1 htb rate {total_rate} ceil {total_rate}')

    # VoIP class (1:10)
    gw.cmd(
        f'tc class add dev {intf} parent 1:1 classid 1:10 htb '
        f'rate {voip_cfg["rate"]} ceil {voip_cfg["ceil"]} '
        f'prio {voip_cfg["priority"]} burst {voip_cfg["burst"]}'
    )
    gw.cmd(f'tc qdisc add dev {intf} parent 1:10 handle 10: sfq perturb 10')

    # Business class (1:20)
    gw.cmd(
        f'tc class add dev {intf} parent 1:1 classid 1:20 htb '
        f'rate {biz_cfg["rate"]} ceil {biz_cfg["ceil"]} '
        f'prio {biz_cfg["priority"]} burst {biz_cfg["burst"]}'
    )
    gw.cmd(f'tc qdisc add dev {intf} parent 1:20 handle 20: sfq perturb 10')

    # Default/Bulk class (1:30)
    gw.cmd(
        f'tc class add dev {intf} parent 1:1 classid 1:30 htb '
        f'rate {default_cfg["rate"]} ceil {default_cfg["ceil"]} '
        f'prio {default_cfg["priority"]} burst {default_cfg["burst"]}'
    )
    gw.cmd(f'tc qdisc add dev {intf} parent 1:30 handle 30: sfq perturb 10')

    # tc filter: Phân loại traffic theo DSCP vào từng class
    # VoIP EF (DSCP 46 → TOS 0xB8)
    gw.cmd(
        f'tc filter add dev {intf} parent 1: protocol ip prio 1 u32 '
        f'match ip dsfield 0xB8 0xFC classid 1:10'
    )
    # VoIP SIP AF31 (DSCP 26 → TOS 0x68)
    gw.cmd(
        f'tc filter add dev {intf} parent 1: protocol ip prio 2 u32 '
        f'match ip dsfield 0x68 0xFC classid 1:10'
    )
    # Business AF21 (DSCP 18 → TOS 0x48)
    gw.cmd(
        f'tc filter add dev {intf} parent 1: protocol ip prio 3 u32 '
        f'match ip dsfield 0x48 0xFC classid 1:20'
    )
    # Web AF11 (DSCP 10 → TOS 0x28)
    gw.cmd(
        f'tc filter add dev {intf} parent 1: protocol ip prio 4 u32 '
        f'match ip dsfield 0x28 0xFC classid 1:20'
    )
    # Default BE (DSCP 0) → class 1:30 (implicit via HTB default 30)

    info(f'  [QoS] HTB queue applied on {gw.name} {intf} (path={path_name})\n')


# ─────────────────────────────────────────────────────────────
# Public Entry Point
# ─────────────────────────────────────────────────────────────

def configure_all_qos(topo_nodes: dict, wan_info: dict):
    """
    Hàm chính gọi từ enterprise_topo.py Phase 11.

    topo_nodes: {'bl_nodes': ..., 'nt_nodes': ..., 'hcm_nodes': ..., 'dc_nodes': ...}
    wan_info: dict trả về từ connect_sites_wan() (chứa wan_links)
    """
    qos_cfg = _load_qos_config()

    gw_nodes = {
        'BL':  topo_nodes['bl_nodes']['gw'],
        'NT':  topo_nodes['nt_nodes']['dist']['NT_DIST01'],
        'HCM': topo_nodes['hcm_nodes']['dist']['HCM_DIST01'],
        'DC':  topo_nodes['dc_nodes']['gw'],
    }

    info('[QoS] Phase 11: Applying DSCP marking on all GW routers...\n')

    # Step 1: DSCP Marking trên tất cả GW routers
    for site, gw in gw_nodes.items():
        _apply_dscp_marking(gw, qos_cfg)

    info('[QoS] Phase 11: Applying HTB queuing on WAN interfaces...\n')

    # Step 2: HTB Queuing trên WAN interfaces
    wan_links = wan_info.get('wan_links', {})
    for path_name, path_links in wan_links.items():
        for site_code, link_info in path_links.items():
            gw_host = link_info['gw_host']
            gw_intf = link_info['gw_intf']
            _apply_htb_queue(gw_host, gw_intf, path_name, qos_cfg)

    info('[PHASE 11] ✓ QoS (DSCP + HTB) configured on all WAN paths\n')
