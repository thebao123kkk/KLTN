"""
fault_injection/scenarios/__init__.py
Registry tập trung cho 12 kịch bản lỗi (F01–F12).
"""

from typing import Dict, Optional, Type
from fault_injection.fault_injector import BaseFaultScenario

from fault_injection.scenarios.f01_access_link_failure import AccessLinkFailureScenario
from fault_injection.scenarios.f02_distribution_failure import DistributionFailureScenario
from fault_injection.scenarios.f03_ospf_failure import OSPFFailureScenario
from fault_injection.scenarios.f04_mpls_down import MPLSDownScenario
from fault_injection.scenarios.f05_internet_down import InternetDownScenario
from fault_injection.scenarios.f06_lte_down import LTEDownScenario
from fault_injection.scenarios.f07_5g_degradation import FiveGDegradationScenario
from fault_injection.scenarios.f08_vpn_failure import VPNFailureScenario
from fault_injection.scenarios.f09_wan_congestion import WANCongestionScenario
from fault_injection.scenarios.f10_voip_degradation import VoIPDegradationScenario
from fault_injection.scenarios.f11_server_failure import ServerFailureScenario
from fault_injection.scenarios.f12_multi_metric_anomaly import MultiMetricAnomalyScenario

ALL_SCENARIOS: Dict[str, Type[BaseFaultScenario]] = {
    "F01": AccessLinkFailureScenario,
    "F02": DistributionFailureScenario,
    "F03": OSPFFailureScenario,
    "F04": MPLSDownScenario,
    "F05": InternetDownScenario,
    "F06": LTEDownScenario,
    "F07": FiveGDegradationScenario,
    "F08": VPNFailureScenario,
    "F09": WANCongestionScenario,
    "F10": VoIPDegradationScenario,
    "F11": ServerFailureScenario,
    "F12": MultiMetricAnomalyScenario,
}


def get_scenario_by_id(scenario_id: str) -> Optional[Type[BaseFaultScenario]]:
    """Lấy lớp kịch bản theo mã ID (F01..F12), không phân biệt hoa thường."""
    return ALL_SCENARIOS.get(scenario_id.upper())


__all__ = [
    "ALL_SCENARIOS",
    "get_scenario_by_id",
    "AccessLinkFailureScenario",
    "DistributionFailureScenario",
    "OSPFFailureScenario",
    "MPLSDownScenario",
    "InternetDownScenario",
    "LTEDownScenario",
    "FiveGDegradationScenario",
    "VPNFailureScenario",
    "WANCongestionScenario",
    "VoIPDegradationScenario",
    "ServerFailureScenario",
    "MultiMetricAnomalyScenario",
]
