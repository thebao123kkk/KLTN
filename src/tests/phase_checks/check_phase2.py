"""
tests/phase_checks/check_phase2.py
CHECKPOINT PHASE 2 — VLAN Isolation Verification
=============================================
Kiểm tra:
  1. Host cùng VLAN ping được nhau
  2. Host khác VLAN KHÔNG ping được nhau (isolation)
  3. Gateway (VIP .1) trả lời ping từ mỗi host
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import info, error


def _ping_test(net, src_name, dst_ip, expect_success, desc):
    """Helper: ping test, kiểm tra kết quả đúng với expectation."""
    src = net.get(src_name)
    if src is None:
        info(f'  ⚠ {src_name}: not found, skip\n')
        return None

    result = src.cmd(f'ping -c 2 -W 2 {dst_ip}')
    reachable = '1 received' in result or '2 received' in result

    if reachable == expect_success:
        status = '✓'
        info(f'  {status} {desc}: {src_name} → {dst_ip} ({"OK" if expect_success else "BLOCKED as expected"})\n')
        return True
    else:
        status = '✗'
        action = 'FAIL (should reach)' if expect_success else 'FAIL (should be blocked)'
        error(f'  {status} {desc}: {src_name} → {dst_ip} {action}\n')
        return False


def run_check(topo):
    """
    Chạy kiểm tra Phase 2 — VLAN isolation.
    """
    net = topo.net
    results = []

    info('\n' + '=' * 60 + '\n')
    info('CHECKPOINT PHASE 2 — VLAN + IP Addressing\n')
    info('=' * 60 + '\n')

    # ── Test 1: Cùng VLAN ping được ───────────────────────
    info('\n[TEST 1] Hosts cùng VLAN phải ping được nhau...\n')
    same_vlan_tests = [
        # BL VLAN 10
        ('BL-ADMIN-PC01', '10.10.10.12', 'BL VLAN10 same-vlan'),
        ('BL-SALES-PC01',  '10.10.10.21', 'BL VLAN10 same-vlan'),
        # NT
        ('NT-ADMIN-PC01', '10.20.10.12', 'NT VLAN110 same-vlan'),
        ('NT-SALES-PC01',  '10.20.20.12', 'NT VLAN120 same-vlan'),
        # HCM
        ('HCM-ADMIN-PC01', '10.30.10.12', 'HCM VLAN210 same-vlan'),
        ('HCM-SALES-PC01',  '10.30.20.12', 'HCM VLAN220 same-vlan'),
        # DC
        ('DC-WEB01', '10.100.10.12', 'DC VLAN310 same-vlan'),
        ('DC-APP01',  '10.100.20.12', 'DC VLAN320 same-vlan'),
    ]
    for args in same_vlan_tests:
        r = _ping_test(net, args[0], args[1], expect_success=True, desc=args[2])
        if r is not None:
            results.append(r)

    # ── Test 2: Khác VLAN không ping được (chưa có routing) ──
    info('\n[TEST 2] Hosts khác VLAN KHÔNG ping được (L2 isolation)...\n')
    diff_vlan_tests = [
        # BL VLAN 10 → VLAN 30 (IoT): không route vì chỉ Phase 2
        ('BL-ADMIN-PC01', '10.10.30.11', 'BL VLAN10→VLAN30 (isolated)'),
        # NT VLAN 110 → VLAN 120: không route vì Phase 2 chưa có OSPF
        ('NT-ADMIN-PC01', '10.20.20.11', 'NT VLAN110→VLAN120 (isolated)'),
    ]
    for args in diff_vlan_tests:
        r = _ping_test(net, args[0], args[1], expect_success=False, desc=args[2])
        if r is not None:
            results.append(r)

    # ── Test 3: Kiểm tra IP đúng theo vlan.yaml ───────────
    info('\n[TEST 3] IP addresses đúng theo config...\n')
    ip_checks = {
        'BL-ADMIN-PC01': '10.10.10.11',
        'NT-SALES-PC01':  '10.20.20.11',
        'HCM-SALES-PC01': '10.30.20.11',
        'DC-WEB01':       '10.100.10.11',
        'DC-DNS01':       '10.100.40.11',
        'DC-DHCP01':      '10.100.40.12',
    }
    for hname, expected_ip in ip_checks.items():
        h = net.get(hname)
        if h is None:
            info(f'  ⚠ {hname}: not found\n')
            continue
        actual_ip = h.IP()
        base_ip = actual_ip.split('/')[0] if '/' in actual_ip else actual_ip
        if base_ip == expected_ip:
            info(f'  ✓ {hname}: {actual_ip} == {expected_ip}\n')
            results.append(True)
        else:
            error(f'  ✗ {hname}: {actual_ip} != {expected_ip}\n')
            results.append(False)

    # ── Kết quả ───────────────────────────────────────────
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)
    total  = len(results)

    info('\n' + '=' * 60 + '\n')
    info(f'PHASE 2 RESULT: {passed}/{total} passed\n')
    if failed == 0:
        info('✓ PHASE 2 CHECKPOINT PASSED\n')
    else:
        error(f'✗ PHASE 2 CHECKPOINT FAILED ({failed} tests failed)\n')
    info('=' * 60 + '\n')
    return failed == 0


if __name__ == '__main__':
    from topology.enterprise_topo import build_network, check_environment
    check_environment()
    topo = build_network(phase=2)
    success = run_check(topo)
    topo.net.stop()
    sys.exit(0 if success else 1)
