# HƯỚNG DẪN KHỞI CHẠY VÀ KIỂM THỬ HỆ THỐNG MẠNG DOANH NGHIỆP THEO TỪNG PHASE

> **Dự án:** Kiến trúc Mạng Doanh nghiệp Tự Phục hồi Sử dụng SD-WAN và Cơ chế Khôi phục Sự cố Thông minh  
> **Cập nhật:** Hướng dẫn khởi chạy và lệnh kiểm thử chi tiết từ Phase 0 đến Phase 14.

---

## 1. DỌN DẸP HỆ THỐNG & CHUẨN BỊ (LÀM TRƯỚC MỖI LẦN TEST)

Trước khi chạy bất kỳ Phase nào (hoặc khi đổi Phase), hãy dọn dẹp các tiến trình cũ để tránh kẹt interface:

```bash
# 1. Dọn dẹp môi trường Mininet cũ
sudo mn -c

# 2. Xóa các dịch vụ ngầm còn tồn đọng
sudo killall -9 dnsmasq chronyd keepalived zebra ospfd haproxy 2>/dev/null; true

# 3. Restart Open vSwitch daemon
sudo systemctl restart openvswitch-switch
```

---

## 2. QUY TRÌNH KHỞI CHẠY VÀ KIỂM THỬ CHI TIẾT THEO TỪNG PHASE

> **Lưu ý:** 
> - **Terminal 1:** Dùng để chạy lệnh khởi tạo Topology (`sudo python3 src/topology/enterprise_topo.py --phase N`).
> - **Terminal 2:** Mở cửa sổ terminal Linux mới để chạy script test tự động (`sudo python3 tests/phase_checks/check_phaseX.py`).
> - **Mininet CLI (`mininet>`):** Thực thi lệnh kiểm thử thủ công ngay trong Terminal 1 sau khi Topo đã khởi chạy thành công.

---

### Phase 0: Kiểm Tra Môi Trường Phần Mềm

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 0
  ```

---

### Phase 1: Dựng Topology Vật Lý L2 (Physical Topology & Links)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 1
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase1.py
  ```

- **Mininet CLI (Test Thủ Công):**
  ```bash
  # Kiểm tra liên kết vật lý cơ bản giữa các switch/router
  mininet> net
  mininet> links
  ```

---

### Phase 2: Cấu Hình VLAN & Sub-interfaces (VLAN Segmentation & IP)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 2
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase2.py
  ```

- **Mininet CLI (Test Thủ Công):**
  ```bash
  # Ping nội bộ cùng VLAN tại Bảo Lộc (VLAN 10)
  mininet> BL_ADM01 ping -c 3 BL_ADM02

  # Ping nội bộ cùng VLAN tại Nha Trang (VLAN 110)
  mininet> NT_ADM01 ping -c 3 NT_ADM02

  # Ping nội bộ cùng VLAN tại HCM (VLAN 210)
  mininet> HCM_ADM01 ping -c 3 HCM_ADM02
  ```

---

### Phase 3: Switching L2 & Spanning Tree Protocol (STP)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 3
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase3.py
  ```

- **Mininet CLI (Test Thủ Công):**
  ```bash
  # Kiểm tra trạng thái vlan filtering & STP trên Linux bridge
  mininet> dpctl show
  ```

---

### Phase 4: Định Tuyến OSPF Liên Site (Inter-Site Routing - FRRouting)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 4
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase4.py
  ```

- **Mininet CLI (Test Thủ Công - Định Tuyến Khác VLAN, Inter-Site & Check OSPF Neighbors):**
  ```bash
  # 1. Ping KHÁC VLAN nội bộ tại Bảo Lộc (Admin VLAN 10 -> IoT Printer VLAN 30)
  mininet> BL_ADM01 ping -c 3 10.10.30.11

  # 2. Ping KHÁC VLAN nội bộ tại Nha Trang (Admin VLAN 110 -> HR VLAN 140)
  mininet> NT_ADM01 ping -c 3 10.20.40.11

  # 3. Ping KHÁC VLAN nội bộ tại HCM (Admin VLAN 210 -> Technical VLAN 270)
  mininet> HCM_ADM01 ping -c 3 10.30.70.11

  # 4. Ping KHÁC VLAN liên site (Bảo Lộc Admin VLAN 10 -> Nha Trang HR VLAN 140)
  mininet> BL_ADM01 ping -c 3 10.20.40.11

  # 5. Ping từ HCM Admin (VLAN 210) tới Server Data Center (VLAN 310 - DC_WEB01)
  mininet> HCM_ADM01 ping -c 3 10.100.10.11

  # 6. SHOW KIỂM TRA LÁNG GIỀNG OSPF (OSPF Neighbors - Trạng thái phải là "Full"):
  mininet> BL_GW vtysh --vty_socket /tmp/frr_BL_GW -c "show ip ospf neighbor"
  mininet> NT_DIST01 vtysh --vty_socket /tmp/frr_NT_DIST01 -c "show ip ospf neighbor"
  mininet> HCM_DIST01 vtysh --vty_socket /tmp/frr_HCM_DIST01 -c "show ip ospf neighbor"
  mininet> DC_SP_GW vtysh --vty_socket /tmp/frr_DC_SP_GW -c "show ip ospf neighbor"

  # 7. SHOW BẢNG ĐỊNH TUYẾN OSPF HỌC ĐƯỢC TRÊN DỊCH VỤ FRR:
  mininet> BL_GW vtysh --vty_socket /tmp/frr_BL_GW -c "show ip ospf route"
  mininet> HCM_DIST01 vtysh --vty_socket /tmp/frr_HCM_DIST01 -c "show ip ospf route"

  # 8. SHOW BẢNG ĐỊNH TUYẾN KERNEL TRÊN ROUTER:
  mininet> BL_GW ip route
  mininet> HCM_DIST01 ip route
  ```

---

### Phase 5: Dự Phòng Gateway VRRP (Keepalived Failover)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 5
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase5.py
  ```

- **Mininet CLI (Test Thủ Công Failover):**
  ```bash
  # 1. Kiểm tra Router chính NT_DIST01 nắm Virtual IP 10.20.10.1
  mininet> NT_DIST01 ip addr show dev NT_DIST01-eth0.110

  # 2. Tắt interface WAN/LAN của router chính để tạo sự cố
  mininet> NT_DIST01 ip link set dev NT_DIST01-eth0 down

  # 3. Kiểm tra Router phụ NT_DIST02 tự động nắm Virtual IP trong < 3s
  mininet> NT_DIST02 ip addr show dev NT_DIST02-eth0.110

  # 4. Phục hồi router chính
  mininet> NT_DIST01 ip link set dev NT_DIST01-eth0 up
  ```

---

### Phase 6: Dịch Vụ Tập Trung (DHCP HA, DNSmasq, Chrony NTP)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 6
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase6.py
  ```

- **Mininet CLI (Test Thủ Công DNS/NTP):**
  ```bash
  # Phân giải tên miền www.enterprise.local từ máy HCM
  mininet> HCM_ADM01 dig @10.100.40.11 www.enterprise.local +short
  # Kết quả kỳ vọng: 10.100.10.11

  # Phân giải app.enterprise.local từ máy Nha Trang
  mininet> NT_ADM01 dig @10.100.40.11 app.enterprise.local +short
  # Kết quả kỳ vọng: 10.100.20.11
  ```

---

### Phase 7: Tường Lửa & Phân Vùng Bảo Mật (ACL Rules)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 7
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase7.py
  ```

- **Mininet CLI (Test Thủ Công Chặn IoT/CCTV):**
  ```bash
  # Kiểm tra IoT Printer (BL_PRN01: 10.10.30.11) ping PC User (BL_ADM01: 10.10.10.11)
  mininet> BL_PRN01 ping -c 3 10.10.10.11
  # Kết quả kỳ vọng: 100% packet loss (ACL DROP theo acl_rules.yaml)
  ```

---

### Phase 8: HAProxy Load Balancer & Web Cluster Data Center

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 8
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase8.py
  ```

- **Mininet CLI (Test Thủ Công Load Balancing):**
  ```bash
  # Gửi HTTP request tới VIP HAProxy (10.100.20.10) từ HCM
  mininet> HCM_ADM01 curl -s http://10.100.20.10
  # Trả về trang Web từ DC_WEB01 hoặc DC_WEB02
  ```

---

### Phase 9: Quality of Service (QoS) & WAN 5-Path Transport (MPLS, 5G, INET, VPN, LTE)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 9
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase9.py
  ```

- **Mininet CLI (Test Thủ Công 5 Đường Truyền WAN - MPLS / 5G / INET / VPN / LTE):**
  ```bash
  # 1. Ping kiểm tra độ trễ (RTT) 5 đường WAN từ BL_GW tới DC_SP_GW (172.16.x.4):
  mininet> BL_GW ping -c 3 172.16.10.4    # Path MPLS   (Delay ~20ms, Leased Line)
  mininet> BL_GW ping -c 3 172.16.40.4    # Path 5G     (Delay ~15ms, Băng thông cao)
  mininet> BL_GW ping -c 3 172.16.20.4    # Path INET   (Delay ~40ms, Broadband)
  mininet> BL_GW ping -c 3 172.16.50.4    # Path VPN    (Delay ~50ms, IPSec)
  mininet> BL_GW ping -c 3 172.16.30.4    # Path LTE 4G (Delay ~60ms, Backup)

  # 2. Mô phỏng ngắt kết nối đường MPLS để kiểm tra chuyển mạch WAN:
  mininet> BL_GW ip link set dev blgw_mpls_g down
  mininet> BL_GW ping -c 3 172.16.40.4    # Kiểm tra đường 5G vẫn hoạt động tốt

  # 3. Khôi phục lại đường MPLS:
  mininet> BL_GW ip link set dev blgw_mpls_g up
  ```

---

### Phase 10: Python SD-WAN Controller & Dynamic Path Selection

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 10
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase10.py
  ```

- **Mininet CLI / Terminal (Test REST API & Force Path Steering):**
  ```bash
  # 1. Kiểm tra trạng thái tổng quan các đường truyền SD-WAN (Port 7070)
  curl http://localhost:7070/api/v1/sdwan/status

  # 2. Xem danh sách chỉ số chất lượng đường truyền (RTT, Jitter, Packet Loss)
  curl http://localhost:7070/api/v1/sdwan/paths

  # 3. Ép toàn bộ Traffic điều hướng qua đường 5G (FIVEG):
  curl -X POST http://localhost:7070/api/v1/sdwan/steer -H "Content-Type: application/json" -d '{"path": "FIVEG"}'

  # 4. Ép toàn bộ Traffic điều hướng trở lại đường MPLS:
  curl -X POST http://localhost:7070/api/v1/sdwan/steer -H "Content-Type: application/json" -d '{"path": "MPLS"}'

  # 5. Kiểm tra traceroute đường đi thực tế từ HCM đến Data Center Web Server
  mininet> HCM_ADM01 traceroute 10.100.10.11
  ```

---

### Phase 11: Cơ Chế Tự Phục Hồi & Chuyển Mạch Sự Cố (Self-Healing Failover)

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 11
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase11.py
  ```

---

### Phase 14: Điều Khiển SDN Faucet Controller & OpenFlow

- **Terminal 1 (Chạy Topo):**
  ```bash
  sudo python3 src/topology/enterprise_topo.py --phase 14
  ```

- **Terminal 2 (Test Tự Động):**
  ```bash
  cd src
  sudo python3 tests/phase_checks/check_phase14.py
  ```

---

## 3. KHỞI CHẠY TOÀN BỘ HỆ THỐNG (FULL ENTERPRISE SYSTEM)

Khởi chạy đồng thời toàn bộ từ Phase 1 đến Phase 14 (Chế độ đầy đủ dịch vụ):

```bash
# 1. Chạy full topology có giao diện Mininet CLI
sudo python3 src/topology/enterprise_topo.py

# 2. Chạy full topology + Tự động PingAll kiểm tra toàn bộ rồi thoát
sudo python3 src/topology/enterprise_topo.py --test-pingall

# 3. Chạy full topology ở chế độ ẩn CLI (Automated Scripting Mode)
sudo python3 src/topology/enterprise_topo.py --no-cli
```

---

## 4. XỬ LÝ LỖI THƯỜNG GẶP (TROUBLESHOOTING)

### 4.1 Lỗi "Exception: Error creating interface" hoặc kẹt OVS Bridge
```bash
sudo mn -c
sudo killall -9 dnsmasq chronyd keepalived zebra ospfd haproxy 2>/dev/null; true
sudo systemctl restart openvswitch-switch
```

### 4.2 Lỗi thiếu Kernel Module VLAN
```bash
sudo modprobe 8021q
```
