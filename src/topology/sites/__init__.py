"""
topology/sites/__init__.py
Module chứa topology từng site:
  - baoloc.py      : BL flat site (1 switch, 5 VLAN)
  - nhatrang.py    : NT 3-tier site (CORE → DIST01/02 → ACC01-06)
  - hcm.py         : HCM 3-tier site (CORE → DIST01/02 → ACC01-06)
  - datacenter.py  : DC Spine-Leaf (SPINE01/02 → LEAF01-04 → Servers)

Mỗi module export một hàm build_<site>(net, ...) nhận Mininet net object
và trả về dict chứa các node đã thêm vào.
"""
