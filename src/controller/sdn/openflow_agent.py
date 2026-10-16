"""
controller/sdn/openflow_agent.py
Phase 14 - OpenFlow Agent giao tiếp với Faucet SDN Controller.
"""

from controller.sdn.faucet_controller import FaucetController
from controller.sdn.flow_manager import FlowManager


class OpenFlowAgent:
    """
    Agent đại diện cho SDN Controller subsystem.
    Cung cấp giao diện làm việc trực tiếp cho AI Engine và Orchestrator.
    """

    def __init__(self, config_path: str = 'config/faucet.yaml'):
        self.controller = FaucetController(config_path=config_path)
        self.flow_mgr = FlowManager()

    def start_sdn_services(self, switches: list[str]):
        """Khởi động Faucet process và kết nối danh sách OVS switches."""
        self.controller.start()
        self.controller.connect_ovs_switches(switches)

    def stop_sdn_services(self, switches: list[str]):
        """Disconnect switches và dừng Faucet controller."""
        self.controller.disconnect_ovs_switches(switches)
        self.controller.stop()

    def block_host_port(self, dp_id: str, port: int) -> bool:
        """AI Engine dùng để cách ly host vi phạm security policy."""
        res = self.flow_mgr.set_port_state(dp_id, port, state=False)
        return res.get('status') == 'ok' or res.get('status') == 200

    def unblock_host_port(self, dp_id: str, port: int) -> bool:
        """AI Engine dùng để bỏ cách ly host sau khi khôi phục."""
        res = self.flow_mgr.set_port_state(dp_id, port, state=True)
        return res.get('status') == 'ok' or res.get('status') == 200
