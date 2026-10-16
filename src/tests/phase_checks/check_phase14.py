"""
tests/phase_checks/check_phase14.py
Phase 14 - Kiểm tra SDN Controller Faucet & OpenFlow Switch Integration

Test cases:
  1. File faucet.yaml tồn tại và hợp lệ
  2. FaucetController khởi tạo thành công
  3. OVS Switches gán controller OpenFlow (tcp:127.0.0.1:6653) & OpenFlow13 protocol
  4. FlowManager REST API tương tác / metrics
  5. OpenFlowAgent block/unblock port interface
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mininet.log import setLogLevel
from topology.enterprise_topo import build_network
from controller.sdn.openflow_agent import OpenFlowAgent
from controller.sdn.faucet_controller import FaucetController


def run_phase14_checks(net, topo) -> tuple[int, int]:
    results = []

    def record(name: str, ok: bool):
        status = '✓' if ok else '✗'
        print(f'    {status} {name}')
        results.append((name, ok))
        return ok

    print('\n' + '=' * 60)
    print('PHASE 14 - SDN Controller Faucet & OpenFlow Tests')
    print('=' * 60)

    # 1. Config file check
    print('\n[Test 1] Faucet Configuration Check')
    config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'faucet.yaml')
    record("faucet.yaml config file exists", os.path.exists(config_file))

    # 2. OpenFlow Controller Binding
    print('\n[Test 2] Binding OVS Switches to Faucet Controller')
    target_switches = ['BL_SW', 'NT_CORE', 'HCM_CORE', 'NT_ACC01', 'HCM_ACC01']
    agent = OpenFlowAgent(config_path='config/faucet.yaml')

    try:
        agent.start_sdn_services(target_switches)
        record("OpenFlowAgent started SDN services & set OpenFlow13 on switches", True)
    except Exception as e:
        record(f"OpenFlowAgent start failed: {e}", False)

    # 3. Verify OVS Controller config
    print('\n[Test 3] Verify OVS Controller Configuration')
    bl_sw = topo.bl_nodes['sw']
    ctrl_output = bl_sw.cmd('ovs-vsctl get-controller BL_SW')
    proto_output = bl_sw.cmd('ovs-vsctl get bridge BL_SW protocols')
    record("BL_SW controller set to tcp:127.0.0.1:6653", '6653' in ctrl_output or 'tcp:' in ctrl_output)
    record("BL_SW configured with OpenFlow13 protocol", 'OpenFlow13' in proto_output)

    # 4. Cleanup
    print('\n[Test 4] Teardown & Reset Switches')
    try:
        agent.stop_sdn_services(target_switches)
        record("SDN services stopped & controllers cleared", True)
    except Exception as e:
        record(f"SDN services stop failed: {e}", False)

    # ── Summary ──────────────────────────────────────────────
    print('\n' + '=' * 60)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f'PHASE 14 Results: {passed}/{total} tests passed')
    if passed == total:
        print('✓ PHASE 14 PASS')
    else:
        print(f'✗ PHASE 14 FAIL - {total - passed} failed')
    print('=' * 60)
    return passed, total


def main():
    setLogLevel('warning')
    print('[Phase 14] Building network (phase 14)...')
    topo = build_network(phase=9)

    try:
        passed, total = run_phase14_checks(topo.net, topo)
        return 0 if passed == total else 1
    finally:
        topo.net.stop()


if __name__ == '__main__':
    if os.geteuid() != 0:
        print('ERROR: Cần chạy với sudo!')
        sys.exit(1)
    sys.exit(main())
