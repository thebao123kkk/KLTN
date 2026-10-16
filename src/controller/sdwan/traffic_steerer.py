"""
controller/sdwan/traffic_steerer.py
Phase 10 - Thực thi path switching trên GW hosts

Khi SD-WAN Controller quyết định chuyển path, TrafficSteerer
thực thi bằng cách thay đổi ip route trên GW hosts của từng site.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Subnet đích của mỗi site (traffic ra khỏi site sẽ dùng route này)
SITE_DESTINATIONS = {
    'BL':  '10.10.0.0/16',
    'NT':  '10.20.0.0/16',
    'HCM': '10.30.0.0/16',
    'DC':  '10.100.0.0/16',
}


class TrafficSteerer:
    """
    Thực thi route changes trên Mininet GW hosts để steer traffic.
    Mỗi site → DC có thể đi qua 1 trong 5 WAN paths.
    """

    def __init__(self, mininet_gws: dict, wan_profile: dict = None):
        """
        mininet_gws: {site_code: mininet_host_object}
          VD: {'BL': bl_gw, 'NT': nt_dist01, 'HCM': hcm_dist01, 'DC': dc_sp_gw}

        wan_profile: đặc tính paths, load từ wan_paths.yaml
          VD: {'MPLS': {'subnet': '172.16.10', ...}, ...}
        """
        self.gws          = mininet_gws
        self.wan_profile  = wan_profile or self._load_wan_profile()
        self.current_paths: dict[tuple, str] = {}   # (from, to) → path_name
        self._history: list[dict] = []

    def _load_wan_profile(self) -> dict:
        """Load wan_paths.yaml."""
        import yaml, os
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'wan_paths.yaml'
        )
        try:
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
            return cfg.get('paths', {})
        except FileNotFoundError:
            logger.warning('wan_paths.yaml not found, using empty profile')
            return {}

    # ─────────────────────────────────────────
    # Steer operations
    # ─────────────────────────────────────────

    def steer_traffic(self, from_site: str, to_site: str, path_name: str) -> bool:
        """
        Chuyển traffic từ from_site → to_site qua path_name.

        Implementation:
          1. Tính via_ip từ path subnet + to_site octet
          2. Xóa route cũ
          3. Cài route mới

        Trả về: True nếu thành công.
        """
        if from_site not in self.gws:
            logger.error(f'Unknown site: {from_site}')
            return False

        gw = self.gws[from_site]
        dst_subnet = SITE_DESTINATIONS.get(to_site)
        if not dst_subnet:
            logger.error(f'Unknown destination site: {to_site}')
            return False

        via_ip = self._get_via_ip(to_site, path_name)
        if not via_ip:
            logger.error(f'Cannot resolve via IP for {to_site} on path {path_name}')
            return False

        # Xóa route cũ
        gw.cmd(f'ip route del {dst_subnet} 2>/dev/null')

        # Cài route mới
        result = gw.cmd(f'ip route add {dst_subnet} via {via_ip} 2>&1')
        if 'Error' in result or 'error' in result:
            # Thử replace nếu route đã tồn tại
            gw.cmd(f'ip route replace {dst_subnet} via {via_ip} 2>/dev/null')

        old_path = self.current_paths.get((from_site, to_site), 'N/A')
        self.current_paths[(from_site, to_site)] = path_name

        event = {
            'timestamp':  time.time(),
            'from_site':  from_site,
            'to_site':    to_site,
            'old_path':   old_path,
            'new_path':   path_name,
            'via_ip':     via_ip,
        }
        self._history.append(event)
        if len(self._history) > 500:
            self._history.pop(0)

        if old_path != path_name:
            logger.info(
                f'[Steerer] {from_site}→{to_site}: '
                f'{old_path} → {path_name} (via {via_ip})'
            )

        return True

    def steer_all_to_path(self, path_name: str,
                           src_sites: list = None,
                           dst_site: str = 'DC') -> dict:
        """
        Chuyển tất cả src_sites → dst_site qua path_name.
        Trả về: {(from, to): success_bool}
        """
        if src_sites is None:
            src_sites = [s for s in self.gws if s != dst_site]

        results = {}
        for from_site in src_sites:
            ok = self.steer_traffic(from_site, dst_site, path_name)
            results[(from_site, dst_site)] = ok

        return results

    def apply_decisions(self, decisions: dict) -> dict:
        """
        Áp dụng dict quyết định: {(from, to): path_name}.
        Trả về: {(from, to): success_bool}
        """
        results = {}
        for (from_site, to_site), path_name in decisions.items():
            if path_name:
                results[(from_site, to_site)] = self.steer_traffic(
                    from_site, to_site, path_name
                )
        return results

    def get_current_paths(self) -> dict:
        """Trả về routing state hiện tại."""
        return dict(self.current_paths)

    def get_history(self, limit: int = 50) -> list:
        """Lấy steering history."""
        return list(self._history[-limit:])

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────

    def _get_via_ip(self, to_site: str, path_name: str) -> Optional[str]:
        """
        Tính via_ip: IP của to_site GW trên WAN path.
        VD: DC trên MPLS = 172.16.10.4
        """
        profile = self.wan_profile.get(path_name, {})
        subnet  = profile.get('subnet')
        if not subnet:
            return None

        # site_octets từ wan_paths.yaml
        import yaml, os
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'wan_paths.yaml'
        )
        try:
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
            octet = cfg.get('site_octets', {}).get(to_site, 4)
        except Exception:
            octets = {'BL': 1, 'NT': 2, 'HCM': 3, 'DC': 4}
            octet  = octets.get(to_site, 4)

        return f'{subnet}.{octet}'

    def verify_route(self, from_site: str, dst_subnet: str) -> Optional[str]:
        """
        Xác minh route hiện tại của from_site đến dst_subnet.
        Trả về via_ip string hoặc None.
        """
        gw = self.gws.get(from_site)
        if not gw:
            return None

        result = gw.cmd(f'ip route get {dst_subnet.split("/")[0]} 2>/dev/null')
        # Parse "via X.X.X.X"
        import re
        match = re.search(r'via (\d+\.\d+\.\d+\.\d+)', result)
        return match.group(1) if match else None
