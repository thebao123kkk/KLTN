"""
tests/test_telemetry.py
Bộ kiểm thử đơn vị cho Module Thu thập Telemetry (10 Test Cases theo kế hoạch)
"""

import json
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

# Đảm bảo import được module từ thư mục src
current_dir = Path(__file__).resolve().parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from ai_engine.telemetry.prometheus_client import PrometheusClient
from ai_engine.telemetry.fault_log_reader import FaultLogReader
from ai_engine.telemetry.context_metadata_parser import ContextMetadataParser, ContextMetadata
from ai_engine.telemetry.vector_assembler import VectorAssembler, StateVector
from ai_engine.telemetry.collector import TelemetryCollector


class TestPrometheusClient(unittest.TestCase):
    """Kiểm thử PrometheusClient."""

    @patch("requests.get")
    def test_query_instant_success(self, mock_get):
        """Test Case 1: Mock Prometheus trả về of_datapath_connected -> fconn = 3.0"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": "of_datapath_connected"},
                        "value": [1729083610.123, "3.0"],
                    }
                ],
            },
        }
        mock_get.return_value = mock_resp

        client = PrometheusClient("http://localhost:9090")
        val = client.query_instant("of_datapath_connected")
        self.assertEqual(val, 3.0)
        self.assertEqual(client._last_known["of_datapath_connected"], 3.0)

    @patch("requests.get")
    def test_query_instant_empty(self, mock_get):
        """Test Case 2: Mock Prometheus trả về rỗng -> None"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "data": {"resultType": "vector", "result": []},
        }
        mock_get.return_value = mock_resp

        client = PrometheusClient("http://localhost:9090")
        val = client.query_instant("unknown_metric")
        self.assertIsNone(val)

    @patch("requests.get")
    def test_query_fallback_last_known(self, mock_get):
        """Test Case 3: Query thất bại, dùng last_known"""
        mock_get.side_effect = Exception("Connection refused")

        client = PrometheusClient("http://localhost:9090")
        client._last_known["faucet_cpu_seconds_total"] = 2.5

        val = client.query_with_fallback("faucet_cpu_seconds_total", fallback="last_known")
        self.assertEqual(val, 2.5)


class TestFaultLogReader(unittest.TestCase):
    """Kiểm thử FaultLogReader."""

    def setUp(self):
        self.test_dir = current_dir / "data" / "test_logs"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.json_log = self.test_dir / "fault_log_test.json"
        self.txt_log = self.test_dir / "fault_log_test.txt"

    def tearDown(self):
        if self.json_log.exists():
            self.json_log.unlink()
        if self.txt_log.exists():
            self.txt_log.unlink()

    def test_fault_log_active_fault(self):
        """Test Case 4: Đọc lỗi active từ file log JSONL"""
        now_iso = datetime.now(timezone.utc).isoformat()
        event = {
            "timestamp": now_iso,
            "scenario_id": "F01",
            "scenario_name": "Link Fault s1-s2",
            "category": "LINK_FAULT",
            "event_type": "INJECT",
            "status": "SUCCESS",
            "duration_sec": 30.0,
        }
        with open(self.json_log, "w", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        reader = FaultLogReader(self.json_log)
        label, dur = reader.get_current_fault()
        self.assertEqual(label, "LINK_FAULT")
        self.assertGreaterEqual(dur, 0.0)

    def test_fault_log_no_fault(self):
        """Test Case 5: File log rỗng hoặc đã recover -> NONE, 0.0"""
        with open(self.json_log, "w", encoding="utf-8") as f:
            f.write("")

        reader = FaultLogReader(self.json_log)
        label, dur = reader.get_current_fault()
        self.assertEqual(label, "NONE")
        self.assertEqual(dur, 0.0)

        # Kiểm tra sau khi có sự kiện RECOVER
        now_iso = datetime.now(timezone.utc).isoformat()
        with open(self.json_log, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": now_iso,
                "event_type": "INJECT",
                "category": "PORT_FAULT",
                "status": "SUCCESS",
            }) + "\n")
            f.write(json.dumps({
                "timestamp": now_iso,
                "event_type": "RECOVER",
                "category": "PORT_FAULT",
                "status": "SUCCESS",
            }) + "\n")

        label, dur = reader.get_current_fault()
        self.assertEqual(label, "NONE")
        self.assertEqual(dur, 0.0)


class TestVectorAssembler(unittest.TestCase):
    """Kiểm thử VectorAssembler và StateVector."""

    def test_vector_assembler_complete(self):
        """Test Case 6: 8 giá trị đầy đủ hợp lệ -> OK"""
        vec = VectorAssembler.assemble(
            ccpu=12.5,
            cres_mem=45000000.0,
            cvirt_mem=250000000.0,
            fsent=100.0,
            ferr=0.0,
            fconn=3.0,
            fdisc=0.0,
            pdown=0.0,
        )
        self.assertEqual(vec.data_quality, "OK")
        self.assertTrue(vec.is_healthy())
        self.assertTrue(vec.validate())
        self.assertEqual(len(vec.to_list()), 8)

    def test_vector_assembler_partial(self):
        """Test Case 7: 1-2 giá trị None -> PARTIAL"""
        vec = VectorAssembler.assemble(
            ccpu=12.5,
            cres_mem=None,
            cvirt_mem=250000000.0,
            fsent=100.0,
            ferr=0.0,
            fconn=3.0,
            fdisc=0.0,
            pdown=None,
        )
        self.assertEqual(vec.data_quality, "PARTIAL")
        self.assertEqual(vec.cres_mem, 0.0)
        self.assertEqual(vec.pdown, 0.0)

    def test_vector_assembler_invalid(self):
        """Test Case 8: Giá trị âm -> INVALID và clamp về 0.0"""
        vec = VectorAssembler.assemble(
            ccpu=12.5,
            cres_mem=45000000.0,
            cvirt_mem=250000000.0,
            fsent=100.0,
            ferr=0.0,
            fconn=3.0,
            fdisc=0.0,
            pdown=-1.0,
        )
        self.assertEqual(vec.data_quality, "INVALID")
        self.assertEqual(vec.pdown, 0.0)

    def test_fconn_normal_3_switches(self):
        """Test Case 9: fconn = 3.0 với 3 switch kết nối bình thường"""
        vec = VectorAssembler.assemble(
            ccpu=1.0, cres_mem=10.0, cvirt_mem=20.0,
            fsent=5.0, ferr=0.0, fconn=3.0, fdisc=0.0, pdown=0.0
        )
        self.assertEqual(vec.fconn, 3.0)
        self.assertEqual(vec.data_quality, "OK")

    def test_fconn_drop_detect(self):
        """Test Case 10: fconn giảm về 0 và fdisc tăng phát hiện mất kết nối switch"""
        vec = VectorAssembler.assemble(
            ccpu=1.0, cres_mem=10.0, cvirt_mem=20.0,
            fsent=5.0, ferr=0.0, fconn=0.0, fdisc=3.0, pdown=0.0
        )
        self.assertEqual(vec.fconn, 0.0)
        self.assertEqual(vec.fdisc, 3.0)
        self.assertFalse(vec.is_healthy())


class TestContextMetadataParser(unittest.TestCase):
    """Kiểm thử trích xuất Context Metadata tầng Micro."""

    def test_context_parser_port_down(self):
        mock_prom = MagicMock()
        mock_prom.query_vector.side_effect = lambda q: (
            [{"labels": {"dp_name": "s1", "port": "2"}, "value": 0.0}]
            if "of_port_status" in q
            else []
        )
        parser = ContextMetadataParser(mock_prom)
        ctx = parser.parse()
        self.assertEqual(ctx.target_dpid, "s1")
    def test_context_parser_parse_from_text(self):
        """Test Case 11: Trích xuất Context Metadata từ text Gauge Exporter (:9303)"""
        sample_text = (
            "# HELP of_port_status\n"
            'of_port_status{dp_name="NT_ACC01",port="2"} 0\n'
            'of_port_status{dp_name="NT_ACC01",port="1"} 1\n'
            'faucet_dp_status{dp_name="HCM_ACC01"} 0\n'
            "of_errors_total 5\n"
        )
        parser = ContextMetadataParser()
        ctx = parser.parse_from_text(sample_text)
        self.assertEqual(ctx.target_dpid, "NT_ACC01")
        self.assertEqual(ctx.target_port, 2)
        self.assertIn("HCM_ACC01", ctx.disconnected_dpids)
        self.assertEqual(ctx.error_cookie, "ERR_COUNT_5")


class TestDirectExporterScraping(unittest.TestCase):
    """Kiểm thử cơ chế cào trực tiếp Exporter theo phương pháp của test_fault_scenarios.py."""

    @patch("urllib.request.urlopen")
    def test_direct_exporter_query(self, mock_urlopen):
        """Test Case 12: Đọc trực tiếp 8 chỉ số từ Exporter :9303 và :9302"""
        gauge_payload = (
            "of_datapath_connected 21.0\n"
            "port_status_down_total 2\n"
            "of_messages_sent_total 1500\n"
            "of_errors_total 3\n"
            "of_datapath_disconnections_total 1\n"
            'of_port_status{dp_name="NT_CORE",port="1"} 0\n'
        ).encode("utf-8")

        faucet_payload = (
            "faucet_cpu_seconds_total 12.34\n"
            'process_resident_memory_bytes{job="faucet"} 45000000\n'
            'process_virtual_memory_bytes{job="faucet"} 230000000\n'
        ).encode("utf-8")

        def mock_response(req, **kwargs):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            resp = MagicMock()
            if "9303" in url:
                resp.read.return_value = gauge_payload
            elif "9302" in url:
                resp.read.return_value = faucet_payload
            else:
                resp.read.return_value = b""
            resp.__enter__.return_value = resp
            return resp

        mock_urlopen.side_effect = mock_response

        collector = TelemetryCollector(
            config_path_or_dict={"scrape": {}, "prometheus": {}, "exporters": {"direct_mode": "direct"}},
            base_dir=current_dir,
        )

        success, data, ctx = collector.query_direct_exporters()
        self.assertTrue(success)
        self.assertEqual(data["fconn"], 21.0)
        self.assertEqual(data["pdown"], 2.0)
        self.assertEqual(data["fsent"], 1500.0)
        self.assertEqual(data["ferr"], 3.0)
        self.assertEqual(data["fdisc"], 1.0)
        self.assertEqual(data["ccpu"], 12.34)
        self.assertEqual(data["cres_mem"], 45000000.0)
        self.assertEqual(data["cvirt_mem"], 230000000.0)
        self.assertEqual(ctx.target_dpid, "NT_CORE")
        self.assertEqual(ctx.target_port, 1)

    @patch("urllib.request.urlopen")
    def test_collect_once_direct_mode(self, mock_urlopen):
        """Test Case 13: collect_once thu thập dữ liệu với data_quality='OK' bằng direct_mode"""
        gauge_payload = "of_datapath_connected 5.0\nport_status_down_total 0\n".encode("utf-8")
        faucet_payload = "faucet_cpu_seconds_total 1.0\n".encode("utf-8")

        def mock_response(req, **kwargs):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            resp = MagicMock()
            resp.read.return_value = gauge_payload if "9303" in url else faucet_payload
            resp.__enter__.return_value = resp
            return resp

        mock_urlopen.side_effect = mock_response

        collector = TelemetryCollector(
            config_path_or_dict={"scrape": {}, "prometheus": {}, "exporters": {"direct_mode": "direct"}},
            base_dir=current_dir,
        )

        row = collector.collect_once()
        self.assertEqual(row["fconn"], 5.0)
        self.assertEqual(row["data_quality"], "OK")


if __name__ == "__main__":
    unittest.main()

