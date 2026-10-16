#!/usr/bin/env python3
"""Sơ đồ mạng phân tầng theo topology thực tế của dự án KLTN.

Cấu trúc đúng:
- BL: router -> switch -> host
- NT/HCM: core switch -> distribution router -> access switch -> host
- DC: spine -> leaf -> host
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUTPUT_FILE = Path(__file__).resolve().parent.parent / "network_topology.png"


class TopologyDiagram:
    def __init__(self):
        self.fig, self.ax = plt.subplots(figsize=(18, 10))
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.axis("off")
        self.ax.set_title("Enterprise Network Topology (Physical Layering)", fontsize=18, pad=18)

    def add_box(self, center, w, h, label, fc, ec, text_color="#111827", fontsize=12):
        x, y = center
        rect = plt.Rectangle((x - w/2, y - h/2), w, h, facecolor=fc, edgecolor=ec, linewidth=2, zorder=0)
        self.ax.add_patch(rect)
        self.ax.text(x, y, label, ha="center", va="center", fontsize=fontsize, color=text_color, weight="bold")

    def add_router(self, center, label, color="#fce7f3", edge="#be185d"):
        x, y = center
        circle = plt.Circle((x, y), 2.9, facecolor=color, edgecolor=edge, linewidth=2, zorder=2)
        self.ax.add_patch(circle)
        self.ax.text(x, y, label, ha="center", va="center", fontsize=8, weight="bold")

    def add_switch(self, center, label, color="#dcfce7", edge="#15803d"):
        x, y = center
        rect = plt.Rectangle((x - 2.8, y - 2.8), 5.6, 5.6, facecolor=color, edgecolor=edge, linewidth=2, zorder=2)
        self.ax.add_patch(rect)
        self.ax.text(x, y, label, ha="center", va="center", fontsize=7, weight="bold")

    def add_host(self, center, label, color="#fef3c7", edge="#b45309"):
        x, y = center
        circle = plt.Circle((x, y), 1.7, facecolor=color, edgecolor=edge, linewidth=1.5, zorder=2)
        self.ax.add_patch(circle)
        self.ax.text(x, y + 2.4, label, ha="center", va="center", fontsize=6)

    def connect(self, a, b, color="#4b5563", lw=1.5):
        self.ax.plot([a[0], b[0]], [a[1], b[1]], color=color, linewidth=lw, zorder=1)

    def save(self, path=OUTPUT_FILE):
        self.fig.tight_layout()
        self.fig.savefig(path, dpi=220, bbox_inches="tight")
        print(f"[OK] Diagram saved to {path}")


def draw_baoloc(diagram):
    # shift BL left a bit for clearer spacing
    base_x = 12
    diagram.add_box((base_x, 84), 16, 12, "BL\nBảo Lộc", "#dbeafe", "#2563eb")
    diagram.add_router((base_x, 66), "BL_GW", "#f9a8d4", "#be185d")
    diagram.add_switch((base_x, 52), "BL_SW", "#bbf7d0", "#15803d")

    hosts = [
        (base_x - 6, 36, "BL_ADM01"), (base_x - 2, 36, "BL_SAL01"), (base_x + 2, 36, "BL_ACC01"),
        (base_x + 6, 36, "BL_IT01"), (base_x + 10, 36, "BL_PRN01"), (base_x + 14, 36, "BL_CAM01"),
    ]
    for x, y, name in hosts:
        diagram.add_host((x, y), name, "#fef3c7", "#b45309")

    diagram.connect((18, 66), (18, 52), color="#374151", lw=2)
    for x, y, _ in hosts:
        diagram.connect((18, 52), (x, y), color="#374151", lw=1.5)


def draw_nt_hcm(diagram, site_name, left_x, core_name, dist1_name, dist2_name):
    # site box centered at left_x
    diagram.add_box((left_x, 84), 20, 12, site_name, "#dcfce7" if site_name == "NT\nNha Trang" else "#ffedd5", "#15803d" if site_name == "NT\nNha Trang" else "#c2410c")

    core = (left_x, 66)
    dist1 = (left_x - 8, 50)
    dist2 = (left_x + 8, 50)
    diagram.add_switch(core, core_name, "#bbf7d0", "#15803d")
    diagram.add_router(dist1, dist1_name, "#f9a8d4", "#be185d")
    diagram.add_router(dist2, dist2_name, "#f9a8d4", "#be185d")

    # spread access switches a bit wider
    acc_positions = [
        (left_x - 15, 34, "ACC01"),
        (left_x - 9, 34, "ACC02"),
        (left_x - 3, 34, "ACC03"),
        (left_x + 3, 34, "ACC04"),
        (left_x + 9, 34, "ACC05"),
        (left_x + 15, 34, "ACC06"),
    ]
    for x, y, label in acc_positions:
        diagram.add_switch((x, y), label, "#dcfce7", "#15803d")

    # align hosts under access switches with wider spacing
    host_positions = [
        (left_x - 15, 20, f"{dist1_name.replace('-', '_')}_ADM01"), (left_x - 9, 20, f"{dist1_name.replace('-', '_')}_SAL01"), (left_x - 3, 20, f"{dist1_name.replace('-', '_')}_ACC01"),
        (left_x + 3, 20, f"{dist1_name.replace('-', '_')}_HR01"), (left_x + 9, 20, f"{dist1_name.replace('-', '_')}_CUS01"), (left_x + 15, 20, f"{dist1_name.replace('-', '_')}_IT01"),
        (left_x + 21, 20, f"{dist1_name.replace('-', '_')}_PRN01"), (left_x + 27, 20, f"{dist1_name.replace('-', '_')}_CAM01"),
    ]
    for x, y, label in host_positions:
        diagram.add_host((x, y), label, "#fef3c7", "#b45309")

    diagram.connect(core, dist1, color="#374151", lw=2)
    diagram.connect(core, dist2, color="#374151", lw=2)
    for x, y, _ in acc_positions:
        diagram.connect(dist1, (x, y), color="#374151", lw=1.5)
        diagram.connect(dist2, (x, y), color="#374151", lw=1.5)
        diagram.connect((x, y), (x, y - 8), color="#374151", lw=1.2)

    # hosts from accs
    for idx, (x, y, _) in enumerate(acc_positions):
        hx = x - 2 + (idx % 2) * 4
        diagram.connect((x, y - 8), (hx, 20 + (idx // 2) * 0), color="#374151", lw=1)


def draw_dc(diagram):
    diagram.add_box((84, 84), 18, 12, "DC\nData Center", "#ede9fe", "#7c3aed")

    spine1 = (80, 66)
    spine2 = (88, 66)
    diagram.add_switch(spine1, "DC_SPINE01", "#bbf7d0", "#15803d")
    diagram.add_switch(spine2, "DC_SPINE02", "#bbf7d0", "#15803d")

    diagram.add_router((84, 52), "DC_SP_GW", "#f9a8d4", "#be185d")

    leaf_positions = [
        (74, 38, "LEAF01"),
        (80, 38, "LEAF02"),
        (86, 38, "LEAF03"),
        (92, 38, "LEAF04"),
    ]
    for x, y, label in leaf_positions:
        diagram.add_switch((x, y), label, "#dcfce7", "#15803d")

    server_positions = [
        (72, 24, "WEB01"), (78, 24, "APP01"), (84, 24, "DB01"),
        (90, 24, "DNS01"), (96, 24, "DHCP01"),
    ]
    for x, y, label in server_positions:
        diagram.add_host((x, y), label, "#fef3c7", "#b45309")

    diagram.connect(spine1, spine2, color="#374151", lw=2)
    diagram.connect(spine1, (84, 52), color="#374151", lw=2)
    diagram.connect(spine2, (84, 52), color="#374151", lw=2)

    for x, y, label in leaf_positions:
        diagram.connect((84, 52), (x, y), color="#374151", lw=1.5)

    for x, y, label in server_positions:
        nearest_leaf = (72, 38) if "WEB" in label else (78, 38) if "APP" in label else (86, 38) if "DB" in label else (92, 38)
        diagram.connect(nearest_leaf, (x, y), color="#374151", lw=1.2)


def draw_wan(diagram):
    # BL -> HCM (adjusted for new positions)
    diagram.connect((12, 66), (52, 50), color="#2563eb", lw=2)
    # NT -> HCM
    diagram.connect((36, 50), (52, 50), color="#2563eb", lw=2)
    # HCM -> DC
    diagram.connect((60, 50), (84, 52), color="#2563eb", lw=2)


def main():
    diagram = TopologyDiagram()
    draw_baoloc(diagram)
    draw_nt_hcm(diagram, "NT\nNha Trang", 40, "NT_CORE", "NT_DIST01", "NT_DIST02")
    draw_nt_hcm(diagram, "HCM\nHồ Chí Minh", 65, "HCM_CORE", "HCM_DIST01", "HCM_DIST02")
    draw_dc(diagram)
    draw_wan(diagram)
    diagram.save(OUTPUT_FILE)


if __name__ == "__main__":
    main()
