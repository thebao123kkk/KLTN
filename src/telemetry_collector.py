"""
telemetry_collector.py
Kịch bản thực thi chính thu thập Telemetry và tạo tập dữ liệu CSV.

Sử dụng:
    python telemetry_collector.py
    python telemetry_collector.py --cycles 6 --interval 5
    python telemetry_collector.py --config config/telemetry_config.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import logging

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Cấu hình logging hiển thị mức INFO ra terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
)

# Đảm bảo import được module telemetry khi chạy trực tiếp từ thư mục src
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from ai_engine.telemetry.collector import TelemetryCollector


def main():
    parser = argparse.ArgumentParser(
        description="SDN/SD-WAN Telemetry Scraper & 8D State-Vector Dataset Collector"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/telemetry_config.yaml",
        help="Đường dẫn file cấu hình YAML (mặc định: config/telemetry_config.yaml)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Số chu kỳ cào dữ liệu trước khi tự dừng (mặc định: chạy liên tục)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Ghi đè khoảng thời gian giữa các chu kỳ cào (giây)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=["auto", "direct", "prometheus"],
        help="Chế độ thu thập: auto (ưu tiên Exporter :9303/:9302 như test_fault_scenarios), direct, hoặc prometheus",
    )

    args = parser.parse_args()

    collector = TelemetryCollector(
        config_path_or_dict=args.config,
        base_dir=current_dir,
        direct_mode=args.mode,
    )
    collector.run(max_cycles=args.cycles, interval=args.interval)


if __name__ == "__main__":
    main()
