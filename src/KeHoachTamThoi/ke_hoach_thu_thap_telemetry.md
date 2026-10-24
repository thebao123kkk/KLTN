# Kế Hoạch Thiết Kế Module Thu Thập Telemetry
## (Telemetry Collector & State-Vector Synthesizer)

> **Phạm vi:** Module 2 — *Thu thập & Gắn nhãn dữ liệu* trong Khung Tự Phục Hồi SDN/SD-WAN dựa trên PPO RL Agent.
> **Mục tiêu:** Cào định kỳ (mỗi 10 giây) tất cả 8 chỉ số telemetry từ nhiều nguồn Prometheus, tổng hợp thành Vector trạng thái 8 chiều $s_t \in \mathbb{R}^8$, gắn nhãn lỗi $\phi_t$ và xuất ra file CSV phục vụ Gym Environment + PPO Agent.

---

## 1. Tổng Quan Kiến Trúc Thu Thập

```
LUỒNG THU THẬP TELEMETRY (10s CYCLE)
==========================================================================

CÁC NGUỒN METRICS (Scrape Targets)
 ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
 │ Faucet Exporter │  │  Gauge Exporter │  │    Node Exporter    │
 │    :9302        │  │    :9303        │  │      :9100          │
 │                 │  │                 │  │                     │
 │ faucet_cpu_     │  │ of_messages_    │  │ process_resident_   │
 │ seconds_total   │  │ sent_total      │  │ memory_bytes        │
 │                 │  │ of_errors_total │  │ process_virtual_    │
 │                 │  │ of_datapath_    │  │ memory_bytes        │
 │                 │  │   connected     │  │                     │
 │                 │  │ of_datapath_    │  │                     │
 │                 │  │   disconnections│  │                     │
 │                 │  │   _total        │  │                     │
 │                 │  │ port_status_    │  │                     │
 │                 │  │   down_total    │  │                     │
 └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘
          └─────────────────────┼──────────────────────┘
                                │ Prometheus HTTP API GET /api/v1/query
                                ▼
  ┌──────────────────────────────────────────────────┐
  │  PROMETHEUS SERVER  (:9090)                      │
  │  Scrape Interval = 10s  |  Retention = 15d       │
  └──────────────────────┬───────────────────────────┘
                         │ Python requests HTTP REST — mỗi 10 giây
                         ▼
  ┌──────────────────────────────────────────────────┐
  │  TELEMETRY COLLECTOR (telemetry_collector.py)    │
  │                                                  │
  │  (1) Query 8 metrics → raw values                │
  │  (2) Validate & normalize (handle NaN/missing)   │
  │  (3) Read fault_log.txt → phi_t, duration_t      │
  │  (4) Assemble s_t = [ccpu, cres_mem, cvirt_mem,  │
  │                       fsent, ferr, fconn,        │
  │                       fdisc, pdown]              │
  │  (5) Append row to CSV + context metadata        │
  └──────────────────────┬───────────────────────────┘
                         │
                         ▼
  ┌──────────────────────────────────────────────────┐
  │  OUTPUT: sdn_telemetry_dataset.csv               │
  │  Columns: timestamp | ccpu | cres_mem | cvirt_mem│
  │           | fsent | ferr | fconn | fdisc | pdown │
  │           | fault_label | duration               │
  │           | target_dpid | target_port            │
  │           | error_cookie | data_quality          │
  └──────────────────────────────────────────────────┘
```

---

## 2. Cơ Chế Đọc Dữ Liệu Đầu Vào (Input Data Reading Mechanism)

Module thu thập telemetry nhận dữ liệu từ **3 luồng đầu vào độc lập**, được đọc đồng bộ mỗi chu kỳ 10 giây:

```
LUỒNG ĐẦU VÀO (3 NGUỒN ĐỌC SONG SONG mỗi 10s)
══════════════════════════════════════════════════════════════

  LUỒNG 1: Prometheus HTTP API           LUỒNG 2: fault_log.txt          LUỒNG 3: Per-datapath Metrics
  (Đọc 8 chỉ số telemetry)               (Đọc nhãn lỗi phi_t)           (Đọc Context Metadata)
  ──────────────────────────             ──────────────────────────       ──────────────────────────
  GET http://localhost:9090              Ghi bởi FaultInjector             GET /api/v1/query
  /api/v1/query?query=<promql>          (fault_injector.py)              (các query per-datapath)
        │                                      │                                │
        ▼                                      ▼                                ▼
  PrometheusClient                      FaultLogReader                  ContextMetadataParser
  .query_with_fallback()               .get_current_fault()            .parse()
        │                                      │                                │
        ▼                                      ▼                                ▼
  8 raw float values                    (phi_t: str,                   ContextMetadata
  [ccpu, cres_mem, ...]                 duration_t: float)             {target_dpid, target_port,
                                                                        error_cookie}
        └──────────────────────────────────────┴────────────────────────────────┘
                                               │
                                               ▼
                                    VectorAssembler.assemble()
                                    → StateVector s_t ∈ ℝ^8
                                    → 1 dòng CSV (15 cột)
```

---

### 2.1 Luồng 1 — Đọc 8 Chỉ Số Qua Prometheus HTTP API

**Nguyên tắc hoạt động:**

Prometheus Server (`:9090`) tự động **cào (scrape)** các exporter sau mỗi **10 giây** theo lịch biểu nội bộ:

| Exporter | Cổng | Chỉ số được cào |
|:---------|:-----|:----------------|
| Faucet Exporter | `:9302` | `faucet_cpu_seconds_total` |
| Gauge Exporter | `:9303` | `of_messages_sent_total`, `of_errors_total`, `of_datapath_connected`, `of_datapath_disconnections_total`, `port_status_down_total` |
| Node Exporter | `:9100` | `process_resident_memory_bytes`, `process_virtual_memory_bytes` |

Sau khi Prometheus lưu các giá trị vào TSDB nội bộ, **script Python của chúng ta** gọi API sau để đọc:

```
HTTP GET http://localhost:9090/api/v1/query?query=<promql_expression>

Response JSON:
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {
        "metric": {"__name__": "of_datapath_connected"},
        "value": [1729083610.123, "3"]   ← [unix_timestamp, "string_value"]
      }
    ]
  }
}
```

**Ví dụ đọc `fconn` (`of_datapath_connected`):**

```python
# Bước 1: Script gọi Prometheus API
GET /api/v1/query?query=of_datapath_connected

# Bước 2: Prometheus trả về
{
  "result": [{"metric": {}, "value": [1729083610.123, "3"]}]
}

# Bước 3: PrometheusClient.query_instant() parse:
value = float("3")  →  fconn = 3.0

# Bước 4: VectorAssembler nhận fconn = 3.0
# Ý nghĩa: 3 switch (s1, s2, s3) đang kết nối active với Faucet qua cổng 6653
```

**Cơ chế 10 giây (khớp với nguyên tắc đã nêu):**

```
Timeline:
  T+0s:   Prometheus cào tất cả exporter (Faucet:9302, Gauge:9303, Node:9100)
  T+0s:   Script Python truy vấn Prometheus lấy 8 giá trị → ghi CSV dòng 1
  T+10s:  Prometheus cào lại
  T+10s:  Script Python truy vấn lại → ghi CSV dòng 2
  ...
  (lặp vô hạn)
```

**Xử lý khi query thất bại:**

```python
# Thứ tự ưu tiên fallback:
# 1. Thành công → dùng giá trị mới
# 2. Query trả về rỗng → cảnh báo, dùng last_known hoặc 0.0
# 3. ConnectionError/Timeout → thử lại tối đa 3 lần, rồi fallback
# 4. Giá trị âm/NaN → clamp về 0.0, ghi data_quality=INVALID

# Ví dụ: fconn bị thất bại query
prom._last_known["of_datapath_connected"] = 3.0  # lần cào trước
fconn = prom.query_with_fallback("of_datapath_connected", fallback="last_known")
# → fconn = 3.0 (lấy từ cache), data_quality = STALE
```

---

### 2.2 Luồng 2 — Đọc Nhãn Lỗi $\phi_t$ từ `fault_log.txt`

**Nguồn ghi log thực tế:** [`fault_injector.py`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/fault_injection/fault_injector.py) — class `FaultInjector.log_event()`

Khi `FaultInjector` thực thi một kịch bản, nó ghi 2 loại file log song song:

```python
# fault_injector.py — FaultInjector.log_event()

# File 1: fault_log.json (JSON Lines, dùng cho AI Engine)
{"timestamp": "2026-10-16T20:30:00+00:00", "scenario_id": "F01",
 "scenario_name": "Link Fault s1-s2", "category": "LINK_FAULT",
 "event_type": "INJECT", "target_devices": ["s1", "s2"],
 "target_interfaces": ["s1-eth2", "s2-eth1"],
 "duration_sec": 30.0, "status": "START"}

# File 2: fault_log.txt (plain text, dùng cho FaultLogReader)
[2026-10-16T20:30:00+00:00] [INJECT] [F01] Link Fault s1-s2 - Targets: ['s1', 's2'] - Status: START
[2026-10-16T20:30:30+00:00] [RECOVER] [F01] Link Fault s1-s2 - Targets: ['s1', 's2'] - Status: SUCCESS
```

**Quan trọng — ánh xạ `event_type` → `phi_t`:**

`FaultInjector` dùng `event_type = "INJECT"/"RECOVER"` và `category` để phân loại. `FaultLogReader` cần đọc **`fault_log.json`** (JSONL) để trích xuất chính xác hơn:

```python
# fault_log_reader.py — Đọc fault_log.json (JSONL format)

def get_current_fault(self) -> Tuple[str, float]:
    """
    Đọc fault_log.json — mỗi dòng là 1 JSON event từ FaultInjector.log_event().

    Mapping category → phi_t:
      "LINK_FAULT"    → "LINK_FAULT"
      "PORT_FAULT"    → "PORT_FAULT"
      "FLOW_ERROR"    → "FLOW_ERROR"
      "FAUCET_RELOAD" → "FAUCET_RELOAD"
      "WAN_*"         → "SOFT_WARNING" (tùy severity)
      (không có event active) → "NONE"

    Logic:
      - Duyệt từ cuối file lên (sự kiện gần nhất).
      - Nếu dòng cuối cùng có event_type="INJECT" và status="START"
        → lỗi đang active, tính duration = now - timestamp
      - Nếu dòng cuối có event_type="RECOVER" và status="SUCCESS"
        → mạng đã phục hồi → phi_t = "NONE"
    """
    now = datetime.now(tz=TZ_UTC)
    CATEGORY_TO_PHI = {
        "LINK_FAULT": "LINK_FAULT",
        "PORT_FAULT": "PORT_FAULT",
        "FLOW_ERROR": "FLOW_ERROR",
        "FAUCET_RELOAD": "FAUCET_RELOAD",
        "WAN_DEGRADATION": "SOFT_WARNING",
        "CONGESTION": "FLOW_ERROR",
    }
    try:
        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
    except Exception:
        return "NONE", 0.0

    for line in reversed(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("event_type", "")
        status     = event.get("status", "")
        category   = event.get("category", "")

        # Sự kiện RECOVER thành công → mạng đã hồi phục
        if event_type == "RECOVER" and status == "SUCCESS":
            return "NONE", 0.0

        # Sự kiện INJECT đang active
        if event_type == "INJECT" and status == "START":
            phi_t = CATEGORY_TO_PHI.get(category, "SOFT_WARNING")
            ts_str = event.get("timestamp", "")
            try:
                start = datetime.fromisoformat(ts_str)
                duration = (now - start).total_seconds()
            except ValueError:
                duration = 0.0
            return phi_t, max(0.0, duration)

    return "NONE", 0.0
```

**Luồng ghi/đọc end-to-end:**

```
fault_injector.py              fault_log.json                FaultLogReader
(Fault Injector Module)        (data/logs/)                  (Telemetry Module)
       │                             │                              │
       │  inject() kịch bản F01      │                              │
       │  LINK_FAULT - status=START  │                              │
       ├────────────────────────────►│  Ghi JSON line               │
       │                             │                              │
       │                             │   mỗi 10 giây               │
       │                             │◄─────────────────────────────│
       │                             │   đọc từ cuối lên            │
       │                             ├─────────────────────────────►│
       │                             │   → phi_t = "LINK_FAULT"     │
       │                             │   → duration = 12.5s         │
       │  recover() F01              │                              │
       │  status=SUCCESS             │                              │
       ├────────────────────────────►│  Ghi JSON line               │
       │                             │                              │
       │                             │   chu kỳ tiếp theo          │
       │                             │◄─────────────────────────────│
       │                             ├─────────────────────────────►│
       │                             │   → phi_t = "NONE"           │
       │                             │   → duration = 0.0           │
```

---

### 2.3 Luồng 3 — Đọc Context Metadata (Per-Datapath Queries)

**Mục đích:** Xác định chính xác thiết bị/cổng bị hỏng để ghi vào cột `target_dpid`, `target_port`, `error_cookie` trong CSV — phục vụ **Tầng Micro** của Execution Engine.

Script thực hiện thêm **3 query bổ sung** sau khi đã đọc xong 8 metrics chính:

```python
# ContextMetadataParser.parse() — 3 query per-datapath

# Query A: Tìm port đang DOWN trên switch nào
GET /api/v1/query?query=of_port_status+==+0
Response: [
  {"metric": {"dp_name": "s1", "port": "2"}, "value": [ts, "0"]},
]
→ target_dpid = "s1", target_port = 2

# Query B: Tìm switch nào đang phát sinh lỗi OpenFlow
GET /api/v1/query?query=of_errors_total+>+0
Response: [
  {"metric": {"dp_name": "s2", "cookie": "0x10a"}, "value": [ts, "3"]},
]
→ error_cookie = "0x10a"  (target_dpid = "s2")

# Query C: Tìm switch nào đang mất kết nối với Faucet
GET /api/v1/query?query=faucet_dp_status+==+0
Response: [
  {"metric": {"dp_name": "s3"}, "value": [ts, "0"]},
]
→ disconnected_dpids = ["s3"]
```

**Ví dụ hoàn chỉnh cho sự kiện PORT_FAULT trên switch s1, port 2:**

```
Chu kỳ T:
  Luồng 1: pdown = 1.0  (tổng 1 port đang DOWN)
            ferr  = 0
            fconn = 3.0  (3 switch vẫn kết nối)
  Luồng 2: phi_t = "PORT_FAULT", duration = 15.3s
  Luồng 3: target_dpid = "s1", target_port = 2, error_cookie = ""

CSV dòng T:
  2026-10-16T20:30:20+07:00 | ... | 1.0 | PORT_FAULT | 15.3 | s1 | 2 | | OK

→ PPO Agent nhận s_t với pdown=1 → chọn a_t=1 (Reset ports)
→ Execution Engine đọc target_dpid="s1", target_port=2
→ Faucet gửi OFPPC_PORT_UP cho PORT 2 trên SWITCH s1
```

---

## 3. Đặc Tả Chi Tiết 8 Chỉ Số Telemetry

### Bảng Ánh Xạ: Thành Phần Vector → Prometheus Metric → Nguồn

| # | Tên Biến | Ký Hiệu | Prometheus Metric Name | Scrape Target | Đơn Vị | Kiểu |
|:--|:---------|:--------|:-----------------------|:--------------|:-------|:-----|
| 1 | `ccpu` | $c_{\text{cpu}}$ | `faucet_cpu_seconds_total` | Faucet Exporter `:9302` | seconds | Monotonic Counter |
| 2 | `cres_mem` | $c_{\text{res\_mem}}$ | `process_resident_memory_bytes` | Prometheus / process exporter | bytes | Gauge |
| 3 | `cvirt_mem` | $c_{\text{virt\_mem}}$ | `process_virtual_memory_bytes` | Prometheus / process exporter | bytes | Gauge |
| 4 | `fsent` | $f_{\text{sent}}$ | `of_messages_sent_total` | Prometheus / Gauge Exporter `:9303` | messages | Monotonic Counter |
| 5 | `ferr` | $f_{\text{err}}$ | `of_errors_total` | Gauge Exporter `:9303` | errors | Monotonic Counter |
| 6 | `fconn` | $f_{\text{conn}}$ | `of_datapath_connected` | Gauge Exporter `:9303` | connections | Gauge |
| 7 | `fdisc` | $f_{\text{disc}}$ | `of_datapath_disconnections_total` | Gauge Exporter `:9303` | disconnections | Monotonic Counter |
| 8 | `pdown` | $p_{\text{down}}$ | `port_status_down_total` | Prometheus / Gauge Exporter `:9303` | ports | Gauge |

---

### 2.1 Nhóm 1 — Sức Khỏe Tiến Trình Controller (Control Plane Health)

#### `ccpu` — $c_{\text{cpu}}$ — Controller CPU Seconds Total

- **Nguồn:** Faucet Exporter `:9302` → `faucet_cpu_seconds_total`
- **Cơ chế:** Bộ đếm tích lũy (Monotonic Counter) tính tổng CPU time (user + system) mà tiến trình Faucet tiêu thụ kể từ khi khởi động.
- **Prometheus Query:** `faucet_cpu_seconds_total`
- **Ý nghĩa đối với PPO:** Giá trị tăng vọt bất thường trong 10 giây báo hiệu Faucet Controller đang xử lý burst lớn (UDP flood → `FLOW_ERROR`). Agent tương quan với `ferr` để chọn `a_t = 3`.
- **Xử lý NaN:** Nếu Faucet exporter mất kết nối → gán `ccpu = last_known_value`, ghi cờ `data_quality=STALE`.

#### `cres_mem` — $c_{\text{res\_mem}}$ — Resident Memory Bytes

- **Nguồn:** Prometheus cào từ **process exporter** → `process_resident_memory_bytes`
- **Cơ chế:** Đo lường trực tiếp lượng bộ nhớ RAM vật lý (Resident Set Size — RSS) được cấp phát cho tiến trình Faucet Controller tại thời điểm cào dữ liệu.
- **Prometheus Query:** `process_resident_memory_bytes`
- **Cách tính:** Giá trị Gauge phản ánh trực tiếp dung lượng RAM vật lý tiến trình controller đang chiếm dụng.
- **Ý nghĩa đối với PPO:** RSS tăng cao kết hợp `ccpu` cao → Faucet bị quá tải → Agent ưu tiên `a_t = 2` (Restart switch).
- **Xử lý NaN:** Gán `cres_mem = 0.0`, ghi cờ `data_quality=MISSING`.

#### `cvirt_mem` — $c_{\text{virt\_mem}}$ — Virtual Memory Bytes

- **Nguồn:** Prometheus cào từ **process exporter** → `process_virtual_memory_bytes`
- **Cơ chế:** Gauge đo tổng dung lượng không gian địa chỉ bộ nhớ ảo (Virtual Memory Size — VMS) mà tiến trình Faucet Controller đã đăng ký với hệ điều hành.
- **Prometheus Query:** `process_virtual_memory_bytes`
- **Cách tính:** Trích xuất tổng dung lượng không gian địa chỉ bộ nhớ ảo mà tiến trình controller đang yêu cầu quản lý tại chu kỳ thu thập.
- **Ý nghĩa đối với PPO:** Thường lớn hơn RSS và ít biến động hơn; hữu ích để phát hiện memory leak dài hạn trong Faucet.

---

### 2.2 Nhóm 2 — Thống Kê OpenFlow (OpenFlow Operation Statistics)

#### `fsent` — $f_{\text{sent}}$ — OpenFlow Messages Sent Counter

- **Mô tả:** Tổng số lượng thông điệp OpenFlow (như `FlowMod`, `PacketOut`, `EchoRequest`...) đã được gửi đi qua kênh điều khiển.
- **Nguồn Metric:** Prometheus / Gauge Exporter `:9303` → `of_messages_sent_total`
- **Cách tính:** Bộ đếm tích lũy (counter) tăng +1 mỗi khi có một thông điệp OpenFlow được tạo và truyền đi. Số lượng thông điệp tăng nhanh báo hiệu quá trình tái thiết lập quy tắc luồng đang diễn ra liên tục.
- **Ý nghĩa đối với PPO:** Tốc độ tăng `fsent` nhanh bất thường trong 10s báo hiệu control plane storm, thường do `FAUCET_RELOAD` hoặc `LINK_FAULT`.

#### `ferr` — $f_{\text{err}}$ — OpenFlow Errors Counter

- **Mô tả:** Tổng số lượng thông điệp lỗi OpenFlow (OpenFlow Error Messages) do các switch phản hồi về controller.
- **Nguồn Metric:** Gauge Exporter `:9303` → `of_errors_total`
- **Cách tính:** Bộ đếm tích lũy tăng lên mỗi khi switch phát hiện quy tắc luồng không hợp lệ, không tìm thấy cổng hoặc lỗi bảng luồng TCAM (OFPBAC_BAD_OUT_PORT, OFPFMFC_TABLE_FULL, ...). Chỉ số này trực tiếp chịu mức phạt $-1 \cdot f_{\text{err}}$ trong hàm phần thưởng.
- **Ý nghĩa đối với PPO:** Giá trị cao → Agent ưu tiên `a_t = 3` (Bespoke self-heal) để flush & re-inject flow rules.
- **Context Metadata:** `of_errors_total{dp_name="s2", error_type="OFPBAC_BAD_OUT_PORT"}` → `target_dpid = "s2"`, `error_cookie = "0x10a"`.

#### `fconn` — $f_{\text{conn}}$ — OpenFlow Datapath Connected

> **Đây là chỉ số trọng tâm của phần telemetry OpenFlow.**

**1. Nguồn thu thập dữ liệu (Telemetry Source):**
- Chỉ số này được theo dõi bởi **Gauge** — agent giám sát đính kèm của Faucet Controller.
- Gauge thu thập trạng thái kênh giao tiếp OpenFlow từ các switch (datapath) và xuất (export) thành chỉ số Prometheus metrics — cụ thể là chỉ số `of_datapath_connected`.
- **Prometheus Query:** `of_datapath_connected` (via Gauge Exporter `:9303`)

**2. Cơ chế đếm (Calculation / Scraping Mechanism):**
- **Đăng ký kết nối:** Khi các OpenFlow switch (`s1`, `s2`, `s3` trong Mininet) khởi tạo và duy trì kênh điều khiển OpenFlow thành công tới Faucet Controller qua cổng `6653`, Gauge ghi nhận mỗi kênh datapath active này là 1 kết nối.
- **Cào dữ liệu định kỳ:** Một kịch bản Python tự động truy vấn Prometheus **mỗi 10 giây/lần** để trích xuất tổng số lượng kết nối datapath đang duy trì tại thời điểm đó.
- **Giá trị điển hình:** Trong cấu hình Base Topology gồm 3 switch kết nối bình thường với controller, `fconn` sẽ ghi nhận các kết nối datapath đang duy trì — **ví dụ `4.0`** tùy theo số lượng kết nối/kênh datapath được thiết lập (bao gồm cả kênh auxiliary nếu có).

**3. Mối liên hệ với `fdisc`:**
- Trong khi `fconn` phản ánh số kết nối datapath đang **hoạt động (active)**, chỉ số **`fdisc`** (`of_datapath_disconnections_total`) ghi nhận tổng số lần kết nối datapath bị **ngắt/mất kết nối**.

  | Chỉ số | Loại | Đo gì |
  |:-------|:-----|:------|
  | `fconn` | Gauge (tức thời) | Số kết nối datapath đang **ACTIVE** |
  | `fdisc` | Counter (tích lũy) | Tổng số lần kết nối bị **NGẮT** |

  - `fconn thấp + fdisc cao` = tình trạng mất kết nối nghiêm trọng.
  - `fconn bình thường + fdisc tăng nhẹ` = có ngắt kết nối nhưng đã phục hồi.

**Ý nghĩa đối với PPO:** `fconn` giảm đột ngột báo hiệu switch mất kết nối. Kết hợp với `fdisc > 0` → Agent nhận diện `FAUCET_RELOAD` → chọn `a_t = 2`.

  ```
  Trạng thái BÌNH THƯỜNG (Base Topology 3 switch):
    of_datapath_connected            = 4.0   (ví dụ: 3 switch + kênh auxiliary)
    of_datapath_disconnections_total = 0

  Sau sự kiện FAUCET_RELOAD:
    of_datapath_connected            = 0.0   (tất cả ngắt kết nối tạm thời)
    of_datapath_disconnections_total = 3     (3 lần ngắt ghi nhận)
    → fconn giảm mạnh + fdisc tăng → PPO Agent chọn a_t = 2 (thưởng +20)
  ```

#### `fdisc` — $f_{\text{disc}}$ — OpenFlow Disconnections Counter

- **Mô tả:** Tổng số lần kênh kết nối datapath giữa các switch OpenFlow và Faucet Controller bị ngắt/đứt kết nối.
- **Nguồn Metric:** Gauge Exporter `:9303` → `of_datapath_disconnections_total`
- **Cách tính:** Bộ đếm gia tăng +1 mỗi khi kênh kết nối OpenFlow của một switch bị gián đoạn — chẳng hạn khi xảy ra sự cố ngắt nguồn switch hoặc sự kiện `FAUCET_RELOAD`.
- **Ý nghĩa đối với PPO:** Tín hiệu chính để nhận diện `FAUCET_RELOAD`. Khi `fdisc` tăng đột biến → Agent được thưởng +20 nếu chọn `a_t = 2`.

---

### 2.3 Nhóm 3 — Trạng Thái Mặt Phẳng Dữ Liệu (Data Plane Status)

#### `pdown` — $p_{\text{down}}$ — Aggregate Down Ports Count

- **Mô tả:** Tổng số lượng cổng mạng (interfaces/ports) hiện đang ở trạng thái ngừng hoạt động (Down) trên toàn hệ thống.
- **Nguồn Metric:** Prometheus cào từ Gauge Exporter `:9303` → `port_status_down_total`
- **Cách tính:** Quét và cộng dồn tổng số cổng giao diện vật lý/ảo bị ngắt kết nối (do sự kiện đứt liên kết `LINK_FAULT` hoặc tắt cổng `PORT_FAULT`) trên toàn bộ các switch tại thời điểm cào dữ liệu.
- **Ý nghĩa đối với PPO:** Chỉ số này bị phạt với hệ số $-2 \cdot p_{\text{down}}$ trong hàm phần thưởng để thúc đẩy tác nhân sớm khôi phục cổng → Agent được thúc đẩy mạnh để chọn `a_t = 1` (Reset ports).
- **Context Metadata:** `of_port_status{dp_name="s1", port="2"} = 0` → `target_dpid = "s1"`, `target_port = 2`.

---

## 3. Thiết Kế Module Python

### 3.1 Cấu Trúc Thư Mục

```
src/
├── telemetry/
│   ├── __init__.py
│   ├── telemetry_collector.py      # Script thu thập chính (10s cycle)
│   ├── prometheus_client.py        # Wrapper query Prometheus HTTP API
│   ├── fault_log_reader.py         # Đọc fault_log.txt → phi_t, duration_t
│   ├── context_metadata_parser.py  # Trích xuất DPID/Port/Cookie (Tầng Micro)
│   └── vector_assembler.py         # Ghép 8 giá trị → s_t, validate
├── data/
│   ├── sdn_telemetry_dataset.csv   # Output chính
│   ├── fault_log.txt               # Input từ Fault Injector
│   └── telemetry_log.jsonl         # Raw log mỗi chu kỳ (debug)
└── config/
    └── telemetry_config.yaml       # Cấu hình endpoints, intervals, thresholds
```

### 3.2 Cấu Hình YAML (`telemetry_config.yaml`)

```yaml
prometheus:
  base_url: "http://localhost:9090"
  api_path: "/api/v1/query"
  timeout_seconds: 5

scrape:
  interval_seconds: 10
  retry_attempts: 3
  retry_delay_seconds: 1

metrics:
  ccpu:
    query: "faucet_cpu_seconds_total"
    type: "counter"
    fallback: "last_known"
  cres_mem:
    query: 'process_resident_memory_bytes{job="faucet"}'
    type: "gauge"
    fallback: 0.0
  cvirt_mem:
    query: 'process_virtual_memory_bytes{job="faucet"}'
    type: "gauge"
    fallback: 0.0
  fsent:
    query: "of_messages_sent_total"
    type: "counter"
    fallback: "last_known"
  ferr:
    query: "of_errors_total"
    type: "counter"
    fallback: "last_known"
  fconn:
    query: "of_datapath_connected"
    type: "gauge"
    fallback: 0.0
  fdisc:
    query: "of_datapath_disconnections_total"
    type: "counter"
    fallback: "last_known"
  pdown:
    query: "port_status_down_total"
    type: "gauge"
    fallback: 0.0

output:
  csv_path: "data/sdn_telemetry_dataset.csv"
  raw_log_path: "data/telemetry_log.jsonl"
  fault_log_path: "data/fault_log.txt"

context_metadata:
  enabled: true
  port_status_query: "of_port_status"
  error_detail_query: "of_errors_total"
  dp_status_query: "faucet_dp_status"
```

### 3.3 `prometheus_client.py` — Wrapper Prometheus HTTP API

```python
"""
prometheus_client.py
Lớp wrapper gọi Prometheus HTTP API để truy vấn instant metrics.
"""
import requests
import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)


class PrometheusClient:
    """Client truy vấn Prometheus HTTP API."""

    def __init__(self, base_url: str = "http://localhost:9090", timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._last_known: dict = {}

    def query_instant(self, promql: str) -> Optional[float]:
        """
        Truy vấn một giá trị instant metric từ Prometheus.
        Returns: float nếu thành công, None nếu thất bại.
        """
        url = f"{self.base_url}/api/v1/query"
        try:
            resp = requests.get(url, params={"query": promql}, timeout=self.timeout)
            resp.raise_for_status()
            results = resp.json().get("data", {}).get("result", [])
            if not results:
                logger.warning(f"[Prometheus] Không có kết quả: {promql}")
                return None
            value = float(results[0]["value"][1])
            self._last_known[promql] = value
            return value
        except requests.exceptions.Timeout:
            logger.error(f"[Prometheus] Timeout: {promql}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"[Prometheus] Không kết nối được tới {self.base_url}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"[Prometheus] Lỗi parse '{promql}': {e}")
            return None

    def query_with_fallback(self, promql: str, fallback: Union[float, str] = 0.0) -> float:
        """
        Query với fallback khi thất bại.
        - fallback='last_known' → dùng giá trị cào được lần cuối.
        - fallback=<float>      → dùng giá trị cứng.
        """
        value = self.query_instant(promql)
        if value is not None:
            return value
        if fallback == "last_known":
            cached = self._last_known.get(promql)
            if cached is not None:
                logger.warning(f"[Prometheus] Dùng last_known={cached:.4f} cho '{promql}'")
                return cached
            logger.error(f"[Prometheus] Không có last_known cho '{promql}', trả về 0.0")
            return 0.0
        return float(fallback)

    def query_vector(self, promql: str, label_filter: dict = None) -> list:
        """
        Truy vấn nhiều kết quả (vector) từ Prometheus.
        Dùng để lấy per-datapath metrics (vd: of_port_status theo dp_name).
        Returns: list[{"labels": {...}, "value": float}]
        """
        url = f"{self.base_url}/api/v1/query"
        results_parsed = []
        try:
            resp = requests.get(url, params={"query": promql}, timeout=self.timeout)
            resp.raise_for_status()
            for item in resp.json().get("data", {}).get("result", []):
                entry = {"labels": item.get("metric", {}), "value": float(item["value"][1])}
                if label_filter:
                    if all(entry["labels"].get(k) == v for k, v in label_filter.items()):
                        results_parsed.append(entry)
                else:
                    results_parsed.append(entry)
        except Exception as e:
            logger.error(f"[Prometheus] query_vector thất bại cho '{promql}': {e}")
        return results_parsed
```

### 3.4 `context_metadata_parser.py` — Tầng Micro Định Vị Thiết Bị

```python
"""
context_metadata_parser.py
Trích xuất Context Metadata (DPID, Port, Cookie) từ per-datapath metrics.

Kiến trúc Định vị 2 Tầng:
  - Tầng MACRO: PPO Agent quyết định LOẠI hành động (a_t in {0,1,2,3}).
  - Tầng MICRO (module này): Xác định THIẾT BỊ CỤ THỂ bị hỏng.
"""
import logging
from dataclasses import dataclass, field
from prometheus_client import PrometheusClient

logger = logging.getLogger(__name__)


@dataclass
class ContextMetadata:
    target_dpid: str = ""
    target_port: int = -1
    error_cookie: str = ""
    disconnected_dpids: list = field(default_factory=list)


class ContextMetadataParser:

    def __init__(self, prom_client: PrometheusClient):
        self.prom = prom_client

    def parse(self) -> ContextMetadata:
        metadata = ContextMetadata()

        # 1. Tìm switch có port bị down (of_port_status == 0)
        port_down_results = self.prom.query_vector("of_port_status == 0")
        if port_down_results:
            labels = port_down_results[0]["labels"]
            metadata.target_dpid = labels.get("dp_name", "")
            port_str = labels.get("port_name", labels.get("port", "-1"))
            try:
                metadata.target_port = int(port_str)
            except ValueError:
                metadata.target_port = -1
            logger.info(
                f"[ContextParser] Port down: dpid={metadata.target_dpid}, "
                f"port={metadata.target_port}"
            )

        # 2. Tìm switch có lỗi OpenFlow (of_errors_total > 0)
        error_results = self.prom.query_vector("of_errors_total > 0")
        if error_results:
            err_labels = error_results[0]["labels"]
            if not metadata.target_dpid:
                metadata.target_dpid = err_labels.get("dp_name", "")
            metadata.error_cookie = err_labels.get("cookie", "")
            logger.info(
                f"[ContextParser] Flow error: dpid={err_labels.get('dp_name')}, "
                f"cookie={metadata.error_cookie}"
            )

        # 3. Tìm switch mất kết nối (faucet_dp_status == 0)
        for entry in self.prom.query_vector("faucet_dp_status == 0"):
            dpid = entry["labels"].get("dp_name", "")
            if dpid:
                metadata.disconnected_dpids.append(dpid)
                logger.info(f"[ContextParser] Switch disconnected: {dpid}")

        if metadata.disconnected_dpids and not metadata.target_dpid:
            metadata.target_dpid = metadata.disconnected_dpids[0]

        return metadata
```

### 3.5 `fault_log_reader.py` — Đọc Nhãn Lỗi $\phi_t$

```python
"""
fault_log_reader.py
Đọc fault_log.txt để lấy nhãn lỗi phi_t và duration_t.

Format dòng:
  2026-10-16T20:30:00+07:00 | FAULT_START | LINK_FAULT | s1-eth2 | s2-eth1
  2026-10-16T20:30:26+07:00 | FAULT_END   | LINK_FAULT | s1-eth2 | s2-eth1
"""
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

FAULT_TYPES = {"LINK_FAULT", "PORT_FAULT", "FLOW_ERROR",
               "FAUCET_RELOAD", "SOFT_WARNING", "TEMP_WARNING", "NONE"}
TZ_VN = timezone(timedelta(hours=7))


class FaultLogReader:

    def __init__(self, fault_log_path: str = "data/fault_log.txt"):
        self.log_path = Path(fault_log_path)
        if not self.log_path.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.write_text("")

    def get_current_fault(self) -> Tuple[str, float]:
        """
        Trả về (phi_t, duration_seconds) của lỗi đang active.
        Nếu không có lỗi → ("NONE", 0.0).
        """
        now = datetime.now(tz=TZ_VN)
        try:
            lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        except Exception as e:
            logger.error(f"[FaultLogReader] Không đọc được: {e}")
            return "NONE", 0.0

        for line in reversed(lines):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                continue
            ts_str, event_type, fault_type = parts[0], parts[1], parts[2]

            if event_type == "FAULT_END":
                return "NONE", 0.0

            if event_type == "FAULT_START" and fault_type in FAULT_TYPES:
                try:
                    start_time = datetime.fromisoformat(ts_str)
                    duration = (now - start_time).total_seconds()
                    logger.debug(f"[FaultLogReader] Active: {fault_type}, {duration:.1f}s")
                    return fault_type, duration
                except ValueError:
                    continue

        return "NONE", 0.0
```

### 3.6 `vector_assembler.py` — Tổng Hợp Vector $s_t$

```python
"""
vector_assembler.py
Ghép 8 raw values → StateVector s_t ∈ R^8, validate, ghi data_quality flag.
"""
import logging
import math
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StateVector:
    """Vector trạng thái 8 chiều s_t."""
    ccpu: float       # c_cpu    - faucet_cpu_seconds_total
    cres_mem: float   # c_res_mem - process_resident_memory_bytes
    cvirt_mem: float  # c_virt_mem - process_virtual_memory_bytes
    fsent: float      # f_sent   - of_messages_sent_total
    ferr: float       # f_err    - of_errors_total
    fconn: float      # f_conn   - of_datapath_connected
    fdisc: float      # f_disc   - of_datapath_disconnections_total
    pdown: float      # p_down   - port_status_down_total
    data_quality: str = "OK"

    def to_list(self) -> list:
        return [self.ccpu, self.cres_mem, self.cvirt_mem,
                self.fsent, self.ferr, self.fconn,
                self.fdisc, self.pdown]

    def is_healthy(self) -> bool:
        return self.ferr == 0.0 and self.fdisc == 0.0 and self.pdown == 0.0

    def validate(self) -> bool:
        return all(
            not (math.isnan(v) or math.isinf(v) or v < 0)
            for v in self.to_list()
        )


class VectorAssembler:

    @staticmethod
    def assemble(
        ccpu: Optional[float], cres_mem: Optional[float], cvirt_mem: Optional[float],
        fsent: Optional[float], ferr: Optional[float], fconn: Optional[float],
        fdisc: Optional[float], pdown: Optional[float],
    ) -> StateVector:
        vals = [ccpu, cres_mem, cvirt_mem, fsent, ferr, fconn, fdisc, pdown]
        missing = sum(1 for v in vals if v is None)

        def safe(v, d=0.0):
            return v if v is not None else d

        vec = StateVector(
            ccpu=safe(ccpu), cres_mem=safe(cres_mem), cvirt_mem=safe(cvirt_mem),
            fsent=safe(fsent), ferr=safe(ferr), fconn=safe(fconn),
            fdisc=safe(fdisc), pdown=safe(pdown),
        )

        if missing == 0:
            vec.data_quality = "OK"
        elif missing <= 2:
            vec.data_quality = "PARTIAL"
        elif missing <= 5:
            vec.data_quality = "STALE"
        else:
            vec.data_quality = "MISSING"

        if not vec.validate():
            logger.warning(f"[VectorAssembler] Vector không hợp lệ: {vec}")
            vec.data_quality = "INVALID"

        return vec
```

### 3.7 `telemetry_collector.py` — Vòng Lặp Chính 10 giây

```python
"""
telemetry_collector.py
Script thu thập Telemetry chính — vòng lặp 10 giây,
tương ứng Algorithm 1 trong Model_Research_and_Implementation_Plan.md
"""
import csv
import json
import logging
import time
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path

from prometheus_client import PrometheusClient
from fault_log_reader import FaultLogReader
from context_metadata_parser import ContextMetadataParser
from vector_assembler import VectorAssembler, StateVector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("TelemetryCollector")
TZ_VN = timezone(timedelta(hours=7))

CSV_COLUMNS = [
    "timestamp",
    "ccpu", "cres_mem", "cvirt_mem",
    "fsent", "ferr", "fconn", "fdisc", "pdown",
    "fault_label", "duration_seconds",
    "target_dpid", "target_port", "error_cookie",
    "data_quality",
]


def load_config(path: str = "config/telemetry_config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def initialize_csv(csv_path: Path):
    if not csv_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_COLUMNS).writeheader()
        logger.info(f"[CSV] Khởi tạo: {csv_path}")


def append_row(csv_path: Path, row: dict):
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_COLUMNS).writerow(row)


def collect_once(prom, fault_reader, ctx_parser, cfg) -> dict:
    """Thực hiện một chu kỳ thu thập đầy đủ."""
    timestamp = datetime.now(tz=TZ_VN).isoformat()
    m = cfg["metrics"]

    # (1) Truy vấn 8 metrics
    ccpu      = prom.query_with_fallback(m["ccpu"]["query"],      m["ccpu"]["fallback"])
    cres_mem  = prom.query_with_fallback(m["cres_mem"]["query"],  m["cres_mem"]["fallback"])
    cvirt_mem = prom.query_with_fallback(m["cvirt_mem"]["query"], m["cvirt_mem"]["fallback"])
    fsent     = prom.query_with_fallback(m["fsent"]["query"],     m["fsent"]["fallback"])
    ferr      = prom.query_with_fallback(m["ferr"]["query"],      m["ferr"]["fallback"])
    fconn     = prom.query_with_fallback(m["fconn"]["query"],     m["fconn"]["fallback"])
    fdisc     = prom.query_with_fallback(m["fdisc"]["query"],     m["fdisc"]["fallback"])
    pdown     = prom.query_with_fallback(m["pdown"]["query"],     m["pdown"]["fallback"])

    # (2) Tổng hợp vector s_t
    vec: StateVector = VectorAssembler.assemble(
        ccpu, cres_mem, cvirt_mem, fsent, ferr, fconn, fdisc, pdown
    )

    # (3) Đọc nhãn lỗi phi_t
    phi_t, duration_t = fault_reader.get_current_fault()

    # (4) Trích xuất Context Metadata
    ctx = ctx_parser.parse()

    # (5) Ghi raw log JSONL (debug)
    logger.debug(json.dumps({
        "timestamp": timestamp, "state_vector": vec.to_list(),
        "fault_label": phi_t, "duration_seconds": round(duration_t, 2),
        "context": {"target_dpid": ctx.target_dpid,
                    "target_port": ctx.target_port,
                    "error_cookie": ctx.error_cookie},
        "data_quality": vec.data_quality,
    }, ensure_ascii=False))

    return {
        "timestamp":        timestamp,
        "ccpu":             round(vec.ccpu, 6),
        "cres_mem":         int(vec.cres_mem),
        "cvirt_mem":        int(vec.cvirt_mem),
        "fsent":            int(vec.fsent),
        "ferr":             int(vec.ferr),
        "fconn":            round(vec.fconn, 1),
        "fdisc":            int(vec.fdisc),
        "pdown":            int(vec.pdown),
        "fault_label":      phi_t,
        "duration_seconds": round(duration_t, 2),
        "target_dpid":      ctx.target_dpid,
        "target_port":      ctx.target_port,
        "error_cookie":     ctx.error_cookie,
        "data_quality":     vec.data_quality,
    }


def run_collector(config_path: str = "config/telemetry_config.yaml"):
    cfg = load_config(config_path)
    interval = cfg["scrape"]["interval_seconds"]
    csv_path = Path(cfg["output"]["csv_path"])

    prom         = PrometheusClient(cfg["prometheus"]["base_url"],
                                    cfg["prometheus"]["timeout_seconds"])
    fault_reader = FaultLogReader(cfg["output"]["fault_log_path"])
    ctx_parser   = ContextMetadataParser(prom)

    initialize_csv(csv_path)
    logger.info(f"[TelemetryCollector] Bắt đầu — chu kỳ {interval}s → {csv_path}")

    cycle = 0
    while True:
        t_start = time.time()
        cycle += 1
        try:
            row = collect_once(prom, fault_reader, ctx_parser, cfg)
            append_row(csv_path, row)
            logger.info(
                f"[{cycle:04d}] fconn={row['fconn']} pdown={row['pdown']} "
                f"ferr={row['ferr']} fdisc={row['fdisc']} "
                f"fault={row['fault_label']}({row['duration_seconds']:.1f}s) "
                f"quality={row['data_quality']}"
            )
        except Exception as e:
            logger.error(f"[{cycle:04d}] Lỗi không mong đợi: {e}", exc_info=True)

        time.sleep(max(0.0, interval - (time.time() - t_start)))


if __name__ == "__main__":
    run_collector()
```

---

## 4. Sơ Đồ Luồng Dữ Liệu Tổng Hợp (Sequence Diagram)

```
Fault Injector     Prometheus        Telemetry Collector      CSV Output
     │                 │                      │                    │
     │  fault_log.txt  │                      │                    │
     ├────────────────────────────────────────►│                    │
     │                 │◄── Gauge/Faucet/Node  │                    │
     │                 │    Exporter (10s)     │                    │
     │                 │                      │                    │
     ╔═══════════════════════════════════════════════════╗  CYCLE T │
     ║                 │   GET /api/v1/query   │         ║          │
     ║                 │   ccpu                │         ║          │
     ║                 │◄─────────────────────-│         ║          │
     ║                 ├──────────────────────►│         ║          │
     ║                 │   cres_mem, cvirt_mem │         ║          │
     ║                 │◄──────────────────────│         ║          │
     ║                 ├──────────────────────►│         ║          │
     ║                 │   fsent,ferr,fconn,   │         ║          │
     ║                 │   fdisc,pdown         │         ║          │
     ║                 │◄──────────────────────│         ║          │
     ║                 ├──────────────────────►│         ║          │
     ║   ◄─────────────────────────────────────│         ║          │
     ║   Đọc fault_log → phi_t, duration_t     │         ║          │
     ║                 │  per-dp metrics       │         ║          │
     ║                 │  (Context Metadata)   │         ║          │
     ║                 │◄──────────────────────│         ║          │
     ║                 ├──────────────────────►│         ║          │
     ║                 │         Assemble s_t  │         ║          │
     ║                 │         Validate      │         ║          │
     ║                 │         Build row     ├──────────────────────►│
     ╚═══════════════════════════════════════════════════╝          │
```

---

## 5. Đặc Tả Định Dạng Output CSV (15 Cột)

| Cột | Kiểu | Ví Dụ | Mô Tả |
|:----|:-----|:------|:------|
| `timestamp` | ISO-8601 string | `2026-10-16T20:30:10+07:00` | Thời điểm thu thập |
| `ccpu` | float (6 dec) | `1234.567890` | CPU seconds tích lũy Faucet |
| `cres_mem` | int (bytes) | `45678592` | RAM vật lý Faucet |
| `cvirt_mem` | int (bytes) | `234567680` | RAM ảo Faucet |
| `fsent` | int | `15234` | Tổng OF messages đã gửi |
| `ferr` | int | `0` | Tổng OF errors |
| `fconn` | float (1 dec) | `3.0` | Kết nối datapath đang active |
| `fdisc` | int | `0` | Tổng lần ngắt kết nối datapath |
| `pdown` | int | `0` | Tổng cổng đang DOWN |
| `fault_label` | string | `LINK_FAULT` | Nhãn lỗi $\phi_t$ |
| `duration_seconds` | float | `12.5` | Giây lỗi đã kéo dài |
| `target_dpid` | string | `s1` | Switch bị ảnh hưởng (Tầng Micro) |
| `target_port` | int | `2` | Port bị ảnh hưởng (-1 nếu N/A) |
| `error_cookie` | string | `0x10a` | Cookie của flow rule lỗi |
| `data_quality` | string | `OK` | Chất lượng dữ liệu chu kỳ này |

**Ví dụ dòng CSV:**

```csv
timestamp,ccpu,cres_mem,cvirt_mem,fsent,ferr,fconn,fdisc,pdown,fault_label,duration_seconds,target_dpid,target_port,error_cookie,data_quality
2026-10-16T20:30:00+07:00,1200.123456,45678592,234567680,15000,0,3.0,0,0,NONE,0.0,,-1,,OK
2026-10-16T20:30:10+07:00,1201.456789,45690112,234567680,15012,0,3.0,0,1,PORT_FAULT,10.2,s1,2,,OK
2026-10-16T20:30:20+07:00,1203.789012,45700000,234567680,15045,2,3.0,0,1,PORT_FAULT,20.3,s1,2,0x10a,OK
2026-10-16T20:30:30+07:00,1205.012345,45710240,234567680,15060,2,3.0,0,0,NONE,0.0,,-1,,OK
```

---

## 6. Chiến Lược Xử Lý Lỗi & Data Quality

### 6.1 Ma Trận Xử Lý Trường Hợp Lỗi Thu Thập

| Tình huống | Nguyên nhân | Xử lý | `data_quality` |
|:-----------|:------------|:------|:---------------|
| Prometheus không phản hồi | Prometheus crashed | `last_known` + warning log | `STALE` |
| Metric không tồn tại | Faucet chưa start | `0.0` + warning log | `MISSING`/`PARTIAL` |
| Timeout 5 giây | Network congestion | Retry 3 lần → fallback | `PARTIAL` |
| Giá trị âm hoặc NaN | Bug exporter | Clamp → `0.0` + error log | `INVALID` |
| fault_log.txt không tồn tại | Fault Injector chưa chạy | `phi_t="NONE"`, `duration=0.0` | `OK` |
| Tất cả 8 metrics bình thường | Hoạt động bình thường | Ghi đầy đủ | `OK` |

### 6.2 Xử Lý Đặc Biệt cho `fconn` (Gauge — Không phải Counter)

```
Case 1: fconn = 3.0 (bình thường, 3 switch connected)
  → data_quality = OK, không cần can thiệp

Case 2: fconn = 0.0 + fdisc = 0 (Prometheus/Gauge mới khởi động)
  → Coi là "chưa có dữ liệu" → data_quality = PARTIAL
  → gán fconn = last_known

Case 3: fconn giảm 3.0→2.0 (switch thực sự mất kết nối)
  → Đây là dữ liệu THẬT, không phải lỗi thu thập
  → data_quality = OK
  → Ghi Context Metadata: target_dpid từ "faucet_dp_status == 0"

Case 4: fconn = None (query thất bại hoàn toàn)
  → fallback = last_known → data_quality = STALE
```

---

## 7. Kế Hoạch Kiểm Thử

### 7.1 Unit Tests (10 Test Cases)

| Test Case | Đầu vào | Kết quả Mong đợi | Priority |
|:----------|:--------|:-----------------|:---------|
| `test_query_instant_success` | Mock Prometheus trả `{"value": [ts, "3.0"]}` | `fconn = 3.0` | P0 |
| `test_query_instant_empty` | Mock trả `{"result": []}` | `None` | P0 |
| `test_query_fallback_last_known` | Query thất bại, `last_known = 2.5` | `2.5` | P0 |
| `test_fault_log_active_fault` | `FAULT_START|LINK_FAULT` trong log | `("LINK_FAULT", ~10.0)` | P0 |
| `test_fault_log_no_fault` | file trống | `("NONE", 0.0)` | P0 |
| `test_vector_assembler_complete` | 8 giá trị hợp lệ | `data_quality = OK` | P0 |
| `test_vector_assembler_partial` | 2 giá trị là None | `data_quality = PARTIAL` | P1 |
| `test_vector_assembler_invalid` | `pdown = -1` | `data_quality = INVALID` | P1 |
| `test_fconn_normal_3_switches` | `of_datapath_connected = 3.0` | `fconn = 3.0`, `OK` | P0 |
| `test_fconn_drop_detect` | `of_datapath_connected = 0.0` + `fdisc > 0` | `fconn = 0.0`, context filled | P0 |

### 7.2 Integration Test — Acceptance Criteria

```
✅ Sau 60s (6 chu kỳ): CSV có đúng 6 dòng dữ liệu hợp lệ
✅ Tất cả 8 cột số >= 0 và không có NaN
✅ fconn = 3.0 khi 3 switch kết nối bình thường
✅ Sau PORT_FAULT: pdown tăng lên 1 trong chu kỳ tiếp theo
✅ fault_label = "PORT_FAULT" khớp với nội dung fault_log.txt
✅ Khi Prometheus ngắt 15s: script không crash, data_quality = STALE
✅ fconn giảm 3→0 sau FAUCET_RELOAD → context metadata được ghi đúng
```

---

## 8. Lịch Trình Triển Khai (3 Tuần)

| Tuần | Công việc | Điều Kiện Nghiệm Thu |
|:-----|:----------|:---------------------|
| **Tuần 1** | Cài đặt `prometheus_client.py` + `vector_assembler.py`, viết 10 unit tests | 10/10 tests PASS |
| **Tuần 1** | Cài đặt `fault_log_reader.py`, kiểm thử với fault_log giả lập | Đọc chính xác `phi_t` và `duration_t` |
| **Tuần 2** | Cài đặt `context_metadata_parser.py`, tích hợp với Prometheus thật | Context Metadata đúng cho cả 3 loại lỗi |
| **Tuần 2** | Cài đặt `telemetry_collector.py` (vòng lặp chính 10s) | Chạy ổn định 1 giờ không crash |
| **Tuần 3** | Integration Test: Mininet + Faucet + Collector đồng thời | 7/7 Acceptance Criteria PASS |
| **Tuần 3** | Thu thập dataset thực ≥ 500 dòng CSV, ≥ 5 fault types | CSV đầy đủ, phân bố đều các nhãn lỗi |

---

## 9. Sơ Đồ Phân Nhóm Vector $s_t$ Theo Chức Năng

```
VECTOR TRẠNG THÁI s_t (8 CHIỀU)
═══════════════════════════════════════════════════════════════

Nhóm 1: Sức khỏe Control Plane (3 chiều)
┌────────────────────────────────────────────────────────┐
│  [0] ccpu      → Phát hiện: FLOW_ERROR, FAUCET_RELOAD  │
│  [1] cres_mem  → Phát hiện: Controller overload        │
│  [2] cvirt_mem → Phát hiện: Memory leak dài hạn        │
└────────────────────────────────────────────────────────┘

Nhóm 2: Thống kê OpenFlow (4 chiều)
┌────────────────────────────────────────────────────────┐
│  [3] fsent → Phát hiện: Control plane storm             │
│  [4] ferr  → Phát hiện: FLOW_ERROR (phạt -1*ferr)      │
│  [5] fconn → Phát hiện: Switch disconnect              │
│              (giảm đột ngột → FAUCET_RELOAD/crash)     │
│  [6] fdisc → Phát hiện: FAUCET_RELOAD, switch crash    │
└────────────────────────────────────────────────────────┘

Nhóm 3: Trạng thái Data Plane (1 chiều)
┌────────────────────────────────────────────────────────┐
│  [7] pdown → Phát hiện: LINK_FAULT, PORT_FAULT         │
│              (phạt -2*pdown, thúc đẩy a_t=1)           │
└────────────────────────────────────────────────────────┘

Kết hợp tín hiệu nhận diện lỗi:
  fconn↓ + fdisc↑           → FAUCET_RELOAD  → a_t = 2 (+20)
  pdown↑                    → PORT/LINK FAULT → a_t = 1 (+10/+12)
  ferr↑ + pdown = 0         → FLOW_ERROR      → a_t = 3 (+8)
  ccpu↑ + cres_mem↑ + ferr↑ → Controller overload → a_t = 2
  tất cả = 0                → HEALTHY (NONE)  → a_t = 0 (+2)
```

Mỗi chu kỳ 10 giây, vector $s_t$ này được:
1. **Ghi vào CSV** → phục vụ offline training của PPO Agent.
2. **Gửi trực tiếp vào Gym Environment** → phục vụ online inference trong production.

---

*Tài liệu tham chiếu:*
- [Model_Research_and_Implementation_Plan.md](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/Model_Research_and_Implementation_Plan.md) — Mục 4 (Module 2), Mục 6 (8D State Vector), Mục 7 (Pseudocode 1)
- [cau_truc_tu_phuc_hoi_sdwan.md](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/cau_truc_tu_phuc_hoi_sdwan.md) — Phần 2 (Reactive Self-Healing), Cơ chế Định vị 2 Tầng
