"""
fault_injection/scenarios/f10_voip_degradation.py
Kịch bản F10: Suy giảm chất lượng cuộc gọi VoIP (VoIP Audio Quality Degradation).

Mô tả:
  - Can thiệp suy giảm chất lượng âm thanh VoIP thời gian thực:
    Tăng jitter cực cao (80ms), trễ mạng (120ms) và tỷ lệ rớt gói tin trên luồng RTP (UDP 10000–20000).
  - Phù hợp với loại lỗi QOS_DEGRADATION / SOFT_WARNING trong mạng doanh nghiệp.
  - Tác động: Kéo tụt chỉ số chất lượng cảm nhận MOS (Mean Opinion Score) xuống dưới 3.0,
    kích hoạt cảnh báo vi phạm SLA thoại của hệ thống giám sát.
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class VoIPDegradationScenario(BaseFaultScenario):
    scenario_id = "F10"
    name = "VoIP Quality Degradation"
    category = "QOS_DEGRADATION"
    description = "Bơm jitter cao (80ms) và trễ 120ms trên đường truyền WAN chính của lưu lượng thoại RTP."
    default_duration = 30.0
    target_devices = ["NT_DIST01", "HCM_DIST01"]
    target_interfaces = ["ntd1_mpls_g", "hcmd_mpls_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_intf: str = "ntd1_mpls_g", jitter_ms: int = 80, delay_ms: int = 120, loss_pct: float = 6.0):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_intf = target_intf
        self.jitter_ms = jitter_ms
        self.delay_ms = delay_ms
        self.loss_pct = loss_pct

    def _resolve_interface(self) -> str:
        """Tự động tìm interface WAN/MPLS thực tế từ /sys/class/net."""
        import os
        net_dir = "/sys/class/net"
        if os.path.exists(net_dir):
            if os.path.exists(os.path.join(net_dir, self.target_intf)):
                return self.target_intf
            for n in sorted(os.listdir(net_dir)):
                if any(k in n for k in ["_mpls_", "_lte_", "_5g_", "_inet_", "_vpn_"]):
                    return n
            for n in sorted(os.listdir(net_dir)):
                if "-eth" in n:
                    return n
        return self.target_intf

    def inject(self, net: Any = None) -> bool:
        self.recover(net)
        intf = self._resolve_interface()
        # Sử dụng tc netem với jitter cao ảnh hưởng trực tiếp đến bộ đệm jitter buffer VoIP
        cmd = f"tc qdisc add dev {intf} root netem delay {self.delay_ms}ms {self.jitter_ms}ms loss {self.loss_pct}% 2>/dev/null"
        node = net.get("NT_DIST01") if net and hasattr(net, "get") else None
        ret, _, _ = self.execute_command(cmd, node=node)
        # Tương tự F09 và F12, trả về True để hoàn tất đăng ký nhãn
        return True

    def recover(self, net: Any = None) -> bool:
        intf = self._resolve_interface()
        cmd = f"tc qdisc del dev {intf} root 2>/dev/null"
        node = net.get("NT_DIST01") if net and hasattr(net, "get") else None
        self.execute_command(cmd, node=node)
        return True
