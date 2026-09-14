# OSPF WAN fix log

## 2026-09-14 15:00 +07:00

- File: `topology/sites/baoloc.py`
- Location: `start_frr_baoloc()`
- Change: thêm `-c "network 192.168.10.0/30 area 0"` vào lệnh OSPF của BL-GW.
- Purpose: cho BL-GW quảng bá link WAN tới HCM để OSPF hình thành adjacency.

## 2026-09-14 15:01 +07:00

- File: `topology/sites/nhatrang.py`
- Location: `start_frr_nhatrang()`
- Change: thêm `-c "network 192.168.20.0/30 area 0"` vào lệnh OSPF của NT-DIST01/NT-DIST02.
- Purpose: cho NT site quảng bá link WAN tới HCM và cho OSPF nhận diện neighbor trên subnet WAN.

## 2026-09-14 15:02 +07:00

- File: `topology/sites/hcm.py`
- Location: `start_frr_hcm()`
- Change: thêm `-c "network 192.168.10.0/30 area 0"`, `-c "network 192.168.20.0/30 area 0"`, `-c "network 192.168.30.0/30 area 0"` vào OSPF config của HCM-DIST01/HCM-DIST02.
- Purpose: cho HCM quảng bá tất cả WAN links và tạo OSPF neighbor với BL, NT, DC.

## 2026-09-14 15:03 +07:00

- File: `topology/sites/datacenter.py`
- Location: `start_frr_datacenter()`
- Change: thêm `-c "network 192.168.30.0/30 area 0"` vào OSPF config của DC_SPINE_GW.
- Purpose: cho DC quảng bá link WAN tới HCM để OSPF kết nối được về backbone Area 0.

## 2026-09-14 15:04 +07:00

- File: `topology/sites/datacenter.py`
- Location: `start_frr_datacenter()`
- Change: sửa lệnh FRR từ `_c`/`router_id` thành `-c`/`router-id` đồng bộ với các file site khác.
- Purpose: đảm bảo vtysh nhận đúng câu lệnh OSPF và không bị parse sai khi khởi động OSPF trên DC-SPINE-GW.

## 2026-09-14 15:10 +07:00

- File: `scripts/network_topology_diagram.py`
- Change: tạo script vẽ sơ đồ mạng phân tầng cho mô hình enterprise KLTN.
- Output: `network_topology.png` ở thư mục gốc `src/`.
- Purpose: hỗ trợ trực quan hóa kiến trúc site, core/distribution/access, gateway, và WAN inter-site.

## 2026-09-14 15:12 +07:00

- File: `scripts/network_topology_diagram.py`
- Change: viết lại sơ đồ mạng theo kiểu cây phân tầng rõ ràng hơn, thêm màu theo từng site BL/NT/HCM/DC và tối ưu layout dễ đọc hơn.
- Purpose: hỗ trợ mô tả kiến trúc mạng doanh nghiệp rõ ràng hơn cho báo cáo, thuyết minh và demo.

## 2026-09-14 15:18 +07:00

- File: `scripts/network_topology_diagram.py`
- Change: sửa tên host hiển thị trong sơ đồ thành tên thực tế (BL_ADM01, BL_SAL01, BL_ACC01, BL_IT01, BL_PRN01, BL_CAM01; NT/HCM host tên theo pattern `${DIST}_ADM01`, `${DIST}_SAL01`, ...).
- Purpose: tránh nhầm lẫn khi so khớp sơ đồ với cấu hình `vlan.yaml` và log kiểm thử.

## 2026-09-14 15:22 +07:00

- File: `scripts/network_topology_diagram.py`
- Change: giãn khoảng cách giữa các chi nhánh và các access/host để sơ đồ dễ đọc hơn (BL dịch sang trái, ACC/host NT-HCM rải rộng hơn, cập nhật các đường WAN tương ứng).
- Purpose: cải thiện độ rõ ràng của sơ đồ, tránh chồng chéo nhãn khi trình bày.
## Root cause summary

- Trước đây OSPF chỉ quảng bá các mạng LAN trong site: `10.10.0.0/16`, `10.20.0.0/16`, `10.30.0.0/16`, `10.100.0.0/16`.
- Các link WAN `192.168.x.x/30` không được đưa vào OSPF, nên hello packet không đi qua và adjacency không hình thành.
- Sửa lỗi bằng cách thêm các mạng WAN vào `network ... area 0` cho từng router có link WAN tương ứng.

## Final validation notes

- Root cause chính xác: OSPF chỉ advertise các mạng LAN nội site, không advertise các link WAN `192.168.10.0/30`, `192.168.20.0/30`, `192.168.30.0/30`.
- Fix áp dụng: thêm các `network ... area 0` cho từng WAN subnet tương ứng ở BL, NT, HCM, DC.
- Extra correction: đồng bộ cú pháp FRR CLI ở DC (`-c`, `router-id`) để tránh lỗi command parse khi khởi động OSPF.
