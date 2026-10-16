"""
topology/enterprise_topo.py
ENTRY POINT — Enterprise Network KLTN
=============================================
Khởi động toàn bộ mạng doanh nghiệp trong Mininet:
  - 4 sites: Bảo Lộc (flat), Nha Trang (3-tier), HCM (3-tier), Data Center (Spine-Leaf)
  - 88 host endpoints
  - VLAN segmentation
  - RSTP loop prevention
  - OSPF inter-site routing (FRRouting)
  - VRRP gateway redundancy (keepalived)
  - DHCP/DNS/NTP services (dnsmasq, chrony)

Cách chạy (trên Ubuntu Linux, yêu cầu sudo):
  sudo python3 topology/enterprise_topo.py [--phase N]

  --phase 1 : Chỉ build topology (pingall L2)
  --phase 2 : + VLAN configuration
  --phase 3 : + STP (tự động khi add switch với stp=True)
  --phase 4 : + OSPF (FRR)
  --phase 5 : + VRRP (keepalived)
  --phase 6 : + DHCP/DNS/NTP services (default)
  --phase 0 : Chỉ kiểm tra môi trường

Yêu cầu phần mềm:
  sudo apt install mininet openvswitch-switch frr keepalived
  sudo apt install dnsmasq chrony iperf3 tcpdump
  pip3 install -r requirements.txt
"""

import argparse
import sys
import os
import subprocess

from mininet.net import Mininet
from mininet.node import OVSSwitch, OVSController
from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.link import TCLink

# Thêm src/ vào Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from topology.sites.baoloc     import build_baoloc,     configure_baoloc,     start_frr_baoloc
from topology.sites.nhatrang   import build_nhatrang,   configure_nhatrang,   start_frr_nhatrang,   start_vrrp_nhatrang
from topology.sites.hcm        import build_hcm,        configure_hcm,        start_frr_hcm,        start_vrrp_hcm
from topology.sites.datacenter import build_datacenter, configure_datacenter, start_frr_datacenter, start_services_datacenter
from topology.wan.wan_links    import connect_sites_wan, configure_wan_ips
from scripts.configure_acl     import configure_all_acl
from scripts.configure_haproxy import configure_dc_services_phase8
from controller.sdwan.sdwan_controller import SDWANController
from controller.sdn.openflow_agent     import OpenFlowAgent


# ── Phase 0: Kiểm tra môi trường ─────────────────────────
def check_environment():
    """
    Kiểm tra các phần mềm cần thiết đã được cài chưa.
    Thoát với lỗi nếu thiếu.
    """
    info('=' * 60 + '\n')
    info('[PHASE 0] Kiểm tra môi trường...\n')

    required = {
        'mn':           'mininet',
        'ovs-vsctl':    'openvswitch-switch',
        'vtysh':        'frr (vtysh)',
        'keepalived':   'keepalived',
        'dnsmasq':      'dnsmasq',
        'chronyd':      'chrony',
        'iperf3':       'iperf3',
        'tcpdump':      'tcpdump',
        'python3':      'python3',
    }

    all_ok = True
    for cmd, pkg in required.items():
        result = subprocess.run(['which', cmd], capture_output=True)
        if result.returncode == 0:
            info(f'  ✓ {cmd:<15} ({pkg})\n')
        else:
            error(f'  ✗ {cmd:<15} KHÔNG TÌM THẤY — cài bằng: sudo apt install {pkg}\n')
            all_ok = False

    if not all_ok:
        error('[PHASE 0] ✗ Môi trường thiếu dependencies. Dừng.\n')
        sys.exit(1)

    # Nạp 802.1Q kernel module cho VLAN sub-interfaces
    subprocess.run(['modprobe', '8021q'], capture_output=True)

    info('[PHASE 0] ✓ Môi trường OK\n')
    info('=' * 60 + '\n')
    return True


# ── Topology class cho Mininet ────────────────────────────
class EnterpriseTopo:
    """
    Container class giữ tất cả node references.
    Không kế thừa mininet.topo.Topo vì ta build trực tiếp trên Mininet instance
    để có thể gán thuộc tính động (vlan, link_intf, ...) cho từng node.
    """

    def __init__(self):
        self.net       = None
        self.bl_nodes  = None
        self.nt_nodes  = None
        self.hcm_nodes = None
        self.dc_nodes  = None
        self.wan_links = None
        self.sdwan     = None
        self.sdn_agent = None


def build_network(phase: int = 14) -> EnterpriseTopo:
    """
    Xây dựng mạng đến phase chỉ định.

    Parameters
    ----------
    phase : int
        Phase tối đa cần build (1-14).

    Returns
    -------
    EnterpriseTopo instance với net đã start.
    """
    topo = EnterpriseTopo()

    info('[NET] Khởi tạo Mininet...\n')
    topo.net = Mininet(
        switch=OVSSwitch,
        controller=None,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=False,
    )

    # ── Phase 1: Build topology ───────────────────────────
    info('\n[PHASE 1] Xây dựng Enterprise Topology...\n')
    info('  → Building Bảo Lộc site...\n')
    topo.bl_nodes  = build_baoloc(topo.net)

    info('  → Building Nha Trang site...\n')
    topo.nt_nodes  = build_nhatrang(topo.net)

    info('  → Building HCM site...\n')
    topo.hcm_nodes = build_hcm(topo.net)

    info('  → Building Data Center site...\n')
    topo.dc_nodes  = build_datacenter(topo.net)

    info('  → Connecting sites via WAN...\n')
    topo.wan_links = connect_sites_wan(
        topo.net,
        topo.bl_nodes, topo.nt_nodes, topo.hcm_nodes, topo.dc_nodes,
        phase=phase
    )

    # ── Start Mininet ─────────────────────────────────────
    info('\n[NET] Khởi động Mininet...\n')
    topo.net.start()
    info('[NET] ✓ Mininet started\n')

    if phase < 2:
        return topo

    # ── Phase 2 + 3: VLAN + STP ───────────────────────────
    info('\n[PHASE 2/3] Cấu hình VLAN + STP...\n')
    configure_baoloc(topo.bl_nodes)
    configure_nhatrang(topo.nt_nodes)
    configure_hcm(topo.hcm_nodes)
    configure_datacenter(topo.dc_nodes)
    configure_wan_ips(topo.wan_links, topo.bl_nodes, topo.nt_nodes, topo.hcm_nodes, topo.dc_nodes, phase=phase)
    info('[PHASE 2/3] ✓ VLAN + STP configured\n')

    if phase < 4:
        return topo

    # ── Phase 4: OSPF (FRRouting) ─────────────────────────
    info('\n[PHASE 4] Khởi động OSPF (FRRouting)...\n')
    start_frr_baoloc(topo.bl_nodes['gw'])
    start_frr_nhatrang(topo.nt_nodes)
    start_frr_hcm(topo.hcm_nodes)
    start_frr_datacenter(topo.dc_nodes)
    info('[PHASE 4] ✓ OSPF started on all routers\n')

    if phase < 5:
        return topo

    # ── Phase 5: VRRP (keepalived) ────────────────────────
    info('\n[PHASE 5] Khởi động VRRP (keepalived)...\n')
    start_vrrp_nhatrang(topo.nt_nodes)
    start_vrrp_hcm(topo.hcm_nodes)
    info('[PHASE 5] ✓ VRRP started\n')

    if phase < 6:
        return topo

    # ── Phase 6: DHCP + DNS + NTP ─────────────────────────
    info('\n[PHASE 6] Khởi động DHCP/DNS/NTP services...\n')
    start_services_datacenter(topo.dc_nodes)
    info('[PHASE 6] ✓ Services started\n')

    # if phase < 7:
    #     return topo

    # # ── Phase 7: ACL + Firewall ───────────────────────────
    # info('\n[PHASE 7] Áp dụng ACL + Firewall rules...\n')
    # configure_all_acl({
    #     'bl_nodes': topo.bl_nodes,
    #     'nt_nodes': topo.nt_nodes,
    #     'hcm_nodes': topo.hcm_nodes,
    #     'dc_nodes': topo.dc_nodes,
    # })
    # info('[PHASE 7] ✓ ACL + Firewall rules applied\n')

    if phase < 8:
        return topo

        # ── Phase 8: DC Services (HAProxy + Web Servers) ──────
    info('\n[PHASE 8] Khởi động DC Services (HAProxy Load Balancer + WEB Servers)...\n')
    configure_dc_services_phase8(topo.dc_nodes)
    info('[PHASE 8] ✓ HAProxy Load Balancer active\n')

    if phase < 9:
        return topo

    # ── Phase 9: WAN 5-Path Transport ─────────────────────
    info('\n[PHASE 9] WAN 5-Path Transport Emulation (tc netem) active.\n')

    if phase < 10:
        return topo

    # ── Phase 10: SD-WAN Controller ───────────────────────
    info('\n[PHASE 10] Khởi động SD-WAN Controller...\n')
    gw_nodes = {
        'BL':  topo.bl_nodes['gw'],
        'NT':  topo.nt_nodes['dist']['NT_DIST01'],
        'HCM': topo.hcm_nodes['dist']['HCM_DIST01'],
        'DC':  topo.dc_nodes['gw'],
    }
    topo.sdwan = SDWANController(gw_nodes, probe_interval=10.0, api_port=7070)
    # topo.sdwan = SDWANController(gw_nodes, probe_interval=3.0, api_port=7070)
    topo.sdwan.start()
    info('[PHASE 10] ✓ SD-WAN Controller active (API: http://localhost:7070)\n')

    if phase < 14:
        return topo

    # ── Phase 14: SDN Faucet Controller ───────────────────
    info('\n[PHASE 14] Khởi động Faucet SDN Controller & Bind OpenFlow Switches...\n')
    switches = ['BL_SW', 'NT_CORE', 'HCM_CORE', 'NT_ACC01', 'HCM_ACC01']
    topo.sdn_agent = OpenFlowAgent(config_path='config/faucet.yaml')
    topo.sdn_agent.start_sdn_services(switches)
    info('[PHASE 14] ✓ Faucet SDN Controller active on OpenFlow switches\n')

    return topo




def print_summary(topo: EnterpriseTopo):
    """In tóm tắt mạng sau khi build xong."""
    net = topo.net
    info('\n' + '=' * 60 + '\n')
    info('ENTERPRISE NETWORK SUMMARY\n')
    info('=' * 60 + '\n')
    info(f'  Switches : {len(net.switches)}\n')
    info(f'  Hosts    : {len(net.hosts)}\n')
    info(f'  Links    : {len(net.links)}\n')
    info('\nSite breakdown:\n')
    info('  BL  : 1 switch (flat), 16 hosts\n')
    info('  NT  : 1 CORE + 2 DIST + 6 ACC switches, 26 hosts\n')
    info('  HCM : 1 CORE + 2 DIST + 6 ACC switches, 35 hosts\n')
    info('  DC  : 2 SPINE + 4 LEAF switches, 10 servers\n')
    info('\nKey services:\n')
    info('  DHCP Server : DC_DHCP01 (10.100.40.12)\n')
    info('  DNS Server  : DC_DNS01  (10.100.40.11)\n')
    info('  NTP Server  : DC_MGMT01 (10.100.60.11)\n')
    info('  VRRP (NT)   : 10.20.x.1 (DIST01 master)\n')
    info('  VRRP (HCM)  : 10.30.x.1 (DIST01 master)\n')
    info('=' * 60 + '\n')


# ── Main ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='KLTN Enterprise Network — Mininet Topology'
    )
    parser.add_argument(
        '--phase', type=int, default=14, choices=range(0, 15),
        help='Build đến Phase N (0=env check only, 1-14, default=14)'
    )
    parser.add_argument(
        '--no-cli', action='store_true',
        help='Không mở Mininet CLI (dùng cho script tự động)'
    )
    parser.add_argument(
        '--test-pingall', action='store_true',
        help='Chạy pingall và in kết quả rồi thoát'
    )
    args = parser.parse_args()

    setLogLevel('info')

    # Phase 0: kiểm tra môi trường
    check_environment()

    if args.phase == 0:
        info('[PHASE 0] Chỉ kiểm tra môi trường. Xong.\n')
        sys.exit(0)

    # Build network
    topo = None
    try:
        topo = build_network(phase=args.phase)
        print_summary(topo)

        if args.test_pingall:
            info('\n[TEST] Chạy pingall...\n')
            loss = topo.net.pingAll()
            info(f'[TEST] Packet loss: {loss:.1f}%\n')
            topo.net.stop()
            sys.exit(0 if loss == 0.0 else 1)

        if not args.no_cli:
            info('\n[CLI] Mở Mininet CLI. Gõ "exit" để thoát.\n')
            CLI(topo.net)

    except KeyboardInterrupt:
        info('\n[NET] Interrupted by user\n')
    except Exception as e:
        error(f'\n[NET] Error: {e}\n')
        import traceback
        traceback.print_exc()

    finally:
        if topo and topo.net:
            info('[NET] Stopping Mininet...\n')
            topo.net.stop()
            info('[NET] Done.\n')


if __name__ == '__main__':
    if os.geteuid() != 0:
        print('ERROR: Phải chạy với sudo!')
        print('  sudo python3 topology/enterprise_topo.py')
        sys.exit(1)
    main()
