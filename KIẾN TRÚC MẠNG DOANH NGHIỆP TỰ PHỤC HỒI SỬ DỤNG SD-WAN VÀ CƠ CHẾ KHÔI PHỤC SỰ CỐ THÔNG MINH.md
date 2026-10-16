# KIẾN TRÚC MẠNG DOANH NGHIỆP TỰ PHỤC HỒI SỬ DỤNG SD-WAN VÀ CƠ CHẾ KHÔI PHỤC SỰ CỐ THÔNG MINH

## 1. Kiến trúc tổng thể đề xuất

Hệ thống được xây dựng theo mô hình **Closed-loop Intelligent Self-Healing Network**, trong đó khối AI đóng vai trò là bộ não trung tâm thực hiện thu thập dữ liệu, phát hiện bất thường, phân tích nguyên nhân và đưa ra quyết định khôi phục. Các quyết định khôi phục không được thực thi trực tiếp trên thiết bị mạng mà được chuyển đến các Controller tương ứng.

- **SDN Controller** chịu trách nhiệm điều khiển và khôi phục các thành phần thuộc miền **LAN**.
- **SD-WAN Controller** chịu trách nhiệm điều khiển và khôi phục các thành phần thuộc miền **WAN**.
- Sau khi Controller thực thi hành động khôi phục, trạng thái mới của mạng tiếp tục được thu thập và gửi về AI để xác minh kết quả.

Kiến trúc tổng thể được đề xuất như sau:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                    AI SELF-HEALING ENGINE                                   │
│                                                                              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────────────┐  │
│  │    Telemetry    │ →  │    Anomaly       │ →  │   Root Cause Analysis  │  │
│  │    Collector    │    │    Detection     │    │         (RCA)           │  │
│  └─────────────────┘    └──────────────────┘    └────────────┬───────────┘  │
│                                                              │              │
│                                                              ▼              │
│                                                   ┌──────────────────────┐   │
│                                                   │ Recovery Decision    │   │
│                                                   │ Engine                │   │
│                                                   └──────────┬───────────┘   │
└────────────────────────────────────────────────────────────┼────────────────┘
                                                             │
                                                      Recovery Intent
                                                             │
                                                             ▼
                                              ┌─────────────────────────┐
                                              │ Policy / Safety Layer   │
                                              │                         │
                                              │ - Policy Validation     │
                                              │ - Risk Assessment       │
                                              │ - Confidence Check       │
                                              │ - Rollback Policy       │
                                              └────────────┬────────────┘
                                                           │
                                                           ▼
                                              ┌─────────────────────────┐
                                              │ Global Network           │
                                              │ Orchestrator             │
                                              └────────────┬────────────┘
                                                           │
                                         ┌─────────────────┴─────────────────┐
                                         │                                   │
                                         ▼                                   ▼
                              ┌─────────────────────┐            ┌─────────────────────┐
                              │   SDN CONTROLLER    │            │  SD-WAN CONTROLLER  │
                              │       (LAN)         │            │        (WAN)        │
                              └──────────┬──────────┘            └──────────┬──────────┘
                                         │                                  │
                                  Control Actions                     Control Actions
                                         │                                  │
                                         ▼                                  ▼
                              ┌─────────────────────┐            ┌─────────────────────┐
                              │    LAN NETWORK      │            │     WAN NETWORK     │
                              │                     │            │                     │
                              │ SDN Switch          │            │ SD-WAN Edge        │
                              │ Core / Access       │            │ MPLS                │
                              │ AP / VLAN / Flow    │            │ Internet            │
                              │ End Users           │            │ LTE / 5G            │
                              └──────────┬──────────┘            └──────────┬──────────┘
                                         │                                  │
                                         └────────────────┬─────────────────┘
                                                          │
                                                    Network State
                                                          │
                                                          ▼
                                              ┌─────────────────────┐
                                              │ Verification &      │
                                              │ Feedback            │
                                              └──────────┬──────────┘
                                                         │
                                                         │ New Telemetry
                                                         └───────────────→ AI
```

---

# 2. Tư tưởng thiết kế cốt lõi

Kiến trúc trên dựa trên nguyên tắc:

> **AI không trực tiếp cấu hình thiết bị mạng. AI đưa ra quyết định khôi phục và yêu cầu Controller thực thi quyết định đó.**

Điều này tạo ra sự phân tách rõ ràng giữa **Intelligence Layer** và **Control Layer**.

Có thể mô hình hóa:

```text
AI
│
│ "Cần làm gì?"
│
▼
Recovery Intent
│
▼
Controller
│
│ "Thực hiện như thế nào?"
│
▼
Network Devices
```

Ví dụ:

AI xác định:

```text
MPLS link tại Branch A bị suy giảm nghiêm trọng.
→ Chuyển traffic sang Internet.
```

AI không cần trực tiếp biết từng câu lệnh cấu hình của thiết bị.

Thay vào đó:

```text
AI
 ↓
Recovery Intent:
"Steer critical traffic to Internet"
 ↓
SD-WAN Controller
 ↓
Tính toán / áp dụng policy
 ↓
SD-WAN Edge
```

Cách tiếp cận này giúp hệ thống dễ mở rộng và giảm sự phụ thuộc của AI vào từng loại thiết bị mạng.

---

# 3. Các thành phần chính của hệ thống

## 3.1. Telemetry Collector

Telemetry Collector chịu trách nhiệm thu thập trạng thái hoạt động của toàn bộ hệ thống mạng.

Các dữ liệu có thể bao gồm:

```text
Network Telemetry
├── CPU Utilization
├── Memory Utilization
├── Interface Utilization
├── Packet Loss
├── Latency
├── Jitter
├── Throughput
├── Interface Errors
├── CRC Errors
├── Link Status
├── Routing State
├── Tunnel State
├── Flow Statistics
└── Network Logs
```

Các nguồn dữ liệu có thể được sử dụng:

```text
SNMP
Syslog
NetFlow / IPFIX
Streaming Telemetry
REST API
Controller API
```

Telemetry Collector đóng vai trò là **cửa ngõ dữ liệu** cho AI.

---

# 4. Anomaly Detection

Sau khi dữ liệu được thu thập, hệ thống AI tiến hành phát hiện các trạng thái bất thường.

Ví dụ trạng thái bình thường:

```text
Latency       = 15 ms
Packet Loss   = 0.1 %
CPU           = 40 %
Utilization   = 45 %
```

Khi xảy ra sự cố:

```text
Latency       = 250 ms
Packet Loss   = 35 %
CPU           = 92 %
Utilization   = 98 %
```

AI xác định:

```text
Normal
   ↓
Anomaly Detected
```

Tuy nhiên, **phát hiện bất thường chưa đồng nghĩa với xác định được nguyên nhân**.

Đây là lý do hệ thống cần thêm tầng Root Cause Analysis.

---

# 5. Root Cause Analysis

Root Cause Analysis (RCA) có nhiệm vụ xác định nguyên nhân thực sự của sự cố thay vì chỉ nhận diện các triệu chứng.

Ví dụ:

```text
Observed Symptoms:

Packet Loss ↑
Latency ↑
CPU ↑
Users complain
```

Không nên kết luận ngay:

```text
CPU cao = Root Cause
```

Có thể chuỗi nguyên nhân thực tế là:

```text
WAN Link Failure
       ↓
Traffic Rerouting
       ↓
Traffic Concentration
       ↓
Core Link Congestion
       ↓
CPU Increase
       ↓
Packet Loss
       ↓
User Impact
```

Do đó hệ thống cần phân biệt:

```text
Symptom
   ↓
Anomaly
   ↓
Correlation
   ↓
Dependency Analysis
   ↓
Root Cause
```

RCA là thành phần quan trọng giúp AI đưa ra quyết định khôi phục chính xác hơn.

---

# 6. Recovery Decision Engine

Sau khi xác định được Root Cause, AI lựa chọn phương án khôi phục phù hợp.

Ví dụ:

```text
Root Cause:
MPLS Link Failure

Candidate Recovery Actions:

1. Switch traffic → Internet
2. Switch traffic → LTE/5G
3. Rebuild tunnel
4. Keep current path
```

AI đánh giá các phương án dựa trên:

```text
Network State
Fault Severity
Application Priority
Available Bandwidth
Latency
Packet Loss
Recovery Cost
Risk
AI Confidence
```

Sau đó tạo ra:

```text
Recovery Intent
```

Ví dụ:

```text
Target:
Branch A

Fault:
MPLS Failure

Action:
Traffic Steering

Preferred Path:
Internet

Traffic:
Critical Applications

Priority:
High
```

---

# 7. Policy / Safety Layer

Đây là lớp bảo vệ nằm giữa AI và Controller.

Mục đích là ngăn AI thực hiện những hành động không an toàn.

```text
                 AI Decision
                      │
                      ▼
             ┌───────────────────┐
             │ Policy / Safety   │
             │      Layer        │
             ├───────────────────┤
             │ Policy Check      │
             │ Risk Assessment   │
             │ Confidence Check  │
             │ Blast Radius      │
             │ Rollback Policy   │
             └─────────┬─────────┘
                       │
                 Approved?
                 /       \
               YES       NO
                │         │
                ▼         ▼
           Controller    Reject
```

Ví dụ:

```text
AI Confidence = 97%
Risk = Low
Action = Switch WAN Path
→ Automatically Execute
```

Trong khi:

```text
AI Confidence = 58%
Risk = High
Action = Modify Core Routing
→ Require Human Approval
```

Điều này giúp xây dựng mô hình **controlled self-healing** thay vì để AI toàn quyền thay đổi hệ thống.

---

# 8. Global Network Orchestrator

Global Network Orchestrator là thành phần trung gian điều phối các Controller.

Nó không trực tiếp thay thế SDN Controller hoặc SD-WAN Controller.

Vai trò:

```text
AI
 ↓
Recovery Intent
 ↓
Global Orchestrator
 ├── LAN Recovery → SDN Controller
 └── WAN Recovery → SD-WAN Controller
```

Nhờ đó hệ thống có thể quản lý đồng thời:

```text
LAN Domain
+
WAN Domain
```

và tạo ra một góc nhìn thống nhất về toàn bộ mạng doanh nghiệp.

---

# 9. SDN Controller – Điều khiển miền LAN

SDN Controller chịu trách nhiệm thực hiện các hành động khôi phục thuộc LAN.

Các đối tượng có thể điều khiển:

```text
SDN Switch
Core Switch
Access Switch
VLAN
Flow
Routing
ACL
Access Policy
```

Ví dụ sự cố:

```text
Access Link Failure
        ↓
AI Detection
        ↓
RCA
        ↓
Recovery Decision
        ↓
SDN Controller
        ↓
Reroute / Flow Adjustment
        ↓
LAN Recovery
```

---

# 10. SD-WAN Controller – Điều khiển miền WAN

SD-WAN Controller chịu trách nhiệm xử lý các sự cố thuộc WAN.

Các thành phần:

```text
MPLS
Internet
LTE / 5G
IPSec Tunnel
SD-WAN Edge
WAN Path
Application Traffic
```

Ví dụ:

```text
MPLS Packet Loss = 80%
        ↓
AI Detection
        ↓
RCA
        ↓
MPLS Degradation
        ↓
Recovery Decision
        ↓
SD-WAN Controller
        ↓
Traffic Steering
        ↓
Internet
        ↓
Service Restored
```

---

# 11. Khả năng phối hợp LAN và WAN

Đây là một trong những điểm quan trọng nhất của kiến trúc.

AI có khả năng nhìn thấy trạng thái của cả:

```text
LAN
│
├── Core
├── Access
├── VLAN
└── Users

WAN
│
├── MPLS
├── Internet
├── LTE / 5G
└── SD-WAN Tunnel
```

Do đó AI có thể xác định Fault Domain.

Ví dụ:

```text
Branch A unreachable
        │
        ├── LAN healthy
        └── WAN degraded
                 ↓
          SD-WAN Recovery
```

Trong trường hợp khác:

```text
Branch A unreachable
        │
        ├── WAN healthy
        └── Access Switch DOWN
                 ↓
            SDN Recovery
```

Như vậy AI không chỉ phát hiện lỗi mà còn xác định **miền cần khôi phục**.

---

# 12. Trường hợp khôi phục phối hợp LAN + WAN

Kiến trúc cũng cho phép xử lý những sự cố có ảnh hưởng đồng thời đến LAN và WAN.

Ví dụ:

```text
MPLS Failure
      ↓
SD-WAN chuyển traffic sang Internet
      ↓
Traffic tăng mạnh
      ↓
WAN Uplink Congestion
      ↓
LAN Core Congestion
      ↓
User Performance Degradation
```

AI có Global Network State có thể nhìn thấy toàn bộ chuỗi sự kiện:

```text
MPLS Failure
      ↓
WAN Path Change
      ↓
Traffic Increase
      ↓
LAN Congestion
```

Từ đó đưa ra chiến lược khôi phục phối hợp:

```text
SD-WAN Controller
        ↓
Traffic Steering

+

SDN Controller
        ↓
LAN Flow Optimization
```

Đây là một điểm có thể tạo ra giá trị nghiên cứu đáng kể cho hệ thống.

---

# 13. Verification & Feedback

Sau khi Controller thực hiện hành động, hệ thống không được mặc định rằng sự cố đã được xử lý.

AI phải kiểm tra lại trạng thái mạng.

```text
Recovery Action
      ↓
Network State Changed
      ↓
Telemetry
      ↓
Verification
      ↓
 ┌───────────────┐
 │ Recovery OK?  │
 └───────┬───────┘
         │
      ┌──┴──┐
     YES    NO
      │      │
      ▼      ▼
  Complete  Re-analyze
             │
             ▼
       New Recovery Plan
```

Đây chính là thành phần tạo ra **Closed-loop Self-Healing**.

---

# 14. Chu trình Closed-loop Self-Healing

Toàn bộ hệ thống có thể được biểu diễn bằng chu trình:

```text
        ┌──────────────────────┐
        │       OBSERVE        │
        │      Telemetry       │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │       DETECT         │
        │ Anomaly Detection    │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │       ANALYZE        │
        │        RCA           │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │        DECIDE        │
        │ Recovery Decision    │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │         ACT          │
        │ SDN / SD-WAN         │
        │ Controller           │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │       VERIFY         │
        │ Recovery Validation  │
        └──────────┬───────────┘
                   │
                   └──────────────→ OBSERVE
```

Có thể gọi chu trình này:

> **Observe → Detect → Analyze → Decide → Act → Verify**

---

# 15. Luồng xử lý sự cố hoàn chỉnh

Một sự cố đi qua hệ thống theo trình tự:

```text
Network Fault
     ↓
Telemetry Collector
     ↓
Data Processing
     ↓
Anomaly Detection
     ↓
Root Cause Analysis
     ↓
Recovery Decision
     ↓
Policy / Safety Validation
     ↓
Global Network Orchestrator
     ↓
 ┌───────────────┬────────────────┐
 │               │                │
 ▼               ▼                │
SDN Controller  SD-WAN Controller  │
 │               │                │
 ▼               ▼                │
LAN Recovery    WAN Recovery       │
 │               │                │
 └───────────────┴────────────────┘
                 ↓
          Network Verification
                 ↓
           Recovery Success?
            /           \
          YES            NO
           │              │
           ▼              ▼
        Complete      Re-analysis
                          ↓
                    New Recovery
```

---

# 16. Ví dụ 1 – Khôi phục sự cố LAN

Giả sử Access Switch tại Branch A bị lỗi uplink.

### Bước 1 – Quan sát

Telemetry:

```text
Interface = DOWN
Packet Loss = 100%
Users affected = 35
```

### Bước 2 – Phát hiện

AI:

```text
Anomaly Detected
```

### Bước 3 – RCA

```text
Root Cause:
Access Link Failure
```

### Bước 4 – Quyết định

```text
Recovery:
Reroute traffic through alternative path
```

### Bước 5 – Controller

```text
AI
 ↓
SDN Controller
 ↓
Flow / Path Adjustment
 ↓
Switch
```

### Bước 6 – Xác minh

```text
Packet Loss = 0%
Latency = Normal
Users = Reachable
```

Kết luận:

```text
LAN Recovery SUCCESS
```

---

# 17. Ví dụ 2 – Khôi phục sự cố WAN

Giả sử MPLS tại Branch B bị suy giảm.

Telemetry:

```text
Latency = 300 ms
Packet Loss = 65%
Jitter = 80 ms
```

AI:

```text
Anomaly
 ↓
RCA
 ↓
MPLS Degradation
 ↓
Recovery Decision
```

Recovery Intent:

```text
Branch B
Critical Traffic
        ↓
Internet Path
```

SD-WAN Controller:

```text
Apply Traffic Steering
        ↓
Internet
```

Sau đó:

```text
Latency = 25 ms
Packet Loss = 0.2%
Application = Reachable
```

Kết luận:

```text
WAN Recovery SUCCESS
```

---

# 18. Các thành phần nên được đánh giá trong luận văn

Hệ thống nên được đánh giá bằng các chỉ số:

| KPI | Ý nghĩa |
|---|---|
| Detection Accuracy | Độ chính xác phát hiện sự cố |
| Precision | Tỷ lệ cảnh báo đúng |
| Recall | Khả năng phát hiện sự cố |
| F1-score | Đánh giá tổng hợp Detection |
| RCA Accuracy | Độ chính xác xác định nguyên nhân |
| MTTD | Mean Time To Detect |
| MTTR | Mean Time To Recover |
| Recovery Success Rate | Tỷ lệ tự phục hồi thành công |
| Recovery Latency | Thời gian thực hiện khôi phục |
| False Recovery Rate | Tỷ lệ khôi phục sai |
| Network Downtime | Thời gian mạng bị gián đoạn |
| Blast Radius | Phạm vi ảnh hưởng của sự cố |

Trong đó, **MTTD và MTTR** là hai chỉ số đặc biệt quan trọng đối với đề tài tự phục hồi.

---

# 19. Phạm vi sự cố đề xuất

Để đề tài không bị quá rộng, có thể giới hạn thực nghiệm vào một số fault scenario đại diện.

## LAN

```text
1. Link Failure
2. Interface Congestion
3. Switch Failure
```

## WAN

```text
4. MPLS Failure
5. High Latency
6. Packet Loss / Path Degradation
```

Sau đó đánh giá khả năng của hệ thống:

```text
Fault
 ↓
Detection
 ↓
RCA
 ↓
Decision
 ↓
Controller Action
 ↓
Verification
```

---

# 20. Vai trò của từng lớp

| Thành phần | Vai trò |
|---|---|
| Telemetry Collector | Thu thập trạng thái mạng |
| Anomaly Detection | Phát hiện bất thường |
| RCA | Xác định nguyên nhân |
| Recovery Decision Engine | Quyết định phương án khôi phục |
| Policy/Safety Layer | Kiểm tra tính an toàn |
| Global Orchestrator | Điều phối Controller |
| SDN Controller | Khôi phục LAN |
| SD-WAN Controller | Khôi phục WAN |
| Network Devices | Thực thi thay đổi |
| Verification | Kiểm tra kết quả |
| Feedback | Đưa trạng thái mới về AI |

---

# 21. Điểm đóng góp chính của kiến trúc

Điểm nổi bật của kiến trúc không nằm ở việc chỉ sử dụng AI để phát hiện lỗi.

Đóng góp chính có thể được định hướng là:

> **Xây dựng kiến trúc mạng doanh nghiệp tự phục hồi theo mô hình closed-loop, trong đó AI có khả năng quan sát đồng thời miền LAN và WAN, phát hiện bất thường, xác định nguyên nhân sự cố, đưa ra quyết định khôi phục và điều phối SDN Controller hoặc SD-WAN Controller thực thi hành động khôi phục tương ứng.**

Mô hình này tạo ra sự phối hợp:

```text
                AI
                 │
       Global Network View
                 │
       ┌─────────┴─────────┐
       │                   │
      LAN                 WAN
       │                   │
      SDN               SD-WAN
       │                   │
       └─────────┬─────────┘
                 │
          Self-Healing
```

---

# 22. Kiến trúc chốt cho luận văn

Cuối cùng, kiến trúc được chốt theo mô hình:

```text
                              ENTERPRISE NETWORK
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                        LAN                       WAN
                         │                         │
                  ┌──────▼──────┐           ┌──────▼──────┐
                  │ SDN Domain  │           │ SD-WAN Domain│
                  └──────┬──────┘           └──────┬──────┘
                         │                         │
                         │      Telemetry          │
                         └────────────┬────────────┘
                                      ▼
                       ┌──────────────────────────┐
                       │     AI SELF-HEALING      │
                       │         ENGINE            │
                       │                          │
                       │ Telemetry Processing      │
                       │ Anomaly Detection         │
                       │ Root Cause Analysis       │
                       │ Recovery Decision         │
                       └────────────┬─────────────┘
                                    │
                              Recovery Intent
                                    ▼
                       ┌──────────────────────────┐
                       │ POLICY / SAFETY LAYER    │
                       └────────────┬─────────────┘
                                    │
                                    ▼
                       ┌──────────────────────────┐
                       │ GLOBAL NETWORK           │
                       │ ORCHESTRATOR             │
                       └────────────┬─────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
           ┌─────────────────┐             ┌─────────────────┐
           │ SDN CONTROLLER  │             │ SD-WAN CONTROLLER│
           │      LAN        │             │       WAN        │
           └────────┬────────┘             └────────┬────────┘
                    │                               │
                    ▼                               ▼
             LAN Infrastructure              WAN Infrastructure
                    │                               │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                           Network New State
                                   │
                                   ▼
                         Verification / Feedback
                                   │
                                   └──────────→ AI
```

## Kết luận

Kiến trúc trên thể hiện rõ ba vai trò:

**AI = Intelligence**

> Quan sát, phát hiện, phân tích, xác định nguyên nhân và quyết định khôi phục.

**SDN / SD-WAN Controller = Control & Execution**

> Nhận yêu cầu khôi phục và chuyển thành các hành động điều khiển mạng.

**Network Infrastructure = Execution Environment**

> Switch, router, SD-WAN Edge, AP và các đường truyền thực hiện thay đổi.

Toàn bộ hệ thống tạo thành một vòng lặp:

> **Observe → Detect → Analyze → Decide → Act → Verify → Observe**

Đây chính là nền tảng của mô hình **Mạng doanh nghiệp tự phục hồi (Enterprise Self-Healing Network)** được đề xuất trong đề tài.