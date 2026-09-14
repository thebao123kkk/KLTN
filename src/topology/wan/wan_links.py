"""
topology/wan/wan_links.py
WAN Emulation — 5 Transport Paths (stub cho Phase 1-6)
=============================================
Đây là placeholder. Nội dung đầy đủ sẽ viết ở Phase 9.

5 WAN transport paths (emulate bằng tc netem trên OVS):
  1. MPLS        — độ trễ thấp, băng thông cao, không mất gói
  2. Internet    — độ trễ vừa, băng thông vừa, mất gói nhỏ
  3. LTE 4G      — độ trễ cao hơn, jitter, packet loss
  4. 5G          — tương tự LTE nhưng tốt hơn
  5. VPN (IPSec) — đi trên Internet nhưng có overhead cipher

Hàm connect_sites_wan(net, bl_nodes, nt_nodes, hcm_nodes, dc_nodes)
sẽ kết nối các site lại với nhau qua 5 OVS switch WAN.
"""


def connect_sites_wan(net, bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """
    [Phase 9 placeholder]
    Kết nối 4 site qua 5 WAN transport paths.
    Hiện tại chỉ tạo kết nối direct (không netem) cho Phase 1-6.
    """
    print('[WAN] Phase 1-6: WAN stub — sites connected via direct links')
    print('[WAN] Phase 9 sẽ thêm 5 OVS WAN switch với tc netem')

    # Direct link BL ↔ HCM (qua GW hosts)
    # Create interface names that are valid on Linux (<=15 chars, no hyphens)
    bl_gw  = bl_nodes['gw']
    hcm_d1 = hcm_nodes['dist']['HCM_DIST01']
    nt_d1  = nt_nodes['dist']['NT_DIST01']
    dc_gw  = dc_nodes['gw']

    def _mk_ifname(node, suffix):
        # node: Mininet node object; suffix: short string like 'w1'
        base = getattr(node, 'name', str(node)).replace('-', '_')
        sep = '_'
        maxlen = 15
        needed = len(sep) + len(suffix)
        max_base = maxlen - needed
        if max_base < 1:
            max_base = 1
        base_trunc = base[:max_base]
        return f"{base_trunc}{sep}{suffix}"

    lk1_if1 = _mk_ifname(bl_gw, 'w1')
    lk1_if2 = _mk_ifname(hcm_d1, 'w1')
    lk1 = net.addLink(bl_gw, hcm_d1, intfName1=lk1_if1, intfName2=lk1_if2)
    bl_gw.wan_intf  = lk1.intf1.name
    hcm_d1.wan_intf = lk1.intf2.name

    lk2_if1 = _mk_ifname(nt_d1, 'w2')
    lk2_if2 = _mk_ifname(hcm_d1, 'w2')
    lk2 = net.addLink(nt_d1, hcm_d1, intfName1=lk2_if1, intfName2=lk2_if2)
    nt_d1.wan_intf    = lk2.intf1.name
    hcm_d1.wan_intf2  = lk2.intf2.name

    lk3_if1 = _mk_ifname(hcm_d1, 'w3')
    lk3_if2 = _mk_ifname(dc_gw, 'w3')
    lk3 = net.addLink(hcm_d1, dc_gw, intfName1=lk3_if1, intfName2=lk3_if2)
    hcm_d1.wan_intf3 = lk3.intf1.name
    dc_gw.wan_intf   = lk3.intf2.name

    return {
        'bl_hcm_link':  lk1,
        'nt_hcm_link':  lk2,
        'hcm_dc_link':  lk3,
    }


def configure_wan_ips(wan_links, bl_nodes, nt_nodes, hcm_nodes, dc_nodes):
    """
    Đặt IP cho WAN interfaces (point-to-point /30).
    Dùng dải 192.168.x.x/30 cho WAN links.
    """
    bl_gw  = bl_nodes['gw']
    nt_d1  = nt_nodes['dist']['NT_DIST01']
    hcm_d1 = hcm_nodes['dist']['HCM_DIST01']
    dc_gw  = dc_nodes['gw']

    # BL ↔ HCM: 192.168.10.0/30
    bl_gw.cmd(f'ip addr add 192.168.10.1/30 dev {bl_gw.wan_intf}')
    bl_gw.cmd(f'ip link set {bl_gw.wan_intf} up')
    hcm_d1.cmd(f'ip addr add 192.168.10.2/30 dev {hcm_d1.wan_intf}')
    hcm_d1.cmd(f'ip link set {hcm_d1.wan_intf} up')

    # NT ↔ HCM: 192.168.20.0/30
    nt_d1.cmd(f'ip addr add 192.168.20.1/30 dev {nt_d1.wan_intf}')
    nt_d1.cmd(f'ip link set {nt_d1.wan_intf} up')
    hcm_d1.cmd(f'ip addr add 192.168.20.2/30 dev {hcm_d1.wan_intf2}')
    hcm_d1.cmd(f'ip link set {hcm_d1.wan_intf2} up')

    # HCM ↔ DC: 192.168.30.0/30
    hcm_d1.cmd(f'ip addr add 192.168.30.1/30 dev {hcm_d1.wan_intf3}')
    hcm_d1.cmd(f'ip link set {hcm_d1.wan_intf3} up')
    dc_gw.cmd(f'ip addr add 192.168.30.2/30 dev {dc_gw.wan_intf}')
    dc_gw.cmd(f'ip link set {dc_gw.wan_intf} up')

    print('[WAN] WAN interface IPs configured (Phase 1-6 direct links)')
