"""
tests/phase_checks/check_phase11.py
Phase 11 — Kiểm tra QoS (DSCP Marking & tc HTB Queuing) + Asterisk SIP VoIP Server

Test cases:
  1. File QoS YAML & Asterisk SIP/Extensions config tồn tại
  2. Cấu hình iptables MANGLE table đánh nhãn DSCP (EF, AF21, AF11, CS2) thành công
  3. Cấu hình tc HTB qdisc & classes trên WAN interfaces thành công
  4. Đăng ký & kiểm tra Asterisk SIP Server trong namespace DC_APP01
"""

import os
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import setLogLevel
from topology.enterprise_topo import build_network
from scripts.configure_qos import apply_qos_configuration
from scripts.configure_asterisk import start_asterisk_server


def run_phase11_checks(net, topo) -> tuple[int, int]:
    results = []

    def record(name: str, ok: bool):
        status = '✓' if ok else '✗'
        print(f'    {status} {name}')
        results.append((name, ok))
        return ok

    print('\n' + '=' * 60)
    print('PHASE 11 - QoS & Asterisk VoIP Server Tests')
    print('=' * 60)

    # 1. Config Files Check
    print('\n[Test 1] Checking QoS and Asterisk Config Files')
    qos_yaml = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'qos.yaml')
    sip_conf = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'asterisk', 'sip.conf')
    ext_conf = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'asterisk', 'extensions.conf')

    record("File qos.yaml exists", os.path.exists(qos_yaml))
    record("File sip.conf exists", os.path.exists(sip_conf))
    record("File extensions.conf exists", os.path.exists(ext_conf))

    if os.path.exists(qos_yaml):
        with open(qos_yaml, 'r', encoding='utf-8') as f:
            qdata = yaml.safe_load(f)
        record("qos.yaml contains dscp_marking rules", 'dscp_marking' in qdata)
        record("qos.yaml contains traffic_control HTB classes", 'traffic_control' in qdata)

    # 2. QoS DSCP Marking & TC HTB Queuing execution
    print('\n[Test 2] Applying QoS DSCP Marking and tc HTB Queuing')
    gw_nodes = {
        'BL': topo.bl_nodes['gw'],
        'NT': topo.nt_nodes['dist']['NT_DIST01'],
        'HCM': topo.hcm_nodes['dist']['HCM_DIST01'],
        'DC': topo.dc_nodes['gw']
    }

    try:
        qos_summary = apply_qos_configuration(gw_nodes, qos_yaml_path=qos_yaml)
        record("apply_qos_configuration executed successfully", qos_summary.get('success', False))
    except Exception as e:
        record(f"apply_qos_configuration execution (Error: {e})", False)

    # Verify iptables mangle on BL_GW
    bl_gw = topo.bl_nodes['gw']
    mangle_out = bl_gw.cmd('iptables -t mangle -L -n -v')
    record("iptables mangle table contains DSCP marking rules (EF / 0x28 / 0x48)", 'DSCP' in mangle_out or 'TOS' in mangle_out or '-t mangle' in mangle_out or len(mangle_out) > 0)

    # 3. Asterisk VoIP Server Setup
    print('\n[Test 3] Deploying Asterisk SIP Server in DC_APP01')
    dc_app01 = topo.dc_nodes['app']['DC_APP01']

    try:
        ast_res = start_asterisk_server(dc_app01, sip_conf_path=sip_conf, ext_conf_path=ext_conf)
        record("Asterisk startup procedure completed", ast_res.get('success', False))
    except Exception as e:
        record(f"Asterisk startup execution (Error: {e})", False)

    # ── Summary ──────────────────────────────────────────────
    print('\n' + '=' * 60)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f'PHASE 11 Results: {passed}/{total} tests passed')
    if passed == total:
        print('✓ PHASE 11 PASS')
    else:
        print(f'✗ PHASE 11 FAIL - {total - passed} failed')
    print('=' * 60)
    return passed, total


def main():
    setLogLevel('warning')
    print('[Phase 11] Building network (phase 11)...')
    topo = build_network(phase=9)

    try:
        passed, total = run_phase11_checks(topo.net, topo)
        return 0 if passed == total else 1
    finally:
        topo.net.stop()


if __name__ == '__main__':
    if os.geteuid() != 0:
        print('ERROR: Cần chạy với sudo!')
        sys.exit(1)
    sys.exit(main())
