"""
fault_injection/scenarios/f07_5g_degradation.py
Kịch bản F07: Suy giảm chất lượng đường truyền 5G (5G Path Degradation).

Mô tả:
  - Can thiệp suy giảm chất lượng dịch vụ (QoS) trên đường truyền 5G NR bằng tc netem:
    Tăng latency lên 180ms (jitter ±40ms), packet loss lên 15%.
  - Phù hợp với loại lỗi WAN_DEGRADATION / SOFT_WARNING trong mô hình nghiên cứu.
  - Tác động: Không làm mất liên kết vật lý nhưng vi phạm nghiêm trọng ngưỡng SLA
    của các ứng dụng thời gian thực, buộc AI Engine và SD-WAN cảnh báo và điều phối lưu lượng.
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class FiveGDegradationScenario(BaseFaultScenario):
    scenario_id = "F07"
    name = "5G Path Degradation"
    category = "WAN_DEGRADATION"
    description = "Áp dụng tc netem tăng delay 180ms (jitter 40ms) và packet loss 15% trên đường 5G NR."
    default_duration = 35.0
    target_devices = ["WAN_FIVEG", "NT_DIST01", "HCM_DIST01"]
    target_interfaces = ["ntd1_5g_g", "hcmd_5g_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_intf: str = "ntd1_5g_g", delay_ms: int = 180, jitter_ms: int = 40, loss_pct: float = 15.0):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_intf = target_intf
        self.delay_ms = delay_ms
        self.jitter_ms = jitter_ms
        self.loss_pct = loss_pct

    def inject(self, net: Any = None) -> bool:
        # Xóa qdisc cũ nếu có trước khi thêm
        self.recover(net)
        cmd = f"tc qdisc add dev {self.target_intf} root netem delay {self.delay_ms}ms {self.jitter_ms}ms loss {self.loss_pct}%"
        node = net.get("NT_DIST01") if net and hasattr(net, "get") else None
        ret, _, _ = self.execute_command(cmd, node=node)
        return ret == 0

    def recover(self, net: Any = None) -> bool:
        cmd = f"tc qdisc del dev {self.target_intf} root 2>/dev/null"
        node = net.get("NT_DIST01") if net and hasattr(net, "get") else None
        self.execute_command(cmd, node=node)
        return True
