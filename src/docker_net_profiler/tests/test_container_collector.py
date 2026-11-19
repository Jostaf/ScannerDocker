import unittest
import sys
import types

# These helper tests do not need a live Docker SDK client.
if "docker" not in sys.modules:
    docker_stub = types.ModuleType("docker")
    docker_stub.errors = types.SimpleNamespace(APIError=Exception)
    docker_stub.from_env = lambda: None
    sys.modules["docker"] = docker_stub

from docker_net_profiler.collectors.container_collector import (
    calculate_cpu_percent,
    calculate_memory_usage,
)


class TestContainerStatsCalculations(unittest.TestCase):

    def test_calculates_cpu_percent(self):
        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 300},
                "system_cpu_usage": 2000,
                "online_cpus": 2,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 100},
                "system_cpu_usage": 1000,
            },
        }
        self.assertEqual(calculate_cpu_percent(stats), 40.0)

    def test_cpu_is_unknown_without_previous_snapshot(self):
        self.assertIsNone(calculate_cpu_percent({"cpu_stats": {}}))

    def test_calculates_memory_usage_using_inactive_file(self):
        stats = {
            "memory_stats": {
                "usage": 800,
                "limit": 1000,
                "stats": {"inactive_file": 200},
            }
        }
        self.assertEqual(calculate_memory_usage(stats), (600, 1000, 60.0))

    def test_calculates_memory_usage_using_cache_fallback(self):
        stats = {
            "memory_stats": {
                "usage": 800,
                "limit": 1000,
                "stats": {"cache": 100},
            }
        }
        self.assertEqual(calculate_memory_usage(stats), (700, 1000, 70.0))

    def test_memory_is_unknown_when_usage_or_limit_missing(self):
        self.assertEqual(calculate_memory_usage({}), (None, None, None))


if __name__ == "__main__":
    unittest.main()
