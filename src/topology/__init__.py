"""
topology/
Chứa toàn bộ định nghĩa Mininet topology cho Enterprise Network KLTN.

Modules:
  enterprise_topo.py    — Entry point, build network theo phase (--phase 1..6)
  sites/baoloc.py       — Bảo Lộc flat site (1 switch, 5 VLAN, 16 hosts)
  sites/nhatrang.py     — Nha Trang 3-tier (CORE+DIST01/02+ACC01-06, 26 hosts)
  sites/hcm.py          — HCM 3-tier (CORE+DIST01/02+ACC01-06, 35 hosts)
  sites/datacenter.py   — Data Center Spine-Leaf (2 SPINE+4 LEAF, 10 servers)
  wan/wan_links.py      — WAN emulation (Phase 1-6: direct; Phase 9: tc netem)
"""
