"""
tests/phase_checks/check_phase9.py
Phase 9 - Kiểm tra WAN 5-path emulation

Test cases:
  1. Tất cả 5 WAN switches tồn tại trong Mininet
  2. Mỗi site GW có 5 WAN interfaces
  3. tc netem đặc tính đúng: MPLS ~20ms, LTE ~60ms
  4. Link down/up trên từng path hoạt động độc lập
  5. OSPF advertise WAN subnets
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import setLogLevel, info
from topology.enterprise_topo import build_network
from topology.wan.wan_links import get_wan_links, get_wan_switches


def _ping_rtt(src_host, dst_ip: str, count: int = 5, timeout: int = 2) -> float:
    """Ping và trả về RTT trung bình (ms). -1 nếu fail."""
    result = src_host.cmd(f'ping -c {count} -W {timeout} {dst_ip}')
    for line in result.split('\n'):
        if 'rtt min/avg/max/mdev' in line:
            # rtt min/avg/max/mdev = 19.2/20.1/21.3/0.8 ms
            nums = line.split('=')[1].strip().split('/')
            return float(nums[1])
    return -1.0


def run_phase9_checks(net, topo) -> tuple:
    """Chạy test Phase 9. Trả về (passed, total)."""
    results = []

    def record(name: str, ok: bool):
        status = '✓' if ok else '✗'
        print(f'    {status} {name}')
        results.append((name, ok))
        return ok

    wan_switches = get_wan_switches(topo.wan_links)
    wan_links    = get_wan_links(topo.wan_links)

    print('\n' + '=' * 60)
    print('PHASE 9 - WAN 5-Path Emulation Tests')
    print('=' * 60)

    # ── Test 1: 5 WAN switches tồn tại ─────────────────────
    print('\n[Test 1] WAN switches exist')
    expected_paths = ['MPLS', 'FIVEG', 'INET', 'VPN', 'LTE']
    for path in expected_paths:
        sw_name = f'WAN_{path}'
        exists = sw_name in [sw.name for sw in net.switches]
        record(f'Switch {sw_name} exists', exists)

    # ── Test 2: GW có WAN interfaces ────────────────────────
    print('\n[Test 2] GW hosts have WAN interfaces')
    bl_gw = topo.bl_nodes['gw']
    bl_intfs = [i.name for i in bl_gw.intfList() if i.name != 'lo']
    wan_intf_count = len([i for i in bl_intfs if any(
        p in i for p in ['mpls', '5g', 'inet', 'vpn', 'lte', 'five']
    )])
    record(f'BL_GW has 5 WAN interfaces (got {wan_intf_count})', wan_intf_count >= 5)

    # ── Test 3: Latency theo đặc tính từng path ─────────────
    print('\n[Test 3] WAN path latency characteristics')

    dc_gw = topo.dc_nodes['gw']

    # MPLS: ~20ms (target 15-30ms)
    dc_mpls_ip = '172.16.10.4'
    mpls_rtt = _ping_rtt(bl_gw, dc_mpls_ip, count=5)
    record(f'MPLS path RTT ~20ms (got {mpls_rtt:.1f}ms)', 10 <= mpls_rtt <= 50)

    # 5G: ~15ms (target 10-30ms)
    dc_5g_ip = '172.16.40.4'
    fiveg_rtt = _ping_rtt(bl_gw, dc_5g_ip, count=5)
    record(f'5G path RTT ~15ms (got {fiveg_rtt:.1f}ms)', 5 <= fiveg_rtt <= 40)

    # LTE: ~60ms (target 40-90ms)
    dc_lte_ip = '172.16.30.4'
    lte_rtt = _ping_rtt(bl_gw, dc_lte_ip, count=5)
    record(f'LTE path RTT ~60ms (got {lte_rtt:.1f}ms)', 30 <= lte_rtt <= 100)

    # MPLS < LTE (đặc tính đúng)
    record('MPLS latency < LTE latency', mpls_rtt < lte_rtt if mpls_rtt > 0 and lte_rtt > 0 else False)

    # ── Test 4: Path independence (link down/up) ─────────────
    print('\n[Test 4] Path independence (fault inject)')

    # Down MPLS path
    if 'MPLS' in wan_links:
        mpls_link = wan_links['MPLS']['BL']
        bl_mpls_intf = mpls_link['gw_intf']

        bl_gw.cmd(f'ip link set {bl_mpls_intf} down')
        time.sleep(1)

        # MPLS không đi được
        mpls_fail_rtt = _ping_rtt(bl_gw, dc_mpls_ip, count=3, timeout=1)
        record('MPLS path DOWN after link set down', mpls_fail_rtt < 0)

        # 5G vẫn đi được
        fiveg_ok_rtt = _ping_rtt(bl_gw, dc_5g_ip, count=3)
        record('5G path still UP when MPLS is down', fiveg_ok_rtt > 0)

        # Khôi phục MPLS
        bl_gw.cmd(f'ip link set {bl_mpls_intf} up')
        time.sleep(1)
        mpls_recover_rtt = _ping_rtt(bl_gw, dc_mpls_ip, count=3)
        record('MPLS path recovers after link set up', mpls_recover_rtt > 0)

    # ── Test 5: OSPF advertise WAN subnets ──────────────────
    print('\n[Test 5] OSPF WAN route advertisement')
    nt_d1 = topo.nt_nodes['dist']['NT_DIST01']
    route_table = nt_d1.cmd('ip route show')
    wan_subnets = ['172.16.10', '172.16.20', '172.16.30', '172.16.40', '172.16.50']
    for subnet_prefix in wan_subnets:
        record(f'Route to {subnet_prefix}.0/24 in NT_DIST01', subnet_prefix in route_table)

    # ── Summary ──────────────────────────────────────────────
    print('\n' + '=' * 60)
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    print(f'PHASE 9 Results: {passed}/{total} tests passed')
    if passed == total:
        print('✓ PHASE 9 PASS')
    else:
        print(f'✗ PHASE 9 FAIL - {total - passed} failed')
        for name, ok in results:
            if not ok:
                print(f'  FAILED: {name}')
    print('=' * 60)
    return passed, total


def main():
    setLogLevel('warning')
    print('[Phase 9] Building network (phase 9)...')

    topo = None
    try:
        topo = build_network(phase=9)
        if topo is None or getattr(topo, 'net', None) is None:
            print('[Phase 9] ✗ FAIL: build_network(phase=9) trả về None hoặc topo.net không tồn tại.')
            return 1

        time.sleep(5)  # Đợi tc netem apply

        passed, total = run_phase9_checks(topo.net, topo)
        return 0 if passed == total else 1
    except Exception as e:
        print(f'[Phase 9] ✗ ERROR trong quá trình khởi tạo hoặc chạy test: {e}')
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if topo and getattr(topo, 'net', None):
            try:
                topo.net.stop()
            except Exception as stop_err:
                print(f'[Phase 9] Warning khi dừng Mininet: {stop_err}')


if __name__ == '__main__':
    if os.geteuid() != 0:
        print('ERROR: Cần chạy với sudo!')
        sys.exit(1)
    sys.exit(main())
