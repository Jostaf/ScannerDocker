from concurrent.futures import ThreadPoolExecutor

import docker


def calculate_cpu_percent(stats):
    """Calculate CPU usage from two consecutive Docker CPU snapshots."""
    cpu_stats = stats.get("cpu_stats", {})
    precpu_stats = stats.get("precpu_stats", {})

    cpu_usage = cpu_stats.get("cpu_usage", {}).get("total_usage")
    previous_cpu_usage = precpu_stats.get("cpu_usage", {}).get("total_usage")
    system_usage = cpu_stats.get("system_cpu_usage")
    previous_system_usage = precpu_stats.get("system_cpu_usage")

    if None in (cpu_usage, previous_cpu_usage, system_usage, previous_system_usage):
        return None

    cpu_delta = cpu_usage - previous_cpu_usage
    system_delta = system_usage - previous_system_usage

    if cpu_delta < 0 or system_delta <= 0:
        return None

    online_cpus = cpu_stats.get("online_cpus")
    if not online_cpus:
        online_cpus = len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", []))

    if not online_cpus:
        return None

    return round((cpu_delta / system_delta) * online_cpus * 100.0, 2)


def calculate_memory_usage(stats):
    """Return memory usage, limit and percentage, or None values if unavailable."""
    memory_stats = stats.get("memory_stats", {})
    usage = memory_stats.get("usage")
    limit = memory_stats.get("limit")

    if usage is None or limit is None or limit <= 0:
        return None, limit, None

    details = memory_stats.get("stats", {})
    # cgroup v2 reports inactive_file; cgroup v1 commonly reports cache.
    cache = details.get("inactive_file")
    if cache is None:
        cache = details.get("cache", 0)

    used = max(usage - (cache or 0), 0)
    percent = round((used / limit) * 100.0, 2)

    return used, limit, percent


def create_docker_client():
    client = docker.from_env()
    client.ping()
    return client


def _collect_one(container):
    """Collect data for a single container (runs in a worker thread)."""
    try:
        container.reload()
    except docker.errors.APIError:
        # Container was removed between list() and reload().
        return None

    state = container.attrs.get("State", {})
    status = state.get("Status", "unknown")
    pid = state.get("Pid", 0)

    rx_bytes = None
    tx_bytes = None
    cpu_percent = None
    memory_usage = None
    memory_limit = None
    memory_percent = None

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

            cpu_percent = calculate_cpu_percent(stats)
            memory_usage, memory_limit, memory_percent = (
                calculate_memory_usage(stats)
            )

        except docker.errors.APIError:
            pass

    network_settings = container.attrs.get("NetworkSettings", {})
    ips = [
        network.get("IPAddress")
        for network in network_settings.get("Networks", {}).values()
        if network.get("IPAddress")
    ]

    return {
        "id": container.id,
        "name": container.name,
        "status": status,
        "pid": pid,
        "rx_bytes": rx_bytes,
        "tx_bytes": tx_bytes,
        "cpu_percent": cpu_percent,
        "memory_usage": memory_usage,
        "memory_limit": memory_limit,
        "memory_percent": memory_percent,
        "image": (
            container.image.tags[0]
            if container.image.tags
            else container.image.short_id
        ),
        "created": container.attrs.get("Created"),
        "ips": ips,
        "published_ports": network_settings.get("Ports") or {}
    }


def collect_containers(client, max_workers=8):
    """Collect all containers. stats(stream=False) takes ~1 s per container,
    so containers are processed in parallel to keep the polling interval
    close to the requested one."""
    containers = client.containers.list(all=True)

    if not containers:
        return []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        collected = list(pool.map(_collect_one, containers))

    return [item for item in collected if item is not None]
