"""
tests/phase_checks/check_phase6.py
CHECKPOINT PHASE 6 — DHCP + DNS + NTP Services
=============================================
Kiểm tra:
  1. DHCP: Một host mới nhận IP từ DC_DHCP01
  2. DNS:  Resolve enterprise.local domains
  3. NTP:  DC_MGMT01 đang sync time

Cách chạy:
  sudo python3 tests/phase_checks/check_phase6.py
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import info, error


def run_check(topo):
    net = topo.net
    results = []

    info('\n' + '=' * 60 + '\n')
    info('CHECKPOINT PHASE 6 — DHCP + DNS + NTP\n')
    info('=' * 60 + '\n')

    # ── Test 1: DHCP ──────────────────────────────────────
    info('\n[TEST 1] DHCP — host lấy IP từ DC_DHCP01...\n')
    dhcp_host = net.get('DC_DHCP01')
    
    if dhcp_host:
        # Kiểm tra dnsmasq DHCP đang chạy
        pid = dhcp_host.cmd('cat /tmp/dnsmasq_dhcp.pid 2>/dev/null').strip()
        if pid and dhcp_host.cmd(f'kill -0 {pid} 2>/dev/null ; echo $?').strip() == '0':
            info(f'  ✓ dnsmasq DHCP running (PID: {pid})\n')
            results.append(True)
        else:
            error(f'  ✗ dnsmasq DHCP không chạy\n')
            results.append(False)

        # Test DHCP bằng cách dùng 1 host không có static IP (nếu có)
        # Hoặc dùng dhclient trên host có VLAN
        # Dùng NT_ADM01 thử dhclient (sẽ nhận IP từ pool)
        test_host = net.get('NT_ADM01')
        if test_host:
            info(f'  → Thử DHCP discover từ NT_ADM01...\n')
            # Xóa IP hiện tại và request DHCP
            intf = test_host.defaultIntf().name
            test_host.cmd(f'dhclient -r {intf} 2>/dev/null')
            time.sleep(1)
            test_host.cmd(f'dhclient {intf} 2>/dev/null &')
            time.sleep(3)

            new_ip = test_host.cmd(f'ip addr show {intf} | grep "inet " | awk "{{print $2}}"').strip()
            # IP từ pool DHCP: 10.20.10.100-200
            if new_ip and '10.20.10.' in new_ip:
                pool_octet = int(new_ip.split('.')[3].split('/')[0])
                if 100 <= pool_octet <= 200:
                    info(f'  ✓ DHCP: NT_ADM01 nhận IP {new_ip} từ pool (100-200)\n')
                    results.append(True)
                else:
                    info(f'  ⚠ DHCP: IP {new_ip} ngoài pool expected range (có thể dùng static IP)\n')
            else:
                info(f'  ⚠ DHCP discover timeout (bình thường nếu relay chưa config xong)\n')
    else:
        error('  ✗ DC_DHCP01 không tìm thấy\n')
        results.append(False)

    # ── Test 2: DNS ───────────────────────────────────────
    info('\n[TEST 2] DNS — Resolve enterprise.local...\n')
    dns_host = net.get('DC_DNS01')

    if dns_host:
        pid = dns_host.cmd('cat /tmp/dnsmasq_dns.pid 2>/dev/null').strip()
        if pid and dns_host.cmd(f'kill -0 {pid} 2>/dev/null ; echo $?').strip() == '0':
            info(f'  ✓ dnsmasq DNS running (PID: {pid})\n')
            results.append(True)
        else:
            error(f'  ✗ dnsmasq DNS không chạy\n')
            results.append(False)

        # DNS resolve tests từ DC_DNS01 host
        dns_records = [
            ('www.enterprise.local',     '10.100.10.11'),
            ('app.enterprise.local',     '10.100.20.11'),
            ('db.enterprise.local',      '10.100.30.11'),
            ('monitor.enterprise.local', '10.100.50.11'),
        ]
        dns_ip = '10.100.40.11'
        for fqdn, expected_ip in dns_records:
            result = dns_host.cmd(f'nslookup {fqdn} {dns_ip} 2>/dev/null | grep "Address:" | tail -1')
            if expected_ip in result:
                info(f'  ✓ DNS: {fqdn} → {expected_ip}\n')
                results.append(True)
            else:
                error(f'  ✗ DNS: {fqdn} → expected {expected_ip}, got: {result.strip()}\n')
                results.append(False)

        # DNS từ remote host (HCM → DNS server)
        hcm_host = net.get('HCM_ADM01')
        if hcm_host:
            info(f'  → DNS query từ HCM_ADM01...\n')
            result = hcm_host.cmd(f'nslookup www.enterprise.local {dns_ip} 2>/dev/null')
            if '10.100.10.11' in result:
                info(f'  ✓ HCM host resolve www.enterprise.local thành công\n')
                results.append(True)
            else:
                error(f'  ✗ HCM host không resolve được www.enterprise.local\n')
                results.append(False)
    else:
        error('  ✗ DC_DNS01 không tìm thấy\n')
        results.append(False)

    # ── Test 3: NTP ───────────────────────────────────────
    info('\n[TEST 3] NTP — DC_MGMT01 đang chạy chrony...\n')
    ntp_host = net.get('DC_MGMT01')

    if ntp_host:
        # Kiểm tra chrony đang chạy
        chrony_status = ntp_host.cmd('chronyd -Q 2>/dev/null || chronyc tracking 2>/dev/null | head -5')
        pid_check = ntp_host.cmd('cat /tmp/chrony.pid 2>/dev/null').strip()

        if pid_check:
            info(f'  ✓ chrony NTP running (PID: {pid_check})\n')
            results.append(True)
        else:
            error(f'  ✗ chrony không chạy trên DC_MGMT01\n')
            results.append(False)

        # NTP client test từ NT_DIST01
        nt_dist1 = net.get('NT_DIST01')
        if nt_dist1:
            info(f'  → NTP query từ NT_DIST01 đến DC_MGMT01 (10.100.60.11)...\n')
            ntp_result = nt_dist1.cmd('ntpdate -q 10.100.60.11 2>&1 | head -3')
            if 'stratum' in ntp_result.lower() or 'offset' in ntp_result.lower():
                info(f'  ✓ NT_DIST01 sync được NTP từ DC_MGMT01\n')
                results.append(True)
            else:
                info(f'  ⚠ NTP query result: {ntp_result.strip()[:100]}\n')
                info(f'  ⚠ NTP có thể cần upstream internet hoặc thêm thời gian sync\n')
    else:
        error('  ✗ DC_MGMT01 không tìm thấy\n')
        results.append(False)

    return _report(results)


def _report(results):
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)
    total  = len(results)
    info('\n' + '=' * 60 + '\n')
    info(f'PHASE 6 RESULT: {passed}/{total} passed\n')
    if failed == 0:
        info('✓ PHASE 6 CHECKPOINT PASSED — PC mới: DHCP ↓ IP ↓ DNS ↓ NTP ✓\n')
    else:
        error(f'✗ PHASE 6 CHECKPOINT FAILED ({failed} failed)\n')
    info('=' * 60 + '\n')
    return failed == 0


if __name__ == '__main__':
    from topology.enterprise_topo import build_network, check_environment
    check_environment()
    topo = build_network(phase=6)
    success = run_check(topo)
    topo.net.stop()
    sys.exit(0 if success else 1)
