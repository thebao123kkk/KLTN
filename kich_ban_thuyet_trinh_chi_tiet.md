# KỊCH BẢN THUYẾT TRÌNH BÁO CÁO GIẢNG VIÊN HƯỚNG DẪN
## Speaker Notes & Presentation Guide for Advisor Review

* **Đối tượng báo cáo:** Giảng viên hướng dẫn (GVHD).
* **Mục tiêu:** Báo cáo tổng quan ý tưởng, làm rõ quá trình dự báo & tự phục hồi diễn ra như thế nào, giải trình 14 kịch bản sự cố và xin ý kiến định hướng.
* **Thời lượng đề xuất:** 10 – 15 phút.
* **Tông giọng:** Lịch sự, lễ phép, rành mạch, đi thẳng vào bản chất kỹ thuật và giải thuật AI.

---

## SLIDE 1: TRANG TIÊU ĐỀ BÁO CÁO GVHD
* **Thời lượng:** 30 giây

### 🎤 Lời thoại trình bày:
> *"Em chào Thầy/Cô ạ! Hôm nay em xin phép được báo cáo tổng quan ý tưởng và tiến độ kiến trúc đề tài Khóa luận Tốt nghiệp:*
>
> ***'Mạng doanh nghiệp tự phục hồi sử dụng SD-WAN và cơ chế khôi phục sự cố thông minh'***.
>
> *Nội dung báo cáo hôm nay em xin phép tập trung làm rõ 3 phần chính mà Thầy/Cô đã định hướng: Chi tiết quá trình AI dự báo và tự phục hồi diễn ra như thế nào, các kịch bản sự cố cụ thể hệ thống xử lý ra sao, và xin ý kiến đóng góp của Thầy/Cô để hoàn thiện đề tài ạ."*

---

## SLIDE 2: TỔNG QUAN Ý TƯỞNG & BẢN CHẤT ĐỀ TÀI
* **Thời lượng:** 1 phút

### 🎤 Lời thoại trình bày:
> *"Thưa Thầy/Cô, bản chất ý tưởng của đề tài là chuyển đổi toàn bộ quy trình vận hành mạng doanh nghiệp từ bị động - làm thủ công sang **Closed-Loop Self-Healing** (Tự phục hồi vòng lặp khép kín).*
>
> *Điểm khác biệt cốt lõi trong giải pháp của em là:*
> *- Em **không sử dụng các phần mềm thương mại đóng (Black-box)** mà tự viết hoàn toàn SD-WAN Controller và AI Engine bằng Python.*
> *- Hệ thống sở hữu **Cơ chế Kép**: Dùng thuật toán Học tăng cường **PPO Reinforcement Learning** cho nhánh **Reactive** để sửa các sự cố cứng như đứt liên kết/hỏng flow; và dùng **Holt-Winters/LSTM + QoE Regression** cho nhánh **Proactive** để dự báo tắc nghẽn và suy giảm chất lượng ứng dụng trước khi đứt.*
> *- Đặt lớp **Safety Guardrails** thẩm định an toàn trước khi cho phép AI can thiệp vào thiết bị."*

---

## SLIDE 3: TỔNG QUAN TOPOLOGY & PHÂN ĐỊNH PHẠM VI ĐIỀU KHIỂN
* **Thời lượng:** 1 phút

### 🎤 Lời thoại trình bày:
> *"Về mô hình hạ tầng, đề tài xây dựng 3 Chi nhánh, 1 Data Center và 5 đường WAN (MPLS, Internet, LTE, 5G, VPN).*
>
> *Về phân định trách nhiệm điều khiển:*
> *- **SDN Controller (Faucet/Ryu)** đóng vai trò là bộ não điều khiển miền LAN. Nó quản lý các OVS Switch, cổng switch, VLAN và bảng Flow Table qua giao thức OpenFlow 1.3.*
> *- **SD-WAN Controller (tự viết)** đóng vai trò là bộ não điều khiển miền WAN. Nó quản lý các Edge Router, chọn đường truyền WAN và thực hiện Traffic Steering.*
>
> *AI Engine đứng ở tầng trên cùng đóng vai trò chỉ huy. AI ra **Recovery Intent**, nếu thuộc phạm vi LAN sẽ chuyển cho SDN thực thi, nếu thuộc phạm vi WAN sẽ chuyển cho SD-WAN thực thi ạ."*

---

## SLIDE 4: QUÁ TRÌNH TỰ PHỤC HỒI TỔNG THỂ (CLOSED-LOOP AUTOMATION)
* **Thời lượng:** 1 phút 30 giây

### 🎤 Lời thoại trình bày:
> *"Thưa Thầy/Cô, đây là luồng xử lý 6 bước của quá trình tự phục hồi diễn ra theo thời gian thực:*
>
> *1. **Telemetry Collector**: Prometheus thu thập các chỉ số mạng mỗi 5s/lần.*
> *2. **Anomaly Detection**: Nếu các chỉ số như Latency $>100ms$ hoặc Packet Loss $>2\%$, hệ thống kích hoạt module Anomaly.*
> *3. **Root Cause Analysis (RCA)**: Phân tích nguyên nhân gốc rễ để xác định chính xác thiết bị hỏng.*
> *4. **AI Decision Engine**: Quyết định phương án sửa lỗi tốt nhất (dùng PPO RL nếu đứt cáp, hoặc dùng Proactive Engine nếu nghẽn WAN).*
> *5. **Safety Layer Check**: Kiểm tra phương án đó có an toàn không (Confidence $\ge 80\%$, Blast Radius $\le 30\%$).*
> *6. **Execution & Verification**: Ra lệnh cho Controller thực thi và thu thập Telemetry mới để kiểm tra xem mạng đã xanh lại chưa ạ."*

---

## SLIDE 5: CHI TIẾT CƠ CHẾ PHẢN ỨNG (REACTIVE - PPO RL AGENT)
* **Thời lượng:** 1 phút 30 giây

### 🎤 Lời thoại trình bày:
> *"Đi sâu vào cơ chế **Reactive Self-Healing**, em áp dụng thuật toán **PPO Reinforcement Learning**:*
>
> *- **Trạng thái $s_t$** là vector 8 chiều gồm các thông số thực tế của Telemetry: CPU/Mem của Controller, số gói gửi, số gói lỗi, số kết nối mất và số cổng bị down.*
> *- **Không gian hành động** gồm 4 mức can thiệp: $a_0$ No-op (không can thiệp khi mạng bình thường), $a_1$ Reset Port (khi $P_{down} > 0$), $a_2$ Restart Datapath (khi CPU tràn), và $a_3$ Bespoke Flow Heal (xóa flow hỏng `OFPFC_DELETE` và nạp lại flow sạch khi $f_{err} > 0$).*
>
> *Agent được huấn luyện qua hàm thưởng/phạt để tự đưa ra hành động tối ưu nhất mà không cần kỹ sư viết luật cứng ạ."*

---

## SLIDE 6: CHI TIẾT CƠ CHẾ DỰ BÁO (PROACTIVE - FORECASTING & QOE)
* **Thời lượng:** 1 phút 30 giây

### 🎤 Lời thoại trình bày:
> *"Đối với cơ chế **Proactive Self-Healing**, quá trình dự báo diễn ra theo 2 nhánh:*
>
> *1. **Dự báo Traffic Spike**: Dùng mô hình **Holt-Winters / LSTM** phân tích tốc độ tăng lưu lượng $d(Traffic)/dt$. Nếu phát hiện lưu lượng đang tăng với tốc độ có thể làm vọt mức $92\%$ băng thông MPLS trong 15s tới, SD-WAN Controller sẽ chủ động chuyển trước các luồng dữ liệu nặng sang đường Internet **trước khi** đường MPLS bị đứt/tắc.*
>
> *2. **Đánh giá QoE thoại VoIP**: Dùng mô hình Hồi quy QoE tính điểm chất lượng trải nghiệm MOS. Khi Jitter tăng làm điểm MOS giảm từ $4.2 \rightarrow 3.8 \rightarrow 3.2$ (tiệm cận mức SLA 3.5), hệ thống sẽ **Mid-session Steering** chuyển luồng VoIP sang đường 5G ngay lập tức. Nhờ đó cuộc gọi thoại diễn ra mượt mà, người dùng không hề nhận ra sự gián đoạn."*

---

## SLIDE 7: LỚP KIỂM SOÁT AN TOÀN (SAFETY GUARDRAILS LAYER)
* **Thời lượng:** 1 phút

### 🎤 Lời thoại trình bày:
> *"Để tránh trường hợp AI ra quyết định sai gây thảm họa cho mạng doanh nghiệp, em xây dựng lớp **Safety Guardrails** làm cổng thẩm định:*
>
> *Mọi quyết định từ AI phải vượt qua 4 tiêu chí: Không vi phạm ACL, Độ tin cậy Confidence $\ge 80\%$, Ảnh hưởng dưới $30\%$ người dùng, và có sẵn plan Rollback cấu hình cũ.*
>
> *Nếu đạt tất cả, hệ thống tự động thực thi dưới 1s. Nếu không đạt (ví dụ AI đề xuất reset Core Switch với Confidence $55\%$), hệ thống giữ nguyên mạng an toàn và đẩy cảnh báo về NOC Dashboard để kỹ sư duyệt thủ công ạ."*

---

## SLIDE 8: DANH SÁCH 14 SỰ CỐ MẠNG HƯỚNG TỚI XỬ LÝ
* **Thời lượng:** 1 phút 15 giây

### 🎤 Lời thoại trình bày:
> *"Thưa Thầy/Cô, tài liệu của em hướng tới giải quyết bộ **14 Kịch bản sự cố toàn diện** bao gồm:*
>
> *- **12 sự cố Reactive (F01-F12)**: Từ đứt cáp Access, sập router Distribution (VRRP failover), sập OSPF, đứt từng kênh WAN (MPLS, Internet, LTE, 5G, VPN), tắc nghẽn băng thông, rớt điểm MOS VoIP, cho tới sập Web Server.*
> *- **2 sự cố Proactive (P1 & P2)**: Dự báo tắc nghẽn lưu lượng đợt Backup đêm và dự báo rớt điểm chất lượng thoại.*
>
> *Mục tiêu MTTR là $<5s$ cho WAN, $<30s$ cho LAN, và **0s** cho các kịch bản dự báo chủ động ạ."*

---

## SLIDE 9 & 10: PHÂN TÍCH VÍ DỤ CỤ THỂ XỬ LÝ & DỰ BÁO SỰ CỐ
* **Thời lượng:** 1 phút 30 giây

### 🎤 Lời thoại trình bày:
> *"Em xin phân tích 2 ví dụ điển hình để Thầy/Cô thấy rõ luồng xử lý:*
>
> *- **Ví dụ Reactive (F04 - Đứt MPLS)**: Khi cáp quang MPLS bị đứt, SD-WAN Probe phát hiện mất gói $100\%$. Telemetry đẩy metric về AI. SD-WAN Controller tính toán trong các kênh còn lại thì 5G có Latency 15ms tốt nhất, lập tức đẩy config chuyển VoIP & DB sang 5G trong $<5$ giây.*
>
> *- **Ví dụ Proactive (P1 - Backup 2h sáng)**: Lúc 01:59:45 (trước 15 giây), Holt-Winters phát hiện lưu lượng tăng vọt. Dự báo 02:00:05 đường MPLS sẽ đạt $95\%$. Hệ thống chủ động chuyển luồng Backup sang Internet từ 02:00:00. Kết quả là đường MPLS không bao giờ bị nghẽn, người dùng không bị rớt gói nào (MTTR = 0s) ạ."*

---

## SLIDE 11: NGUỒN DỮ LIỆU TELEMETRY & NOC DASHBOARD
* **Thời lượng:** 1 phút

### 🎤 Lời thoại trình bày:
> *"Toàn bộ hệ thống được nuôi bằng dữ liệu Telemetry lấy từ Prometheus Exporters, ICMP/iperf3 Probes và OpenFlow events mỗi 5s/lần.*
>
> *Em cũng đã thiết kế giao diện **NOC Dashboard** bằng Flask và SocketIO để hiển thị Topology thời gian thực, bảng nhật ký AI Log và cung cấp nút bấm Manual Override khi kỹ sư muốn đè lệnh AI."*

---

## SLIDE 12: XIN Ý KIẾN ĐỊNH HƯỚNG TỪ GIẢNG VIÊN HƯỚNG DẪN
* **Thời lượng:** 1 phút 30 giây

### 🎤 Lời thoại trình bày:
> *"Dạ thưa Thầy/Cô, trên đây là toàn bộ tổng quan ý tưởng kiến trúc và cơ chế tự phục hồi của đề tài.*
>
> *Em xin phép được xin ý kiến định hướng của Thầy/Cô ở 3 điểm sau ạ:*
>
> *1. Bộ **14 kịch bản sự cố** này theo đánh giá của Thầy/Cô đã đủ độ bao phủ và tính thực tiễn cho luận văn chưa ạ?*
> *2. Ngưỡng Confidence ($80\%$) và Blast Radius ($30\%$) của lớp Safety Layer có cần phân biệt giữa Chi nhánh nhỏ (Bảo Lộc) và Chi nhánh lớn (HCM) không ạ?*
> *3. Về cách thức trình bày kết quả đánh giá, em định vẽ biểu đồ so sánh chỉ số MTTR giữa Mạng truyền thống vs Mạng Self-Healing dưới 14 kịch bản này, Thầy/Cô thấy phương án này đã tối ưu chưa ạ?*
>
> *Em xin cảm ơn Thầy/Cô rất nhiều ạ!"*

---

## 💡 CÁC CÂU HỎI GVHD CÓ THỂ HỎI & CÁCH TRẢ LỜI ĐẶC THÙ

### ❓ GVHD Hỏi: *Em huấn luyện PPO Agent ở đâu? Mininet có đủ nhanh để RL hội tụ không?*
* **Trả lời:** *Dạ thưa Thầy/Cô, em tạo một môi trường Gym Wrapper (`MininetEnv`) bọc lấy topology Mininet. Quá trình huấn luyện offline sẽ chạy trước trên môi trường mô phỏng này để Agent học Policy tối ưu. Khi triển khai online, Agent chỉ cần thực hiện inference (tính toán Action $a_t$ từ Vector $s_t$) nên tốc độ ra quyết định là gần như tức thì ($<10ms$) ạ.*

### ❓ GVHD Hỏi: *Thuật toán Holt-Winters liệu có dự báo chính xác được các đợt lưu lượng tăng bất ngờ không?*
* **Trả lời:** *Dạ, Holt-Winters xử lý rất tốt các lưu lượng có tính chu kỳ (như lịch backup hằng đêm). Đối với các đợt tăng bất ngờ không có chu kỳ, em bổ sung thêm biến tốc độ tăng trưởng $d(Traffic)/dt$. Nếu $d(Traffic)/dt$ vượt ngưỡng an toàn trong 2-3 chu kỳ lấy mẫu liên tiếp (10-15s), hệ thống sẽ kích hoạt chuyển hướng trước ngay lập tức mà không cần đợi mô hình chuỗi thời gian ạ.*
