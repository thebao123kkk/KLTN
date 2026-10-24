# OSPF WAN fix log

## 2026-09-14 15:00 +07:00
v
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


## 2026-10-07 22:00 +07:00 — Cross-System Audit & Code/Doc Synchronization

### 1. File: `topology/sites/hcm.py`
- Location: `ACC_VLANS`, `HOST_TO_ACC`
- Change: Đổi tất cả kí tự `-` thành `_` cho switch names (`HCM_ACC01`..`06`) và host names (`HCM_ADMIN_PC01`..). Điều chỉnh VLAN mapping cho `HCM_ACC05` (250, 260) và `HCM_ACC06` (270, 280) cho khớp với `topology.md`.
- Purpose: Sửa lỗi lookup switch/host name thất bại do Mininet addSwitch/addHost dùng tên `_` nhưng dictionary key dùng `-`.

### 2. File: `config/acl_rules.yaml` & `ke_hoach_thiet_ke_phase7_8_9_10_14.md`
- Location: `zones` mapping (iot, cctv, wifi, voice)
- Change: Sửa subnet mapping cho đúng VLAN thực tế:
  - NT IoT (VLAN 170): `10.20.70.0/24`, NT CCTV (VLAN 175): `10.20.75.0/24`, NT WiFi (VLAN 180): `10.20.80.0/24`
  - HCM IoT (VLAN 290): `10.30.90.0/24`, HCM CCTV (VLAN 295): `10.30.95.0/24`, HCM WiFi (VLAN 296): `10.30.96.0/24`
- Purpose: Đồng bộ 100% giữa tài liệu kiến trúc `topology.md`, kế hoạch thực thi và file cấu hình ACL thực tế.

### 3. File: `config/qos.yaml`
- Location: `dscp_classes`, `htb_classes`
- Change: Chuẩn hoá 5 lớp HTB (voip: 30%, database: 30%, web_app: 25%, mgmt_mon: 10%, bulk: 5%) theo đúng `topology.md` Section 4. Bổ sung class `mgmt_mon` (CS2, dscp=16).
- Purpose: Đảm bảo phân loại gói tin QoS và băng thông HTB khớp hoàn toàn với thiết kế tổng thể.

### 4. File: `topology/sites/datacenter.py`
- Location: `_configure_gw_interfaces()`
- Change: Thêm `gw_host.cmd('bridge vlan add dev br0 vid 2-4094 self 2>/dev/null')`.
- Purpose: Đảm bảo CPU interface của `br0` tiếp nhận đúng traffic 802.1Q tagged cho các sub-interface `br0.VLAN` trên `DC_SP_GW`, đồng bộ với `nhatrang.py`, `hcm.py` và `baoloc.py`.

### 5. File: `topology/enterprise_topo.py`
- Location: `print_summary()`
- Change: Sửa display hostnames từ `DC-DHCP01` thành `DC_DHCP01` (dấu `_`).
- Purpose: Đồng bộ tên hiển thị console với tên Mininet Host thực tế.

## 2026-10-08 00:45 +07:00 — FRR OSPF Isolated Sockets Fix & Test Documentation Synchronization

### 1. File: `controller/sdwan/sdwan_controller.py`
- Location: Imports (Line 24)
- Change: Bổ sung `from typing import Optional, Dict, List, Any`.
- Purpose: Khắc phục lỗi `NameError: name 'Optional' is not defined` khi khởi chạy standalone controller.

### 2. File: `topology/sites/baoloc.py`, `nhatrang.py`, `hcm.py`, `datacenter.py`
- Location: `start_frr_baoloc()`, `start_frr_nhatrang()`, `start_frr_hcm()`, `start_frr_datacenter()`
- Change: Thêm cấu hình socket và PID riêng cho từng router host tại `/tmp/frr_<HOSTNAME>` (`--vty_socket /tmp/frr_<HOSTNAME>`, `-z /tmp/frr_<HOSTNAME>/zserv.api`, `-i /tmp/frr_<HOSTNAME>/<daemon>.pid`). Bổ sung subnet `172.16.0.0/12` vào OSPF router config.
- Purpose: Sửa triệt để lỗi xung đột VTY/Zserv socket trên Linux root filesystem làm FRR daemon ở các site sau không chạy được $\Rightarrow$ Giúp OSPF hình thành quan hệ láng giềng (Full State) thành công giữa 4 site.

### 3. File: `tests/phase_checks/check_phase4.py`
- Location: `run_check()` (Line 106)
- Change: Cập nhật câu lệnh kiểm tra OSPF neighbor từ `vtysh` thành `vtysh --vty_socket /tmp/frr_{router.name}` với fallback về socket mặc định.
- Purpose: Đảm bảo script test tự động Phase 4 đọc đúng VTY socket độc lập của từng router.

### 4. File: `demochaytam.md`
- Location: Toàn bộ các Phase
- Change:
  - Chuẩn hóa tên thiết bị cho đúng 100% với topology thực tế (`BL_ADM01`, `BL_ADM02` thay vì `BL_ADMIN_PC01`).
  - Bổ sung lệnh test ping khác VLAN trong nội bộ từng site và giữa các site.
  - Bổ sung lệnh test 5 đường truyền WAN (MPLS, 5G, INET, VPN, LTE) và SD-WAN Path Steering (`/api/v1/sdwan/steer`).
  - Cập nhật tham số `--vty_socket /tmp/frr_<HOSTNAME>` cho các lệnh `vtysh` kiểm tra láng giềng OSPF.
- Purpose: Giúp việc kiểm thử thủ công trực quan, chính xác và không bị đứt quãng bởi lỗi lệch tên node hoặc xung đột socket.

## 2026-10-08 01:10 +07:00 — OSPF Passive-Interface & Redistribute Connected Fix

### Root Cause Analysis Recap

Phân tích nguyên nhân OSPF không học được routes liên site đã phát hiện 3 vấn đề còn tồn tại:

| # | Mức độ | Vấn đề | Ảnh hưởng |
|---|--------|--------|-----------|
| 1 | 🔴 HIGH | `network 10.x.0.0/16 area 0` match tất cả LAN sub-interfaces (`br0.110`, `br0.210`...) → OSPF gửi Hello packets vào LAN | Lãng phí bandwidth, có thể gây loop/conflict khi có DIST02 cùng chạy OSPF trên cùng VLAN |
| 2 | 🟠 MEDIUM | Thiếu `redistribute connected` → chỉ có trực tiếp connected subnets, các connected routes không được quảng bá đầy đủ sang site khác | Routes học được thiếu, ping liên site không ổn định |
| 3 | 🟡 LOW | OSPF Hello broadcast ra tất cả VLAN sub-interfaces không có neighbor → timer timeout liên tục | Log noise, tăng CPU trên router ảo |

### Fix áp dụng (4 files)

#### 1. File: `topology/sites/baoloc.py`
- Location: `start_frr_baoloc()`
- Change:
  - Thêm `passive-interface default` chặn Hello trên tất cả interfaces.
  - Thêm `no passive-interface <WAN_INTF>` mở Hello chỉ trên WAN interface (tự detect bằng `_w` trong tên).
  - Thêm `redistribute connected` quảng bá tất cả connected subnets qua OSPF.

#### 2. File: `topology/sites/nhatrang.py`
- Location: `start_frr_nhatrang()`
- Change: Tương tự baoloc — passive-interface default + no passive trên WAN + redistribute connected cho cả NT_DIST01 và NT_DIST02.

#### 3. File: `topology/sites/hcm.py`
- Location: `start_frr_hcm()`
- Change: Tương tự nhưng HCM_DIST01 có **tối đa 3 WAN interfaces** (`_w1`, `_w2`, `_w3`) nên dùng loop tìm tất cả WAN interfaces và mở `no passive-interface` cho từng cái.

#### 4. File: `topology/sites/datacenter.py`
- Location: `start_frr_datacenter()`
- Change: Tương tự baoloc — passive-interface default + no passive trên WAN + redistribute connected.

### Kết quả mong đợi

- OSPF Hello **chỉ** gửi qua WAN links (`192.168.x.x/30`) → hình thành adjacency nhanh hơn, ổn định hơn.
- `redistribute connected` đảm bảo LAN subnets (`10.10.0.0/16`, `10.20.0.0/16`, `10.30.0.0/16`, `10.100.0.0/16`) được quảng bá đầy đủ sang tất cả site.
- Không còn Hello timeout log noise trên LAN sub-interfaces.

### Đánh giá CT.md / QT.md

- **CT.md**: Không có mô tả chi tiết cấu hình FRR daemon-level → không cần cập nhật.
- **QT.md**: Phase 4 (dòng 201-223) chỉ mô tả kiến trúc OSPF Area 0 ở mức khái niệm → không cần cập nhật.
- **demochaytam.md**: Các lệnh test thủ công (`vtysh --vty_socket`, `show ip ospf neighbor`, `show ip ospf route`) vẫn đúng → không cần cập nhật.

## 2026-10-09 15:30 +07:00 — Fix AttributeError on NoneType topo.net & Check Phase 9 Initialization Guard

### 1. File: `topology/enterprise_topo.py`
- Location: `print_summary()`, `main()`
- Change:
  - Bổ sung kiểm tra an toàn `if topo is None or getattr(topo, 'net', None) is None:` trước khi truy cập `topo.net`.
  - Trong `main()`, kiểm tra giá trị `topo` ngay sau khi gọi `build_network()`. Nếu thất bại, xuất thông báo lỗi rõ ràng và thoát với `sys.exit(1)`.
- Purpose: Tránh văng ngoại lệ `AttributeError: 'NoneType' object has no attribute 'net'` khi `build_network()` gặp sự cố hoặc trả về `None`, giúp log ra lỗi gốc thực sự trong quá trình khởi tạo Mininet.

### 2. File: `tests/phase_checks/check_phase9.py`
- Location: `main()`
- Change:
  - Đưa `build_network(phase=9)` vào bên trong khối `try: ... except Exception as e: ... finally:`.
  - Bổ sung kiểm tra `if topo is None or getattr(topo, 'net', None) is None:` và trả về mã lỗi `1` nếu thất bại.
  - Bổ sung khối `except Exception as e:` xử lý ngoại lệ tập trung và in ra traceback chi tiết.
  - Trong khối `finally:`, sử dụng guard `if topo and getattr(topo, 'net', None):` để dừng `topo.net.stop()` an toàn.
- Purpose: Đảm bảo script kiểm thử tự động Phase 9 không bị crash đè bởi `AttributeError`, dừng tài nguyên mạng an toàn và ghi nhận log kết quả kiểm thử chuẩn xác.


## 2026-10-16 15:10 +07:00 — Xây dựng Toàn diện Phân hệ Tiêm Lỗi (Fault Injection Framework) & 12 Kịch bản Lỗi (F01–F12)

### 1. Bối cảnh & Căn cứ Kỹ thuật
- Tham chiếu theo đặc tả tại `Model_Research_and_Implementation_Plan.md`:
  - **Module 1 (Network & Fault Injector Module)**: Yêu cầu khả năng tiêm lỗi có kiểm soát trên mạng Mininet/SDN, xuất log sự cố có mốc thời gian ISO-8601 phục vụ gán nhãn Telemetry ($\phi_t$) và huấn luyện mô hình RL (PPO) / RCA (Random Forest).
  - **Mục 9 (Kịch bản tạo lỗi & Thu thập log)**: Chi tiết hóa 4 nhóm sự cố chính (`LINK_FAULT`, `PORT_FAULT`, `FLOW_ERROR / Congestion`, `FAUCET_RELOAD / Controller Overload`).
- Căn cứ theo danh mục 12 kịch bản được quy hoạch tại `fault_injection/__init__.py` (F01–F12).

### 2. Chi tiết các File Triển khai Mới & Cập nhật

#### A. Core Engine & API chung
- **File**: `fault_injection/fault_injector.py`
  - `BaseFaultScenario`: Lớp cơ sở trừu tượng chuẩn hóa vòng đời sự cố: `inject()`, `recover()`, `run(duration)`. Hỗ trợ cả `net` Mininet node execution, Linux shell subprocess và chế độ `dry_run` an toàn không cần quyền root.
  - `FaultInjector`: Bộ quản trị và điều phối trung tâm. Quản lý trạng thái kịch bản đang active, hỗ trợ tiêm lỗi đơn lẻ, chạy trọn gói theo thời gian hoặc khôi phục đồng loạt (`recover_all()`).
  - `FaultEventLog`: Cấu trúc ghi nhật ký sự cố có mốc thời gian chuẩn ISO-8601 UTC. Tự động ghi ra cả 2 định dạng: `data/logs/fault_log.json` (phục vụ Scraper/Dataset Labeler) và `data/logs/fault_log.txt` (phục vụ theo dõi nhân sự NOC/Audit).
  - CLI Interface: Cung cấp giao diện dòng lệnh mạnh mẽ hỗ trợ các tham số: `--scenario`, `--duration`, `--action` (`run`, `inject`, `recover`, `recover-all`), `--list`, `--dry-run`, `--all`, `--interval`.

#### B. 12 Kịch bản Lỗi Chuyên biệt (`fault_injection/scenarios/`)
1. **`f01_access_link_failure.py` (F01 - Access Link Failure | `PORT_FAULT`)**:
   - Ngắt kết nối uplink của Access switch (`NT_ACC01` $\leftrightarrow$ `NT_CORE` hoặc interface `NT_ACC01-eth1`).
   - Tác động: Gây mất kết nối người dùng cục bộ, kiểm tra khả năng phát hiện cổng down ($p_{down}$).
2. **`f02_distribution_failure.py` (F02 - Distribution Failure | `LINK_FAULT`)**:
   - Ngắt kết nối Trunk Distribution Switch chính (`NT_DIST01` $\leftrightarrow$ `NT_CORE`).
   - Tác động: Kích hoạt cơ chế VRRP Failover (Keepalived) sang `DIST02` và OSPF tái hội tụ.
3. **`f03_ospf_failure.py` (F03 - OSPF Neighbor Failure | `ROUTING_FAULT`)**:
   - Chặn lưu lượng OSPF Hello (IP Protocol 89) bằng iptables trên router `NT_DIST01`.
   - Tác động: Hết hạn Dead Interval, ngắt quan hệ láng giềng OSPF, làm đứt đoạn định tuyến liên site.
4. **`f04_mpls_down.py` (F04 - WAN MPLS Down | `LINK_FAULT`)**:
   - Hạ giao diện WAN MPLS (`ntd1_mpls_g`, `blgw_mpls_g`) hoặc ngắt switch `WAN_MPLS`.
   - Tác động: Làm mất đường truyền cao cấp nhất (cost 10, SLA premium), kích hoạt SD-WAN Controller điều phối lưu lượng sang các đường dự phòng.
5. **`f05_internet_down.py` (F05 - WAN Internet Down | `LINK_FAULT`)**:
   - Hạ cổng mạng kết nối Internet broadband (`hcmd_inet_g`, `blgw_inet_g`).
   - Tác động: Gián đoạn truy cập Web/App thông thường, chuyển hướng lưu lượng sang LTE/MPLS.
6. **`f06_lte_down.py` (F06 - WAN LTE Down | `LINK_FAULT`)**:
   - Hạ giao diện WAN LTE dự phòng (`blgw_lte_g`, `ntd1_lte_g`).
   - Tác động: Mất kênh truyền backup cuối cùng của các Site chi nhánh.
7. **`f07_5g_degradation.py` (F07 - 5G Path Degradation | `WAN_DEGRADATION`)**:
   - Can thiệp `tc netem` bơm trễ 180ms (jitter $\pm$40ms) và packet loss 15% trên đường 5G NR.
   - Tác động: Kiểm thử khả năng phát hiện suy giảm QoS mềm (Soft Warning) trước khi xảy ra timeout kết nối.
8. **`f08_vpn_failure.py` (F08 - VPN Failure | `VPN_FAULT`)**:
   - Chặn các gói tin IPSec/IKE (UDP 500, UDP 4500, protocol ESP 50) trên Gateway DC và HCM.
   - Tác động: Làm sập đường hầm bảo mật VPN giữa các chi nhánh về Trung tâm dữ liệu.
9. **`f09_wan_congestion.py` (F09 - WAN Congestion | `FLOW_ERROR`)**:
   - Phát luồng lưu lượng UDP flood dung lượng lớn (`iperf3 -u -b 100M`) hoặc thắt hàng đợi `tc tbf` xuống 1Mbps.
   - Tác động: Gây tràn bộ đệm (Bufferbloat), tăng đột biến độ trễ hàng đợi và rớt gói diện rộng trên WAN.
10. **`f10_voip_degradation.py` (F10 - VoIP Quality Degradation | `QOS_DEGRADATION`)**:
    - Bơm jitter cao (80ms), trễ 120ms và rớt gói 6% trên luồng thoại RTP (UDP 10000–20000).
    - Tác động: Làm suy giảm điểm chất lượng MOS < 3.0, kích hoạt phản ứng của QoS Priority Queue và Policy Engine.
11. **`f11_server_failure.py` (F11 - Server Failure | `SERVER_FAULT`)**:
    - Hạ cổng mạng `DC_WEB01-eth1` và dừng tiến trình HTTP server trên `DC_WEB01`.
    - Tác động: Kiểm thử cơ chế Health-check của HAProxy Load Balancer và chuyển hướng dịch vụ sang `DC_WEB02`.
12. **`f12_multi_metric_anomaly.py` (F12 - Multi-Metric Anomaly | `MULTI_METRIC_ANOMALY`)**:
    - Kích hoạt đồng thời suy giảm WAN 5G + tắc nghẽn luồng + gửi tín hiệu reload Faucet Controller (`pkill -HUP faucet`) + stress tải CPU.
    - Tác động: Kiểm thử sức bền và năng lực phân loại đa triệu chứng của mô hình AI RCA & PPO RL Agent.

#### C. Đóng gói & Re-export Module
- **File**: `fault_injection/scenarios/__init__.py`: Xuất `ALL_SCENARIOS` (Dictionary 12 kịch bản) và hàm tiện ích `get_scenario_by_id(scenario_id)`.
- **File**: `fault_injection/__init__.py`: Giữ nguyên khối chú thích quy hoạch 12 kịch bản ban đầu, đồng thời xuất đầy đủ các class `FaultInjector`, `BaseFaultScenario`, `FaultEventLog` và toàn bộ 12 scenarios.

### 3. Kết Quả Kiểm Thử & Nghiệm Thu
- Chạy lệnh liệt kê: `python -m fault_injection.fault_injector --list` thành công, hiển thị đầy đủ thông số 12 kịch bản.
- Chạy thử nghiệm tuần tự toàn bộ 12 kịch bản ở chế độ `--dry-run`: 100% kịch bản thực thi đúng quy trình `inject` $\rightarrow$ duy trì $\rightarrow$ `recover` mà không gặp lỗi cú pháp hay ngoại lệ.
- Kiểm tra dữ liệu log: Tự động ghi nhận đầy đủ 26 sự kiện (INJECT & RECOVER) có mốc thời gian chuẩn ISO-8601 vào `data/logs/fault_log.json` và `data/logs/fault_log.txt`.

## 2026-10-23 00:45 +07:00 — Xây Dựng Phân Hệ Thu Thập Telemetry (`ai_engine/telemetry`), Trích Xuất State Vector & Kiểm Thử Toàn Diện

### 1. Bối Cảnh & Mục Tiêu Triển Khai
- Căn cứ theo tài liệu đặc tả `ke_hoach_thu_thap_telemetry.md` và kế hoạch nghiên cứu `Model_Research_and_Implementation_Plan.md` (Module 2: Telemetry Collector & State-Vector Synthesizer).
- Mục tiêu: Thiết lập đường ống (pipeline) tự động cào số liệu định kỳ mỗi 10 giây từ Prometheus Server, trích xuất 8 chỉ số trạng thái mạng thô, bóc tách nhãn sự cố $\phi_t$ từ phân hệ tiêm lỗi (`fault_injection`), phân tích Context Metadata lỗi chi tiết tầng micro và tổng hợp thành Vector trạng thái 8 chiều $s_t \in \mathbb{R}^8$.
- Đầu ra chuẩn hóa: Tập dữ liệu huấn luyện `data/sdn_telemetry_dataset.csv` gồm 15 thuộc tính và nhật ký thô `data/telemetry_log.jsonl`.

### 2. Chi Tiết Các File Đã Cài Đặt Trong Phân Hệ `ai_engine/telemetry/`

#### A. `ai_engine/telemetry/prometheus_client.py` (Lớp Wrapper Prometheus HTTP API)
- **Nhiệm vụ**: Kết nối và gửi truy vấn PromQL tới Prometheus Server qua HTTP API (`/api/v1/query`).
- **Các hàm & Tính năng chính**:
  - `is_reachable()`: Kiểm tra máy chủ Prometheus có đang hoạt động hay không qua endpoint `/-/healthy` với timeout ngắn (2 giây).
  - `query_instant(promql)`: Truy vấn một giá trị số thực tức thời từ Prometheus, tự động lưu giá trị thành công vào bộ đệm cache `_last_known`.
  - `query_with_fallback(promql, fallback)`: Cơ chế truy vấn chịu lỗi (fault-tolerant). Khi mất kết nối hoặc query rỗng, hàm hỗ trợ fallback linh hoạt: trả về giá trị cào thành công gần nhất (`fallback="last_known"`) hoặc giá trị mặc định được cấu hình.
  - `query_vector(promql, label_filter)`: Lấy toàn bộ vector nhãn và giá trị của các metric per-datapath phục vụ bóc tách vị trí sự cố.

#### B. `ai_engine/telemetry/context_metadata_parser.py` (Bộ Phân Tích Context Metadata Tầng Micro)
- **Nhiệm vụ**: Bóc tách siêu dữ liệu định vị lỗi phần cứng/luồng từ các metric per-datapath trên Prometheus.
- **Cấu trúc dữ liệu `ContextMetadata`**:
  - `target_dpid`: Tên hoặc ID switch xảy ra sự cố (ví dụ: `NT_CORE`, `0x1`).
  - `target_port`: Số hiệu cổng mạng gặp sự cố (chuyển đổi chuẩn hóa từ chuỗi như `eth1` $\rightarrow$ số nguyên `1`).
  - `error_cookie`: Mã nhận diện luồng OpenFlow bị lỗi (ví dụ: `0x10a`).
  - `disconnected_dpids`: Danh sách ID các switch bị ngắt kết nối với Controller.
- **Phương thức `parse()`**:
  - Quét `of_port_status == 0` để tìm switch và cổng bị hạ (Port Down).
  - Quét `of_errors_total > 0` để tìm cookie của luồng OpenFlow bị xung đột/từ chối.
  - Quét `faucet_dp_status == 0` để phát hiện switch bị mất kết nối OpenFlow.

#### C. `ai_engine/telemetry/fault_log_reader.py` (Bộ Đọc & Đồng Bộ Nhãn Sự Cố)
- **Nhiệm vụ**: Đọc log sự cố do `fault_injection` phát sinh để đồng bộ nhãn $\phi_t$ và thời lượng tồn tại lỗi `duration_seconds` vào dòng telemetry tương ứng.
- **Khả năng tương thích**:
  - Hỗ trợ đọc tệp JSONL `data/logs/fault_log.json`: Đọc ngược từ dòng cuối cùng (sự kiện mới nhất), tính toán thời gian trôi qua `duration = now - timestamp` (UTC ISO-8601) và tự động nhận diện kết thúc lỗi nếu đã hết `duration_sec`.
  - Hỗ trợ đọc tệp Text `data/logs/fault_log.txt`: Phân tích các dòng log pipe-delimited (`FAULT_START`, `FAULT_END`) hoặc nhãn tag (`[INJECT]`, `[RECOVER]`).
- **Chuẩn hóa nhãn**: Ánh xạ phân loại kịch bản sang tập nhãn chuẩn $\phi_t \in \{\text{LINK\_FAULT}, \text{PORT\_FAULT}, \text{FLOW\_ERROR}, \text{FAUCET\_RELOAD}, \text{SOFT\_WARNING}, \text{TEMP\_WARNING}, \text{NONE}\}$.

#### D. `ai_engine/telemetry/vector_assembler.py` (Lắp Ráp & Thẩm Định State Vector 8D)
- **Nhiệm vụ**: Tổng hợp 8 giá trị đo lường thành `StateVector` ($s_t \in \mathbb{R}^8$):
  - `ccpu` (Counter - CPU seconds của controller).
  - `cres_mem` (Gauge - RAM Resident của controller).
  - `cvirt_mem` (Gauge - RAM Virtual của controller).
  - `fsent` (Counter - OpenFlow messages sent).
  - `ferr` (Counter - OpenFlow errors).
  - `fconn` (Gauge - Datapath connected count).
  - `fdisc` (Counter - Datapath disconnections total).
  - `pdown` (Gauge - Ports down total).
- **Làm sạch & Đánh giá chất lượng dữ liệu**:
  - `sanitize()`: Tự động loại bỏ các giá trị không hợp lệ (`NaN`, `Inf`, số âm $<0$) về giá trị mặc định an toàn.
  - Đánh giá cờ chất lượng `data_quality`:
    - `OK`: Thu thập đầy đủ 8 chỉ số hợp lệ.
    - `PARTIAL`: Thiếu $\le 2$ chỉ số (được bổ sung từ fallback).
    - `STALE`: Thiếu $3 - 5$ chỉ số, phải dùng giá trị cũ `_last_known`.
    - `MISSING`: Thiếu $>5$ chỉ số hoặc Prometheus server ngoại tuyến.
    - `INVALID`: Chứa giá trị lỗi NaN, Inf hoặc âm.
  - `is_healthy()`: Kiểm tra trạng thái bình thường khi $\text{ferr} = 0, \text{fdisc} = 0, \text{pdown} = 0$.

#### E. `ai_engine/telemetry/collector.py` (Bộ Điều Phối Thu Thập Dữ Liệu Tập Trung)
- **Nhiệm vụ**: Điều phối toàn bộ quy trình thu thập telemetry theo chu kỳ scrape định kỳ (10 giây).
- **Hàm `collect_once()`**:
  1. Kiểm tra trạng thái kết nối máy chủ Prometheus.
  2. Truy vấn đồng thời 8 chỉ số trạng thái mạng dựa trên câu lệnh PromQL trong cấu hình.
  3. Lắp ráp vector $s_t$ và đánh giá chất lượng `data_quality` qua `VectorAssembler`.
  4. Đọc nhãn lỗi $\phi_t$ và thời gian tồn tại qua `FaultLogReader`.
  5. Trích xuất metadata vị trí lỗi qua `ContextMetadataParser`.
  6. Ghi dòng dữ liệu 15 cột vào CSV `data/sdn_telemetry_dataset.csv`.
  7. Ghi bản ghi JSON thô vào `data/telemetry_log.jsonl`.
- **Hàm `run(max_cycles, interval)`**: Vòng lặp thu thập tự động, bù trừ thời gian trôi của chu kỳ lấy mẫu và hiển thị thông tin trực quan ra console.

#### F. `ai_engine/telemetry/__init__.py` (Khởi Tạo & Re-export Package)
- Đóng gói và xuất toàn bộ các lớp, hằng số công khai: `PrometheusClient`, `FaultLogReader`, `ContextMetadataParser`, `ContextMetadata`, `VectorAssembler`, `StateVector`, `TelemetryCollector`, `STANDARD_FAULT_LABELS`, `CSV_HEADER`.

---

### 3. Chi Tiết Các Tệp Cấu Hình & Công Cụ Hỗ Trợ Đã Cài Đặt

#### A. Điểm Vào Thực Thi & Cấu Hình
- **`telemetry_collector.py` (Thư mục gốc `src/`)**:
  - Script dòng lệnh (CLI) chính để khởi chạy tiến trình thu thập.
  - Hỗ trợ các tham số: `--config <path>`, `--cycles <N>`, `--interval <seconds>`. Tự động cấu hình chuẩn UTF-8 cho console.
- **`config/telemetry_config.yaml`**:
  - Khai báo chu kỳ cào `interval_seconds: 10`, timeout 5 giây.
  - Khai báo URL Prometheus (`http://localhost:9091` hoặc `9090`).
  - Định nghĩa chi tiết PromQL cho 8 chỉ số trạng thái, kiểu dữ liệu (counter/gauge) và chiến lược fallback.
  - Định cấu hình đường dẫn tệp dataset CSV, file log thô, log sự cố và các truy vấn context metadata.
- **`config/prometheus.yml`**:
  - Cấu hình server Prometheus với chu kỳ scrape toàn hệ thống là 10 giây.
  - Thiết lập các job giám sát:
    - `faucet_sdn` (cổng 9302): CPU và RAM tiến trình Faucet.
    - `gauge_sdn` (cổng 9303): Số liệu datapath, cổng mạng và luồng OpenFlow.
    - `system_node` (cổng 9100): Sức khỏe node máy chủ.
    - `sdwan_controller` (cổng 7070): Chỉ số chất lượng đường truyền SD-WAN.

#### B. Phân Hệ Exporter Giám Sát Mặt Phẳng Dữ Liệu
- **`controller/sdn/telemetry_exporter.py`**:
  - HTTP exporter đa cổng phục vụ cào dữ liệu Prometheus theo chuẩn `/metrics`:
    - Port `9302` (Faucet Exporter): Trích xuất tài nguyên CPU/RAM hệ thống qua `/proc/self/statm` hoặc process time.
    - Port `9303` (Gauge Exporter): Tự động quét cấu trúc mạng Mininet qua hệ thống `/sys/class/net` và OVS, xác định trạng thái cổng switch `<switch>-eth<port>` (`operstate`), tính toán số switch kết nối (`fconn`), số cổng bị hạ (`pdown`), và xuất các metric per-datapath (`of_port_status`, `faucet_dp_status`).
    - Port `9100`: Giả lập Node Exporter.

---

### 4. Kết Quả Kiểm Thử & Nghiệm Thu Thử Nghiệm

#### A. Kiểm Thử Đơn Vị (`tests/test_telemetry.py`)
- Xây dựng bộ 11 test case kiểm thử toàn diện toàn bộ module:
  - `TestPrometheusClient`: Kiểm tra truy vấn instant thành công, truy vấn rỗng, cơ chế fallback `last_known`.
  - `TestFaultLogReader`: Kiểm tra đọc lỗi active, kiểm tra trạng thái mạng đã khôi phục (`RECOVER`), kiểm tra hết hạn thời gian duration.
  - `TestContextMetadataParser`: Kiểm tra bóc tách `target_dpid` & `target_port` khi có cổng down, kiểm tra bóc tách `error_cookie` khi có OpenFlow error.
  - `TestVectorAssembler`: Kiểm tra lắp ghép vector hợp lệ, kiểm tra khử lỗi NaN/Inf/âm, kiểm tra xếp hạng chất lượng dữ liệu (`OK`, `INVALID`, `PARTIAL`, `MISSING`).
  - `TestTelemetryCollector`: Kiểm tra chu kỳ cào mẫu tích hợp và xuất file CSV đúng chuẩn 15 cột.
- **Kết quả thực thi**: `Ran 11 tests in 0.027s - OK` (100% test case vượt qua).

#### B. Công Cụ Chẩn Đoán Đường Ống (`tests/check_telemetry_pipeline.py`)
- Script chẩn đoán nhanh toàn bộ đường ống thu thập:
  - Kiểm tra kết nối HTTP tới 4 Exporter (`:9302`, `:9303`, `:9100`, `:7070`).
  - Kiểm tra trạng thái máy chủ Prometheus (`:9090/-/healthy`).
  - Tự động truy vấn danh sách Scrape Targets từ API Prometheus (`/api/v1/targets`) và in trạng thái UP/DOWN của từng job.


