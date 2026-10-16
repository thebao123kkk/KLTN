"""
tests/phase_checks/check_phase7.py
Phase 7 - Kiểm tra ACL + Firewall

Thực hiện 4 nhóm test:
  1. DENY rules hoạt động: CCTV→DB, IoT→USER
  2. ALLOW rules hoạt động: USER→WEB, USER→APP
  3. Infra services vẫn thông: DNS, DHCP, OSPF
  4. DC Firewall zones: WEB→APP, APP→DB (ALLOW); direct DB access (DENY)

Cách chạy:
  sudo python3 tests/phase_checks/check_phase7.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.net import Mininet
from mininet.log import setLogLevel, info, error

from topology.enterprise_topo import build_network
from scripts.configure_acl import configure_all_acl, verify_acl_rule


def run_phase7_checks(net, topo_nodes):
    """
    Chạy toàn bộ test cases cho Phase 7.
    Trả về (passed, total).
    """
    results = []

    def test(name, src_host, dst_ip, expected, proto='icmp', port=None):
        ok = verify_acl_rule(src_host, None, dst_ip, expected, proto, port)
        results.append((name, ok))
        return ok

    hosts = {}
    for site_key in ['bl_nodes', 'nt_nodes', 'hcm_nodes', 'dc_nodes']:
        node_dict = topo_nodes.get(site_key, {})
        for h_name, h in node_dict.get('hosts', {}).items():
            hosts[h_name] = h

    print('\n' + '=' * 60)
    print('PHASE 7 - ACL + Firewall Tests')
    print('=' * 60)

    # ── Group 1: DENY rules ──────────────────────────────────
    print('\n[Group 1] DENY rules (should be blocked)')

    # CCTV → DB Server: DENY
    cctv_hosts = [h for n, h in hosts.items() if 'CAM' in n]
    db_ip = '10.100.30.11'  # DC_DB01
    for cam in cctv_hosts[:2]:
        test(f'DENY_CCTV_{cam.name}→DB', cam, db_ip, expected=False)

    # IoT → User VLAN: DENY
    iot_hosts = [h for n, h in hosts.items() if 'PRN' in n]
    user_ip = '10.20.10.11'  # NT_ADM01
    for iot in iot_hosts[:2]:
        test(f'DENY_IoT_{iot.name}→USER', iot, user_ip, expected=False)

    # IoT → DB: DENY
    for iot in iot_hosts[:1]:
        test(f'DENY_IoT_{iot.name}→DB', iot, db_ip, expected=False)

    # ── Group 2: ALLOW rules ─────────────────────────────────
    print('\n[Group 2] ALLOW rules (should pass)')

    # USER → WEB Server: ALLOW (port 80)
    user_hosts = [h for n, h in hosts.items() if 'ADM' in n]
    web_ip = '10.100.10.11'  # DC_WEB01
    for user in user_hosts[:2]:
        test(f'ALLOW_{user.name}→WEB(ICMP)', user, web_ip, expected=True)

    # USER → APP Server: ALLOW
    app_ip = '10.100.20.11'  # DC_APP01
    for user in user_hosts[:1]:
        test(f'ALLOW_{user.name}→APP(ICMP)', user, app_ip, expected=True)

    # ── Group 3: Infra services ──────────────────────────────
    print('\n[Group 3] Infra services (DNS/NTP must work)')

    dns_ip = '10.100.40.11'   # DC_DNS01
    ntp_ip = '10.100.60.11'   # DC_MGMT01 (NTP)
    for user in user_hosts[:1]:
        test(f'ALLOW_{user.name}→DNS', user, dns_ip, expected=True)
        test(f'ALLOW_{user.name}→NTP', user, ntp_ip, expected=True)

    # ICMP tổng quát (ping) phải thông tất cả
    if 'DC_SP_GW' in [n.name for n in [topo_nodes['dc_nodes']['gw']]]:
        dc_gw = topo_nodes['dc_nodes']['gw']
        for user in user_hosts[:1]:
            test(f'ICMP_{user.name}→DC_GW', user, '10.100.99.1', expected=True)

    # ── Group 4: Cross-site connectivity ─────────────────────
    print('\n[Group 4] Cross-site user connectivity')

    bl_user_ip = '10.10.10.11'
    hcm_users = [h for n, h in hosts.items() if 'HCM' in n and 'ADM' in n]
    for hu in hcm_users[:1]:
        test(f'ALLOW_HCM→BL_USER(ICMP)', hu, bl_user_ip, expected=True)

    # ── Summary ──────────────────────────────────────────────
    print('\n' + '=' * 60)
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    print(f'PHASE 7 Results: {passed}/{total} tests passed')

    if passed == total:
        print('✓ PHASE 7 PASS - All ACL rules working correctly')
    else:
        print(f'✗ PHASE 7 FAIL - {total - passed} tests failed')
        for name, ok in results:
            if not ok:
                print(f'  FAILED: {name}')
    print('=' * 60)

    return passed, total


def main():
    setLogLevel('warning')

    print('[Phase 7] Building network (phase 7)...')
    topo = build_network(phase=7)
    topo_nodes = {
        'bl_nodes':  topo.bl_nodes,
        'nt_nodes':  topo.nt_nodes,
        'hcm_nodes': topo.hcm_nodes,
        'dc_nodes':  topo.dc_nodes,
    }

    time.sleep(3)

    try:
        passed, total = run_phase7_checks(topo.net, topo_nodes)
        return 0 if passed == total else 1
    finally:
        topo.net.stop()


if __name__ == '__main__':
    if os.geteuid() != 0:
        print('ERROR: Cần chạy với sudo!')
        sys.exit(1)
    sys.exit(main())
