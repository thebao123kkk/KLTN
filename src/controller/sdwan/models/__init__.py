"""
controller/sdwan/models/__init__.py
SD-WAN data models
"""
from .path_state import PathState, PathStatus
from .traffic_class import TrafficClass, SLA_REQUIREMENTS, PATH_PRIORITY

__all__ = ['PathState', 'PathStatus', 'TrafficClass', 'SLA_REQUIREMENTS', 'PATH_PRIORITY']
