"""
tests/fast_check.py
Script kiểm tra nhanh Topology & Phase Checks
==================================================
Tùy chọn:
  1. Dry Run (không cần sudo/Mininet, < 2 giây):
     python3 tests/fast_check.py --dry-run
     - Kiểm tra cú pháp Python, imports, YAML configs, string template.

  2. Target Phase Run (xây mạng đến Phase N chỉ định):
     sudo python3 tests/fast_check.py --phase 8
     - Chỉ khởi động đến Phase N cần debug, không cần chờ hết Phase 14 (tiết kiệm thời gian).

  3. Unified All Checks (dùng 1 Mininet instance duy nhất):
     sudo python3 tests/fast_check.py --all --max-phase 9
     - Khởi động Mininet 1 lần duy nhất và chạy kiểm tra liên tiếp các Phase từ 1 -> max-phase.
"""

import os
import sys
import argparse
import py_compile
import time
import yaml

# Thêm thư mục src vào sys.path
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR  = os.path.dirname(_TEST_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')


def run_dry_run():
    """Kiểm tra cú pháp Python và nạp config tĩnh không cần Mininet."""
    print("=" * 65)
    print(" [FAST CHECK] DRY-RUN MODE (Phân tích tĩnh & Cú pháp)")
    print("=" * 65)

    errors = 0
    passed_files = 0

    # 1. Kiểm tra compile tất cả file .py
    print("\n[Step 1] Kiểm tra cú pháp Python (py_compile)...")
    for root, _, files in os.walk(_SRC_DIR):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, _SRC_DIR)
                try:
                    py_compile.compile(full_path, doraise=True)
                    passed_files += 1
                except py_compile.PyCompileError as e:
                    print(f"  ✗ Lỗi cú pháp tại [{rel_path}]: {e}")
                    errors += 1

    print(f"  ✓ Đã kiểm tra {passed_files} file .py. Số lỗi: {errors}")

    # 2. Kiểm tra nạp file YAML config
    print("\n[Step 2] Kiểm tra file cấu hình YAML...")
    config_dir = os.path.join(_SRC_DIR, 'config')
    yaml_files = ['vlan.yaml', 'services.yaml', 'wan_paths.yaml', 'acl_rules.yaml', 'faucet.yaml', 'prometheus.yml', 'telemetry_config.yaml']
    for yf in yaml_files:
        ypath = os.path.join(config_dir, yf)
        if os.path.exists(ypath):
            try:
                with open(ypath, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                print(f"  ✓ {yf:<20} OK")
            except Exception as e:
                print(f"  ✗ {yf:<20} Lỗi YAML: {e}")
                errors += 1
        else:
            print(f"  ⚠ {yf:<20} Không tìm thấy")

    # 3. Kiểm tra import thử các module chính
    print("\n[Step 3] Test import các module chính...")
    modules = [
        'topology.enterprise_topo',
        'topology.sites.baoloc',
        'topology.sites.nhatrang',
        'topology.sites.hcm',
        'topology.sites.datacenter',
        'topology.wan.wan_links',
        'topology.wan.wan_topo',
        'scripts.configure_acl',
        'scripts.configure_haproxy',
        'controller.sdwan.sdwan_controller',
    ]

    for mod in modules:
        try:
            __import__(mod)
            print(f"  ✓ Import {mod:<35} OK")
        except ModuleNotFoundError as e:
            if 'mininet' in str(e):
                print(f"  ⚠ Import {mod:<35} Mininet chưa cài (chỉ chạy trên Linux)")
            else:
                print(f"  ✗ Import {mod:<35} Thiếu module: {e}")
                errors += 1
        except Exception as e:
            print(f"  ✗ Import {mod:<35} LỖI: {e}")
            errors += 1

    print("\n" + "=" * 65)
    if errors == 0:
        print(" ✓ DRY-RUN SUCCESS: Tất cả cú pháp, configs và imports đều hợp lệ!")
    else:
        print(f" ✗ DRY-RUN FAILED: Tìm thấy {errors} lỗi cần sửa trước khi chạy Mininet.")
    print("=" * 65)
    return errors == 0


def run_target_phase(phase: int, run_check: bool = True):
    """Khởi động mạng dừng ở Phase N cụ thể và chạy test."""
    print("=" * 65)
    print(f" [FAST CHECK] TARGET PHASE MODE (Phase {phase})")
    print("=" * 65)

    if os.geteuid() != 0:
        print("ERROR: Cần quyền sudo để chạy Mininet!")
        sys.exit(1)

    from topology.enterprise_topo import build_network, print_summary

    topo = None
    try:
        print(f"\n[NET] Khởi động Mininet dừng ở Phase {phase}...")
        start_t = time.time()
        topo = build_network(phase=phase)
        elapsed = time.time() - start_t

        if topo is None or getattr(topo, 'net', None) is None:
            print(f"✗ LỖI: build_network(phase={phase}) thất bại!")
            return False

        print(f"✓ Mininet khởi động thành công sau {elapsed:.2f}s (thay vì 5 phút)")
        print_summary(topo)

        if run_check:
            # Tìm module test tương ứng
            check_mod_name = f"tests.phase_checks.check_phase{phase}"
            try:
                mod = __import__(check_mod_name, fromlist=['run_check', f'run_phase{phase}_checks'])
                check_fn = getattr(mod, f'run_phase{phase}_checks', None) or getattr(mod, 'run_check', None)
                if check_fn:
                    print(f"\n[TEST] Đang chạy test cho Phase {phase}...")
                    if 'topo_nodes' in check_fn.__code__.co_varnames:
                        topo_nodes = {
                            'bl_nodes': topo.bl_nodes,
                            'nt_nodes': topo.nt_nodes,
                            'hcm_nodes': topo.hcm_nodes,
                            'dc_nodes': topo.dc_nodes,
                        }
                        check_fn(topo.net, topo_nodes)
                    elif check_fn.__code__.co_argcount == 2:
                        check_fn(topo.net, topo)
                    else:
                        check_fn(topo)
                else:
                    print(f"  ⚠ Không tìm thấy hàm test phù hợp trong {check_mod_name}")
            except ImportError:
                print(f"  ℹ Không có file test riêng cho Phase {phase}")

        return True

    except Exception as e:
        print(f"\n✗ LỖI THỰC THI PHASE {phase}: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if topo and getattr(topo, 'net', None):
            print("\n[NET] Stopping Mininet...")
            try:
                topo.net.stop()
            except Exception as se:
                print(f"Warning khi dừng Mininet: {se}")


def run_unified_all(max_phase: int = 14):
    """Khởi động mạng 1 LẦN DUY NHẤT và chạy tất cả các phase checks liên tiếp."""
    print("=" * 65)
    print(f" [FAST CHECK] UNIFIED SINGLE-SESSION MODE (Up to Phase {max_phase})")
    print("=" * 65)

    if os.geteuid() != 0:
        print("ERROR: Cần quyền sudo để chạy Mininet!")
        sys.exit(1)

    from topology.enterprise_topo import build_network

    topo = None
    try:
        print(f"\n[NET] Khởi động mạng 1 lần duy nhất đến Phase {max_phase}...")
        start_t = time.time()
        topo = build_network(phase=max_phase)
        print(f"✓ Mạng đã sẵn sàng sau {time.time() - start_t:.2f}s")

        if topo is None or getattr(topo, 'net', None) is None:
            print("✗ Khởi tạo thất bại.")
            return False

        # Chạy kiểm tra từng phase
        for p in range(1, max_phase + 1):
            mod_name = f"tests.phase_checks.check_phase{p}"
            try:
                mod = __import__(mod_name, fromlist=['run_check', f'run_phase{p}_checks'])
                check_fn = getattr(mod, f'run_phase{p}_checks', None) or getattr(mod, 'run_check', None)
                if check_fn:
                    print(f"\n---> Running Checks for Phase {p} <---")
                    if 'topo_nodes' in check_fn.__code__.co_varnames:
                        topo_nodes = {
                            'bl_nodes': topo.bl_nodes,
                            'nt_nodes': topo.nt_nodes,
                            'hcm_nodes': topo.hcm_nodes,
                            'dc_nodes': topo.dc_nodes,
                        }
                        check_fn(topo.net, topo_nodes)
                    elif check_fn.__code__.co_argcount == 2:
                        check_fn(topo.net, topo)
                    else:
                        check_fn(topo)
            except ImportError:
                continue

        print("\n" + "=" * 65)
        print(" ✓ UNIFIED TEST COMPLETE!")
        print("=" * 65)
        return True

    finally:
        if topo and getattr(topo, 'net', None):
            print("\n[NET] Stopping Mininet...")
            try:
                topo.net.stop()
            except Exception as se:
                print(f"Warning khi dừng Mininet: {se}")


def main():
    parser = argparse.ArgumentParser(description="KLTN Fast Topology & Phase Checker")
    parser.add_argument("--dry-run", action="store_true", help="Kiểm tra cú pháp tĩnh & imports (<2s, không cần sudo/Mininet)")
    parser.add_argument("--phase", type=int, default=None, help="Chỉ khởi động và test 1 Phase N cụ thể (1-14)")
    parser.add_argument("--all", action="store_true", help="Khởi động Mininet 1 lần và chạy tất cả Phase Checks liên tiếp")
    parser.add_argument("--max-phase", type=int, default=14, help="Phase tối đa khi dùng --all (mặc định=14)")

    args = parser.parse_args()

    if args.dry_run:
        ok = run_dry_run()
        sys.exit(0 if ok else 1)
    elif args.phase is not None:
        ok = run_target_phase(args.phase)
        sys.exit(0 if ok else 1)
    elif args.all:
        ok = run_unified_all(max_phase=args.max_phase)
        sys.exit(0 if ok else 1)
    else:
        # Default: Chạy dry-run nếu không chỉ định cờ
        print("Không chỉ định cờ nào. Mặc định chạy --dry-run.\n"
              "Dùng --help để xem các tùy chọn (--phase N, --all, --dry-run).")
        ok = run_dry_run()
        sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
