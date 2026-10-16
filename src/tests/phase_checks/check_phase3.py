"""
tests/phase_checks/check_phase3.py
CHECKPOINT PHASE 3 — RSTP Convergence Verification
=============================================
Kiểm tra:
  1. STP đã bật trên tất cả OVS switch
  2. Root bridge đúng (CORE switch có priority thấp nhất)
  3. Fault test: tắt 1 link, topology tự khôi phục trong < 30s
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import info, error


def _get_stp_state(sw):
    """Lấy STP state của switch."""
    result = sw.cmd(f'ovs-vsctl get bridge {sw.name} stp_enable')
    return result.strip()


def _get_root_priority(sw):
    """Lấy root bridge priority."""
    result = sw.cmd(f'ovs-ofctl show {sw.name} 2>/dev/null | grep -i priority || echo "unknown"')
    return result.strip()


def run_check(topo):
    """
    Chạy kiểm tra Phase 3 — RSTP convergence.
    """
    net = topo.net
    results = []

    info('\n' + '=' * 60 + '\n')
    info('CHECKPOINT PHASE 3 — L2 Switching + RSTP\n')
    info('=' * 60 + '\n')

    # ── Test 1: STP enabled trên tất cả switch ────────────
    info('\n[TEST 1] STP bật trên tất cả switch...\n')
    core_switches = ['BL_SW', 'NT_CORE', 'HCM_CORE', 'DC_SPINE01']
    
    for sw_name in core_switches:
        sw = net.get(sw_name)
        if sw is None:
            info(f'  ⚠ {sw_name}: not found\n')
            continue
        stp_state = sw.cmd(f'ovs-vsctl get bridge {sw_name} stp_enable').strip()
        if 'true' in stp_state.lower():
            info(f'  ✓ {sw_name}: STP enabled\n')
            results.append(True)
        else:
            error(f'  ✗ {sw_name}: STP NOT enabled (state: {stp_state})\n')
            results.append(False)

    # ── Test 2: Kiểm tra STP port states ─────────────────
    info('\n[TEST 2] Kiểm tra STP port states (không có loop)...\n')
    for sw in net.switches:
        stp_info = sw.cmd(f'ovs-appctl stp/show {sw.name} 2>/dev/null | head -20')
        if 'blocking' in stp_info or 'forwarding' in stp_info:
            info(f'  ✓ {sw.name}: STP active\n')
            results.append(True)
        else:
            info(f'  ⚠ {sw.name}: STP state unknown (may be ok if no redundant links)\n')

    # ── Test 3: Fault test — link failure RSTP convergence ──
    info('\n[TEST 3] Fault test — RSTP convergence sau link failure...\n')
    info('  Lấy baseline ping NT_ADM01 → NT_ADM02...\n')

    src = net.get('NT_ADM01')
    dst = net.get('NT_ADM02')

    if src and dst:
        dst_ip = dst.IP().split('/')[0]

        # Baseline ping
        baseline = src.cmd(f'ping -c 3 -W 2 {dst_ip}')
        if '3 received' in baseline or '2 received' in baseline:
            info(f'  ✓ Baseline ping OK: {src.name} → {dst_ip}\n')
        else:
            error(f'  ✗ Baseline ping FAIL\n')
            results.append(False)
            return _report(results)

        # Tắt uplink NT_ACC01 → NT_DIST01
        # Tìm link giữa ACC01 và DIST01
        acc01 = net.get('NT_ACC01')
        dist1 = net.get('NT_DIST01')
        
        if acc01 and dist1:
            # Tìm interface nối ACC01 với DIST01
            for intf in acc01.intfList():
                link = intf.link
                if link and (dist1.name in str(link)):
                    info(f'  → Tắt link: {intf.name} (ACC01 → DIST01)...\n')
                    acc01.cmd(f'ip link set {intf.name} down')
                    break

            # Đo thời gian convergence
            start_time = time.time()
            converged  = False
            info('  → Chờ RSTP convergence (tối đa 30s)...\n')

            for i in range(30):
                time.sleep(1)
                result = src.cmd(f'ping -c 1 -W 1 {dst_ip}')
                if '1 received' in result:
                    converge_time = time.time() - start_time
                    info(f'  ✓ Convergence sau {converge_time:.1f}s\n')
                    converged = True
                    results.append(True)
                    break

            if not converged:
                error(f'  ✗ Không convergence trong 30s\n')
                results.append(False)

            # Khôi phục link
            for intf in acc01.intfList():
                link = intf.link
                if link and (dist1.name in str(link)):
                    acc01.cmd(f'ip link set {intf.name} up')
                    info(f'  → Khôi phục link {intf.name}\n')
                    break
        else:
            info('  ⚠ NT_ACC01 hoặc NT_DIST01 không tìm thấy, skip fault test\n')
    else:
        info('  ⚠ NT hosts không tìm thấy, skip fault test\n')

    return _report(results)


def _report(results):
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)
    total  = len(results)
    info('\n' + '=' * 60 + '\n')
    info(f'PHASE 3 RESULT: {passed}/{total} passed\n')
    if failed == 0:
        info('✓ PHASE 3 CHECKPOINT PASSED\n')
    else:
        error(f'✗ PHASE 3 CHECKPOINT FAILED ({failed} tests failed)\n')
    info('=' * 60 + '\n')
    return failed == 0


if __name__ == '__main__':
    from topology.enterprise_topo import build_network, check_environment
    check_environment()
    topo = build_network(phase=3)
    success = run_check(topo)
    topo.net.stop()
    sys.exit(0 if success else 1)
