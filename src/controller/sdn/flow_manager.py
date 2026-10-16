"""
controller/sdn/flow_manager.py
Phase 14 - Quản lý Flow table và Switch Port states qua Faucet REST API.
"""
from __future__ import annotations#mới thêm dô sau
import json
import requests

FAUCET_API_BASE = 'http://localhost:9302'


class FlowManager:
    """
    Interface cho phép AI Engine và NOC Dashboard đọc/thay đổi trạng thái
    OpenFlow datapath và flow rules trên Faucet SDN Controller.
    """

    def __init__(self, api_base: str = FAUCET_API_BASE):
        self.api_base = api_base

    def get_dp_status(self) -> str:
        """Lấy metrics/trạng thái các Datapath từ Faucet API."""
        try:
            resp = requests.get(f'{self.api_base}/metrics', timeout=3)
            return resp.text
        except Exception as e:
            return f"Error connecting to Faucet API: {e}"

    def get_port_status(self, dp_id: str, port: int) -> dict:
        """Lấy trạng thái của 1 port trên Datapath."""
        try:
            resp = requests.get(
                f'{self.api_base}/port/status',
                params={'dp_id': dp_id, 'port': port},
                timeout=3
            )
            return resp.json()
        except Exception as e:
            return {'error': str(e)}

    def set_port_state(self, dp_id: str, port: int, state: bool) -> dict:
        """
        Khóa / Mở port trên switch bằng OpenFlow.
        state: True = UP, False = DOWN
        """
        try:
            resp = requests.post(
                f'{self.api_base}/port/state',
                json={
                    'dp_id': dp_id,
                    'port': port,
                    'status': 1 if state else 0
                },
                timeout=3
            )
            action = 'UP' if state else 'DOWN'
            print(f'[FlowManager] Set Datapath {dp_id} Port {port} → {action}')
            return resp.json()
        except Exception as e:
            print(f'[FlowManager] Failed to set port state: {e}')
            return {'status': 'error', 'message': str(e)}

    def reload_config(self) -> bool:
        """Yêu cầu Faucet reload lại file faucet.yaml."""
        try:
            resp = requests.post(f'{self.api_base}/reload', timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def get_flow_stats(self, dp_id: str) -> list | dict:
        """Lấy danh sách flow entries của 1 datapath."""
        try:
            resp = requests.get(
                f'{self.api_base}/flow_stats',
                params={'dp_id': dp_id},
                timeout=3
            )
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
