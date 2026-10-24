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
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
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
    """Bộ thu thập dữ liệu tập trung: truy vấn Exporter trực tiếp / Prometheus, đồng bộ nhãn lỗi và xuất dataset CSV."""

    def __init__(
        self,
        config_path_or_dict: Union[str, Path, dict] = "config/telemetry_config.yaml",
        base_dir: Optional[Union[str, Path]] = None,
        direct_mode: Optional[str] = None,
    ):
        if base_dir is None:
            # Tìm thư mục gốc `src` (3 cấp tính từ file này: collector -> telemetry -> ai_engine -> src)
            self.base_dir = Path(__file__).resolve().parents[2]
        else:
            self.base_dir = Path(base_dir)

        if isinstance(config_path_or_dict, (str, Path)):
            cfg_file = self.base_dir / config_path_or_dict if not os.path.isabs(config_path_or_dict) else Path(config_path_or_dict)
            with open(cfg_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = config_path_or_dict or {}

        # Cấu hình Scrape
        scrape_cfg = self.config.get("scrape", {})
        self.interval = float(scrape_cfg.get("interval_seconds", 10.0))

        # Prometheus client
        prom_cfg = self.config.get("prometheus", {})
        base_url = prom_cfg.get("base_url", "http://localhost:9091")
        timeout = int(prom_cfg.get("timeout_seconds", 5))
        self.prom = PrometheusClient(base_url=base_url, timeout=timeout)

        # Cấu hình Exporters (Học hỏi trực tiếp từ test_fault_scenarios.py)
        exp_cfg = self.config.get("exporters", {})
        self.gauge_url = exp_cfg.get("gauge_url", "http://localhost:9303/metrics")
        self.faucet_url = exp_cfg.get("faucet_url", "http://localhost:9302/metrics")
        self.node_url = exp_cfg.get("node_url", "http://localhost:9100/metrics")
        self.direct_mode = direct_mode or exp_cfg.get("direct_mode", "auto")

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

    def query_direct_exporters(self) -> Tuple[bool, Dict[str, float], ContextMetadata]:
        """
        Truy vấn trực tiếp Gauge Exporter (:9303) và Faucet Exporter (:9302)
        theo chuẩn thực thi của test_fault_scenarios.py.
        Đảm bảo đọc đầy đủ 8 chỉ số trạng thái và Micro Context Metadata
        ngay cả khi không có máy chủ Prometheus.
        """
        data: Dict[str, float] = {
            "ccpu": 0.0,
            "cres_mem": 0.0,
            "cvirt_mem": 0.0,
            "fsent": 0.0,
            "ferr": 0.0,
            "fconn": 0.0,
            "fdisc": 0.0,
            "pdown": 0.0,
        }
        ctx = ContextMetadata()
        gauge_success = False
        faucet_success = False

        # 1. Gauge Exporter (:9303) -> fconn, pdown, fsent, ferr, fdisc, port status
        try:
            req = urllib.request.Request(self.gauge_url, headers={"User-Agent": "TelemetryCollector"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                content = resp.read().decode("utf-8")
                gauge_success = True
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("#") or not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        name, val_str = parts[0], parts[1]
                        try:
                            val = float(val_str)
                        except ValueError:
                            continue
                        if name == "of_datapath_connected":
                            data["fconn"] = val
                        elif name == "port_status_down_total":
                            data["pdown"] = val
                        elif name == "of_messages_sent_total":
                            data["fsent"] = val
                        elif name == "of_errors_total":
                            data["ferr"] = val
                            if val > 0 and not ctx.error_cookie:
                                ctx.error_cookie = f"ERR_{int(val)}"
                        elif name == "of_datapath_disconnections_total":
                            data["fdisc"] = val
                        elif "of_port_status" in name and val == 0.0:
                            m_dp = re.search(r'dp_name="([^"]+)"', name)
                            m_port = re.search(r'port="([^"]+)"', name)
                            if m_dp and not ctx.target_dpid:
                                ctx.target_dpid = m_dp.group(1)
                            if m_port and ctx.target_port == -1:
                                p_str = m_port.group(1)
                                try:
                                    if "eth" in p_str:
                                        digits = "".join(filter(str.isdigit, p_str))
                                        ctx.target_port = int(digits) if digits else -1
                                    else:
                                        ctx.target_port = int(p_str)
                                except ValueError:
                                    ctx.target_port = -1
                        elif "faucet_dp_status" in name and val == 0.0:
                            m_dp = re.search(r'dp_name="([^"]+)"', name)
                            if m_dp:
                                dpid = m_dp.group(1)
                                if dpid not in ctx.disconnected_dpids:
                                    ctx.disconnected_dpids.append(dpid)
                                if not ctx.target_dpid:
                                    ctx.target_dpid = dpid
        except Exception as e:
            logger.debug(f"[Collector] Không đọc được Gauge Exporter ({self.gauge_url}): {e}")

        # 2. Faucet Exporter (:9302) -> ccpu, cres_mem, cvirt_mem
        try:
            req = urllib.request.Request(self.faucet_url, headers={"User-Agent": "TelemetryCollector"})
            with urllib.request.urlopen(req, timeout=1) as resp:
                content = resp.read().decode("utf-8")
                faucet_success = True
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("#") or not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        name, val_str = parts[0], parts[1]
                        try:
                            val = float(val_str)
                        except ValueError:
                            continue
                        if "faucet_cpu_seconds_total" in name:
                            data["ccpu"] = val
                        elif "process_resident_memory_bytes" in name:
                            data["cres_mem"] = val
                        elif "process_virtual_memory_bytes" in name:
                            data["cvirt_mem"] = val
        except Exception as e:
            logger.debug(f"[Collector] Không đọc được Faucet Exporter ({self.faucet_url}): {e}")

        # 3. Node Exporter fallback (:9100) nếu Faucet chưa có RAM
        if (data["cres_mem"] == 0.0 or data["cvirt_mem"] == 0.0) and self.node_url:
            try:
                req = urllib.request.Request(self.node_url, headers={"User-Agent": "TelemetryCollector"})
                with urllib.request.urlopen(req, timeout=1) as resp:
                    content = resp.read().decode("utf-8")
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("#") or not line:
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            name, val_str = parts[0], parts[1]
                            try:
                                val = float(val_str)
                            except ValueError:
                                continue
                            if "process_resident_memory_bytes" in name and data["cres_mem"] == 0.0:
                                data["cres_mem"] = val
                            elif "process_virtual_memory_bytes" in name and data["cvirt_mem"] == 0.0:
                                data["cvirt_mem"] = val
            except Exception:
                pass

        # 4. Trực tiếp từ Linux /sys/class/net nếu Exporter chưa chạy nhưng Mininet đang active
        if not gauge_success and os.path.exists("/sys/class/net"):
            try:
                switches = set()
                ports_down = 0
                for iface in os.listdir("/sys/class/net"):
                    if "-eth" in iface:
                        switches.add(iface.split("-eth")[0])
                        flags_f = Path(f"/sys/class/net/{iface}/flags")
                        if flags_f.exists():
                            try:
                                if (int(flags_f.read_text().strip(), 16) & 1) == 0:
                                    ports_down += 1
                            except Exception:
                                pass
                if switches:
                    data["fconn"] = float(len(switches))
                    data["pdown"] = float(ports_down)
                    gauge_success = True
            except Exception:
                pass

        success = gauge_success or faucet_success
        return success, data, ctx

    def collect_once(self) -> Dict[str, Any]:
        """
        Thực hiện một chu kỳ cào và tổng hợp 8D vector.
        Hỗ trợ cào trực tiếp Exporter (như test_fault_scenarios.py) hoặc qua Prometheus.
        Trả về dictionary 15 cột.
        """
        ts = datetime.now(timezone.utc).isoformat()
        metrics_cfg = self.config.get("metrics", {})

        # 1. Thử thu thập trực tiếp từ Exporter nếu mode là auto hoặc direct
        direct_ok = False
        direct_metrics: Dict[str, float] = {}
        direct_ctx = ContextMetadata()

        if self.direct_mode in ("auto", "direct"):
            direct_ok, direct_metrics, direct_ctx = self.query_direct_exporters()

        vec: Optional[StateVector] = None
        ctx: ContextMetadata = direct_ctx

        if direct_ok:
            # Lấy thành công trực tiếp từ Exporter (:9303 & :9302)
            vec = VectorAssembler.assemble(
                ccpu=direct_metrics.get("ccpu", 0.0),
                cres_mem=direct_metrics.get("cres_mem", 0.0),
                cvirt_mem=direct_metrics.get("cvirt_mem", 0.0),
                fsent=direct_metrics.get("fsent", 0.0),
                ferr=direct_metrics.get("ferr", 0.0),
                fconn=direct_metrics.get("fconn", 0.0),
                fdisc=direct_metrics.get("fdisc", 0.0),
                pdown=direct_metrics.get("pdown", 0.0),
            )
            vec.data_quality = "OK"

            # Lưu vào last_known của PrometheusClient để làm cache
            for k, v in direct_metrics.items():
                m = metrics_cfg.get(k, {})
                promql = m.get("query", k)
                self.prom._last_known[promql] = v
        else:
            # Fallback sang Prometheus Server
            prom_online = self.prom.is_reachable()
            if not prom_online:
                logger.warning("[Collector] Cả Exporter lẫn Prometheus đều không phản hồi -> dùng fallback")

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

            ccpu = q("ccpu")
            cres_mem = q("cres_mem")
            cvirt_mem = q("cvirt_mem")
            fsent = q("fsent")
            ferr = q("ferr")
            fconn = q("fconn")
            fdisc = q("fdisc")
            pdown = q("pdown")

            vec = VectorAssembler.assemble(
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

            ctx = self.ctx_parser.parse() if prom_online else ContextMetadata()

        # 2. Đọc nhãn lỗi phi_t và duration từ FaultInjector
        fault_label, duration_sec = self.fault_reader.get_current_fault()

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
