
import unittest
from unittest.mock import patch

from docker_net_profiler.analyzer import ActivityAnalyzer


class TestActivityAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = ActivityAnalyzer(idle_timeout=60)

    def make_container(self, rx=1000, tx=2000, status="running",
                       container_id="nginx"):
        return {
            "id": container_id,
            "name": container_id,
            "status": status,
            "rx_bytes": rx,
            "tx_bytes": tx
        }

    @patch("docker_net_profiler.analyzer.time.monotonic", return_value=100)
    def test_first_snapshot_is_observing(self, mock_time):
        result = self.analyzer.analyze([self.make_container()])

        self.assertEqual(result[0]["activity"], "OBSERVING")
        self.assertEqual(result[0]["idle_seconds"], 0)

    def test_increased_counters_mean_active(self):
        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=100):
            self.analyzer.analyze([self.make_container()])

        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=105):
            result = self.analyzer.analyze([
                self.make_container(rx=1500, tx=2500)
            ])

        self.assertEqual(result[0]["activity"], "ACTIVE")
        self.assertEqual(result[0]["idle_seconds"], 0)

    def test_unchanged_counters_become_inactive_after_timeout(self):
        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=100):
            self.analyzer.analyze([self.make_container()])

        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=160):
            result = self.analyzer.analyze([self.make_container()])

        self.assertEqual(result[0]["activity"], "INACTIVE")
        self.assertEqual(result[0]["idle_seconds"], 60)

    def test_counter_reset_starts_observation_again(self):
        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=100):
            self.analyzer.analyze([self.make_container()])

        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=110):
            result = self.analyzer.analyze([
                self.make_container(rx=100, tx=200)
            ])

        self.assertEqual(result[0]["activity"], "OBSERVING")
        self.assertEqual(result[0]["idle_seconds"], 0)

    def test_stopped_container_clears_saved_data(self):
        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=100):
            self.analyzer.analyze([self.make_container()])

        stopped = self.make_container(status="exited")

        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=110):
            result = self.analyzer.analyze([stopped])

        self.assertEqual(result[0]["activity"], "STOPPED")
        self.assertNotIn("nginx", self.analyzer.previous_io)
        self.assertNotIn("nginx", self.analyzer.last_activity)

    def test_missing_counters_return_unknown(self):
        container = self.make_container(rx=None, tx=None)

        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=100):
            result = self.analyzer.analyze([container])

        self.assertEqual(result[0]["activity"], "UNKNOWN")
        self.assertIsNone(result[0]["idle_seconds"])

    def test_removed_container_is_cleaned_up(self):
        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=100):
            self.analyzer.analyze([self.make_container()])

        with patch("docker_net_profiler.analyzer.time.monotonic", return_value=110):
            self.analyzer.analyze([])

        self.assertNotIn("nginx", self.analyzer.previous_io)
        self.assertNotIn("nginx", self.analyzer.last_activity)


if __name__ == "__main__":
    unittest.main()
