
import unittest
import socket
import psutil

from docker_net_profiler.filters import filter_connections


class TestFilterConnections(unittest.TestCase):

    def setUp(self):
        self.container_pids = [100, 200]

    def make_connection(
        self,
        pid=100,
        connection_type=socket.SOCK_STREAM,
        status=psutil.CONN_ESTABLISHED,
        remote_address=("127.0.0.1", 8080)
    ):
        return {
            "pid": pid,
            "type": connection_type,
            "status": status,
            "remote_address": remote_address
        }

    def test_filters_connections_by_pid(self):
        connections = [
            self.make_connection(pid=100),
            self.make_connection(pid=300)
        ]

        result = filter_connections(
            connections, self.container_pids
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["pid"], 100)

    def test_accepts_established_tcp(self):
        connections = [
            self.make_connection(
                connection_type=socket.SOCK_STREAM,
                status=psutil.CONN_ESTABLISHED
            )
        ]

        result = filter_connections(
            connections, self.container_pids
        )

        self.assertEqual(len(result), 1)

    def test_rejects_non_established_tcp(self):
        connections = [
            self.make_connection(
                connection_type=socket.SOCK_STREAM,
                status=psutil.CONN_LISTEN
            )
        ]

        result = filter_connections(
            connections, self.container_pids
        )

        self.assertEqual(len(result), 0)

    def test_accepts_udp_with_remote_address(self):
        connections = [
            self.make_connection(
                connection_type=socket.SOCK_DGRAM,
                remote_address=("127.0.0.1", 53)
            )
        ]

        result = filter_connections(
            connections, self.container_pids
        )

        self.assertEqual(len(result), 1)

    def test_rejects_udp_without_remote_address(self):
        connections = [
            self.make_connection(
                connection_type=socket.SOCK_DGRAM,
                remote_address=None
            )
        ]

        result = filter_connections(
            connections, self.container_pids
        )

        self.assertEqual(len(result), 0)

    def test_rejects_unsupported_connection_type(self):
        connections = [
            self.make_connection(connection_type=999)
        ]

        result = filter_connections(
            connections, self.container_pids
        )

        self.assertEqual(len(result), 0)

    def test_empty_connections_list(self):
        result = filter_connections([], self.container_pids)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
