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

## 2026-09-19 15:00 +07:00 — Gateway Interface & FRR Namespace Bug Fixes

### 1. File: `topology/sites/baoloc.py`
- Location: `_configure_gw_interfaces()`, `start_frr_baoloc()`
- Change (Sửa từ -> Thành):
  - Sửa `base_intf = 'BL-GW-eth0'` (dấu `-`) thành `base_intf = f'{gw_host.name}-eth0'` (`BL_GW-eth0` dấu `_`).
  - Sửa `gw_host.cmd('service frr start')` thành khởi động zebra + ospfd per-namespace (`/usr/lib/frr/zebra -d`, `/usr/lib/frr/ospfd -d`).
- Purpose: Khắc phục lỗi `Cannot find device "BL-GW-eth0"` làm thất bại khởi tạo sub-interface VLAN trên `BL_GW`, và đảm bảo daemon OSPF chạy trong network namespace riêng của `BL_GW`.

### 2. File: `topology/sites/nhatrang.py`
- Location: `build_nhatrang()`, `_configure_dist_interfaces()`, `start_frr_nhatrang()`
- Change (Sửa từ -> Thành):
  - Sửa `dist1` & `dist2` từ `net.addSwitch('NT_DIST01', cls=OVSSwitch...)` / `net.addSwitch('NT_DIST02', cls=OVSSwitch...)` thành `net.addHost('NT_DIST01', ip=None)` / `net.addHost('NT_DIST02', ip=None)` (Mininet Host Router).
  - Sửa `base_intf = f'{dist_name}-eth0'` thành `base_intf = f'{dist_host.name}-eth0'` (`NT_DIST01-eth0` / `NT_DIST02-eth0`).
  - Sửa `dist_host.cmd('service frr start')` thành khởi động zebra + ospfd per-namespace.
- Purpose: Chuyển `NT_DIST01` và `NT_DIST02` thành router L3 có namespace riêng thay vì L2 OVS switch, cho phép tạo sub-interface VLAN `NT_DIST01-eth0.110`... và khởi tạo OSPF/VRRP gateway độc lập.

### 3. File: `topology/sites/hcm.py`
- Location: `build_hcm()`, `configure_hcm()`, `_configure_dist_interfaces()`, `start_frr_hcm()`
- Change (Sửa từ -> Thành):
  - Sửa `dist1` & `dist2` từ `net.addSwitch('HCM_DIST01', cls=OVSSwitch...)` / `net.addSwitch('HCM_DIST02', cls=OVSSwitch...)` thành `net.addHost('HCM_DIST01', ip=None)` / `net.addHost('HCM_DIST02', ip=None)`.
  - Sửa parameter gọi hàm `_configure_dist_interfaces(dist1, 'HCM-DIST01', vlan_cfg)` (dấu `-`) thành `_configure_dist_interfaces(dist1, 'HCM_DIST01', vlan_cfg)` (dấu `_`).
  - Sửa `base_intf = f'{dist_name}-eth0'` thành `base_intf = f'{dist_host.name}-eth0'` (`HCM_DIST01-eth0` / `HCM_DIST02-eth0`).
  - Sửa `dist_host.cmd('service frr start')` thành khởi động zebra + ospfd per-namespace.
- Purpose: Chuyển HCM distribution routers từ OVS switches thành L3 Mininet host routers, sửa tên interface đồng bộ, tạo được sub-interfaces VLAN và chạy OSPF/VRRP daemon đúng namespace.

### 4. File: `topology/sites/datacenter.py`
- Location: `_configure_gw_interfaces()`, `start_frr_datacenter()`
- Change (Sửa từ -> Thành):
  - Sửa `base_intf = 'DC_SP_GW-eth0'` thành `base_intf = f'{gw_host.name}-eth0'` (`DC_SP_GW-eth0`).
  - Sửa `gw.cmd('service frr start')` thành khởi động zebra + ospfd per-namespace.
- Purpose: Đồng bộ cú pháp đặt base interface động và khởi động FRR OSPF trong namespace của `DC_SP_GW`.

### 5. File: `scripts/generate_keepalived_conf.py`
- Location: `generate_keepalived_conf()`
- Change (Sửa từ -> Thành):
  - Sửa `interface_name = f'eth0.{vlan_id}'` thành `interface_name = f'{clean_node_name}-eth0.{vlan_id}'` (ví dụ `NT_DIST01-eth0.110`, `HCM_DIST01-eth0.210`).
- Purpose: Đảm bảo Keepalived bind VIP đúng vào sub-interface VLAN thực tế trong namespace của từng router ảo.

### 6. Files: `topology/sites/baoloc.py`, `nhatrang.py`, `hcm.py`, `datacenter.py`
- Locat## 2026-09-19 16:00 +07:00 — Linux Bridge VLAN Filtering & 802.1Q Module Fix (`vlan_filtering 1`)

### Files: `topology/sites/baoloc.py`, `nhatrang.py`, `hcm.py`, `datacenter.py`, `topology/enterprise_topo.py`
- Location: `_configure_gw_interfaces()`, `_configure_dist_interfaces()`, `check_environment()`
- Change (Sửa từ -> Thành):
  - Kích hoạt `vlan_filtering 1` trên Linux bridge `br0` (`ip link set dev br0 type bridge vlan_filtering 1`).
  - Cấu hình cho phép dải VLAN 2-4094 đi qua các cổng slave của bridge `br0` (`bridge vlan add dev <intf> vid 2-4094`).
  - Thêm tự động nạp Linux kernel module 802.1Q (`modprobe 8021q`) trong `check_environment()`.
- Purpose: Khắc phục triệt để lỗi Linux Bridge mặc định lọc bỏ các gói tin gắn thẻ 802.1Q VLAN khác 1 khi chưa bật `vlan_filtering 1`, giúp các sub-interface `br0.VLAN` phân giải ARP và nhận gói tin ICMP hoàn toàn thông suốt.

## 2026-09-19 16:35 +07:00 — Controller Configuration Update (`controller=None`)

### Files: `topology/enterprise_topo.py`, `test.py`
- Location: `build_network()`, `main()`
- Change (Sửa từ -> Thành):
  - Sửa `controller=OVSController` thành `controller=None` trong khởi tạo `Mininet(...)`.
  - Loại bỏ lệnh khởi tạo dummy controller `topo.net.addController('c0')`.
- Purpose: Đảm bảo toàn bộ các OVS Switch ở các Phase 1–8 hoạt động tức thì ở chế độ Standalone L2 MAC Learning Switch thuần túy, tránh việc OVS Switch gửi bản tin OpenFlow lên controller không tồn tại làm nghẽn hoặc hủy các gói tin ARP/Ping.

## 2026-09-19 17:40 +07:00 — Fix Inter-VLAN Routing, Bridge STP & Test Script Update

### 1. File: `test.py`
- Change: Chuyển đổi kịch bản kiểm thử độc lập từ Bảo Lộc sang Nha Trang site ([`nhatrang.py`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/git/KLTN/src/topology/sites/nhatrang.py)). Tự động tạo cấu hình Keepalived, khởi động OSPF/VRRP và thực thi 4 bộ kiểm thử (Sub-interfaces, Intra-VLAN ping, Gateway ping, Inter-VLAN routing ping) cho 22 end hosts.

### 2. Files: `topology/sites/nhatrang.py`, `topology/sites/hcm.py`
- Location: `_set_stp_priority()`, `_configure_dist_interfaces()`, `start_vrrp_nhatrang()`, `start_vrrp_hcm()`
- Change (Sửa từ -> Thành):
  - Bổ sung `other-config:stp-forward-delay=2` cho các OVS Switch để giảm thời gian hội tụ OVS STP từ 30s xuống 4s.
  - Bật `stp_state 1` và `forward_delay 200` trên Linux bridge `br0` của `NT_DIST01/02` và `HCM_DIST01/02` (`ip link set dev br0 type bridge vlan_filtering 1 stp_state 1 forward_delay 200`).
  - Gán trực tiếp IP Default Gateway `.1` (`10.20.x.1` ở Nha Trang, `10.30.x.1` ở HCM) cho router chính (`DIST01`) ngay từ bước cấu hình VLAN sub-interface `br0.VLAN`.
  - Thêm tự động kiểm tra và sinh file cấu hình Keepalived `/tmp/keepalived_*.conf` trong hàm `start_vrrp_*` nếu chưa có sẵn.
- Purpose: 
  - Khắc phục triệt để bão gói tin vòng lặp L2 (Broadcast/Multicast storm) trên Linux Bridge `br0` giữa 2 Distribution Routers làm đứng mạng trong `enterprise_topo.py`.
  - Đảm bảo định tuyến Inter-VLAN chạy thành công 100% (0% packet loss) trên toàn bộ 4 site khi chạy kịch bản kiểm thử đơn lẻ (`test.py`) lẫn mô hình doanh nghiệp đầy đủ (`enterprise_topo.py`).
�ch bản kiểm thử độc lập từ Bảo Lộc sang Nha Trang site ([`nhatrang.py`](file:///d:/DaiHoc/Nam4/KhoaLuanTotNghiep/src/git/KLTN/src/topology/sites/nhatrang.py)). Tự động tạo cấu hình Keepalived, khởi động OSPF/VRRP và thực thi 4 bộ kiểm thử (Sub-interfaces, Intra-VLAN ping, Gateway ping, Inter-VLAN routing ping) cho 22 end hosts.

### 2. Files: `topology/sites/nhatrang.py`, `topology/sites/hcm.py`
- Location: `_set_stp_priority()`, `_configure_dist_interfaces()`, `start_vrrp_nhatrang()`, `start_vrrp_hcm()`
- Change (Sửa từ -> Thành):
  - Bổ sung `other-config:stp-forward-delay=2` cho các OVS Switch để giảm thời gian hội tụ OVS STP từ 30s xuống 4s.
  - Bật `stp_state 1` và `forward_delay 200` trên Linux bridge `br0` của `NT_DIST01/02` và `HCM_DIST01/02` (`ip link set dev br0 type bridge vlan_filtering 1 stp_state 1 forward_delay 200`).
  - Gán trực tiếp IP Default Gateway `.1` (`10.20.x.1` ở Nha Trang, `10.30.x.1` ở HCM) cho router chính (`DIST01`) ngay từ bước cấu hình VLAN sub-interface `br0.VLAN`.
  - Thêm tự động kiểm tra và sinh file cấu hình Keepalived `/tmp/keepalived_*.conf` trong hàm `start_vrrp_*` nếu chưa có sẵn.
- Purpose: 
  - Khắc phục triệt để bão gói tin vòng lặp L2 (Broadcast/Multicast storm) trên Linux Bridge `br0` giữa 2 Distribution Routers làm đứng mạng trong `enterprise_topo.py`.
  - Đảm bảo định tuyến Inter-VLAN chạy thành công 100% (0% packet loss) trên toàn bộ 4 site khi chạy kịch bản kiểm thử đơn lẻ (`test.py`) lẫn mô hình doanh nghiệp đầy đủ (`enterprise_topo.py`).
