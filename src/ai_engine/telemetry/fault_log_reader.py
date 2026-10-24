"""
ai_engine/telemetry/fault_log_reader.py
Đọc nhật ký tiêm sự cố từ fault_log.json (JSON Lines) hoặc fault_log.txt để trích xuất:
- Nhãn lỗi phi_t (fault_label)
- Thời gian tồn tại lỗi duration_seconds
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Union

logger = logging.getLogger("ai_engine.telemetry.fault_reader")

STANDARD_FAULT_LABELS = {
    "LINK_FAULT",
    "PORT_FAULT",
    "FLOW_ERROR",
    "FAUCET_RELOAD",
    "SOFT_WARNING",
    "TEMP_WARNING",
    "NONE",
}

CATEGORY_TO_PHI = {
    "LINK_FAULT": "LINK_FAULT",
    "PORT_FAULT": "PORT_FAULT",
    "FLOW_ERROR": "FLOW_ERROR",
    "FAUCET_RELOAD": "FAUCET_RELOAD",
    "WAN_DEGRADATION": "SOFT_WARNING",
    "CONGESTION": "FLOW_ERROR",
    "TEMP_WARNING": "TEMP_WARNING",
    "SOFT_WARNING": "SOFT_WARNING",
}


class FaultLogReader:
    """Đọc log sự cố do FaultInjector phát sinh để đồng bộ nhãn lỗi phi_t vào State Vector."""

    def __init__(self, log_path: Union[str, Path] = "data/logs/fault_log.json"):
        self.log_path = Path(log_path)
        if self.log_path.suffix == ".txt":
            self.txt_path = self.log_path
            self.json_path = self.log_path.with_suffix(".json")
        else:
            self.json_path = self.log_path
            self.txt_path = self.log_path.with_suffix(".txt")

    def get_current_fault(self) -> Tuple[str, float]:
        """
        Xác định trạng thái lỗi hiện tại.
        Trả về: (fault_label: str, duration_seconds: float).
        Nếu mạng bình thường hoặc đã khôi phục -> ("NONE", 0.0).
        """
        if self.json_path.exists() and self.json_path.stat().st_size > 0:
            result = self._read_jsonl(self.json_path)
            if result is not None:
                return result

        if self.txt_path.exists() and self.txt_path.stat().st_size > 0:
            result = self._read_txt(self.txt_path)
            if result is not None:
                return result

        return "NONE", 0.0

    def _read_jsonl(self, path: Path) -> Optional[Tuple[str, float]]:
        """Đọc file JSONL từ dòng cuối lên (sự kiện mới nhất)."""
        now = datetime.now(timezone.utc)
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"[FaultLogReader] Lỗi đọc {path}: {e}")
            return None

        for line in reversed(lines):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get("event_type", "").upper()
            status = event.get("status", "").upper()
            category = event.get("category", "").upper()
            ts_str = event.get("timestamp", "")
            duration_sec = float(event.get("duration_sec", 0.0))

            if event_type == "RECOVER" and status in ("SUCCESS", "DRY_RUN"):
                return "NONE", 0.0

            if event_type == "INJECT" and status in ("SUCCESS", "DRY_RUN", "START"):
                phi_t = CATEGORY_TO_PHI.get(category, "SOFT_WARNING")
                duration = 0.0
                if ts_str:
                    try:
                        event_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if event_time.tzinfo is None:
                            event_time = event_time.replace(tzinfo=timezone.utc)
                        duration = max(0.0, (now - event_time).total_seconds())
                    except Exception:
                        duration = 0.0

                if duration_sec > 0 and duration > duration_sec + 5.0:
                    return "NONE", 0.0

                return phi_t, round(duration, 2)

        return "NONE", 0.0

    def _read_txt(self, path: Path) -> Optional[Tuple[str, float]]:
        """Đọc file txt dạng pipe-delimited hoặc dạng log line của FaultInjector."""
        now = datetime.now(timezone.utc)
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"[FaultLogReader] Lỗi đọc {path}: {e}")
            return None

        for line in reversed(lines):
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    ts_str, event_type, fault_type = parts[0], parts[1], parts[2]
                    if event_type == "FAULT_END":
                        return "NONE", 0.0
                    if event_type == "FAULT_START":
                        phi_t = CATEGORY_TO_PHI.get(fault_type, fault_type)
                        try:
                            start_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if start_time.tzinfo is None:
                                start_time = start_time.replace(tzinfo=timezone.utc)
                            duration = max(0.0, (now - start_time).total_seconds())
                        except Exception:
                            duration = 0.0
                        return phi_t, round(duration, 2)

            if "[RECOVER]" in line:
                return "NONE", 0.0

            if "[INJECT]" in line:
                for cat in CATEGORY_TO_PHI:
                    if cat in line:
                        return CATEGORY_TO_PHI[cat], 0.0
                return "SOFT_WARNING", 0.0

        return "NONE", 0.0
