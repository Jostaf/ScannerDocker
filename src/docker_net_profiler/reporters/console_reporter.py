def _format_bytes(value):
    if value is None:
        return "-"
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024


def print_report(results):
    print("\n" + "=" * 115)
    print("                                      DOCKER MONITOR")
    print("=" * 115)

    print(f"Total containers: {len(results)}")
    print(f"Running:          {sum(1 for item in results if item['status'] == 'running')}")
    print(f"Stopped:          {sum(1 for item in results if item['status'] != 'running')}")
    print(f"Active:           {sum(1 for item in results if item['activity'] == 'ACTIVE')}")
    print(f"Connected:        {sum(1 for item in results if item['activity'] == 'CONNECTED')}")
    print(f"Idle (dead):      {sum(1 for item in results if item['activity'] == 'IDLE')}")

    print("\n" + "-" * 115)
    print(
        f"{'NAME':<18}{'STATUS':<12}{'ACTIVITY':<12}"
        f"{'CPU %':<10}{'MEMORY':<14}{'MEM %':<10}"
        f"{'CONNECTIONS':<14}{'IDLE (SEC)':<12}"
    )
    print("-" * 115)

    for item in results:
        connections = item.get("connections_count")
        idle = item.get("idle_seconds")
        cpu = item.get("cpu_percent")
        memory = item.get("memory_usage")
        memory_percent = item.get("memory_percent")

        print(
            f"{item['name']:<18.18}{item['status']:<12.12}{item['activity']:<12.12}"
            f"{(f'{cpu:.2f}' if cpu is not None else '-'):<10}"
            f"{_format_bytes(memory):<14}"
            f"{(f'{memory_percent:.2f}' if memory_percent is not None else '-'):<10}"
            f"{(str(connections) if connections is not None else '-'):<14}"
            f"{(str(idle) if idle is not None else '-'):<12}"
        )

    print("-" * 115)
