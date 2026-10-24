"""
ai_engine/telemetry/collector.py
Bộ thu thập Telemetry và tổng hợp State Vector chu kỳ 10 giây.
Xuất dữ liệu ra file CSV dataset và JSONL logs.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

from .prometheus_client import PrometheusClient
from .fault_log_reader import FaultLogReader
from .context_metadata_parser import ContextMetadataParser, ContextMetadata
from .vector_assembler import VectorAssembler, StateVector

logger = logging.getLogger("ai_engine.telemetry.collector")

CSV_HEADER = [
    "timestamp",
    "ccpu",
    "cres_mem",
    "cvirt_mem",
    "fsent",
    "ferr",
    "fconn",
    "fdisc",
    "pdown",
    "fault_label",
    "duration_seconds",
    "target_dpid",
    "target_port",
    "error_cookie",
    "data_quality",
]


class TelemetryCollector:
    """Bộ thu thập dữ liệu tập trung: truy vấn Prometheus, đồng bộ nhãn lỗi và xuất dataset CSV."""

    def __init__(
        self,
        config_path_or_dict: Union[str, Path, dict] = "config/telemetry_config.yaml",
        base_dir: Optional[Union[str, Path]] = None,
    ):
        if base_dir is None:
            # Tìm thư mục gốc `src` (3 cấp tính từ file này: collector -> telemetry -> ai_engine -> src)
            self.base_dir = Path(__file__).resolve().parents[2]
        else:
            self.base_dir = Path(base_dir)

        if isinstance(config_path_or_dict, (str, Path)):
            cfg_file = self.base_dir / config_path_or_dict if not os.path.isabs(config_path_or_dict) else Path(config_path_or_dict)
            with open(cfg_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config_path_or_dict

        # Cấu hình Scrape
        scrape_cfg = self.config.get("scrape", {})
        self.interval = float(scrape_cfg.get("interval_seconds", 10.0))

        # Prometheus client
        prom_cfg = self.config.get("prometheus", {})
        base_url = prom_cfg.get("base_url", "http://localhost:9090")
        timeout = int(prom_cfg.get("timeout_seconds", 5))
        self.prom = PrometheusClient(base_url=base_url, timeout=timeout)

        # Output paths
        output_cfg = self.config.get("output", {})
        csv_rel = output_cfg.get("csv_path", "data/sdn_telemetry_dataset.csv")
        self.csv_path = self.base_dir / csv_rel if not os.path.isabs(csv_rel) else Path(csv_rel)

        raw_rel = output_cfg.get("raw_log_path", "data/telemetry_log.jsonl")
        self.raw_log_path = self.base_dir / raw_rel if not os.path.isabs(raw_rel) else Path(raw_rel)

        fault_log_rel = output_cfg.get("fault_log_path", "data/logs/fault_log.json")
        self.fault_log_path = self.base_dir / fault_log_rel if not os.path.isabs(fault_log_rel) else Path(fault_log_rel)

        # Sub-modules
        self.fault_reader = FaultLogReader(self.fault_log_path)
        self.ctx_parser = ContextMetadataParser(self.prom)

        self._ensure_output_dirs()

    def _ensure_output_dirs(self):
        """Khởi tạo thư mục và tệp CSV nếu chưa tồn tại."""
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
                writer.writeheader()
            logger.info(f"[CSV] Đã khởi tạo tệp mới: {self.csv_path}")

        self.raw_log_path.parent.mkdir(parents=True, exist_ok=True)

    def collect_once(self) -> Dict[str, Any]:
        """
        Thực hiện một chu kỳ cào và tổng hợp 8D vector.
        Trả về dictionary 15 cột.
        """
        ts = datetime.now(timezone.utc).isoformat()
        metrics_cfg = self.config.get("metrics", {})

        # Kiểm tra nhanh kết nối Prometheus
        prom_online = self.prom.is_reachable()
        if not prom_online:
            logger.warning("[Collector] Prometheus server không phản hồi -> dùng fallback")

        def q(key: str) -> float:
            m = metrics_cfg.get(key, {})
            promql = m.get("query", key)
            fallback = m.get("fallback", 0.0)
            if not prom_online:
                if fallback == "last_known":
                    return self.prom._last_known.get(promql, 0.0)
                try:
                    return float(fallback)
                except (ValueError, TypeError):
                    return 0.0
            return self.prom.query_with_fallback(promql, fallback)

        # 1. Truy vấn 8 chỉ số trạng thái
        ccpu = q("ccpu")
        cres_mem = q("cres_mem")
        cvirt_mem = q("cvirt_mem")
        fsent = q("fsent")
        ferr = q("ferr")
        fconn = q("fconn")
        fdisc = q("fdisc")
        pdown = q("pdown")

        # 2. Tổng hợp State Vector
        vec: StateVector = VectorAssembler.assemble(
            ccpu=ccpu,
            cres_mem=cres_mem,
            cvirt_mem=cvirt_mem,
            fsent=fsent,
            ferr=ferr,
            fconn=fconn,
            fdisc=fdisc,
            pdown=pdown,
        )

        if not prom_online:
            vec.data_quality = "STALE" if bool(self.prom._last_known) else "MISSING"

        # 3. Đọc nhãn lỗi phi_t và duration từ FaultInjector
        fault_label, duration_sec = self.fault_reader.get_current_fault()

        # 4. Trích xuất Context Metadata tầng Micro
        ctx: ContextMetadata = self.ctx_parser.parse() if prom_online else ContextMetadata()

        row: Dict[str, Any] = {
            "timestamp": ts,
            "ccpu": round(vec.ccpu, 4),
            "cres_mem": int(vec.cres_mem),
            "cvirt_mem": int(vec.cvirt_mem),
            "fsent": int(vec.fsent),
            "ferr": int(vec.ferr),
            "fconn": round(vec.fconn, 1),
            "fdisc": int(vec.fdisc),
            "pdown": int(vec.pdown),
            "fault_label": fault_label,
            "duration_seconds": round(duration_sec, 2),
            "target_dpid": ctx.target_dpid,
            "target_port": ctx.target_port,
            "error_cookie": ctx.error_cookie,
            "data_quality": vec.data_quality,
        }

        # 5. Ghi dòng dữ liệu vào CSV
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
                writer.writerow(row)
        except Exception as e:
            logger.error(f"[CSV] Ghi thất bại: {e}")

        # 6. Ghi raw log JSONL phục vụ debug
        try:
            with open(self.raw_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug(f"[JSONL] Ghi log thất bại: {e}")

        return row

    def run(self, max_cycles: Optional[int] = None, interval: Optional[float] = None):
        """Vòng lặp thu thập telemetry định kỳ theo chu kỳ (mặc định 10 giây)."""
        scrape_interval = interval if interval is not None else self.interval
        cycle = 0
        banner = (
            f"\n=======================================================\n"
            f" [TELEMETRY COLLECTOR] Interval: {scrape_interval}s\n"
            f" CSV Output: {self.csv_path}\n"
            f"=======================================================\n"
        )
        try:
            print(banner, flush=True)
        except Exception:
            pass

        try:
            while True:
                t_start = time.time()
                cycle += 1

                try:
                    row = self.collect_once()
                    msg = (
                        f"[{cycle:04d}] fconn={row['fconn']} pdown={row['pdown']} "
                        f"ferr={row['ferr']} fdisc={row['fdisc']} | "
                        f"label={row['fault_label']}({row['duration_seconds']}s) | "
                        f"quality={row['data_quality']}"
                    )
                    logger.info(msg)
                    try:
                        print(f"  [CYCLE {cycle:04d}] {msg}", flush=True)
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f"[{cycle:04d}] Error: {e}", exc_info=True)
                    try:
                        print(f"  [ERROR {cycle:04d}] {e}", flush=True)
                    except Exception:
                        pass

                if max_cycles is not None and cycle >= max_cycles:
                    print(f"\n[DONE] Finished {max_cycles} cycles.", flush=True)
                    break

                elapsed = time.time() - t_start
                sleep_time = max(0.0, scrape_interval - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n[STOP] Stopped by user (Ctrl+C).", flush=True)
