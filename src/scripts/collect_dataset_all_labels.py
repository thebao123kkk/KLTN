"""
scripts/collect_dataset_all_labels.py
Tự động phối hợp Tiêm lỗi (Fault Injection) và Cào Telemetry (Telemetry Collector)
đảm bảo thu thập đầy đủ 7/7 loại nhãn lỗi (phi_t).

Mỗi nhãn lỗi thu thập tối thiểu N dòng (mặc định 3 dòng):
  0: NONE            (Trạng thái bình thường)
  1: SOFT_WARNING     (F03 OSPF / F07 WAN 5G degradation)
  2: TEMP_WARNING     (F10 VoIP jitter/latency spike thoáng qua)
  3: FLOW_ERROR       (F09 WAN congestion / flow overflow)
  4: PORT_FAULT       (F01 Access port down)
  5: LINK_FAULT       (F02/F04 Trunk/MPLS link down)
  6: FAUCET_RELOAD    (F12 Faucet Controller reload / reconnect)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

# Thêm đường dẫn src vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai_engine.telemetry.collector import TelemetryCollector
from fault_injection.fault_injector import create_default_injector, FaultInjector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
)
logger = logging.getLogger("collect_dataset")

# Thứ tự 7 nhãn và kịch bản tương ứng
TARGET_LABELS_MAP = [
    ("NONE", None),              # 0: Mạng bình thường, không tiêm lỗi
    ("PORT_FAULT", "F01"),       # 4: F01 - Access Link Failure
    ("LINK_FAULT", "F02"),       # 5: F02 - Distribution Failure
    ("FLOW_ERROR", "F09"),       # 3: F09 - WAN Congestion
    ("SOFT_WARNING", "F03"),     # 1: F03 - OSPF Convergence Failure
    ("TEMP_WARNING", "F10"),     # 2: F10 - VoIP Jitter/Latency spike
    ("FAUCET_RELOAD", "F12"),    # 6: F12 - Controller reload / Multi-metric
]


def collect_all_labels(
    target_per_label: int = 3,
    interval: float = 2.0,
    dry_run: bool = False,
    config_path: str = "config/telemetry_config.yaml",
    direct_mode: Optional[str] = None,
) -> Dict[str, int]:
    """
    Hàm vừa điều phối tiêm lỗi, vừa cào telemetry ghi vào dataset CSV.
    Đảm bảo đủ 7/7 nhãn lỗi chuẩn, mỗi nhãn đạt tối thiểu `target_per_label` dòng.
    
    Args:
        target_per_label: Số dòng dữ liệu cần cào cho mỗi loại nhãn (mặc định 3).
        interval: Thời gian chờ (giây) giữa các lần cào trong cùng 1 nhãn.
        dry_run: Chế độ chạy thử nghiệm (an toàn trên Windows hoặc không cần Mininet).
        config_path: Đường dẫn file cấu hình telemetry.
        
    Returns:
        Dict thống kê số dòng thu được cho từng nhãn.
    """
    logger.info("=" * 65)
    logger.info(f"BẮT ĐẦU QUY TRÌNH VỪA CHẠY VỪA CÀO ĐỦ 7 NHÃN TELEMETRY")
    logger.info(f"Mỗi nhãn mục tiêu: {target_per_label} dòng | Chu kỳ: {interval}s | Dry-run: {dry_run}")
    logger.info("=" * 65)

    if hasattr(os, "geteuid") and os.geteuid() != 0 and not dry_run:
        logger.warning("!" * 65)
        logger.warning(" [CẢNH BÁO] BẠN ĐANG CHẠY BẰNG USER THƯỜNG (KHÔNG CÓ SUDO)!")
        logger.warning(" Các kịch bản can thiệp mạng (ip link, iptables, tc) yêu cầu quyền root.")
        logger.warning(" Nếu gặp lỗi kích hoạt, vui lòng chạy lại bằng quyền sudo:")
        logger.warning(f"   sudo python3 scripts/collect_dataset_all_labels.py --target-per-label {target_per_label} --mode {direct_mode or 'auto'}")
        logger.warning("!" * 65)

    collector = TelemetryCollector(
        config_path_or_dict=config_path,
        base_dir=BASE_DIR,
        direct_mode=direct_mode,
    )
    injector = create_default_injector(dry_run=dry_run)

    collected_counts: Counter = Counter()

    for label_name, scenario_id in TARGET_LABELS_MAP:
        logger.info(f"\n>>> [NHÃN: {label_name}] - Bắt đầu điều phối...")

        if scenario_id is None:
            # 1. Trạng thái NONE: Đảm bảo không có lỗi nào active
            injector.recover_all()
            time.sleep(0.5)
        else:
            # 2. Tiêm kịch bản tương ứng
            logger.info(f"    Tiêm lỗi kịch bản [{scenario_id}] để tạo nhãn {label_name}...")
            inject_ok = injector.inject(scenario_id)
            if not inject_ok:
                logger.error(
                    f"    [LỖI] Kích hoạt kịch bản [{scenario_id}] thất bại!\n"
                    f"    => Nguyên nhân: Thiếu quyền sudo hoặc interface switch chưa sẵn sàng.\n"
                    f"    => Bỏ qua cào nhãn [{label_name}] để tránh ghi nhầm nhãn NONE vào dataset."
                )
                continue
            time.sleep(0.5)

        # 3. Cào đủ số dòng target_per_label cho nhãn này
        rows_for_this_label = 0
        attempts = 0
        max_attempts = target_per_label * 3  # Tránh lặp vô hạn

        while rows_for_this_label < target_per_label and attempts < max_attempts:
            attempts += 1
            row = collector.collect_once()
            actual_label = row.get("fault_label", "")
            collected_counts[actual_label] += 1

            if actual_label == label_name:
                rows_for_this_label += 1
                logger.info(
                    f"    [Dòng {rows_for_this_label}/{target_per_label}] Ghi nhận {actual_label} "
                    f"| Quality: {row.get('data_quality')} | Dur: {row.get('duration_seconds')}s"
                )
            else:
                logger.warning(
                    f"    Nhãn thực tế ({actual_label}) khác nhãn mong đợi ({label_name}). Đang thử lại..."
                )

            if rows_for_this_label < target_per_label:
                time.sleep(interval)

        # 4. Thu hồi lỗi sau khi đã cào xong nhãn này
        if scenario_id is not None:
            logger.info(f"    Thu hồi lỗi [{scenario_id}] về trạng thái NONE...")
            injector.recover(scenario_id)
            time.sleep(0.5)

    # 5. Phục hồi toàn bộ hệ thống
    injector.recover_all()

    # 6. Tổng kết kết quả
    print("\n" + "=" * 65)
    print(" KẾT QUẢ THU THẬP TELEMETRY THEO TỪNG NHÃN")
    print("=" * 65)
    print(f"{'Mã':<4} | {'Nhãn Fault':<16} | {'Số dòng cào':<12} | {'Trạng thái':<10}")
    print("-" * 65)

    all_satisfied = True
    for idx, (lbl, _) in enumerate(TARGET_LABELS_MAP):
        cnt = collected_counts.get(lbl, 0)
        status = "✅ ĐẠT" if cnt >= target_per_label else "❌ THIẾU"
        if cnt < target_per_label:
            all_satisfied = False
        print(f"{idx:<4} | {lbl:<16} | {cnt:<12} | {status:<10}")

    print("-" * 65)
    print(f"Tổng số dòng ghi nhận: {sum(collected_counts.values())}")
    print(f"File lưu trữ: {collector.csv_path}")
    print(f"Toàn bộ 7 nhãn thỏa mãn: {'CÓ (HOÀN THÀNH)' if all_satisfied else 'CHƯA'}")
    print("=" * 65 + "\n")

    return dict(collected_counts)


def main():
    parser = argparse.ArgumentParser(
        description="Thu thập telemetry tự động thỏa mãn đầy đủ 7 loại nhãn lỗi."
    )
    parser.add_argument(
        "--target-per-label",
        type=int,
        default=3,
        help="Số dòng dữ liệu thu thập cho mỗi loại nhãn (mặc định: 3)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Khoảng cách giữa các lần cào trong cùng 1 nhãn (giây, mặc định: 2.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chạy ở chế độ dry-run mô phỏng (dùng khi không có mạng Mininet/Linux thật)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/telemetry_config.yaml",
        help="File cấu hình telemetry",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=["auto", "direct", "prometheus"],
        help="Chế độ cào: auto (ưu tiên Exporter :9303/:9302 như test_fault_scenarios), direct, prometheus",
    )
    args = parser.parse_args()

    collect_all_labels(
        target_per_label=args.target_per_label,
        interval=args.interval,
        dry_run=args.dry_run,
        config_path=args.config,
        direct_mode=args.mode,
    )


if __name__ == "__main__":
    main()
