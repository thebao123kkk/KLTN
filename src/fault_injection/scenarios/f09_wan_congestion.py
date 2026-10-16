"""
fault_injection/scenarios/f09_wan_congestion.py
Kịch bản F09: Tắc nghẽn đường truyền WAN do bão lưu lượng (WAN Congestion / UDP Flood).

Mô tả:
  - Sinh luồng lưu lượng UDP Flood dung lượng lớn (iperf3 -u -b 100M) giữa các Site
    hoặc siết băng thông hàng đợi (tc tbf/htb) để gây nghẽn nghiêm trọng.
  - Phù hợp với loại lỗi FLOW_ERROR / Congestion trong Model_Research_and_Implementation_Plan.md.
  - Tác động: Gây tràn bộ đệm hàng đợi (Bufferbloat), tăng độ trễ RTT, làm rơi rớt gói tin
    của các ứng dụng dùng chung đường truyền WAN.
"""

from typing import Any, Optional
from fault_injection.fault_injector import BaseFaultScenario


class WANCongestionScenario(BaseFaultScenario):
    scenario_id = "F09"
    name = "WAN Congestion"
    category = "FLOW_ERROR"
    description = "Phát luồng UDP flood dung lượng lớn (iperf3 100Mbps) hoặc bóp băng thông WAN xuống 1Mbps gây tràn hàng đợi."
    default_duration = 30.0
    target_devices = ["BL_GW", "HCM_DIST01", "DC_WEB01"]
    target_interfaces = ["blgw_inet_g", "hcmd_inet_g"]

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False,
                 target_intf: str = "blgw_inet_g", bandwidth_limit: str = "1mbit"):
        super().__init__(duration=duration, dry_run=dry_run)
        self.target_intf = target_intf
        self.bandwidth_limit = bandwidth_limit
        self.iperf_pid: Optional[int] = None

    def inject(self, net: Any = None) -> bool:
        # Cách 1: Thắt chặt bandwidth bằng tc tbf trên interface WAN để tạo nghẽn lập tức
        self.recover(net)
        cmd_tc = f"tc qdisc add dev {self.target_intf} root tbf rate {self.bandwidth_limit} burst 32kbit latency 400ms"
        node = net.get("BL_GW") if net and hasattr(net, "get") else None
        self.execute_command(cmd_tc, node=node)

        # Cách 2: Phát luồng UDP iperf3 nếu có host nguồn và đích trong Mininet
        if net and hasattr(net, "get"):
            src_host = net.get("BL_USER01")
            dst_host = net.get("DC_WEB01")
            if src_host and dst_host:
                dst_host.cmd("iperf3 -s -D 2>/dev/null")
                src_host.cmd(f"iperf3 -c 10.100.10.11 -u -b 100M -t {int(self.duration)} >/dev/null 2>&1 &")

        return True

    def recover(self, net: Any = None) -> bool:
        cmd = f"tc qdisc del dev {self.target_intf} root 2>/dev/null"
        node = net.get("BL_GW") if net and hasattr(net, "get") else None
        self.execute_command(cmd, node=node)

        # Diệt các tiến trình iperf3 nếu còn chạy
        self.execute_command("pkill -9 iperf3 2>/dev/null", node=node)
        return True
