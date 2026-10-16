# Cấu Trúc Tự Phục Hồi (Self-Healing Architecture) Trong Mạng SDN / SD-WAN

Hệ thống tự phục hồi (Self-Healing Framework) cho mạng SDN/SD-WAN được thiết kế theo mô hình **Vòng lặp điều khiển khép kín (Closed-Loop Assurance / MAPE-K)**. Trung tâm của kiến trúc là **Tác tử AI/RL (AI/RL Agent)** đóng vai trò bộ não tự động thu thập số liệu telemetry, phân tích trạng thái mạng, đưa ra quyết định tối ưu và chỉ thị cho các bộ điều khiển SDN (SDN Controller) hoặc thiết bị biên SD-WAN (SD-WAN Edge) thực thi xuống mặt phẳng dữ liệu (Data Plane).

Kiến trúc tự phục hồi được chia làm **2 phần chính**:
1. **Cơ chế Xử lý Tiền phát (Proactive / Predictive Self-Healing)**: Tối ưu gọn nhẹ, tập trung vào việc dự báo đợt bùng nổ lưu lượng hoặc suy giảm chất lượng ứng dụng để chủ động điều hướng lưu lượng **trước khi** xảy ra quá tải hay gián đoạn.
2. **Cơ chế Xử lý Hậu phát (Reactive Self-Healing)**: Sử dụng Tác tử Học tăng cường PPO (Proximal Policy Optimization) kết hợp cơ chế định vị sự cố đa tầng để chọn đúng hành động và nhắm chính xác thiết bị/cổng hư hỏng nhằm khôi phục tức thì **sau khi** xuất hiện lỗi.

---

## 📐 Luồng Kiến Trúc Tổng Quan (Overall Architecture Flow)

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║           LUỒNG KIẾN TRÚC TỰ PHỤC HỒI SDN/SD-WAN  (Left-to-Right Data Flow)                                    ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────┐     ┌──────────────────────────────────┐
│  1. MẶT PHẲNG DỮ LIỆU      │     │  2. LỚP GIÁM SÁT & TELEMETRY     │
│  (Data Plane)               │     │                                  │
│                             │     │  ┌──────────────────────────┐    │
│  ┌─────────────────────┐   │     │  │  Prometheus Server       │    │
│  │ OpenFlow Switches   │   │     │  │  (Scrape Cycle 10s)      │    │
│  │  (s1, s2, s3)       ├──────────►│  └──────────┬─────────────┘    │
│  │ & SD-WAN Edges      │   │  Pull   │             │                  │
│  └──────────┬──────────┘   │  10s    │  ┌──────────▼─────────────┐    │
│             │               │     │  │  Telemetry Thô:          │    │
│  ┌──────────▼──────────┐   │     │  │  • Port Status (up/down) │    │
│  │  Gauge Exporters /  ├──────────►│  │  • Flow Error Counters  │    │
│  │  Node Exporters     │   │     │  │  • Latency, Jitter, Loss │    │
│  └─────────────────────┘   │     │  │  • CPU & RAM Usage       │    │
│                             │     │  └──────────────────────────┘    │
└─────────────────────────────┘     └────────────────┬─────────────────┘
                                                      │
                                                      ▼
                        ┌─────────────────────────────────────────────────────────────────────┐
                        │  3. BỘ NÃO AI AGENT (Decision Engine)                               │
                        │                                                                     │
                        │            ┌───────────────────────────────┐                        │
                        │            │  Feature Collector            │                        │
                        │            │  & Context Parser             │                        │
                        │            └───────┬───────────────┬────────┘                        │
                        │                   │               │                                │
                        │     Chuỗi thời    │   Global      │  Fault Details                 │
                        │     gian & SLA    │   Metrics     │  (DPID/Port)                   │
                        │                   ▼               ▼                                │
                        │  ┌──────────────────────┐  ┌──────────────────────────────────┐   │
                        │  │ NHÁNH 1: TIỀN PHÁT   │  │ NHÁNH 2: HẬU PHÁT               │   │
                        │  │ (Proactive/Predictive)│  │ (Reactive/Recovery)              │   │
                        │  │                      │  │                                  │   │
                        │  │ ┌──────────────────┐ │  │ ┌────────────────────────────┐  │   │
                        │  │ │ Holt-Winters /   │ │  │ │  Vector State s_t (8D)     │  │   │
                        │  │ │ LSTM Predictor   │ │  │ │  ──────────────────────    │  │   │
                        │  │ │ (Dự báo 15-30s)  │ │  │ │  PPO RL Agent              │  │   │
                        │  │ └──────────────────┘ │  │ │  (Policy Net → Action a_t) │  │   │
                        │  │ ┌──────────────────┐ │  │ └────────────────────────────┘  │   │
                        │  │ │ QoE Regression   │ │  │ ┌────────────────────────────┐  │   │
                        │  │ │ Model (SLA)      │ │  │ │  Metadata Parser           │  │   │
                        │  │ └──────────────────┘ │  │ │  (DPID, Port, Cookie)      │  │   │
                        │  └──────────┬───────────┘  │ └────────────────────────────┘  │   │
                        │             │               └──────────────┬───────────────────┘   │
                        └────────────┼────────────────────────────── ┼────────────────────────┘
                                     │                               │
                    Cấu hình né nghẽn│              Action a_t       │  Vị trí hư hỏng
                                     │              + Metadata        │
                                     ▼               ▼               ▼
                        ┌─────────────────────────────────────────────────────────┐
                        │  4. LỚP ĐIỀU KHIỂN & THỰC THI                          │
                        │                                                         │
                        │  ┌──────────────────────────────────────┐              │
                        │  │  Execution Engine                    │              │
                        │  │  (Ghép Action a_t + DPID/Port)       │              │
                        │  └──────────────────┬───────────────────┘              │
                        │                     │                                  │
                        │                     ▼                                  │
                        │  ┌──────────────────────────────────────┐              │
                        │  │  SDN Controller (Faucet)             │              │
                        │  │  / SD-WAN Orchestrator               │              │
                        │  └──────────────────────────────────────┘              │
                        └───────────────────────┬─────────────────────────────────┘
                                                │
                          OpenFlow Port Mod /   │
                          Flow Mod / Sys Cmd    │
                                                ▼
                        ┌───────────────────────────────────────────┐
                        │   Data Plane: Switches s1, s2, s3         │
                        │   & SD-WAN Edges                         │
                        └───────────────────────────────────────────┘
```

---

## Phần 1: Cơ Chế Tự Phục Hồi Tiền Phát (Proactive / Predictive Self-Healing)

Cơ chế Tiền phát không sử dụng các mô hình quá phức tạp gây tiêu tốn tài nguyên tính toán. Hệ thống được **tối ưu gọn nhẹ**, tập trung vào 2 mô hình cốt lõi:
1. **Dự báo Chuỗi thời gian (Traffic Forecasting)**: Mô hình gọn nhẹ (Holt-Winters / LSTM) kết hợp ngưỡng động (Dynamic Thresholding) để dự báo xu hướng băng thông trước $15 - 30$ giây.
2. **Đánh giá QoE / Nhận thức Ứng dụng (App-Aware QoE Model)**: Mô hình Hồi quy tuyến tính / Decision Tree nhẹ đánh giá chất lượng trải nghiệm ứng dụng thời gian thực (VoIP, Video) dựa trên Latency, Jitter, Loss.

---

### Bảng Tổng hợp Phương Pháp Tiền Phát (Đã Tối Ưu)

| Tên phương pháp | Phương pháp / Thuật toán | Đầu vào | Đầu ra | Luồng đi (Decision/Data Flow) | Lí do xảy ra (Trigger) | Cách xử lý vấn đề |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dự báo bùng nổ lưu lượng & Chuyển hướng chủ động** | Dự báo Chuỗi thời gian (Holt-Winters / LSTM gọn nhẹ) + Dynamic Thresholding. | Dữ liệu băng thông quá khứ (Byte count/thời gian) cào định kỳ từ Prometheus. | Dự báo băng thông trong $15-30$ giây tới & Quyết định chuyển tuyến tiền phát. | SD-WAN Edge \(\rightarrow\) Prometheus \(\rightarrow\) Time-Series Predictor \(\rightarrow\) SD-WAN Controller điều hướng tuyến trước khi nghẽn. | Dự báo băng thông đường truyền chính sắp vượt ngưỡng an toàn ($>85\%$ dung lượng) trong vài chục giây tới (ví dụ: do lịch sao lưu dữ liệu tự động). | Tự động chuyển chủ động (preemptively steer) các luồng dữ liệu ưu tiên (VoIP, Video) sang đường truyền phụ trước khi đường truyền chính bị quá tải. |
| **Cân bằng tải đa đường truyền dựa trên Nhận thức QoE** | Mô hình Hồi quy QoE (Linear Regression / Decision Tree) đánh giá chỉ số MOS/QoE. | Chỉ số mạng thời gian thực (Độ trễ, Jitter, Tỉ lệ mất gói) + Mức độ nhạy cảm của ứng dụng. | Điểm QoE Score ($1.0 - 5.0$) và Quyết định chuyển tuyến mid-session. | Telemetry Collector \(\rightarrow\) QoE Engine tính điểm \(\rightarrow\) SD-WAN Controller chỉ định đường truyền mới (MPLS, Broadband, LTE/5G). | Đường truyền chính bị suy giảm chất lượng nhẹ (tăng Jitter/Độ trễ) đe dọa đến SLA của ứng dụng thời gian thực. | Thực hiện chuyển tuyến không gián đoạn (mid-call switching) sang kênh phụ có chất lượng cao hơn ngay trong phiên làm việc mà người dùng không bị rớt cuộc gọi. |

---

### Các Trường Hợp Thực Tế Tiền Phát & Luồng Xử Lý Chi Tiết

#### 🔴 Trường hợp P1: Dự báo bùng nổ lưu lượng do Lịch Sao lưu (Scheduled Data Backup / Traffic Spike)
* **Hiện tượng / Khả năng xảy ra**:
  Vào các khung giờ cố định hoặc đột xuất, hệ thống thực hiện sao lưu dữ liệu tự động (Bulk Data Transfer). Lưu lượng qua liên kết WAN chính tăng vọt từ $30\%$ lên $80\%$ và có xu hướng chạm mốc $100\%$ trong vòng 20 giây tới, đe dọa làm rớt toàn bộ luồng VoIP/Video của doanh nghiệp.
* **Luồng xử lý từng bước**:
  1. **Nhận dữ liệu**: Mô hình dự báo chuỗi thời gian đọc dữ liệu `bytes_sent` từ Prometheus mỗi 5 giây.
  2. **Dự báo xu hướng**: Thuật toán Holt-Winters/LSTM tính toán tốc độ tăng trưởng $\frac{d(\text{Traffic})}{dt}$ và đưa ra dự báo: *Băng thông kênh chính sẽ chạm $92\%$ trong 15 giây tới*.
  3. **Ra quyết định**: Bộ tiền phát kích hoạt quy tắc né tránh: *Chuyển trước các luồng ứng dụng nhạy cảm với độ trễ (VoIP/Video) sang đường truyền phụ 5G/Broadband*.
  4. **Thực thi**: SD-WAN Controller phát bản tin cấu hình xuống SD-WAN Edge Router để cập nhật bảng định tuyến trước khi kênh chính rơi vào nghẽn hoàn toàn.

#### 🔴 Trường hợp P2: Suy giảm chất lượng liên kết (Link Quality Degradation / Jitter Spike)
* **Hiện tượng / Khả năng xảy ra**:
  Đường truyền WAN chính (MPLS) bị suy hao do sự cố nhà mạng, chỉ số Jitter tăng đột ngột từ $5\text{ms}$ lên $40\text{ms}$, tỉ lệ mất gói tăng lên $2\%$. Liên kết chưa sập hoàn toàn (Link Still UP), nhưng chất lượng cuộc gọi hội nghị VoIP bị giật và rè tiếng.
* **Luồng xử lý từng bước**:
  1. **Nhận dữ liệu**: Prometheus thu thập thông số `jitter_ms` và `packet_loss_ratio` từ các mốc kiểm tra.
  2. **Đánh giá QoE**: Mô hình QoE Regression tính điểm chất lượng trải nghiệm $QoE_{VoIP}$ tụt từ $4.2$ xuống $2.8$ (dưới ngưỡng cam kết SLA $3.5$).
  3. **Ra quyết định**: QoE Engine đưa ra quyết định: *Tách luồng VoIP khỏi liên kết MPLS và điều hướng sang liên kết WAN2 (Broadband) đang có Jitter $<5\text{ms}$*.
  4. **Thực thi**: Controller gửi lệnh re-routing giữa phiên (mid-session flow steer), cuộc gọi tiếp tục diễn ra mượt mà mà người dùng không hề hay biết.

---

## Phần 2: Cơ Chế Tự Phục Hồi Hậu Phát (Reactive Self-Healing)

Cơ chế Hậu phát chịu trách nhiệm khôi phục hệ thống **ngay sau khi xuất hiện sự cố thực tế** (đứt kết nối, đứt link, sập port, lỗi luồng OpenFlow, quá tải bộ điều khiển).

---

### 1. Cơ Chế Chọn Hành Động (Lí Do Đằng Sau Của PPO Agent)

Tác tử Học tăng cường PPO (Proximal Policy Optimization) chọn hành động dựa trên **Vector trạng thái 8 chiều ($s_t$)**:
$$s_t = \left[ C_{cpu},\ C_{res\_mem},\ C_{virt\_mem},\ f_{sent},\ f_{err},\ f_{conn},\ f_{disc},\ P_{down} \right]^T$$

#### 🌳 Sơ Đồ Cây Suy Luận Ra Quyết Định PPO Agent ($s_t \rightarrow a_t$)

```
                 Vector Trạng Thái s_t
       ┌──────────────────────────────────────────┐
       │  [C_cpu, C_mem, f_sent, f_err,           │
       │   f_conn, f_disc, P_down]                │
       └──────────────────┬───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Kiểm Tra Chỉ Số s_t  │
              │  (PPO Policy Network) │
              └───┬───────┬───────┬───┘
                  │       │       │       │
   ───────────────┘       │       │       └────────────────────
   │                      │       │                           │
   ▼                      ▼       ▼                           ▼

 Điều kiện 1:        Điều kiện 2:    Điều kiện 3:        Điều kiện 4:
 P_down=0            P_down>0        f_disc>0            f_err>0
 f_err=0             f_err thấp      hoặc                P_down=0
 f_disc=0                            C_cpu>90%

   │                      │               │                    │
   ▼                      ▼               ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  a_t = 0       │  │  a_t = 1       │  │  a_t = 2       │  │  a_t = 3       │
│  [No-op]       │  │  [Reset Ports] │  │  [Restart      │  │  [Bespoke      │
│                │  │                │  │   Switch]      │  │   Self-Heal]   │
│ • Mạng ổn định │  │ • Cổng ảo/vật  │  │ • Mất socket   │  │ • Xung đột     │
│ • Không can    │  │   lý bị sập    │  │   kết nối      │  │   Flow Rules   │
│   thiệp        │  │ • Khởi động    │  │ • Controller   │  │ • Xóa rule     │
│ • Tránh phạt   │  │   lại cổng     │  │   bị quá tải   │  │   hỏng &       │
│   thừa (-1)    │  │   bị ảnh hưởng │  │ • Khởi động    │  │   push luật    │
│                │  │ (Thưởng: +10)  │  │   lại switch   │  │   mới xuống    │
│                │  │                │  │ (Thưởng: +20)  │  │   switch       │
└────────────────┘  └────────────────┘  └────────────────┘  └────────────────┘
```

* **Tại sao không can thiệp thừa?** 
  Nếu mạng bình thường ($\phi_t = \text{NONE}$) mà Agent vẫn thực thi hành động ($1, 2, 3$), hệ thống sẽ **phạt can thiệp thừa (Unnecessary action penalty = -1)**. Điều này giúp Agent học được tính kiên nhẫn và chỉ ra tay khi có sự cố thực sự.

---

### 2. Cơ Chế Định Vị Đúng Thiết Bị Hư Hỏng (Device Targeting Mechanism)

Hệ thống sử dụng **Kiến trúc Định vị 2 Tầng (Two-Tier Targeting Architecture)** để chuyển dịch quyết định cấp Macro thành chỉ thị cấp Micro chính xác:

```
  Switch s1        Prometheus/        Feature Collector      PPO Agent       Execution Engine     Faucet SDN
 (Thiết Bị Đích)   Exporters          & Context Parser      (Macro Level)    (Micro Binding)      Controller
      │                │                      │                   │                 │                   │
      │  (1) Sự cố     │                      │                   │                 │                   │
      │  Port 2 Down   │                      │                   │                 │                   │
      │  of_port_status│                      │                   │                 │                   │
      │  = 0           │                      │                   │                 │                   │
      ├ ─ ─ ─ ─ ─ ─ ─►│                      │                   │                 │                   │
      │                │                      │                   │                 │                   │
      │                │  (2) Telemetry thô    │                   │                 │                   │
      │                │  & Log sự cố         │                   │                 │                   │
      │                ├─────────────────────►│                   │                 │                   │
      │                │                      │                   │                 │                   │
      │                │                      │  ┌────────────────────────────────────────┐             │
      │                │                      │  │  (3) Phân luồng xử lý 2 tầng (PAR)    │             │
      │                │                      │  │                                        │             │
      │                │                      │  │ (3a) Tầng MACRO:                       │             │
      │                │                      ├──┼──► Vector s_t (P_down=1) ─────────────►│             │
      │                │                      │  │                                        │             │
      │                │                      │  │ (3b) Tầng MICRO:                       │             │
      │                │                      │  │  Context Metadata                      │             │
      │                │                      ├──┼──► {target_dpid:"0x1", port:2} ────────────────────►│
      │                │                      │  └────────────────────────────────────────┘             │
      │                │                      │                   │                 │                   │
      │                │                      │  (4) Quyết định   │                 │                   │
      │                │                      │  Macro: a_t=1     │                 │                   │
      │                │                      │  (Reset Ports)    │                 │                   │
      │                │                      │                   ├────────────────►│                   │
      │                │                      │                   │                 │                   │
      │                │                      │                   │  ╔═══════════════════════════════╗  │
      │                │                      │                   │  ║ Cơ chế Ghép Nối              ║  │
      │                │                      │                   │  ║ a_t=1 + {DPID:0x1, Port:2}  ║  │
      │                │                      │                   │  ╚═══════════════════════════════╝  │
      │                │                      │                   │  (5) Lệnh OpenFlow: Reset Port 2   │
      │                │                      │                   │  trên Switch DPID 0x1              │
      │                │                      │                   │                 ├──────────────────►│
      │                │                      │                   │                 │                   │
      │  (6) OpenFlow Port Mod                │                   │                 │                   │
      │  OFPPC_PORT_DOWN → OFPPC_PORT_UP      │                   │                 │                   │
      │◄───────────────────────────────────────────────────────────────────────────────────────────────┤
      │                │                      │                   │                 │                   │
      │  (7) Khôi phục │                      │                   │                 │                   │
      │  Port 2 UP     │                      │                   │                 │                   │
      ├ ─ ─ ─ ─ ─ ─ ─►│                      │                   │                 │                   │
      │                │                      │                   │                 │                   │
```

1. **Tầng Macro (PPO Agent)**: Đọc Vector $s_t$ tổng hợp để quyết định **Nên làm loại hành động nào ($a_t \in \{0, 1, 2, 3\}$)**.
2. **Tầng Micro (Context Parser & Execution Engine)**: Trích xuất **Context Metadata** từ log/metric của Prometheus:
   - `target_dpid`: ID của Switch gặp sự cố (ví dụ: `0x1` tương ứng với switch `s1`).
   - `target_port`: Số cổng gặp sự cố (ví dụ: Port `2`).
   - `error_flow_cookie`: Mã nhận diện luồng bị lỗi (ví dụ: `0x10a`).
3. **Cơ chế Ghép nối (Execution Binding)**:
   SDN Controller tiếp nhận loại hành động $a_t$ từ Agent và kết hợp ngay với `Context Metadata` để tạo thành lệnh OpenFlow hoàn chỉnh gửi tới đúng thiết bị bị hỏng.

---

### 3. Bảng Tổng hợp Chi Tiết Các Trường Hợp Hậu Phát

| Tên phương pháp | Phương pháp / Thuật toán | Đầu vào | Đầu ra | Luồng đi (Decision/Data Flow) | Lí do xảy ra (Trigger) | Cách xử lý vấn đề |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Phục hồi sự cố Cổng / Liên kết (Port & Link Fault Recovery)** | PPO Policy ($a_t=1$) kết hợp Prometheus Metadata Parsing & OpenFlow Port Mod. | Vector $s_t$ ($P_{down} > 0$) + Metric `of_port_status{dp="s1", port="2"} = 0`. | Hành động $a_t = 1$ + Lệnh OpenFlow `PORT_MOD` hạ/nâng đúng Port 2 trên Switch `s1`. | Telemetry \(\rightarrow\) Prometheus \(\rightarrow\) PPO Agent ($a_t=1$) + Context Parser (`s1`, Port 2) \(\rightarrow\) Faucet Controller \(\rightarrow\) Send `OFPPC_PORT_UP` to Switch `s1`. | Sự cố cổng bị ngắt kết nối do lỗi cáp ảo, nhiễu mạng hoặc tiêm lỗi ngẫu nhiên. | Tác tử PPO nhận diện $P_{down}>0$, ra quyết định $a_t=1$. Faucet Controller lấy vị trí `s1`, Port 2 và phát lệnh reset riêng cổng này, khôi phục link trong 20-30s. |
| **Khôi phục Lỗi Luồng OpenFlow (Flow Error Bespoke Self-Heal)** | PPO Policy ($a_t=3$) kết hợp OpenFlow Flow Table Flush & Rule Re-injection. | Vector $s_t$ ($f_{err} > 0, P_{down} = 0$) + Log `of_errors{dp="s2", cookie="0x10a"}`. | Hành động $a_t = 3$ + Lệnh OpenFlow `OFPFC_DELETE` & nạp lại Flow Rules sạch xuống Switch `s2`. | Prometheus \(\rightarrow\) PPO Agent ($a_t=3$) + Context Parser (`s2`, Cookie `0x10a`) \(\rightarrow\) Faucet Controller \(\rightarrow\) Clear & Push Flow Rules to Switch `s2`. | Xung đột luật OpenFlow, lỗi sai cấu hình luồng hoặc tràn bảng lưu lượng làm mất gói tin. | Agent chọn $a_t=3$. Faucet Controller định vị switch `s2`, phát lệnh xóa bỏ luồng hỏng `0x10a` và tái nạp luật mới, khôi phục luồng thông suốt mà không cần reset switch. |
| **Tái khởi động Switch & Khôi phục Controller (Switch & Controller Crash Recovery)** | PPO Policy ($a_t=2$) kết hợp Faucet Auto-Reload & Datapath Handshake Re-establishment. | Vector $s_t$ ($f_{disc} > 0$ hoặc $C_{cpu} > 90\%$) + Metric `faucet_dp_status{dp="s3"} = 0`. | Hành động $a_t = 2$ + Lệnh khởi tạo lại kết nối Datapath / Reload Faucet Controller. | Faucet Log \(\rightarrow\) Prometheus ($f_{disc} > 0$) \(\rightarrow\) PPO Agent ($a_t=2$) \(\rightarrow\) Faucet Controller / Sys Exec \(\rightarrow\) Re-handshake Datapath `s3`. | Switch `s3` bị treo, sập nguồn ảo hoặc mất kết nối Socket với Faucet Controller. | Agent ra quyết định $a_t=2$. Controller phát lệnh tái kết nối Datapath `s3` (nhận thưởng lớn $+20$), đưa switch về lại topology hoạt động. |
| **Duy trì Trạng thái Bình thường (Normal Operation / No-op)** | PPO Policy ($a_t=0$) duy trì trạng thái ổn định. | Vector $s_t$ sạch ($P_{down}=0, f_{err}=0, f_{disc}=0, C_{cpu} < 50\%$). | Hành động $a_t = 0$ (No-op), không phát lệnh can thiệp. | Prometheus \(\rightarrow\) PPO Agent ($a_t=0$) \(\rightarrow\) Faucet Controller không gửi lệnh can thiệp. | Mạng hoạt động ổn định, không có lỗi hay nguy cơ tắc nghẽn. | Giữ nguyên trạng thái cấu hình hiện tại, tránh can thiệp thừa gây mất ổn định mạng và tránh bị hệ thống phạt điểm ($-1$). |

---

### Các Trường Hợp Thực Tế Hậu Phát & Luồng Xử Lý Chi Tiết

#### 🔵 Trường hợp R1: Đứt cổng kết nối trên Switch s1 (Port Down Event)
* **Hiện tượng / Khả năng xảy ra**:
  Cổng số 2 của Switch `s1` bị ngắt kết nối đột ngột (do lỗi cáp, tiêm lỗi ngẫu nhiên hoặc sự cố giao tiếp). Mạng bị đứt một nhánh truyền tải chính.
* **Luồng xử lý từ Nhận dữ liệu $\rightarrow$ Ra quyết định $\rightarrow$ Thực thi đúng thiết bị**:
  1. **Nhận dữ liệu (Telemetry)**: Prometheus thu thập metric `of_port_status{dp_name="s1", port="2"} = 0`.
  2. **Tạo Vector & Trích xuất Metadata**:
     - Feature Collector nạp vào Vector $s_t$: $P_{down} = 1$.
     - Context Parser lưu Metadata: `{target_dpid: "s1", target_port: 2}`.
  3. **Ra quyết định (PPO Agent)**: Mạng MLP của PPO Agent nhận $s_t$ với $P_{down}=1 \rightarrow$ Quyết định chọn **Loại hành động $a_t = 1$ (Reset ports)**.
  4. **Định vị & Thực thi (SDN Controller)**:
     - Execution Engine ghép $a_t = 1$ với `{target_dpid: "s1", target_port: 2}`.
     - Faucet SDN Controller phát bản tin OpenFlow `OFPPC_PORT_DOWN` rồi `OFPPC_PORT_UP` xuống **chính xác Port 2 của Switch s1**.
  5. **Kết quả**: Cổng 2 trên `s1` khởi động lại thành công, $P_{down}$ trở về $0$, Agent nhận điểm thưởng $+10$.

#### 🔵 Trường hợp R2: Lỗi quy tắc luồng OpenFlow trên Switch s2 (Flow Error Event)
* **Hiện tượng / Khả năng xảy ra**:
  Do lỗi tiêm luồng hoặc sai lệch cấu hình (Configuration Drift), bảng Flow Table trên Switch `s2` bị tràn hoặc chứa quy tắc hỏng (Flow Error Cookie `0x10a`), khiến gói tin qua `s2` bị drop liên tục.
* **Luồng xử lý từng bước**:
  1. **Nhận dữ liệu**: Prometheus ghi nhận `of_errors_total{dp_name="s2", error_type="OFPBAC_BAD_OUT_PORT"} > 0`.
  2. **Tạo Vector & Metadata**:
     - Vector $s_t$ ghi nhận $f_{err} = 1, P_{down} = 0$.
     - Context Parser lưu Metadata: `{target_dpid: "s2", error_cookie: "0x10a"}`.
  3. **Ra quyết định**: PPO Agent nhận $s_t$ với $f_{err} > 0 \rightarrow$ Quyết định chọn **Hành động $a_t = 3$ (Bespoke self-heal)**.
  4. **Định vị & Thực thi**:
     - Faucet Controller gửi lệnh OpenFlow `OFPFC_DELETE` xóa quy tắc lỗi `0x10a` trên **Switch s2**.
     - Ngay sau đó, Faucet tái tạo và đẩy lại luật chuyển tiếp sạch (Fresh Flow Rule) xuống `s2`.
  5. **Kết quả**: Luồng dữ liệu qua `s2` thông suốt trở lại, $f_{err}$ trở về $0$.

#### 🔵 Trường hợp R3: Mất kết nối Datapath giữa Switch s3 và Controller (Switch Disconnect Event)
* **Hiện tượng / Khả năng xảy ra**:
  Switch `s3` bị mất kết nối OpenFlow Socket với Faucet Controller (Switch Crash hoặc đứt liên kết điều khiển Control Plane).
* **Luồng xử lý từng bước**:
  1. **Nhận dữ liệu**: Prometheus/Gauge phát hiện `faucet_dp_status{dp_name="s3"} = 0`.
  2. **Tạo Vector & Metadata**:
     - Vector $s_t$ ghi nhận $f_{disc} = 1$.
     - Context Parser lưu Metadata: `{target_dpid: "s3"}`.
  3. **Ra quyết định**: PPO Agent nhận $s_t$ với $f_{disc} > 0 \rightarrow$ Quyết định chọn **Hành động $a_t = 2$ (Restart switch)**.
  4. **Định vị & Thực thi**:
     - System Execution Engine phát lệnh quản trị tái khởi động socket kết nối đối với **Switch s3** (`systemctl restart mininet-switch@s3`).
  5. **Kết quả**: Switch `s3` thực hiện lại bắt tay (Handshake) OpenFlow thành công với Faucet Controller, $f_{disc}$ về $0$, Agent nhận điểm thưởng lớn $+20$.

---

## 🔄 Tổng Kết Vòng Lặp Toàn Diện (End-to-End Self-Healing Sequence)

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║         VÒNG LẶP TỰ PHỤC HỒI KHÉP KÍN (Closed-Loop, 10s/cycle)                            ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

   Data Plane             Prometheus            AI / PPO RL Agent         SDN / SD-WAN
  (s1, s2, s3)          (10s Cycle)             (Decision Brain)           Controller
       │                     │                         │                       │
       ║◄══════════════════════════════════════════════════════════════════════╗
       ║                     ║                         ║                       ║
       ║     ┌───────────────────────────────────────────────────────────────────────────────┐
       ║     │     CHU KỲ TỰ PHỤC HỒI KHÉP KÍN (lặp mỗi 10 giây)                           │
       ║     │                                                                               │
       ║     │  (1) Thu thập metrics thô: Port Status, Flow Errors, Latency, Jitter, CPU    │
       ╠═════════════════════►║                         ║                       ║            │
       ║     │                                                                               │
       ║     │               ║  (2) Truyền Vector s_t + Context Metadata                    │
       ║     │               ║      (Target DPID / Port / Cookie)                           │
       ║     │               ╠════════════════════════►║                       ║            │
       ║     │                                                                               │
       ║     │                    ┌──────────────────────────────────────────────────┐       │
       ║     │                    │  PHÂN NHÁNH XỬ LÝ (alt / else)                 │       │
       ║     │                    │                                                  │       │
       ║     │                    │  [NHÁNH 1: TIỀN PHÁT - Proactive]               │       │
       ║     │                    │   • Dự báo băng thông Holt-Winters / LSTM       │       │
       ║     │                    │   • Tính điểm QoE                               │       │
       ║     │                    │   • Preemptive Steering ──────────────────────────────►║
       ║     │                    │                                                  │       │
       ║     │                    │  [NHÁNH 2: HẬU PHÁT - Reactive]                │       │
       ║     │                    │   • PPO chọn a_t trong {0,1,2,3} từ s_t        │       │
       ║     │                    │   • Ghép a_t + Metadata                         │       │
       ║     │                    │   • Chỉ định đúng Switch/Port hỏng ──────────────────►║
       ║     │                    └──────────────────────────────────────────────────┘       │
       ║     │                                                                               │
       ║     │  (3) Gửi lệnh OpenFlow (Port Mod / Flow Mod / Sys Cmd) tới Switch đích       │
       ╠◄════════════════════════════════════════════════════════════════════════╣            │
       ║     │                                                                               │
       ║     │  (4) Trả về trạng thái mới s_(t+1) và Reward r_t                            │
       ╠ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─►║                    ║            │
       ║     │                                                                               │
       ║     └───────────────────────────────────────────────────────────────────────────────┘
       ║                     ║         (Tiếp tục chu kỳ tiếp theo...)         ║
       │                     │                         │                       │
```

---

Với thiết kế sơ đồ cải tiến này:
- **Luồng dữ liệu (Data Flow)** đi từ Trái sang Phải (Left-to-Right) rõ ràng giữa 4 lớp chức năng.
- **Cây suy luận (Decision Tree)** của PPO Agent trực quan hóa rõ ràng 4 nhánh điều kiện ứng với 4 loại hành động $a_t \in \{0, 1, 2, 3\}$.
- **Sơ đồ tương tác (Sequence Diagram)** minh họa chính xác cơ chế ghép nối giữa Loại hành động (Tầng Macro) và Vị trí hư hỏng (Tầng Micro) để tác động xuống đúng thiết bị bị hỏng.
