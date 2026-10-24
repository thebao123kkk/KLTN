Tôi đã tìm ra nguyên nhân và **nâng cấp cơ chế cào dữ liệu để đọc trực tiếp 100% từ mô hình mạng Mininet thực tế**.

---

### 🔍 Nguyên nhân trước đó chưa thấy cào từ mạng thật:

1. Trước đó, `telemetry_exporter.py` dùng danh sách 5 switch tĩnh làm mẫu (baseline).
2. Khi Mininet chạy bằng `sudo`, các switch và interface (`BL_SW-eth1`, `NT_CORE-eth2`,...) được tạo ra trực tiếp trong kernel mạng của Linux. Exporter trước đó chưa tự động quét động các interface này nên chưa phản ánh đúng mạng Mininet đang chạy.

---

### 🚀 Cơ chế cào dữ liệu THỰC TẾ mới (Đã nâng cấp):

Tôi vừa cập nhật [controller/sdn/telemetry_exporter.py](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/wwsl/src/controller/sdn/telemetry_exporter.py) để đọc trực tiếp từ nhân Linux (`/sys/class/net/`):

1. **`fconn` (Số switch hoạt động):** Tự động quét và đếm **toàn bộ switch thực tế** đang chạy trong Mininet (`BL_SW`, `NT_CORE`, `HCM_CORE`, `DC_SPINE`, `NT_ACC`, `HCM_ACC`,...).
2. **`fsent` (Số gói tin):** Đọc bộ đếm gói tin thực tế (`tx_packets`) trên tất cả các cổng switch. Khi các host trong Mininet gửi traffic hoặc ping nhau, `fsent` sẽ **tăng theo lưu lượng thật**.
3. **`pdown` (Cổng bị sự cố):** Đọc trạng thái đường truyền vật lý (`carrier`) của từng interface. Khi bạn ngắt link hoặc hạ port trong Mininet, `pdown` sẽ **nhảy từ 0 lên 1 ngay lập tức**.
4. **`ferr` (Lỗi OpenFlow/Packet):** Đọc lỗi truyền gói tin thực tế (`tx_errors`).

---

### 🧪 Cách kiểm chứng dữ liệu cào thật từ Mininet:

#### Bước 1: Khởi động Mininet Topology (Terminal 1)
```bash
sudo -E python3 topology/enterprise_topo.py
```
*(Chờ Mininet khởi tạo xong và hiện dấu nhắc lệnh `mininet>`)*

#### Bước 2: Khởi động Exporter & Prometheus (Terminal 2)
```bash
# Chạy exporter quét mạng Mininet:
python3 controller/sdn/telemetry_exporter.py &

# Chạy Prometheus:
prometheus --config.file=config/prometheus.yml --storage.tsdb.path=data/prometheus_data &
```

#### Bước 3: Xem dữ liệu thay đổi theo hành động trong Mininet

1. **Khi mạng bình thường:**
   Kiểm tra:
   ```bash
   curl -s http://localhost:9303/metrics | grep -E 'of_datapath_connected|port_status_down'
   ```
   *Bạn sẽ thấy `of_datapath_connected` hiển thị đúng tổng số switch Mininet thực tế đang chạy trên máy (thay vì số giả lập).*

2. **Khi bạn hạ một cổng mạng trong Mininet (Terminal 1):**
   ```text
   mininet> link BL_SW BL_GW down
   ```
   Kiểm tra lại trên Terminal 2:
   ```bash
   curl -s http://localhost:9303/metrics | grep 'port_status_down_total'
   # -> port_status_down_total 1 (Tăng lên 1 ngay lập tức!)
   ```

3. **Khi bạn truyền lưu lượng ping trong Mininet (Terminal 1):**
   ```text
   mininet> pingall
   ```
   Bộ đếm gói tin `of_messages_sent_total` sẽ tăng vọt theo đúng số lượng gói tin ARP/ICMP thực tế vừa truyền qua các switch.

Edited temp.txt
Viewed temp.txt:64-87