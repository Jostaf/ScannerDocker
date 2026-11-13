
import docker


def create_docker_client():
    """Создаёт и проверяет подключение к Docker."""
    client = docker.from_env()
    client.ping()
    return client


def collect_containers(client):
    """Собирает информацию обо всех контейнерах."""
    containers = client.containers.list(all=True)
    result = []

    for container in containers:
        container.reload()

        state = container.attrs.get("State", {})
        status = state.get("Status", "unknown")
        pid = state.get("Pid", 0)

        rx_bytes = None
        tx_bytes = None

        if status == "running":
            try:
                stats = container.stats(stream=False)
                networks = stats.get("networks", {})

                if networks:
                    rx_bytes = sum(
                        interface.get("rx_bytes", 0)
                        for interface in networks.values()
                    )
                    tx_bytes = sum(
                        interface.get("tx_bytes", 0)
                        for interface in networks.values()
                    )

            except docker.errors.APIError:
                pass

        network_settings = container.attrs.get(
            "NetworkSettings", {}
        )

        ips = [
            network.get("IPAddress")
            for network in network_settings.get("Networks", {}).values()
            if network.get("IPAddress")
        ]

        result.append({
            "id": container.id,
            "name": container.name,
            "status": status,
            "pid": pid,
            "rx_bytes": rx_bytes,
            "tx_bytes": tx_bytes,
            "image": (
                container.image.tags[0]
                if container.image.tags
                else container.image.short_id
            ),
            "created": container.attrs.get("Created"),
            "ips": ips,
            "published_ports": network_settings.get("Ports") or {}
        })

    return result
