"""
fault_injection/fault_injector.py
API chung & Framework điều phối tiêm lỗi có kiểm soát cho mạng SDN/SD-WAN.

Tham chiếu:
  - Model_Research_and_Implementation_Plan.md (Mục 4 - Module 1, Mục 9 - Kịch bản tạo lỗi & Log)
  - fault_injection/__init__.py (12 kịch bản F01–F12)

Cung cấp:
  - BaseFaultScenario: Lớp cơ sở cho toàn bộ 12 kịch bản lỗi.
  - FaultInjector: Bộ quản trị vòng đời tiêm lỗi, ghi log ISO-8601, tích hợp Mininet CLI/API & Mock mode.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Type, Union

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("fault_injector")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
)


@dataclass
class FaultEventLog:
    """Cấu trúc ghi nhật ký sự cố có mốc thời gian chuẩn ISO-8601."""
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    scenario_id: str = ""
    scenario_name: str = ""
    category: str = ""
    event_type: str = "INJECT"   # INJECT | RECOVER | FAILED
    target_devices: List[str] = field(default_factory=list)
    target_interfaces: List[str] = field(default_factory=list)
    duration_sec: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    status: str = "SUCCESS"      # SUCCESS | FAILED | DRY_RUN

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class BaseFaultScenario(ABC):
    """
    Lớp cơ sở trừu tượng cho tất cả các kịch bản tiêm lỗi (F01–F12).
    """

    scenario_id: str = "F00"
    name: str = "Base Scenario"
    category: str = "GENERAL"  # LINK_FAULT, PORT_FAULT, FLOW_ERROR, WAN_DEGRADATION, etc.
    description: str = "Mô tả kịch bản tiêm lỗi"
    default_duration: float = 30.0
    target_devices: List[str] = []
    target_interfaces: List[str] = []

    def __init__(self, duration: Optional[float] = None, dry_run: bool = False):
        self.duration = duration if duration is not None else self.default_duration
        self.dry_run = dry_run
        self.is_active = False
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def execute_command(self, cmd: Union[str, List[str]], node: Any = None) -> tuple[int, str, str]:
        """
        Thực thi lệnh shell hoặc lệnh trên Mininet node.
        Hỗ trợ dry_run an toàn khi chạy trên máy test không có môi trường Linux Mininet.
        """
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        if self.dry_run:
            logger.info(f"[DRY-RUN] Executing on node={node}: {cmd_str}")
            return 0, "[DRY-RUN OK]", ""

        if node is not None and hasattr(node, "cmd"):
            logger.debug(f"[NODE {node.name}] cmd: {cmd_str}")
            out = node.cmd(cmd_str)
            return 0, out, ""
        else:
            logger.debug(f"[HOST SHELL] cmd: {cmd_str}")
            res = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
            return res.returncode, res.stdout, res.stderr

    @abstractmethod
    def inject(self, net: Any = None) -> bool:
        """
        Thực hiện gây lỗi trên mạng Mininet hoặc hệ thống.
        Trả về True nếu tiêm lỗi thành công.
        """
        pass

    @abstractmethod
    def recover(self, net: Any = None) -> bool:
        """
        Thực hiện khôi phục mạng về trạng thái bình thường ban đầu.
        Trả về True nếu khôi phục thành công.
        """
        pass

    def run(self, net: Any = None, duration: Optional[float] = None) -> bool:
        """
        Chạy toàn bộ vòng đời tiêm lỗi:
        Inject -> Duy trì trong duration giây -> Tự động Recover.
        """
        dur = duration if duration is not None else self.duration
        logger.info(f"=== Bắt đầu kịch bản [{self.scenario_id}] {self.name} (Thời lượng: {dur}s) ===")
        inject_ok = self.inject(net)
        if not inject_ok:
            logger.error(f"[{self.scenario_id}] Tiêm lỗi thất bại!")
            return False

        self.is_active = True
        self.start_time = time.time()
        try:
            logger.info(f"[{self.scenario_id}] Đang duy trì trạng thái lỗi trong {dur}s...")
            time.sleep(dur)
        except KeyboardInterrupt:
            logger.warning(f"[{self.scenario_id}] Bị ngắt bởi người dùng, đang tiến hành phục hồi khẩn cấp...")
        finally:
            logger.info(f"[{self.scenario_id}] Đang khôi phục hệ thống...")
            recover_ok = self.recover(net)
            self.is_active = False
            self.end_time = time.time()
            if recover_ok:
                logger.info(f"=== Hoàn tất kịch bản [{self.scenario_id}] {self.name} thành công ===")
            else:
                logger.error(f"[{self.scenario_id}] Khôi phục lỗi thất bại! Cần can thiệp thủ công.")
        return recover_ok


class FaultInjector:
    """
    Bộ điều phối tập trung các kịch bản tiêm lỗi.
    Ghi log ra file fault_log.json / fault_log.txt để Telemetry Scraper và AI Engine đọc.
    """

    def __init__(
        self,
        net: Any = None,
        log_file: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.net = net
        self.dry_run = dry_run

        if log_file is None:
            # Lưu mặc định tại thư mục gốc /data/logs hoặc cùng cấp fault_injection/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "data", "logs")
            os.makedirs(log_dir, exist_ok=True)
            self.log_file = os.path.join(log_dir, "fault_log.json")
            self.txt_log_file = os.path.join(log_dir, "fault_log.txt")
        else:
            self.log_file = log_file
            self.txt_log_file = log_file.replace(".json", ".txt")

        self.registered_scenarios: Dict[str, Type[BaseFaultScenario]] = {}
        self.active_scenarios: Dict[str, BaseFaultScenario] = {}

    def register(self, scenario_cls: Type[BaseFaultScenario]):
        """Đăng ký một lớp kịch bản lỗi vào bộ điều phối."""
        self.registered_scenarios[scenario_cls.scenario_id.upper()] = scenario_cls
        logger.debug(f"Đã đăng ký kịch bản: {scenario_cls.scenario_id} - {scenario_cls.name}")

    def log_event(self, event: FaultEventLog):
        """Ghi nhận log sự cố ra file JSON và text."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")

            with open(self.txt_log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"[{event.timestamp}] [{event.event_type}] [{event.scenario_id}] "
                    f"{event.scenario_name} - Targets: {event.target_devices} - Status: {event.status}\n"
                )
        except Exception as e:
            logger.error(f"Không thể ghi log sự cố: {e}")

    def inject(self, scenario_id: str, duration: Optional[float] = None) -> bool:
        """Kích hoạt tiêm lỗi theo mã kịch bản (F01..F12)."""
        sid = scenario_id.upper()
        if sid not in self.registered_scenarios:
            logger.error(f"Kịch bản '{sid}' chưa được đăng ký trong hệ thống!")
            return False

        scenario_cls = self.registered_scenarios[sid]
        instance = scenario_cls(duration=duration, dry_run=self.dry_run)

        ok = instance.inject(self.net)
        event = FaultEventLog(
            scenario_id=instance.scenario_id,
            scenario_name=instance.name,
            category=instance.category,
            event_type="INJECT",
            target_devices=instance.target_devices,
            target_interfaces=instance.target_interfaces,
            duration_sec=instance.duration,
            status="SUCCESS" if ok else "FAILED",
        )
        self.log_event(event)

        if ok:
            self.active_scenarios[sid] = instance
        return ok

    def recover(self, scenario_id: str) -> bool:
        """Khôi phục lỗi cho một kịch bản đang active hoặc theo ID."""
        sid = scenario_id.upper()
        instance = self.active_scenarios.get(sid)
        if instance is None:
            if sid in self.registered_scenarios:
                instance = self.registered_scenarios[sid](dry_run=self.dry_run)
            else:
                logger.error(f"Kịch bản '{sid}' không tồn tại!")
                return False

        ok = instance.recover(self.net)
        event = FaultEventLog(
            scenario_id=instance.scenario_id,
            scenario_name=instance.name,
            category=instance.category,
            event_type="RECOVER",
            target_devices=instance.target_devices,
            target_interfaces=instance.target_interfaces,
            duration_sec=instance.duration,
            status="SUCCESS" if ok else "FAILED",
        )
        self.log_event(event)

        if sid in self.active_scenarios:
            del self.active_scenarios[sid]
        return ok

    def run_scenario(self, scenario_id: str, duration: Optional[float] = None) -> bool:
        """Chạy trọn gói kịch bản (tiêm lỗi -> giữ thời gian -> phục hồi)."""
        sid = scenario_id.upper()
        if sid not in self.registered_scenarios:
            logger.error(f"Kịch bản '{sid}' không tồn tại!")
            return False

        scenario_cls = self.registered_scenarios[sid]
        instance = scenario_cls(duration=duration, dry_run=self.dry_run)

        self.log_event(FaultEventLog(
            scenario_id=instance.scenario_id,
            scenario_name=instance.name,
            category=instance.category,
            event_type="INJECT",
            target_devices=instance.target_devices,
            target_interfaces=instance.target_interfaces,
            duration_sec=instance.duration,
            status="START",
        ))

        success = instance.run(self.net, duration=duration)

        self.log_event(FaultEventLog(
            scenario_id=instance.scenario_id,
            scenario_name=instance.name,
            category=instance.category,
            event_type="RECOVER",
            target_devices=instance.target_devices,
            target_interfaces=instance.target_interfaces,
            duration_sec=instance.duration,
            status="SUCCESS" if success else "FAILED",
        ))
        return success

    def recover_all(self):
        """Khôi phục tất cả các kịch bản đang active."""
        for sid in list(self.active_scenarios.keys()):
            self.recover(sid)


def create_default_injector(net: Any = None, dry_run: bool = False) -> FaultInjector:
    """Tạo bộ injector mặc định với đủ 12 kịch bản đã đăng ký sẵn."""
    from fault_injection.scenarios import ALL_SCENARIOS

    injector = FaultInjector(net=net, dry_run=dry_run)
    for scenario_cls in ALL_SCENARIOS.values():
        injector.register(scenario_cls)
    return injector


def main():
    """CLI entrypoint cho bộ tiêm lỗi."""
    parser = argparse.ArgumentParser(description="KLTN - Fault Injection Framework (F01–F12)")
    parser.add_argument("--scenario", "-s", type=str, help="Mã kịch bản cần chạy (VD: F01, F04, ...)")
    parser.add_argument("--duration", "-d", type=float, default=None, help="Thời gian duy trì lỗi (giây)")
    parser.add_argument("--action", "-a", choices=["run", "inject", "recover", "recover-all"], default="run")
    parser.add_argument("--list", "-l", action="store_true", help="Liệt kê toàn bộ 12 kịch bản lỗi")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử nghiệm không tác động lên mạng thật")
    parser.add_argument("--all", action="store_true", help="Chạy tuần tự toàn bộ 12 kịch bản")
    parser.add_argument("--interval", type=float, default=10.0, help="Khoảng nghỉ giữa các kịch bản khi chạy --all")
    args = parser.parse_args()

    injector = create_default_injector(dry_run=args.dry_run)

    if args.list:
        print("\n" + "=" * 70)
        print("DANH SÁCH 12 KỊCH BẢN TIÊM LỖI (F01–F12) - SELF-HEALING NETWORK")
        print("=" * 70)
        for sid, cls in sorted(injector.registered_scenarios.items()):
            print(f"[{sid}] {cls.name:<30} | {cls.category:<18} | Default: {cls.default_duration}s")
            print(f"      Targets: {', '.join(cls.target_devices) or 'N/A'}")
            print(f"      Mô tả  : {cls.description}\n")
        sys.exit(0)

    if args.all:
        logger.info("Bắt đầu chạy tuần tự tất cả các kịch bản lỗi...")
        for sid in sorted(injector.registered_scenarios.keys()):
            injector.run_scenario(sid, duration=args.duration)
            logger.info(f"Nghỉ {args.interval}s trước kịch bản tiếp theo...")
            time.sleep(args.interval)
        logger.info("Đã hoàn tất chạy toàn bộ kịch bản lỗi.")
        sys.exit(0)

    if not args.scenario:
        parser.print_help()
        sys.exit(1)

    sid = args.scenario.upper()
    if args.action == "run":
        injector.run_scenario(sid, duration=args.duration)
    elif args.action == "inject":
        injector.inject(sid, duration=args.duration)
    elif args.action == "recover":
        injector.recover(sid)
    elif args.action == "recover-all":
        injector.recover_all()


if __name__ == "__main__":
    main()
