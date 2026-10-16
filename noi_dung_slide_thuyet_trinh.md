# NỘI DUNG SLIDE BÁO CÁO GIẢNG VIÊN HƯỚNG DẪN
## BÁO CÁO TỔNG QUAN Ý TƯỞNG & KIẾN TRÚC TỰ PHỤC HỒI MẠNG ENTERPRISE SD-WAN

**Đề tài:** MẠNG DOANH NGHIỆP TỰ PHỤC HỒI SỬ DỤNG SD-WAN VÀ CƠ CHẾ KHÔI PHỤC SỰ CỐ THÔNG MINH  
**Trọng tâm báo cáo:** Kiến trúc Closed-Loop, Chi tiết Quá trình Dự báo & Tự phục hồi, và Bộ Kịch bản Sự cố Hướng tới Xử lý.  
**Tài liệu tham chiếu chính:** `chot_y_tuong.md` & `cau_truc_tu_phuc_hoi_sdwan.md`

---

## SLIDE 1: TRANG TIÊU ĐỀ BÁO CÁO GVHD
* **Tiêu đề:** BÁO CÁO TỔNG QUAN Ý TƯỞNG DỰ ÁN KHÓA LUẬN TỐT NGHIỆP
* **Tên đề tài:** MẠNG DOANH NGHIỆP TỰ PHỤC HỒI SỬ DỤNG SD-WAN VÀ CƠ CHẾ KHÔI PHỤC SỰ CỐ THÔNG MINH
* **Sinh viên thực hiện:** [Họ và tên Sinh viên] - [MSSV]
* **Giảng viên hướng dẫn:** [Họ và tên GVHD]
* **Mục tiêu buổi làm việc:** Báo cáo tổng quan ý tưởng kiến trúc, giải trình chi tiết cơ chế AI dự báo & tự phục hồi, trình bày bộ kịch bản sự cố thử nghiệm và xin ý kiến định hướng từ Thầy/Cô.

---

## SLIDE 2: TỔNG QUAN Ý TƯỞNG & BẢN CHẤT ĐỀ TÀI
* **Ý tưởng cốt lõi:**
  * Chuyển đổi từ mô hình vận hành mạng **Bị động - Thủ công (Reactive & Manual)** sang mô hình **Tự vận hành - Tự phục hồi thông minh (Closed-Loop Self-Healing)**.
* **Bản chất của giải pháp:**
  1. **Không bắt chước phần mềm đóng:** Tự phát triển SD-WAN Controller và AI Engine để nắm trọn mã nguồn.
  2. **Song hành Kép (Dual AI Engine):**
     * **Reactive (Ứng phó sự cố):** Dùng **PPO Reinforcement Learning** xử lý lỗi cứng (đứt cáp, đứt đường WAN, sập switch, lỗi Flow Table).
     * **Proactive (Dự báo chủ động):** Dùng **Holt-Winters/LSTM & QoE Regression** xử lý lỗi mềm (tắc nghẽn mạng, suy giảm chất lượng cuộc gọi thoại trước khi đứt).
  3. **Safety-First (An toàn là trên hết):** Đặt lớp **Safety Guardrails** duyệt mọi lệnh của AI trước khi gửi tới thiết bị.
* **Visual:** Sơ đồ chuyển đổi từ "Mạng truyền thống (Manual SSH)" sang "Closed-Loop AI Network".

---

## SLIDE 3: TỔNG QUAN TOPOLOGY & PHÂN ĐỊNH PHẠM VI ĐIỀU KIỂM
* **Mô hình hạ tầng:** 3 Chi nhánh (Bảo Lộc, Nha Trang, HCM) + 1 Data Center + 5 Đường WAN Transport (MPLS, Internet, LTE, 5G, VPN).
* **Phân định rõ ràng phạm vi điều khiển:**

```
                        ┌──────────────────────────────────────────┐
                        │          AI SELF-HEALING ENGINE          │
                        │    (Anomaly Detection + RCA + Decision)  │
                        └────────────────────┬─────────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       │                                           │
         ┌─────────────┴─────────────┐               ┌─────────────┴─────────────┐
         │       SDN CONTROLLER      │               │     SD-WAN CONTROLLER     │
         │      (Faucet / Ryu)       │               │      (Python custom)      │
         │   BỘ NÃO ĐIỀU KHIỂN LAN   │               │   BỘ NÃO ĐIỀU KHIỂN WAN   │
         └─────────────┬─────────────┘               └─────────────┬─────────────┘
                       │                                           │
          ┌────────────┴───────────┐                  ┌────────────┴───────────┐
          │  OpenFlow 1.3 Protocol │                  │   REST API / Policy    │
          │  OVS Switches / Ports  │                  │   Edge Routers / Paths │
          │  VLANs / Flow Tables   │                  │   Traffic Steering     │
          └────────────────────────┘                  └────────────────────────┘
```

* **Quy tắc:** AI không trực tiếp gõ lệnh vào router/switch. AI ra lệnh **Recovery Intent**, SDN Controller thực thi trong LAN, SD-WAN Controller thực thi ngoài WAN.

---

## SLIDE 4: QUÁ TRÌNH TỰ PHỤC HỒI TỔNG THỂ (CLOSED-LOOP AUTOMATION)
* **Luồng xử lý 6 bước khép kín (Chi tiết từng giây):**

```
 [1. TELEMETRY]  ──5s/lần──► [2. ANOMALY DETECT] ──Phát hiện──► [3. RCA ENGINE]
 (Prometheus metrics)        (Ngưỡng Latency/Loss)              (Định vị điểm lỗi)
                                                                       │
                                                                  Root Cause
                                                                       │
 [6. EXEC & VERIFY] ◄──Duyệt OK─ [5. SAFETY LAYER] ◄─Intent Decision─ [4. AI DECISION]
 (SDN/SD-WAN Controller)     (Policy & Risk Check)             (PPO RL / Proactive)
```

1. **Telemetry:** Prometheus & Custom Probes lấy chỉ số mỗi 5s (CPU, Mem, Loss, Latency, Jitter, Flow stats).
2. **Anomaly Detection:** So sánh với ngưỡng (Baseline). Nếu Latency $> 100ms$ hoặc Loss $> 2\%$ $\rightarrow$ Kích hoạt RCA.
3. **RCA (Root Cause Analysis):** Phân tích ma trận sự phụ thuộc $\rightarrow$ Tìm ra thiết bị hỏng nguyên phát.
4. **AI Decision Engine:** Lựa chọn phương án sửa lỗi tốt nhất (Reset port, Reroute flow, Steering traffic).
5. **Safety Layer Check:** Kiểm tra độ tin cậy $\ge 80\%$, vi phạm ACL hay không, bán kính ảnh hưởng.
6. **Execute & Verify:** Controller gửi lệnh điều khiển. Thu thập Telemetry mới để xác nhận mạng đã bình thường.

---

## SLIDE 5: CHI TIẾT CƠ CHẾ PHẢN ỨNG (REACTIVE - PPO RL AGENT)
* **Đối tượng xử lý:** Các sự cố vật lý đứt đứt liên kết đột ngột, sập switch, lỗi bảng Flow Table.
* **Cách thức PPO Agent ra quyết định:**

```
Vector Trạng Thái s_t (8 chiều Telemetry)
┌────────────────────────────────────────────────────────────────────────┐
│ s_t = [ C_cpu, C_res_mem, C_virt_mem, f_sent, f_err, f_conn, f_disc, P_down ] │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                         Mô hình PPO Policy Network
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
     Action a_0               Action a_1               Action a_3
      (No-op)                (Reset Port)         (Bespoke Flow Heal)
 (Mạng bình thường)      (Khi P_down > 0)          (Khi f_err > 0)
```

* **Cơ chế Thưởng/Phạt (Reward Matrix):**
  * Khôi phục thành công: Thưởng $+10$ (Port reset), $+15$ (Flow restore), $+20$ (Full Datapath).
  * Can thiệp sai (False Alarm): Phạt $-5$.
  * Bỏ sót sự cố (Missed Fault): Phạt $-10$.
* **Ưu điểm:** Agent tự học qua mô phỏng, xử lý được cả các kịch bản lỗi LAN phức tạp mà con người khó dự đoán hết.

---

## SLIDE 6: CHI TIẾT CƠ CHẾ DỰ BÁO (PROACTIVE - FORECASTING & QOE)
* **Đối tượng xử lý:** Các sự cố suy giảm chất lượng từ từ (Tắc nghẽn WAN, Jitter tăng, rớt điểm MOS cuộc gọi).
* **Quá trình diễn ra theo 2 nhánh:**

### Nhánh 1: Dự báo Traffic Spike (Holt-Winters / LSTM)
* **Input:** Chuỗi thời gian `bytes_sent` thu thập từ Prometheus mỗi 5 giây.
* **Tính toán:** Tốc độ tăng trưởng lưu lượng $d(Traffic)/dt$.
* **Dự báo:** *"Đường MPLS đang 65%, tốc độ tăng hiện tại sẽ khiến MPLS quá tải 92% sau 15 giây nữa"*.
* **Hành động chủ động:** SD-WAN Controller điều hướng trước các luồng dữ liệu nặng (Bulk Backup) sang Internet/VPN **TRƯỚC KHI** đường MPLS bị nghẽn hoàn toàn.

### Nhánh 2: Đánh giá Chất lượng Trải nghiệm (QoE Regression Engine)
* **Input:** Latency, Jitter, Packet Loss thực tế trên đường truyền.
* **Tính toán:** Điểm MOS VoIP (từ 1.0 đến 5.0).
* **Cảnh báo:** Jitter tăng $\rightarrow$ Điểm MOS giảm từ $4.2 \rightarrow 3.8 \rightarrow 3.2$ (tiệm cận ngưỡng SLA 3.5).
* **Hành động chủ động:** Thực hiện **Mid-session Steering** chuyển luồng thoại VoIP sang đường 5G khi MOS = 3.2 $\rightarrow$ Người dùng gọi điện liên tục không bị mất tiếng hay gián đoạn.

---

## SLIDE 7: LỚP KIỂM SOÁT AN TOÀN (SAFETY GUARDRAILS LAYER)
* **Vai trò:** Bảo vệ hệ thống mạng khỏi các quyết định sai lầm hoặc chưa tối ưu của AI.
* **Quy trình thẩm định quyết định của AI:**

```
                          Quyết định từ AI Engine
                                     │
                                     ▼
                   ┌──────────────────────────────────┐
                   │    SAFETY GUARDRAILS CHECKER     │
                   ├──────────────────────────────────┤
                   │ 1. Vi phạm Policy / ACL?         │
                   │ 2. Confidence Score ≥ 80%?       │
                   │ 3. Blast Radius ≤ 30% User?      │
                   │ 4. Có phương án Rollback chưa?   │
                   └─────────────────┬────────────────┘
                                     │
                        Đạt tất cả tiêu chí?
                         /                \
                       YES                 NO
                        │                   │
                        ▼                   ▼
               [TỰ ĐỘNG THỰC THI]     [CHUYỂN KỸ SƯ NOC]
                  (Dưới 1 giây)       (Phê duyệt thủ công)
```

---

## SLIDE 8: DANH SÁCH 14 SỰ CỐ MẠNG HƯỚNG TỚI XỬ LÝ
* **Phân loại 14 Kịch bản Sự cố thử nghiệm chi tiết:**

### 🔴 Nhóm Sự cố Phản ứng (Reactive Scenarios - F01 đến F12)
1. **F01 - Access Link Failure:** Đứt cáp nối Access Switch (Nha Trang).
2. **F02 - Distribution Failure:** Sập router Distribution Master (Nha Trang/HCM) $\rightarrow$ Kích hoạt VRRP Failover.
3. **F03 - OSPF Link Failure:** Đứt kết nối L3 giữa các chi nhánh $\rightarrow$ OSPF Reconvergence.
4. **F04 - MPLS Down:** Đứt đường WAN MPLS chính $\rightarrow$ Chuyển toàn bộ lưu lượng sang 5G/Internet.
5. **F05 - Internet Down:** Mất kênh Internet $\rightarrow$ Route traffic Web qua 5G/VPN.
6. **F06 - LTE Down:** Mất đường di động backup $\rightarrow$ Chuyển sang 5G.
7. **F07 - 5G Degradation:** Đường 5G bị nhiễu/suy hao packet loss $>5\%$ $\rightarrow$ Trả traffic về MPLS.
8. **F08 - VPN Failure:** Sập kênh VPN mã hóa $\rightarrow$ Chuyển luồng bảo mật sang MPLS.
9. **F09 - WAN Congestion:** Tắc nghẽn băng thông MPLS ($>85\%$) $\rightarrow$ Traffic steering + QoS.
10. **F10 - VoIP Degradation:** Jitter cao làm rớt MOS thoại $\rightarrow$ QoE-driven path change.
11. **F11 - Web Server Crash:** Sập Web01 ở DC $\rightarrow$ HAProxy Load Balancer chuyển sang Web02.
12. **F12 - Multi-metric Anomaly:** Lỗi đa chỉ số phức tạp $\rightarrow$ Kích hoạt chuỗi khôi phục tự động AI.

### 🟡 Nhóm Sự cố Dự báo Chủ động (Proactive Scenarios - P1 & P2)
13. **P1 - Preemptive Traffic Steering:** Dự báo tắc nghẽn do lịch Backup dữ liệu lúc 2h sáng.
14. **P2 - Mid-Session QoE Protection:** Dự báo vi phạm SLA thoại do Jitter tăng từ từ.

---

## SLIDE 9: PHÂN TÍCH VÍ DỤ CỤ THỂ: CÁCH HỆ THỐNG XỬ LÝ SỰ CỐ
* **Ví dụ 1: Xử lý sự cố đứt đường WAN MPLS (F04 - Reactive)**
  * **Hiện tượng:** Kênh MPLS giữa HCM và DC bị đứt cáp quang biển.
  * **Phát hiện:** SD-WAN Edge probe phát hiện mất gói 100% trên kênh MPLS.
  * **Luồng tự phục hồi:**
    1. Telemetry phát hiện `wan_path_status{transport="MPLS"} = 0`.
    2. SD-WAN Controller tính toán bảng đường truyền còn lại: Đường 5G có Latency 15ms, Loss 0.3% (Tốt nhất).
    3. SD-WAN Controller ra lệnh cho HCM-GW chuyển luồng VoIP & DB sang 5G, luồng Web sang Internet.
    4. **Thời gian phục hồi:** $< 5$ giây.

---

## SLIDE 10: PHÂN TÍCH VÍ DỤ CỤ THỂ: CÁCH HỆ THỐNG DỰ BÁO SỰ CỐ
* **Ví dụ 2: Dự báo và xử lý tắc nghẽn lưu lượng chủ động (P1 - Proactive)**
  * **Kịch bản:** Lúc 02:00:00, tiến trình Backup tự động từ HCM về Data Center khởi chạy làm lưu lượng tăng vọt.
  * **Luồng dự báo & tự phục hồi:**
    1. Lúc 01:59:45 (trước 15 giây), Holt-Winters Model phát hiện tốc độ tăng lưu lượng $d(Traffic)/dt$ bất thường.
    2. Model dự tính: Đến 02:00:05, kênh MPLS sẽ đạt mức $95\%$ băng thông (Gây nghẽn nặng).
    3. Proactive Engine kích hoạt trước 02:00:00: Chuyển toàn bộ luồng Backup nặng sang kênh Internet (băng thông rộng), giữ kênh MPLS thông thoáng cho luồng ứng dụng Core.
    4. **Kết quả:** Người dùng hoàn toàn không hề thấy mạng bị chậm hay rớt gói (MTTR = **0 giây**).

---

## SLIDE 11: NGUỒN DỮ LIỆU TELEMETRY & NOC DASHBOARD
* **Ma trận dữ liệu Telemetry thu thập:**

| Chỉ số Telemetry | Công cụ / Nguồn | Tần suất | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **CPU / Memory / Disk** | Prometheus Node Exporter | 5 giây | Đầu vào cho PPO State Vector $s_t$ |
| **Packet Loss / Delay / Jitter** | ICMP / iperf3 Custom Probes | 5 giây | Đánh giá chất lượng 5 đường WAN |
| **Interface & Port Status** | OpenFlow `port_status` | Real-time | Phát hiện sự cố đứt cáp L2/L3 |
| **Flow Error Stats** | OpenFlow `flow_stats` | 5 giây | Phát hiện tràn/lỗi bảng Flow Table |
| **OSPF / VRRP State** | FRR / Keepalived Syslog | Event-driven | Xác định trạng thái định tuyến L3 |

* **Giao diện NOC Dashboard (Flask + SocketIO):**
  * Trực quan hóa Topology 4 sites theo thời gian thực.
  * Hiển thị bảng nhật ký quyết định AI (AI Decision Log), chỉ số Confidence Score và nút can thiệp đè lệnh (Manual Override).

---

## SLIDE 12: XIN Ý KIẾN ĐỊNH HƯỚNG TỪ GIẢNG VIÊN HƯỚNG DẪN
* **Các đóng góp cốt lõi của đề tài xin báo cáo Thầy/Cô:**
  1. Mô hình hóa 5 đường WAN bằng thuần Mininet + `tc netem`.
  2. Tự lập trình SD-WAN Controller bằng Python (không dùng Black-box commercial software).
  3. Kết hợp thành công giữa PPO RL (Reactive) và Forecast/QoE (Proactive).
  4. Đảm bảo tính an toàn hệ thống với lớp Safety Guardrails.
* **Các điểm sinh viên xin ý kiến định hướng từ GVHD:**
  * Thầy/Cô đánh giá bộ **14 Kịch bản sự cố** đã đủ độ bao phủ cho bài Khóa luận chưa? Có cần bổ sung kịch bản nào đặc thù không ạ?
  * Ngưỡng Confidence Score ($80\%$) và Blast Radius ($30\%$) của lớp Safety Layer có cần điều chỉnh theo từng loại chi nhánh không ạ?
  * Định hướng công bố kết quả: So sánh MTTR giữa Mạng truyền thống vs Mạng Self-Healing dưới dạng biểu đồ dạng cột.

---
* **XIN CHÂN THÀNH CẢM ƠN THẦY/CÔ ĐÃ LẮNG NGHE VÀ GIÚP ĐỠ!**
