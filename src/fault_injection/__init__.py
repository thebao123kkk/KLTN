# fault_injection/
# Scripts gây lỗi có kiểm soát để huấn luyện ML và đánh giá hệ thống.
# - fault_injector.py   : API chung để inject fault
# - scenarios/          : 12 kịch bản lỗi (F01–F12)
#   - f01_access_link_failure.py
#   - f02_distribution_failure.py
#   - f03_ospf_failure.py
#   - f04_mpls_down.py
#   - f05_internet_down.py
#   - f06_lte_down.py
#   - f07_5g_degradation.py
#   - f08_vpn_failure.py
#   - f09_wan_congestion.py
#   - f10_voip_degradation.py
#   - f11_server_failure.py
#   - f12_multi_metric_anomaly.py
