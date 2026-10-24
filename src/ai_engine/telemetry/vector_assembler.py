"""
ai_engine/telemetry/vector_assembler.py
Tổng hợp 8 chỉ số telemetry thành State Vector s_t in R^8.
Kiểm tra tính hợp lệ dữ liệu (validation) và phân loại chất lượng dữ liệu (data_quality flag).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger("ai_engine.telemetry.assembler")


@dataclass
class StateVector:
    """
    Vector trạng thái mạng 8 chiều s_t:
    [0] ccpu      : faucet_cpu_seconds_total (Monotonic Counter)
    [1] cres_mem  : process_resident_memory_bytes (Gauge)
    [2] cvirt_mem : process_virtual_memory_bytes (Gauge)
    [3] fsent     : of_messages_sent_total (Monotonic Counter)
    [4] ferr      : of_errors_total (Monotonic Counter)
    [5] fconn     : of_datapath_connected (Gauge)
    [6] fdisc     : of_datapath_disconnections_total (Monotonic Counter)
    [7] pdown     : port_status_down_total (Gauge)
    """
    ccpu: float
    cres_mem: float
    cvirt_mem: float
    fsent: float
    ferr: float
    fconn: float
    fdisc: float
    pdown: float
    data_quality: str = "OK"  # OK | PARTIAL | STALE | MISSING | INVALID

    def to_list(self) -> List[float]:
        return [
            self.ccpu,
            self.cres_mem,
            self.cvirt_mem,
            self.fsent,
            self.ferr,
            self.fconn,
            self.fdisc,
            self.pdown,
        ]

    def to_dict(self) -> Dict[str, float]:
        return {
            "ccpu": self.ccpu,
            "cres_mem": self.cres_mem,
            "cvirt_mem": self.cvirt_mem,
            "fsent": self.fsent,
            "ferr": self.ferr,
            "fconn": self.fconn,
            "fdisc": self.fdisc,
            "pdown": self.pdown,
        }

    def is_healthy(self) -> bool:
        """Trạng thái mạng được coi là khỏe mạnh nếu không có lỗi, không đứt kết nối và không sập port."""
        return self.ferr == 0.0 and self.fdisc == 0.0 and self.pdown == 0.0

    def validate(self) -> bool:
        """Kiểm tra giá trị không được NaN, Inf hoặc âm."""
        for v in self.to_list():
            if math.isnan(v) or math.isinf(v) or v < 0:
                return False
        return True


class VectorAssembler:
    """Lắp ghép các giá trị đọc được từ Prometheus thành StateVector chuẩn hóa."""

    @staticmethod
    def assemble(
        ccpu: Optional[float],
        cres_mem: Optional[float],
        cvirt_mem: Optional[float],
        fsent: Optional[float],
        ferr: Optional[float],
        fconn: Optional[float],
        fdisc: Optional[float],
        pdown: Optional[float],
    ) -> StateVector:
        vals = [ccpu, cres_mem, cvirt_mem, fsent, ferr, fconn, fdisc, pdown]
        missing_count = sum(1 for v in vals if v is None)

        def sanitize(val: Optional[float], default: float = 0.0) -> tuple[float, bool]:
            if val is None:
                return default, False
            if math.isnan(val) or math.isinf(val) or val < 0:
                return max(0.0, 0.0 if math.isnan(val) or math.isinf(val) else val), True
            return float(val), False

        has_invalid = False
        v_ccpu, inv1 = sanitize(ccpu)
        v_cres, inv2 = sanitize(cres_mem)
        v_cvirt, inv3 = sanitize(cvirt_mem)
        v_fsent, inv4 = sanitize(fsent)
        v_ferr, inv5 = sanitize(ferr)
        v_fconn, inv6 = sanitize(fconn)
        v_fdisc, inv7 = sanitize(fdisc)
        v_pdown, inv8 = sanitize(pdown)

        if any([inv1, inv2, inv3, inv4, inv5, inv6, inv7, inv8]):
            has_invalid = True

        vec = StateVector(
            ccpu=v_ccpu,
            cres_mem=v_cres,
            cvirt_mem=v_cvirt,
            fsent=v_fsent,
            ferr=v_ferr,
            fconn=v_fconn,
            fdisc=v_fdisc,
            pdown=v_pdown,
        )

        # Đánh giá chất lượng dữ liệu
        if has_invalid:
            vec.data_quality = "INVALID"
        elif missing_count == 0:
            vec.data_quality = "OK"
        elif missing_count <= 2:
            vec.data_quality = "PARTIAL"
        elif missing_count <= 5:
            vec.data_quality = "STALE"
        else:
            vec.data_quality = "MISSING"

        return vec
