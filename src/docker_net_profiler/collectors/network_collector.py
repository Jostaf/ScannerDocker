
import psutil
import socket
import logging


def format_address(address):
    """Преобразует сетевой адрес в строку."""

    if not address:
        return None

    if hasattr(address, "ip"):
        return f"{address.ip}:{address.port}"

    return f"{address[0]}:{address[1]}"


def get_network_connections():
    """Получает сетевые соединения хоста."""

    try:
        connections = psutil.net_connections(kind="inet")

    except psutil.AccessDenied:
        logging.warning(
            "Access denied while collecting network connections"
        )
        return []

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
    """Получает PID основного и дочерних процессов."""

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
