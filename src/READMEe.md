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
python3 -m .venv venv

source .venv/bin/activate

pip install -r requirements.txt
```

## Thứ tự khởi động

### 1. Chạy Ryu SDN Controller
```bash
ryu-manager controller/sdn/flow_manager.py
```

### 2. Chạy SD-WAN Controller
```bash
python3 controller/sdwan/sdwan_controller.py
```

### 3. Chạy Mininet topology
```bash
sudo python3 topology/enterprise_topo.py

sudo -E /home/baobao/KLTN/KLTN/src/.venv/bin/python3 topology/enterprise_topo.py

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

---

## 6. Chạy Thử Nghiệm Telemetry & Thu Thập Dataset ML

Phân hệ Telemetry thu thập 8 chỉ số trạng thái mạng ($s_t \in \mathbb{R}^8$), bóc tách nhãn sự cố ($\phi_t$) và phân tích siêu dữ liệu ngữ cảnh (Context Metadata) phục vụ giám sát thời gian thực và huấn luyện các mô hình AI/ML.

### 6.1 Khởi động Telemetry Exporters
Khởi chạy dịch vụ Exporter cung cấp metrics chuẩn Prometheus trên các cổng `:9302` (Faucet/Controller process) và `:9303` (Gauge/OVS datapath & port status):
```bash
# Chạy background trong môi trường Mininet/SDN
python3 controller/sdn/telemetry_exporter.py &
```

> **Lưu ý**: Có thể kiểm tra nhanh các endpoint bằng lệnh:
> ```bash
> curl -s http://localhost:9303/metrics | head -n 20
> curl -s http://localhost:9302/metrics | head -n 20
> ```

---

### 6.2 Chạy Telemetry Collector (Chế độ độc lập / Giám sát liên tục)
Cào dữ liệu định kỳ mỗi 2 giây hoặc 10 giây (mặc định cấu hình), tự động ghi ra `data/sdn_telemetry_dataset.csv` và `data/telemetry_log.jsonl`:
```bash
# Chế độ tự động dò tìm Exporter/Prometheus (khuyên dùng):
python3 telemetry_collector.py --cycles 10 --interval 2 --mode auto

# Hoặc chế độ đọc trực tiếp từ Exporter:
python3 telemetry_collector.py --cycles 10 --interval 2 --mode direct
```

---

### 6.3 Chạy Kiểm Thử Độ Nhạy & Khả Năng Bắt Lỗi Telemetry
Kịch bản kiểm thử toàn diện khả năng phát hiện lỗi của Telemetry khi tiêm các kịch bản thực tế (Access down, Link down, OSPF flap, Congestion...):
```bash
# Chạy với quyền sudo để cho phép tác động vào kernel netem và OVS interface
sudo python3 tests/test_fault_scenarios.py
```
Script sẽ kiểm tra:
- Độ trễ phản hồi của Telemetry ($p_{\text{down}}$, $f_{\text{conn}}$, $f_{\text{sent}}$).
- Tính chính xác của Context Metadata (`target_dpid`, `target_port`, `error_cookie`).
- Đảm bảo hệ thống tự động khôi phục mạng hoàn toàn (`recover_all`) sau khi kiểm thử.

---

### 6.4 Chạy Tự Động Cào Đủ 7/7 Nhãn Sự Cố Cho Dataset Huấn Luyện
Script tự động phối hợp giữa Phân hệ Tiêm lỗi (`fault_injector`) và Bộ thu thập Telemetry (`telemetry_collector`) để tạo ra bộ dữ liệu cân bằng hoàn hảo cả 7 nhãn:
1. `NONE` (Mạng bình thường)
2. `SOFT_WARNING` (F03 - OSPF Failure)
3. `TEMP_WARNING` (F10 - VoIP Jitter/Delay)
4. `FLOW_ERROR` (F09 - WAN Congestion)
5. `PORT_FAULT` (F01 - Access Link Down)
6. `LINK_FAULT` (F02 - Distribution Trunk Down)
7. `FAUCET_RELOAD` (F12 - Multi-Metric / Controller Flapping)

**Lệnh thực thi (Bắt buộc dùng `sudo`):**
```bash
# Thu thập 3 mẫu cho mỗi nhãn (tổng cộng 21 dòng cân bằng, chu kỳ 2s):
sudo python3 scripts/collect_dataset_all_labels.py --target-per-label 3 --mode auto

# Chế độ kiểm tra nhanh không can thiệp mạng thật (Dry-run):
python3 scripts/collect_dataset_all_labels.py --target-per-label 3 --dry-run
```

**Kiểm tra kết quả dataset thu được:**
```bash
head -n 25 data/sdn_telemetry_dataset.csv
```

---

### 6.5 Chạy Bộ Kiểm Thử Đơn Vị (Unit Tests)
Kiểm tra tính toàn vẹn của toàn bộ phân hệ Telemetry (14 test cases: Prometheus client fallback, Parser context, Direct scraper, State Vector Assembler):
```bash
python3 tests/test_telemetry.py
```
Kết quả mong đợi: `Ran 14 tests in ... - OK`.

