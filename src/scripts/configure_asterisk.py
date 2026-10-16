"""
scripts/configure_asterisk.py
Phase 11 - Khởi động VoIP Asterisk SIP Registrar Server trong DC_APP01 Namespace
"""

import os
import time
import subprocess

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'config', 'asterisk')


def configure_and_start_asterisk(dc_nodes):
    """
    Khởi động Asterisk SIP Server trong Namespace DC_APP01 (10.100.20.11).
    """
    app01 = dc_nodes['hosts']['DC_APP01']
    sip_conf = os.path.join(_CONFIG_DIR, 'sip.conf')
    ext_conf = os.path.join(_CONFIG_DIR, 'extensions.conf')

    # Copy config files
    app01.cmd('mkdir -p /tmp/asterisk')
    if os.path.exists(sip_conf):
        app01.cmd(f'cp {sip_conf} /tmp/asterisk/sip.conf')
    if os.path.exists(ext_conf):
        app01.cmd(f'cp {ext_conf} /tmp/asterisk/extensions.conf')

    # Thử khởi động Asterisk daemon
    res = app01.cmd('asterisk -C /tmp/asterisk/asterisk.conf 2>/dev/null || asterisk -C /etc/asterisk/asterisk.conf 2>/dev/null')

    # Nếu môi trường không cài gói asterisk binary, chạy Python SIP Echo/Registrar Server fallback
    if 'not found' in res or 'command not found' in res or app01.cmd('pgrep asterisk').strip() == '':
        _start_python_sip_fallback(app01)
    else:
        print('[PHASE 11] ✓ Asterisk SIP Server started on DC_APP01 (10.100.20.11:5060)')


def _start_python_sip_fallback(app01_host):
    """Fallback Python UDP SIP/RTP Echo Server khi chưa cài gói asterisk."""
    sip_server_code = """#!/usr/bin/env python3
import socket, threading, time

def handle_sip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 5060))
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            msg = data.decode('utf-8', errors='ignore')
            if 'REGISTER' in msg:
                resp = "SIP/2.0 200 OK\\r\\nCSeq: 1 REGISTER\\r\\nContent-Length: 0\\r\\n\\r\\n"
                sock.sendto(resp.encode('utf-8'), addr)
            elif 'INVITE' in msg:
                resp = "SIP/2.0 200 OK\\r\\nCSeq: 1 INVITE\\r\\nContent-Length: 0\\r\\n\\r\\n"
                sock.sendto(resp.encode('utf-8'), addr)
        except Exception:
            pass

def handle_rtp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 10000))
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            sock.sendto(data, addr)
        except Exception:
            pass

threading.Thread(target=handle_sip, daemon=True).start()
threading.Thread(target=handle_rtp, daemon=True).start()

while True:
    time.sleep(3600)
"""
    app01_host.cmd("cat > /tmp/sip_server_fallback.py << 'EOF'\n" + sip_server_code + "\nEOF")
    app01_host.cmd("python3 /tmp/sip_server_fallback.py &")
    print('[PHASE 11] ✓ VoIP SIP Server (Simulated Daemon) active on DC_APP01 (10.100.20.11:5060)')
