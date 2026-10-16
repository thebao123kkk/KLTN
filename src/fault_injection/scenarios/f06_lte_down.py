"""
fault_injection/scenarios/f06_lte_down.py
Kịch bản F06: Đường truyền WAN LTE dự phòng bị sập (LTE Link Down).

Mô tả:
  - Ngắt giao diện mạng LTE 4G dự phòng (WAN_SW_LTE / các cổng *_lte_g).
  - Phù hợp với loại lỗi LINK_FAULT / WAN_FAULT trong SD-WAN.
  - Tác động: Làm mất kênh truyền dự phòng cuối cùng của các Site vệ tinh (Bảo Lộc, Nha Trang).
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class LTEDownScenario(BaseFaultScenario):
    scenario_id = "F06"
    name = "WAN LTE Down"
    category = "LINK_FAULT"
    description = "Hạ giao diện kết nối WAN LTE dự phòng trên Gateway và switch WAN_LTE."
    default_duration = 30.0
    target_devices = ["WAN_LTE", "BL_GW", "NT_DIST01"]
    target_interfaces = ["blgw_lte_g", "ntd1_lte_g", "hcmd_lte_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_intf: str = "blgw_lte_g"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_intf = target_intf

    def inject(self, net: Any = None) -> bool:
        node = net.get("BL_GW") if net and hasattr(net, "get") else None
        cmd = f"ip link set dev {self.target_intf} down 2>/dev/null || ovs-vsctl set interface {self.target_intf} admin_state=down"
        ret, _, _ = self.execute_command(cmd, node=node)
        self.execute_command(f"ip link set dev {self.target_intf.replace('_g', '_s')} down 2>/dev/null")
        return ret == 0

    def recover(self, net: Any = None) -> bool:
        node = net.get("BL_GW") if net and hasattr(net, "get") else None
        cmd = f"ip link set dev {self.target_intf} up 2>/dev/null || ovs-vsctl set interface {self.target_intf} admin_state=up"
        ret, _, _ = self.execute_command(cmd, node=node)
        self.execute_command(f"ip link set dev {self.target_intf.replace('_g', '_s')} up 2>/dev/null")
        return ret == 0
