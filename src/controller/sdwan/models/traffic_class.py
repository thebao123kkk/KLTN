"""
controller/sdwan/models/traffic_class.py
Traffic Class definitions và SLA requirements cho SD-WAN policy engine
"""
from enum import Enum


class TrafficClass(Enum):
    VOIP     = "voip"       # VoIP RTP/SIP - latency sensitive
    DATABASE = "database"   # DB queries - low loss
    WEB      = "web"        # HTTP/HTTPS - moderate
    CCTV     = "cctv"       # CCTV stream - moderate BW
    BULK     = "bulk"       # File transfer - best effort
    BACKUP   = "backup"     # Backup - lowest priority


# SLA requirements per traffic class
# max_latency (ms), max_loss (%), max_jitter (ms)
SLA_REQUIREMENTS: dict[TrafficClass, dict] = {
    TrafficClass.VOIP: {
        'max_latency': 50,
        'max_loss':    1.0,
        'max_jitter':  10,
        'description': 'VoIP - ITU-T G.114 compliant',
    },
    TrafficClass.DATABASE: {
        'max_latency': 100,
        'max_loss':    0.5,
        'max_jitter':  20,
        'description': 'Database transactions - low loss critical',
    },
    TrafficClass.WEB: {
        'max_latency': 200,
        'max_loss':    2.0,
        'max_jitter':  50,
        'description': 'Web browsing / application',
    },
    TrafficClass.CCTV: {
        'max_latency': 300,
        'max_loss':    2.0,
        'max_jitter':  50,
        'description': 'CCTV streaming',
    },
    TrafficClass.BULK: {
        'max_latency': 500,
        'max_loss':    5.0,
        'max_jitter':  100,
        'description': 'Bulk file transfer',
    },
    TrafficClass.BACKUP: {
        'max_latency': 2000,
        'max_loss':    10.0,
        'max_jitter':  500,
        'description': 'Backup / lowest priority',
    },
}

# Path priority order per traffic class (từ ưu tiên cao → thấp)
# Nếu path đầu tiên không đạt SLA, thử path tiếp theo
PATH_PRIORITY: dict[TrafficClass, list] = {
    TrafficClass.VOIP:     ['MPLS', 'FIVEG', 'INET', 'VPN', 'LTE'],
    TrafficClass.DATABASE: ['MPLS', 'FIVEG', 'INET', 'VPN', 'LTE'],
    TrafficClass.WEB:      ['MPLS', 'INET',  'FIVEG', 'VPN', 'LTE'],
    TrafficClass.CCTV:     ['INET', 'FIVEG', 'VPN', 'LTE',  'MPLS'],
    TrafficClass.BULK:     ['INET', 'LTE',   'FIVEG', 'VPN', 'MPLS'],
    TrafficClass.BACKUP:   ['LTE',  'VPN',   'INET', 'FIVEG', 'MPLS'],
}

# DSCP marking per traffic class (cho Phase 11 QoS)
DSCP_MARKING: dict[TrafficClass, int] = {
    TrafficClass.VOIP:     46,   # EF (Expedited Forwarding)
    TrafficClass.DATABASE: 18,   # AF21
    TrafficClass.WEB:      10,   # AF11
    TrafficClass.CCTV:     16,   # CS2
    TrafficClass.BULK:     0,    # BE (Best Effort)
    TrafficClass.BACKUP:   0,    # BE
}
