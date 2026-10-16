# MẠNG DOANH NGHIỆP TỰ PHỤC HỒI SỬ DỤNG SD-WAN VÀ CƠ CHẾ KHÔI PHỤC SỰ CỐ THÔNG MINH

## Tài liệu tổng hợp đề xuất luận văn

---
## 1. Phân tích thực trạng

### 1.1. Hạn chế của mạng WAN doanh nghiệp truyền thống

Hầu hết các doanh nghiệp hiện nay vận hành trên nền tảng **WAN truyền thống** với kiến trúc Hub-and-Spoke, trong đó mọi lưu lượng từ chi nhánh đều phải định tuyến về Trung tâm Dữ liệu (Data Center) trung tâm trước khi đi ra ngoài. Kiến trúc này được xây dựng trong bối cảnh tài nguyên tập trung và ứng dụng nội bộ là chủ đạo — song đã bộc lộ nhiều bất cập trong kỷ nguyên Cloud.

Các điểm yếu cốt lõi bao gồm:

- **Backhauling (Trombone Effect):** Nhân viên chi nhánh truy cập dịch vụ Cloud (Microsoft 365, Zoom, AWS) nhưng luồng dữ liệu phải đi vòng qua DC trung tâm rồi mới ra Internet — tăng độ trễ đáng kể và lãng phí băng thông MPLS đắt tiền.
- **Quản lý phân tán, thủ công:** Mỗi thiết bị (Router, Switch) cần cấu hình độc lập qua CLI. Với hàng chục đến hàng trăm chi nhánh, chi phí vận hành leo thang và xác suất lỗi do con người tăng cao.
- **Khôi phục sự cố thụ động:** Các giao thức định tuyến truyền thống (OSPF, BGP) chỉ phản ứng khi đường truyền hoàn toàn đứt (*link down*), không phát hiện được các vấn đề chất lượng ngầm như tăng độ trễ, mất gói, hay jitter — dẫn đến trải nghiệm người dùng xấu đi mà hệ thống không hay biết.
- **Chi phí MPLS cao, triển khai chậm:** Băng thông MPLS đắt gấp 10–50 lần Internet thông thường, và việc mở một chi nhánh mới có thể mất 1–3 tháng chờ nhà mạng.

**Hybrid WAN** ra đời như một giải pháp tình thế — kết hợp MPLS cho lưu lượng nhạy cảm và đường Internet giá rẻ cho các dịch vụ thông thường. Tuy nhiên, mô hình này chỉ giải quyết một phần vấn đề chi phí, trong khi bài toán quản lý chính sách phân chia lưu lượng (Policy-Based Routing) lại trở nên phức tạp hơn và vẫn phụ thuộc hoàn toàn vào can thiệp thủ công của kỹ sư.

---

### 1.2. Sự trỗi dậy của SD-WAN và bài toán tự phục hồi

**SD-WAN (Software-Defined Wide Area Network)** ra đời để giải quyết căn bản các hạn chế trên bằng cách tách biệt *Control Plane* (điều khiển) khỏi *Data Plane* (chuyển tiếp dữ liệu), đưa toàn bộ logic điều khiển lên một bộ điều phối tập trung (Orchestrator/Controller). Nhờ đó:

- **Quản lý tập trung:** Chính sách định tuyến được cấu hình một lần, tự động phân phối xuống mọi Edge Router tại chi nhánh.
- **Khai thác đa đường truyền (Active-Active):** SD-WAN sử dụng đồng thời MPLS, Internet, LTE/5G và phân phối lưu lượng theo chất lượng thực tế từng đường, không chỉ chuyển đổi đơn giản khi đứt link.
- **Application-Aware Routing:** Nhận diện ứng dụng đến tầng 7 (Layer 7), ưu tiên lưu lượng thời gian thực (VoIP, Video Conference) trên đường tốt nhất.
- **Zero Touch Provisioning (ZTP):** Chi nhánh mới chỉ cần cắm điện và kết nối Internet — thiết bị tự tải cấu hình từ Cloud về, rút ngắn thời gian triển khai từ hàng tuần xuống còn vài giờ.

| Tiêu chí | WAN truyền thống | SD-WAN |
|---|---|---|
| Quản lý | Thủ công, từng thiết bị | Tập trung, tự động |
| Phụ thuộc MPLS | Bắt buộc | Không bắt buộc |
| Tối ưu Cloud | Kém (Backhauling) | Trực tiếp ra Internet |
| Khôi phục sự cố | Thụ động (link down) | Chủ động (quality-aware) |
| Triển khai chi nhánh | 1–3 tháng | Vài giờ (ZTP) |
| Khả năng mở rộng | Khó | Linh hoạt |

Tuy nhiên, ngay cả SD-WAN thế hệ đầu vẫn tồn tại khoảng trống quan trọng: **cơ chế phát hiện và khôi phục sự cố phần lớn vẫn dựa trên ngưỡng cố định (static threshold) và luật tay (rule-based)**. Hệ thống không tự suy luận được *nguyên nhân gốc rễ* của sự cố — phân biệt lỗi Switch LAN, lỗi đường truyền WAN, hay suy giảm chất lượng dịch vụ ISP — dẫn đến quyết định khắc phục đôi khi không đúng đích, kéo dài thời gian gián đoạn dịch vụ.

---

### 1.3. Động lực nghiên cứu

Khoảng trống nêu trên đặt ra yêu cầu xây dựng một **cơ chế tự phục hồi thông minh** (Intelligent Self-Healing) tích hợp vào nền tảng SD-WAN, trong đó:

1. **Giám sát liên tục** telemetry từ cả lớp LAN (SDN) và WAN (SD-WAN).
2. **Phát hiện bất thường** bằng mô hình học máy (thay vì ngưỡng tĩnh) để phát hiện sớm sự cố ngầm.
3. **Phân loại nguyên nhân gốc rễ (RCA)** tự động để định hướng hành động khắc phục đúng đích.
4. **Thực thi khắc phục** qua API điều khiển SDN/SD-WAN mà không cần can thiệp thủ công.

Luận văn này hướng đến thiết kế, triển khai và đánh giá một hệ thống như vậy — đặt trọng tâm vào **AI Fault-Recovery Engine** hoạt động xuyên suốt hai lớp SDN (LAN) và SD-WAN (WAN), góp phần giảm MTTR (*Mean Time to Repair*), tăng độ chính xác RCA và giảm thiểu thời gian gián đoạn dịch vụ so với phương pháp truyền thống.

---

## 2. Kiến trúc tổng thể

```
                NOC DASHBOARD  (http://localhost:5050)
                ┌──────────────────────────────────────┐
                │  Topology Map  │  Metrics Charts      │
                │  Alert Panel   │  AI Decision Log     │
                │  WAN Path Status│  Recovery History   │
                └──────────────────────┬───────────────┘
                       WebSocket / REST API (Flask-SocketIO)
                                       │
                    AI FAULT-RECOVERY ENGINE  (trọng tâm luận văn)
                    ┌─────────────────────────────┐
                    │  Telemetry Collector         │
                    │  Anomaly Detection            │
                    │  Root Cause Analysis (RCA)    │
                    │  Self-Healing Decision Engine │
                    └───────────────┬───────────────┘
                                    │
            ┌───────────────────────┴────────────────────────┐
      SDN Controller (LAN)                          SD-WAN Controller (WAN)
            │                                                 │
      ──────────────────────────────────────────────────────────────────
            |                    |                    |                 |
      Bảo Lộc (Flat)      Nha Trang (3-Tier)   HCM (3-Tier)     Data Center
            |                    |                    |           (Spine-Leaf)
      ──────────────────────────────────────────────────────────────────
                                 │
                           WAN Transport (tc netem)
                   MPLS | Internet | LTE | 5G | VPN
```

### 2.1. SDN Controller — Lớp điều khiển mạng LAN

**SDN Controller** (triển khai bằng Ryu hoặc ONOS) đóng vai trò điều khiển tập trung toàn bộ hạ tầng mạng nội bộ (LAN) của các chi nhánh. Thay vì mỗi Switch tự đưa ra quyết định định tuyến độc lập, toàn bộ logic điều khiển được tách ra khỏi thiết bị và đưa về Controller.

**Chức năng chính:**

| Chức năng | Mô tả |
|---|---|
| Quản lý Flow Table | Cài đặt, cập nhật, xóa luồng (flow entries) trên các SDN Switch qua giao thức OpenFlow |
| Quản lý VLAN & ACL | Phân đoạn mạng theo phòng ban, áp dụng chính sách kiểm soát truy cập tập trung |
| Phân phối QoS | Ưu tiên lưu lượng quan trọng (VoIP, ERP) ngay tại lớp LAN trước khi ra WAN |
| Cung cấp Telemetry | Xuất dữ liệu trạng thái port, số flow entries, packet drop qua REST API cho AI Engine |
| Thực thi Self-Healing | Nhận lệnh từ AI Engine để reroute flow khi Switch/port gặp sự cố |

> **Lưu ý thiết kế:** Chỉ triển khai **một SDN Controller duy nhất (hoặc cụm HA)** quản lý tất cả chi nhánh, thay vì mỗi chi nhánh một Controller riêng — giảm chi phí vận hành và đơn giản hóa quản lý.

---

### 2.2. SD-WAN Controller — Lớp điều khiển kết nối WAN

**SD-WAN Controller** (tự triển khai bằng Python module trong môi trường Mininet thuần) quản lý toàn bộ các đường kết nối WAN giữa các chi nhánh, Data Center và dịch vụ Cloud. Mỗi transport WAN được mô phỏng bằng một đường riêng trên OvS với đặc tính mạng khác nhau (băng thông, độ trễ, tỷ lệ mất gói) được cấu hình qua `tc netem`.

**Chức năng chính:**

| Chức năng | Mô tả |
|---|---|
| Dynamic Path Selection | Liên tục đo lường chất lượng từng đường (latency, jitter, packet loss) và chọn đường tốt nhất theo thời gian thực |
| Traffic Steering | Điều hướng lưu lượng theo loại ứng dụng: lưu lượng ERP/VoIP ưu tiên MPLS, lưu lượng web/cloud đi Internet |
| Overlay Tunnel Management | Duy trì các đường hầm IPsec/VPN giữa các điểm mạng, tự động tái thiết lập khi tunnel đứt |
| Quản lý Policy | Áp dụng chính sách định tuyến (Policy-Based Routing) từ Controller xuống toàn bộ Edge Router |
| Cung cấp Telemetry | Xuất dữ liệu chất lượng đường truyền (latency, loss, throughput, tunnel status) cho AI Engine |

---

### 2.3. AI Fault-Recovery Engine — Lớp trí tuệ tự phục hồi

Đây là thành phần **trọng tâm của luận văn**, hoạt động như một lớp điều phối thông minh phía trên hai Controller. Engine thu thập dữ liệu từ cả hai lớp, phân tích và ra quyết định khắc phục — tất cả đều tự động, không cần can thiệp thủ công.

Kiến trúc bên trong Engine được trình bày chi tiết tại **Mục 3**.

---

## 3. Chi tiết AI Fault-Recovery Engine

### 3.1. Kiến trúc pipeline xử lý

Engine hoạt động theo pipeline tuyến tính gồm 5 khối, trong đó 2 khối sử dụng mô hình học máy có huấn luyện rõ ràng:

```
Telemetry Collector
        │  (dữ liệu time-series mỗi 1–5 giây)
        ▼
Anomaly Detection  ──► Isolation Forest / One-Class SVM   [ML #1]
        │  (phát hiện điểm bất thường, gắn cờ sự kiện)
        ▼
Feature Extraction
        │  (vector đặc trưng: vị trí lỗi, loại metric, phạm vi ảnh hưởng...)
        ▼
Root Cause Classification ──► Random Forest / Decision Tree   [ML #2]
        │  (nhãn: Switch fault | Link fault | ISP fault | Cloud fault + confidence)
        ▼
Self-Healing Decision Engine
        │  (ánh xạ root cause → hành động, rule-based có chủ đích)
        ▼
Action Executor
        │  (gọi API SDN Controller hoặc SD-WAN Controller)
        ▼
   [Mạng tự phục hồi]
```

---

### 3.2. Khối 1 — Telemetry Collector

**Vai trò:** Cửa ngõ dữ liệu đầu vào. Thu thập và chuẩn hóa toàn bộ số liệu đo lường từ hai lớp mạng thành chuỗi thời gian liên tục.

**Nguồn dữ liệu:**

| Lớp | Giao thức/Công cụ | Chỉ số thu thập |
|---|---|---|
| SDN (LAN) | Ryu REST API / OVS-OFCTL | Trạng thái port, số flow entries, packet drop, CPU/queue của Switch |
| SD-WAN (WAN) | ping, iperf3, script Python | Latency, jitter, packet loss, throughput, trạng thái tunnel IPsec |

**Lưu trữ:** Time-series dạng CSV/SQLite/InfluxDB, mỗi bản ghi gắn `timestamp` + `node_id` + `link_id` để phục vụ truy vấn và huấn luyện ML.

**Tần suất:** 1–5 giây/lần — đủ nhanh để phát hiện sự cố ngầm (latency tăng dần) trước khi link hoàn toàn đứt.

---

### 3.3. Khối 2 — Anomaly Detection *(ML #1)*

**Vai trò:** Phát hiện các điểm bất thường trong chuỗi dữ liệu telemetry — bao gồm cả sự cố rõ ràng (link down) lẫn sự cố ngầm (latency tăng bất thường, packet loss leo thang dần).

**Mô hình:** **Isolation Forest** (ưu tiên) hoặc **One-Class SVM** (scikit-learn).

- *Isolation Forest* hoạt động bằng cách phân vùng ngẫu nhiên không gian đặc trưng — điểm dữ liệu nào bị cô lập nhanh hơn (cần ít bước phân vùng hơn) thì được coi là bất thường.
- Huấn luyện **unsupervised** trên dữ liệu telemetry lúc mạng hoạt động bình thường — không cần nhãn, phù hợp với môi trường thực tế khó thu thập dữ liệu lỗi có sẵn.

**Đầu ra:** Cờ nhị phân `{normal, anomaly}` + anomaly score, kèm danh sách metric vi phạm.

**Điểm mạnh so với threshold tĩnh:** Phát hiện được sự cố ngầm dạng "tổ hợp nhiều metric cùng lệch nhẹ" — điều mà ngưỡng cố định trên từng metric riêng lẻ sẽ bỏ sót.

---

### 3.4. Khối 3 — Root Cause Analysis / Classification *(ML #2)*

**Vai trò:** Xác định *tại sao* có sự cố — phân loại nguyên nhân gốc rễ để hành động khắc phục đúng đích, tránh lãng phí tài nguyên hoặc gây tác động lan rộng.

**Mô hình:** **Random Forest** (ưu tiên) hoặc Decision Tree.
- Chọn Random Forest vì khả năng chống overfitting tốt và hỗ trợ xuất `feature_importance` — giải thích được đặc trưng nào quan trọng nhất (hướng Explainable AI).

**Đầu vào (feature vector):**

| Đặc trưng | Ý nghĩa |
|---|---|
| Số branch bị ảnh hưởng | Phân biệt lỗi cục bộ (1 branch) vs lỗi hạ tầng chung (nhiều branch) |
| Loại metric bất thường | Switch metric hay WAN metric → khoanh vùng lớp lỗi |
| Vị trí trong topology | Lỗi tại edge, core, hay uplink? |
| Thời gian kéo dài | Lỗi thoáng qua hay lỗi dai dẳng |
| Tốc độ leo thang | Đột ngột (link down) hay tăng dần (ISP degrade) |

**Đầu ra:** Nhãn phân loại + confidence score:
- `Switch fault` — lỗi thiết bị hoặc port tại LAN
- `Link fault` — đứt đường truyền WAN
- `ISP fault` — suy giảm chất lượng từ nhà mạng (loss/latency cao kéo dài)
- `Cloud/SaaS fault` — endpoint đích không phản hồi

**Tạo dữ liệu huấn luyện:** Chủ động gây lỗi có kiểm soát trong testbed (switch down, `tc netem` tăng loss dần, ifdown tunnel, tắt cloud endpoint giả lập), mỗi lần gây lỗi tự gán nhãn tương ứng — tạo tập labeled dataset có thể tái tạo.

---

### 3.5. Khối 4 — Self-Healing Decision Engine

**Vai trò:** Ánh xạ root cause đã xác định sang hành động khắc phục cụ thể và thực thi qua API của Controller tương ứng.

**Thiết kế rule-based có chủ đích:** Bước này giữ logic rõ ràng, có thể kiểm tra và giải thích — tránh để mô hình ML tự quyết định hành động tác động trực tiếp vào hạ tầng mạng (có thể gây downtime lớn hơn nếu sai).

| Root Cause | Hành động khắc phục | Thực thi qua |
|---|---|---|
| Switch/port lỗi | Reroute flow sang switch/port dự phòng | SDN Controller (Ryu REST API) |
| Link/Tunnel WAN down | Tái thiết lập tunnel / chuyển sang backup link | SD-WAN Controller script |
| ISP degrade (loss/latency cao) | Traffic steering toàn bộ lưu lượng sang link khác | SD-WAN Controller (policy route) |
| Cloud/SaaS fault | Ghi log + cảnh báo, không tự can thiệp | Log + Notify (ngoài phạm vi kiểm soát) |

**Thời gian phản ứng mục tiêu:** < 10 giây từ lúc phát hiện bất thường đến khi thực thi hành động — so sánh với MTTR của phương pháp thủ công thường từ vài phút đến vài chục phút.

---


---

## 4. Testbed thực nghiệm

**Toàn bộ hệ thống triển khai 100% trên Mininet** — không phụ thuộc GNS3/EVE-NG, đảm bảo reproducibility hoàn toàn.

| Thành phần | Công cụ |
|---|---|
| Nền tảng mô phỏng | **Mininet 2.3+ + Open vSwitch** (Ubuntu 20.04/22.04) |
| SDN LAN | **Ryu SDN Framework** — điều khiển OvS qua OpenFlow 1.3 |
| SD-WAN WAN | **Python SD-WAN Controller tự viết** — 5 transport path (MPLS/Internet/LTE/5G/VPN) mô phỏng bằng `tc netem` + OvS flow rules |
| Sinh lỗi | `tc netem` (tăng delay/loss/jitter), `link.intf.ifconfig down`, `net.configLinkStatus()` |
| Sinh traffic | `iperf3`, `ping`, Mininet host CLI |
| AI engine | Python + scikit-learn (Isolation Forest, Random Forest) |
| Lưu trữ telemetry | CSV / SQLite / InfluxDB |
| Tổ chức mã nguồn | `src/` — xem cây thư mục chi tiết |

### Đặc tính mô phỏng 5 WAN transport

| Transport | Bandwidth | Delay | Loss | Ghi chú |
|---|---|---|---|---|
| MPLS | 100 Mbps | 20 ms | 0.1% | Đường ưu tiên VoIP/ERP |
| Internet | 100 Mbps | 40 ms | 0.5% | Đường Web/Cloud |
| LTE | 30 Mbps | 60 ms | 1.0% | Backup di động |
| 5G | 200 Mbps | 15 ms | 0.3% | Đường tốc độ cao |
| VPN | 50 Mbps | 50 ms | 0.8% | Backup mã hóa |

> **Lưu ý:** Các giá trị trên là baseline ban đầu. Trong quá trình thực nghiệm, các thông số sẽ được điều chỉnh để tạo ra các kịch bản suy giảm/congestion khác nhau cho AI học và kiểm thử.

---

## 5. Kịch bản đánh giá (metrics)

So sánh **mạng rule-based tĩnh (baseline)** vs **mạng có AI Fault-Recovery Engine**:

1. **MTTR** (Mean Time to Repair) — thời gian từ lúc lỗi xảy ra đến lúc traffic được khôi phục
2. **Độ chính xác RCA** — accuracy/precision/recall/F1 của mô hình phân loại nguyên nhân
3. **Tỷ lệ vi phạm SLA** trong lúc lỗi
4. **Traffic loss/downtime** trong quá trình failover

**Kịch bản lỗi cần test:**
- Switch LAN lỗi
- Tunnel WAN down
- ISP degrade dần (packet loss tăng từ từ)
- Lỗi đồng thời nhiều branch (kiểm tra khả năng RCA phân biệt lỗi cục bộ vs lỗi hạ tầng chung)

---

