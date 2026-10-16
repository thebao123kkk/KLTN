"""
controller/sdwan/policy_engine.py
Phase 10 - SD-WAN Policy Engine

Đọc policy từ config/sdwan_policy.yaml và quyết định path tốt nhất
cho mỗi traffic class dựa trên SLA requirements.
"""

import os
import yaml
import logging
from typing import Optional

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from controller.sdwan.models.path_state import PathState, PathStatus
from controller.sdwan.models.traffic_class import (
    TrafficClass, SLA_REQUIREMENTS, PATH_PRIORITY
)

logger = logging.getLogger(__name__)

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
_DEFAULT_POLICY_PATH = os.path.join(_CONFIG_DIR, 'sdwan_policy.yaml')


class PolicyEngine:
    """
    SD-WAN Policy Engine.
    Dựa trên trạng thái 5 paths và SLA requirements,
    chọn path tốt nhất cho mỗi traffic class.
    """

    def __init__(self, policy_path: str = _DEFAULT_POLICY_PATH):
        self.policy_path = policy_path
        self.policy      = self._load_policy()
        logger.info(f'PolicyEngine initialized from {policy_path}')

    def _load_policy(self) -> dict:
        """Đọc sdwan_policy.yaml. Dùng empty dict nếu không tìm thấy."""
        try:
            with open(self.policy_path) as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f'Policy file not found: {self.policy_path}. Using defaults.')
            return {}
        except yaml.YAMLError as e:
            logger.error(f'Error parsing policy YAML: {e}')
            return {}

    def reload(self):
        """Tải lại policy từ file (hot reload)."""
        self.policy = self._load_policy()
        logger.info('Policy reloaded')

    # ─────────────────────────────────────────
    # Core decision logic
    # ─────────────────────────────────────────

    def select_best_path(
        self,
        traffic_class: TrafficClass,
        available_paths: dict,        # {path_name: PathState}
    ) -> Optional[str]:
        """
        Chọn path tốt nhất cho traffic_class.

        Algorithm:
          1. Lọc paths đang UP
          2. Lọc paths đạt SLA requirements cho traffic_class
          3. Theo priority order (PATH_PRIORITY)
          4. Nếu không có path đạt SLA → fallback path UP có score thấp nhất
          5. Nếu không có path UP nào → None

        Returns: tên path ('MPLS', 'FIVEG', ...) hoặc None.
        """
        sla            = self._get_sla(traffic_class)
        priority_order = PATH_PRIORITY.get(traffic_class, list(available_paths.keys()))

        # Lọc paths UP
        up_paths = {
            name: state for name, state in available_paths.items()
            if state.status == PathStatus.UP
        }

        if not up_paths:
            #logger.warning(f'No UP paths for {traffic_class.value}!')
            
            return None

        # Lọc paths đạt SLA
        sla_paths = {
            name: state for name, state in up_paths.items()
            if state.meets_sla(
                sla['max_latency'],
                sla['max_loss'],
                sla['max_jitter']
            )
        }

        if sla_paths:
            # Chọn path có priority cao nhất trong SLA-compliant candidates
            for preferred in priority_order:
                if preferred in sla_paths:
                    logger.debug(
                        f'{traffic_class.value}: selected {preferred} '
                        f'(latency={sla_paths[preferred].latency_ms:.1f}ms, '
                        f'loss={sla_paths[preferred].loss_pct:.1f}%)'
                    )
                    return preferred

        # Fallback: không có path nào đạt SLA → chọn path UP có score thấp nhất
        logger.warning(
            f'{traffic_class.value}: No SLA-compliant path! '
            f'Falling back to best-effort.'
        )
        best_fallback = min(up_paths.items(), key=lambda x: x[1].score())
        return best_fallback[0]

    def evaluate_all_traffic(self, available_paths: dict) -> dict:
        """
        Đánh giá path tốt nhất cho tất cả traffic classes.
        Trả về: {TrafficClass: path_name_or_None}
        """
        return {
            tc: self.select_best_path(tc, available_paths)
            for tc in TrafficClass
        }

    def evaluate_to_site_decisions(
        self,
        available_paths: dict,
        src_sites: list = None,
        dst_site: str = 'DC',
    ) -> dict:
        """
        Quyết định path cho từng (src_site, dst_site) pair.
        Trả về: {(src_site, dst_site): path_name}

        Trong demo: tất cả traffic dùng chung 1 path
        (phân biệt theo traffic_class là optimization sau).
        """
        if src_sites is None:
            src_sites = ['BL', 'NT', 'HCM']

        # Chọn path "chủ đạo" dựa trên traffic class quan trọng nhất (VOIP)
        primary_path = self.select_best_path(TrafficClass.VOIP, available_paths)

        decisions = {}
        for src in src_sites:
            decisions[(src, dst_site)] = primary_path

        return decisions

    def _get_sla(self, traffic_class: TrafficClass) -> dict:
        """
        Lấy SLA requirements cho traffic_class.
        Override từ policy YAML nếu có.
        """
        base_sla = SLA_REQUIREMENTS.get(traffic_class, {
            'max_latency': 1000,
            'max_loss':    20.0,
            'max_jitter':  500,
        })

        # Kiểm tra override trong policy YAML
        overrides = self.policy.get('sla_overrides', {})
        tc_override = overrides.get(traffic_class.value, {})

        return {
            'max_latency': tc_override.get('max_latency', base_sla['max_latency']),
            'max_loss':    tc_override.get('max_loss',    base_sla['max_loss']),
            'max_jitter':  tc_override.get('max_jitter',  base_sla['max_jitter']),
        }

    def get_policy_summary(self) -> dict:
        """Summary policy cho REST API."""
        return {
            'version':       self.policy.get('version', '1.0'),
            'policy_file':   self.policy_path,
            'traffic_classes': {
                tc.value: {
                    'sla':      self._get_sla(tc),
                    'priority': PATH_PRIORITY.get(tc, []),
                }
                for tc in TrafficClass
            }
        }
