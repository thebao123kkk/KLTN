"""
ai_engine/telemetry/context_metadata_parser.py
Trích xuất Context Metadata (DPID, Port, Cookie) từ per-datapath metrics.

Định vị 2 Tầng (2-Tier Localization):
  - Tầng MACRO: PPO Agent quyết định loại hành động a_t (0: NOOP, 1: PORT_UP, 2: CONTROLLER_RESET, 3: FLUSH_FLOWS).
  - Tầng MICRO (module này): Xác định thiết bị, cổng, hoặc cookie cụ thể bị sự cố.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional
from .prometheus_client import PrometheusClient

logger = logging.getLogger("ai_engine.telemetry.context_parser")


@dataclass
class ContextMetadata:
    """Thông tin định vị lỗi tầng Micro phục vụ bộ thực thi hành động."""
    target_dpid: str = ""
    target_port: int = -1
    error_cookie: str = ""
    disconnected_dpids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "target_dpid": self.target_dpid,
            "target_port": self.target_port,
            "error_cookie": self.error_cookie,
            "disconnected_dpids": self.disconnected_dpids,
        }


class ContextMetadataParser:
    """Truy vấn các metric per-datapath để xác định vị trí phần cứng/giao thức gặp sự cố."""

    def __init__(self, prom_client: PrometheusClient):
        self.prom = prom_client

    def parse(self) -> ContextMetadata:
        metadata = ContextMetadata()

        # 1. Tìm switch có port bị down (of_port_status == 0)
        try:
            port_down_results = self.prom.query_vector("of_port_status == 0")
            if port_down_results:
                labels = port_down_results[0].get("labels", {})
                metadata.target_dpid = str(labels.get("dp_name", labels.get("dpid", "")))
                port_raw = labels.get("port_name", labels.get("port", "-1"))
                try:
                    if isinstance(port_raw, str) and "eth" in port_raw:
                        digits = "".join(filter(str.isdigit, port_raw))
                        metadata.target_port = int(digits) if digits else -1
                    else:
                        metadata.target_port = int(port_raw)
                except (ValueError, TypeError):
                    metadata.target_port = -1

                logger.debug(
                    f"[ContextParser] Port DOWN phát hiện: dpid={metadata.target_dpid}, "
                    f"port={metadata.target_port}"
                )
        except Exception as e:
            logger.debug(f"[ContextParser] Lỗi parse port_status: {e}")

        # 2. Tìm switch có lỗi OpenFlow (of_errors_total > 0)
        try:
            error_results = self.prom.query_vector("of_errors_total > 0")
            if error_results:
                err_labels = error_results[0].get("labels", {})
                if not metadata.target_dpid:
                    metadata.target_dpid = str(err_labels.get("dp_name", err_labels.get("dpid", "")))
                metadata.error_cookie = str(err_labels.get("cookie", ""))
                logger.debug(
                    f"[ContextParser] OpenFlow error phát hiện: dpid={metadata.target_dpid}, "
                    f"cookie={metadata.error_cookie}"
                )
        except Exception as e:
            logger.debug(f"[ContextParser] Lỗi parse errors_total: {e}")

        # 3. Tìm switch mất kết nối (faucet_dp_status == 0)
        try:
            dp_disconnected_results = self.prom.query_vector("faucet_dp_status == 0")
            for entry in dp_disconnected_results:
                dpid = str(entry.get("labels", {}).get("dp_name", entry.get("labels", {}).get("dpid", "")))
                if dpid and dpid not in metadata.disconnected_dpids:
                    metadata.disconnected_dpids.append(dpid)
                    logger.debug(f"[ContextParser] Switch mất kết nối: {dpid}")

            if metadata.disconnected_dpids and not metadata.target_dpid:
                metadata.target_dpid = metadata.disconnected_dpids[0]
        except Exception as e:
            logger.debug(f"[ContextParser] Lỗi parse dp_status: {e}")

        return metadata
