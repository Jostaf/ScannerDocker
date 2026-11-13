
import psutil
import socket
import logging
import sys


def format_address(address):
    """Преобразует сетевой адрес в строку."""
    if not address:
        return None

    if hasattr(address, "ip"):
        return f"{address.ip}:{address.port}"

    return f"{address[0]}:{address[1]}"


def supports_host_pid_matching(client):
    """
    Проверяет, можно ли сопоставлять PID контейнеров
    с процессами хостовой системы.
    """

    # На macOS и Windows Docker Desktop использует
    # отдельную Linux-среду для контейнеров.
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

    # Не используем PID-сопоставление для Docker Desktop.
    if "docker desktop" in operating_system:
        return False

    return True


def get_network_connections():
    """Получает сетевые соединения хостовой системы."""

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
