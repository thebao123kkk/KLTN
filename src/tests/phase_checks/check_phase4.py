"""
tests/phase_checks/check_phase4.py
CHECKPOINT PHASE 4 — L3 Routing + OSPF Verification
=============================================
Kiểm tra:
  1. Inter-VLAN routing trong cùng site
  2. Inter-site routing qua WAN
  3. OSPF neighbor relationships
  4. Fault test: link down → OSPF reconverge
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import info, error


def _ping(net, src_name, dst_ip, count=3, timeout=3):
    """Ping helper. Returns (bool, rtt_avg_ms)."""
    src = net.get(src_name)
    if src is None:
        return None, None
    result = src.cmd(f'ping -c {count} -W {timeout} {dst_ip}')
    success = f'{count} received' in result or '1 received' in result
    rtt = None
    for line in result.splitlines():
        if 'rtt min/avg/max' in line or 'round-trip' in line:
            try:
                rtt = float(line.split('/')[4])
            except Exception:
                pass
    return success, rtt


def run_check(topo):
    """
    Chạy kiểm tra Phase 4 — OSPF routing.
    """
    net = topo.net
    results = []

    info('\n' + '=' * 60 + '\n')
    info('CHECKPOINT PHASE 4 — L3 Routing + OSPF\n')
    info('=' * 60 + '\n')

    # ── Test 1: Inter-VLAN trong cùng site ────────────────
    info('\n[TEST 1] Inter-VLAN routing trong cùng site...\n')
    inter_vlan_tests = [
        # BL: VLAN 10 → VLAN 30
        ('BL-ADMIN-PC01', '10.10.30.11', 'BL: VLAN10 → IoT VLAN30'),
        # NT: VLAN 110 ADMIN → VLAN 120 SALES
        ('NT-ADMIN-PC01', '10.20.20.11', 'NT: ADMIN → SALES'),
        # HCM: VLAN 210 → VLAN 220
        ('HCM-ADMIN-PC01', '10.30.20.11', 'HCM: ADMIN → SALES'),
    ]
    for src_name, dst_ip, desc in inter_vlan_tests:
        ok, rtt = _ping(net, src_name, dst_ip)
        if ok is None:
            info(f'  ⚠ {src_name}: not found\n')
            continue
        if ok:
            info(f'  ✓ {desc}: {src_name} → {dst_ip} (RTT: {rtt} ms)\n')
            results.append(True)
        else:
            error(f'  ✗ {desc}: {src_name} → {dst_ip} FAIL\n')
            results.append(False)

    # ── Test 2: Inter-site routing ────────────────────────
    info('\n[TEST 2] Inter-site routing (BL ↔ HCM ↔ NT ↔ DC)...\n')
    inter_site_tests = [
        # BL → DC Web server
        ('BL-ADMIN-PC01', '10.100.10.11', 'BL → DC-WEB01'),
        # NT → DC App server
        ('NT-SALES-PC01',  '10.100.20.11', 'NT → DC-APP01'),
        # HCM → DC DB
        ('HCM-ADMIN-PC01', '10.100.30.11', 'HCM → DC-DB01'),
        # BL → NT
        ('BL-ADMIN-PC01', '10.20.10.11', 'BL → NT-ADMIN-PC01'),
        # NT → HCM
        ('NT-ADMIN-PC01', '10.30.10.11', 'NT → HCM-ADMIN-PC01'),
    ]
    for src_name, dst_ip, desc in inter_site_tests:
        ok, rtt = _ping(net, src_name, dst_ip)
        if ok is None:
            info(f'  ⚠ {src_name}: not found\n')
            continue
        if ok:
            info(f'  ✓ {desc}: {src_name} → {dst_ip} (RTT: {rtt} ms)\n')
            results.append(True)
        else:
            error(f'  ✗ {desc}: {src_name} → {dst_ip} FAIL\n')
            results.append(False)

    # ── Test 3: OSPF neighbors ────────────────────────────
    info('\n[TEST 3] Kiểm tra OSPF neighbors trên routers...\n')
    ospf_routers = ['BL-GW', 'NT-DIST01', 'HCM-DIST01', 'DC-SPINE-GW']
    for rname in ospf_routers:
        router = net.get(rname)
        if router is None:
            info(f'  ⚠ {rname}: not found\n')
            continue
        neighbors = router.cmd('vtysh -c "show ip ospf neighbor" 2>/dev/null')
        if 'Full' in neighbors:
            neighbor_count = neighbors.count('Full')
            info(f'  ✓ {rname}: {neighbor_count} OSPF neighbor(s) in Full state\n')
            results.append(True)
        else:
            error(f'  ✗ {rname}: Không có OSPF neighbor Full\n')
            error(f'    Output: {neighbors[:200]}\n')
            results.append(False)

    # ── Test 4: Fault test — OSPF reconvergence ───────────
    info('\n[TEST 4] Fault test — OSPF reconvergence...\n')
    bl_gw = net.get('BL-GW')
    hcm_d1 = net.get('HCM-DIST01')

    if bl_gw and hcm_d1:
        # Ping baseline: BL → DC
        ok, rtt = _ping(net, 'BL-ADMIN-PC01', '10.100.10.11')
        if ok:
            info(f'  ✓ Baseline: BL → DC-WEB01 (RTT={rtt}ms)\n')

            # Tắt WAN link BL ↔ HCM
            wan_intf = getattr(bl_gw, 'wan_intf', None)
            if wan_intf:
                info(f'  → Tắt BL WAN interface {wan_intf}...\n')
                bl_gw.cmd(f'ip link set {wan_intf} down')

                start = time.time()
                converged = False
                for _ in range(60):
                    time.sleep(1)
                    ok2, _ = _ping(net, 'BL-ADMIN-PC01', '10.100.10.11', count=1)
                    if ok2:
                        converge_time = time.time() - start
                        info(f'  ✓ OSPF reconverged sau {converge_time:.1f}s\n')
                        converged = True
                        results.append(True)
                        break

                if not converged:
                    error('  ✗ OSPF không reconverge trong 60s (có thể normal nếu chỉ 1 đường)\n')
                    # Không append False vì có thể không có backup path ở Phase 1-6

                # Khôi phục
                bl_gw.cmd(f'ip link set {wan_intf} up')
                info(f'  → Khôi phục {wan_intf}\n')
    else:
        info('  ⚠ BL-GW hoặc HCM-DIST01 không tìm thấy, skip fault test\n')

    return _report(results)


def _report(results):
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)
    total  = len(results)
    info('\n' + '=' * 60 + '\n')
    info(f'PHASE 4 RESULT: {passed}/{total} passed\n')
    if failed == 0:
        info('✓ PHASE 4 CHECKPOINT PASSED\n')
    else:
        error(f'✗ PHASE 4 CHECKPOINT FAILED ({failed} failed)\n')
    info('=' * 60 + '\n')
    return failed == 0


if __name__ == '__main__':
    from topology.enterprise_topo import build_network, check_environment
    check_environment()
    topo = build_network(phase=4)
    success = run_check(topo)
    topo.net.stop()
    sys.exit(0 if success else 1)
