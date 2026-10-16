"""
fault_injection/scenarios/f11_server_failure.py
Kịch bản F11: Sự cố máy chủ Trung tâm dữ liệu (Data Center Server Failure).

Mô tả:
  - Làm sập máy chủ Web chính DC_WEB01 (dừng tiến trình Web server hoặc hạ interface DC_WEB01-eth1).
  - Phù hợp với loại lỗi SERVER_FAULT / PORT_FAULT trong kiến trúc Data Center Spine-Leaf.
  - Tác động: Kiểm thử cơ chế Health-check của HAProxy Load Balancer
    và khả năng cô lập nút lỗi, chuyển hướng toàn bộ traffic sang DC_WEB02.
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class ServerFailureScenario(BaseFaultScenario):
    scenario_id = "F11"
    name = "Server Failure"
    category = "SERVER_FAULT"
    description = "Hạ giao diện mạng và dừng dịch vụ Web trên máy chủ DC_WEB01 tại Data Center."
    default_duration = 30.0
    target_devices = ["DC_WEB01", "DC_LB01"]
    target_interfaces = ["DC_WEB01-eth1"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_server: str = "DC_WEB01", intf_name: str = "DC_WEB01-eth1"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_server = target_server
        self.intf_name = intf_name

    def inject(self, net: Any = None) -> bool:
        node = net.get(self.target_server) if net and hasattr(net, "get") else None

        # Dừng HTTP server nếu đang chạy trên host
        self.execute_command("pkill -9 -f 'python.*http.server' 2>/dev/null; systemctl stop nginx 2>/dev/null", node=node)

        # Hạ interface mạng của Server
        cmd = f"ip link set dev {self.intf_name} down 2>/dev/null"
        ret, _, _ = self.execute_command(cmd, node=node)
        return ret == 0

    def recover(self, net: Any = None) -> bool:
        node = net.get(self.target_server) if net and hasattr(net, "get") else None

        # Bật lại interface mạng
        cmd = f"ip link set dev {self.intf_name} up 2>/dev/null"
        self.execute_command(cmd, node=node)

        # Khởi động lại dịch vụ HTTP giả lập nếu cần
        self.execute_command("python3 -m http.server 80 >/dev/null 2>&1 &", node=node)
        return True
