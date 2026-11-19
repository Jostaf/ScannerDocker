import ipaddress
import logging
import socket
import sys

import psutil


def format_address(address):
    if not address:
        return None

    if hasattr(address, "ip"):
        return f"{address.ip}:{address.port}"

    return f"{address[0]}:{address[1]}"


def supports_host_pid_matching(client):
    """Host PID matching works only with a native Linux Docker engine."""

    if sys.platform != "linux":
        return False

    try:
        docker_info = client.info()
    except Exception as error:
        logging.warning(
            "Cannot determine Docker environment: %s",
            error
        )
        return False

    operating_system = docker_info.get(
        "OperatingSystem", ""
    ).lower()

    if "docker desktop" in operating_system:
        return False

    return True


def get_network_connections():

    try:
        connections = psutil.net_connections(kind="inet")

    except psutil.AccessDenied:
        logging.warning(
            "Access denied while collecting network connections"
        )
        return None

    network_data = []

    for connection in connections:
        network_data.append({
            "pid": connection.pid,
            "type": connection.type,
            "status": connection.status,
            "local_address": format_address(connection.laddr),
            "remote_address": format_address(connection.raddr)
        })

    return network_data


def get_process_pids(root_pid):

    if not root_pid:
        return set()

    try:
        process = psutil.Process(root_pid)

        pids = {root_pid}

        for child in process.children(recursive=True):
            pids.add(child.pid)

        return pids

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return set()


# ---------------------------------------------------------------------------
# Cross-platform path: read /proc/net/* from inside the container.
# Works on Linux, macOS and Windows (Docker Desktop) alike, because it only
# uses the Docker API and needs no access to the host's process table.
# ---------------------------------------------------------------------------

_PROC_NET_SCRIPT = (
    "for f in tcp tcp6 udp udp6; do "
    "echo \"## $f\"; cat /proc/net/$f 2>/dev/null; "
    "done"
)

_TCP_ESTABLISHED = "01"


def _decode_proc_address(hex_address):
    """Decode 'IP:PORT' from /proc/net/* (little-endian hex words)."""
    ip_hex, port_hex = hex_address.split(":")
    raw = bytes.fromhex(ip_hex)

    if len(raw) == 4:
        ip = ipaddress.IPv4Address(raw[::-1])
    else:
        words = [raw[i:i + 4][::-1] for i in range(0, 16, 4)]
        ip = ipaddress.IPv6Address(b"".join(words))
        if ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped

    return str(ip), int(port_hex, 16)


def parse_proc_net(text):
    """Parse the output of _PROC_NET_SCRIPT into connection dicts.

    Dicts have the same shape as the ones from get_network_connections(),
    so the same filters can be applied. Only ESTABLISHED TCP sockets and
    connected UDP sockets are returned.
    """
    connections = []
    section = None

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("## "):
            section = line[3:]
            continue

        if not line or line.startswith("sl") or section is None:
            continue

        fields = line.split()
        if len(fields) < 4:
            continue

        try:
            local_ip, local_port = _decode_proc_address(fields[1])
            remote_ip, remote_port = _decode_proc_address(fields[2])
        except ValueError:
            continue

        state = fields[3]
        is_tcp = section.startswith("tcp")

        if is_tcp:
            if state != _TCP_ESTABLISHED:
                continue
            connection_type = socket.SOCK_STREAM
            status = psutil.CONN_ESTABLISHED
            remote = f"{remote_ip}:{remote_port}"
        else:
            if remote_port == 0 and ipaddress.ip_address(remote_ip).is_unspecified:
                continue
            connection_type = socket.SOCK_DGRAM
            status = "NONE"
            remote = f"{remote_ip}:{remote_port}"

        connections.append({
            "pid": None,
            "type": connection_type,
            "status": status,
            "local_address": f"{local_ip}:{local_port}",
            "remote_address": remote
        })

    return connections


def get_container_connections(client, container_id):
    """Return connections of a container, or None if they can't be read
    (container has no sh/cat, is stopped, exec denied, ...)."""
    try:
        container = client.containers.get(container_id)
        exit_code, output = container.exec_run(
            ["sh", "-c", _PROC_NET_SCRIPT]
        )
    except Exception as error:
        logging.debug(
            "exec failed for %s: %s", container_id[:12], error
        )
        return None

    if exit_code != 0 or not output:
        return None

    return parse_proc_net(output.decode("utf-8", errors="replace"))
