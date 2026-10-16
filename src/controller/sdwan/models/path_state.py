"""
controller/sdwan/models/path_state.py
Dataclass mô tả trạng thái của 1 WAN path
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class PathStatus(Enum):
    UP        = "UP"
    DOWN      = "DOWN"
    DEGRADED  = "DEGRADED"   # UP nhưng không đạt SLA
    UNKNOWN   = "UNKNOWN"    # Chưa probe lần nào


@dataclass
class PathState:
    """
    Trạng thái realtime của 1 WAN path.
    Được cập nhật bởi PathMonitor mỗi probe_interval giây.
    """
    name:          str
    status:        PathStatus = PathStatus.UNKNOWN
    latency_ms:    float      = 0.0
    jitter_ms:     float      = 0.0
    loss_pct:      float      = 0.0
    bandwidth_mbps: float     = 0.0
    last_probe:    float      = field(default_factory=time.time)
    probe_count:   int        = 0
    fail_count:    int        = 0   # Consecutive failures

    def meets_sla(self, max_latency: float, max_loss: float, max_jitter: float) -> bool:
        """
        Kiểm tra path có đáp ứng SLA yêu cầu không.
        Chỉ trả về True nếu path đang UP và tất cả metrics <= threshold.
        """
        return (
            self.status == PathStatus.UP and
            self.latency_ms <= max_latency and
            self.loss_pct   <= max_loss and
            self.jitter_ms  <= max_jitter
        )

    def to_dict(self) -> dict:
        """Serialize để gửi qua REST API / SocketIO."""
        return {
            'name':          self.name,
            'status':        self.status.value,
            'latency_ms':    round(self.latency_ms, 2),
            'jitter_ms':     round(self.jitter_ms, 2),
            'loss_pct':      round(self.loss_pct, 3),
            'bandwidth_mbps': self.bandwidth_mbps,
            'last_probe':    self.last_probe,
            'probe_count':   self.probe_count,
        }

    def score(self) -> float:
        """
        Tính điểm tổng hợp (thấp = tốt hơn).
        Dùng để so sánh các paths khi chọn đường.
        """
        if self.status == PathStatus.DOWN:
            return float('inf')
        # Kết hợp latency + jitter*2 + loss*100
        return self.latency_ms + (self.jitter_ms * 2) + (self.loss_pct * 100)
