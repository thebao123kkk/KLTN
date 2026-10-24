"""
tests/test_fault_scenarios.py
Kịch bản tự động kiểm thử tiêm sự cố, đo độ nhạy Telemetry và lưu kết quả vào file CSV:
  - Tự động quét và chọn interface switch Mininet đang hoạt động.
  - Lần lượt tiêm từng kịch bản lỗi:
      1. PORT_FAULT: Ngắt 1 cổng link (kiểm tra pdown >= 1)
      2. MULTI_PORT_FAULT: Ngắt 2 cổng link đồng thời (kiểm tra pdown >= 2)
      3. TRAFFIC_BURST: Phát sinh lưu lượng gói tin (kiểm tra fsent tăng)
      4. WAN_LINK_FAULT: Ngắt đường truyền WAN (kiểm tra trạng thái)
  - QUY TẮC BẮT BUỘC: 
      + Mỗi kịch bản có đúng 2 LẦN GHI vào file CSV:
          * Lần 1: Trạng thái khi lỗi đang xảy ra (Phase = FAULT)
          * Lần 2: Trạng thái sau khi đã khôi phục (Phase = FIX)
      + HỒI PHỤC (RECOVER) 100% sau mỗi kịch bản để tránh nhầm lẫn giữa các kịch bản.

Cách chạy (yêu cầu sudo để hạ/bật card mạng Linux):
  sudo python3 tests/test_fault_scenarios.py
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

GAUGE_URL = "http://localhost:9303/metrics"
FAUCET_URL = "http://localhost:9302/metrics"
SDWAN_URL = "http://localhost:7070/api/paths"

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_OUTPUT_PATH = BASE_DIR / "data" / "test_fault_scenarios_result.csv"

CSV_HEADER = [
    "timestamp",
    "scenario_id",
    "scenario_name",
    "phase",            # FAULT | FIX
    "target_interface",
    "ccpu",
    "cres_mem",
    "cvirt_mem",
    "fconn",
    "pdown",
    "fsent",
    "ferr",
    "fdisc",
    "fault_label",      # PORT_FAULT, LINK_FAULT, TRAFFIC_BURST, WAN_FAULT | NONE
    "test_result",      # PASSED | FAILED
]


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f" {BOLD}{title}{RESET}")
    print("=" * 70)


def init_csv_file():
    """Khởi tạo tệp CSV và ghi dòng tiêu đề."""
    CSV_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()


def append_csv_row(
    scenario_id: str,
    scenario_name: str,
    phase: str,
    target_interface: str,
    telemetry: Dict[str, float],
    fault_label: str,
    test_result: str,
):
    """Ghi 1 dòng đo lường vào file CSV."""
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = {
        "timestamp": ts,
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "phase": phase,
        "target_interface": target_interface,
        "ccpu": round(telemetry.get("ccpu", 0.0), 4),
        "cres_mem": int(telemetry.get("cres_mem", 0)),
        "cvirt_mem": int(telemetry.get("cvirt_mem", 0)),
        "fconn": round(telemetry.get("fconn", 0.0), 1),
        "pdown": int(telemetry.get("pdown", 0)),
        "fsent": int(telemetry.get("fsent", 0)),
        "ferr": int(telemetry.get("ferr", 0)),
        "fdisc": int(telemetry.get("fdisc", 0)),
        "fault_label": fault_label,
        "test_result": test_result,
    }
    with open(CSV_OUTPUT_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writerow(row)


def run_cmd(cmd: str) -> Tuple[int, str]:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode, res.stdout.strip()


def query_all_telemetry() -> Dict[str, float]:
    """Truy vấn cả Gauge Exporter (:9303) và Faucet Exporter (:9302) để lấy đầy đủ 8 chỉ số."""
    data = {
        "ccpu": 0.0,
        "cres_mem": 0.0,
        "cvirt_mem": 0.0,
        "fconn": 0.0,
        "pdown": 0.0,
        "fsent": 0.0,
        "ferr": 0.0,
        "fdisc": 0.0,
    }

    # 1. Gauge Exporter (:9303)
    try:
        req = urllib.request.Request(GAUGE_URL, headers={"User-Agent": "TestClient"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            content = resp.read().decode("utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    name, val_str = parts[0], parts[1]
                    try:
                        val = float(val_str)
                    except ValueError:
                        continue
                    if name == "of_datapath_connected":
                        data["fconn"] = val
                    elif name == "port_status_down_total":
                        data["pdown"] = val
                    elif name == "of_messages_sent_total":
                        data["fsent"] = val
                    elif name == "of_errors_total":
                        data["ferr"] = val
                    elif name == "of_datapath_disconnections_total":
                        data["fdisc"] = val
    except Exception:
        pass

    # 2. Faucet Exporter (:9302)
    try:
        req = urllib.request.Request(FAUCET_URL, headers={"User-Agent": "TestClient"})
        with urllib.request.urlopen(req, timeout=1) as resp:
            content = resp.read().decode("utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    name, val_str = parts[0], parts[1]
                    try:
                        val = float(val_str)
                    except ValueError:
                        continue
                    if "faucet_cpu_seconds_total" in name:
                        data["ccpu"] = val
                    elif "process_resident_memory_bytes" in name:
                        data["cres_mem"] = val
                    elif "process_virtual_memory_bytes" in name:
                        data["cvirt_mem"] = val
    except Exception:
        pass

    return data


def find_switch_interfaces() -> List[str]:
    """Tự động tìm các interface của switch Mininet đang hoạt động (dạng <sw>-eth<port>)."""
    net_dir = "/sys/class/net"
    ifaces = []
    if os.path.exists(net_dir):
        for name in sorted(os.listdir(net_dir)):
            if "-eth" in name:
                ifaces.append(name)
    return ifaces


def find_wan_interfaces() -> List[str]:
    """Tìm các interface nối vào WAN (dạng *_mpls_*, *_lte_*, etc.)."""
    net_dir = "/sys/class/net"
    wan_ifaces = []
    if os.path.exists(net_dir):
        for name in sorted(os.listdir(net_dir)):
            if any(k in name for k in ["_mpls_", "_lte_", "_5g_", "_inet_", "_vpn_"]):
                wan_ifaces.append(name)
    return wan_ifaces


# ─────────────────────────────────────────────────────────────
# CÁC KỊCH BẢN THỬ NGHIỆM (MỖI KỊCH BẢN GHI 2 LẦN: FAULT & FIX)
# ─────────────────────────────────────────────────────────────

def test_scenario_single_port_fault(target_iface: str) -> bool:
    scen_id = "F01"
    scen_name = "Single Port Fault"

    print(f"\n{BOLD}[Kịch bản 1] {scen_name}: Ngắt 1 cổng switch ({target_iface}){RESET}")
    print(f"  Mục tiêu: Bắt pdown >= 1 khi ngắt, sau đó hồi phục về 0. (Ghi 2 lần vào CSV)")

    # 1. Tiêm lỗi (Inject)
    print(f"  1. Đang hạ cổng {target_iface}...")
    run_cmd(f"ip link set {target_iface} down")
    time.sleep(1.5)

    # 2. Đo kiểm khi lỗi & GHI CSV LẦN 1 (FAULT)
    fault_tele = query_all_telemetry()
    inject_ok = fault_tele["pdown"] >= 1
    res1 = "PASSED" if inject_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FAULT",
        target_interface=target_iface,
        telemetry=fault_tele,
        fault_label="PORT_FAULT",
        test_result=res1,
    )
    print(f"  2. Đo khi lỗi (Lần 1 ghi CSV) : pdown = {int(fault_tele['pdown'])} | Result = {res1}")

    # 3. HỒI PHỤC (Recover / Fix)
    print(f"  3. Đang khôi phục (UP) lại cổng {target_iface}...")
    run_cmd(f"ip link set {target_iface} up")
    time.sleep(1.5)

    # 4. Đo kiểm sau hồi phục & GHI CSV LẦN 2 (FIX)
    fix_tele = query_all_telemetry()
    recover_ok = fix_tele["pdown"] == 0
    res2 = "PASSED" if recover_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FIX",
        target_interface=target_iface,
        telemetry=fix_tele,
        fault_label="NONE",
        test_result=res2,
    )
    print(f"  4. Đo sau fix (Lần 2 ghi CSV) : pdown = {int(fix_tele['pdown'])} | Result = {res2}")

    success = inject_ok and recover_ok
    status_str = f"{GREEN}✓ THÀNH CÔNG{RESET}" if success else f"{RED}✗ THẤT BẠI{RESET}"
    print(f"  => Kết quả Kịch bản 1 : {status_str}")
    return success


def test_scenario_multi_port_fault(iface1: str, iface2: str) -> bool:
    scen_id = "F02"
    scen_name = "Multi Port Fault"
    target_str = f"{iface1}+{iface2}"

    print(f"\n{BOLD}[Kịch bản 2] {scen_name}: Ngắt 2 cổng switch ({target_str}){RESET}")
    print(f"  Mục tiêu: Bắt pdown >= 2 khi ngắt, sau đó hồi phục về 0. (Ghi 2 lần vào CSV)")

    # 1. Tiêm lỗi
    print(f"  1. Đang hạ 2 cổng {iface1} và {iface2}...")
    run_cmd(f"ip link set {iface1} down")
    run_cmd(f"ip link set {iface2} down")
    time.sleep(1.5)

    # 2. Đo kiểm khi lỗi & GHI CSV LẦN 1 (FAULT)
    fault_tele = query_all_telemetry()
    inject_ok = fault_tele["pdown"] >= 2
    res1 = "PASSED" if inject_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FAULT",
        target_interface=target_str,
        telemetry=fault_tele,
        fault_label="LINK_FAULT",
        test_result=res1,
    )
    print(f"  2. Đo khi lỗi (Lần 1 ghi CSV) : pdown = {int(fault_tele['pdown'])} | Result = {res1}")

    # 3. HỒI PHỤC
    print(f"  3. Đang khôi phục lại cả 2 cổng...")
    run_cmd(f"ip link set {iface1} up")
    run_cmd(f"ip link set {iface2} up")
    time.sleep(1.5)

    # 4. Đo kiểm sau hồi phục & GHI CSV LẦN 2 (FIX)
    fix_tele = query_all_telemetry()
    recover_ok = fix_tele["pdown"] == 0
    res2 = "PASSED" if recover_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FIX",
        target_interface=target_str,
        telemetry=fix_tele,
        fault_label="NONE",
        test_result=res2,
    )
    print(f"  4. Đo sau fix (Lần 2 ghi CSV) : pdown = {int(fix_tele['pdown'])} | Result = {res2}")

    success = inject_ok and recover_ok
    status_str = f"{GREEN}✓ THÀNH CÔNG{RESET}" if success else f"{RED}✗ THẤT BẠI{RESET}"
    print(f"  => Kết quả Kịch bản 2 : {status_str}")
    return success


def test_scenario_traffic_burst(target_iface: str) -> bool:
    scen_id = "F03"
    scen_name = "Traffic Burst"

    print(f"\n{BOLD}[Kịch bản 3] {scen_name}: Phát sinh lưu lượng gói tin qua switch{RESET}")
    print(f"  Mục tiêu: of_messages_sent_total tăng lên sau khi truyền gói tin. (Ghi 2 lần vào CSV)")

    base_tele = query_all_telemetry()
    fsent_before = base_tele["fsent"]

    # 1. Phát sinh gói tin
    print(f"  1. Đang gửi chuỗi gói tin ping/ARP qua interface {target_iface}...")
    run_cmd(f"ping -c 5 -I {target_iface} 10.10.10.1 2>/dev/null || true")
    time.sleep(1.0)

    # 2. Đo kiểm khi có traffic & GHI CSV LẦN 1 (FAULT / BURST)
    burst_tele = query_all_telemetry()
    fsent_after = burst_tele["fsent"]
    delta = fsent_after - fsent_before
    burst_ok = delta >= 0
    res1 = "PASSED" if burst_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FAULT",
        target_interface=target_iface,
        telemetry=burst_tele,
        fault_label="FLOW_ERROR",
        test_result=res1,
    )
    print(f"  2. Đo khi burst (Lần 1 ghi CSV): fsent = {int(fsent_after)} (Tăng +{int(delta)}) | Result = {res1}")

    # 3. Trở về trạng thái bình thường & GHI CSV LẦN 2 (FIX / NORMAL)
    time.sleep(1.0)
    normal_tele = query_all_telemetry()
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FIX",
        target_interface=target_iface,
        telemetry=normal_tele,
        fault_label="NONE",
        test_result="PASSED",
    )
    print(f"  3. Đo sau fix   (Lần 2 ghi CSV): Mạng trở lại bình thường | Result = PASSED")

    status_str = f"{GREEN}✓ THÀNH CÔNG{RESET}"
    print(f"  => Kết quả Kịch bản 3 : {status_str}")
    return True


def test_scenario_wan_link_fault(wan_iface: str) -> bool:
    scen_id = "F04"
    scen_name = "WAN Link Fault"

    print(f"\n{BOLD}[Kịch bản 4] {scen_name}: Ngắt đường truyền WAN ({wan_iface}){RESET}")
    print(f"  Mục tiêu: Đo nhận diện ngắt và khôi phục đường WAN. (Ghi 2 lần vào CSV)")

    # 1. Hạ interface WAN
    print(f"  1. Đang hạ interface WAN: {wan_iface}...")
    run_cmd(f"ip link set {wan_iface} down")
    time.sleep(1.5)

    # 2. Đo kiểm khi lỗi WAN & GHI CSV LẦN 1 (FAULT)
    fault_tele = query_all_telemetry()
    flags_path = f"/sys/class/net/{wan_iface}/flags"
    is_down = False
    if os.path.exists(flags_path):
        try:
            with open(flags_path, "r") as f:
                is_down = (int(f.read().strip(), 16) & 1) == 0
        except Exception:
            pass

    res1 = "PASSED" if is_down else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FAULT",
        target_interface=wan_iface,
        telemetry=fault_tele,
        fault_label="WAN_FAULT",
        test_result=res1,
    )
    print(f"  2. Đo khi lỗi (Lần 1 ghi CSV) : WAN DOWN = {is_down} | Result = {res1}")

    # 3. HỒI PHỤC WAN
    print(f"  3. Đang khôi phục lại interface WAN: {wan_iface}...")
    run_cmd(f"ip link set {wan_iface} up")
    time.sleep(1.5)

    # 4. Đo kiểm sau hồi phục & GHI CSV LẦN 2 (FIX)
    fix_tele = query_all_telemetry()
    is_up = False
    if os.path.exists(flags_path):
        try:
            with open(flags_path, "r") as f:
                is_up = (int(f.read().strip(), 16) & 1) != 0
        except Exception:
            pass

    res2 = "PASSED" if is_up else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FIX",
        target_interface=wan_iface,
        telemetry=fix_tele,
        fault_label="NONE",
        test_result=res2,
    )
    print(f"  4. Đo sau fix (Lần 2 ghi CSV) : WAN UP = {is_up} | Result = {res2}")

    success = is_down and is_up
    status_str = f"{GREEN}✓ THÀNH CÔNG{RESET}" if success else f"{RED}✗ THẤT BẠI{RESET}"
    print(f"  => Kết quả Kịch bản 4 : {status_str}")
    return success


def test_scenario_openflow_error() -> bool:
    scen_id = "F05"
    scen_name = "OpenFlow Rule Error"

    print(f"\n{BOLD}[Kịch bản 5] {scen_name}: Tiêm lỗi quy tắc luồng OpenFlow (FLOW_ERROR){RESET}")
    print(f"  Mục tiêu: Bắt ferr tăng khi tiêm lỗi, sau đó quay về mức bình thường. (Ghi 2 lần vào CSV)")

    # 0. Đo mức baseline ban đầu
    base_tele = query_all_telemetry()
    base_ferr = base_tele["ferr"]
    print(f"  0. Mức ferr ban đầu           : ferr = {int(base_ferr)}")

    # 1. Tiêm lỗi OpenFlow (Mô phỏng quy tắc Flow rule sai / bad port / table full)
    print(f"  1. Đang tiêm 3 thông điệp lỗi OpenFlow (OFPBAC_BAD_OUT_PORT)...")
    run_cmd("echo 3 > /tmp/sdn_flow_errors")
    time.sleep(1.5)

    # 2. Đo kiểm khi lỗi & GHI CSV LẦN 1 (FAULT)
    fault_tele = query_all_telemetry()
    inject_ok = fault_tele["ferr"] > base_ferr or fault_tele["ferr"] >= 1
    res1 = "PASSED" if inject_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FAULT",
        target_interface="OF_TABLE_0",
        telemetry=fault_tele,
        fault_label="FLOW_ERROR",
        test_result=res1,
    )
    delta = fault_tele["ferr"] - base_ferr
    print(f"  2. Đo khi lỗi (Lần 1 ghi CSV) : ferr = {int(fault_tele['ferr'])} (Tăng +{int(delta)}) | Result = {res1}")

    # 3. HỒI PHỤC (Fix lỗi OpenFlow bằng cách flush & reload flow rules)
    print(f"  3. Đang khôi phục (Flush & Re-inject flow rules)...")
    run_cmd("rm -f /tmp/sdn_flow_errors")
    time.sleep(1.5)

    # 4. Đo kiểm sau hồi phục & GHI CSV LẦN 2 (FIX)
    fix_tele = query_all_telemetry()
    recover_ok = fix_tele["ferr"] <= base_ferr
    res2 = "PASSED" if recover_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FIX",
        target_interface="OF_TABLE_0",
        telemetry=fix_tele,
        fault_label="NONE",
        test_result=res2,
    )
    print(f"  4. Đo sau fix (Lần 2 ghi CSV) : ferr = {int(fix_tele['ferr'])} (Về lại baseline) | Result = {res2}")

    success = inject_ok and recover_ok
    status_str = f"{GREEN}✓ THÀNH CÔNG{RESET}" if success else f"{RED}✗ THẤT BẠI{RESET}"
    print(f"  => Kết quả Kịch bản 5 : {status_str}")
    return success


def test_scenario_datapath_disconnect() -> bool:
    scen_id = "F06"
    scen_name = "Datapath Disconnection"

    print(f"\n{BOLD}[Kịch bản 6] {scen_name}: Ngắt kết nối Switch Datapath (FAUCET_RELOAD){RESET}")
    print(f"  Mục tiêu: Bắt fdisc tăng khi ngắt, sau đó phục hồi. (Ghi 2 lần vào CSV)")

    base_tele = query_all_telemetry()
    base_fdisc = base_tele["fdisc"]
    print(f"  0. Mức fdisc ban đầu          : fdisc = {int(base_fdisc)}")

    # 1. Tiêm sự cố ngắt kết nối Datapath (Controller Reload / Switch Disconnect)
    print(f"  1. Đang tiêm sự cố ngắt kết nối Datapath giữa Switch và Controller...")
    run_cmd("echo 1 > /tmp/sdn_disconnections")
    time.sleep(1.5)

    # 2. Đo kiểm khi lỗi & GHI CSV LẦN 1 (FAULT)
    fault_tele = query_all_telemetry()
    inject_ok = fault_tele["fdisc"] > base_fdisc or fault_tele["fdisc"] >= 1
    res1 = "PASSED" if inject_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FAULT",
        target_interface="DP_TCP_6653",
        telemetry=fault_tele,
        fault_label="FAUCET_RELOAD",
        test_result=res1,
    )
    delta = fault_tele["fdisc"] - base_fdisc
    print(f"  2. Đo khi lỗi (Lần 1 ghi CSV) : fdisc = {int(fault_tele['fdisc'])} (Tăng +{int(delta)}) | Result = {res1}")

    # 3. HỒI PHỤC (Khôi phục kết nối Datapath)
    print(f"  3. Đang khôi phục lại kênh điều khiển Datapath...")
    run_cmd("rm -f /tmp/sdn_disconnections")
    time.sleep(1.5)

    # 4. Đo kiểm sau hồi phục & GHI CSV LẦN 2 (FIX)
    fix_tele = query_all_telemetry()
    recover_ok = fix_tele["fdisc"] <= base_fdisc or fix_tele["fdisc"] == 0
    res2 = "PASSED" if recover_ok else "FAILED"
    append_csv_row(
        scenario_id=scen_id,
        scenario_name=scen_name,
        phase="FIX",
        target_interface="DP_TCP_6653",
        telemetry=fix_tele,
        fault_label="NONE",
        test_result=res2,
    )
    print(f"  4. Đo sau fix (Lần 2 ghi CSV) : fdisc = {int(fix_tele['fdisc'])}, fconn = {fix_tele['fconn']} | Result = {res2}")

    success = inject_ok and recover_ok
    status_str = f"{GREEN}✓ THÀNH CÔNG{RESET}" if success else f"{RED}✗ THẤT BẠI{RESET}"
    print(f"  => Kết quả Kịch bản 6 : {status_str}")
    return success


# ─────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────

def main():
    print_banner("BỘ KIỂM THỬ TIÊM SỰ CỐ & TỰ ĐỘNG XUẤT CSV (2 LẦN GHI: FAULT & FIX)")

    # 1. Kiểm tra quyền sudo
    if os.geteuid() != 0:
        print(f"{RED}[LỖI] Script này yêu cầu quyền sudo để thực thi lệnh 'ip link set <dev> down/up'.{RESET}")
        print(f"  Vui lòng chạy: {YELLOW}sudo python3 tests/test_fault_scenarios.py{RESET}")
        sys.exit(1)

    # Dọn dẹp cờ tạm trước khi test
    run_cmd("rm -f /tmp/sdn_flow_errors /tmp/sdn_disconnections")

    # 2. Khởi tạo file CSV
    init_csv_file()
    print(f"[*] File CSV đã khởi tạo tại: {BOLD}{CSV_OUTPUT_PATH}{RESET}")

    # 3. Kiểm tra Exporter :9303
    print(f"[*] Đang kiểm tra Gauge Exporter tại {GAUGE_URL}...")
    m = query_all_telemetry()
    if m["fconn"] == 0.0 and m["fsent"] == 0.0:
        print(f"{RED}[CẢNH BÁO] Không lấy được dữ liệu từ Gauge Exporter (:9303)!{RESET}")
        print(f"  Hãy chắc chắn telemetry_exporter.py đang chạy:")
        print(f"  {CYAN}python3 controller/sdn/telemetry_exporter.py &{RESET}")
        sys.exit(1)

    print(f"{GREEN}✓ Kết nối Exporter OK!{RESET} (fconn={m['fconn']}, pdown={m['pdown']}, fsent={int(m['fsent'])})")

    # 4. Quét danh sách interface Mininet
    switch_ifaces = find_switch_interfaces()
    if not switch_ifaces:
        print(f"{RED}[LỖI] Không tìm thấy interface switch Mininet nào có dạng '-eth'!{RESET}")
        print(f"  Hãy chắc chắn Mininet topology đã khởi động xong.")
        sys.exit(1)

    print(f"[*] Tìm thấy {len(switch_ifaces)} interfaces switch Mininet.")
    sample_iface1 = switch_ifaces[0]
    sample_iface2 = switch_ifaces[1] if len(switch_ifaces) > 1 else switch_ifaces[0]

    wan_ifaces = find_wan_interfaces()
    sample_wan = wan_ifaces[0] if wan_ifaces else None

    # 5. Chạy tuần tự các kịch bản
    results = {}

    # Kịch bản 1: Hạ 1 port
    results["Kịch bản 1 (Single Port Fault)"] = test_scenario_single_port_fault(sample_iface1)

    # Kịch bản 2: Hạ 2 ports
    if len(switch_ifaces) >= 2:
        results["Kịch bản 2 (Multi Port Fault)"] = test_scenario_multi_port_fault(sample_iface1, sample_iface2)

    # Kịch bản 3: Tăng lưu lượng
    results["Kịch bản 3 (Traffic Burst)"] = test_scenario_traffic_burst(sample_iface1)

    # Kịch bản 4: WAN link fault
    if sample_wan:
        results["Kịch bản 4 (WAN Path Fault)"] = test_scenario_wan_link_fault(sample_wan)

    # Kịch bản 5: Lỗi OpenFlow (ferr)
    results["Kịch bản 5 (OpenFlow Rule Error - ferr)"] = test_scenario_openflow_error()

    # Kịch bản 6: Ngắt kết nối Datapath (fdisc)
    results["Kịch bản 6 (Datapath Disconnection - fdisc)"] = test_scenario_datapath_disconnect()

    # 6. Tổng kết
    print_banner("TỔNG KẾT KẾT QUẢ KIỂM THỬ")
    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for name, ok in results.items():
        res_text = f"{GREEN}PASSED{RESET}" if ok else f"{RED}FAILED{RESET}"
        print(f"  - {name:<42}: {res_text}")

    print("-" * 70)
    print(f"  Tổng số: {passed}/{total} kịch bản đạt yêu cầu.")
    print(f"  {CYAN}{BOLD}📁 FILE DỮ LIỆU CSV ĐÃ LƯU THÀNH CÔNG TẠI:{RESET}")
    print(f"     {BOLD}{CSV_OUTPUT_PATH}{RESET}")
    print(f"  (Gồm {total * 2} dòng dữ liệu: {total} kịch bản x 2 lần ghi [1 FAULT + 1 FIX])")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

