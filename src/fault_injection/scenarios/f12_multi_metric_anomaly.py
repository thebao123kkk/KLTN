"""
fault_injection/scenarios/f12_multi_metric_anomaly.py
Kịch bản F12: Sự cố dị thường đa chỉ số phức hợp (Multi-Metric Anomaly).

Mô tả:
  - Kích hoạt đồng thời nhiều sự cố ở cả 3 mặt phẳng:
    1. Data Plane: Tắc nghẽn lưu lượng (Congestion) và suy giảm đường truyền WAN 5G (tc netem).
    2. Control Plane: Quá tải hoặc gửi tín hiệu HUP reload Faucet Controller (pkill -HUP faucet).
    3. Device Health: Tăng đột biến tải CPU và bộ nhớ (CPU/Memory stress spike).
  - Phù hợp với trường hợp kiểm thử độ nhạy Vector 8 chiều (8D State Vector s_t)
    và đánh giá khả năng hội tụ của tác nhân PPO trong Model_Research_and_Implementation_Plan.md.
  - Tác động: Kiểm thử năng lực phân loại nguyên nhân gốc rễ (RCA) của AI Engine
    khi xuất hiện đồng thời nhiều triệu chứng phức tạp.
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class MultiMetricAnomalyScenario(BaseFaultScenario):
    scenario_id = "F12"
    name = "Multi-Metric Anomaly"
    category = "MULTI_METRIC_ANOMALY"
    description = "Kích hoạt đồng thời suy giảm WAN 5G, bão lưu lượng và tải CPU/Controller Reload."
    default_duration = 40.0
    target_devices = ["WAN_FIVEG", "BL_GW", "NT_CORE", "FaucetController"]
    target_interfaces = ["ntd1_5g_g", "blgw_inet_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_intf: str = "ntd1_5g_g", flood_intf: str = "blgw_inet_g"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_intf = target_intf
        self.flood_intf = flood_intf

    def _resolve_interfaces(self) -> tuple[str, str]:
        """Tự động tìm interfaces WAN thực tế từ /sys/class/net."""
        import os
        net_dir = "/sys/class/net"
        intf1, intf2 = self.target_intf, self.flood_intf
        if os.path.exists(net_dir):
            wan_ifaces = [n for n in sorted(os.listdir(net_dir)) if any(k in n for k in ["_5g_", "_inet_", "_mpls_", "_lte_", "_vpn_"])]
            if len(wan_ifaces) >= 2:
                intf1, intf2 = wan_ifaces[0], wan_ifaces[1]
            elif wan_ifaces:
                intf1 = wan_ifaces[0]
            else:
                eth_ifaces = [n for n in sorted(os.listdir(net_dir)) if "-eth" in n]
                if len(eth_ifaces) >= 2:
                    intf1, intf2 = eth_ifaces[0], eth_ifaces[1]
                elif eth_ifaces:
                    intf1 = eth_ifaces[0]
        return intf1, intf2

    def inject(self, net: Any = None) -> bool:
        intf1, intf2 = self._resolve_interfaces()
        # 1. Tiêm suy giảm QoS trên đường 5G (delay 200ms, loss 20%)
        self.execute_command(f"tc qdisc add dev {intf1} root netem delay 200ms 50ms loss 20% 2>/dev/null || true")

        # 2. Tiêm nghẽn băng thông trên đường Internet
        self.execute_command(f"tc qdisc add dev {intf2} root tbf rate 2mbit burst 32kbit latency 500ms 2>/dev/null || true")

        # 3. Gửi tín hiệu reload Faucet Controller (FAUCET_RELOAD theo tài liệu nghiên cứu)
        self.execute_command("pkill -HUP faucet 2>/dev/null || pkill -HUP ryu-manager 2>/dev/null || true")

        # 4. Giả lập tải CPU tạm thời trên host (stress ngắn 5s)
        self.execute_command("python3 -c 'import time; t=time.time()+5; [x*x for x in range(10000000) if time.time()<t]' >/dev/null 2>&1 &")

        return True

    def recover(self, net: Any = None) -> bool:
        intf1, intf2 = self._resolve_interfaces()
        # Xóa các cấu hình qdisc đã tiêm
        self.execute_command(f"tc qdisc del dev {intf1} root 2>/dev/null || true")
        self.execute_command(f"tc qdisc del dev {intf2} root 2>/dev/null || true")

        # Đảm bảo Faucet / Ryu hoạt động bình thường
        self.execute_command("pkill -9 iperf3 2>/dev/null || true")
        return True
