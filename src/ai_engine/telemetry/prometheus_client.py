"""
ai_engine/telemetry/prometheus_client.py
Lớp wrapper gọi Prometheus HTTP API để truy vấn instant metrics và vector metrics.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
import requests

logger = logging.getLogger("ai_engine.telemetry.prometheus")


class PrometheusClient:
    """Client truy vấn Prometheus HTTP API (mặc định http://localhost:9090)."""

    def __init__(self, base_url: str = "http://localhost:9090", timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._last_known: Dict[str, float] = {}

    def is_reachable(self) -> bool:
        """Kiểm tra nhanh xem Prometheus server có phản hồi không."""
        try:
            resp = requests.get(f"{self.base_url}/-/healthy", timeout=min(2, self.timeout))
            return resp.status_code == 200
        except Exception:
            return False

    def query_instant(self, promql: str) -> Optional[float]:
        """
        Truy vấn một giá trị instant metric từ Prometheus.
        Trả về float nếu thành công, None nếu không có kết quả hoặc gặp lỗi.
        """
        url = f"{self.base_url}/api/v1/query"
        try:
            resp = requests.get(url, params={"query": promql}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            results = data.get("result", [])
            if not results:
                logger.warning(f"[Prometheus] Query rỗng: '{promql}'")
                return None

            raw_val = results[0]["value"][1]
            val = float(raw_val)
            self._last_known[promql] = val
            return val
        except requests.exceptions.Timeout:
            logger.error(f"[Prometheus] Timeout ({self.timeout}s) khi query: '{promql}'")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"[Prometheus] Không kết nối được tới {self.base_url}")
            return None
        except (KeyError, IndexError, ValueError, TypeError) as e:
            logger.error(f"[Prometheus] Lỗi parse kết quả cho '{promql}': {e}")
            return None
        except Exception as e:
            logger.error(f"[Prometheus] Lỗi không xác định khi query '{promql}': {e}")
            return None

    def query_with_fallback(self, promql: str, fallback: Union[float, str] = 0.0) -> float:
        """
        Query với cơ chế fallback khi Prometheus không phản hồi:
        - fallback='last_known': trả về giá trị cào thành công gần nhất (hoặc 0.0 nếu chưa có).
        - fallback=<số float>: trả về giá trị chỉ định.
        """
        value = self.query_instant(promql)
        if value is not None:
            return value

        if fallback == "last_known":
            cached = self._last_known.get(promql)
            if cached is not None:
                logger.warning(f"[Prometheus] Dùng last_known={cached:.4f} cho '{promql}'")
                return cached
            logger.error(f"[Prometheus] Không có last_known cho '{promql}', trả về 0.0")
            return 0.0

        try:
            return float(fallback)
        except (ValueError, TypeError):
            return 0.0

    def query_vector(self, promql: str, label_filter: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Truy vấn danh sách kết quả (vector) từ Prometheus để trích xuất Context Metadata.
        Trả về danh sách các dict có dạng: [{"labels": {...}, "value": float}]
        """
        url = f"{self.base_url}/api/v1/query"
        results_parsed: List[Dict[str, Any]] = []
        try:
            resp = requests.get(url, params={"query": promql}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            for item in data.get("result", []):
                metric_labels = item.get("metric", {})
                raw_val = item.get("value", [0, "0"])[1]
                try:
                    val = float(raw_val)
                except (ValueError, TypeError):
                    val = 0.0

                if label_filter:
                    if all(metric_labels.get(k) == v for k, v in label_filter.items()):
                        results_parsed.append({"labels": metric_labels, "value": val})
                else:
                    results_parsed.append({"labels": metric_labels, "value": val})
        except Exception as e:
            logger.error(f"[Prometheus] query_vector thất bại cho '{promql}': {e}")

        return results_parsed
