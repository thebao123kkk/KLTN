# Self-Healing Enterprise Network — Source Code

## Cấu trúc thư mục dự án

```text
d:\KLTN\src\
├── README.md
├── requirements.txt
├── topology/
│   ├── __init__.py        ← mô tả vai trò từng file sẽ viết
│   ├── sites/             ← BL, NT, HCM, DC topology
│   └── wan/               ← WAN emulation (5 path netem)
├── controller/
│   ├── sdn/               ← Ryu apps (flow, VLAN, QoS)
│   └── sdwan/             ← SD-WAN Controller tự viết (Python)
├── ai_engine/
│   ├── __init__.py        ← Pipeline: Telemetry→Detect→RCA→Decision→Execute
│   ├── telemetry/
│   ├── detection/         ← Isolation Forest
│   ├── rca/               ← Random Forest
│   ├── decision/          ← Rule-based engine
│   └── executor/          ← Gọi Ryu REST API / SD-WAN API
├── noc/                   ← NOC Dashboard — trung tâm giám sát toàn hệ thống
│   ├── backend/
│   │   ├── api/           ← REST API (network status, alerts, AI log, topology)
│   │   └── websocket/     ← Flask-SocketIO push real-time lên dashboard
│   └── frontend/
│       ├── templates/     ← HTML pages (dashboard, topology map, alert panel)
│       └── static/
│           ├── css/       ← Giao diện NOC (dark theme)
│           └── js/        ← Chart.js (metrics), vis-network (topology map)
├── traffic/               ← Traffic generator (iperf3, ping)
├── fault_injection/
│   ├── __init__.py        ← 12 scenario F01–F12 được liệt kê
│   └── scenarios/
├── evaluation/            ← Thu thập metrics, báo cáo
├── data/
│   ├── training/          ← Dataset huấn luyện ML
│   ├── models/            ← Model đã train (.pkl)
│   └── logs/
├── config/                ← YAML config (network, VLAN, AI params)
└── tests/
```


## Môi trường chạy
- Ubuntu 20.04 / 22.04
- Mininet 2.3+
- Open vSwitch 2.13+
- Python 3.9+
- Ryu SDN Framework
- Flask + Flask-SocketIO (NOC dashboard)

## Cài đặt
```bash
source .venv/bin/activate

pip install -r requirements.txt
```

## Thứ tự khởi động

### 1. Chạy Ryu SDN Controller
```bash
ryu-manager controller/sdn/l2_switch.py controller/sdn/flow_manager.py
```

### 2. Chạy SD-WAN Controller
```bash
python3 controller/sdwan/sdwan_controller.py
```

### 3. Chạy Mininet topology
```bash
sudo python3 topology/enterprise_topo.py
```

### 4. Chạy AI Fault-Recovery Engine
```bash
python3 ai_engine/main.py
```

### 5. Chạy NOC Dashboard
```bash
python3 noc/backend/app.py
# Truy cập: http://localhost:5050
```
