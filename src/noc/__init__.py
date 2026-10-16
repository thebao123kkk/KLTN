# noc/
# Network Operations Center — Dashboard giám sát trung tâm.
#
# Đây là giao diện web hiển thị real-time toàn bộ trạng thái hệ thống:
#   - Topology mạng (SDN LAN + SD-WAN WAN paths)
#   - Telemetry metrics từng node/link (latency, loss, throughput)
#   - Alert khi AI phát hiện anomaly
#   - Log quyết định và hành động khắc phục của AI Engine
#   - Trạng thái 5 WAN transport path
#   - Recovery history & MTTR dashboard
#
# Stack:
#   backend/   → Flask + Flask-SocketIO (REST API + WebSocket push)
#   frontend/  → HTML/CSS/JS thuần (Chart.js, vis-network topology map)
#
# Chạy NOC:
#   python3 noc/backend/app.py
#   Truy cập: http://localhost:5050
