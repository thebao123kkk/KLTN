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

    def inject(self, net: Any = None) -> bool:
        # 1. Tiêm suy giảm QoS trên đường 5G (delay 200ms, loss 20%)
        self.execute_command(f"tc qdisc add dev {self.target_intf} root netem delay 200ms 50ms loss 20% 2>/dev/null")

        # 2. Tiêm nghẽn băng thông trên đường Internet
        self.execute_command(f"tc qdisc add dev {self.flood_intf} root tbf rate 2mbit burst 32kbit latency 500ms 2>/dev/null")

        # 3. Gửi tín hiệu reload Faucet Controller (FAUCET_RELOAD theo tài liệu nghiên cứu)
        self.execute_command("pkill -HUP faucet 2>/dev/null || pkill -HUP ryu-manager 2>/dev/null")

        # 4. Giả lập tải CPU tạm thời trên host (stress ngắn 5s)
        self.execute_command("python3 -c 'import time; t=time.time()+5; [x*x for x in range(10000000) if time.time()<t]' >/dev/null 2>&1 &")

        return True

    def recover(self, net: Any = None) -> bool:
        # Xóa các cấu hình qdisc đã tiêm
        self.execute_command(f"tc qdisc del dev {self.target_intf} root 2>/dev/null")
        self.execute_command(f"tc qdisc del dev {self.flood_intf} root 2>/dev/null")

        # Đảm bảo Faucet / Ryu hoạt động bình thường
        self.execute_command("pkill -9 iperf3 2>/dev/null")
        return True
