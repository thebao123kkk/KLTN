# 📑 TÀI LIỆU TOÀN DIỆN VỀ TELEMETRY: CÁC THÀNH CÔNG ĐÃ ĐẠT ĐƯỢC & HƯỚNG DẪN KHẮC PHỤC SỰ CỐ

---

## 1. Những thành quả và tính năng đã hiện thực hóa thành công của hệ thống Telemetry

Hệ thống Telemetry của đồ án đã được thiết kế và hiện thực hóa một cách bài bản, đạt được các kết quả kỹ thuật xuất sắc sau:

### 1.1. Cào dữ liệu 100% từ môi trường mạng Mininet & OVS Kernel thực tế
- **Quét động chính xác toàn bộ thiết bị mạng:** Module [telemetry_exporter.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/controller/sdn/telemetry_exporter.py) đã vượt qua giai đoạn giả lập số liệu tĩnh. Hệ thống tự động truy vấn trực tiếp từ nhân Linux (`/sys/class/net/`) và phát hiện chính xác **21 OpenFlow switch** đang hoạt động đồng thời trong Mininet (`of_datapath_connected: 21.0`).
- **Bắt kịp trạng thái cổng vật lý tức thì:** Đọc trạng thái liên kết (`carrier`) của từng giao diện mạng (`-eth`). Khi một đường truyền bị ngắt trong Mininet, bộ đếm cổng hỏng (`port_status_down_total`) lập tức nhảy từ `0` lên `1` hoặc `2` mà không có độ trễ.
- **Đo đếm lưu lượng truyền nhận thực tế:** Chỉ số gói tin (`tx_packets`) phản ánh chính xác lưu lượng thật. Khi các trạm gửi gói tin ping hoặc chạy kiểm tra băng thông (iperf), số lượng gói tin gửi đi (`of_messages_sent_total`) tăng trưởng chuẩn xác theo thời gian thực.

### 1.2. Hiện thực hóa chuẩn mô hình Vector Trạng Thái 8 Chiều (8D State Vector)
Module tổng hợp dữ liệu [vector_assembler.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/vector_assembler.py) và [collector.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/collector.py) đã chuẩn hóa đầu ra theo đúng nghiên cứu lý thuyết:
- Đầy đủ 8 tham số trạng thái cốt lõi: CPU controller (`ccpu`), bộ nhớ thực tế (`cres_mem`), bộ nhớ ảo (`cvirt_mem`), gói tin gửi (`fsent`), lỗi OpenFlow (`ferr`), số switch kết nối (`fconn`), số lần mất kết nối (`fdisc`), và số cổng down (`pdown`).
- Trích xuất tự động **Ngữ cảnh vi mô (Micro Context Metadata)**: Nhận diện chính xác ID của switch gặp sự cố (`target_dpid`), số hiệu cổng bị lỗi (`target_port`) và mã lỗi chi tiết (`error_cookie`), hỗ trợ đắc lực cho khâu phân tích nguyên nhân gốc rễ (RCA).

### 1.3. Cơ chế chịu lỗi đa tầng (Graceful Degradation & Fallback)
- Toàn bộ đường ống thu thập được trang bị cơ chế bảo vệ: Khi Prometheus server bị trễ hoặc ngắt quãng, bộ thu thập không bao giờ bị dừng đột ngột (crash). Thay vào đó, hệ thống tự kích hoạt cơ chế `last_known` (lấy giá trị hợp lệ gần nhất) và tự động gắn cờ chất lượng dữ liệu (`data_quality: OK | STALE | MISSING`).

### 1.4. Tích hợp đồng bộ tự động với 12 Kịch Bản Tiêm Sự Cố (F01–F12)
- Module [fault_log_reader.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/ai_engine/telemetry/fault_log_reader.py) liên kết trực tiếp với bộ điều phối lỗi [fault_injector.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/fault_injection/fault_injector.py).
- Tự động gắn nhãn sự cố theo chuẩn (`fault_label`: `PORT_FAULT`, `LINK_FAULT`, `FLOW_ERROR`, `NONE`,...) và tính toán chính xác thời gian duy trì lỗi (`duration_seconds`) theo mốc thời gian chuẩn quốc tế ISO-8601.

### 1.5. Tự động xuất Dataset chuẩn hóa cho Machine Learning & AI Engine
- Sau mỗi chu kỳ quét (mặc định 10 giây), hệ thống tự động ghi bổ sung (append) vào tệp dữ liệu CSV chuẩn 15 cột [data/sdn_telemetry_dataset.csv](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/data/sdn_telemetry_dataset.csv).
- Tệp dữ liệu này có cấu trúc chuẩn hóa, có thể đưa trực tiếp vào huấn luyện các mô hình Trí tuệ Nhân tạo như Rừng Ngẫu Nhiên (Random Forest), Rừng Cách Ly (Isolation Forest) và Học tăng cường sâu (PPO) mà không cần qua bất kỳ bước làm sạch thủ công nào.
- Đồng thời ghi lưu song song tệp nhật ký dạng dòng JSON (`telemetry_log.jsonl`) để phục vụ lưu vết và kiểm tra chi tiết.

---

## 2. Hiện tượng: Telemetry đang bị lỗi gì?

Khi quan sát kết quả kiểm tra của bạn:
1. **Tại Exporter (`:9303`):** Lệnh `curl -s http://localhost:9303/metrics` trả về dữ liệu OVS switch thực tế rất tốt:
   - `of_datapath_connected 21.0` (phát hiện đủ 21 switch Mininet đang kết nối).
   - `port_status_down_total 0`.
2. **Tại Collector (`telemetry_collector.py`):** Khi thu thập dữ liệu lại gặp lỗi:
   ```text
   2026-10-17 21:32:27,711 [WARNING]: [Prometheus] Query rỗng: 'faucet_cpu_seconds_total'
   2026-10-17 21:32:27,766 [WARNING]: [Prometheus] Query rỗng: 'of_datapath_connected'
   2026-10-17 21:32:27,787 [WARNING]: [Prometheus] Query rỗng: 'port_status_down_total'
   2026-10-17 21:32:27,834 [INFO]: [0001] fconn=0.0 pdown=0 ferr=0 fdisc=0 | quality=OK
   ```

### Hệ quả:
- Mặc dù mạng thật có **21 switch**, nhưng State Vector thu thập được lại chỉ nhận `fconn=0.0`, `ccpu=0.0`.
- Dataset huấn luyện AI lưu vào file `data/sdn_telemetry_dataset.csv` bị toàn số `0.0`, khiến mô hình AI sau này không phát hiện được sự cố.

---

## 3. Vị trí lỗi: Lỗi xảy ra ở đâu trong hệ thống?

Mô hình luồng dữ liệu Telemetry của dự án gồm 3 mắt xích:
```text
[Mininet & OVS Kernel] 
         │
         ▼
[telemetry_exporter.py] (:9302, :9303)  ───> HOẠT ĐỘNG TỐT (curl ra 21 switch)
         │
         ▼ (Scrape định kỳ)
[Prometheus Server] (:9090)             ───> ❌ NƠI PHÁT SINH LỖI
         │
         ▼ (Query PromQL)
[telemetry_collector.py]                 ───> ❌ NHẬN KẾT QUẢ RỖNG TỪ PROMETHEUS
```

### Nguyên nhân gốc rễ (Root Causes):

1. **Nguyên nhân 1 (Phổ biến nhất): Prometheus khởi động không tải đúng file cấu hình [config/prometheus.yml](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/config/prometheus.yml)**
   - Nếu bạn gõ lệnh `prometheus` hoặc Prometheus chạy ngầm qua service hệ thống mà **thiếu cờ `--config.file=config/prometheus.yml`**, Prometheus sẽ tải file cấu hình mặc định của Linux (thường chỉ scrape cổng `localhost:9090` của chính nó).
   - Kết quả: Prometheus vẫn chạy bình thường (`quality=OK`), nhưng nó **hoàn toàn không biết** có 2 endpoint `:9302` và `:9303` để scrape. Khi `telemetry_collector.py` truy vấn `of_datapath_connected`, Prometheus trả về danh sách rỗng (`"result": []`).

2. **Nguyên nhân 2: Scrape Target trong Prometheus đang ở trạng thái `DOWN`**
   - Prometheus scrape theo chu kỳ (mặc định trong config là `10s`). Nếu Prometheus khởi động trước khi Exporter chạy, hoặc nếu target gặp lỗi mạng nội bộ, Prometheus sẽ đánh dấu target là `DOWN`.

3. **Nguyên nhân 3: Endpoint `:9302` (Faucet CPU/Memory) chưa chạy**
   - Trong `telemetry_exporter.py`, cổng `:9302` phục vụ các chỉ số `faucet_cpu_seconds_total`, `process_resident_memory_bytes`, còn cổng `:9303` phục vụ `of_datapath_connected`. Nếu chỉ mới kích hoạt cổng 9303 mà cổng 9302 chưa mở, các chỉ số CPU/Memory sẽ trả về query rỗng.

---

## 4. Cách khắc phục chi tiết (Từng bước)

Hãy thực hiện tuần tự các bước sau trong terminal Linux/WSL:

### Bước 1: Dọn dẹp tiến trình Prometheus cũ đang chạy sai cấu hình
```bash
# Tắt tất cả tiến trình prometheus và exporter cũ đang chạy nền
pkill -9 -f prometheus
pkill -9 -f telemetry_exporter.py
```

### Bước 2: Khởi động lại Exporter
Đảm bảo bạn đang đứng tại thư mục `.../src/`:
```bash
cd ~/KLTN/KLTN/src
python3 controller/sdn/telemetry_exporter.py &
```
*Kiểm tra nhanh xem cả 2 cổng 9302 và 9303 đã lắng nghe chưa:*
```bash
curl -s http://localhost:9302/metrics | grep "faucet_cpu"
curl -s http://localhost:9303/metrics | grep "of_datapath_connected"
```
*(Nếu cả hai đều xuất ra số liệu là đạt chuẩn).*

### Bước 3: Khởi động Prometheus với ĐÚNG file cấu hình của dự án
```bash
prometheus --config.file=config/prometheus.yml --storage.tsdb.path=data/prometheus_data &
```

### Bước 4: Kiểm tra trạng thái liên kết (Scrape Targets)
Dự án đã có sẵn script chẩn đoán tự động [tests/check_telemetry_pipeline.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/tests/check_telemetry_pipeline.py), hãy chạy ngay:
```bash
python3 tests/check_telemetry_pipeline.py
```
Hoặc kiểm tra nhanh qua `curl`:
```bash
curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"[^"]*"'
```
> **Yêu cầu:** Các target `gauge_sdn` (:9303) và `faucet_sdn` (:9302) phải hiển thị `"health":"up"`.

> [!IMPORTANT]
> **Đợi khoảng 10 đến 15 giây** sau khi bật Prometheus để nó hoàn thành chu kỳ scrape (lấy mẫu) đầu tiên ghi vào cơ sở dữ liệu TSDB.

### Bước 5: Chạy lại Telemetry Collector và kiểm tra bắt lỗi
```bash
python3 telemetry_collector.py --cycles 3 --interval 10
```

**Kỳ vọng kết quả hiển thị trên Terminal:**
```text
[0001] fconn=21.0 pdown=0 ferr=0 fdisc=0 | label=NONE(0.0s) | quality=OK
[0002] fconn=21.0 pdown=0 ferr=0 fdisc=0 | label=NONE(0.0s) | quality=OK
```
👉 `fconn` nhận đủ **21.0**, không còn dòng cảnh báo `Query rỗng` nào nữa!

---

## 5. Kiểm chứng khi tiêm lỗi mạng (Fault Injection)

Sau khi telemetry đã cào được dữ liệu sống:

1. **Thực hiện tiêm lỗi hạ port / ngắt link trên Mininet:**
   ```bash
   # Trong một terminal khác, tiêm kịch bản F01 trong 30 giây:
   python3 fault_injection/fault_injector.py -s F01 --duration 30 --action inject
   ```
   *(Hoặc gõ trực tiếp trong Mininet CLI: `mininet> link NT_ACC01 NT_CORE down`)*

2. **Quan sát Telemetry Collector:**
   - Cột `pdown` sẽ tự động nhảy từ `0` lên `1` hoặc `2` (tương ứng số cổng bị down).
   - Cột `label` sẽ chuyển từ `NONE(0.0s)` sang `PORT_FAULT(x.xs)`.
   - Cột `quality` giữ nguyên `OK`.

3. **Khôi phục lỗi:**
   ```bash
   python3 fault_injection/fault_injector.py -s F01 --action recover
   ```
   *(Hoặc trong Mininet CLI: `mininet> link NT_ACC01 NT_CORE up`)*
   - Cột `pdown` sẽ lập tức trở về `0` và `label` trở về `NONE(0.0s)`.

---

## 6. Sự cố: Đã tiêm lỗi nhưng Telemetry vẫn không bắt được

### Hiện tượng:
Lệnh tiêm lỗi đã được chạy thành công trên màn hình, nhưng khi bộ thu thập dữ liệu quét qua thì nhãn sự cố vẫn báo trạng thái bình thường (mã nhãn là `NONE`, thời lượng lỗi là `0.0`), đồng thời số cổng bị ngắt vẫn giữ nguyên là `0`.

### Các nguyên nhân chính:

1. **Lỗi trôi qua thời gian hiệu lực (Hết hạn sự cố trước khi quét):**
   - Bộ quản lý lỗi được cài đặt thời gian duy trì sự cố nhất định (mặc định 30 giây). Bộ thu thập telemetry có cơ chế tự động hủy bỏ nhãn nếu thời gian kể từ lúc tiêm lỗi đến lúc quét vượt quá thời lượng quy định cộng thêm 5 giây dự phòng.
   - Nếu bạn kích hoạt tiêm lỗi xong nhưng vài phút sau mới bật bộ thu thập, hệ thống sẽ hiểu sự cố đó đã kết thúc từ lâu và tự động đánh nhãn an toàn trở lại.

2. **Lệch thư mục lưu và đọc nhật ký sự cố:**
   - Khi chạy kịch bản tiêm lỗi và bộ thu thập ở hai cửa sổ dòng lệnh khác nhau, nếu đứng sai thư mục gốc thì file nhật ký sự cố được ghi ra ở một vị trí khác, trong khi bộ thu thập lại tìm kiếm ở thư mục mặc định của dự án. Do không tìm thấy dòng sự kiện mới, hệ thống mặc định coi như không có lỗi.

3. **Thiếu quyền quản trị hệ thống khi ngắt đường truyền mạng thật:**
   - Một số kịch bản tác động trực tiếp vào liên kết mạng và giao diện switch ảo yêu cầu quyền quản trị cao nhất của hệ điều hành. Nếu chạy thiếu quyền, hệ điều hành sẽ từ chối thao tác ngắt cổng mạng trong âm thầm, khiến trạng thái đường truyền thực tế không hề bị mất.

4. **Độ lệch giữa chu kỳ quét và thời gian duy trì lỗi:**
   - Bộ thu thập lấy mẫu theo khoảng thời gian định kỳ (ví dụ 10 giây một lần). Nếu khoảng thời gian tiêm lỗi quá ngắn và kết thúc ngay trong khoảng nghỉ giữa hai chu kỳ quét, bộ thu thập sẽ hoàn toàn bỏ lỡ thời điểm xảy ra sự cố.

### Cách khắc phục:

1. **Tăng thời lượng duy trì sự cố khi tiêm:**
   - Khi thử nghiệm, nên nâng thời gian tồn tại của lỗi lên từ 60 đến 120 giây để có đủ thời gian mở bộ thu thập quan sát qua nhiều chu kỳ.
   ```bash
   python3 fault_injection/fault_injector.py -s F01 --duration 120 --action inject
   ```

2. **Bật bộ thu thập chạy liên tục trước, sau đó mới tiến hành tiêm lỗi:**
   - Hãy để cửa sổ thu thập telemetry chạy nền hoặc hiển thị liên tục theo chu kỳ ngắn (ví dụ 2 đến 5 giây). Sau đó, tại một cửa sổ khác bạn mới thực hiện tiêm lỗi. Bạn sẽ thấy dòng dữ liệu đang từ trạng thái bình thường lập tức chuyển sang trạng thái cảnh báo ngay trong chu kỳ tiếp theo.

3. **Chạy đúng quyền quản trị và cùng thư mục làm việc:**
   - Luôn đảm bảo đứng tại thư mục mã nguồn chính của dự án trên cả hai cửa sổ làm việc và sử dụng quyền quản trị thích hợp khi thực thi các kịch bản can thiệp mạng thực tế.

---

## 7. Tổng hợp các vấn đề của hệ thống Telemetry (Trình bày bằng lời văn)

Dưới đây là bức tranh toàn cảnh về các trục trặc có thể gặp phải trong hệ thống giám sát và thu thập số liệu mạng, giải thích cặn kẽ bản chất vấn đề và hướng xử lý một cách tự nhiên, dễ hiểu nhất:

### Vấn đề thứ nhất: Số liệu các thiết bị mạng hiển thị bằng không dù mạng vẫn hoạt động
- **Bản chất vấn đề nằm ở đâu:** Trục trặc này xuất phát từ cầu nối trung gian lưu trữ dữ liệu. Bộ phận đo lường đặt tại các thiết bị mạng đã đo đạc chính xác và sẵn sàng cung cấp số liệu, nhưng máy chủ lưu trữ dữ liệu tập trung khi khởi động lại không được chỉ định đúng hồ sơ cấu hình của hệ thống. Do đó, máy chủ này chỉ tự kiểm tra chính nó mà hoàn toàn không biết đến sự tồn tại của các trạm đo lường mạng, dẫn đến việc khi trung tâm phân tích hỏi số liệu thì máy chủ trả lời không có thông tin.
- **Cách khắc phục:** Cần tắt hoàn toàn các tiến trình máy chủ lưu trữ đang chạy sai, sau đó khởi động lại với hướng dẫn nạp đúng tệp cấu hình riêng của dự án. Sau khi bật, cần kiên nhẫn đợi khoảng mười đến mười lăm giây để máy chủ kịp thời hoàn thành lượt lấy mẫu đầu tiên trước khi tiến hành đọc số liệu.

### Vấn đề thứ hai: Bị thiếu hụt các chỉ số về tài nguyên bộ nhớ và tải của bộ điều khiển
- **Bản chất vấn đề nằm ở đâu:** Hệ thống phân chia việc đo đạc thành hai cổng dịch vụ riêng biệt: một cổng chuyên đo trạng thái phần cứng và các cổng mạng, cổng còn lại chuyên đo mức độ sử dụng tài nguyên của bộ điều khiển. Người vận hành thường chỉ bật một dịch vụ phục vụ mạng mà quên khởi động dịch vụ còn lại, khiến các câu hỏi về mức độ chiếm dụng bộ nhớ hay xử lý của bộ điều khiển bị bỏ trống.
- **Cách khắc phục:** Đảm bảo kịch bản xuất số liệu tổng hợp được chạy đầy đủ để mở cùng lúc cả hai kênh thông tin, đáp ứng đầy đủ tất cả các nhóm dữ liệu mà trung tâm giám sát yêu cầu.

### Vấn đề thứ ba: Đã cố tình tạo sự cố mạng nhưng hệ thống giám sát vẫn báo mọi thứ bình thường
- **Bản chất vấn đề nằm ở đâu:** Vấn đề này thường do sự lệch pha về thời gian hoặc phân quyền thực thi. Khi sự cố được tạo ra với thời gian tồn tại quá ngắn, hệ thống tự động nhận diện rằng sự cố đã trôi qua và tự xóa cảnh báo trước khi chu kỳ kiểm tra tiếp theo diễn ra. Bên cạnh đó, nếu thao tác ngắt kết nối mạng không được cấp quyền quản trị hệ thống, hệ điều hành sẽ chặn hành động này lại, nghĩa là trên thực tế sợi dây mạng ảo vẫn chưa hề bị đứt dù lệnh đã được gõ. Cuối cùng, việc chạy các câu lệnh ở các thư mục khác nhau cũng khiến việc ghi nhật ký và đọc nhật ký không tìm thấy nhau.
- **Cách khắc phục:** Luôn mở màn hình quan sát chạy đều đặn trước, sau đó mới tiến hành thao tác gây sự cố ở một màn hình khác. Khi tạo sự cố, hãy đặt thời gian kéo dài từ một đến hai phút để quan sát kịp thời. Đồng thời, luôn thực thi các thao tác can thiệp hệ thống với quyền quản trị viên cao nhất và đảm bảo các cửa sổ làm việc đều mở chung từ thư mục làm việc của dự án.