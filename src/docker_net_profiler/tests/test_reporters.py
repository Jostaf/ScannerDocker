import json
import tempfile
import unittest
from pathlib import Path

from docker_net_profiler.reporters.html_reporter import save_html_report
from docker_net_profiler.reporters.json_reporter import save_json_report
from docker_net_profiler.reporters.markdown_reporter import (
    save_markdown_report,
)

RESULTS = [
    {"name": "a", "status": "running", "activity": "ACTIVE",
     "cpu_percent": 1.5, "memory_usage": 10, "memory_percent": 1.0,
     "rx_bytes": 5, "tx_bytes": 6, "connections_count": 2,
     "idle_seconds": 0},
    {"name": "b|<x>", "status": "running", "activity": "CONNECTED",
     "cpu_percent": None, "memory_usage": None, "memory_percent": None,
     "rx_bytes": None, "tx_bytes": None, "connections_count": 1,
     "idle_seconds": 0},
    {"name": "c", "status": "exited", "activity": "STOPPED",
     "cpu_percent": None, "memory_usage": None, "memory_percent": None,
     "rx_bytes": None, "tx_bytes": None, "connections_count": 0,
     "idle_seconds": None},
]


class TestReporters(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_markdown_uses_real_newlines(self):
        path = self.dir / "r.md"
        save_markdown_report(RESULTS, str(path))
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("\\n", text)
        self.assertGreater(len(text.splitlines()), 10)
        self.assertIn("b\\|<x>", text)

    def test_json_summary_counts(self):
        path = self.dir / "r.json"
        save_json_report(RESULTS, str(path))
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["summary"]["connected"], 1)
        self.assertEqual(data["summary"]["stopped"], 1)

    def test_html_escapes_names(self):
        path = self.dir / "r.html"
        save_html_report(RESULTS, str(path))
        text = path.read_text(encoding="utf-8")
        self.assertIn("b|&lt;x&gt;", text)
        self.assertNotIn("<x>", text)


if __name__ == "__main__":
    unittest.main()
