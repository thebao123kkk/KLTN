"""
fault_injection/scenarios/f04_mpls_down.py
Kịch bản F04: Đường truyền WAN MPLS bị sập (MPLS Link Down).

Mô tả:
  - Ngắt đường truyền WAN MPLS (kênh truyền chính, SLA premium, cost OSPF = 10).
  - Phù hợp với loại lỗi LINK_FAULT / WAN_FAULT trong mạng SD-WAN.
  - Tác động: Kích hoạt PathMonitor và SD-WAN Controller chuyển hướng lưu lượng ưu tiên
    (VoIP, Database) sang các đường truyền dự phòng (5G, Internet, LTE).
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class MPLSDownScenario(BaseFaultScenario):
    scenario_id = "F04"
    name = "WAN MPLS Down"
    category = "LINK_FAULT"
    description = "Hạ giao diện mạng WAN MPLS trên Gateway các Site hoặc ngắt cổng OVS switch WAN_MPLS."
    default_duration = 30.0
    target_devices = ["WAN_MPLS", "NT_DIST01", "HCM_DIST01"]
    target_interfaces = ["ntd1_mpls_g", "hcmd_mpls_g", "blgw_mpls_g", "dcgw_mpls_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_intf: str = "ntd1_mpls_g", wan_switch: str = "WAN_MPLS"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_intf = target_intf
        self.wan_switch = wan_switch

    def inject(self, net: Any = None) -> bool:
        # Cách 1: Hạ interface trên node nếu có
        node = net.get("NT_DIST01") if net and hasattr(net, "get") else None
        cmd = f"ip link set dev {self.target_intf} down 2>/dev/null || ovs-vsctl set interface {self.target_intf} admin_state=down"
        ret, _, _ = self.execute_command(cmd, node=node)

        # Đảm bảo hạ interface switch phía WAN
        self.execute_command(f"ip link set dev {self.target_intf.replace('_g', '_s')} down 2>/dev/null")
        return ret == 0

    def recover(self, net: Any = None) -> bool:
        node = net.get("NT_DIST01") if net and hasattr(net, "get") else None
        cmd = f"ip link set dev {self.target_intf} up 2>/dev/null || ovs-vsctl set interface {self.target_intf} admin_state=up"
        ret, _, _ = self.execute_command(cmd, node=node)
        self.execute_command(f"ip link set dev {self.target_intf.replace('_g', '_s')} up 2>/dev/null")
        return ret == 0
