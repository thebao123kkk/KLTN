"""
tests/phase_checks/check_phase1.py
CHECKPOINT PHASE 1 — Enterprise Topology Verification
=============================================
Kiểm tra:
  1. Tất cả switch và host đã khởi động
  2. Tất cả link UP
  3. Các host cùng switch ping được nhau ở L2

Cách chạy:
  sudo python3 -c "
  from tests.phase_checks.check_phase1 import run_check
  # Truyền vào topo object từ enterprise_topo.py
  run_check(topo)
  "

Hoặc chạy trực tiếp (tự tạo topo):
  sudo python3 tests/phase_checks/check_phase1.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import info, error


def run_check(topo):
    """
    Chạy kiểm tra Phase 1.
    
    Parameters
    ----------
    topo : EnterpriseTopo
        Object từ enterprise_topo.build_network(phase=1)
    
    Returns
    -------
    bool : True nếu pass, False nếu fail
    """
    net = topo.net
    passed = 0
    failed = 0

    info('\n' + '=' * 60 + '\n')
    info('CHECKPOINT PHASE 1 — Enterprise Topology\n')
    info('=' * 60 + '\n')

    # ── Test 1: Số lượng nodes ────────────────────────────
    info('\n[TEST 1] Số lượng nodes...\n')
    expected_switches = 1 + 1 + 6 + 1 + 6 + 2 + 4  # BL + NT(1+6) + HCM(1+6) + DC(2+4)
    expected_hosts_min = 80  # 88 hosts + GW hosts

    actual_switches = len(net.switches)
    actual_hosts    = len(net.hosts)

    if actual_switches >= expected_switches:
        info(f'  ✓ Switches: {actual_switches} (expected >= {expected_switches})\n')
        passed += 1
    else:
        error(f'  ✗ Switches: {actual_switches} (expected >= {expected_switches})\n')
        failed += 1

    if actual_hosts >= expected_hosts_min:
        info(f'  ✓ Hosts: {actual_hosts} (expected >= {expected_hosts_min})\n')
        passed += 1
    else:
        error(f'  ✗ Hosts: {actual_hosts} (expected >= {expected_hosts_min})\n')
        failed += 1

    # ── Test 2: Links UP ──────────────────────────────────
    info('\n[TEST 2] Kiểm tra tất cả links UP...\n')
    links_down = []
    for link in net.links:
        intf1, intf2 = link.intf1, link.intf2
        status1 = intf1.node.cmd(f'cat /sys/class/net/{intf1.name}/operstate').strip()
        if 'down' in status1:
            links_down.append(f'{intf1.node.name}:{intf1.name}')

    if not links_down:
        info(f'  ✓ Tất cả {len(net.links)} links UP\n')
        passed += 1
    else:
        error(f'  ✗ Links DOWN: {links_down}\n')
        failed += 1

    # ── Test 3: Ping trong cùng switch ───────────────────
    info('\n[TEST 3] Ping test trong cùng site (L2)...\n')
    
    # Test BL: BL_ADM01 → BL_ADM02 (cùng switch, cùng VLAN)
    test_pairs = [
        ('BL_ADM01', 'BL_ADM02', 'BL same-switch'),
        ('NT_ADM01', 'NT_ADM02', 'NT same-switch'),
        ('HCM_ADM01', 'HCM_ADM02', 'HCM same-switch'),
        ('DC_WEB01', 'DC_WEB02', 'DC same-leaf'),
    ]

    for src_name, dst_name, desc in test_pairs:
        src = net.get(src_name)
        dst = net.get(dst_name)
        if src is None or dst is None:
            info(f'  ⚠ {desc}: host not found, skip\n')
            continue

        dst_ip = dst.IP()
        result = src.cmd(f'ping -c 2 -W 2 {dst_ip}')
        if '2 received' in result or '1 received' in result:
            info(f'  ✓ {desc}: {src_name} → {dst_name} ({dst_ip}) OK\n')
            passed += 1
        else:
            error(f'  ✗ {desc}: {src_name} → {dst_name} ({dst_ip}) FAIL\n')
            failed += 1

    # ── Kết quả ───────────────────────────────────────────
    total = passed + failed
    info('\n' + '=' * 60 + '\n')
    info(f'PHASE 1 RESULT: {passed}/{total} passed\n')
    if failed == 0:
        info('✓ PHASE 1 CHECKPOINT PASSED\n')
    else:
        error(f'✗ PHASE 1 CHECKPOINT FAILED ({failed} tests failed)\n')
    info('=' * 60 + '\n')

    return failed == 0


if __name__ == '__main__':
    from topology.enterprise_topo import build_network, check_environment

    check_environment()
    topo = build_network(phase=1)
    success = run_check(topo)
    topo.net.stop()
    sys.exit(0 if success else 1)
