"""
fault_injection/scenarios/f05_internet_down.py
Kịch bản F05: Đường truyền WAN Internet bị sập (Internet Link Down).

Mô tả:
  - Ngắt giao diện mạng Internet broadband (WAN_SW_INET / các cổng *_inet_g).
  - Phù hợp với loại lỗi LINK_FAULT / WAN_FAULT trong mạng doanh nghiệp.
  - Tác động: Gây mất kết nối truy cập Internet thông thường và các dịch vụ Web/App
    buộc SD-WAN chuyển sang đường LTE hoặc MPLS.
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class InternetDownScenario(BaseFaultScenario):
    scenario_id = "F05"
    name = "WAN Internet Down"
    category = "LINK_FAULT"
    description = "Hạ giao diện kết nối WAN Internet broadband trên Gateway và switch WAN_INET."
    default_duration = 30.0
    target_devices = ["WAN_INET", "HCM_DIST01", "BL_GW"]
    target_interfaces = ["hcmd_inet_g", "blgw_inet_g", "ntd1_inet_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_intf: str = "hcmd_inet_g"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_intf = target_intf

    def inject(self, net: Any = None) -> bool:
        node = net.get("HCM_DIST01") if net and hasattr(net, "get") else None
        cmd = f"ip link set dev {self.target_intf} down 2>/dev/null || ovs-vsctl set interface {self.target_intf} admin_state=down"
        ret, _, _ = self.execute_command(cmd, node=node)
        self.execute_command(f"ip link set dev {self.target_intf.replace('_g', '_s')} down 2>/dev/null")
        return ret == 0

    def recover(self, net: Any = None) -> bool:
        node = net.get("HCM_DIST01") if net and hasattr(net, "get") else None
        cmd = f"ip link set dev {self.target_intf} up 2>/dev/null || ovs-vsctl set interface {self.target_intf} admin_state=up"
        ret, _, _ = self.execute_command(cmd, node=node)
        self.execute_command(f"ip link set dev {self.target_intf.replace('_g', '_s')} up 2>/dev/null")
        return ret == 0
