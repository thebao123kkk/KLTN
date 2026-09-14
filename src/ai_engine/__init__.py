# ai_engine/
# AI Fault-Recovery Engine — trọng tâm của luận văn.
# Pipeline: Telemetry → Anomaly Detection → RCA → Decision → Executor
# - telemetry/  : thu thập dữ liệu từ Ryu REST API + ping/iperf3
# - detection/  : Isolation Forest phát hiện bất thường (ML #1)
# - rca/        : Random Forest phân loại nguyên nhân gốc rễ (ML #2)
# - decision/   : rule-based engine ánh xạ root cause → hành động
# - executor/   : gọi REST API của Ryu / SD-WAN Controller để thực thi
# - main.py     : khởi động toàn bộ engine
