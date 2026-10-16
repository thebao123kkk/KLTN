"""
fault_injection/scenarios/f03_ospf_failure.py
Kịch bản F03: Lỗi giao thức định tuyến OSPF (OSPF Neighbor/Routing Failure).

Mô tả:
  - Chặn các gói tin OSPF (IP Protocol 89) bằng iptables hoặc tạm dừng tiến trình ospfd trên FRR router.
  - Phù hợp với loại lỗi ROUTING_FAULT / SOFT_WARNING.
  - Tác động: Gây hết hạn Dead Interval (40s), mất quan hệ láng giềng OSPF (Neighbor Down),
    làm đứt đoạn định tuyến liên site.
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class OSPFFailureScenario(BaseFaultScenario):
    scenario_id = "F03"
    name = "OSPF Neighbor Failure"
    category = "ROUTING_FAULT"
    description = "Chặn lưu lượng OSPF Hello (Protocol 89) trên Router NT_DIST01 gây đứt quan hệ láng giềng OSPF."
    default_duration = 45.0
    target_devices = ["NT_DIST01", "BL_GW"]
    target_interfaces = ["ntd1_mpls_g", "blgw_mpls_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_router: str = "NT_DIST01"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_router = target_router

    def inject(self, net: Any = None) -> bool:
        node = net.get(self.target_router) if net and hasattr(net, "get") else None
        # Chặn OSPF protocol (IP proto 89) ở cả INPUT và OUTPUT
        cmd = "iptables -I INPUT 1 -p 89 -j DROP && iptables -I OUTPUT 1 -p 89 -j DROP"
        ret, _, _ = self.execute_command(cmd, node=node)
        return ret == 0

    def recover(self, net: Any = None) -> bool:
        node = net.get(self.target_router) if net and hasattr(net, "get") else None
        # Xóa rule chặn OSPF
        cmd = "iptables -D INPUT -p 89 -j DROP 2>/dev/null; iptables -D OUTPUT -p 89 -j DROP 2>/dev/null"
        ret, _, _ = self.execute_command(cmd, node=node)
        return ret == 0
