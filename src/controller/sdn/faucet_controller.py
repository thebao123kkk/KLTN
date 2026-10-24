"""
controller/sdn/faucet_controller.py
Phase 14 - Quản lý Faucet SDN Controller process và OVS Switch OpenFlow bindings.
"""

import os
import subprocess
import time
import shutil

FAUCET_CONFIG_PATH = '/tmp/faucet.yaml'
FAUCET_LOG_PATH    = '/tmp/faucet.log'
FAUCET_PORT        = 6653  # OpenFlow TCP Port
FAUCET_API_PORT    = 9302  # Faucet REST / Prometheus API Port


class FaucetController:
    """
    Quản lý Faucet Controller process và kết nối các OVS switches
    trong topology Mininet với Faucet SDN Controller.
    """

    def __init__(self, config_path: str = 'config/faucet.yaml'):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.isabs(config_path):
            config_path = os.path.join(base_dir, config_path)
        self.config_path = config_path
        self.process = None

    def prepare_config(self):
        """Copy faucet.yaml vào /tmp/ để Faucet daemon đọc."""
        if os.path.exists(self.config_path):
            shutil.copy(self.config_path, FAUCET_CONFIG_PATH)
            print(f'[Faucet] Config copied from {self.config_path} to {FAUCET_CONFIG_PATH}')
        else:
            print(f'[Faucet] Warning: Config file {self.config_path} not found!')

    def start(self):
        """Khởi động Faucet SDN Controller process."""
        self.prepare_config()

        env = os.environ.copy()
        env['FAUCET_CONFIG'] = FAUCET_CONFIG_PATH
        env['FAUCET_LOG']    = FAUCET_LOG_PATH

        try:
            self.process = subprocess.Popen(
                ['faucet', '--ryu-ofp-tcp-listen-port', str(FAUCET_PORT)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)

            if self.process.poll() is not None:
                print(f'[Faucet] Failed to launch faucet executable. Check {FAUCET_LOG_PATH}')
            else:
                print(f'[Faucet] Started Faucet Controller (PID={self.process.pid}, OF_Port={FAUCET_PORT})')
        except FileNotFoundError:
            print('[Faucet] Faucet executable not installed in system path. Starting integrated Telemetry Exporter (:9302, :9303)...')
            exporter_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telemetry_exporter.py')
            try:
                self.process = subprocess.Popen([sys.executable, exporter_script])
                time.sleep(1)
                print('[Faucet] Telemetry Exporters active on ports 9302 and 9303.')
            except Exception as e:
                print(f'[Faucet] Could not start telemetry exporter: {e}')

    def stop(self):
        """Ngừng Faucet process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                pass
            print('[Faucet] Controller stopped.')

    def connect_ovs_switches(self, switch_names: list[str], controller_ip: str = '127.0.0.1'):
        """
        Gán OpenFlow controller TCP endpoint và OpenFlow 1.3 cho danh sách OVS switches.
        """
        for sw_name in switch_names:
            try:
                subprocess.run([
                    'ovs-vsctl', 'set-controller', sw_name,
                    f'tcp:{controller_ip}:{FAUCET_PORT}'
                ], check=True, capture_output=True)
                subprocess.run([
                    'ovs-vsctl', 'set', 'bridge', sw_name,
                    'protocols=OpenFlow13'
                ], check=True, capture_output=True)
                print(f'[Faucet] Connected {sw_name} → tcp:{controller_ip}:{FAUCET_PORT} (OF13)')
            except Exception as e:
                print(f'[Faucet] Failed to set controller on {sw_name}: {e}')

    def disconnect_ovs_switches(self, switch_names: list[str]):
        """Xóa controller binding khỏi OVS switches, đưa về standalone mode."""
        for sw_name in switch_names:
            try:
                subprocess.run(['ovs-vsctl', 'del-controller', sw_name], check=True, capture_output=True)
                print(f'[Faucet] Disconnected {sw_name} from Faucet controller.')
            except Exception as e:
                print(f'[Faucet] Failed to disconnect {sw_name}: {e}')
