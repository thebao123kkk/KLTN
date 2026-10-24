"""
tests/check_telemetry_pipeline.py
Script chẩn đoán nhanh toàn bộ đường ống Telemetry:
  1. Kiểm tra Exporter (:9302, :9303, :9100)
  2. Kiểm tra Prometheus Server (:9090)
  3. Kiểm tra trạng thái cào (Scrape Targets UP/DOWN) của Prometheus
"""

import json
import urllib.request
import urllib.error
import sys

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_url(name, url, timeout=2):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DiagnosisClient"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                print(f"  {GREEN}✓{RESET} {name:<25} ({url}): {GREEN}HOẠT ĐỘNG (HTTP 200){RESET}")
                return True
            else:
                print(f"  {YELLOW}⚠{RESET} {name:<25} ({url}): HTTP {resp.status}")
                return False
    except urllib.error.URLError as e:
        print(f"  {RED}✗{RESET} {name:<25} ({url}): {RED}KHÔNG KẾT NỐI ĐƯỢC ({e.reason}){RESET}")
        return False
    except Exception as e:
        print(f"  {RED}✗{RESET} {name:<25} ({url}): {RED}LỖI ({e}){RESET}")
        return False


def check_prometheus_targets():
    url = "http://localhost:9090/api/v1/targets"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DiagnosisClient"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            active_targets = data.get("data", {}).get("activeTargets", [])
            if not active_targets:
                print(f"  {YELLOW}⚠ Prometheus chưa cấu hình bất kỳ target nào.{RESET}")
                return

            print("\n  Trạng thái các Scrape Targets trong Prometheus:")
            all_up = True
            for t in active_targets:
                job = t.get("labels", {}).get("job", "unknown")
                scrape_url = t.get("scrapeUrl", "")
                health = t.get("health", "").lower()
                last_err = t.get("lastError", "")

                if health == "up":
                    print(f"    {GREEN}✓ [UP]{RESET}   Job: {job:<16} Endpoint: {scrape_url}")
                else:
                    all_up = False
                    print(f"    {RED}✗ [DOWN]{RESET} Job: {job:<16} Endpoint: {scrape_url} -> Lỗi: {last_err}")
            return all_up
    except Exception as e:
        print(f"  {RED}✗ Không lấy được danh sách targets từ Prometheus: {e}{RESET}")
        return False


def main():
    print("=" * 65)
    print(" CHẨN ĐOÁN HỆ THỐNG THU THẬP TELEMETRY")
    print("=" * 65)

    print("\n[Bước 1] Kiểm tra các Exporter:")
    exp_9302 = check_url("Faucet Exporter", "http://localhost:9302/metrics")
    exp_9303 = check_url("Gauge Exporter", "http://localhost:9303/metrics")
    exp_9100 = check_url("Node Exporter", "http://localhost:9100/metrics")
    exp_7070 = check_url("SD-WAN Exporter", "http://localhost:7070/metrics")

    print("\n[Bước 2] Kiểm tra Prometheus Server:")
    prom_ok = check_url("Prometheus Server", "http://localhost:9090/-/healthy")

    if prom_ok:
        print("\n[Bước 3] Kiểm tra liên kết cào dữ liệu của Prometheus:")
        check_prometheus_targets()

    print("\n" + "=" * 65)
    if not (exp_9302 and exp_9303):
        print(f"{YELLOW}👉 Khắc phục:{RESET} telemetry_exporter.py CHƯA CHẠY. Hãy chạy lệnh:")
        print("   python3 controller/sdn/telemetry_exporter.py &")
    elif not prom_ok:
        print(f"{YELLOW}👉 Khắc phục:{RESET} Prometheus CHƯA CHẠY. Hãy chạy lệnh:")
        print("   prometheus --config.file=config/prometheus.yml --storage.tsdb.path=data/prometheus_data &")
    else:
        print(f"{GREEN}✓ Toàn bộ hệ thống sẵn sàng! Chạy ngay:{RESET}")
        print("   python3 telemetry_collector.py --cycles 6 --interval 10")
    print("=" * 65)


if __name__ == "__main__":
    main()
