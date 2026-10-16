"""
controller/sdwan/path_monitor.py
Phase 10 - Monitor 5 WAN paths realtime

Chạy trong background thread, probe mỗi probe_interval giây.
Cung cấp get_state() cho policy_engine và sdwan_controller.
"""

import threading
import time
import logging
from typing import Callable, Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from controller.sdwan.probes.wan_prober import WanProber
from controller.sdwan.models.path_state import PathState, PathStatus

logger = logging.getLogger(__name__)


class PathMonitor:
    """
    Background thread monitor 5 WAN paths.
    Probe mỗi probe_interval giây, lưu PathState hiện tại.
    Trigger callback on_state_change khi status thay đổi.
    """

    def __init__(self,
                 probe_targets: dict = None,
                 probe_interval: float = 3.0,
                 probe_count: int = 5):
        """
        probe_targets: {path_name: target_ip}. None = dùng default.
        probe_interval: Giây giữa các lần probe.
        probe_count: Số ICMP packet mỗi probe.
        """
        self.probe_interval = probe_interval
        self.prober         = WanProber(
            probe_targets=probe_targets,
            probe_count=probe_count,

            #--
            timeout_s=1,        # timeout 1s/packet thay vì 2s
            #--
        )

        # State dict (thread-safe via lock)
        self._lock   = threading.RLock()
        self._states: dict[str, PathState] = {
            name: PathState(name=name, status=PathStatus.UNKNOWN)
            for name in (probe_targets or self.prober.targets)
        }

        self._running = False
        self._thread:  Optional[threading.Thread] = None

        # Callback: fn(path_name, old_status, new_status) → None
        self.on_state_change: Optional[Callable] = None

        # History: danh sách (timestamp, path_name, old, new) gần nhất
        self._history: list[dict] = []
        self._max_history = 200

    # ─────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────

    def start(self):
        """Bắt đầu probe loop trong background thread."""
        if self._running:
            logger.warning('PathMonitor already running')
            return

        self._running = True
        self._thread  = threading.Thread(
            target=self._monitor_loop,
            name='wan-path-monitor',
            daemon=True,
        )
        self._thread.start()
        logger.info(f'PathMonitor started (interval={self.probe_interval}s, '
                    f'paths={list(self._states.keys())})')

    def stop(self):
        """Dừng probe loop."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.probe_interval * 2)
        logger.info('PathMonitor stopped')

    # ─────────────────────────────────────────
    # State Access
    # ─────────────────────────────────────────

    def get_state(self, path_name: str) -> PathState:
        """Lấy trạng thái hiện tại của 1 path."""
        with self._lock:
            return self._states.get(path_name, PathState(name=path_name))

    def get_all_states(self) -> dict:
        """Lấy trạng thái tất cả paths. Trả về shallow copy."""
        with self._lock:
            return dict(self._states)

    def get_up_paths(self) -> list:
        """Trả về danh sách tên paths đang UP."""
        with self._lock:
            return [
                name for name, state in self._states.items()
                if state.status == PathStatus.UP
            ]

    def get_history(self, limit: int = 50) -> list:
        """Lấy history các lần state change."""
        with self._lock:
            return list(self._history[-limit:])

    def get_summary(self) -> dict:
        """Tóm tắt trạng thái cho REST API / NOC Dashboard."""
        with self._lock:
            return {
                name: state.to_dict()
                for name, state in self._states.items()
            }

    # ─────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────

    def _monitor_loop(self):
        """Main probe loop."""
        while self._running:
            start_time = time.time()

            for path_name in list(self._states.keys()):
                if not self._running:
                    break
                try:
                    self._probe_one(path_name)
                except Exception as e:
                    logger.error(f'Error probing {path_name}: {e}')

            # Sleep remaining time
            elapsed = time.time() - start_time
            sleep_time = max(0.1, self.probe_interval - elapsed)
            time.sleep(sleep_time)

    def _probe_one(self, path_name: str):
        """Probe 1 path và cập nhật state."""
        new_state = self.prober.probe_path(path_name)

        with self._lock:
            old_state  = self._states.get(path_name)
            old_status = old_state.status if old_state else PathStatus.UNKNOWN

            # Kế thừa probe_count và fail_count từ cũ
            if old_state:
                new_state.probe_count = old_state.probe_count + 1
                if new_state.status in (PathStatus.DOWN, PathStatus.UNKNOWN):
                    new_state.fail_count = old_state.fail_count + 1
                else:
                    new_state.fail_count = 0

            self._states[path_name] = new_state

        # Trigger callback nếu status thay đổi
        if old_status != new_state.status:
            event = {
                'timestamp':  new_state.last_probe,
                'path':       path_name,
                'old_status': old_status.value,
                'new_status': new_state.status.value,
                'latency_ms': new_state.latency_ms,
                'loss_pct':   new_state.loss_pct,
            }
            with self._lock:
                self._history.append(event)
                if len(self._history) > self._max_history:
                    self._history.pop(0)

            logger.info(
                f'[PathMonitor] {path_name}: '
                f'{old_status.value} → {new_state.status.value} '
                f'(latency={new_state.latency_ms:.1f}ms, loss={new_state.loss_pct:.1f}%)'
            )

            if self.on_state_change:
                try:
                    self.on_state_change(path_name, old_status, new_state.status, new_state)
                except Exception as e:
                    logger.error(f'on_state_change callback error: {e}')
