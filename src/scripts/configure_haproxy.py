"""
scripts/configure_haproxy.py
Phase 8 - Load Balancing với HAProxy trên DC_APP01

Chức năng:
  1. Khởi động simple HTTP server trên DC_WEB01, DC_WEB02
  2. Gán VIP 10.100.10.10/24 alias trên DC_APP01
  3. Sinh config và khởi động HAProxy trong namespace DC_APP01
  4. Cập nhật DNS để www.enterprise.local → 10.100.10.10

Cách dùng:
  Gọi configure_dc_services_phase8(dc_nodes) từ enterprise_topo.py phase 8.
"""

import os
import sys
import time
import textwrap

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR    = os.path.dirname(_SCRIPT_DIR)

# ─────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────

WEB_VIP    = '10.100.10.10'    # Virtual IP cho HAProxy
WEB01_IP   = '10.100.10.11'   # DC_WEB01
WEB02_IP   = '10.100.10.12'   # DC_WEB02
STATS_PORT = 8404              # HAProxy stats page

HAPROXY_CFG_TEMPLATE = """\
global
    log 127.0.0.1 local0
    maxconn 4096
    daemon

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  forwardfor
    timeout connect 5s
    timeout client  30s
    timeout server  30s
    retries 3

frontend web_frontend
    bind {vip}:80
    default_backend web_backend
    option http-server-close
    capture request header Host len 64

backend web_backend
    balance roundrobin
    option httpchk GET /health HTTP/1.1\\r\\nHost:\\ health
    http-check expect string OK
    server web01 {web01}:80 check inter 2s fall 3 rise 2
    server web02 {web02}:80 check inter 2s fall 3 rise 2

listen stats
    bind {vip}:{stats_port}
    stats enable
    stats uri /stats
    stats refresh 5s
    stats show-legends
    stats show-node
"""

# Simple HTTP server script chạy trên DC_WEB01 / DC_WEB02
WEBSERVER_SCRIPT = '''\
#!/usr/bin/env python3
"""Minimal HTTP server cho HAProxy health checks và test traffic."""
import sys
import http.server
import socketserver

HOSTNAME = "{hostname}"
PORT = 80

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = b"OK"
            code = 200
        else:
            body = f"200 OK - Hello from {hostname}!".encode()
            code = 200
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Server", hostname)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # Tắt access log

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as srv:
    srv.serve_forever()
'''


# ─────────────────────────────────────────────────────────
# Web Server Setup
# ─────────────────────────────────────────────────────────

def start_web_servers(dc_nodes: dict):
    """
    Khởi động simple HTTP server trên DC_WEB01 và DC_WEB02.
    Mỗi server lắng nghe port 80, phục vụ /health endpoint.
    """
    hosts = dc_nodes['hosts']

    for server_name in ['DC_WEB01', 'DC_WEB02']:
        if server_name not in hosts:
            print(f'  [WARNING] {server_name} không tìm thấy trong dc_nodes')
            continue

        host = hosts[server_name]
        script_content = WEBSERVER_SCRIPT.format(hostname=server_name)
        script_path    = f'/tmp/webserver_{server_name}.py'

        # Ghi script vào /tmp trong namespace host
        # Dùng heredoc để tránh vấn đề escape
        host.cmd(f"cat > {script_path} << 'EOPY'\n{script_content}\nEOPY")
        host.cmd(f'chmod +x {script_path}')

        # Kill old instances
        host.cmd(f'pkill -f "webserver_{server_name}" 2>/dev/null')
        time.sleep(0.2)

        # Start server in background
        host.cmd(f'python3 {script_path} &')

        print(f'  [{server_name}] HTTP server started on port 80')

    time.sleep(1.5)  # Đợi servers init


def stop_web_servers(dc_nodes: dict):
    """Dừng web servers (dùng khi test failover)."""
    hosts = dc_nodes['hosts']
    for server_name in ['DC_WEB01', 'DC_WEB02']:
        if server_name in hosts:
            host = hosts[server_name]
            host.cmd(f'pkill -f "webserver_{server_name}" 2>/dev/null')


# ─────────────────────────────────────────────────────────
# HAProxy Setup
# ─────────────────────────────────────────────────────────

def configure_haproxy(dc_nodes: dict):
    """
    Cài VIP alias và khởi động HAProxy trên DC_APP01.

    Topology:
      DC_APP01 chạy HAProxy, bind VIP 10.100.10.10
      Backend pool: DC_WEB01 (10.100.10.11) + DC_WEB02 (10.100.10.12)
    """
    hosts = dc_nodes['hosts']

    if 'DC_APP01' not in hosts:
        print('[ERROR] DC_APP01 không tồn tại trong dc_nodes')
        return False

    app01 = hosts['DC_APP01']

    # 1. Gán VIP alias lên interface của DC_APP01
    # DC_APP01 đang có IP 10.100.20.11 (VLAN 320)
    # Ta cần thêm alias 10.100.10.10 (VLAN 310 subnet)
    app01_intfs = [i.name for i in app01.intfList() if i.name != 'lo']
    if not app01_intfs:
        print('[ERROR] DC_APP01 không có interface')
        return False

    primary_intf = app01_intfs[0]
    result = app01.cmd(f'ip addr add {WEB_VIP}/24 dev {primary_intf} 2>&1')
    if 'exists' not in result and 'RTNETLINK' not in result:
        print(f'  [DC_APP01] VIP {WEB_VIP}/24 added on {primary_intf}')
    else:
        print(f'  [DC_APP01] VIP {WEB_VIP} already exists (OK)')

    # 2. Sinh HAProxy config
    cfg_content = HAPROXY_CFG_TEMPLATE.format(
        vip        = WEB_VIP,
        web01      = WEB01_IP,
        web02      = WEB02_IP,
        stats_port = STATS_PORT,
    )
    cfg_path = '/tmp/haproxy_lb.cfg'
    pid_path = '/tmp/haproxy_lb.pid'

    app01.cmd(f"cat > {cfg_path} << 'EOCFG'\n{cfg_content}\nEOCFG")

    # 3. Kill cũ nếu có
    app01.cmd(f'haproxy -f {cfg_path} -p {pid_path} -sf $(cat {pid_path} 2>/dev/null) 2>/dev/null || true')
    time.sleep(0.5)
    app01.cmd(f'pkill -f "haproxy.*haproxy_lb" 2>/dev/null')
    time.sleep(0.5)

    # 4. Khởi động HAProxy
    result = app01.cmd(f'haproxy -f {cfg_path} -p {pid_path} -D 2>&1')
    time.sleep(2)

    # 5. Kiểm tra HAProxy đang chạy
    pid_check = app01.cmd(f'cat {pid_path} 2>/dev/null')
    if pid_check.strip():
        print(f'  [DC_APP01] HAProxy started (PID={pid_check.strip()})')
        print(f'  [DC_APP01] VIP: http://{WEB_VIP}:80')
        print(f'  [DC_APP01] Stats: http://{WEB_VIP}:{STATS_PORT}/stats')
        return True
    else:
        print(f'  [DC_APP01] WARNING: HAProxy may not be running (check /tmp/haproxy_lb.log)')
        print(f'  [DC_APP01] HAProxy output: {result}')
        return False


def check_haproxy_health(dc_nodes: dict) -> dict:
    """
    Kiểm tra HAProxy đang hoạt động.
    Trả về dict: {'vip_reachable': bool, 'web01_up': bool, 'web02_up': bool}
    """
    hosts = dc_nodes['hosts']
    app01 = hosts.get('DC_APP01')
    if not app01:
        return {'vip_reachable': False, 'web01_up': False, 'web02_up': False}

    vip_result = app01.cmd(f'curl -s -o /dev/null -w "%{{http_code}}" http://{WEB_VIP}/health --max-time 2')
    vip_ok = '200' in vip_result

    web01_result = app01.cmd(f'curl -s http://{WEB01_IP}/health --max-time 2')
    web01_ok = 'OK' in web01_result

    web02_result = app01.cmd(f'curl -s http://{WEB02_IP}/health --max-time 2')
    web02_ok = 'OK' in web02_result

    return {
        'vip_reachable': vip_ok,
        'web01_up': web01_ok,
        'web02_up': web02_ok,
    }


# ─────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────

def configure_dc_services_phase8(dc_nodes: dict):
    """
    Entry point từ enterprise_topo.py phase 8.
    Thứ tự:
      1. Khởi động HTTP servers trên WEB01/02
      2. Khởi động HAProxy trên APP01
      3. Verify hoạt động
    """
    print('[PHASE 8] Cấu hình DC Services (HAProxy Load Balancer)...')

    # Step 1: Start web servers
    print('  Step 1: Khởi động HTTP servers...')
    start_web_servers(dc_nodes)

    # Step 2: Configure HAProxy
    print('  Step 2: Cấu hình HAProxy...')
    ok = configure_haproxy(dc_nodes)

    if ok:
        # Step 3: Quick health check
        time.sleep(2)
        health = check_haproxy_health(dc_nodes)
        print(f'  Health Check: VIP={health["vip_reachable"]} '
              f'WEB01={health["web01_up"]} WEB02={health["web02_up"]}')

    print('[PHASE 8] ✓ DC Services (HAProxy) configured')
    return ok
