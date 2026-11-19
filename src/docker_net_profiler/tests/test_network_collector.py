import socket
import unittest

from docker_net_profiler.collectors.network_collector import (
    parse_proc_net,
)
from docker_net_profiler.filters import drop_loopback

SAMPLE = """\
## tcp
  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 00000000:0050 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 1 1
   1: 0200A8C0:D2A2 0100A8C0:18EB 01 00000000:00000000 00:00000000 00000000     0        0 2 1
   2: 0100007F:1F90 0100007F:D2A2 01 00000000:00000000 00:00000000 00000000     0        0 3 1
   3: 0200A8C0:D2A3 0100A8C0:18EB 06 00000000:00000000 00:00000000 00000000     0        0 4 1
## tcp6
  sl  local_address                         remote_address                        st
   0: 0000000000000000FFFF00000200A8C0:1F90 0000000000000000FFFF00000300A8C0:D2A2 01 0 0
## udp
  sl  local_address rem_address   st
   0: 0B00007F:A1B2 0000007F:0035 01 0
   1: 00000000:0044 00000000:0000 07 0
## udp6
"""


class TestParseProcNet(unittest.TestCase):

    def setUp(self):
        self.connections = parse_proc_net(SAMPLE)

    def test_only_established_tcp_and_connected_udp(self):
        # LISTEN, TIME_WAIT-like (06) and unconnected UDP are dropped
        self.assertEqual(len(self.connections), 4)

    def test_decodes_ipv4(self):
        first = self.connections[0]
        self.assertEqual(first["local_address"], "192.168.0.2:53922")
        self.assertEqual(first["remote_address"], "192.168.0.1:6379")
        self.assertEqual(first["type"], socket.SOCK_STREAM)

    def test_decodes_ipv4_mapped_ipv6(self):
        mapped = self.connections[2]
        self.assertEqual(mapped["local_address"], "192.168.0.2:8080")
        self.assertEqual(mapped["remote_address"], "192.168.0.3:53922")

    def test_udp_is_marked_as_datagram(self):
        self.assertEqual(self.connections[3]["type"], socket.SOCK_DGRAM)

    def test_drop_loopback_removes_docker_dns_and_local_chatter(self):
        remaining = drop_loopback(self.connections)
        remotes = {c["remote_address"] for c in remaining}
        self.assertEqual(
            remotes,
            {"192.168.0.1:6379", "192.168.0.3:53922"},
        )

    def test_garbage_input_is_ignored(self):
        self.assertEqual(parse_proc_net("## tcp\nnot a line\n"), [])
        self.assertEqual(parse_proc_net(""), [])


if __name__ == "__main__":
    unittest.main()
