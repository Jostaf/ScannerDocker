
import socket
import psutil


def filter_connections(connections, container_pids):
    """Фильтрует соединения по PID и типу подключения."""

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
