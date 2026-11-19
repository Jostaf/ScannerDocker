
import socket
import psutil


def filter_connections(connections, container_pids):

    filtered = []

    for connection in connections:

        if connection["pid"] not in container_pids:
            continue

        if connection["type"] == socket.SOCK_STREAM:
            if connection["status"] != psutil.CONN_ESTABLISHED:
                continue

        elif connection["type"] == socket.SOCK_DGRAM:
            if connection["remote_address"] is None:
                continue

        else:
            continue

        filtered.append(connection)

    return filtered


def _remote_host(remote_address):
    if not remote_address:
        return None

    if isinstance(remote_address, (tuple, list)):
        return str(remote_address[0])

    return str(remote_address).rsplit(":", 1)[0]


def drop_loopback(connections):
    """Remove noise: connections to loopback addresses.

    This also removes Docker's embedded DNS (127.0.0.11) and in-container
    chatter between processes, which says nothing about outside activity.
    """
    import ipaddress

    result = []

    for connection in connections:
        host = _remote_host(connection.get("remote_address"))

        try:
            address = ipaddress.ip_address(host)
            if address.is_loopback:
                continue
        except (ValueError, TypeError):
            pass

        result.append(connection)

    return result
