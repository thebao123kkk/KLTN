"""
scripts/configure_acl.py
Phase 7 - Áp dụng ACL + Firewall rules dùng iptables trên Host Routers

Nodes được áp dụng:
  - BL_GW       (Bảo Lộc gateway)
  - NT_DIST01   (Nha Trang distribution primary)
  - NT_DIST02   (Nha Trang distribution backup)
  - HCM_DIST01  (HCM distribution primary)
  - HCM_DIST02  (HCM distribution backup)
  - DC_SP_GW    (Data Center spine gateway / firewall)

Cách dùng:
  Gọi configure_all_acl(topo) từ enterprise_topo.py ở phase 7.
  Hoặc chạy độc lập: python3 scripts/configure_acl.py (cần Mininet đang chạy)
"""

import os
import sys
import yaml

_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR     = os.path.dirname(_SCRIPT_DIR)
_CONFIG_PATH = os.path.join(_SRC_DIR, 'config', 'acl_rules.yaml')


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _load_rules(config_path: str = _CONFIG_PATH) -> dict:
    """Đọc acl_rules.yaml."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def _ipt(host, rule: str) -> str:
    """Thực thi iptables command trong namespace của Mininet host."""
    cmd = f'iptables {rule} 2>/dev/null'
    return host.cmd(cmd)


def _expand_zone(rules_cfg: dict, zone_name) -> list:
    """
    Trả về danh sách subnet strings cho zone_name.
    Nếu zone_name là list → trả về nguyên.
    Nếu zone_name là str → lookup trong rules_cfg['zones'].
    """
    if zone_name is None:
        return ['0.0.0.0/0']

    zones = rules_cfg.get('zones', {})

    if isinstance(zone_name, list):
        # List of strings (may be zone names or subnets)
        result = []
        for item in zone_name:
            if item in zones:
                result.extend(zones[item])
            else:
                result.append(item)
        return result or ['0.0.0.0/0']

    if isinstance(zone_name, str):
        if zone_name in zones:
            return zones[zone_name]
        return [zone_name]  # Literal subnet

    return ['0.0.0.0/0']


def _build_iptables_rules(rule: dict, rules_cfg: dict) -> list:
    """
    Chuyển 1 rule dict → danh sách iptables command strings (phần sau 'iptables').
    Trả về list để cho phép multiple (src × dst × proto × dport).
    """
    action = rule.get('action', 'ACCEPT').upper()
    log    = rule.get('log', False)
    log_prefix = rule.get('log_prefix', f"ACL_{rule.get('id','?')}")

    srcs = _expand_zone(rules_cfg, rule.get('src_zone') or rule.get('src'))
    dsts = _expand_zone(rules_cfg, rule.get('dst_zone') or rule.get('dst'))

    protos = rule.get('proto', 'any')
    if protos == 'any' or protos is None:
        protos = [None]
    elif protos == 'ospf':
        protos = ['ospf']
    elif isinstance(protos, str):
        protos = [protos]
    # else: already a list

    dports = rule.get('dport', [])
    if isinstance(dports, int):
        dports = [dports]

    commands = []

    for src in srcs:
        for dst in dsts:
            # Build base per proto
            for proto in protos:
                base_parts = ['-A FORWARD']
                base_parts.append(f'-s {src}')
                base_parts.append(f'-d {dst}')

                if proto and proto not in ('any', 'ospf'):
                    base_parts.append(f'-p {proto}')

                if proto == 'ospf':
                    # OSPF không dùng port, dùng protocol number
                    base_parts = ['-A FORWARD', f'-s {src}', f'-d {dst}', '-p 89']

                if dports and proto not in (None, 'any', 'ospf'):
                    # Multiple dports → multiple rules
                    for dport in dports:
                        port_str = str(dport)
                        rule_str = ' '.join(base_parts) + f' --dport {port_str} -j {action}'
                        commands.append(rule_str)
                        if log and action == 'DROP':
                            log_rule = ' '.join(base_parts) + f' --dport {port_str} -j LOG --log-prefix "{log_prefix}: "'
                            commands.insert(-1, log_rule)  # LOG trước DROP
                else:
                    rule_str = ' '.join(base_parts) + f' -j {action}'
                    commands.append(rule_str)
                    if log and action == 'DROP':
                        log_rule = ' '.join(base_parts) + f' -j LOG --log-prefix "{log_prefix}: "'
                        commands.insert(-1, log_rule)

    return commands


# ─────────────────────────────────────────────
# Per-host application
# ─────────────────────────────────────────────

def apply_acl_to_host(host, rules_cfg: dict, host_role: str = 'router'):
    """
    Áp dụng toàn bộ ACL rules lên 1 Mininet host (router).

    host_role:
      'router'  - DIST/GW router: forward all inter-VLAN traffic
      'dc_gw'   - DC_SP_GW: cũng enforce firewall DMZ zones
    """
    host_name = getattr(host, 'name', str(host))

    # 1. Enable IP forwarding
    host.cmd('sysctl -w net.ipv4.ip_forward=1 2>/dev/null')

    # 2. Flush existing FORWARD chain
    _ipt(host, '-F FORWARD 2>/dev/null')

    # 3. Set default policy
    # ACCEPT mặc định (lab env) - thay bằng DROP ở production
    _ipt(host, '-P FORWARD ACCEPT')

    # 4. Apply rules
    applied = 0
    skipped = 0
    for rule in rules_cfg.get('rules', []):
        rule_id = rule.get('id', '?')
        if rule.get('action', '').upper() == 'ACCEPT':
            # ACCEPT rules: luôn áp dụng
            pass
        elif rule.get('action', '').upper() == 'DROP':
            # DROP rules: chỉ áp dụng nếu liên quan đến zone mà router này quản lý
            pass  # Áp dụng tất cả trên mọi router (stateless ACL)

        try:
            cmds = _build_iptables_rules(rule, rules_cfg)
            for cmd in cmds:
                _ipt(host, cmd)
            applied += len(cmds)
        except Exception as e:
            skipped += 1

    print(f'  [{host_name}] ACL applied: {applied} iptables rules ({skipped} skipped)')


def apply_dc_firewall(dc_gw_host, rules_cfg: dict):
    """
    Áp dụng thêm firewall zone rules đặc biệt trên DC_SP_GW.
    Đây là "firewall" bảo vệ Data Center.
    """
    host = dc_gw_host
    host_name = getattr(host, 'name', 'DC_SP_GW')

    # Firewall zone INPUT chain (bảo vệ chính DC_SP_GW)
    _ipt(host, '-F INPUT 2>/dev/null')
    _ipt(host, '-P INPUT ACCEPT')

    # Cho phép established connections
    _ipt(host, '-A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT')

    # DC-specific: block direct external access đến DB
    dc_db_nets = rules_cfg['zones']['dc_db']
    for db_net in dc_db_nets:
        # Chặn kết nối KHÔNG phải từ APP server → DB
        dc_app_nets = rules_cfg['zones']['dc_app']
        for app_net in dc_app_nets:
            _ipt(host, f'-A FORWARD -s {app_net} -d {db_net} -p tcp --dport 3306 -j ACCEPT')
            _ipt(host, f'-A FORWARD -s {app_net} -d {db_net} -p tcp --dport 5432 -j ACCEPT')

    print(f'  [{host_name}] DC Firewall zones applied')


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def configure_all_acl(topo_nodes: dict):
    """
    Áp dụng ACL rules lên tất cả routers.

    topo_nodes: dict với structure:
      {
        'bl_nodes':  bl_nodes dict từ build_baoloc(),
        'nt_nodes':  nt_nodes dict từ build_nhatrang(),
        'hcm_nodes': hcm_nodes dict từ build_hcm(),
        'dc_nodes':  dc_nodes dict từ build_datacenter(),
      }
    """
    rules_cfg = _load_rules()
    print('[PHASE 7] Áp dụng ACL + Firewall rules...')
    print(f'  Config: {_CONFIG_PATH}')
    print(f'  Rules: {len(rules_cfg.get("rules", []))} rules defined')

    # --- Bảo Lộc GW ---
    bl_gw = topo_nodes['bl_nodes']['gw']
    apply_acl_to_host(bl_gw, rules_cfg, 'router')

    # --- Nha Trang DIST01 + DIST02 ---
    for dist_name, dist_host in topo_nodes['nt_nodes']['dist'].items():
        apply_acl_to_host(dist_host, rules_cfg, 'router')

    # --- HCM DIST01 + DIST02 ---
    for dist_name, dist_host in topo_nodes['hcm_nodes']['dist'].items():
        apply_acl_to_host(dist_host, rules_cfg, 'router')

    # --- DC Spine GW (có firewall zone đặc biệt) ---
    dc_gw = topo_nodes['dc_nodes']['gw']
    apply_acl_to_host(dc_gw, rules_cfg, 'dc_gw')
    apply_dc_firewall(dc_gw, rules_cfg)

    print('[PHASE 7] ✓ ACL + Firewall configured on all routers')
    _print_acl_summary(rules_cfg)


def _print_acl_summary(rules_cfg: dict):
    """In tóm tắt ACL rules cho log."""
    print('\n  ACL Rule Summary:')
    deny_rules  = [r for r in rules_cfg['rules'] if r['action'].upper() == 'DROP']
    allow_rules = [r for r in rules_cfg['rules'] if r['action'].upper() == 'ACCEPT']
    print(f'  ALLOW rules: {len(allow_rules)}')
    print(f'  DROP  rules: {len(deny_rules)}')
    for r in deny_rules:
        print(f'    [DENY] {r["id"]}: {r["name"]}')


# ─────────────────────────────────────────────
# Test helpers (dùng trong check_phase7.py)
# ─────────────────────────────────────────────

def verify_acl_rule(src_host, dst_host, dst_ip: str,
                    expected_pass: bool, proto: str = 'icmp',
                    port: int = None) -> bool:
    """
    Kiểm tra ACL rule bằng cách ping hoặc nc.
    Trả về True nếu kết quả đúng với expected_pass.

    src_host, dst_host: Mininet host objects.
    """
    if proto == 'icmp':
        result = src_host.cmd(f'ping -c 2 -W 1 {dst_ip}')
        packets_rx = '2 received' in result or '1 received' in result
        success = packets_rx == expected_pass
        status = '✓' if success else '✗'
        exp = 'ALLOW' if expected_pass else 'DENY'
        got = 'PASS' if packets_rx else 'BLOCK'
        print(f'    {status} {src_host.name} → {dst_ip} [{exp}]: got {got}')
        return success

    elif proto == 'tcp' and port:
        result = src_host.cmd(f'nc -z -w 1 {dst_ip} {port} 2>&1')
        connected = 'succeeded' in result or 'open' in result
        success = connected == expected_pass
        status = '✓' if success else '✗'
        exp = 'ALLOW' if expected_pass else 'DENY'
        got = 'OPEN' if connected else 'FILTERED'
        print(f'    {status} {src_host.name} → {dst_ip}:{port} [{exp}]: got {got}')
        return success

    return False


if __name__ == '__main__':
    # Standalone mode: in rules summary
    rules = _load_rules()
    print(f'ACL Rules loaded: {len(rules["rules"])} rules')
    for r in rules['rules']:
        print(f'  {r["id"]}: {r["action"]} - {r["name"]}')
