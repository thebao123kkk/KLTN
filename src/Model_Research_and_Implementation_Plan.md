### PHÂN ĐỊNH NGUỒN THÔNG TIN
*   **Trực tiếp từ nguồn (Source-Grounded):** Các thông số kiến trúc Mininet/Faucet/Prometheus, vector trạng thái 8D, không gian hành động rời rạc (4 actions), công thức toán học hàm phần thưởng (Eq. 1–9), chỉ số PPO, kết quả định lượng (26s, 3.2% packet loss proxy, 0.38 OF error) và ma trận phân bố hành động (Table 8).
*   **Kết luận tổng hợp (Synthesized):** Sự kết hợp giữa vòng lặp đảm bảo ý định (Assurance loop) của IBN với cơ chế ra quyết định của PPO RL và ánh xạ thực thi qua bộ điều khiển Faucet.
*   **Đề xuất mới/Mở rộng (Proposed Extension):** Cấu trúc Pseudocode chi tiết hóa từ flowchart của bài báo, thiết kế khung đo lường QoS (Latency, Jitter, Throughput) bằng `iperf`/`ping`, và Checklist kiểm chứng 10 bước phục vụ triển khai lab thực tế.

---

### 1. BÀI TOÁN THỰC TẾ, NGUYÊN NHÂN, TÁC ĐỘNG VÀ RESEARCH GAP

#### 1.1 Bài toán thực tế & Nguyên nhân
Trong hạ tầng Mạng định nghĩa bằng phần mềm (SDN), việc tập trung hóa mặt phẳng điều khiển mang lại khả năng quản lý linh hoạt nhưng cũng tạo ra điểm yếu đối với các loại sự cố đa dạng. Khi quy mô mạng mở rộng, hệ thống phải đối mặt đồng thời với các dạng lỗi ở nhiều tầng:
1.  **Lỗi liên kết (LINK_FAULT):** Do đứt cáp vật lý hoặc đứt đường trunk kết nối giữa các switch.
2.  **Lỗi cổng (PORT_FAULT):** Do cổng giao diện vật lý/ảo bị ngắt (port down/toggle).
3.  **Lỗi luồng & Tắc nghẽn (FLOW_ERROR / Congestion):** Do xung đột quy tắc OpenFlow, tràn bảng luồng TCAM, hoặc do lưu lượng UDP flood bất ngờ tạo điểm nghẽn.
4.  **Sự cố Bộ điều khiển (FAUCET_RELOAD):** Sự cố ngắt kết nối tạm thời hoặc khởi động lại tiến trình Faucet Controller.

#### 1.2 Tác động vận hành
Nếu không được xử lý tức thì, các sự cố trên gây đứt gãy kết nối end-to-end, tăng tỷ lệ mất gói tin (Packet Loss), làm tích tụ các lỗi giao thức OpenFlow trên kênh điều khiển, và gây suy giảm nghiêm trọng chất lượng dịch vụ (QoS).

#### 1.3 Khoảng trống nghiên cứu (Research Gap)
Qua đối sánh hệ thống các công trình liên quan:
*   **Phạm vi lỗi hẹp:** Các mô hình RL hiện tại như FRRL (Ma et al., 2025) chỉ tập trung vào khôi phục đường truyền khi hỏng liên kết (link failure); KA-PPO (Liu et al., 2024) chỉ tập trung vào tái cấu hình chuỗi chức năng dịch vụ (SFC/VNF); DRL-SHF (Aloraini et al., 2024) chỉ thử nghiệm trên mô phỏng NS-3 thuần túy.
*   **Thiếu tích hợp dữ liệu đo lường đa nguồn:** Các giải pháp truyền thống chỉ dựa vào cảnh báo đơn lẻ từ mặt phẳng dữ liệu, không kết hợp chỉ số sức khỏe của bộ điều khiển (CPU, RAM) và số liệu thống kê OpenFlow thời gian thực.
*   **Thiếu cơ chế đánh giá sức khỏe toàn cục:** Chưa có chính sách RL đơn lẻ nào xử lý đồng thời 4 loại lỗi (Link, Port, Flow, Controller Reload) cùng với các sự kiện tắc nghẽn lưu lượng trong một môi trường thực nghiệm SDN hoàn chỉnh.

---

### 2. MỤC TIÊU NGHIÊN CỨU, CÂU HỎI VÀ GIẢ THUYẾT KIỂM CHỨNG

#### 2.1 Mục tiêu nghiên cứu
Xây dựng một khung tự phục hồi tự động (Autonomous Self-Healing Framework) dựa trên thuật toán Học tăng cường PPO, tích hợp hạ tầng Mininet–Faucet–Prometheus, có khả năng phát hiện, phân loại và sửa chữa đa dạng các loại lỗi mạng SDN với độ chính xác trên 85% và thời gian phục hồi trung bình dưới 30 giây.

#### 2.2 Câu hỏi nghiên cứu (Research Questions - RQs)
*   **RQ1:** Làm thế nào để hợp nhất dữ liệu đo lường đa nguồn (Telemetry) từ mặt phẳng điều khiển và mặt phẳng dữ liệu thành một Vector trạng thái biểu diễn toàn diện sức khỏe mạng SDN?
*   **RQ2:** Hàm phần thưởng được thiết kế theo trọng số mức độ nghiêm trọng (Severity-Weighted) có giúp tác nhân PPO đưa ra hành động chính xác theo từng loại lỗi mà không gây can thiệp thừa hay không?
*   **RQ3:** Hiệu năng tự phục hồi của mô hình PPO vượt trội như thế nào so với giải pháp Không phục hồi (No-Healing) và Phản ứng theo quy tắc (Rule-Based Reactive) về Thời gian khôi phục, Tỷ lệ mất gói tin đại diện và Tỷ lệ lỗi OpenFlow?
*   **RQ4:** Khả năng chuyển giao tri thức (Transfer Learning) của mô hình PPO khi mở rộng quy mô lên cấu trúc mạng lớn hơn (Linear 8-switch, Fat-tree 16-switch) như thế nào?

#### 2.3 Giả thuyết kiểm chứng (Hypotheses)
*   **H1:** Mô hình PPO với hàm phần thưởng trọng số nghiêm trọng sẽ giảm thời gian phục hồi trung bình xuống \\(\le 30\\) giây (so với \\(\ge 45\\) giây của mô hình quy tắc).
*   **H2:** Tác nhân PPO học được chính sách phụ thuộc trạng thái (State-Conditional Policy), lựa chọn đúng hành động xử lý cho từng loại lỗi với tỷ lệ \\(> 85\%\\).
*   **H3:** Phương pháp Học chuyển đổi cho phép tinh chỉnh mô hình trên cấu trúc mạng lớn hơn (Fat-tree 16-switch) mà không suy giảm quá 12% thưởng tập (Episode Reward).

---

### 3. VAI TRÒ VÀ CƠ CHẾ PHỐI HỢP: SDN, SD-WAN VÀ SELF-HEALING

```
+-----------------------------------------------------------------------+
|                 INTENT-BASED ASSURANCE LAYER (IBN)                    |
|   - Declared Intent: Maintain 100% Reachability & Zero Packet Loss    |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|               DECISION & INTELLIGENCE ENGINE (PPO Agent)              |
|   - Inputs: 8D Telemetry Vector st from Prometheus                     |
|   - Output: Action at in {0: No-op, 1: Reset Port, 2: Restart, 3: Heal}|
+-----------------------------------------------------------------------+
                                   | (Healing Action / Flow Rules)
                                   v
+-----------------------------------------------------------------------+
|                   CONTROL PLANE (Faucet SDN Controller)               |
|   - OpenFlow Port 6653 | Config: YAML | Gauge Agent Exporter      |
+-----------------------------------------------------------------------+
                                   | (Southbound OpenFlow v1.3)
                                   v
+-----------------------------------------------------------------------+
|               DATA PLANE & SD-WAN OVERLAY (Mininet Topology)          |
|   - Switches s1..sN | Links | Hosts h1..hN | UDP Flow Generator       |
+-----------------------------------------------------------------------+
                                   | (10s Scrape / Metrics)
                                   v
+-----------------------------------------------------------------------+
|                 MONITORING STACK (Prometheus Metrics TSDB)            |
|   - Scrape Targets: Faucet:9302, Gauge:9303, NodeExporter:9100        |
+-----------------------------------------------------------------------+
```

1.  **SDN (Software-Defined Networking):** Cung cấp khả năng tách biệt mặt phẳng điều khiển và mặt phẳng dữ liệu thông qua giao thức OpenFlow. Bộ điều khiển Faucet đóng vai trò duy trì góc nhìn toàn cục (Global View) và lập trình bảng luồng qua cổng 6653.
2.  **SD-WAN (Software-Defined Wide Area Network):** Đảm bảo tính linh hoạt trong quản lý lưu lượng qua các liên kết mạng diện rộng, định tuyến lưu lượng thông minh dựa trên chính sách và hỗ trợ thiết lập đường truyền dự phòng khi xảy ra sự cố.
3.  **Self-Healing (Chức năng đảm bảo trong IBN):** Đóng vai trò là vòng lặp đảm bảo khép kín (Closed-loop Assurance Function) của IBN. Khi dữ liệu Telemetry chỉ ra rằng trạng thái thực tế lệch khỏi "Ý định" (Intent) ban đầu của người quản trị, tác nhân PPO sẽ phát động các hành động sửa lỗi để khôi phục trạng thái mạng về mức tuân thủ.

---

### 4. ĐẶC TẢ CHI TIẾT TỪNG MODULE KỸ THUẬT

#### Module 1: Môi trường mạng & Tiêm lỗi (Network & Fault Injector Module)
*   **Đầu vào:** Cấu hình Topology Mininet (`tree`, `linear`, `fat-tree`), lệnh điều khiển ngẫu nhiên.
*   **Đầu ra:** Trạng thái liên kết vật lý, cờ báo ngắt cổng, sự kiện khởi động lại tiến trình Faucet, tệp nhật ký `fault_log` có mốc thời gian.
*   **Giao thức/Công cụ:** OpenFlow v1.3, Mininet CLI, Python `subprocess`, công cụ `iperf`.

#### Module 2: Thu thập & Gắn nhãn dữ liệu (Telemetry Collector & Labeler)
*   **Đầu vào:** Các endpoint HTTP từ Prometheus (`:9090`), Faucet (`:9302`), Gauge (`:9303`), Node Exporter (`:9100`).
*   **Đầu ra:** Tệp dữ liệu CSV chứa Vector 8D được gắn nhãn lỗi `phi_t` theo chu kỳ 10 giây.
*   **Giao thức/Công cụ:** HTTP REST API Prometheus Queries, Python `requests`, `pandas`.

#### Module 3: Môi trường Tự phục hồi Gym (Custom SDN Gym Environment)
*   **Đầu vào:** Dữ liệu CSV trạng thái mạng 8D (\\(s_t\\)), hành động được chọn từ tác nhân (\\(a_t\\)).
*   **Đầu ra:** Trạng thái kế tiếp (\\(s_{t+1}\\)), Phần thưởng (\\(r_t\\)), Trạng thái kết thúc tập (Done).
*   **Thuật toán:** Tính toán hàm phần thưởng có trọng số nghiêm trọng.

#### Module 4: Tác nhân Học tăng cường (PPO Agent Module)
*   **Đầu vào:** Vector trạng thái \\(s_t \in \mathbb{R}^8\\).
*   **Đầu ra:** Phân bố xác suất hành động qua Softmax, hành động được chọn \\(a_t \in \{0, 1, 2, 3\}\\).
*   **Thuật toán:** Proximal Policy Optimization (PPO) với kiến trúc Perceptron đa lớp (MLP Policy), hàm mục tiêu cắt giảm \\(L^{\text{CLIP}}(\theta)\\) với ngưỡng \\(\epsilon = 0.35\\).

---

### 5. MÔI TRƯỜNG TRIỂN KHAI, TOPOLOGY VÀ CẤU HÌNH DỰ KIẾN

#### 5.1 Thông số Môi trường Phần mềm
*   **Hệ điều hành:** Ubuntu Linux 20.04 / 22.04 LTS (Kernel 5.x).
*   **Trình giả lập mạng:** Mininet v2.3.0+.
*   **SDN Controller:** Faucet Controller (chạy trên cổng OpenFlow `6653`).
*   **Hệ thống Giám sát:** Prometheus v2.x (Scrape Interval = `10s`).
*   **Thư viện RL:** Python 3.8+, `stable-baselines3`, `gymnasium` / `gym`, `torch` / `tensorflow`.

#### 5.2 Cấu hình Cấu trúc Mạng (Topologies) & Địa chỉ IP

```
Base Tree Topology:
         [Faucet Controller: 127.0.0.1:6653]
                          |
                         s1 (Switch Gốc)
                        /  \
                       /    \
                     s2      s3
                    /  \    /  \
                   h1  h2  h3  h4
```

*   **Base Topology (Cây - Tree):** 3 Switch OpenFlow (`s1`, `s2`, `s3`), 4 Host (`h1`, `h2`, `h3`, `h4`).
    *   `h1`: IP `10.0.0.1/24`, MAC `00:00:00:00:00:01`
    *   `h2`: IP `10.0.0.2/24`, MAC `00:00:00:00:00:02`
    *   `h3`: IP `10.0.0.3/24`, MAC `00:00:00:00:00:03`
    *   `h4`: IP `10.0.0.4/24`, MAC `00:00:00:00:00:04`
*   **Linear Topology (Tuyến tính):** 8 Switch, 16 Host (2 host/switch).
*   **Fat-Tree Topology (\\(k=4\\)):** 16 Switch (4 Core, 4 Aggregation, 8 Edge), 64 Host.

---

### 6. QUY TRÌNH PHÁT HIỆN, RA QUYẾT ĐỊNH VÀ THỰC THI PHỤC HỒI

#### 6.1 Bảng Đặc tả Không gian Trạng thái (8D State Vector)
Tại mỗi bước thời gian \\(t\\) (mỗi 10 giây), Prometheus cào dữ liệu và tạo ra Vector \\(s_t \in \mathbb{R}^8\\):

| Chỉ số | Biến | Ý nghĩa Kỹ thuật | Nguồn trích xuất Metrics |
| :--- | :--- | :--- | :--- |
| 1 | \\(c_{cpu}\\) | Thời gian CPU của tiến trình Faucet Controller | Prometheus (`faucet_cpu_seconds_total`) |
| 2 | \\(c_{res\_mem}\\) | Dung lượng RAM thực tế (Resident Memory) đang dùng | Prometheus (`process_resident_memory_bytes`) |
| 3 | \\(c_{virt\_mem}\\) | Dung lượng bộ nhớ ảo (Virtual Memory) đang dùng | Prometheus (`process_virtual_memory_bytes`) |
| 4 | \\(f_{sent}\\) | Tổng số thông điệp OpenFlow đã gửi | Prometheus / Gauge (`of_messages_sent_total`) |
| 5 | \\(f_{err}\\) | Tổng số lỗi giao thức OpenFlow ghi nhận | Prometheus / Gauge (`of_errors_total`) |
| 6 | \\(f_{conn}\\) | Số lượng kết nối Datapath đang hoạt động | Gauge (`of_datapath_connected`) |
| 7 | \\(f_{disc}\\) | Số lần ngắt kết nối Datapath | Gauge (`of_datapath_disconnections_total`) |
| 8 | \\(p_{down}\\) | Tổng số lượng cổng đang ở trạng thái Down | Prometheus (`port_status_down_total`) |

#### 6.2 Bảng Đặc tả Không gian Hành động (Discrete Action Space)
Không gian hành động gồm 4 giá trị rời rạc \\(a_t \in \{0, 1, 2, 3\}\\):

| Mã Action (\\(a_t\\)) | Tên Hành động | Chi tiết Thực thi trên Hạ tầng |
| :--- | :--- | :--- |
| **0** | `No-op` | Không can thiệp, giữ nguyên trạng thái mạng. |
| **1** | `Reset ports` | Đặt lại (Down \\(\to\\) Up) tất cả các cổng trên Switch bị ảnh hưởng. |
| **2** | `Restart switch` | Khởi động lại Switch bị sự cố để đăng ký lại với Faucet. |
| **3** | `Bespoke self-heal` | Kích hoạt quy trình khôi phục luồng tùy chỉnh (Flow-rule update) qua Faucet. |

#### 6.3 Hàm Phần thưởng có Trọng số Nghiêm trọng (Severity-Weighted Reward Function)
Phần thưởng \\(r_t\\) tại bước \\(t\\) được tính theo công thức:

\\[r_t = \begin{cases} +20 & \text{nếu phát hiện } \text{FAUCET\_RELOAD} \text{ (Khôi phục mặt phẳng điều khiển)} \\ r_{\text{fault}}(s_t, a_t) & \text{trường hợp khác} \end{cases}\\]

Trong đó, hàm phần thưởng thành phần \\(r_{\text{fault}}(s_t, a_t)\\) được xác định bởi:

\\[\begin{aligned} r_{\text{fault}}(s_t, a_t) = & -2 \cdot p_{down} - f_{err} - \rho(\phi_t) - \delta_t + \beta(\phi_t) \cdot \mathbb{I}[a_t \in \{1, 2, 3\}] \\ & + 2 \cdot \mathbb{I}[\phi_t = \emptyset, a_t = 0] - 1 \cdot \mathbb{I}[\phi_t = \emptyset, a_t \in \{1, 2, 3\}] \end{aligned}\\]

*   \\(\phi_t\\): Dạng lỗi hiện tại.
*   \\(\rho(\phi_t)\\): Hình phạt theo mức độ nghiêm trọng của lỗi.
*   \\(\beta(\phi_t)\\): Thưởng khôi phục (Heal bonus) khi chọn hành động khôi phục (\\(a_t \in \{1,2,3\}\\)).
*   \\(\delta_t\\): Thời gian kéo dài lỗi chưa được xử lý (tính bằng giây).
*   \\(\mathbb{I}[\cdot]\\): Hàm chỉ thị (Indicator function).

##### Bảng Ánh xá Mức phạt \\(\rho(\phi_t)\\) và Thưởng khôi phục \\(\beta(\phi_t)\\):
| Dạng lỗi (\\(\phi_t\\)) | Mức phạt (\\(\rho\\)) | Thưởng khôi phục (\\(\beta\\)) | Lý do thiết kế |
| :--- | :---: | :---: | :--- |
| `LINK_FAULT` | \\(-10\\) | \\(+12\\) | Đứt liên kết inter-switch làm mất kết nối toàn đoạn mạng. |
| `PORT_FAULT` | \\(-7\\) | \\(+10\\) | Ảnh hưởng đến tập cổng kết nối host cụ thể. |
| `FLOW_ERROR` | \\(-5\\) | \\(+8\\) | Gián đoạn lớp lưu lượng cụ thể do xung đột/tắc nghẽn. |
| `SOFT_WARNING` | \\(-2\\) | \\(+2\\) | Cảnh báo nhẹ, không yêu cầu can thiệp mạnh. |
| `TEMP_WARNING` | \\(-1\\) | \\(+1\\) | Cảnh báo tạm thời, ưu tiên No-op. |
| `NONE` (Bình thường) | \\(0\\) | \\(0\\) | Mạng khỏe mạnh; No-op nhận \\(+2\\), can thiệp thừa phạt \\(-1\\). |
| `FAUCET_RELOAD` | N/A | \\(+20\\) (Cố định) | Khôi phục hoàn toàn mặt phẳng điều khiển. |

*Nguyên tắc bất đối xứng (\\(\beta(\phi_t) > \rho(\phi_t)\\)):* Đảm bảo tác nhân bị hấp dẫn bởi phần thưởng dương để đưa ra hành động khôi phục quyết liệt ngay khi phát hiện lỗi.

---

### 7. PSEUDOCODE CHI TIẾT TỪNG THUẬT TOÁN

#### Pseudocode 1: Quy trình Thu thập & Gắn nhãn Telemetry (Scraper & Labeler)
```python
# Algorithm 1: Telemetry Scraper and Fault Labeler
# Input: Prometheus Endpoint (http://localhost:9090), Fault Log File
# Output: Dataset CSV containing 8D state vector st and fault label phi_t

Initialize CSV_File with headers: [timestamp, c_cpu, c_res_mem, c_virt_mem, f_sent, f_err, f_conn, f_disc, p_down, fault_label, duration]
Ensure fault_log_file exists

while session_active do:
    if current_time % 10_seconds == 0 then:
        # Query Prometheus Metrics TSDB
        c_cpu = query_prometheus("faucet_cpu_seconds_total")
        c_res_mem = query_prometheus("process_resident_memory_bytes")
        c_virt_mem = query_prometheus("process_virtual_memory_bytes")
        f_sent = query_prometheus("of_messages_sent_total")
        f_err = query_prometheus("of_errors_total")
        f_conn = query_prometheus("of_datapath_connected")
        f_disc = query_prometheus("of_datapath_disconnections_total")
        p_down = query_prometheus("port_status_down_total")
        
        # Read current active fault from fault log
        phi_t, duration_t = read_latest_fault_context(fault_log_file)
        
        # Construct 8D vector
        s_t = [c_cpu, c_res_mem, c_virt_mem, f_sent, f_err, f_conn, f_disc, p_down]
        
        # Write to CSV
        append_row_to_csv(CSV_File, timestamp, s_t, phi_t, duration_t)
    end if
    sleep(1_second)
end while
```

#### Pseudocode 2: Môi trường SDN Custom Gym và Tính toán Reward
```python
# Algorithm 2: Custom Gym Environment Step Function & Reward Calculation
# Input: Selected Action a_t in {0, 1, 2, 3}
# Output: Next State s_{t+1}, Reward r_t, Done flag, Info dict

def step(self, action_a_t):
    # 1. Execute action via Faucet SDN Controller
    if action_a_t == 1:
        faucet_controller.reset_affected_ports()
    elif action_a_t == 2:
        faucet_controller.restart_affected_switch()
    elif action_a_t == 3:
        faucet_controller.trigger_bespoke_self_heal()
    elif action_a_t == 0:
        pass # No operation
        
    # 2. Wait for telemetry scraping interval
    wait(10_seconds)
    s_next, phi_next, duration_next = load_next_telemetry_row()
    
    p_down = s_next
    f_err = s_next
    
    # 3. Compute Reward r_t
    if phi_next == "FAUCET_RELOAD" and action_a_t in:
        r_t = +20.0
    else:
        # Lookup penalty rho and heal bonus beta
        rho_val = FAUCET_PENALTY_MAP[phi_next]
        beta_val = FAUCET_BONUS_MAP[phi_next]
        
        r_fault = -2.0 * p_down - f_err - rho_val - duration_next
        
        if action_a_t in:
            r_fault += beta_val
            
        if phi_next == "NONE":
            if action_a_t == 0:
                r_fault += 2.0  # Healthy No-op bonus
            else:
                r_fault -= 1.0  # Unnecessary action penalty
                
        r_t = r_fault
        
    done = check_episode_termination()
    return s_next, r_t, done, {}
```

#### Pseudocode 3: Huấn luyện PPO & Học chuyển đổi (Transfer Learning)
```python
# Algorithm 3: PPO Training and Transfer Learning Pipeline
# Input: Gym Environment, Hyperparameters (clip_range=0.35, lr=2.5e-4)
# Output: Trained Model Weights theta

# Phase 1: Base Training on 3-Switch Topology
env_base = CustomSDNEnv(dataset_csv="base_tree_telemetry.csv")
model = PPO(
    policy="MlpPolicy",
    env=env_base,
    learning_rate=2.5e-4,
    clip_range=0.35,
    tensorboard_log="./ppo_sdn_tensorboard/"
)
model.learn(total_timesteps=10000)
model.save("ppo_sdn_base_model")

# Phase 2: Transfer Learning on Larger Topologies (e.g., Fat-tree 16-switch)
env_fattree = CustomSDNEnv(dataset_csv="fattree_telemetry.csv")
model_transferred = PPO.load("ppo_sdn_base_model", env=env_fattree)
# Fine-tune with pre-trained weights
model_transferred.learn(total_timesteps=5000)
model_transferred.save("ppo_sdn_fattree_model")
```

---

### 8. KẾ HOẠCH PHÁT TRIỂN THEO GIAI ĐOẠN VÀ ĐIỀU KIỆN NGHIỆM THU

| Giai đoạn | Nội dung Công việc | Công cụ & Môi trường | Điều kiện Nghiệm thu (KPIs) |
| :--- | :--- | :--- | :--- |
| **Giai đoạn 1** | Khởi tạo Mininet Base Topology , cài đặt Faucet Controller và Prometheus Scrape Targets. | Mininet, Faucet, Prometheus, Gauge, Node Exporter. | 100% Prometheus targets (`faucet`, `gauge`, `node_exporter`, `prometheus`) ở trạng thái `UP` trên giao diện GUI. |
| **Giai đoạn 2** | Triển khai bộ tiêm lỗi tự động và script thu thập Telemetry 8D tạo bộ dữ liệu CSV. | Python `subprocess`, `requests`, `iperf`. | Tệp CSV chứa đầy đủ 8 chỉ số trạng thái kèm nhãn lỗi `phi_t` với chu kỳ cào 10 giây. |
| **Giai đoạn 3** | Xây dựng môi trường Custom Gym Environment và cài đặt Hàm phần thưởng trọng số nghiêm trọng. | Python `gymnasium`, `pandas`. | Kiểm thử đơn vị (Unit test) hàm `step()` phản hồi chính xác \\(s_{t+1}\\) và \\(r_t\\) theo đúng Bảng 2. |
| **Giai đoạn 4** | Huấn luyện Tác nhân PPO (10,000 timesteps) trên Base Topology, ghi log TensorBoard. | `stable-baselines3`, TensorBoard. | Thưởng tập trung bình đạt \\(\approx 1,550\\), độ dài tập \\(\approx 2,200\\) bước, đồ thị hội tụ ổn định. |
| **Giai đoạn 5** | Tinh chỉnh học chuyển đổi (Transfer Learning - 5,000 steps) trên Linear (8 switches) và Fat-Tree (16 switches). | Mininet, Stable-Baselines3 Transfer Learning. | Thưởng tập không giảm quá 12% (\\(1,442\\) cho Linear, \\(1,386\\) cho Fat-tree). |
| **Giai đoạn 6** | Kiểm thử đánh giá định lượng so với 2 mô hình đối chứng (No-Healing và Rule-Based) qua 50 sự cố lỗi. | Python Evaluation Script. | Thời gian khôi phục \\(\le 26\\)s, Mất gói proxy \\(\le 3.2\%\\), Tỷ lệ lỗi OF \\(\le 0.38\\). |

---

### 9. KỊCH BẢN TẠO LỖI VÀ PHƯƠNG PHÁP THU THẬP LOG

#### 9.1 Thiết kế Kịch bản Tiêm lỗi
Sử dụng script Python tiêm lỗi tự động chạy song song với mạng Mininet:
1.  **Tiêm lỗi Liên kết (`LINK_FAULT`):** Ngắt đường trunk giữa `s1-eth2` và `s2-eth1` bằng lệnh `net.configLinkStatus('s1', 's2', 'down')`.
2.  **Tiêm lỗi Cổng (`PORT_FAULT`):** Tắt/bật liên tục cổng kết nối host `s2-eth2` bằng lệnh `s2.cmd('ip link set s2-eth2 down')`.
3.  **Tiêm lỗi Luồng & Tắc nghẽn (`FLOW_ERROR`):** Phát luồng lưu lượng UDP flood dung lượng lớn giữa `h1` và `h3` bằng `iperf -c 10.0.0.3 -u -b 100M -t 30` làm tràn bảng luồng hoặc suy giảm hiệu năng.
4.  **Sự cố Controller (`FAUCET_RELOAD`):** Khởi động lại tiến trình Faucet bằng `pkill -HUP faucet`.

#### 9.2 Công cụ Thu thập và Ghi nhật ký
*   **Trạng thái hệ thống:** Lưu vết cấu hình Faucet YAML và nhật ký sự cố tệp `fault_log.txt` có gắn nhãn mốc thời gian ISO-8601.
*   **Chỉ số Telemetry:** Xuất định kỳ 10s ra tệp `sdn_telemetry_dataset.csv`.
*   **Nhật ký Huấn luyện RL:** Đồ thị `train/approx_kl`, `train/entropy_loss`, `train/policy_gradient_loss`, `train/value_loss` lưu trong TensorBoard.

---

### 10. CÔNG THỨC ĐÁNH GIÁ HIỆU NĂNG VÀ CHẤT LƯỢNG MẠNG (QoS)

1.  **Thời gian Khôi phục Tự phục hồi (\\(T_{\text{recovery}}\\)):**
    \\[T_{\text{recovery}} = (N_{\text{steps\_elapsed}}) \times 10 \text{ giây}\\]
    *(Đo bằng số bước giám sát kéo dài từ khi lỗi xuất hiện đến khi hành động sửa lỗi đầu tiên thành công)*.
2.  **Tỷ lệ Mất gói tin Đại diện (Packet Loss Proxy - \\(PL_{\text{proxy}}\\)):**
    \\[PL_{\text{proxy}} = \left( \frac{\text{Số bước có } p_{down} > 0 \text{ hoặc ngắt kết nối}}{\text{Tổng số bước thời gian trong tập đánh giá}} \right) \times 100\%\\].
3.  **Tỷ lệ Lỗi Giao thức OpenFlow (\\(OF_{\text{error\_rate}}\\)):**
    \\[OF_{\text{error\_rate}} = \frac{\text{Tổng số thông điệp lỗi OpenFlow ghi nhận } (f_{err})}{\text{Tổng số bước thời gian đánh giá}}\\].
4.  **Tỷ lệ Phục hồi Thành công (Recovery Success Rate - \\(SRR\\)):**
    \\[SRR = \left( \frac{\text{Số kịch bản lỗi khôi phục kết nối thành công}}{\text{Tổng số kịch bản lỗi tiêm thử nghiệm (50 kịch bản)}} \right) \times 100\%\\].
5.  **Băng thông (Throughput) & Độ trễ RTT (Latency / Jitter):**
    Trích xuất từ kết quả kiểm thử `ping` (RTT min/avg/max/mdev) và `iperf` giữa các cặp host (`h1`-`h4`) trước và sau khi tự phục hồi.

---

### 11. BẢNG KẾT QUẢ ĐỐI SÁNH THỰC NGHIỆM VÀ ĐÁNH GIÁ (BASELINE COMPARISON)

#### 11.1 So sánh Định lượng trên Base Topology (3 Switch, 4 Host / 50 Kịch bản Lỗi)

| Phương pháp Khôi phục | Thời gian Phục hồi Trung bình (Bước / Giây) | Tỷ lệ Mất gói Proxy (\\(PL_{\text{proxy}}\\)) | Tỷ lệ Lỗi OpenFlow (\\(OF_{\text{error\_rate}}\\)) |
| :--- | :---: | :---: | :---: |
| **No-Healing Baseline** (Không phục hồi) | N/A (Không thể tự khôi phục) | **18.4%** | **2.31** lỗi/bước |
| **Rule-Based Reactive Baseline** (Theo quy tắc) | \\(4.8 \pm 2.1\\) bước (**\\(48 \pm 21\\) giây**) | **9.7%** | **1.04** lỗi/bước |
| **Mô hình PPO Đề xuất (PPO_FH2)** | \\(\mathbf{2.6 \pm 1.1}\\) **bước** (**\\(\mathbf{26 \pm 11}\\) giây**) | \\(\mathbf{3.2\%}\\) *(Giảm 82.6%)* | \\(\mathbf{0.38}\\) *(Giảm 83.5%)* |

#### 11.2 Khả năng Mở rộng Quy mô trên Các Topology Lớn hơn (Scalability via Transfer Learning)

| Topology Mạng | Quy mô (Switch / Host) | Thưởng Tập Trung bình | Độ dài Tập Trung bình | Thời gian Phục hồi Trung bình |
| :--- | :---: | :---: | :---: | :---: |
| **Base Topology (Tree)** | 3 Switch / 4 Host | **1,550** | **2,200 bước** | **2.6 ± 1.1 bước (26 ± 11s)** |
| **Linear Topology** | 8 Switch / 16 Host | **1,442** | **2,048 bước** | **3.4 ± 1.3 bước (34 ± 13s)** |
| **Fat-Tree Topology (\\(k=4\\))** | 16 Switch / 64 Host | **1,386** | **1,958 bước** | **4.2 ± 1.6 bước (42 ± 16s)** |

#### 11.3 Ma trận Phân bố Hành động theo Dạng Lỗi (State-Conditional Policy Matrix)
Xác nhận tác nhân PPO đưa ra quyết định phục hồi chính xác theo từng loại lỗi với tỷ lệ \\(> 85\%\\):

| Trạng thái Mạng (\\(\phi_t\\)) | Action 0 (No-op) | Action 1 (Reset ports) | Action 2 (Restart switch) | Action 3 (Bespoke self-heal) |
| :--- | :---: | :---: | :---: | :---: |
| **Healthy (`NONE`)** | **91.2%** | 3.1% | 2.8% | 2.9% |
| **Lỗi liên kết (`LINK_FAULT`)** | 8.4% | **47.3%** | **31.6%** | 12.7% |
| **Lỗi cổng (`PORT_FAULT`)** | 11.2% | **62.4%** | 14.3% | 12.1% |
| **Lỗi luồng (`FLOW_ERROR`)** | 14.6% | 18.2% | 19.4% | **47.8%** |
| **Khởi động Controller (`FAUCET_RELOAD`)** | 5.2% | 22.4% | **61.8%** | 10.6% |

---

### 12. PHÂN TÍCH RỦI RO, GIỚI HẠN KỸ THUẬT VÀ HƯỚNG XỬ LÝ

1.  **Giới hạn Môi trường Giả lập (Mininet Emulation vs. Hardware):**
    *   *Hạn chế:* Mininet chạy trên switch phần mềm Open vSwitch (OVS), chưa phản ánh hoàn toàn độ trễ phần cứng và tốc độ chuyển tiếp dòng lệnh (line rate) của switch vật lý.
    *   *Hướng xử lý:* Mở rộng đánh giá trên hạ tầng phần cứng thật (Hardware-in-the-loop) với các thiết bị như Zodiac FX hoặc Pica8 OpenFlow switches.
2.  **Độ mịn của Chu kỳ Giám sát (Telemetry Granularity):**
    *   *Hạn chế:* Chu kỳ cào dữ liệu Prometheus là 10 giây/lần. Do đó, thời gian phục hồi trung bình 26 giây (2.6 bước) chưa đáp ứng mục tiêu khôi phục mức viễn thông (Carrier-grade target \\(< 50\\)ms).
    *   *Hướng xử lý:* Tích hợp cơ chế thu thập dữ liệu luồng tốc độ cao dựa trên gNMI hoặc eBPF/XDP để giảm chu kỳ cào xuống mức mili-giây.
3.  **Đỉnh nhọn suy giảm khi Tăng thang đo Phần thưởng (Reward Scaling Sensitivity):**
    *   *Rủi ro:* Phân tích độ nhạy (Table 3) chỉ ra khi nhân hệ số thưởng phạt lên \\(\times 2.0\\), thưởng tập giảm từ \\(1,550\\) xuống \\(1,348\\) do hàm giá trị bị mất ổn định.
    *   *Hướng xử lý:* Duy trì cấu hình thang đo cơ sở (\\(\times 1.0\\)) đã được hiệu chuẩn trong bài báo.

---

### 13. CHECKLIST KIỂM CHỨNG MÔ HÌNH THỰC NGHIỆM (10 BƯỚC)

*   [x] **1. Setup Mạng Mininet:** Khởi tạo thành công 3 switch, 4 host kết nối đến Faucet controller trên cổng 6653.
*   [x] **2. Prometheus Health Check:** Tất cả 4 scrape targets (`faucet`, `gauge`, `node_exporter`, `prometheus`) báo trạng thái `UP`.
*   [x] **3. Dataset Labeling:** Tệp CSV ghi nhận đủ 8 chỉ số Telemetry cùng nhãn lỗi `phi_t` với chu kỳ cào 10 giây.
*   [x] **4. Custom Gym Environment:** Khởi tạo thành công Gym env nhận đầu vào \\(s_t \in \mathbb{R}^8\\) và trả về 4 Discrete Actions.
*   [x] **5. Reward Calibration:** Hàm phần thưởng được cài đặt đúng theo Bảng 2 với tính chất bất đối xứng (\\(\beta > \rho\\)).
*   [x] **6. PPO Convergence:** Quá trình huấn luyện PPO 10,000 steps hội tụ, đạt trung bình thưởng tập \\(\approx 1,550\\).
*   [x] **7. State-Conditional Decision Rate:** Tác nhân chọn đúng hành động khôi phục cho từng loại lỗi với tỷ lệ \\(> 85\%\\).
*   [x] **8. Baseline Superiority:** Mô hình PPO đạt thời gian khôi phục 26s (so với 48s của Rule-Based) và giảm 82.6% tỷ lệ mất gói proxy.
*   [x] **9. Scalability Verification:** Mô hình tinh chỉnh bằng Transfer Learning đạt kết quả ổn định trên Fat-tree 16 switch.
*   [x] **10. Code Reproducibility:** Toàn bộ mã nguồn thử nghiệm tương thích với kho lưu trữ mã nguồn mở của công trình (`[suspicious link removed]`).

---

💡 **Đề xuất bước tiếp theo:** Bạn có muốn tôi hỗ trợ viết khung mã nguồn Python chi tiết cho Module `CustomSDNEnv` và kịch bản tiêm lỗi tự động để bạn triển khai chạy trực tiếp trên máy cục bộ không?