# """
# controller/sdwan/probes/wan_prober.py
# ICMP + iperf3 probe để đo đặc tính của mỗi WAN path.

# Probe targets (DC_SP_GW trên mỗi path):
#   MPLS:  172.16.10.4
#   FIVEG: 172.16.40.4
#   INET:  172.16.20.4
#   VPN:   172.16.50.4
#   LTE:   172.16.30.4
# """

# import subprocess
# import time
# import re
# from typing import Optional

# import sys, os
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# from controller.sdwan.models.path_state import PathState, PathStatus


# # DC_SP_GW IP trên mỗi WAN path (octet .4 = DC site)
# DEFAULT_PROBE_TARGETS = {
#     'MPLS':  '172.16.10.4',
#     'FIVEG': '172.16.40.4',
#     'INET':  '172.16.20.4',
#     'VPN':   '172.16.50.4',
#     'LTE':   '172.16.30.4',
# }


# class WanProber:
#     """
#     Probe WAN paths bằng ICMP ping.
#     Tùy chọn: iperf3 để đo bandwidth thực.
#     """

#     def __init__(self,
#                  probe_targets: dict = None,
#                  probe_count: int = 5,
#                  timeout_s: int = 2,
#                  enable_iperf: bool = False):
#         """
#         probe_targets: {path_name: target_ip}. Mặc định = DEFAULT_PROBE_TARGETS.
#         probe_count:   Số ICMP packet mỗi lần probe.
#         timeout_s:     Timeout mỗi packet (giây).
#         enable_iperf:  Nếu True, đo bandwidth bằng iperf3 (chậm hơn).
#         """
#         self.targets     = probe_targets or DEFAULT_PROBE_TARGETS
#         self.count       = probe_count
#         self.timeout     = timeout_s
#         self.enable_iperf = enable_iperf

#     def probe_path(self, path_name: str) -> PathState:
#         """
#         Probe 1 WAN path, trả về PathState với metrics cập nhật.
#         """
#         target_ip = self.targets.get(path_name)
#         if not target_ip:
#             state = PathState(name=path_name, status=PathStatus.UNKNOWN)
#             return state

#         state = PathState(name=path_name)
#         state.last_probe  = time.time()
#         state.probe_count += 1

#         # ICMP probe
#         latency, jitter, loss = self._ping_probe(target_ip)

#         if loss >= 100.0:
#             state.status   = PathStatus.DOWN
#             state.loss_pct = 100.0
#             state.fail_count += 1
#             return state

#         state.latency_ms = latency
#         state.jitter_ms  = jitter
#         state.loss_pct   = loss
#         state.fail_count = 0

#         # Đánh dấu DEGRADED nếu loss > 5%
#         if loss > 5.0:
#             state.status = PathStatus.DEGRADED
#         else:
#             state.status = PathStatus.UP

#         #------
#         # # Optional: iperf3 bandwidth measurement
#         # if self.enable_iperf:
#         #     bw = self._iperf_probe(target_ip)
#         #     state.bandwidth_mbps = bw
#         #------

#         return state

#     def probe_all(self) -> dict:
#         """Probe tất cả paths. Trả về {path_name: PathState}."""
#         results = {}
#         for path_name in self.targets:
#             results[path_name] = self.probe_path(path_name)
#         return results

#     def _ping_probe(self, target_ip: str) -> tuple:
#         """
#         Chạy ping, parse output.
#         Trả về (latency_ms, jitter_ms, loss_pct).
#         Nếu unreachable: (-1, -1, 100.0).
#         """
#         try:
#             result = subprocess.run(
#                 ['ping', '-c', str(self.count), '-W', str(self.timeout), target_ip],
#                 capture_output=True,
#                 text=True,
#                 timeout=self.count * (self.timeout + 1) + 2
#             )

#             output = result.stdout + result.stderr

#             # Parse loss
#             loss_match = re.search(r'(\d+(?:\.\d+)?)% packet loss', output)
#             loss_pct = float(loss_match.group(1)) if loss_match else 100.0

#             if loss_pct >= 100.0 or result.returncode != 0:
#                 return -1.0, -1.0, 100.0

#             # Parse RTT: "rtt min/avg/max/mdev = 19.2/20.1/21.3/0.8 ms"
#             rtt_match = re.search(
#                 r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/([\d.]+) ms',
#                 output
#             )
#             if rtt_match:
#                 latency_ms = float(rtt_match.group(1))   # avg
#                 jitter_ms  = float(rtt_match.group(2))   # mdev (approximation)
#             else:
#                 latency_ms = -1.0
#                 jitter_ms  = -1.0

#             return latency_ms, jitter_ms, loss_pct

#         except subprocess.TimeoutExpired:
#             return -1.0, -1.0, 100.0
#         except Exception as e:
#             return -1.0, -1.0, 100.0

#     def _iperf_probe(self, target_ip: str, duration: int = 3) -> float:
#         """
#         Đo bandwidth bằng iperf3 UDP.
#         Trả về bandwidth (Mbps). -1 nếu fail.
#         Yêu cầu: iperf3 server chạy trên target_ip port 5201.
#         """
#         try:
#             result = subprocess.run(
#                 ['iperf3', '-c', target_ip, '-u', '-b', '200M',
#                  '-t', str(duration), '-J'],
#                 capture_output=True,
#                 text=True,
#                 timeout=duration + 5
#             )
#             import json
#             data = json.loads(result.stdout)
#             bps = data['end']['sum']['bits_per_second']
#             return bps / 1_000_000  # Convert to Mbps
#         except Exception:
#             return -1.0

#     def check_path_up(self, path_name: str, fast: bool = False) -> bool:
#         """
#         Quick check: path có UP không?
#         fast=True: chỉ ping 2 packet (nhanh hơn nhưng ít chính xác hơn).
#         """
#         count = 2 if fast else self.count
#         target_ip = self.targets.get(path_name)
#         if not target_ip:
#             return False

#         try:
#             result = subprocess.run(
#                 ['ping', '-c', str(count), '-W', '1', target_ip],
#                 capture_output=True,
#                 timeout=count * 2 + 1
#             )
#             return result.returncode == 0
#         except Exception:
#             return False


"""
controller/sdwan/probes/wan_prober.py
ICMP + iperf3 probe để đo đặc tính của mỗi WAN path.

Probe targets (DC_SP_GW trên mỗi path):
  MPLS:  172.16.10.4
  FIVEG: 172.16.40.4
  INET:  172.16.20.4
  VPN:   172.16.50.4
  LTE:   172.16.30.4
"""

import subprocess
import time
import re
from typing import Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from controller.sdwan.models.path_state import PathState, PathStatus


# DC_SP_GW IP trên mỗi WAN path (octet .4 = DC site)
# Chỉ giữ MPLS và LTE; FIVEG/INET/VPN tạm thời disabled
DEFAULT_PROBE_TARGETS = {
    'MPLS':  '172.16.10.4',
    # 'FIVEG': '172.16.40.4',   # disabled
    # 'INET':  '172.16.20.4',   # disabled
    # 'VPN':   '172.16.50.4',   # disabled
    'LTE':   '172.16.30.4',
}


class WanProber:
    """
    Probe WAN paths bằng ICMP ping.
    Tùy chọn: iperf3 để đo bandwidth thực.
    """

    def __init__(self,
                 probe_targets: dict = None,
                 probe_count: int = 5,
                 timeout_s: int = 2):
                 # enable_iperf: bool = False):  # iperf giả lập tải — tạm thời disabled
        """
        probe_targets: {path_name: target_ip}. Mặc định = DEFAULT_PROBE_TARGETS.
        probe_count:   Số ICMP packet mỗi lần probe.
        timeout_s:     Timeout mỗi packet (giây).
        # enable_iperf:  Nếu True, đo bandwidth bằng iperf3 (chậm hơn). [disabled]
        """
        self.targets      = probe_targets or DEFAULT_PROBE_TARGETS
        self.count        = probe_count
        self.timeout      = timeout_s
        # self.enable_iperf = enable_iperf

    def probe_path(self, path_name: str) -> PathState:
        """
        Probe 1 WAN path, trả về PathState với metrics cập nhật.
        """
        target_ip = self.targets.get(path_name)
        if not target_ip:
            state = PathState(name=path_name, status=PathStatus.UNKNOWN)
            return state

        state = PathState(name=path_name)
        state.last_probe  = time.time()
        state.probe_count += 1

        # ICMP probe
        latency, jitter, loss = self._ping_probe(target_ip)

        if loss >= 100.0:
            state.status   = PathStatus.DOWN
            state.loss_pct = 100.0
            state.fail_count += 1
            return state

        state.latency_ms = latency
        state.jitter_ms  = jitter
        state.loss_pct   = loss
        state.fail_count = 0

        # Đánh dấu DEGRADED nếu loss > 5%
        if loss > 5.0:
            state.status = PathStatus.DEGRADED
        else:
            state.status = PathStatus.UP

        # Optional: iperf3 bandwidth measurement — tạm thời disabled
        # if self.enable_iperf:
        #     bw = self._iperf_probe(target_ip)
        #     state.bandwidth_mbps = bw

        return state

    def probe_all(self) -> dict:
        """Probe tất cả paths. Trả về {path_name: PathState}."""
        results = {}
        for path_name in self.targets:
            results[path_name] = self.probe_path(path_name)
        return results

    def _ping_probe(self, target_ip: str) -> tuple:
        """
        Chạy ping, parse output.
        Trả về (latency_ms, jitter_ms, loss_pct).
        Nếu unreachable: (-1, -1, 100.0).
        """
        try:
            result = subprocess.run(
                ['ping', '-c', str(self.count), '-W', str(self.timeout), target_ip],
                capture_output=True,
                text=True,
                timeout=self.count * (self.timeout + 1) + 2
            )

            output = result.stdout + result.stderr

            # Parse loss
            loss_match = re.search(r'(\d+(?:\.\d+)?)% packet loss', output)
            loss_pct = float(loss_match.group(1)) if loss_match else 100.0

            if loss_pct >= 100.0 or result.returncode != 0:
                return -1.0, -1.0, 100.0

            # Parse RTT: "rtt min/avg/max/mdev = 19.2/20.1/21.3/0.8 ms"
            rtt_match = re.search(
                r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/([\d.]+) ms',
                output
            )
            if rtt_match:
                latency_ms = float(rtt_match.group(1))   # avg
                jitter_ms  = float(rtt_match.group(2))   # mdev (approximation)
            else:
                latency_ms = -1.0
                jitter_ms  = -1.0

            return latency_ms, jitter_ms, loss_pct

        except subprocess.TimeoutExpired:
            return -1.0, -1.0, 100.0
        except Exception as e:
            return -1.0, -1.0, 100.0

    # iperf3 bandwidth probe — tạm thời disabled (giả lập tăng tải trên WAN)
    # def _iperf_probe(self, target_ip: str, duration: int = 3) -> float:
    #     """
    #     Đo bandwidth bằng iperf3 UDP.
    #     Trả về bandwidth (Mbps). -1 nếu fail.
    #     Yêu cầu: iperf3 server chạy trên target_ip port 5201.
    #     """
    #     try:
    #         result = subprocess.run(
    #             ['iperf3', '-c', target_ip, '-u', '-b', '200M',
    #              '-t', str(duration), '-J'],
    #             capture_output=True,
    #             text=True,
    #             timeout=duration + 5
    #         )
    #         import json
    #         data = json.loads(result.stdout)
    #         bps = data['end']['sum']['bits_per_second']
    #         return bps / 1_000_000  # Convert to Mbps
    #     except Exception:
    #         return -1.0

    def check_path_up(self, path_name: str, fast: bool = False) -> bool:
        """
        Quick check: path có UP không?
        fast=True: chỉ ping 2 packet (nhanh hơn nhưng ít chính xác hơn).
        """
        count = 2 if fast else self.count
        target_ip = self.targets.get(path_name)
        if not target_ip:
            return False

        try:
            result = subprocess.run(
                ['ping', '-c', str(count), '-W', '1', target_ip],
                capture_output=True,
                timeout=count * 2 + 1
            )
            return result.returncode == 0
        except Exception:
            return False
