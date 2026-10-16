# CHƯƠNG I: MỞ ĐẦU VÀ TỔNG QUAN ĐỀ TÀI

## Đề tài: MẠNG DOANH NGHIỆP TỰ PHỤC HỒI SỬ DỤNG SD-WAN VÀ CƠ CHẾ KHÔI PHỤC SỰ CỐ THÔNG MINH

---

## 1.1. Lý do chọn đề tài

Trong bối cảnh chuyển đổi số diễn ra mạnh mẽ, hạ tầng mạng diện rộng (WAN) truyền thống dựa trên MPLS đang bộc lộ nhiều hạn chế khi doanh nghiệp dịch chuyển khối lượng ứng dụng và dữ liệu lên môi trường đa đám mây (multi-cloud). Kiến trúc MPLS tuy có độ ổn định và độ trễ thấp nhưng lại có chi phí thuê kênh cao, thời gian triển khai chậm, kém linh hoạt khi mở rộng chi nhánh, và không tối ưu cho việc truy cập trực tiếp vào các ứng dụng cloud vì lưu lượng thường phải đi vòng qua trung tâm dữ liệu trung tâm [1][2]. Đây chính là động lực khiến Software-Defined Wide Area Network (SD-WAN) — kiến trúc mạng WAN được quản trị và điều phối bằng phần mềm, tách biệt control plane và data plane — trở thành xu hướng hạ tầng mạng doanh nghiệp được ưu tiên hàng đầu hiện nay [3][2].

Thực tế thị trường cho thấy tốc độ tăng trưởng của SD-WAN là rất đáng chú ý. Theo báo cáo "SD-WAN Market Report 2026" của ResearchAndMarkets công bố tháng 4/2026, quy mô thị trường SD-WAN toàn cầu được dự báo tăng từ 9,17 tỷ USD năm 2025 lên 12,03 tỷ USD năm 2026, đạt tốc độ tăng trưởng kép hàng năm (CAGR) khoảng 31,2%, và có thể chạm mốc 35,39 tỷ USD vào năm 2030, trong đó các xu hướng nổi bật gồm tối ưu hóa dựa trên AI, triển khai hybrid và công nghệ bảo mật hậu lượng tử [4]. Gartner cũng dự báo rằng đến năm 2026, khoảng 60% các thương vụ mua sắm SD-WAN mới sẽ được tích hợp vào một nền tảng SASE (Secure Access Service Edge) đơn nhà cung cấp, tăng mạnh so với tỷ lệ 15% của năm 2022 [5]. Tại Việt Nam, các nhà mạng lớn như Viettel (với dịch vụ V-WAN) và VNPT đã và đang cung cấp dịch vụ SD-WAN thương mại cho nhiều tổ chức có mạng lưới chi nhánh rộng như ngành điện lực, ngân hàng; nhiều doanh nghiệp lớn như Vinamilk, BIDV, SHB, MSB, AIA... cũng đã nghiên cứu và có xu hướng chuyển dịch sang SD-WAN [6][7].

Tuy nhiên, bản thân SD-WAN chỉ giải quyết được bài toán về định tuyến thông minh, cân bằng tải và chuyển đổi kênh truyền dự phòng (failover) ở mức cơ bản theo các chính sách được cấu hình sẵn; việc phát hiện, chẩn đoán và xử lý sự cố trong nhiều giải pháp hiện nay vẫn phụ thuộc phần lớn vào các ngưỡng cảnh báo tĩnh và sự can thiệp thủ công của đội ngũ vận hành mạng (NOC). Trong khi đó, chi phí của việc gián đoạn dịch vụ mạng (downtime) đối với doanh nghiệp là cực kỳ lớn. Theo khảo sát "Hourly Cost of Downtime" của ITIC giai đoạn 2024–2025, hơn 90% doanh nghiệp quy mô vừa và lớn báo cáo thiệt hại vượt 300.000 USD cho mỗi giờ ngừng hoạt động, trong đó 41% doanh nghiệp chịu thiệt hại từ 1 đến 5 triệu USD mỗi giờ [8]. Báo cáo "Observability Forecast 2025" của New Relic, khảo sát hơn 1.700 chuyên gia CNTT tại 23 quốc gia, cũng chỉ ra rằng các sự cố nghiêm trọng (high-impact outages) có chi phí trung vị lên tới 2 triệu USD mỗi giờ, tương đương khoảng 33.333 USD mỗi phút, với tổng thiệt hại trung vị hàng năm đạt 76 triệu USD cho mỗi doanh nghiệp [9]. Báo cáo "Hidden Costs of Downtime 2026" do Splunk và Cisco phối hợp thực hiện ước tính trung bình mỗi tổ chức thiệt hại khoảng 300 triệu USD doanh thu mỗi năm chỉ riêng từ các sự cố ngừng hoạt động ngoài kế hoạch [10]. Những con số này cho thấy thời gian phát hiện sự cố (Mean Time To Detect – MTTD) và thời gian khôi phục sự cố (Mean Time To Recover – MTTR) là hai chỉ số sống còn quyết định năng lực vận hành liên tục của doanh nghiệp.

Đây chính là lý do các nhà cung cấp giải pháp mạng hàng đầu đang tích hợp trí tuệ nhân tạo (AI) và học máy (Machine Learning) vào nền tảng SD-WAN nhằm xây dựng "mạng tự phục hồi" (self-healing network) — hệ thống có khả năng tự động phát hiện bất thường, dự đoán nguy cơ sự cố, và tự đưa ra hành động khắc phục mà không cần hoặc chỉ cần rất ít sự can thiệp của con người. Palo Alto Networks nhận định rằng sự kết hợp giữa tự động hóa, machine learning và AI tạo nên một mạng tự phục hồi, tự vận hành, có khả năng giám sát, phân tích, điều chỉnh và tự sửa lỗi với sự can thiệp tối thiểu từ con người [11]. Trên thực tế, Juniper Networks đã tích hợp nền tảng Mist AI vào SD-WAN để cung cấp khả năng dự đoán và tự phục hồi, tự động định tuyến lại lưu lượng khi phát hiện sự cố; tương tự, Aruba (HPE) cũng phát triển AIOps nhằm giám sát chủ động và dự đoán lỗi trước khi xảy ra downtime [12]. Nhiều công trình nghiên cứu học thuật gần đây cũng tập trung khai thác các kỹ thuật AI như học tăng cường (Reinforcement Learning), mạng nơ-ron nhân tạo và các thuật toán tối ưu hóa metaheuristic để nâng cao độ chính xác phát hiện lỗi và rút ngắn thời gian khôi phục trong mạng tự phục hồi [13][14].

Xuất phát từ khoảng cách giữa (i) tiềm năng linh hoạt của kiến trúc SD-WAN, (ii) thiệt hại nặng nề mà downtime gây ra cho hoạt động kinh doanh, và (iii) xu hướng ứng dụng AI để tự động hóa việc phát hiện – chẩn đoán – khôi phục sự cố mạng, đề tài "Mạng doanh nghiệp tự phục hồi sử dụng SD-WAN và cơ chế khôi phục sự cố thông minh" được lựa chọn nhằm nghiên cứu, thiết kế và thử nghiệm một mô hình mạng doanh nghiệp có khả năng tự giám sát, tự chẩn đoán và tự khôi phục khi xảy ra sự cố đường truyền, qua đó góp phần nâng cao tính sẵn sàng (availability) và độ tin cậy (reliability) của hạ tầng mạng hiện đại.

---

## 1.2. Mục tiêu thực hiện đề tài

**Mục tiêu tổng quát:** Nghiên cứu, xây dựng và đánh giá một mô hình mạng doanh nghiệp tự phục hồi (self-healing enterprise network) trên nền tảng SD-WAN, tích hợp cơ chế giám sát và khôi phục sự cố thông minh, nhằm giảm thiểu thời gian phát hiện và xử lý sự cố, đảm bảo tính liên tục trong hoạt động của hệ thống mạng doanh nghiệp.

**Mục tiêu cụ thể:**

- Nghiên cứu kiến trúc, nguyên lý hoạt động của SD-WAN (tách control plane – data plane, orchestration tập trung, định tuyến theo ứng dụng, chuyển đổi kênh truyền động) và các cơ chế bảo đảm dự phòng, cân bằng tải hiện có của công nghệ này [1][3].
- Khảo sát và hệ thống hóa các phương pháp phát hiện bất thường và dự đoán sự cố mạng dựa trên AI/Machine Learning (học có giám sát, học không giám sát, học tăng cường) đã được công bố trong các nghiên cứu liên quan [13][14][15].
- Thiết kế cơ chế khôi phục sự cố thông minh (intelligent incident recovery) có khả năng: (i) phát hiện sớm bất thường về hiệu năng đường truyền (độ trễ, mất gói, jitter); (ii) tự động phân loại và chẩn đoán nguyên nhân sự cố; (iii) tự động kích hoạt hành động khắc phục (chuyển hướng lưu lượng, chuyển đổi kênh dự phòng, điều chỉnh chính sách định tuyến) mà không cần can thiệp thủ công.
- Xây dựng mô hình thử nghiệm (mô phỏng hoặc triển khai thực nghiệm trên nền tảng ảo hóa) để đo lường các chỉ số hiệu năng cốt lõi: thời gian phát hiện sự cố (MTTD), thời gian khôi phục (MTTR/failover time), tỷ lệ mất gói và độ khả dụng của dịch vụ trước và sau khi áp dụng cơ chế tự phục hồi.
- Đánh giá hiệu quả của mô hình đề xuất so với cơ chế SD-WAN truyền thống (dựa trên ngưỡng tĩnh, không có yếu tố AI), từ đó đề xuất khuyến nghị áp dụng thực tế cho doanh nghiệp.

---

## 1.3. Đối tượng nghiên cứu

Đối tượng nghiên cứu của đề tài bao gồm:

- **Công nghệ SD-WAN**: kiến trúc, thành phần (SD-WAN Edge, SD-WAN Controller/Orchestrator, Gateway), cơ chế định tuyến động, chính sách QoS theo ứng dụng, và khả năng tích hợp bảo mật (SASE) [3][16].
- **Cơ chế khôi phục sự cố thông minh**: các thuật toán và mô hình AI/Machine Learning phục vụ phát hiện bất thường (anomaly detection), dự đoán lỗi (predictive failure analytics) và tự động hóa hành động khắc phục (automated remediation), bao gồm các kỹ thuật học máy giám sát/không giám sát, mạng nơ-ron, học tăng cường đã được ứng dụng trong các nghiên cứu về mạng tự phục hồi [13][14][15][17].
- **Hạ tầng mạng doanh nghiệp nhiều chi nhánh (multi-branch enterprise network)**: mô hình mạng có trụ sở chính (Headquarter/Data Center) kết nối với nhiều chi nhánh và các nền tảng đám mây thông qua nhiều kênh truyền song song (Internet băng rộng, MPLS, LTE/5G).
- **Các nền tảng, công cụ mô phỏng/thử nghiệm** phục vụ xây dựng mô hình: phần mềm SD-WAN mã nguồn mở hoặc thương mại, môi trường ảo hóa mạng (ví dụ GNS3, EVE-NG, hoặc nền tảng cloud lab), công cụ giám sát hiệu năng mạng và công cụ xử lý/huấn luyện mô hình học máy.

---

## 1.4. Phạm vi nghiên cứu

Do giới hạn về thời gian, nguồn lực và quy mô của một đề tài nghiên cứu, phạm vi thực hiện được giới hạn như sau:

- **Về không gian**: Đề tài tập trung xây dựng và thử nghiệm mô hình trong môi trường mô phỏng/ảo hóa mô phỏng một mạng doanh nghiệp cỡ vừa gồm trụ sở chính và một số chi nhánh kết nối qua SD-WAN, không triển khai trên toàn bộ hạ tầng mạng diện rộng của một doanh nghiệp thực tế cụ thể.
- **Về kỹ thuật**: Đề tài tập trung vào lớp mạng WAN (định tuyến, chuyển mạch kênh truyền, giám sát hiệu năng đường truyền) và cơ chế phát hiện – khôi phục sự cố liên quan đến kết nối WAN (mất kết nối, suy giảm chất lượng đường truyền, nghẽn băng thông); đề tài không đi sâu vào các vấn đề bảo mật chuyên sâu (như phân tích mã độc, kiểm thử xâm nhập) hay các lớp mạng LAN/ứng dụng nội bộ.
- **Về mô hình AI**: Đề tài sử dụng các thuật toán học máy đã được kiểm chứng trong các nghiên cứu liên quan (ví dụ mô hình phân loại bất thường, hồi quy dự đoán lỗi) để xây dựng cơ chế phát hiện và ra quyết định khôi phục; đề tài không đặt trọng tâm vào việc phát triển thuật toán học máy hoàn toàn mới mà tập trung vào việc ứng dụng, tích hợp và đánh giá hiệu quả trong bối cảnh mạng SD-WAN.
- **Về thời gian**: Đề tài được thực hiện trong khuôn khổ thời gian của học phần/khóa luận, do đó dữ liệu thử nghiệm chủ yếu được thu thập từ môi trường mô phỏng và một số kịch bản sự cố được chủ động tạo ra (fault injection) thay vì giám sát dài hạn trên hệ thống sản xuất thực tế.

---

## 1.5. Ý nghĩa thực tiễn của đề tài

**Về mặt kinh tế:** Kết quả nghiên cứu góp phần cung cấp cơ sở kỹ thuật để doanh nghiệp giảm thiểu thiệt hại do downtime — vốn được ước tính có thể lên tới hàng trăm nghìn đến hàng triệu USD mỗi giờ đối với doanh nghiệp quy mô vừa và lớn theo các khảo sát của ITIC và New Relic [8][9]. Việc rút ngắn MTTD và MTTR thông qua cơ chế tự động hóa không chỉ giảm chi phí vận hành (nhân sự trực NOC 24/7, chi phí xử lý sự cố thủ công) mà còn giảm thiểu doanh thu bị mất do gián đoạn dịch vụ, đặc biệt quan trọng với các ngành có yêu cầu vận hành liên tục như tài chính – ngân hàng, bán lẻ, sản xuất và thương mại điện tử [7].

**Về mặt kỹ thuật – vận hành:** Đề tài cung cấp một mô hình tham khảo giúp đội ngũ kỹ thuật mạng hiểu rõ hơn cách kết hợp giữa hạ tầng SD-WAN sẵn có và các kỹ thuật AI để chuyển đổi cách vận hành mạng từ mô hình phản ứng (reactive – xử lý sự cố sau khi xảy ra và được báo cáo) sang mô hình chủ động/dự đoán (proactive/predictive), qua đó nâng cao tính sẵn sàng cao (high availability) của hệ thống mà không cần đầu tư quá lớn vào hạ tầng phần cứng dự phòng truyền thống.

**Về mặt chiến lược chuyển đổi số:** Trong bối cảnh doanh nghiệp Việt Nam đang đẩy mạnh dịch chuyển lên đa đám mây và mô hình làm việc kết hợp (hybrid work), hạ tầng mạng WAN đóng vai trò "xương sống" quyết định sự ổn định của toàn bộ hệ thống công nghệ thông tin [7]. Đề tài góp phần cung cấp luận cứ kỹ thuật hỗ trợ các doanh nghiệp — đặc biệt là doanh nghiệp vừa và nhỏ chưa đủ nguồn lực để thuê các dịch vụ SD-WAN có AIOps thương mại đắt đỏ — có thêm phương án tham khảo để từng bước xây dựng năng lực tự giám sát và tự phục hồi cho hạ tầng mạng của mình.

**Về mặt học thuật:** Đề tài góp phần hệ thống hóa và kiểm chứng thực nghiệm các phương pháp AI ứng dụng trong lĩnh vực mạng tự phục hồi (self-healing network) vốn đang là hướng nghiên cứu được quan tâm rộng rãi trong cộng đồng khoa học mạng những năm gần đây [13][14][15][17], đồng thời là tài liệu tham khảo cho các nghiên cứu tiếp theo về tự động hóa vận hành mạng (Network AIOps) tại Việt Nam.

---

## TÀI LIỆU THAM KHẢO

[1] So sánh SD-WAN và MPLS: Cập nhật xu hướng kết nối doanh nghiệp mới nhất 2025. MSP Vietnam, 2025. https://www.mspvn.com/so-sanh-sd-wan-va-mpls-cap-nhat-xu-huong-2025/

[2] SD-WAN là gì? Giải pháp mạng doanh nghiệp thời đại Cloud & Hybrid Work. Vietnamese Professional Forum – VNPro, 2026. https://www.forum.vnpro.org/forum/ccna%C2%AE/ccna-200-301/438857

[3] Tại sao SD-WAN là ưu tiên của Doanh nghiệp khi bắt đầu chuyển đổi số? CMC Telecom, 2025. https://cmctelecom.vn/bai-viet/tai-sao-sd-wan-la-uu-tien-cua-doanh-nghiep-khi-bat-dau-chuyen-doi-so/

[4] Software-Defined Wide Area Network (SD-WAN) Market to Witness 31% CAGR Through 2026-2030. GlobeNewswire / ResearchAndMarkets, 04/2026. https://www.globenewswire.com/news-release/2026/04/01/3266492/

[5] SD-WAN Statistics 2026: Trends in Software-Defined Networking (trích dẫn dự báo của Gartner về SASE). TWC IT Solutions, 2024–2026. https://twc-it-solutions.com/blog/industry-statistics/sd-wan-statistics/

[6] Dịch vụ V-Wan và xu hướng triển khai kết nối mạng diện rộng tại Việt Nam. Điện Tử Ngày Nay, 2025. https://dientungaynay.vn/vien-thong/dich-vu-v-wan-va-xu-huong-trien-khai-ket-noi-mang-dien-rong-tai-viet-nam

[7] SD-WAN đạt chuẩn MEF SASE 3.0 - Giải pháp tối ưu cho doanh nghiệp. CMC Telecom, 04/2025. https://cmctelecom.vn/bai-viet/sd-wan-dat-chuan-mef-sase-3-0-giai-phap-toi-uu-cho-doanh-nghiep/

[8] What is the cost of Downtime in 2026? (trích dẫn khảo sát ITIC 2024 Hourly Cost of Downtime Survey). Dotcom-Monitor, 2026. https://www.dotcom-monitor.com/blog/what-is-the-cost-of-downtime/

[9] IT Downtime Cost Statistics: What Outages Cost in 2025 (trích dẫn New Relic 2025 Observability Forecast). Virima, 2025. https://virima.com/blog/it-downtime-cost-statistics-what-outages-actually-cost-in-2025

[10] Cost of downtime in 2026: $15,000 per minute (trích dẫn báo cáo Splunk/Cisco "Hidden Costs of Downtime 2026"). Gatling, 2026. https://gatling.io/blog/the-cost-of-downtime

[11] Why Machine Learning (ML) and Artificial Intelligence (AI) Are Key Technologies for SD-WAN. Palo Alto Networks – Cyberpedia. https://www.paloaltonetworks.com/cyberpedia/why-ml-and-ai-are-key-technologies-for-sd-wan

[12] Self-Healing Networks: The Future of Autonomous Networking. SolveForce Unified Intelligence. https://solveforce.com/self-healing-networks-the-future-of-autonomous-networking/

[13] Perumallaplli, R. Self-Healing Networks: An AI Approach to Network Fault Management. SSRN, 05/2025. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5228591

[14] Intelligent Fault Detection and Self-Healing Mechanisms in Wireless Sensor Networks Using Machine Learning and Flying Fox Optimization. MDPI, 06/2025. https://www.mdpi.com/2073-431X/14/6/233

[15] Self-Healing Networks: Implementing AI-Powered Mechanisms to Automatically Detect and Resolve Network Issues with Minimal Human Intervention. ResearchGate, 02/2025. https://www.researchgate.net/publication/388927201

[16] VNPT SD-Wan - Giải pháp nâng cao hiệu quả sử dụng các kênh truyền dẫn cho Doanh nghiệp. VNPT TP.HCM, 2025. https://vnpttphcm.com.vn/dich-vu-vnpt-sd-wan

[17] Self-Healing Cloud Infrastructure: Leveraging AI for Fault Detection and Recovery. Springer Nature Link. https://link.springer.com/chapter/10.1007/978-3-032-05373-2_3

---

*Ghi chú: Các tài liệu [4], [5], [8]–[10] là báo cáo thị trường/khảo sát ngành (industry report), phù hợp để trích dẫn cho các số liệu thực tiễn về quy mô thị trường SD-WAN và chi phí downtime; các tài liệu [13]–[15], [17] là các công trình nghiên cứu học thuật liên quan trực tiếp đến cơ chế AI cho mạng tự phục hồi, nên được ưu tiên tham khảo sâu hơn ở Chương II (Cơ sở lý thuyết) khi trình bày chi tiết các thuật toán.*
