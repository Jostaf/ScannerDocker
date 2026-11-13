
def print_report(containers):
    """
    Формирует и выводит отчёт о Docker-контейнерах.
    """

    total = len(containers)

    running = sum(
        1 for container in containers
        if container.status == "running"
    )

    stopped = total - running

    print("\n" + "=" * 45)
    print("             DOCKER MONITOR")
    print("=" * 45)

    print(f"\nTotal containers: {total}")
    print(f"Running:          {running}")
    print(f"Stopped:          {stopped}")

    print("\n" + "-" * 45)
    print(f"{'NAME':<20} {'ID':<12} {'STATUS'}")
    print("-" * 45)

    for container in containers:
        print(
            f"{container.name:<20} "
            f"{container.short_id:<12} "
            f"{container.status}"
        )

    print("=" * 45)
