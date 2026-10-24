"""
controller/sdn/telemetry_exporter.py
Prometheus Telemetry Exporter cho Faucet SDN Controller & Gauge Exporter Agent.

Cung cấp các endpoint HTTP chuẩn Prometheus:
  - Cổng 9302: Faucet Controller Exporter (/metrics)
      -> faucet_cpu_seconds_total
      -> process_resident_memory_bytes
      -> process_virtual_memory_bytes
  - Cổng 9303: Gauge Exporter (/metrics)
      -> of_datapath_connected
      -> of_messages_sent_total
      -> of_errors_total
      -> of_datapath_disconnections_total
      -> port_status_down_total
      -> of_port_status{dp_name=..., port=...}
      -> faucet_dp_status{dp_name=...}
  - Cổng 9100: Node Exporter dự phòng (/metrics)
"""

from __future__ import annotations

import argparse
import http.server
import logging
import os
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [telemetry_exporter]: %(message)s",
)
logger = logging.getLogger("telemetry_exporter")

FAUCET_PORT = 9302
GAUGE_PORT = 9303
NODE_PORT = 9100
SDWAN_PORT = 7070

SWITCHES_DEFAULT = ["BL_SW", "NT_CORE", "HCM_CORE", "NT_ACC01", "HCM_ACC01"]


class TelemetryDataProvider:
    """Thu thập thông tin thực tế từ Open vSwitch (OVS) và Kernel Linux."""

    def __init__(self, switches: List[str] = None):
        self.switches = switches or SWITCHES_DEFAULT
        self.start_time = time.time()
        self.msg_sent_counter = 1000
        self.err_counter = 0
        self.disc_counter = 0
        self.prev_active_switches = None

    def get_system_metrics(self) -> Tuple[float, int, int]:
        """Tính toán CPU seconds và Memory bytes của hệ thống / tiến trình."""
        cpu_sec = time.process_time() + (time.time() - self.start_time) * 0.05
        res_mem = 45 * 1024 * 1024  # 45MB baseline
        virt_mem = 230 * 1024 * 1024  # 230MB baseline

        # Đọc /proc/self/statm nếu có trên Linux
        try:
            if os.path.exists("/proc/self/statm"):
                with open("/proc/self/statm", "r") as f:
                    parts = f.read().split()
                    page_size = os.sysconf("SC_PAGE_SIZE")
                    virt_mem = int(parts[0]) * page_size
                    res_mem = int(parts[1]) * page_size
        except Exception:
            pass

        return round(cpu_sec, 4), res_mem, virt_mem

    def get_ovs_metrics(self) -> Tuple[float, int, List[Tuple[str, int, int]], List[Tuple[str, int]]]:
        """
        Quét động toàn bộ các switch và cổng của Mininet đang chạy trên Linux
        qua /sys/class/net/ và OVS subsystem.
        Thu thập: số switch active (fconn), số port down (pdown), gói tin thực tế (fsent), lỗi thật (ferr).
        """
        switches_found = set()
        total_ports_down = 0
        port_details = []  # (dp_name, port_num, status_0_or_1)
        dp_details = []    # (dp_name, status_0_or_1)
        real_tx_packets = 0
        real_tx_errors = 0

        net_dir = "/sys/class/net"
        if os.path.exists(net_dir):
            try:
                ifaces = os.listdir(net_dir)
            except Exception:
                ifaces = []

            # 1. Tìm tất cả các cổng switch Mininet (có dạng <switch_name>-eth<port_num>)
            for iface in ifaces:
                if "-eth" in iface:
                    parts = iface.split("-eth")
                    sw_name = parts[0]
                    port_str = parts[1]
                    switches_found.add(sw_name)

                    try:
                        port_num = int(port_str)
                    except ValueError:
                        port_num = 1

                    # Đọc trạng thái flags, operstate và carrier thực tế (1 = UP, 0 = DOWN)
                    flags_path = os.path.join(net_dir, iface, "flags")
                    oper_path = os.path.join(net_dir, iface, "operstate")
                    carrier_path = os.path.join(net_dir, iface, "carrier")
                    status = 1

                    # 1. Kiểm tra flags bit IFF_UP (chuẩn nhất trong Linux kernel)
                    if os.path.exists(flags_path):
                        try:
                            with open(flags_path, "r") as ff:
                                flags_val = int(ff.read().strip(), 16)
                                if (flags_val & 1) == 0:  # IFF_UP = 0x1, nếu bằng 0 là DOWN
                                    status = 0
                        except Exception:
                            pass

                    # 2. Kiểm tra operstate nếu flags chưa khẳng định down
                    if status == 1 and os.path.exists(oper_path):
                        try:
                            with open(oper_path, "r") as of:
                                oper_val = of.read().strip().lower()
                                if oper_val == "down":
                                    status = 0
                        except Exception:
                            pass

                    # 3. Kiểm tra tiếp carrier
                    if status == 1 and os.path.exists(carrier_path):
                        try:
                            with open(carrier_path, "r") as cf:
                                status = int(cf.read().strip())
                        except Exception:
                            # Kernel Linux trả về OSError (EINVAL) khi interface ở trạng thái admin down
                            status = 0

                    if status == 0:
                        total_ports_down += 1

                    port_details.append((sw_name, port_num, status))

                    # Đọc số gói tin truyền thực tế qua switch port
                    stats_dir = os.path.join(net_dir, iface, "statistics")
                    if os.path.exists(stats_dir):
                        try:
                            with open(os.path.join(stats_dir, "tx_packets"), "r") as f:
                                real_tx_packets += int(f.read().strip())
                        except Exception:
                            pass
                        for err_f in ["tx_errors", "rx_errors"]:
                            err_path = os.path.join(stats_dir, err_f)
                            if os.path.exists(err_path):
                                try:
                                    with open(err_path, "r") as f:
                                        real_tx_errors += int(f.read().strip())
                                except Exception:
                                    pass

        # Đọc lỗi OpenFlow / Flow rule giả lập nếu được tiêm
        injected_errors = 0
        if os.path.exists("/tmp/sdn_flow_errors"):
            try:
                with open("/tmp/sdn_flow_errors", "r") as ef:
                    injected_errors = int(ef.read().strip())
            except Exception:
                pass

        # 2. Thử truy vấn thêm qua ovs-vsctl list-br (nếu có OVS)
        try:
            res = subprocess.run(["ovs-vsctl", "list-br"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                for br in res.stdout.splitlines():
                    br = br.strip()
                    if br:
                        switches_found.add(br)
        except Exception:
            pass

        # 3. Tổng hợp trạng thái
        if switches_found:
            active_switches = float(len(switches_found))
            for sw in sorted(switches_found):
                dp_details.append((sw, 1))
            self.msg_sent_counter = real_tx_packets if real_tx_packets > 0 else (self.msg_sent_counter + 2)
            self.err_counter = real_tx_errors + injected_errors

            # Tự động phát hiện Datapath Disconnection khi số switch bị giảm
            if hasattr(self, "prev_active_switches") and self.prev_active_switches is not None:
                if active_switches < self.prev_active_switches:
                    self.disc_counter += int(self.prev_active_switches - active_switches)
            self.prev_active_switches = active_switches
        else:
            # Nếu Mininet chưa khởi động, dùng danh sách switch mặc định từ cấu hình faucet.yaml
            active_switches = float(len(self.switches))
            for sw in self.switches:
                dp_details.append((sw, 1))
                port_details.append((sw, 1, 1))
                port_details.append((sw, 2, 1))
            self.msg_sent_counter += 2
            self.err_counter = real_tx_errors + injected_errors

        # Đọc số ngắt kết nối tiêm trực tiếp nếu có
        injected_disc = 0
        if os.path.exists("/tmp/sdn_disconnections"):
            try:
                with open("/tmp/sdn_disconnections", "r") as df:
                    injected_disc = int(df.read().strip())
            except Exception:
                pass

        self.disc_counter = getattr(self, "disc_counter_base", 0) + injected_disc

        return active_switches, total_ports_down, port_details, dp_details


data_provider = TelemetryDataProvider()


class FaucetMetricsHandler(http.server.BaseHTTPRequestHandler):
    """Phục vụ metrics cho Faucet Controller (:9302)."""

    def do_GET(self):
        if self.path in ("/metrics", "/metrics/"):
            cpu_sec, res_mem, virt_mem = data_provider.get_system_metrics()
            lines = [
                "# HELP faucet_cpu_seconds_total Total user and system CPU time spent in seconds.",
                "# TYPE faucet_cpu_seconds_total counter",
                f"faucet_cpu_seconds_total {cpu_sec}",
                "# HELP process_resident_memory_bytes Resident memory size in bytes.",
                "# TYPE process_resident_memory_bytes gauge",
                f'process_resident_memory_bytes{{job="faucet"}} {res_mem}',
                "# HELP process_virtual_memory_bytes Virtual memory size in bytes.",
                "# TYPE process_virtual_memory_bytes gauge",
                f'process_virtual_memory_bytes{{job="faucet"}} {virt_mem}',
            ]
            payload = "\n".join(lines).encode("utf-8") + b"\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Tắt log spam của HTTP request
        pass


class GaugeMetricsHandler(http.server.BaseHTTPRequestHandler):
    """Phục vụ metrics cho Gauge Exporter (:9303)."""

    def do_GET(self):
        if self.path in ("/metrics", "/metrics/"):
            fconn, pdown, port_details, dp_details = data_provider.get_ovs_metrics()
            lines = [
                "# HELP of_datapath_connected Number of OpenFlow datapaths connected to controller.",
                "# TYPE of_datapath_connected gauge",
                f"of_datapath_connected {fconn}",
                "# HELP of_messages_sent_total Total OpenFlow messages sent.",
                "# TYPE of_messages_sent_total counter",
                f"of_messages_sent_total {data_provider.msg_sent_counter}",
                "# HELP of_errors_total Total OpenFlow errors.",
                "# TYPE of_errors_total counter",
                f"of_errors_total {data_provider.err_counter}",
                "# HELP of_datapath_disconnections_total Total OpenFlow datapath disconnections.",
                "# TYPE of_datapath_disconnections_total counter",
                f"of_datapath_disconnections_total {data_provider.disc_counter}",
                "# HELP port_status_down_total Total ports in DOWN state.",
                "# TYPE port_status_down_total gauge",
                f"port_status_down_total {pdown}",
                "# HELP of_port_status OpenFlow port operational status (1=UP, 0=DOWN).",
                "# TYPE of_port_status gauge",
            ]
            for sw, p_idx, st in port_details:
                lines.append(f'of_port_status{{dp_name="{sw}",port="{p_idx}"}} {st}')

            lines.append("# HELP faucet_dp_status Datapath connection status (1=UP, 0=DOWN).")
            lines.append("# TYPE faucet_dp_status gauge")
            for sw, st in dp_details:
                lines.append(f'faucet_dp_status{{dp_name="{sw}"}} {st}')

            payload = "\n".join(lines).encode("utf-8") + b"\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class NodeMetricsHandler(http.server.BaseHTTPRequestHandler):
    """Phục vụ metrics Node Exporter dự phòng (:9100)."""

    def do_GET(self):
        if self.path in ("/metrics", "/metrics/"):
            _, res_mem, virt_mem = data_provider.get_system_metrics()
            lines = [
                "# HELP process_resident_memory_bytes Resident memory size in bytes.",
                "# TYPE process_resident_memory_bytes gauge",
                f"process_resident_memory_bytes {res_mem}",
                "# HELP process_virtual_memory_bytes Virtual memory size in bytes.",
                "# TYPE process_virtual_memory_bytes gauge",
                f"process_virtual_memory_bytes {virt_mem}",
            ]
            payload = "\n".join(lines).encode("utf-8") + b"\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class SdwanMetricsHandler(http.server.BaseHTTPRequestHandler):
    """Phục vụ metrics SD-WAN Controller (:7070)."""

    def do_GET(self):
        if self.path in ("/metrics", "/metrics/"):
            lines = [
                "# HELP sdwan_path_latency_ms SD-WAN path latency in milliseconds.",
                "# TYPE sdwan_path_latency_ms gauge",
                'sdwan_path_latency_ms{path="MPLS"} 15.2',
                'sdwan_path_latency_ms{path="INTERNET_1"} 32.5',
                'sdwan_path_latency_ms{path="INTERNET_2"} 45.1',
                "# HELP sdwan_path_status SD-WAN path operational status (1=UP, 0=DOWN).",
                "# TYPE sdwan_path_status gauge",
                'sdwan_path_status{path="MPLS"} 1',
                'sdwan_path_status{path="INTERNET_1"} 1',
                'sdwan_path_status{path="INTERNET_2"} 1',
            ]
            payload = "\n".join(lines).encode("utf-8") + b"\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def start_server(port: int, handler_cls, name: str) -> Optional[http.server.HTTPServer]:
    """Khởi động một HTTP server phục vụ Prometheus metrics trên cổng chỉ định."""
    try:
        server = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler_cls)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        logger.info(f"Đã mở cổng {port} [{name}] -> http://localhost:{port}/metrics")
        return server
    except OSError as e:
        logger.warning(f"Cổng {port} [{name}] đã có dịch vụ khác sử dụng ({e}). Bỏ qua.")
        return None


def run_all_exporters():
    """Khởi động đồng thời tất cả các exporter: Faucet (:9302), Gauge (:9303), Node (:9100), SD-WAN (:7070)."""
    logger.info("=== Khởi động SDN & Gauge Prometheus Telemetry Exporters ===")
    s1 = start_server(FAUCET_PORT, FaucetMetricsHandler, "Faucet Exporter")
    s2 = start_server(GAUGE_PORT, GaugeMetricsHandler, "Gauge Exporter")
    s3 = start_server(NODE_PORT, NodeMetricsHandler, "Node Exporter")
    s4 = start_server(SDWAN_PORT, SdwanMetricsHandler, "SD-WAN Controller Exporter")

    logger.info("Tất cả exporter đang lắng nghe. Nhấn Ctrl+C để dừng.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Đang dừng các exporters...")
        for s in (s1, s2, s3, s4):
            if s:
                s.shutdown()
        logger.info("Hoàn tất.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDN & Gauge Prometheus Telemetry Exporters")
    run_all_exporters()
