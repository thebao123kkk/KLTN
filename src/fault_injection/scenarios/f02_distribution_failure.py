"""
fault_injection/scenarios/f02_distribution_failure.py
Kịch bản F02: Lỗi Distribution Switch/Link (Distribution Failure).

Mô tả:
  - Ngắt switch Distribution chính (NT_DIST01 hoặc HCM_DIST01) hoặc ngắt link kết nối tới Core switch.
  - Phù hợp với loại lỗi LINK_FAULT / SWITCH_FAULT trong mô hình nghiên cứu.
  - Tác động: Kiểm thử khả năng chuyển đổi dự phòng của giao thức VRRP (keepalived) sang DIST02
    và hội tụ định tuyến OSPF.
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class DistributionFailureScenario(BaseFaultScenario):
    scenario_id = "F02"
    name = "Distribution Failure"
    category = "LINK_FAULT"
    description = "Ngắt kết nối Distribution Switch chính (NT_DIST01 <-> NT_CORE) để kích hoạt VRRP/OSPF failover."
    default_duration = 35.0
    target_devices = ["NT_DIST01", "NT_CORE"]
    target_interfaces = ["ntd1_core", "NT_CORE-eth1"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 dist_node: str = "NT_DIST01", core_node: str = "NT_CORE"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.dist_node = dist_node
        self.core_node = core_node

    def _resolve_interface(self) -> str:
        """Tự động tìm interface trunk/distribution switch thực tế từ /sys/class/net."""
        import os
        net_dir = "/sys/class/net"
        if os.path.exists(net_dir):
            ifaces = [n for n in sorted(os.listdir(net_dir)) if "-eth" in n]
            if len(ifaces) >= 2:
                return ifaces[1]
            elif ifaces:
                return ifaces[0]
        return "NT_DIST01-eth1"

    def inject(self, net: Any = None) -> bool:
        if net is not None and hasattr(net, "configLinkStatus"):
            try:
                net.configLinkStatus(self.dist_node, self.core_node, "down")
                return True
            except Exception:
                pass

        # Ngắt link qua ifconfig / ip link trên node hoặc host
        intf = self._resolve_interface()
        cmd = f"ip link set dev {intf} down 2>/dev/null || ip link set {intf} down 2>/dev/null || ovs-vsctl set interface {intf} admin_state=down 2>/dev/null || true"
        node = net.get(self.dist_node) if net and hasattr(net, "get") else None
        self.execute_command(cmd, node=node)
        return True

    def recover(self, net: Any = None) -> bool:
        if net is not None and hasattr(net, "configLinkStatus"):
            try:
                net.configLinkStatus(self.dist_node, self.core_node, "up")
                return True
            except Exception:
                pass

        intf = self._resolve_interface()
        cmd = f"ip link set dev {intf} up 2>/dev/null || ip link set {intf} up 2>/dev/null || ovs-vsctl set interface {intf} admin_state=up 2>/dev/null || true"
        node = net.get(self.dist_node) if net and hasattr(net, "get") else None
        self.execute_command(cmd, node=node)
        return True
