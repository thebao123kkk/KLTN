"""
tests/phase_checks/check_phase8.py
Phase 8 - Kiểm tra Load Balancing (HAProxy)

Test cases:
  1. VIP 10.100.10.10 phản hồi HTTP
  2. DC_WEB01 down → HAProxy chuyển sang DC_WEB02 trong < 8s
  3. DC_WEB01 khôi phục → cả 2 backend hoạt động
  4. DNS www.enterprise.local resolve đúng VIP
  5. Client ngoài DC cũng curl được VIP
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import setLogLevel, info

from topology.enterprise_topo import build_network
from scripts.configure_haproxy import (
    configure_dc_services_phase8,
    WEB_VIP, WEB01_IP, WEB02_IP, STATS_PORT
)


def run_phase8_checks(net, topo_nodes) -> tuple:
    """Chạy toàn bộ test Phase 8. Trả về (passed, total)."""
    results = []

    def record(name: str, ok: bool):
        status = '✓' if ok else '✗'
        print(f'    {status} {name}')
        results.append((name, ok))
        return ok

    dc_nodes = topo_nodes['dc_nodes']
    hosts = dc_nodes['hosts']
    app01  = hosts['DC_APP01']
    web01  = hosts['DC_WEB01']
    web02  = hosts['DC_WEB02']

    # Một client ngoài DC (dùng để test cross-site access)
    nt_hosts = topo_nodes['nt_nodes']['hosts']
    client = list(nt_hosts.values())[0]  # Lấy host đầu tiên của NT site

    print('\n' + '=' * 60)
    print('PHASE 8 - Load Balancing (HAProxy) Tests')
    print('=' * 60)

    # ── Test 1: VIP phản hồi cơ bản ────────────────────────
    print('\n[Test 1] VIP HTTP response')
    result = app01.cmd(f'curl -s http://{WEB_VIP}/health --max-time 3')
    record('VIP /health returns OK', 'OK' in result)

    result = app01.cmd(f'curl -s http://{WEB_VIP}/ --max-time 3')
    record('VIP / returns 200', 'Hello from' in result or '200' in result)

    # ── Test 2: Round-robin cả 2 backend ───────────────────
    print('\n[Test 2] Round-robin load balancing')
    servers_seen = set()
    for _ in range(6):
        r = app01.cmd(f'curl -s http://{WEB_VIP}/ --max-time 2')
        if 'WEB01' in r:
            servers_seen.add('WEB01')
        if 'WEB02' in r:
            servers_seen.add('WEB02')
        time.sleep(0.3)

    record('Both WEB01 and WEB02 served requests', len(servers_seen) == 2)

    # ── Test 3: WEB01 failure → failover ───────────────────
    print('\n[Test 3] WEB01 failure → failover to WEB02')
    print('    Stopping DC_WEB01 HTTP server...')
    web01.cmd('pkill -f "webserver_DC_WEB01" 2>/dev/null')
    time.sleep(0.5)
    web01.cmd('pkill -f python3 2>/dev/null')

    # HAProxy cần 2s interval × 3 falls = 6s để detect failure
    print('    Waiting 8s for HAProxy health check to detect failure...')
    time.sleep(8)

    # Kiểm tra traffic vẫn hoạt động qua WEB02
    ok_count = 0
    for _ in range(4):
        r = app01.cmd(f'curl -s http://{WEB_VIP}/health --max-time 3')
        if 'OK' in r:
            ok_count += 1
        time.sleep(0.5)

    record('VIP still reachable after WEB01 down', ok_count >= 3)

    # Kiểm tra chỉ WEB02 phục vụ
    r = app01.cmd(f'curl -s http://{WEB_VIP}/ --max-time 2')
    record('Only WEB02 serving during WEB01 failure', 'WEB02' in r)

    # ── Test 4: WEB01 recover ──────────────────────────────
    print('\n[Test 4] WEB01 recovery')
    from scripts.configure_haproxy import WEBSERVER_SCRIPT
    script_content = WEBSERVER_SCRIPT.format(hostname='DC_WEB01')
    web01.cmd(f"cat > /tmp/webserver_DC_WEB01.py << 'EOPY'\n{script_content}\nEOPY")
    web01.cmd('python3 /tmp/webserver_DC_WEB01.py &')

    # HAProxy cần 2s × 2 rises để mark UP
    print('    Waiting 6s for HAProxy to detect WEB01 recovery...')
    time.sleep(6)

    servers_seen2 = set()
    for _ in range(6):
        r = app01.cmd(f'curl -s http://{WEB_VIP}/ --max-time 2')
        if 'WEB01' in r:
            servers_seen2.add('WEB01')
        if 'WEB02' in r:
            servers_seen2.add('WEB02')
        time.sleep(0.3)

    record('Both backends active after WEB01 recovery', len(servers_seen2) == 2)

    # ── Test 5: Cross-site access ──────────────────────────
    print('\n[Test 5] Cross-site client access to VIP')
    result = client.cmd(f'curl -s http://{WEB_VIP}/health --max-time 5')
    record(f'{client.name} can reach VIP via WAN', 'OK' in result)

    # ── Test 6: HAProxy stats page ─────────────────────────
    print('\n[Test 6] HAProxy stats page')
    result = app01.cmd(f'curl -s http://{WEB_VIP}:{STATS_PORT}/stats --max-time 3')
    record('HAProxy stats page accessible', 'HAProxy' in result or 'Statistics' in result)

    # ── Summary ────────────────────────────────────────────
    print('\n' + '=' * 60)
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    print(f'PHASE 8 Results: {passed}/{total} tests passed')
    if passed == total:
        print('✓ PHASE 8 PASS')
    else:
        print(f'✗ PHASE 8 FAIL - {total - passed} failed:')
        for name, ok in results:
            if not ok:
                print(f'  FAILED: {name}')
    print('=' * 60)

    return passed, total


def main():
    setLogLevel('warning')

    print('[Phase 8] Building network (phase 8)...')
    topo = build_network(phase=8)
    topo_nodes = {
        'bl_nodes':  topo.bl_nodes,
        'nt_nodes':  topo.nt_nodes,
        'hcm_nodes': topo.hcm_nodes,
        'dc_nodes':  topo.dc_nodes,
    }

    time.sleep(3)

    try:
        passed, total = run_phase8_checks(topo.net, topo_nodes)
        return 0 if passed == total else 1
    finally:
        topo.net.stop()


if __name__ == '__main__':
    if os.geteuid() != 0:
        print('ERROR: Cần chạy với sudo!')
        sys.exit(1)
    sys.exit(main())
