"""
fault_injection/scenarios/f01_access_link_failure.py
Kịch bản F01: Lỗi liên kết Access Switch (Access Link Failure).

Mô tả:
  - Ngắt liên kết giữa Access switch (ví dụ: NT_ACC01) và Core/Distribution switch,
    hoặc ngắt interface kết nối xuống các VLAN end-user.
  - Phù hợp với loại lỗi PORT_FAULT / LINK_FAULT trong mô hình nghiên cứu.
  - Tác động: Host ở tầng Access mất kết nối lên Gateway/Core, gây mất gói tin (Packet Loss).
"""

from typing import Any, List, Optional
from fault_injection.fault_injector import BaseFaultScenario


class AccessLinkFailureScenario(BaseFaultScenario):
    scenario_id = "F01"
    name = "Access Link Failure"
    category = "PORT_FAULT"
    description = "Ngắt liên kết uplink của Access switch (NT_ACC01 -> NT_CORE) gây đứt đoạn kết nối cục bộ."
    default_duration = 30.0
    target_devices = ["NT_ACC01", "NT_CORE"]
    target_interfaces = ["NT_ACC01-eth1", "NT_CORE-eth2"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 switch_name: str = "NT_ACC01", peer_switch: str = "NT_CORE", intf_name: str = "NT_ACC01-eth1"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.switch_name = switch_name
        self.peer_switch = peer_switch
        self.intf_name = intf_name

    def inject(self, net: Any = None) -> bool:
        if net is not None and hasattr(net, "configLinkStatus"):
            try:
                net.configLinkStatus(self.switch_name, self.peer_switch, "down")
                return True
            except Exception:
                pass

        # Fallback qua lệnh Linux / OVS
        cmd = f"ip link set {self.intf_name} down 2>/dev/null || ovs-vsctl set interface {self.intf_name} admin_state=down"
        ret, _, _ = self.execute_command(cmd)
        return ret == 0

    def recover(self, net: Any = None) -> bool:
        if net is not None and hasattr(net, "configLinkStatus"):
            try:
                net.configLinkStatus(self.switch_name, self.peer_switch, "up")
                return True
            except Exception:
                pass

        cmd = f"ip link set {self.intf_name} up 2>/dev/null || ovs-vsctl set interface {self.intf_name} admin_state=up"
        ret, _, _ = self.execute_command(cmd)
        return ret == 0
