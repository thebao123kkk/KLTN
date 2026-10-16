# Kế Hoạch Chi Tiết Xây Dựng Hệ Thống Tự Phục Hồi SD-WAN (Closed-Loop Self-Healing Framework)

> **Tài liệu tham chiếu gốc**: [cau_truc_tu_phuc_hoi_sdwan.md](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/cau_truc_tu_phuc_hoi_sdwan.md)  
> **Mục tiêu**: Xây dựng hoàn chỉnh chu trình điều khiển khép kín (MAPE-K Closed Loop) kết hợp **AI/RL Agent (PPO)** và **Mô hình Dự báo Tiền phát (Holt-Winters/LSTM + QoE Regression)** trên nền tảng Mininet, Faucet SDN và SD-WAN Controller.

---

## 📌 Tổng Quan Lộ Trình Triển Khai (Roadmap Overview)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        LỘ TRÌNH 6 GIAI ĐOẠN TRIỂN KHAI                                 │
├──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬─────────────┤
│ GIAI ĐOẠN 1  │ GIAI ĐOẠN 2  │ GIAI ĐOẠN 3  │ GIAI ĐOẠN 4  │ GIAI ĐOẠN 5  │ GIAI ĐOẠN 6 │
│ Thu thập     │ Phân tách    │ Xây dựng     │ Động cơ      │ Kiểm thử     │ Đánh giá    │
│ Telemetry    │ 2 tầng Macro │ Bộ não AI    │ Thực thi &   │ Kịch bản &   │ & Báo cáo   │
│ & Giám sát   │ & Micro      │ Tiền/Hậu     │ Ghép nối     │ Tích hợp     │ Luận văn    │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴─────────────┘
```

---

## GIAI ĐOẠN 1: Lớp Giám Sát & Thu Thập Dữ Liệu (Telemetry & Monitoring Layer)

Mục tiêu giai đoạn này là số hóa toàn bộ trạng thái Data Plane (cổng switch, luồng OpenFlow, chất lượng link WAN) và Control Plane thành chuỗi thời gian (time-series) chuẩn Prometheus.

```
                   Data Plane (Switches s1-s3 & WAN Edges)
                                      │
               ┌──────────────────────┼──────────────────────┐
               ▼                      ▼                      ▼
      SDN Switch Exporter    SD-WAN Path Prober     Node / System Exporter
      (of_port_status,       (Ping / UDP Probe      (CPU %, RAM RSS/VMS,
       of_flow_errors)        Latency, Jitter, Loss) Datapath Handshake)
               │                      │                      │
               └──────────────────────┼──────────────────────┘
                                      │ (Scrape Cycle: 5s)
                                      ▼
                           Prometheus Server (TSDB)
```

### 1.1. Xây dựng các Telemetry Collectors
Vị trí thư mục: `src/ai_engine/telemetry/`

1. **SDN Switch & Port Exporter (`sdn_exporter.py`)**:
   - Giao tiếp với Faucet REST API qua [flow_manager.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/controller/sdn/flow_manager.py) (cổng 9302).
   - Thu thập các chỉ số OpenFlow:
     - Trạng thái cổng: `of_port_status{dp_id="0x1", port="2"} = 0|1` (0 = DOWN, 1 = UP).
     - Bộ đếm gói tin / bytes: `of_port_rx_bytes`, `of_port_tx_bytes`, `of_port_rx_packets`, `of_port_tx_packets`.
     - Bộ đếm lỗi: `of_port_errors_total{dp_id="...", port="..."}`, `of_flow_errors_total{dp_id="...", cookie="..."}`.

2. **SD-WAN Path Prober (`wan_telemetry.py`)**:
   - Tích hợp với `PathMonitor` trong [path_monitor.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/controller/sdwan/path_monitor.py).
   - Đo đạc chất lượng 5 đường truyền WAN (MPLS, Internet, LTE, 5G, VPN) giữa các Gateway (BL, NT, HCM, DC) theo chu kỳ 1–2 giây:
     - `sdwan_path_latency_ms{path="MPLS_BL_HCM"}`
     - `sdwan_path_jitter_ms{path="MPLS_BL_HCM"}`
     - `sdwan_path_loss_ratio{path="MPLS_BL_HCM"}`
     - `sdwan_path_bandwidth_util{path="MPLS_BL_HCM"}`

3. **Node & Controller Health Exporter (`node_exporter.py`)**:
   - Đo tài nguyên phần cứng của tiến trình Faucet Controller và SD-WAN Controller:
     - CPU utilization: `controller_cpu_percent` ($C_{cpu}$).
     - Bộ nhớ RAM Resident/Virtual: `controller_mem_rss_mb`, `controller_mem_vms_mb` ($C_{res\_mem}, C_{virt\_mem}$).
     - Trạng thái kết nối OpenFlow Datapath: `faucet_dp_status{dp_name="s3"} = 0|1` ($f_{conn}, f_{disc}$).

### 1.1.1 Gom nhóm Folder Telemetry theo chức năng để dễ theo dõi
Cấu trúc phân hệ [`ai_engine/telemetry/`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry) đã được tổ chức lại gọn gàng, loại bỏ các file trùng lặp nằm phân tán ở thư mục gốc:

```text
src/ai_engine/telemetry/
├── __init__.py                     # Interface re-export toàn bộ module (tương thích ngược 100%)
├── collector.py                    # Script điều phối chính (hỗ trợ single-run & auto-collect 10s)
├── exporters/                      # [NHÓM 1] Thu thập số liệu thô từ mạng & xuất Prometheus/API
│   ├── __init__.py
│   ├── sdn_exporter.py             # Port stats, error counters từ Faucet SDN Controller
│   ├── wan_exporter.py             # Active probing 5 WAN paths (Latency, Jitter, Loss, Bandwidth)
│   ├── node_exporter.py            # Tài nguyên Controller (CPU, RAM) & trạng thái Datapath switch
│   └── unified_server.py           # HTTP Server hợp nhất tất cả metrics (:9100/metrics & JSON API)
└── analysis/                       # [NHÓM 2] Biểu diễn và phân tích trạng thái mạng cho AI
    ├── __init__.py
    ├── feature_collector.py        # Vector trạng thái 8 chiều (s_t) & chuẩn hóa [0, 1] cho PPO
    └── context_parser.py           # Bộ định vị chính xác thiết bị sự cố (Switch, Port, Flow, WAN)
```

### 1.1.2. Sửa file Test: Chỉ giữ và lưu lại phần thu thập thông tin
Các file test trong [`tests/`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/tests) đã được tinh chỉnh loại bỏ hoàn toàn các kịch bản tiêm lỗi giả lập, chỉ tập trung kiểm tra thu thập thông tin và tự động lưu dữ liệu snapshot ra file JSON:

- **[`tests/test_feature_collector.py`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/tests/test_feature_collector.py)**:
  - `test_collect_state_vector_and_registry`: Thu thập Vector 8 chiều $s_t$ và Registry thiết bị.
  - `test_collect_raw_telemetry_metrics_and_save`: Thu thập metrics đầy đủ 3 phân hệ và lưu vào [`tests/collected_telemetry_snapshot.json`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/tests/collected_telemetry_snapshot.json).
  - `test_normalized_vector_for_ai`: Chuẩn hóa Vector về khoảng $[0, 1]$ cho mạng neural PPO.
- **[`tests/test_telemetry.py`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/tests/test_telemetry.py)**:
  - Kiểm tra thu thập số liệu thuần túy từ 4 thành phần: [`SDNExporter`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/exporters/sdn_exporter.py), [`WANTelemetryExporter`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/exporters/wan_exporter.py), [`NodeHealthExporter`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/exporters/node_exporter.py), [`UnifiedTelemetryService`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/exporters/unified_server.py).
  - Tự động lưu snapshot ra [`tests/collected_exporters_snapshot.json`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/tests/collected_exporters_snapshot.json).

---

### 1.1.3. Tự động thu thập dữ liệu mỗi 10 giây (Auto-Collect 10s - Comment sẵn sàng)
Đã bổ sung cơ chế thu thập nền định kỳ mỗi 10s (chạy trong background daemon thread kèm stop event an toàn) tại 2 vị trí:

1. **Trong class [`FeatureCollector`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/analysis/feature_collector.py#L118-L182)**:
   - Các phương thức `start_auto_collector(interval_seconds=10)` và `stop_auto_collector()` được viết hoàn chỉnh và comment lại.
2. **Trong [`ai_engine/telemetry/collector.py`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/collector.py#L57-L130)**:
   - Khối hàm `start_auto_collect(interval=10)` và `stop_auto_collect()` được comment lại kèm tùy chọn lưu snapshot JSON định kỳ mỗi 10 giây.
   - *Cách dùng sau này*: Chỉ cần bỏ dấu comment `#` và gọi `start_auto_collect()` hoặc chạy script với cờ `--auto`.


### 1.2. Cấu hình Prometheus Scraper Pipeline & Time-Series Buffer (Đã hoàn thành)
File cấu hình chuẩn Prometheus: [`config/prometheus.yml`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/config/prometheus.yml)
```yaml
global:
  scrape_interval: 10s       # Chu kỳ lấy mẫu 10s (phù hợp phản ứng nhanh SD-WAN)
  evaluation_interval: 10s
  scrape_timeout: 5s

scrape_jobs:
  - job_name: 'faucet_sdn'
    static_configs:
      - targets: ['127.0.0.1:9302']
  - job_name: 'sdwan_controller'
    static_configs:
      - targets: ['127.0.0.1:7070']
  - job_name: 'system_node'
    static_configs:
      - targets: ['127.0.0.1:9100']
```

#### 1.2.1. Giải pháp Thuần Python Zero-Docker: `TimeSeriesPipeline`
Module: [`src/ai_engine/telemetry/time_series_pipeline.py`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/time_series_pipeline.py)
Theo chuẩn các bài báo khoa học về SDN/SD-WAN Self-Healing và Traffic Steering, hệ thống không phụ thuộc vào cụm Docker hay daemon ngoài mà sử dụng **Pipeline đệm chuỗi thời gian In-Memory (Ring Buffer / Deque)**:
- **Chu kỳ cào**: Chạy nền (daemon thread an toàn) hoặc bước thủ công (`collect_step()`) mỗi 10 giây.
- **Cung cấp cho Mô hình Dự báo & Cân bằng tải**:
  - Hàm `get_time_series_matrix(metric_name, window_size, paths)`: Trích xuất ma trận 2D NumPy `shape=(window_size, num_paths)` (chuẩn float32) phục vụ mô hình **Holt-Winters / LSTM**.
  - Hàm `get_qoe_features(paths)`: Trích xuất Latency, Jitter, Loss và điểm ước tính MOS/QoE (1.0 - 4.5) phục vụ mô hình **QoE Regression** cân bằng tải nhận thức ứng dụng.
- **Cung cấp cho Mô hình Tự phục hồi**:
  - Hàm `get_current_state_vector(normalized=True)`: Trả về Vector trạng thái $s_t$ 8 chiều chuẩn hóa $[0, 1]$ cho **Tác tử PPO RL**.
- **Xuất / Nhập Snapshot**:
  - Lưu snapshot chuỗi thời gian ra [`tests/collected_pipeline_snapshot.json`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/tests/collected_pipeline_snapshot.json) và xuất Pandas DataFrame qua `get_history_dataframe()`.

#### 1.2.2. Kiểm thử xác thực tự động: [`tests/test_time_series_pipeline.py`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/tests/test_time_series_pipeline.py)
- `test_01_prometheus_yaml_configuration`: Kiểm tra cú pháp YAML chuẩn của Prometheus.
- `test_02_pipeline_step_collection`: Kiểm tra thu thập mẫu và đệm vào Ring Buffer.
- `test_03_time_series_matrix_for_load_balancing`: Kiểm tra trích xuất ma trận 2D `(10, 6)` cho AI dự báo.
- `test_04_qoe_features_extraction`: Kiểm tra trích xuất SLA và điểm MOS cho 6 đường WAN.
- `test_05_ppo_state_vector_and_snapshot`: Kiểm tra trích xuất vector $s_t$ và xuất snapshot JSON.
- `test_06_background_thread_start_stop`: Kiểm tra thread chạy ngầm và dừng an toàn.
*(Toàn bộ 6/6 test cases đạt 100% OK).*

---

## GIAI ĐOẠN 2: Bộ Phân Tách Ngữ Cảnh & Trích Xuất Đặc Trưng (Feature Collector & Context Parser)

Mục tiêu: Đưa dữ liệu thô từ Prometheus thành **Vector trạng thái 8 chiều ($s_t$)** cho tầng Macro và **Context Metadata** cho tầng Micro.

```
                      Prometheus TSDB Metrics
                                 │
                                 ▼
       ┌──────────────────────────────────────────────────┐
       │   Feature Collector & Context Parser Module      │
       └────────────────────────┬─────────────────────────┘
                                │
            ┌───────────────────┴───────────────────┐
            ▼                                       ▼
  TẦNG MACRO (Cho PPO Agent)              TẦNG MICRO (Cho Execution Engine)
  Vector s_t 8 Chiều:                     Incident Context Metadata:
  • C_cpu       : % CPU controller        • target_dpid       : "0x1"
  • C_res_mem   : % RAM resident          • target_port       : 2
  • C_virt_mem  : % RAM virtual           • error_flow_cookie : "0x10a"
  • f_sent      : Rate nạp flow           • affected_path_id  : "MPLS_BL_HCM"
  • f_err       : Đếm flow lỗi            • predicted_overflow: True/False
  • f_conn      : Đếm kết nối DP          • qoe_score         : 2.8 / 5.0
  • f_disc      : Đếm ngắt kết nối DP
  • P_down      : Đếm số port sập
```

### 2.1. Vector Trạng Thái 8 Chiều Macro ($s_t$)
File: `src/ai_engine/telemetry/feature_collector.py`
$$s_t = \left[ C_{cpu},\ C_{res\_mem},\ C_{virt\_mem},\ f_{sent},\ f_{err},\ f_{conn},\ f_{disc},\ P_{down} \right]^T$$
- Tất cả các giá trị đều được chuẩn hóa (normalize) về miền $[0, 1]$ trước khi nạp vào mạng Neural của Agent PPO.

### 2.2. Trích Xuất Micro Context Metadata
File: `src/ai_engine/telemetry/context_parser.py`
```python
@dataclass
class IncidentContext:
    timestamp: float
    target_dpid: Optional[str] = None          # Ví dụ: "0x000000000001" (NT_CORE)
    target_port: Optional[int] = None          # Ví dụ: 2
    error_flow_cookie: Optional[str] = None    # Ví dụ: "0x10a"
    affected_path_id: Optional[str] = None     # Ví dụ: "MPLS_BL_HCM"
    predicted_overflow: bool = False           # Bùng nổ băng thông dự báo trước
    qoe_score: float = 5.0                     # Điểm trải nghiệm hiện tại (1.0 - 5.0)
```

---

## GIAI ĐOẠN 3: Hiện Thực Hóa Bộ Não AI (AI Decision Engine)

Bộ não AI được chia thành **2 nhánh xử lý chuyên biệt**:

### 3.1. Nhánh 1: Cơ Chế Tự Phục Hồi Tiền Phát (Proactive / Predictive Self-Healing)
File: `src/ai_engine/decision/proactive_engine.py`

```
           Chuỗi Băng Thông (Bytes Sent 60s)        Chỉ số Mạng (Latency, Jitter, Loss)
                          │                                           │
                          ▼                                           ▼
             ┌─────────────────────────┐                 ┌─────────────────────────┐
             │  Holt-Winters / LSTM    │                 │  QoE Regression Model   │
             │  Traffic Predictor      │                 │  (ITU-T G.107 E-Model)  │
             └────────────┬────────────┘                 └────────────┬────────────┘
                          │                                           │
                 Dự báo Y_(t+20s)                             Điểm MOS VoIP/Video
                          │                                           │
                          ▼                                           ▼
             ┌─────────────────────────┐                 ┌─────────────────────────┐
             │  Dynamic Thresholding   │                 │     SLA Verification    │
             │  Y_(t+20s) > 85% Cap?   │                 │     MOS < 3.5 SLA?      │
             └────────────┬────────────┘                 └────────────┬────────────┘
                          │ (Trigger = True)                          │ (Trigger = True)
                          └─────────────────────┬─────────────────────┘
                                                │
                                                ▼
                               ┌─────────────────────────────────┐
                               │ Preemptive SD-WAN Steering      │
                               │ Điều hướng sớm luồng ưu tiên    │
                               │ sang 5G/Broadband trước sự cố   │
                               └─────────────────────────────────┘
```

1. **Mô-đun Dự báo Bùng nổ Lưu lượng (Traffic Forecasting)**:
   - Thuật toán: Holt-Winters Exponential Smoothing (hoặc LSTM 1-layer gọn nhẹ).
   - Đầu vào: Chuỗi dữ liệu `byte_count` cào mỗi 5 giây trong 60 giây qua.
   - Dự báo: Giá trị băng thông dự kiến trong $15 - 30$ giây tới ($\hat{Y}_{t+20s}$).
   - Logic Ngưỡng Động (Dynamic Thresholding):
     $$\text{Nếu } \hat{Y}_{t+20s} > 0.85 \times \text{Bandwidth\_Capacity} \implies \text{Phát tín hiệu Preemptive Steer}$$

2. **Mô-đun Đánh giá Trải nghiệm Ứng dụng (App-Aware QoE Model)**:
   - Dựa trên chuẩn ITU-T G.107 (E-Model rút gọn) tính điểm MOS từ $1.0$ đến $5.0$:
     $$R = 94.2 - 0.024 \times d - 0.11 \times (d - 177.3) \cdot \mathbb{I}_{d > 177.3} - I_e(loss, jitter)$$
     $$MOS = 1 + 0.035 R + R(R - 60)(100 - R) \cdot 7 \times 10^{-6}$$
   - Điều kiện kích hoạt:
     $$\text{Nếu } MOS_{VoIP} < 3.5 \text{ hoặc } Jitter > 30\text{ms} \implies \text{Phát tín hiệu Mid-session Flow Re-routing}$$

---

### 3.2. Nhánh 2: Cơ Chế Tự Phục Hồi Hậu Phát (Reactive - PPO RL Agent)
File: `src/ai_engine/decision/ppo_agent.py` và `network_env.py`

```
                                  Vector s_t (8 Chiều)
                                           │
                                           ▼
                           ┌───────────────────────────────┐
                           │   PPO Policy Network (MLP)    │
                           │   FC(64, ReLU) → FC(64, ReLU) │
                           │   → Softmax Output (4 Actions)│
                           └───────────────┬───────────────┘
                                           │
           ┌───────────────────┬───────────┴───────────┬───────────────────┐
           ▼                   ▼                       ▼                   ▼
     ┌───────────┐       ┌───────────┐           ┌───────────┐       ┌───────────┐
     │  a_t = 0  │       │  a_t = 1  │           │  a_t = 2  │       │  a_t = 3  │
     │  [No-op]  │       │[Reset Port│           │[Restart SW│       │ [Bespoke  │
     │           │       │           │           │/Datapath] │       │ Flow Heal]│
     └─────┬─────┘       └─────┬─────┘           └─────┬─────┘       └─────┬─────┘
           │                   │                       │                   │
   P_down=0, f_err=0       P_down > 0             f_disc > 0            f_err > 0
   Mạng ổn định            Cổng bị sập            hoặc C_cpu > 90%      Xung đột luồng
   Tránh phạt (-1)        Thưởng: +10             Thưởng: +20          Thưởng: +15
```

1. **Không gian Hành động (Action Space)**:
   - $a_t = 0$: **No-op** (Mạng bình thường, giữ nguyên hiện trạng).
   - $a_t = 1$: **Reset Ports** (Kích hoạt lại cổng vật lý/ảo bị down).
   - $a_t = 2$: **Restart Switch / Datapath** (Khởi tạo lại socket kết nối OpenFlow giữa switch và Faucet).
   - $a_t = 3$: **Bespoke Self-Heal** (Xóa luật OpenFlow lỗi và nạp lại quy tắc chuyển tiếp sạch).

2. **Hàm Thưởng / Phạt (Reward Function)**:
   $$R_t = \begin{cases}
   +10 & \text{khi phục hồi cổng thành công } (a_t=1 \text{ và } P_{down} \to 0) \\
   +20 & \text{khi khôi phục kết nối switch crash } (a_t=2 \text{ và } f_{disc} \to 0) \\
   +15 & \text{khi xóa luật hỏng và khôi phục flow } (a_t=3 \text{ và } f_{err} \to 0) \\
   0   & \text{mạng bình thường và chọn No-op } (a_t=0) \\
   -1  & \text{can thiệp thừa khi mạng không có sự cố } (a_t \in \{1,2,3\} \text{ khi lỗi}=0) \\
   -10 & \text{chọn sai hành động hoặc lỗi kéo dài qua nhiều chu kỳ}
   \end{cases}$$

3. **Môi trường Huấn luyện Giả lập (`network_env.py`)**:
   - Xây dựng lớp kế thừa `gym.Env` chứa mô hình động học mạng.
   - Tiêm 12 kịch bản lỗi ngẫu nhiên và huấn luyện mô hình PPO đạt hội tụ (Convergence) sau $\approx 50.000$ episodes.

---

## GIAI ĐOẠN 4: Lớp Thực Thi & Ghép Nối Điều Khiển (Execution Engine & Controller Binding)

Mục tiêu: Đóng vai trò **cầu nối ghép cặp (Binding Engine)** giữa Quyết định Vĩ mô ($a_t$) và Vị trí Vi mô (`IncidentContext`) để phát lệnh chính xác xuống Open vSwitch và SD-WAN Edge.

File: `src/ai_engine/executor/execution_engine.py`

```
  Quyết định Macro a_t             Incident Metadata Vi mô
       (Từ PPO)                   (Từ Context Parser)
           │                               │
           └───────────────┬───────────────┘
                           │
                           ▼
             ┌───────────────────────────┐
             │     EXECUTION ENGINE      │
             │   (Ghép nối a_t + Meta)   │
             └─────────────┬─────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌─────────────────────────────────┐ ┌─────────────────────────────────┐
│     Faucet OpenFlow Binding     │ │     SD-WAN Routing Binding      │
│ • OFPPC_PORT_DOWN / UP          │ │ • Linux Advanced Policy Routing │
│ • OFPFC_DELETE_STRICT (Cookie)  │ │ • ip rule / ip route steer      │
│ • Datapath Re-handshake         │ │ • DSCP Matching Steering        │
└────────────────┬────────────────┘ └────────────────┬────────────────┘
                 │                                   │
                 ▼                                   ▼
        OpenFlow Switches s1-s3              SD-WAN Edge Gateways
```

### 4.1. Bảng Ghép Nối Hành Động Thực Tế

| Nhóm | Quyết định AI | Metadata Nhận Được | Thao tác Thực thi Cụ thể | Hàm Thực thi trong Source |
| :--- | :--- | :--- | :--- | :--- |
| **Tiền phát P1** | Preemptive Steer | `path_src="BL", class="VoIP"` | Đổi bảng routing, gán luồng VoIP sang đường phụ 5G | `TrafficSteerer.steer_traffic()` |
| **Tiền phát P2** | Mid-session Switch | `flow="VoIP", new_path="Broadband"` | Cập nhật ip rule nexthop mà không ngắt session | `SDWANController.manual_steer()` |
| **Hậu phát R1** | $a_t = 1$ (Reset Port) | `target_dpid="0x1", target_port=2` | Gửi OpenFlow `PORT_MOD` hạ rồi nâng Port 2 trên Switch `s1` | `FlowManager.set_port_state()` |
| **Hậu phát R2** | $a_t = 3$ (Bespoke Heal) | `target_dpid="0x2", cookie="0x10a"` | Gửi OpenFlow `FLOW_MOD DELETE` xóa cookie và nạp lại rule sạch | `FlowManager.delete_flow()` |
| **Hậu phát R3** | $a_t = 2$ (Restart SW) | `target_dpid="0x3"` | Khởi động lại Datapath handshake với Faucet | `FaucetController.connect_ovs_switches()` |
| **Bình thường R4** | $a_t = 0$ (No-op) | `None` | Giữ nguyên hiện trạng, ghi log hệ thống ổn định | `Logger.info("System Healthy")` |

---

## GIAI ĐOẠN 5: Kế Hoạch Kiểm Thử Từng Phần Đến Toàn Diện (Testing & Validation Workflow)

Kế hoạch kiểm thử được thực thi theo 4 cấp độ tăng dần:

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                 CẤP ĐỘ 4: BENCHMARK HIỆU NĂNG                    │
  │ • MTTR phục hồi | • CPU/RAM Overhead | • VoIP MOS Preservation   │
  └────────────────────────────────▲─────────────────────────────────┘
                                   │
  ┌────────────────────────────────┴─────────────────────────────────┐
  │                 CẤP ĐỘ 3: KỊCH BẢN THỰC TẾ E2E                   │
  │ • 2 Kịch bản Tiền phát (P1, P2) | • 4 Kịch bản Hậu phát (R1-R4) │
  └────────────────────────────────▲─────────────────────────────────┘
                                   │
  ┌────────────────────────────────┴─────────────────────────────────┐
  │                 CẤP ĐỘ 2: TÍCH HỢP PHÂN HỆ                       │
  │ • Prometheus ↔ AI Engine | • AI Engine ↔ Faucet & SD-WAN API     │
  └────────────────────────────────▲─────────────────────────────────┘
                                   │
  ┌────────────────────────────────┴─────────────────────────────────┐
  │                 CẤP ĐỘ 1: KIỂM THỬ ĐƠN VỊ (UNIT)                 │
  │ • Feature Vector | • Context Parser | • Predictor | • PPO Model  │
  └──────────────────────────────────────────────────────────────────┘
```

### Bước 5.1: Kiểm Thử Đơn Vị (Unit Tests)
File kiểm thử: `tests/test_ai_units.py`
- [x] **Test 1 - Feature Vector Generator**: Kiểm tra dữ liệu Prometheus giả lập chuyển thành vector $s_t$ đúng 8 chiều, giá trị trong $[0, 1]$.
- [x] **Test 2 - Context Parser**: Kiểm tra bóc tách chính xác `target_dpid`, `target_port`, `cookie` từ log lỗi.
- [x] **Test 3 - Holt-Winters / LSTM Predictor**: Đưa chuỗi dữ liệu dốc đứng $\rightarrow$ Kiểm tra hàm dự báo kích hoạt ngưỡng $>85\%$.
- [x] **Test 4 - QoE Model**: Đưa $Latency=120\text{ms}, Jitter=40\text{ms}, Loss=3\% \rightarrow$ Kiểm tra $MOS < 3.5$.
- [x] **Test 5 - PPO Inference**: Kiểm tra mạng neural sinh action $a_t \in \{0, 1, 2, 3\}$.

### Bước 5.2: Kiểm Thử Tích Hợp Phân Hệ (Subsystem Integration Tests)
File kiểm thử: `tests/test_subsystems.py`
- [x] **Test 1**: AI Engine đọc thành công metrics từ Faucet API (`http://localhost:9302/metrics`).
- [x] **Test 2**: AI Engine đọc thành công trạng thái đường truyền từ SD-WAN Controller API (`http://127.0.0.1:7070/api/status`).
- [x] **Test 3**: Execution Engine gửi lệnh bật/tắt port và kiểm tra trạng thái OVS phản hồi đúng.

### Bước 5.3: Kiểm Thử Kịch Bản Thực Tế Toàn Diện (End-to-End Fault Injection)
File điều phối: `tests/test_self_healing_e2e.py`

#### 🟢 Các Kịch Bản Tiền Phát (Proactive Test Cases)
1. **Kịch bản P1: Tiêm bùng nổ lưu lượng sao lưu (Scheduled Backup Traffic Spike)**:
   - Dùng `iperf3` tạo tải lớn trên đường WAN MPLS chính làm băng thông tăng từ $30\% \rightarrow 80\%$.
   - **Kỳ vọng**: Dự báo Holt-Winters phát hiện xu hướng chạm ngưỡng an toàn trong $15-20$s tới $\rightarrow$ SD-WAN Controller điều hướng trước luồng VoIP sang đường 5G, cuộc gọi không bị rớt gói.
2. **Kịch bản P2: Suy giảm chất lượng đường truyền (Jitter Degradation)**:
   - Dùng lệnh `tc netem` làm tăng jitter trên đường chính từ $5\text{ms} \rightarrow 40\text{ms}$, mất gói $2\%$.
   - **Kỳ vọng**: Mô hình QoE ghi nhận điểm MOS giảm dưới $3.5$ $\rightarrow$ Hệ thống tự động chuyển luồng thoại giữa phiên (mid-session steer) sang Broadband, đàm thoại liên tục.

#### 🔵 Các Kịch Bản Hậu Phát (Reactive Test Cases)
3. **Kịch bản R1: Sập cổng trên Switch s1 (Port Down Event)**:
   - Lệnh tiêm lỗi: Ngắt cổng số 2 trên Switch `s1` (`ovs-ofctl mod-port s1 2 down`).
   - **Kỳ vọng**: $P_{down}=1 \rightarrow$ PPO Agent chọn $a_t = 1$ $\rightarrow$ Context Parser trích xuất `{target_dpid: "s1", port: 2}` $\rightarrow$ Faucet gửi lệnh OpenFlow bật lại cổng trong vòng $\le 20$s, Agent nhận $+10$ điểm thưởng.
4. **Kịch bản R2: Xung đột luật luồng OpenFlow trên Switch s2 (Flow Error Event)**:
   - Lệnh tiêm lỗi: Nạp luật lỗi khiến gói tin bị drop và log lỗi cookie `0x10a`.
   - **Kỳ vọng**: $f_{err}=1, P_{down}=0 \rightarrow$ PPO Agent chọn $a_t = 3$ $\rightarrow$ Faucet xóa quy tắc hỏng và nạp lại rule hợp lệ, luồng dữ liệu thông suốt.
5. **Kịch bản R3: Mất kết nối Switch Datapath trên Switch s3 (Switch Disconnect Event)**:
   - Lệnh tiêm lỗi: Xóa controller kết nối với switch `s3` (`ovs-vsctl del-controller s3`).
   - **Kỳ vọng**: $f_{disc}=1 \rightarrow$ PPO Agent chọn $a_t = 2$ $\rightarrow$ Tái lập kết nối Datapath và hoàn thành handshake OpenFlow 1.3, Agent nhận $+20$ điểm thưởng.
6. **Kịch bản R4: Duy trì trạng thái bình thường (Normal Baseline)**:
   - Để hệ thống chạy tải ổn định trong 10 phút liên tục.
   - **Kỳ vọng**: PPO Agent duy trì chọn $a_t = 0$ (No-op), không có bất kỳ lệnh can thiệp thừa nào, điểm phạt can thiệp thừa $= 0$.

---

## GIAI ĐOẠN 6: Chỉ Số Đánh Giá (Evaluation Benchmarks) & Kế Hoạch Báo Cáo

Bảng chỉ số đo lường phục vụ số liệu cho luận văn tốt nghiệp:

| Tiêu Chí Đánh Giá | Chỉ Số Cụ Thể | Giá Trị Mục Tiêu | Cách Thức Thu Thập & Đo Lường |
| :--- | :--- | :--- | :--- |
| **Tốc độ Phục hồi** | **MTTR** (Mean Time to Recovery) | $\le 20 - 30$ giây | So khớp timestamp giữa lúc tiêm lỗi và lúc log báo `RECOVERED` |
| **Độ chính xác Định vị** | Targeting Accuracy | $100\%$ | Đối chiếu thiết bị bị can thiệp với thiết bị bị tiêm lỗi |
| **Tránh can thiệp thừa** | False Action Rate | $< 1\%$ | Đếm số lần bị phạt ($-1$) do phát lệnh khi không có sự cố |
| **Chất lượng Thoại VoIP** | MOS Score khi xảy ra lỗi | $MOS \ge 3.8 / 5.0$ | Ghi lại luồng RTP/RTCP của Asterisk và tính bằng ITU-T PESQ/E-Model |
| **Mức độ Tiêu hao Tài nguyên** | CPU / RAM Overhead | CPU $< 5\%$, RAM $< 250$MB | Đo bằng thư viện `psutil` trên tiến trình AI Engine |

---

## 📂 Danh Sách File Cần Tạo Mới & Mở Rộng

```text
src/
├── ai_engine/
│   ├── main.py                         # Vòng lặp Closed-Loop chính (10s/tick)
│   ├── telemetry/
│   │   ├── __init__.py
│   │   ├── sdn_exporter.py             # Trích xuất metrics OpenFlow & Port
│   │   ├── wan_telemetry.py            # Active probing 5 WAN paths
│   │   ├── feature_collector.py        # Chuẩn hóa Vector s_t 8D (Macro)
│   │   └── context_parser.py           # Trích xuất DPID, Port, Cookie (Micro)
│   ├── decision/
│   │   ├── __init__.py
│   │   ├── proactive_engine.py         # Holt-Winters / LSTM + QoE Regression
│   │   ├── ppo_agent.py                # PPO Actor-Critic Model (PyTorch/SB3)
│   │   └── network_env.py              # Gym Environment để train PPO
│   └── executor/
│       ├── __init__.py
│       ├── execution_engine.py         # Bộ ghép nối Macro (a_t) + Micro (Metadata)
│       └── sdn_sdwan_binding.py        # OpenFlow Port Mod & IP Routing Steer
├── config/
│   └── prometheus.yml                  # Cấu hình Scraper 5s cho hệ thống
└── tests/
    ├── test_ai_units.py                # Test đơn vị cho từng hàm toán học/ML
    ├── test_subsystems.py              # Test tích hợp API giữa các phân hệ
    └── test_self_healing_e2e.py        # Test toàn diện 6 kịch bản P1-P2, R1-R4
```

---

## 🚀 Kế Hoạch Các Bước Thực Hiện Ngay Tiếp Theo (Action Items)

1. **Bước 1**: Hiện thực module `feature_collector.py` và `context_parser.py` để hình thành 2 luồng dữ liệu Macro ($s_t$) và Micro (Context Metadata).
2. **Bước 2**: Viết module `proactive_engine.py` (thuật toán Holt-Winters nhẹ và công thức QoE MOS).
3. **Bước 3**: Xây dựng mô hình PPO và môi trường `network_env.py` để train tác tử ra quyết định 4 hành động.
4. **Bước 4**: Hoàn thiện `execution_engine.py` kết nối trực tiếp với [flow_manager.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/controller/sdn/flow_manager.py) và [sdwan_controller.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/controller/sdwan/sdwan_controller.py).
5. **Bước 5**: Viết kịch bản kiểm thử tự động `test_self_healing_e2e.py` và chạy thực nghiệm trên Mininet.
