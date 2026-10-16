# Đề tài số 7

## 7.1 Tên đề tài
- **Tên TV:** Mạng doanh nghiệp tự phục hồi sử dụng SD-WAN và cơ chế khôi phục sự cố thông minh
- **Tên TA:** Self-Healing Enterprise Network using SD-WAN and Intelligent Failure Recovery

## 7.2 Nội dung
- Phát hiện lỗi.
- Phân tích nguyên nhân gốc (Root Cause Analysis).
- Khôi phục SDN (LAN domain).
- Chuyển đổi dự phòng SD-WAN (WAN domain).
- Quyết định bằng AI (PPO Reinforcement Learning + Proactive/Reactive Self-Healing).

## 7.3 Mục tiêu
- Phát hiện lỗi tự động (Anomaly Detection).
- Khôi phục tự động (Self-Healing Loop).
- Giảm downtime (MTTR < 30s).
- Duy trì dịch vụ (Service Continuity).
- Dự đoán sự cố trước khi xảy ra (Proactive/Predictive Healing).

## 7.4 Đánh giá
- Detection Time
- Recovery Time (MTTR)
- Packet Recovery Rate
- Network Availability
- Recovery Success Rate
- QoE Score (VoIP/Video quality)

**Ngành:** Mạng máy tính và truyền thông dữ liệu  
**Hướng đề tài:** Mạng cảm biến và Thiết kế xây dựng mạng

## 7.5 Bộ mô hình so sánh
- Flat Network (Bảo Lộc baseline)
- Three-Tier (Nha Trang / HCM)
- HSRP/VRRP (Gateway redundancy)
- VXLAN EVPN (Data Center)
- SDN Recovery (Faucet + OpenFlow)
- **Đề xuất: Self-Healing (AI + SDN + SD-WAN)**

## 7.6 Tiến độ hiện tại (cập nhật 2026-09-26)

| Phase | Nội dung | Trạng thái |
| --- | --- | --- |
| 0 | Chuẩn hoá môi trường | ✅ Hoàn thành |
| 1 | Build Enterprise Topology | ✅ Hoàn thành |
| 2 | VLAN + IP Addressing | ✅ Hoàn thành |
| 3 | L2 Switching + RSTP | ✅ Hoàn thành |
| 4 | L3 Routing + OSPF | ✅ Hoàn thành |
| 5 | Gateway Redundancy (VRRP) | ✅ Hoàn thành |
| 6 | DHCP + DNS + NTP | ✅ Hoàn thành |
| 7-21 | ACL, DC, SD-WAN, AI, ... | 🔲 Chưa làm |

### Các vấn đề đã sửa (tính đến Phase 6)
- **BL-GW interface naming:** Sửa `BL-GW-eth0` (dấu `-`) → `{gw_host.name}-eth0` và khởi động FRR per-namespace.
- **NT/HCM DIST01/02:** Chuyển từ OVS Switch → Mininet Host Router để hỗ trợ sub-interface VLAN và OSPF/VRRP namespace.
- **DC_SP_GW:** Đồng bộ cú pháp đặt interface và FRR namespace.
- **Keepalived config:** Bind VIP đúng sub-interface VLAN thực tế.
- **Linux Bridge VLAN Filtering:** Kích hoạt `vlan_filtering 1` + `modprobe 8021q` để 802.1Q tags đi qua bridge.
- **OVS Controller:** Chuyển sang `controller=None` để OVS hoạt động L2 Standalone, tránh gói tin ARP/Ping bị giữ.
- **STP/RSTP:** Giảm forward-delay xuống 4s, bật `stp_state 1` trên Linux bridge để tránh broadcast storm.
- **Inter-VLAN Routing:** Fix 100% packet loss trên toàn bộ 4 site.