# 14 KỊCH BẢN SỰ CỐ MẠNG — HỆ THỐNG TỰ PHỤC HỒI

> Mỗi kịch bản gồm:
> - **Sự cố:** Chuyện gì xảy ra với mạng
> - **Hệ thống phát hiện:** AI/hệ thống nhận ra điều gì bất thường
> - **Tự khắc phục:** Hệ thống tự làm gì để sửa
> - **Thời gian phục hồi (MTTR)**

---

## 🔴 NHÓM PHẢN ỨNG (F01 – F12) — Xử lý sau khi sự cố xảy ra

---

### F01 — Đứt cáp tầng Access (Nha Trang)

| | |
|:---|:---|
| **Sự cố** | Dây cáp nối switch phòng Kinh Doanh (SALES) bị đứt → 3 máy tính phòng Kinh Doanh mất mạng |
| **Hệ thống phát hiện** | Prometheus báo: cổng kết nối switch SALES không còn tín hiệu |
| **Tự khắc phục** | AI ra lệnh reset lại cổng đó → Switch tự tìm đường đi khác (dự phòng) → Máy tính kết nối lại |
| **MTTR** | **< 30 giây** _(so với thủ công: 15–30 phút)_ |

---

### F02 — Sập Router phân phối — Dự phòng VRRP (Nha Trang)

| | |
|:---|:---|
| **Sự cố** | Router chính (DIST01) bị sập → Nhiều phòng ban tại Nha Trang mất cổng kết nối ra ngoài |
| **Hệ thống phát hiện** | VRRP phát hiện router chính không còn gửi tín hiệu "tôi đang sống" sau 3 giây |
| **Tự khắc phục** | Router dự phòng (DIST02) tự động tiếp quản → Phát thông báo đến toàn mạng "Tôi thay thế DIST01" → Mạng chạy bình thường qua DIST02 |
| **MTTR** | **< 5 giây** _(so với thủ công: 5–10 phút)_ |

---

### F03 — Đứt kết nối giữa Bảo Lộc và HCM

| | |
|:---|:---|
| **Sự cố** | Đường kết nối trực tiếp Bảo Lộc ↔ HCM bị đứt → Gói tin không đi thẳng được nữa |
| **Hệ thống phát hiện** | Giao thức định tuyến OSPF báo: "Hàng xóm HCM không còn liên lạc được" |
| **Tự khắc phục** | OSPF tự tính đường vòng mới: Bảo Lộc → Nha Trang → HCM → AI điều hướng thêm: dữ liệu nặng (backup) đi Internet, VoIP đi đường vòng |
| **MTTR** | **< 40 giây** _(so với thủ công: 2–5 phút)_ |

---

### F04 — Đứt đường WAN chính MPLS

| | |
|:---|:---|
| **Sự cố** | Kênh truyền MPLS (đường WAN chính, nhanh nhất) bị đứt hoàn toàn → Cuộc gọi VoIP mất tiếng, ứng dụng ERP/DB bị đứt |
| **Hệ thống phát hiện** | SD-WAN gửi 3 gói thăm dò qua MPLS → Không nhận được phản hồi → Xác nhận đứt |
| **Tự khắc phục** | Hệ thống tự chọn đường tốt nhất còn lại (5G, delay 15ms) → Chuyển toàn bộ VoIP và Database sang 5G → Chuyển Web sang Internet |
| **MTTR** | **< 5 giây** _(so với thủ công: 10–30 phút)_ |

---

### F05 — Mất kênh Internet

| | |
|:---|:---|
| **Sự cố** | Đường Internet bị mất → Không vào được web, dịch vụ Cloud bị gián đoạn |
| **Hệ thống phát hiện** | SD-WAN phát hiện kênh Internet không phản hồi |
| **Tự khắc phục** | Chuyển traffic Web/Cloud sang kênh **5G** (ưu tiên 1) → nếu 5G không đủ thì sang **LTE** (ưu tiên 2) |
| **MTTR** | **< 5 giây** |

---

### F06 — Mất đường LTE

| | |
|:---|:---|
| **Sự cố** | Đường LTE (di động dự phòng) bị mất sóng hoặc lỗi SIM |
| **Hệ thống phát hiện** | SD-WAN phát hiện LTE không phản hồi |
| **Tự khắc phục** | Chuyển toàn bộ traffic đang đi qua LTE → sang **5G** |
| **MTTR** | **< 5 giây** _(LTE chỉ là đường backup nhỏ, tác động ít)_ |

---

### F07 — Đường 5G bị nhiễu, chất lượng kém

| | |
|:---|:---|
| **Sự cố** | Đường 5G vẫn còn kết nối nhưng bị nhiễu → Tỉ lệ mất gói vượt 5% → VoIP/video bị giật, vỡ tiếng |
| **Hệ thống phát hiện** | SD-WAN đo: tỉ lệ mất gói trên 5G = 6% → Vượt ngưỡng cho phép (5%) |
| **Tự khắc phục** | Chuyển VoIP và Database (nhạy cảm nhất) → sang **MPLS** (chất lượng tốt hơn) → Tiếp tục theo dõi 5G, khi ổn sẽ chuyển lại |
| **MTTR** | **< 5 giây** |

---

### F08 — Sập kênh VPN

| | |
|:---|:---|
| **Sự cố** | Đường VPN mã hóa bị sập → Dữ liệu bảo mật (backup được mã hóa) bị gián đoạn |
| **Hệ thống phát hiện** | SD-WAN phát hiện VPN tunnel không còn hoạt động |
| **Tự khắc phục** | Chuyển dữ liệu sang **MPLS** → Gửi cảnh báo cho kỹ sư NOC (vì liên quan dữ liệu nhạy cảm) → Hệ thống tự thử kết nối lại VPN |
| **MTTR** | **< 5 giây** _(kỹ sư được cảnh báo để giám sát thêm)_ |

---

### F09 — Tắc nghẽn băng thông MPLS

| | |
|:---|:---|
| **Sự cố** | Đường MPLS vẫn còn hoạt động nhưng bị quá tải (dùng tới 88%) → Cuộc gọi VoIP bị giật, điểm chất lượng (MOS) giảm xuống 2.8/5.0 (dưới mức SLA 3.5) |
| **Hệ thống phát hiện** | Prometheus báo: băng thông MPLS đạt 88%, jitter tăng từ 5ms lên 40ms, điểm chất lượng thoại giảm |
| **Tự khắc phục** | Chuyển các luồng ít quan trọng (tải file, backup) → sang Internet/VPN để giải phóng MPLS → Tăng ưu tiên cho VoIP và ERP trên MPLS → Băng thông giảm từ 88% về 55%, MOS phục hồi lên 4.1 |
| **MTTR** | **< 10 giây** |

---

### F10 — Chất lượng cuộc gọi VoIP giảm dần

| | |
|:---|:---|
| **Sự cố** | Đường truyền không đứt, nhưng jitter tăng từ từ → Chất lượng cuộc gọi đang xấu dần (MOS: 4.2 → 3.6 → 3.2) → Sắp dưới ngưỡng SLA (3.5) |
| **Hệ thống phát hiện** | Mô hình QoE tính điểm chất lượng thoại liên tục và phát hiện điểm MOS đang giảm về gần ngưỡng 3.5 |
| **Tự khắc phục** | Khi MOS = 3.2: Chuyển luồng RTP của cuộc gọi đang diễn ra từ MPLS → 5G (jitter chỉ 3ms) → **Cuộc gọi không bị cắt, người dùng không nghe thấy gì** |
| **MTTR** | **0 giây** _(người dùng không cảm nhận được sự cố)_ |

---

### F11 — Web Server bị sập

| | |
|:---|:---|
| **Sự cố** | Web Server chính (WEB01) tại Data Center bị sập → Người dùng không vào được website |
| **Hệ thống phát hiện** | HAProxy gửi yêu cầu kiểm tra sức khỏe tới WEB01 mỗi 2 giây → 3 lần liên tiếp không nhận được phản hồi |
| **Tự khắc phục** | HAProxy tự loại WEB01 khỏi danh sách → Chuyển toàn bộ request người dùng → **WEB02** (server dự phòng) → Địa chỉ web vẫn như cũ, người dùng không biết |
| **MTTR** | **< 5 giây** |

---

### F12 — Nhiều sự cố xảy ra cùng lúc (Cascade)

| | |
|:---|:---|
| **Sự cố** | Đồng thời: CPU router HCM vọt lên 93% → Bảng định tuyến bị lỗi → Database bị timeout (180ms) + Chất lượng VoIP giảm (MOS 3.3) + 5G bị nhiễu nhẹ (4%) |
| **Hệ thống phát hiện** | AI phát hiện nhiều chỉ số bất thường cùng lúc và phân tích ra: nguyên nhân gốc rễ là CPU quá tải trên router HCM |
| **Tự khắc phục** | AI xử lý đúng thứ tự: ① Khởi động lại tiến trình controller trên HCM → CPU về 40% → ② Bảng định tuyến tự làm mới → DB và VoIP tự phục hồi → ③ 5G loss 4% chưa đến ngưỡng → chỉ theo dõi |
| **MTTR** | **< 60 giây** _(phức tạp nhất trong 14 kịch bản)_ |

---

## 🟡 NHÓM DỰ BÁO CHỦ ĐỘNG (P1 – P2) — Xử lý TRƯỚC khi sự cố xảy ra

---

### P1 — Dự báo tắc nghẽn trước giờ Backup tự động

| | |
|:---|:---|
| **Sự cố (sắp xảy ra)** | Lúc 02:00:00, tiến trình sao lưu dữ liệu tự động khởi chạy → Băng thông MPLS sắp tăng vọt lên 94% → Cuộc gọi VoIP sẽ bị ảnh hưởng |
| **Hệ thống phát hiện** | Lúc 01:59:45 (15 giây trước): AI đo tốc độ tăng lưu lượng và dự báo "MPLS sẽ đầy sau 15 giây nữa" |
| **Tự khắc phục** | AI chuyển NGAY traffic Backup → Internet (rộng hơn) → MPLS còn thông thoáng → 02:00:00 Backup chạy nhưng MPLS chỉ dùng 40% → VoIP không bị ảnh hưởng gì |
| **MTTR** | **0 giây** — _Sự cố không bao giờ xảy ra với người dùng_ |

---

### P2 — Bảo vệ cuộc gọi khi đường truyền đang xấu dần

| | |
|:---|:---|
| **Sự cố (đang diễn ra)** | Cuộc họp VoIP đang diễn ra → Jitter trên MPLS tăng từ từ từ 5ms lên 35ms trong 1.5 phút → Chất lượng thoại đang trượt dần về ngưỡng báo động |
| **Hệ thống phát hiện** | Mô hình QoE theo dõi: điểm MOS giảm dần 4.2 → 3.6 → 3.2 → Cảnh báo: "Sắp vi phạm SLA (3.5) sau ~15 giây" |
| **Tự khắc phục** | AI chuyển luồng âm thanh của cuộc gọi đang diễn ra sang đường 5G (jitter chỉ 3ms) → Chất lượng phục hồi lên MOS 4.3 → **Cuộc họp tiếp tục bình thường, không ai bị ngắt** |
| **MTTR** | **0 giây** — _Người dùng không cảm nhận được gì_ |

---

## 📊 TỔNG HỢP NHANH

| # | Sự cố | Hệ thống tự làm gì | MTTR |
|:---:|:---|:---|:---:|
| F01 | Đứt cáp switch tầng Access | Reset cổng + tìm đường dự phòng | < 30s |
| F02 | Router phân phối sập | Router dự phòng tự tiếp quản (VRRP) | < 5s |
| F03 | Đứt kết nối BL↔HCM | Định tuyến lại qua Nha Trang | < 40s |
| F04 | MPLS đứt hoàn toàn | Chuyển toàn bộ sang 5G | < 5s |
| F05 | Internet mất | Web/Cloud sang 5G → LTE | < 5s |
| F06 | LTE mất | Backup sang 5G | < 5s |
| F07 | 5G bị nhiễu (loss > 5%) | VoIP/DB sang MPLS | < 5s |
| F08 | VPN sập | Dữ liệu sang MPLS + cảnh báo NOC | < 5s |
| F09 | MPLS tắc nghẽn 88% | Tải nhẹ sang Internet, tăng ưu tiên VoIP | < 10s |
| F10 | Chất lượng VoIP giảm dần | Chuyển cuộc gọi sang 5G (không cắt máy) | 0s |
| F11 | Web Server sập | HAProxy chuyển sang server dự phòng | < 5s |
| F12 | Nhiều sự cố cùng lúc | AI tìm nguyên nhân gốc → xử lý đúng thứ tự | < 60s |
| P1 | Sắp tắc nghẽn lúc 02:00 | Chuyển trước Backup sang Internet | **0s** ✨ |
| P2 | Chất lượng VoIP đang trượt | Chuyển cuộc gọi sang 5G trước khi tệ | **0s** ✨ |
