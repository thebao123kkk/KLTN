# noc/backend/websocket/
# WebSocket server dùng Flask-SocketIO để push real-time update lên dashboard.
# - events.py   : định nghĩa các event (telemetry_update, alert_new, recovery_done)
# - broadcaster.py : vòng lặp đọc data từ AI Engine và broadcast tới tất cả client
