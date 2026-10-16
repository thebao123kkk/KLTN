# CHƯƠNG II: CƠ SỞ LÝ THUYẾT

## Đề tài: MẠNG DOANH NGHIỆP TỰ PHỤC HỒI SỬ DỤNG SD-WAN VÀ CƠ CHẾ KHÔI PHỤC SỰ CỐ THÔNG MINH

---

## 2.1. Tổng quan về mạng WAN doanh nghiệp và công nghệ SD-WAN

### 2.1.1. Mạng WAN truyền thống (MPLS) và các hạn chế trong bối cảnh điện toán đám mây

MPLS (Multiprotocol Label Switching) là công nghệ định tuyến dữ liệu qua mạng riêng dựa trên cơ chế gán nhãn (label switching), được sử dụng phổ biến hơn 20 năm qua để kết nối trụ sở chính với các chi nhánh doanh nghiệp [1]. Ưu điểm nổi bật của MPLS là độ ổn định cao, độ trễ thấp và khả năng cam kết chất lượng dịch vụ (SLA) chặt chẽ, phù hợp với các ứng dụng thời gian thực như thoại VoIP hay hội nghị truyền hình [1]. Tuy nhiên, khi doanh nghiệp dịch chuyển ứng dụng và dữ liệu lên môi trường đa đám mây, MPLS bộc lộ nhiều hạn chế: chi phí thuê kênh riêng cao, thời gian triển khai chậm khi mở rộng chi nhánh mới, thiếu linh hoạt trong việc điều chỉnh băng thông theo nhu cầu, và đặc biệt là không tối ưu cho lưu lượng cloud vì toàn bộ traffic thường phải "đi vòng" (backhaul) qua trung tâm dữ liệu chính trước khi ra Internet, gây tăng độ trễ và giảm hiệu năng ứng dụng [1][2]. Đây chính là tiền đề thúc đẩy sự ra đời và phát triển của SD-WAN như một giải pháp thay thế hoặc bổ sung cho MPLS.

### 2.1.2. Khái niệm và kiến trúc SD-WAN

SD-WAN (Software-Defined Wide Area Network) là kiến trúc mạng diện rộng được quản trị bằng phần mềm, cho phép tổ chức hiện đại hóa hạ tầng WAN nhằm đáp ứng nhu cầu chuyển đổi số [2][3]. Nguyên lý cốt lõi của SD-WAN là tách biệt giữa **Control Plane** (mặt phẳng điều khiển) và **Data Plane** (mặt phẳng dữ liệu): Control Plane tập trung tại bộ điều khiển/orchestrator để quản lý chính sách, cấu hình và định tuyến trên toàn mạng, trong khi Data Plane tại các thiết bị biên (Edge) chịu trách nhiệm chuyển tiếp lưu lượng thực tế theo các quyết định từ Control Plane [3]. Kiến trúc SD-WAN thường gồm ba thành phần chính:

- **SD-WAN Edge (CPE)**: thiết bị đặt tại chi nhánh/trụ sở, thực hiện định tuyến, mã hóa, bảo mật và tối ưu hóa lưu lượng theo cấu hình được đẩy xuống từ Controller [3].
- **SD-WAN Controller/Orchestrator**: nền tảng quản trị tập trung, nơi quản trị viên cấu hình chính sách một lần và triển khai tự động trên toàn hệ thống [3][4].
- **SD-WAN Gateway**: điểm kết nối trung gian giúp Edge truy cập trực tiếp và an toàn vào các nền tảng đám mây công cộng (AWS, Azure, Google Cloud) [3].

### 2.1.3. Nguyên lý hoạt động

SD-WAN vận hành dựa trên khả năng tận dụng đồng thời nhiều loại kết nối WAN khác nhau (MPLS, Internet băng rộng, LTE/4G/5G) như một "resource pool" chung, sau đó dùng phần mềm để định tuyến lưu lượng một cách thông minh [3][4]. Các cơ chế chính bao gồm:

- **Định tuyến theo ứng dụng (application-aware routing)**: SD-WAN nhận diện loại ứng dụng đang chạy qua traffic (ví dụ hội nghị video, ERP, VoIP) và tự động chọn tuyến đường phù hợp nhất dựa trên yêu cầu về độ trễ, băng thông, tính toàn vẹn dữ liệu [2][4].
- **Chất lượng dịch vụ (QoS) và cân bằng tải**: lưu lượng được phân loại và ưu tiên theo chính sách cấu hình sẵn, đồng thời cân bằng tải giữa các đường truyền để tối ưu hiệu năng [4].
- **Chuyển đổi kênh dự phòng (failover)**: đây là cơ chế phục hồi cơ bản của SD-WAN — hệ thống liên tục giám sát trạng thái các đường truyền theo thời gian thực; khi phát hiện sự cố (mất kết nối, suy giảm chất lượng), lưu lượng được tự động chuyển sang đường truyền khác đang hoạt động tốt, giúp giảm thiểu thời gian gián đoạn dịch vụ [5][4].

### 2.1.4. So sánh SD-WAN với WAN truyền thống

So với WAN truyền thống, SD-WAN có ưu thế về chi phí (tận dụng Internet băng rộng thay vì phụ thuộc hoàn toàn vào MPLS đắt đỏ), khả năng quản trị tập trung từ một giao diện duy nhất, và khả năng mở rộng nhanh cho mô hình nhiều chi nhánh; ngược lại, MPLS vẫn có lợi thế về độ ổn định và cam kết SLA nên trong thực tế nhiều doanh nghiệp lựa chọn mô hình lai (Hybrid WAN) kết hợp cả hai để đảm bảo quá trình chuyển đổi diễn ra êm ả, không gián đoạn hoạt động [1].

### 2.1.5. Xu hướng tích hợp SASE vào SD-WAN

Một xu hướng quan trọng là sự hội tụ giữa SD-WAN và SASE (Secure Access Service Edge) — mô hình kết hợp năng lực định tuyến mạng của SD-WAN với các dịch vụ bảo mật được phân phối từ đám mây (NGFW, IPS, SWG, Zero Trust Network Access) trong cùng một nền tảng thống nhất [6]. Gartner dự báo đến năm 2026, khoảng 60% các thương vụ mua sắm SD-WAN mới sẽ được tích hợp vào một nền tảng SASE đơn nhà cung cấp, tăng mạnh so với tỷ lệ 15% năm 2022 [7]. Tại Việt Nam, CMC Telecom là đơn vị đầu tiên đạt chứng chỉ MEF SASE SD-WAN 3.0, phản ánh xu hướng các nhà cung cấp trong nước cũng đang bắt kịp chuẩn quốc tế này [6].

---

## 2.2. Cơ sở lý thuyết về tính sẵn sàng cao và khả năng phục hồi mạng

### 2.2.1. Các khái niệm nền tảng

- **Fault Tolerance (khả năng chịu lỗi)**: khả năng hệ thống tiếp tục hoạt động đúng chức năng ngay cả khi một hoặc một số thành phần bị lỗi.
- **Redundancy (dự phòng)**: việc bố trí nhiều thành phần/đường truyền song song để khi một thành phần gặp sự cố, thành phần dự phòng có thể thay thế ngay lập tức; trong SD-WAN, mô hình phổ biến là mỗi điểm chi nhánh được kết nối bằng ít nhất hai đường truyền độc lập nhằm đảm bảo tính liên tục kết nối [5].
- **Failover**: quá trình tự động chuyển đổi hoạt động từ thành phần/đường truyền đang gặp sự cố sang thành phần dự phòng.
- **High Availability (HA – tính sẵn sàng cao)**: đặc tính của hệ thống được thiết kế để duy trì mức độ khả dụng dịch vụ cao (thường được đo bằng tỷ lệ phần trăm thời gian hoạt động, ví dụ 99,9% – "three nines" hay 99,99% – "four nines").

### 2.2.2. Các chỉ số đo lường then chốt

Việc đánh giá hiệu quả của một cơ chế phục hồi sự cố cần dựa trên các chỉ số định lượng:

- **MTTD (Mean Time To Detect)**: thời gian trung bình để hệ thống phát hiện ra sự cố kể từ khi sự cố xảy ra.
- **MTTR (Mean Time To Recover/Repair)**: thời gian trung bình để hệ thống khôi phục lại trạng thái hoạt động bình thường sau khi phát hiện sự cố; đây cũng là chỉ số Gartner sử dụng khi định nghĩa lợi ích cốt lõi của AIOps là rút ngắn MTTR thông qua phân tích dữ liệu lớn kết hợp học máy [8].
- **MTBF (Mean Time Between Failures)**: thời gian trung bình giữa hai lần xảy ra sự cố liên tiếp, phản ánh độ tin cậy của hệ thống.
- **Availability/SLA (%)**: tỷ lệ thời gian hệ thống hoạt động bình thường trên tổng thời gian vận hành.

Các chỉ số này có ý nghĩa thực tiễn rất lớn vì downtime gây thiệt hại tài chính nghiêm trọng cho doanh nghiệp — theo khảo sát của ITIC giai đoạn 2024–2025, hơn 90% doanh nghiệp quy mô vừa và lớn báo cáo thiệt hại vượt 300.000 USD cho mỗi giờ ngừng hoạt động (đã được trình bày chi tiết ở Chương I) — do đó việc rút ngắn MTTD và MTTR chính là mục tiêu kỹ thuật trung tâm của một mạng tự phục hồi.

### 2.2.3. Cơ chế phát hiện sự cố truyền thống

Trước khi AI được tích hợp, các hệ thống mạng thường phát hiện sự cố dựa trên: (i) giám sát theo ngưỡng tĩnh (threshold-based monitoring) — cảnh báo được kích hoạt khi một chỉ số (độ trễ, tỷ lệ mất gói) vượt quá ngưỡng cố định được cấu hình sẵn; (ii) các giao thức phát hiện lỗi nhanh ở tầng mạng như BFD (Bidirectional Forwarding Detection) hoặc cơ chế keepalive/heartbeat giữa các thiết bị để nhanh chóng nhận biết mất kết nối. Hạn chế chung của các cơ chế này là ngưỡng tĩnh dễ gây ra cảnh báo giả (false positive) hoặc bỏ sót sự cố tiềm ẩn (false negative) khi điều kiện mạng thay đổi linh hoạt theo thời gian, đồng thời không có khả năng dự đoán sự cố trước khi nó xảy ra — đây chính là khoảng trống mà các kỹ thuật AI/ML được kỳ vọng lấp đầy.

---

## 2.3. Mạng tự phục hồi (Self-Healing Network)

### 2.3.1. Khái niệm và mô hình tổng quát

Mạng tự phục hồi là mạng có khả năng tự động phát hiện, chẩn đoán và khắc phục các sự cố mà không cần (hoặc chỉ cần rất ít) sự can thiệp của con người, dựa trên việc ứng dụng AI, học máy và tự động hóa để nhận diện lỗi, điểm nghẽn hiệu năng hoặc lỗ hổng bảo mật và thực hiện hành động khắc phục theo thời gian thực [9]. Khả năng "self-healing" là một trong bốn thuộc tính self-* kinh điển của hệ thống tự trị (autonomic system) do IBM đề xuất, bên cạnh self-configuration, self-optimization và self-protection [10][11].

Nền tảng lý thuyết phổ biến nhất cho việc thiết kế các hệ thống tự thích ứng (self-adaptive systems), bao gồm mạng tự phục hồi, là mô hình vòng lặp phản hồi **MAPE-K** do Kephart và Chess đề xuất trong sáng kiến Autonomic Computing của IBM năm 2003 [12][13]. MAPE-K gồm bốn giai đoạn hoạt động liên tục trên một cơ sở tri thức dùng chung (Knowledge Base):

1. **Monitor (Giám sát)**: thu thập dữ liệu thời gian thực từ hệ thống được quản lý (ví dụ độ trễ, tỷ lệ mất gói, băng thông, trạng thái đường truyền).
2. **Analyze (Phân tích)**: đánh giá dữ liệu giám sát để xác định liệu có cần thực hiện hành động thích ứng hay không (ví dụ phát hiện bất thường, dự đoán nguy cơ sự cố).
3. **Plan (Lập kế hoạch)**: xây dựng một tập hành động cụ thể nhằm đưa hệ thống về trạng thái mong muốn (ví dụ chuyển hướng lưu lượng, đổi tuyến dự phòng).
4. **Execute (Thực thi)**: triển khai hành động đã lập kế hoạch thông qua các effector tác động trực tiếp lên hệ thống được quản lý.

### 2.3.2. Kiến trúc closed-loop automation trong self-healing network

Việc vận hành mạng tự phục hồi theo mô hình MAPE-K tạo thành một vòng lặp khép kín (closed-loop automation): dữ liệu giám sát liên tục được đưa vào bộ phân tích, kết quả phân tích được dùng để cập nhật cơ sở tri thức và điều chỉnh kế hoạch hành động, sau đó hành động được thực thi và kết quả lại tiếp tục được giám sát — tạo thành chu trình tự cải thiện theo thời gian. Một nghiên cứu gần đây về khôi phục sự cố tự động cho ứng dụng web dựa trên MAPE-K cho thấy hệ thống tích hợp mô-đun "AutoFix" giúp giảm trung bình 18,6% thời gian khôi phục (TTR) sau năm chu kỳ học, đồng thời cải thiện 13% độ chính xác của các quy tắc triển khai bản vá tự động — minh chứng cho lợi ích của việc kết hợp vòng lặp phản hồi liên tục với học máy trong hệ thống tự phục hồi [14].

### 2.3.3. Vai trò của AI/ML trong việc "thông minh hóa" từng bước của vòng lặp

Trong bối cảnh mạng SD-WAN doanh nghiệp, AI/ML được tích hợp vào các giai đoạn của MAPE-K như sau: ở giai đoạn Monitor, AI hỗ trợ xử lý và chuẩn hóa lượng lớn dữ liệu telemetry từ nhiều thiết bị Edge; ở giai đoạn Analyze, các mô hình học máy thực hiện phát hiện bất thường và dự đoán sự cố thay vì chỉ so sánh với ngưỡng tĩnh; ở giai đoạn Plan, học tăng cường hoặc các thuật toán tối ưu hóa giúp lựa chọn hành động khắc phục tối ưu; ở giai đoạn Execute, cơ chế tự động hóa (automation/orchestration) triển khai hành động mà không cần thao tác thủ công [15][9].

---

## 2.4. Trí tuệ nhân tạo và học máy trong phát hiện – dự đoán sự cố mạng

### 2.4.1. Phát hiện bất thường (Anomaly Detection)

Phát hiện bất thường là kỹ thuật xác định các mẫu dữ liệu (traffic, hiệu năng, log) lệch khỏi hành vi bình thường của hệ thống, thường sử dụng học không giám sát (unsupervised learning) khi dữ liệu gán nhãn sự cố khan hiếm, hoặc các phương pháp thống kê để mô hình hóa phân phối "bình thường" của các chỉ số mạng và gắn cờ khi có độ lệch lớn [15]. Trong lĩnh vực self-healing network, một số nghiên cứu đã ứng dụng thuật toán Isolation Forest và các mô hình tương tự để phát hiện lỗi tự động trong mạng cảm biến không dây (WSN) [11].

### 2.4.2. Dự đoán sự cố (Predictive Failure Analytics)

Khác với phát hiện bất thường (xử lý phản ứng khi sự cố đã/đang xảy ra), dự đoán sự cố hướng tới việc nhận diện nguy cơ trước khi downtime xảy ra, thường dùng học có giám sát (supervised learning) trên dữ liệu lịch sử có gán nhãn, hoặc các mô hình chuỗi thời gian (time-series forecasting) như LSTM (Long Short-Term Memory) để dự báo xu hướng suy giảm hiệu năng đường truyền [16]. Nghiên cứu "Intelligent Fault Detection and Self-Healing Mechanisms" công bố trên MDPI (2025) đã áp dụng thuật toán Light Gradient Boosting Machine (LGBM) — được đánh giá có độ chính xác, khả năng mở rộng và hiệu quả cao khi xử lý tập dữ liệu lớn — để phát hiện lỗi trong mạng cảm biến không dây, kết hợp với thuật toán tối ưu hóa Flying Fox Optimization Algorithm (FFOA) nhằm tối ưu hóa chiến lược khôi phục như định tuyến lại lưu lượng hoặc thay thế node lỗi [11].

### 2.4.3. Học tăng cường (Reinforcement Learning) trong ra quyết định khôi phục tự động

Học tăng cường phù hợp với bài toán ra quyết định khôi phục sự cố vì bản chất bài toán là một chuỗi quyết định tuần tự (sequential decision-making) trong môi trường không chắc chắn: agent (bộ điều khiển tự phục hồi) quan sát trạng thái mạng, chọn hành động khắc phục (ví dụ chuyển kênh, định tuyến lại), nhận phản hồi (reward) dựa trên hiệu quả của hành động, từ đó dần tối ưu hóa chính sách ra quyết định theo thời gian. Nghiên cứu của Liu, Gao và Fan (2020) đã áp dụng học tăng cường cho bài toán phát hiện và khôi phục lỗi trong mạng tự phục hồi, cho thấy tiềm năng của phương pháp này trong việc tự động hóa toàn bộ quy trình xử lý sự cố mà không cần định nghĩa trước tập luật cứng [17].

### 2.4.4. Một số mô hình/thuật toán tiêu biểu

Tổng hợp từ các nghiên cứu liên quan, một số nhóm thuật toán thường được ứng dụng trong self-healing network gồm: (i) các mô hình cây quyết định và ensemble learning (Random Forest, LightGBM) cho bài toán phân loại/dự đoán lỗi với độ chính xác cao trên dữ liệu dạng bảng [11]; (ii) mạng nơ-ron nhân tạo (Artificial Neural Network) và các biến thể sâu hơn cho bài toán phát hiện và khôi phục lỗi phức tạp [18]; (iii) mô hình chuỗi thời gian (LSTM) cho dự báo xu hướng suy giảm hiệu năng trước khi xảy ra sự cố [16]; (iv) học tăng cường cho bài toán ra quyết định hành động khắc phục tối ưu [17].

---

## 2.5. AIOps và tự động hóa vận hành mạng (Network AIOps)

### 2.5.1. Khái niệm AIOps

AIOps (Artificial Intelligence for IT Operations) là thuật ngữ do Gartner đưa ra lần đầu năm 2016, chỉ việc kết hợp dữ liệu lớn (big data) và học máy để tự động hóa các quy trình vận hành CNTT, bao gồm tương quan sự kiện (event correlation), phát hiện bất thường (anomaly detection) và xác định nguyên nhân gốc rễ (causality determination/root cause analysis) [8][19]. Theo Gartner, AIOps chính là sự kết hợp giữa big data và ML nhằm tạo ra các kết quả dự đoán, từ đó giúp đẩy nhanh quá trình phân tích nguyên nhân gốc rễ và rút ngắn thời gian khôi phục trung bình (MTTR) [8]. Trong lĩnh vực vận hành mạng nói riêng (Network AIOps/NetOps automation), AIOps giúp chuyển đổi mô hình vận hành từ "phản ứng" (reactive — xử lý sau khi sự cố được báo cáo) sang "chủ động/dự đoán" (proactive/predictive) [19].

### 2.5.2. Ví dụ ứng dụng thực tế trong các nền tảng SD-WAN thương mại

Một số nhà cung cấp SD-WAN hàng đầu đã tích hợp AIOps vào sản phẩm thương mại: Juniper Networks phát triển nền tảng **Mist AI** tích hợp trực tiếp vào SD-WAN, cung cấp khả năng phân tích dự đoán và tự động xác định, khắc phục vấn đề mạng thông qua điều chỉnh cấu hình và định tuyến lại lưu lượng khi phát hiện sự cố [9]. Tương tự, **Aruba AIOps** (thuộc HPE) sử dụng các mô hình học máy để giám sát chủ động và dự đoán các nguy cơ hỏng hóc, đặc biệt hiệu quả trong môi trường mạng không dây quy mô lớn [9]. Palo Alto Networks cũng nhấn mạnh rằng khi AI/ML được nhúng vào SD-WAN, mạng trở nên "thông minh hơn" nhờ khả năng xử lý dữ liệu quy mô lớn và hiểu sâu hơn về hiệu năng mạng/ứng dụng, từ đó tạo thành một mạng tự phục hồi, tự vận hành (self-healing, self-driving network) [4].

---

## 2.6. Các công trình nghiên cứu liên quan (Related Work)

Bảng dưới đây tổng hợp một số công trình nghiên cứu tiêu biểu liên quan trực tiếp đến đề tài, làm cơ sở xác định khoảng trống nghiên cứu:

| STT | Công trình | Trọng tâm | Phương pháp | Hạn chế/Khoảng trống |
|---|---|---|---|---|
| 1 | Xiao, Zhou & Wang (2018) [20] | Phát hiện và khôi phục lỗi trong mạng tự phục hồi | AI nói chung | Chưa tập trung cụ thể vào kiến trúc SD-WAN doanh nghiệp |
| 2 | Liu, Gao & Fan (2020) [17] | Phát hiện và khôi phục lỗi | Học tăng cường (Reinforcement Learning) | Thử nghiệm ở quy mô hạn chế, chưa đánh giá trên mô hình nhiều chi nhánh |
| 3 | Zhang, Wang & Yang (2021) [21] | Phát hiện và khôi phục lỗi | Machine Learning nói chung | Chưa đề cập đến chỉ số MTTD/MTTR cụ thể trong bối cảnh WAN |
| 4 | MDPI (2025) [11] | Phát hiện lỗi và tự phục hồi trong WSN | LightGBM + Flying Fox Optimization | Áp dụng cho mạng cảm biến không dây (WSN), không phải mạng WAN doanh nghiệp |
| 5 | Perumallaplli (2025) [15] | Kiến trúc AI lai cho quản lý lỗi mạng | Kết hợp nhiều kỹ thuật AI (hybrid) | Mang tính khảo sát/đề xuất kiến trúc tổng quát, chưa triển khai thực nghiệm cụ thể trên SD-WAN |
| 6 | arXiv, MAPE-K cho ứng dụng web (2026) [14] | Tự phục hồi ở tầng ứng dụng | MAPE-K + AutoFix | Áp dụng ở tầng ứng dụng web, không phải tầng mạng WAN |

Qua tổng hợp trên có thể thấy: các nghiên cứu hiện có hoặc tập trung vào khía cạnh thuật toán AI một cách tổng quát (không gắn với kiến trúc SD-WAN cụ thể), hoặc áp dụng cho các lĩnh vực lân cận như WSN, mạng di động, ứng dụng web, ứng dụng đám mây, chưa có nhiều công trình xây dựng và đánh giá thực nghiệm một mô hình tích hợp đầy đủ giữa kiến trúc SD-WAN doanh nghiệp nhiều chi nhánh với vòng lặp khôi phục sự cố thông minh dựa trên MAPE-K, đo lường cụ thể trên các chỉ số MTTD/MTTR/Availability. Đây chính là khoảng trống mà đề tài hướng tới giải quyết.

---

## 2.7. Khung lý thuyết đề xuất cho đề tài

Từ các nội dung lý thuyết đã trình bày, đề tài đề xuất một khung tham chiếu (conceptual framework) làm nền tảng cho việc thiết kế mô hình ở Chương III, gồm ba lớp chính:

1. **Lớp hạ tầng SD-WAN**: đóng vai trò "sensor" và "effector" — vừa cung cấp dữ liệu giám sát liên tục về trạng thái các đường truyền (mục 2.1, 2.2), vừa là nơi thực thi các hành động khôi phục (chuyển kênh, định tuyến lại) theo lệnh từ lớp điều khiển thông minh.
2. **Lớp điều khiển tự phục hồi (Self-Healing Controller)**: được thiết kế dựa trên vòng lặp MAPE-K (mục 2.3), trong đó giai đoạn Analyze và Plan được "thông minh hóa" bằng các mô hình AI/ML phù hợp (anomaly detection, predictive analytics, và/hoặc reinforcement learning) đã khảo sát ở mục 2.4.
3. **Lớp AIOps/giám sát – đánh giá**: cung cấp bảng điều khiển (dashboard) theo dõi các chỉ số MTTD, MTTR, tỷ lệ mất gói và độ khả dụng dịch vụ (mục 2.2, 2.5), làm cơ sở đánh giá hiệu quả mô hình so với cơ chế SD-WAN truyền thống ở Chương IV.

Khung lý thuyết này sẽ được cụ thể hóa thành sơ đồ kiến trúc, luồng xử lý dữ liệu và lựa chọn công nghệ/thuật toán triển khai chi tiết trong Chương III của đề tài.

---

## TÀI LIỆU THAM KHẢO

[1] So sánh SD-WAN và MPLS: Cập nhật xu hướng kết nối doanh nghiệp mới nhất 2025. MSP Vietnam, 2025. https://www.mspvn.com/so-sanh-sd-wan-va-mpls-cap-nhat-xu-huong-2025/

[2] SD-WAN là gì? Giải pháp mạng doanh nghiệp thời đại Cloud & Hybrid Work. VNPro Forum, 2026. https://www.forum.vnpro.org/forum/ccna%C2%AE/ccna-200-301/438857

[3] VNPT SD-Wan - Giải pháp nâng cao hiệu quả sử dụng các kênh truyền dẫn cho Doanh nghiệp. VNPT TP.HCM, 2025. https://vnpttphcm.com.vn/dich-vu-vnpt-sd-wan

[4] Why Machine Learning (ML) and Artificial Intelligence (AI) Are Key Technologies for SD-WAN. Palo Alto Networks – Cyberpedia. https://www.paloaltonetworks.com/cyberpedia/why-ml-and-ai-are-key-technologies-for-sd-wan

[5] SD-WAN đạt chuẩn MEF SASE 3.0 - Giải pháp tối ưu cho doanh nghiệp. CMC Telecom, 04/2025. https://cmctelecom.vn/bai-viet/sd-wan-dat-chuan-mef-sase-3-0-giai-phap-toi-uu-cho-doanh-nghiep/

[6] SD-WAN đạt chuẩn MEF SASE 3.0. CMC Telecom, 04/2025. (như trên, mục chứng chỉ MEF SASE 3.0)

[7] SD-WAN Statistics 2026: Trends in Software-Defined Networking (trích dẫn dự báo Gartner về SASE). TWC IT Solutions, 2024–2026. https://twc-it-solutions.com/blog/industry-statistics/sd-wan-statistics/

[8] Gartner on AIOps: A Complete Guide (trích định nghĩa AIOps của Gartner). Aisera, 2025. https://aisera.com/blog/gartner-on-aiops-the-complete-guide/ ; xem thêm ScienceLogic, "What is AIOps?". https://sciencelogic.com/product/resources/what-is-aiops

[9] Self-Healing Networks: The Future of Autonomous Networking. SolveForce Unified Intelligence. https://solveforce.com/self-healing-networks-the-future-of-autonomous-networking/

[10] TinyAC: Bringing Autonomic Computing Principles to Resource-Constrained Systems. arXiv, 2025. https://arxiv.org/pdf/2509.19350

[11] Intelligent Fault Detection and Self-Healing Mechanisms in Wireless Sensor Networks Using Machine Learning and Flying Fox Optimization. MDPI, 06/2025. https://www.mdpi.com/2073-431X/14/6/233

[12] Using Models at Runtime to Address Assurance for Self-Adaptive Systems (trích dẫn Kephart & Chess, 2003). arXiv. https://arxiv.org/pdf/1505.00903

[13] The MAPE-K self-adaptive cycle as proposed by IBM. ResearchGate. https://www.researchgate.net/figure/The-MAPE-K-self-adaptive-cycle-as-proposed-by-IBM-23_fig2_220106130

[14] When Web Apps Heal Themselves: A MAPE-K Based Approach to Fault Tolerance and Adaptive Recovery. arXiv, 2026. https://arxiv.org/pdf/2605.19261

[15] Perumallaplli, R. Self-Healing Networks: An AI Approach to Network Fault Management. SSRN, 05/2025. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5228591

[16] AIOps Explained: Detection, Prediction, and Mitigation in IT Operations (trích dẫn ứng dụng LSTM trong dự đoán sự cố). Splunk. https://www.splunk.com/en_us/blog/learn/aiops.html

[17] Liu, K., Gao, C., Fan, Z. (2020). Fault Detection and Recovery in Self-Healing Networks Using Reinforcement Learning. 2020 IEEE 4th Information Technology and Mechatronics Engineering Conference (ITOEC), pp. 293-298. (trích trong: Self-Healing Networks: AI-Based Approaches for Fault Detection and Recovery, ResearchGate, 02/2024). https://www.researchgate.net/publication/378517886

[18] Self-Healing Networks: Implementing AI-Powered Mechanisms to Automatically Detect and Resolve Network Issues with Minimal Human Intervention (tổng hợp các nghiên cứu về mạng nơ-ron nhân tạo trong self-healing network). ResearchGate, 02/2025. https://www.researchgate.net/publication/388927201

[19] What Is AIOps? Artificial Intelligence for IT Operations. Cisco. https://www.cisco.com/site/us/en/learn/topics/artificial-intelligence/what-is-aiops.html

[20] Xiao, L., Zhou, W., Wang, Z. (2018). Research on Fault Detection and Recovery of Self-healing Network Based on Artificial Intelligence. 2018 15th ICCWAMTIP, pp. 174-177. (trích trong: Self-Healing Networks: AI-Based Approaches, ResearchGate, 02/2024). https://www.researchgate.net/publication/378517886

[21] Zhang, H., Wang, Y., Yang, H. (2021). Fault Detection and Recovery for Self-Healing Network Based on Machine Learning. 2021 ICMCR. (trích trong: Self-Healing Networks: AI-Based Approaches, ResearchGate, 02/2024). https://www.researchgate.net/publication/378517886

---

*Ghi chú: Các tài liệu [12], [13], [14] cung cấp nền tảng lý thuyết cốt lõi cho mô hình MAPE-K sẽ được sử dụng làm khung thiết kế kiến trúc ở Chương III. Các tài liệu [11], [15], [17], [20], [21] là các nghiên cứu thực nghiệm về thuật toán AI/ML trong self-healing network, cần được đọc kỹ hơn để lựa chọn thuật toán cụ thể áp dụng cho mô hình đề xuất.*
