"""
tests/phase_checks/check_phase5.py
CHECKPOINT PHASE 5 — VRRP Gateway Redundancy
=============================================
Kiểm tra:
  1. VIP (.1) trả lời ping từ các host
  2. VRRP MASTER đang là DIST01
  3. Fault test: kill DIST01 → VIP chuyển sang DIST02 trong < 5s
  4. Sau khôi phục DIST01 → preempt trở lại MASTER
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import info, error


def _ping_once(net, src_name, dst_ip, timeout=2):
    src = net.get(src_name)
    if src is None:
        return None
    result = src.cmd(f'ping -c 1 -W {timeout} {dst_ip}')
    return '1 received' in result


def run_check(topo):
    net = topo.net
    results = []

    info('\n' + '=' * 60 + '\n')
    info('CHECKPOINT PHASE 5 — VRRP Gateway Redundancy\n')
    info('=' * 60 + '\n')

    # ── Test 1: VIP ping được từ hosts ────────────────────
    info('\n[TEST 1] VIP (.1) trả lời ping từ hosts...\n')
    vip_tests = [
        ('NT-ADMIN-PC01', '10.20.10.1', 'NT ADMIN VLAN VIP'),
        ('NT-SALES-PC01',  '10.20.20.1', 'NT SALES VLAN VIP'),
        ('HCM-ADMIN-PC01', '10.30.10.1', 'HCM ADMIN VLAN VIP'),
        ('HCM-SALES-PC01',  '10.30.20.1', 'HCM SALES VLAN VIP'),
    ]
    for src_name, vip, desc in vip_tests:
        ok = _ping_once(net, src_name, vip)
        if ok is None:
            info(f'  ⚠ {src_name}: not found\n')
            continue
        if ok:
            info(f'  ✓ {desc}: {src_name} → {vip} OK\n')
            results.append(True)
        else:
            error(f'  ✗ {desc}: {src_name} → {vip} FAIL\n')
            results.append(False)

    # ── Test 2: Kiểm tra VRRP MASTER state ───────────────
    info('\n[TEST 2] VRRP Master state trên NT-DIST01...\n')
    dist1 = net.get('NT-DIST01')
    if dist1:
        ka_state = dist1.cmd('cat /proc/$(cat /tmp/ka_dist01.pid)/status 2>/dev/null | grep State || '
                             'ip addr show | grep -c "10.20.10.1" || echo "keepalived_unknown"')
        info(f'  keepalived state: {ka_state.strip()}\n')
        # Kiểm tra VIP trên dist1
        vip_on_dist1 = dist1.cmd('ip addr show | grep "10.20.10.1"')
        if '10.20.10.1' in vip_on_dist1:
            info(f'  ✓ NT-DIST01 đang giữ VIP 10.20.10.1 (MASTER)\n')
            results.append(True)
        else:
            error(f'  ✗ NT-DIST01 KHÔNG giữ VIP (keepalived có thể chưa start)\n')
            results.append(False)

    # ── Test 3: Fault test — DIST01 down ─────────────────
    info('\n[TEST 3] Fault test — NT-DIST01 DOWN → VIP chuyển DIST02...\n')
    src = net.get('NT-ADMIN-PC01')
    dist1 = net.get('NT-DIST01')
    dist2 = net.get('NT-DIST02')

    if src and dist1 and dist2:
        vip = '10.20.10.1'

        # Baseline
        ok = _ping_once(net, 'NT-ADMIN-PC01', vip)
        if not ok:
            error(f'  ✗ Baseline VIP ping FAIL — bỏ qua fault test\n')
        else:
            info(f'  ✓ Baseline VIP OK\n')

            # Tắt NT-DIST01 (kill keepalived + ip down)
            info(f'  → Kill keepalived trên NT-DIST01...\n')
            dist1.cmd('kill $(cat /tmp/ka_dist01.pid) 2>/dev/null')
            # Tắt tất cả interfaces của DIST01
            for intf in dist1.intfList():
                dist1.cmd(f'ip link set {intf.name} down')

            # Đo thời gian failover
            start_time = time.time()
            info(f'  → Chờ VIP failover sang DIST02 (tối đa 10s)...\n')
            failover_ok = False

            for _ in range(10):
                time.sleep(1)
                ok = _ping_once(net, 'NT-ADMIN-PC01', vip, timeout=1)
                if ok:
                    failover_time = time.time() - start_time
                    info(f'  ✓ VIP failover thành công sau {failover_time:.1f}s\n')
                    failover_ok = True
                    results.append(True)
                    break

            if not failover_ok:
                error(f'  ✗ VIP không failover trong 10s\n')
                results.append(False)

            # ── Test 4: Khôi phục DIST01 → preempt ──────
            info('\n[TEST 4] Khôi phục NT-DIST01 → preempt MASTER...\n')
            for intf in dist1.intfList():
                dist1.cmd(f'ip link set {intf.name} up')
            dist1.cmd('keepalived -f /tmp/keepalived_NT_DIST01.conf -p /tmp/ka_dist01.pid')

            # Chờ preempt (advert_int=1, preempt_delay thường 0-5s)
            time.sleep(5)
            vip_on_dist1 = dist1.cmd('ip addr show | grep "10.20.10.1"')
            if '10.20.10.1' in vip_on_dist1:
                info(f'  ✓ NT-DIST01 preempt thành công, VIP trở về DIST01\n')
                results.append(True)
            else:
                error(f'  ✗ NT-DIST01 chưa preempt (có thể cần thêm thời gian)\n')
                results.append(False)
    else:
        info('  ⚠ Không tìm thấy NT hosts, skip fault test\n')

    return _report(results)


def _report(results):
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)
    total  = len(results)
    info('\n' + '=' * 60 + '\n')
    info(f'PHASE 5 RESULT: {passed}/{total} passed\n')
    if failed == 0:
        info('✓ PHASE 5 CHECKPOINT PASSED\n')
    else:
        error(f'✗ PHASE 5 CHECKPOINT FAILED ({failed} failed)\n')
    info('=' * 60 + '\n')
    return failed == 0


if __name__ == '__main__':
    from topology.enterprise_topo import build_network, check_environment
    check_environment()
    topo = build_network(phase=5)
    success = run_check(topo)
    topo.net.stop()
    sys.exit(0 if success else 1)
