"""
controller/sdwan/sdwan_controller.py
Phase 10 - SD-WAN Controller chính

Orchestrate PathMonitor + PolicyEngine + TrafficSteerer.
Cung cấp REST API (Flask) để AI Engine và NOC Dashboard tương tác.

Cách chạy:
  # Chạy độc lập (sau khi Mininet đã start):
  python3 src/controller/sdwan/sdwan_controller.py

  # Hoặc tích hợp vào enterprise_topo.py phase 10:
  from controller.sdwan.sdwan_controller import SDWANController
  sdwan = SDWANController(mininet_gws={...})
  sdwan.start()
"""

import threading
import time
import logging
import json
import os
import sys
from typing import Optional, Dict, List, Any #mới thêm vô

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from controller.sdwan.path_monitor    import PathMonitor
from controller.sdwan.policy_engine   import PolicyEngine
from controller.sdwan.traffic_steerer import TrafficSteerer
from controller.sdwan.models.path_state  import PathStatus
from controller.sdwan.models.traffic_class import TrafficClass

try:
    from flask import Flask, jsonify, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print('[WARNING] Flask not installed. REST API disabled.')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('sdwan')


class SDWANController:
    """
    SD-WAN Controller chính.
    Tích hợp PathMonitor + PolicyEngine + TrafficSteerer.
    Cung cấp REST API tại cổng api_port.
    """

    def __init__(self,
                 mininet_gws: dict = None,
                 probe_interval: float = 3.0,
                 control_interval: float = 5.0,
                 api_port: int = 7070):
        """
        mininet_gws: {site_code: mininet_host}
          VD: {'BL': bl_gw, 'NT': nt_dist01, 'HCM': hcm_dist01, 'DC': dc_sp_gw}
          Nếu None → dùng standalone mode (chỉ monitor, không steer).

        probe_interval:   Giây giữa mỗi lần probe paths.
        control_interval: Giây giữa mỗi lần control loop evaluate + steer.
        api_port:         REST API port.
        """
        self.mininet_gws      = mininet_gws
        self.probe_interval   = probe_interval
        self.control_interval = control_interval
        self.api_port         = api_port

        # Components
        #self.monitor = PathMonitor(probe_interval=probe_interval)
        self.monitor = PathMonitor(probe_interval=probe_interval, probe_count=2)
        self.policy  = PolicyEngine()
        self.steerer = TrafficSteerer(mininet_gws or {}) if mininet_gws else None

        # State
        self._running          = False
        self._control_thread   = None
        self._api_thread       = None
        self.events: list[dict] = []   # Log path switch events
        self.last_decisions: dict = {}  # Quyết định cuối cùng

        # Flask app
        if HAS_FLASK:
            self.app = Flask(__name__)
            self._setup_routes()
        else:
            self.app = None

        # Register state change callback
        self.monitor.on_state_change = self._on_path_state_change

    # ─────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────

    def start(self):
        """Khởi động controller: monitor + control loop + REST API."""
        logger.info('Starting SD-WAN Controller...')

        # 1. Bắt đầu probe loop
        self.monitor.start()
        logger.info(f'PathMonitor started (probe_interval={self.probe_interval}s)')

        # 2. Bắt đầu control loop
        self._running = True
        self._control_thread = threading.Thread(
            target=self._control_loop,
            name='sdwan-control-loop',
            daemon=True,
        )
        self._control_thread.start()
        logger.info(f'Control loop started (interval={self.control_interval}s)')

        # 3. Bắt đầu REST API (nếu có Flask)
        if self.app and HAS_FLASK:
            self._api_thread = threading.Thread(
                target=lambda: self.app.run(
                    host='0.0.0.0',
                    port=self.api_port,
                    debug=False,
                    use_reloader=False,
                ),
                name='sdwan-api',
                daemon=True,
            )
            self._api_thread.start()
            logger.info(f'REST API started at http://0.0.0.0:{self.api_port}')

        print(f'[SDWAN] Controller started')
        print(f'[SDWAN] REST API: http://localhost:{self.api_port}')
        print(f'[SDWAN] Status:   http://localhost:{self.api_port}/api/status')

    def stop(self):
        """Dừng controller."""
        self._running = False
        self.monitor.stop()
        if self._control_thread:
            self._control_thread.join(timeout=10)
        logger.info('SD-WAN Controller stopped')

    # ─────────────────────────────────────────
    # Control Loop
    # ─────────────────────────────────────────

    def _control_loop(self):
        """
        Main control loop.
        Mỗi control_interval giây:
          1. Lấy path states từ monitor
          2. Đánh giá path tốt nhất (policy engine)
          3. Steer traffic nếu cần
        """
        while self._running:
            time.sleep(self.control_interval)

            try:
                states    = self.monitor.get_all_states()
                decisions = self.policy.evaluate_all_traffic(states)

                # Lấy primary path (VOIP = highest priority)
                primary_path = decisions.get(TrafficClass.VOIP)

                if primary_path and self.steerer:
                    src_sites = ['BL', 'NT', 'HCM']
                    for from_site in src_sites:
                        if from_site in (self.mininet_gws or {}):
                            self.steerer.steer_traffic(from_site, 'DC', primary_path)

                self.last_decisions = {
                    tc.value: path for tc, path in decisions.items()
                }

            except Exception as e:
                logger.error(f'Control loop error: {e}')

    def _on_path_state_change(self, path_name: str, old_status, new_status, new_state):
        """
        Callback khi 1 path thay đổi trạng thái.
        Trigger immediate re-evaluation và steering.
        """
        # event = {
        #     'timestamp':  time.time(),
        #     'type':       'PATH_STATE_CHANGE',
        #     'path':       path_name,
        #     'old_status': old_status.value,
        #     'new_status': new_status.value,
        #     'latency_ms': new_state.latency_ms,
        #     'loss_pct':   new_state.loss_pct,
        # }
        # self.events.append(event)
        # if len(self.events) > 1000:
        #     self.events.pop(0)

        # if new_status == PathStatus.DOWN:
        #     logger.warning(f'[SDWAN] PATH DOWN: {path_name} → Immediate failover!')
        #     self._immediate_failover(path_name)
        # elif old_status == PathStatus.DOWN and new_status == PathStatus.UP:
        #     logger.info(f'[SDWAN] PATH RECOVERED: {path_name}')

    def _immediate_failover(self, failed_path: str):
        """Failover ngay lập tức khi 1 path DOWN (không chờ control_loop)."""
        try:
            states = self.monitor.get_all_states()
            decisions = self.policy.evaluate_all_traffic(states)
            primary_path = decisions.get(TrafficClass.VOIP)

            if primary_path and primary_path != failed_path and self.steerer:
                logger.info(f'[SDWAN] Failover: {failed_path} → {primary_path}')
                src_sites = ['BL', 'NT', 'HCM']
                for from_site in src_sites:
                    if from_site in (self.mininet_gws or {}):
                        self.steerer.steer_traffic(from_site, 'DC', primary_path)

                event = {
                    'timestamp':   time.time(),
                    'type':        'FAILOVER',
                    'failed_path': failed_path,
                    'new_path':    primary_path,
                }
                self.events.append(event)
        except Exception as e:
            logger.error(f'Failover error: {e}')

    # ─────────────────────────────────────────
    # REST API
    # ─────────────────────────────────────────

    def _setup_routes(self):
        """Cài đặt Flask REST API endpoints."""
        app = self.app

        @app.route('/api/status', methods=['GET'])
        def get_status():
            """Trạng thái tất cả WAN paths."""
            return jsonify(self.monitor.get_summary())

        @app.route('/api/decisions', methods=['GET'])
        def get_decisions():
            """Quyết định path hiện tại per traffic class."""
            return jsonify({
                'decisions': self.last_decisions,
                'timestamp': time.time(),
            })

        @app.route('/api/steer', methods=['POST'])
        def manual_steer():
            """
            AI Engine hoặc NOC Dashboard gọi để force-steer traffic.
            Body: {"from_site": "HCM", "to_site": "DC", "path": "5G"}
            """
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON body'}), 400

            from_site = data.get('from_site')
            to_site   = data.get('to_site', 'DC')
            path_name = data.get('path')

            if not all([from_site, path_name]):
                return jsonify({'error': 'from_site and path required'}), 400

            if not self.steerer:
                return jsonify({'error': 'No steerer (standalone mode)'}), 503

            ok = self.steerer.steer_traffic(from_site, to_site, path_name)

            event = {
                'timestamp': time.time(),
                'type':      'MANUAL_STEER',
                'from_site': from_site,
                'to_site':   to_site,
                'path':      path_name,
                'success':   ok,
                'source':    'REST_API',
            }
            self.events.append(event)

            return jsonify({'status': 'ok' if ok else 'failed', 'path': path_name})

        @app.route('/api/steer_all', methods=['POST'])
        def steer_all():
            """Force tất cả sites dùng 1 path cụ thể."""
            data = request.get_json() or {}
            path_name = data.get('path')
            if not path_name:
                return jsonify({'error': 'path required'}), 400

            if not self.steerer:
                return jsonify({'error': 'No steerer'}), 503

            results = self.steerer.steer_all_to_path(path_name)
            return jsonify({
                'status': 'ok',
                'path': path_name,
                'results': {f'{k[0]}→{k[1]}': v for k, v in results.items()}
            })

        @app.route('/api/events', methods=['GET'])
        def get_events():
            """Lịch sử các sự kiện path change / steer."""
            limit = int(request.args.get('limit', 50))
            return jsonify(self.events[-limit:])

        @app.route('/api/history', methods=['GET'])
        def get_history():
            """Lịch sử steering decisions."""
            if self.steerer:
                return jsonify(self.steerer.get_history())
            return jsonify([])

        @app.route('/api/policy', methods=['GET'])
        def get_policy():
            """Policy summary."""
            return jsonify(self.policy.get_policy_summary())

        @app.route('/api/policy/reload', methods=['POST'])
        def reload_policy():
            """Hot reload policy từ YAML file."""
            self.policy.reload()
            return jsonify({'status': 'reloaded'})

        @app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint cho NOC Dashboard."""
            up_count = len(self.monitor.get_up_paths())
            return jsonify({
                'status':    'healthy' if up_count > 0 else 'degraded',
                'paths_up':  up_count,
                'timestamp': time.time(),
            })

    # ─────────────────────────────────────────
    # Public helpers
    # ─────────────────────────────────────────

    def get_current_path(self, from_site: str = 'BL', to_site: str = 'DC') -> Optional[str]:
        """Trả về path đang active cho 1 route pair."""
        if self.steerer:
            return self.steerer.current_paths.get((from_site, to_site))
        return None

    def force_path(self, path_name: str):
        """Force tất cả sites dùng path này (dùng bởi AI Engine)."""
        if self.steerer:
            self.steerer.steer_all_to_path(path_name)


# ─────────────────────────────────────────────────────────────
# Standalone entry point
# ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='SD-WAN Controller')
    parser.add_argument('--port', type=int, default=7070, help='REST API port')
    parser.add_argument('--probe-interval', type=float, default=3.0)
    parser.add_argument('--control-interval', type=float, default=5.0)
    args = parser.parse_args()

    print('SD-WAN Controller - Standalone Mode (no Mininet steerer)')
    print('Monitoring only - use REST API to view path states')
    print(f'API: http://localhost:{args.port}')
    print('Ctrl+C to stop\n')

    controller = SDWANController(
        mininet_gws=None,   # Standalone: chỉ monitor, không steer
        probe_interval=args.probe_interval,
        control_interval=args.control_interval,
        api_port=args.port,
    )
    controller.start()

    try:
        while True:
            time.sleep(10)
            states = controller.monitor.get_summary()
            print('\n=== WAN Path Status ===')
            for name, s in states.items():
                print(f'  {name:6s}: {s["status"]:8s} | '
                      f'latency={s["latency_ms"]:6.1f}ms | '
                      f'loss={s["loss_pct"]:5.2f}%')
    except KeyboardInterrupt:
        print('\nStopping...')
        controller.stop()
