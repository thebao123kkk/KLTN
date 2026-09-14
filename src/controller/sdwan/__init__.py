# controller/sdwan/
# SD-WAN Controller tự viết bằng Python (thay thế GNS3/Viptela).
# - sdwan_controller.py : vòng lặp chính, theo dõi trạng thái 5 path
# - path_selector.py    : thuật toán chọn path tốt nhất (quality-aware)
# - policy_engine.py    : áp dụng traffic steering policy (VoIP→MPLS, Web→Internet...)
# - tunnel_manager.py   : quản lý OvS tunnel giữa các site
