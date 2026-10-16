"""
topology/sites/hcm.py
HỒ CHÍ MINH — 3-Tier Network (site lớn nhất)
=============================================
Topology vật lý:
                       HCM-CORE (OVS)
                      /              \
              HCM-DIST01              HCM-DIST02
             (FRR+VRRP Master)        (FRR+VRRP Backup)
             / | \                   / | \
          ACC01 ACC02 ACC03       ACC04 ACC05 ACC06

ACC01 → VLAN 210 ADMIN      (3 PC)
ACC02 → VLAN 220 SALES      (3 PC)
ACC03 → VLAN 230 ACCOUNTING (3 PC)
ACC04 → VLAN 240 HR         (3 PC)
ACC05 → VLAN 250 MKT + 260 CUST (6 PC)
ACC06 → VLAN 270/280/290/295/296/297  TECH+IT+IoT+CCTV+WIFI+VOICE

Phase coverage: Phase 1, 2, 3, 4 (OSPF), 5 (VRRP)
"""

import os
import yaml
from mininet.node import OVSSwitch


_CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')


def _load_configs():
    with open(os.path.join(_CONFIG_DIR, 'vlan.yaml')) as f:
        vlan_cfg = yaml.safe_load(f)
    with open(os.path.join(_CONFIG_DIR, 'vrrp.yaml')) as f:
        vrrp_cfg = yaml.safe_load(f)
    return vlan_cfg, vrrp_cfg


def _set_access_port(port_name, vlan_id):
    os.system(f'ovs-vsctl set port {port_name} vlan_mode=access tag={vlan_id}')


def _set_trunk_port(port_name, vlan_ids=None):
    os.system(f'ovs-vsctl set port {port_name} vlan_mode=trunk')


def _set_stp_priority(sw_name, priority):
    os.system(f'ovs-vsctl set bridge {sw_name} other-config:stp-priority={priority} other-config:stp-forward-delay=2 2>/dev/null')


# Access switch VLAN assignment (topology.md Section 2.3 + CT.md section 7)
# ⚠ Dùng dấu gạch DƯỚI _ để khớp với tên Mininet addSwitch() — log.md 2026-09-19
ACC_VLANS = {
    'HCM_ACC01': [210],
    'HCM_ACC02': [220],
    'HCM_ACC03': [230],
    'HCM_ACC04': [240],
    'HCM_ACC05': [250, 260],
    'HCM_ACC06': [270, 280, 290, 295, 296, 297],
}

# ⚠ Host names cũng phải dùng _ theo CT.md section 14.2 naming convention
HOST_TO_ACC = {
    # ADMIN (VLAN 210)
    'HCM_ADM01': 'HCM_ACC01', 'HCM_ADM02': 'HCM_ACC01', 'HCM_ADM03': 'HCM_ACC01',
    # SALES (VLAN 220)
    'HCM_SAL01': 'HCM_ACC02', 'HCM_SAL02': 'HCM_ACC02', 'HCM_SAL03': 'HCM_ACC02',
    # ACCOUNTING (VLAN 230)
    'HCM_ACC01': 'HCM_ACC03', 'HCM_ACC02': 'HCM_ACC03', 'HCM_ACC03': 'HCM_ACC03',
    # HR (VLAN 240)
    'HCM_HR01':  'HCM_ACC04', 'HCM_HR02':  'HCM_ACC04', 'HCM_HR03':  'HCM_ACC04',
    # MARKETING (VLAN 250) + CUSTOMER (VLAN 260)
    'HCM_MKT01': 'HCM_ACC05', 'HCM_MKT02': 'HCM_ACC05', 'HCM_MKT03': 'HCM_ACC05',
    'HCM_CUS01': 'HCM_ACC05', 'HCM_CUS02': 'HCM_ACC05', 'HCM_CUS03': 'HCM_ACC05',
    # TECHNICAL (VLAN 270) + IT (VLAN 280) + IoT/CCTV/WIFI/VOICE
    'HCM_TEC01': 'HCM_ACC06', 'HCM_TEC02': 'HCM_ACC06', 'HCM_TEC03': 'HCM_ACC06',
    'HCM_IT01':  'HCM_ACC06', 'HCM_IT02':  'HCM_ACC06', 'HCM_IT03':  'HCM_ACC06',
    'HCM_PRN01': 'HCM_ACC06', 'HCM_PRN02': 'HCM_ACC06', 'HCM_PRN03': 'HCM_ACC06',
    'HCM_CAM01': 'HCM_ACC06', 'HCM_CAM02': 'HCM_ACC06',
    'HCM_CAM03': 'HCM_ACC06', 'HCM_CAM04': 'HCM_ACC06',
    'HCM_AP01':  'HCM_ACC06', 'HCM_AP02':  'HCM_ACC06',
    'HCM_PHN01': 'HCM_ACC06', 'HCM_PHN02': 'HCM_ACC06',
}


def build_hcm(net):
    """
    Thêm toàn bộ HCM site vào Mininet net.

    Returns
    -------
    dict:
        'core'  : HCM-CORE switch
        'dist'  : { 'HCM-DIST01': host, 'HCM-DIST02': host }
        'acc'   : { 'HCM-ACC01': switch, ..., 'HCM-ACC06': switch }
        'hosts' : { hostname: host }
    """
    vlan_cfg, _ = _load_configs()
    hcm_vlan = vlan_cfg['hcm']

    nodes = {}

    # ── Core switch ───────────────────────────────────────
    core = net.addSwitch('HCM_CORE', cls=OVSSwitch, failMode='standalone', stp=True, dpid='0000000000000003')
    nodes['core'] = core

    # ── Distribution routers ───────────────────────────────────────
    dist1 = net.addHost('HCM_DIST01', ip=None)
    dist2 = net.addHost('HCM_DIST02', ip=None)
    nodes['dist'] = {'HCM_DIST01': dist1, 'HCM_DIST02': dist2}

    lk_d1 = net.addLink(dist1, core)
    lk_d2 = net.addLink(dist2, core)
    dist1.uplink_intf = lk_d1.intf1.name
    dist1.core_intf   = lk_d1.intf2.name
    dist2.uplink_intf = lk_d2.intf1.name
    dist2.core_intf   = lk_d2.intf2.name

    # ── Access switches ───────────────────────────────────
    # Tên đã dùng _ nhất quán, không cần replace('-','_')
    acc_switches = {}
    dpid_counter = 0x0000000000000200
    for acc_name in ACC_VLANS:
        acc_sw = net.addSwitch(acc_name, cls=OVSSwitch, failMode='standalone', stp=True, dpid=f'{dpid_counter:016x}')
        acc_switches[acc_name] = acc_sw
        dpid_counter += 1

        lk  = net.addLink(acc_sw, dist1)
        lk2 = net.addLink(acc_sw, dist2)
        acc_sw.uplink_dist1 = lk.intf1.name
        acc_sw.uplink_dist2 = lk2.intf1.name

    nodes['acc'] = acc_switches

    # ── End hosts ─────────────────────────────────────────
    hosts = {}
    host_cfg_map = {h['name']: h for h in hcm_vlan['hosts']}

    for hname, h_cfg in host_cfg_map.items():
        acc_name = HOST_TO_ACC.get(hname, 'HCM_ACC06')   # default ACC06 (dùng _)
        acc_sw   = acc_switches[acc_name]

        h = net.addHost(
            hname,
            ip=h_cfg['ip'],
            defaultRoute=f"via {h_cfg['gw']}"
        )
        hosts[hname] = h

        lk = net.addLink(h, acc_sw)
        h.vlan      = h_cfg['vlan']
        h.link_intf = lk.intf2.name

    nodes['hosts'] = hosts

    print(f'[HCM] Đã thêm: 1 CORE, 2 DIST, 6 ACC switches, {len(hosts)} end hosts')
    return nodes


def configure_hcm(hcm_nodes):
    """
    Cấu hình VLAN + STP sau net.start().
    """
    vlan_cfg, _ = _load_configs()
    hcm_vlan = vlan_cfg['hcm']
    host_cfg_map = {h['name']: h for h in hcm_vlan['hosts']}
    all_vlans = list(hcm_vlan['vlans'].keys())

    # STP priorities (HCM_DIST là Mininet Host không phải OVS Switch → không set STP)
    _set_stp_priority('HCM_CORE', 4096)
    for acc_name in ACC_VLANS:
        _set_stp_priority(acc_name, 32768)   # acc_name đã dùng _

    print('[HCM] Cấu hình VLAN ports...')

    # Trunk CORE ↔ DIST
    dist1 = hcm_nodes['dist']['HCM_DIST01']
    dist2 = hcm_nodes['dist']['HCM_DIST02']
    _set_trunk_port(dist1.core_intf, all_vlans)
    _set_trunk_port(dist2.core_intf, all_vlans)

    # Trunk DIST ↔ ACC (acc_name đã dùng _ → lookup trực tiếp)
    for acc_name, vlans in ACC_VLANS.items():
        acc_sw = hcm_nodes['acc'][acc_name]
        _set_trunk_port(acc_sw.uplink_dist1, vlans)
        _set_trunk_port(acc_sw.uplink_dist2, vlans)

    # Access ports
    for hname, h in hcm_nodes['hosts'].items():
        h_cfg = host_cfg_map[hname]
        _set_access_port(h.link_intf, h_cfg['vlan'])

    # DIST host IP
    _configure_dist_interfaces(dist1, 'HCM_DIST01', vlan_cfg)
    _configure_dist_interfaces(dist2, 'HCM_DIST02', vlan_cfg)

    print('[HCM] ✓ VLAN configuration done')


def _configure_dist_interfaces(dist_host, dist_name, vlan_cfg):
    """Sub-interfaces cho DIST host — gộp LAN ports vào br0 (VLAN-aware)."""
    is_dist1 = '01' in dist_name
    hcm_vlans = vlan_cfg['hcm']['vlans']

    dist_host.cmd('sysctl -w net.ipv4.ip_forward=1')

    # Lấy tất cả LAN interfaces (trừ lo và WAN links)
    # WAN interfaces của HCM_DIST01 có tên dạng 'hcmd_*' (kết nối vào WAN switch)
    lan_intfs = [
        intf.name for intf in dist_host.intfList()
        if intf.name != 'lo'
        and '_w' not in intf.name
        and not intf.name.startswith('hcmd_')
    ]
    for intf_name in lan_intfs:
        dist_host.cmd(f'ip link set {intf_name} up')

    # Tạo Linux bridge br0 gộp các LAN interfaces với VLAN filtering & STP
    dist_host.cmd('ip link add name br0 type bridge 2>/dev/null')
    dist_host.cmd('ip link set dev br0 type bridge vlan_filtering 1 stp_state 1 forward_delay 200 2>/dev/null')
    dist_host.cmd('bridge vlan add dev br0 vid 2-4094 self 2>/dev/null')
    for intf_name in lan_intfs:
        dist_host.cmd(f'ip link set {intf_name} master br0 2>/dev/null')
        dist_host.cmd(f'bridge vlan add dev {intf_name} vid 2-4094 2>/dev/null')
    dist_host.cmd('ip link set br0 up')

    for vlan_id, vinfo in hcm_vlans.items():
        sub_intf = f'br0.{vlan_id}'
        prefix = vinfo['subnet'].split('/')[1]
        octet = '2' if is_dist1 else '3'
        ip_addr = vinfo['gateway'].rsplit('.', 1)[0] + f'.{octet}'
        gw_vip = vinfo['gateway']

        dist_host.cmd(f'ip link add link br0 name {sub_intf} type vlan id {vlan_id} 2>/dev/null')
        dist_host.cmd(f'ip addr add {ip_addr}/{prefix} dev {sub_intf} 2>/dev/null')
        if is_dist1:
            dist_host.cmd(f'ip addr add {gw_vip}/{prefix} dev {sub_intf} 2>/dev/null')
        dist_host.cmd(f'ip link set {sub_intf} up')

    print(f'  [{dist_name}] Sub-interfaces configured on br0')




def start_vrrp_hcm(hcm_nodes):
    """Khởi động keepalived trên HCM-DIST01/02."""
    dist1 = hcm_nodes['dist']['HCM_DIST01']
    dist2 = hcm_nodes['dist']['HCM_DIST02']

    if not os.path.exists('/tmp/keepalived_HCM_DIST01.conf'):
        try:
            from scripts.generate_keepalived_conf import main as gen_ka
            gen_ka()
        except Exception:
            pass

    dist1.cmd('keepalived -f /tmp/keepalived_HCM_DIST01.conf -p /tmp/ka_hcm_dist01.pid')
    dist2.cmd('keepalived -f /tmp/keepalived_HCM_DIST02.conf -p /tmp/ka_hcm_dist02.pid')
    print('[HCM] keepalived VRRP started')


def start_frr_hcm(hcm_nodes):
    """Khởi động FRR OSPF trên HCM-DIST01/02 với socket riêng."""
    for dist_name, dist_host in hcm_nodes['dist'].items():
        router_id = '10.30.10.2' if '01' in dist_name else '10.30.10.3'
        hname = getattr(dist_host, 'name', dist_name)
        run_dir = f'/tmp/frr_{hname}'
        dist_host.cmd(f'mkdir -p {run_dir}')
        dist_host.cmd(f'chmod 777 {run_dir}')
        dist_host.cmd(f'chown frr:frr {run_dir} 2>/dev/null; true')
        # Tắt integrated-vtysh-config trong /etc/frr/frr.conf để tránh bị override
        dist_host.cmd("sed -i 's/^service integrated-vtysh-config/no service integrated-vtysh-config/' /etc/frr/frr.conf 2>/dev/null; true")

        # Tìm tất cả WAN interfaces — Phase 9: tên dạng 'hcmd_mpls_g', 'hcmd_lte_g'
        wan_intfs = [intf.name for intf in dist_host.intfList() if intf.name.startswith('hcmd_')]
        # Fallback: tìm theo '_w' (Phase 1-8 naming)
        if not wan_intfs:
            wan_intfs = [intf.name for intf in dist_host.intfList() if '_w' in intf.name]

        conf_file  = f'{run_dir}/frr.conf'
        zebra_conf = f'{run_dir}/zebra.conf'
        ospfd_conf = f'{run_dir}/ospfd.conf'
        passive_lines = " passive-interface default\n"
        for wi in wan_intfs:
            passive_lines += f" no passive-interface {wi}\n"
        zebra_content = (
            f"frr version 8\n"
            f"frr defaults traditional\n"
            f"no service integrated-vtysh-config\n"
            f"hostname {hname}\n"
            f"log file {run_dir}/frr.log\n"
            "line vty\n"
        )
        ospfd_content = (
            f"frr version 8\n"
            f"frr defaults traditional\n"
            f"no service integrated-vtysh-config\n"
            f"hostname {hname}\n"
            f"log file {run_dir}/frr.log\n"
            "router ospf\n"
            f" ospf router-id {router_id}\n"
            " network 10.30.0.0/16 area 0\n"
            " network 192.168.10.0/30 area 0\n"
            " network 192.168.20.0/30 area 0\n"
            " network 192.168.30.0/30 area 0\n"
            " network 172.16.0.0/12 area 0\n"
            f"{passive_lines}"
            " redistribute connected\n"
            "line vty\n"
        )
        dist_host.cmd(f'printf "{zebra_content}" > {zebra_conf}')
        dist_host.cmd(f'printf "{ospfd_content}" > {ospfd_conf}')
        dist_host.cmd(f'cp {ospfd_conf} {conf_file}')
        dist_host.cmd(f'kill -9 $(cat {run_dir}/zebra.pid 2>/dev/null) 2>/dev/null; true')
        dist_host.cmd(f'kill -9 $(cat {run_dir}/ospfd.pid 2>/dev/null) 2>/dev/null; true')
        dist_host.cmd(f'pkill -9 -f "zebra.*{run_dir}" 2>/dev/null; true')
        dist_host.cmd(f'pkill -9 -f "ospfd.*{run_dir}" 2>/dev/null; true')
        dist_host.cmd(f'rm -f {run_dir}/zebra.pid {run_dir}/ospfd.pid {run_dir}/zserv.api 2>/dev/null; true')
        dist_host.cmd('sleep 1')

        dist_host.cmd(
            f'/usr/lib/frr/zebra -d -f {zebra_conf} '
            f'-i {run_dir}/zebra.pid -z {run_dir}/zserv.api '
            f'--vty_socket {run_dir} 2>{run_dir}/zebra.err '
            f'|| /usr/libexec/frr/zebra -d -f {zebra_conf} '
            f'-i {run_dir}/zebra.pid -z {run_dir}/zserv.api '
            f'--vty_socket {run_dir} 2>{run_dir}/zebra.err'
        )
        dist_host.cmd('sleep 1')
        dist_host.cmd(
            f'/usr/lib/frr/ospfd -d -f {ospfd_conf} '
            f'-i {run_dir}/ospfd.pid -z {run_dir}/zserv.api '
            f'--vty_socket {run_dir} 2>{run_dir}/ospfd.err '
            f'|| /usr/libexec/frr/ospfd -d -f {ospfd_conf} '
            f'-i {run_dir}/ospfd.pid -z {run_dir}/zserv.api '
            f'--vty_socket {run_dir} 2>{run_dir}/ospfd.err'
        )
        print(f'  [{dist_name}] FRR OSPF started, router-id={router_id} (isolated socket)')


