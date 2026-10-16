"""
fault_injection/scenarios/f08_vpn_failure.py
Kịch bản F08: Gián đoạn kênh truyền IPSec VPN (VPN Failure).

Mô tả:
  - Chặn lưu lượng đường hầm IPSec VPN (IKE UDP 500, NAT-T UDP 4500, giao thức ESP proto 50)
    hoặc ngắt giao diện switch WAN_SW_VPN.
  - Phù hợp với loại lỗi VPN_FAULT / SECURITY_FAULT trong mạng SD-WAN.
  - Tác động: Mất kết nối bảo mật giữa các chi nhánh và Trung tâm dữ liệu (DC).
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class VPNFailureScenario(BaseFaultScenario):
    scenario_id = "F08"
    name = "VPN Failure"
    category = "VPN_FAULT"
    description = "Chặn các gói tin IPSec VPN (UDP 500/4500, proto ESP) trên Gateway DC và HCM."
    default_duration = 30.0
    target_devices = ["WAN_VPN", "DC_SP_GW", "HCM_DIST01"]
    target_interfaces = ["dcgw_vpn_g", "hcmd_vpn_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_intf: str = "dcgw_vpn_g"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_intf = target_intf

    def inject(self, net: Any = None) -> bool:
        # Chặn IKE / ESP qua iptables trên DC Gateway
        node = net.get("DC_SP_GW") if net and hasattr(net, "get") else None
        cmd = (
            "iptables -I INPUT 1 -p udp --dport 500 -j DROP && "
            "iptables -I INPUT 1 -p udp --dport 4500 -j DROP && "
            "iptables -I INPUT 1 -p 50 -j DROP"
        )
        ret, _, _ = self.execute_command(cmd, node=node)

        # Đồng thời ngắt interface WAN_VPN nếu có
        self.execute_command(f"ip link set dev {self.target_intf} down 2>/dev/null")
        return ret == 0

    def recover(self, net: Any = None) -> bool:
        node = net.get("DC_SP_GW") if net and hasattr(net, "get") else None
        cmd = (
            "iptables -D INPUT -p udp --dport 500 -j DROP 2>/dev/null; "
            "iptables -D INPUT -p udp --dport 4500 -j DROP 2>/dev/null; "
            "iptables -D INPUT -p 50 -j DROP 2>/dev/null"
        )
        self.execute_command(cmd, node=node)
        self.execute_command(f"ip link set dev {self.target_intf} up 2>/dev/null")
        return True
