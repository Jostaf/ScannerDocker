

def print_report(results):
    """Выводит отчёт о состоянии Docker-контейнеров."""

    print("\n" + "=" * 85)
    print("                         DOCKER MONITOR")
    print("=" * 85)

    print(f"Total containers: {len(results)}")
    print(f"Running:          {sum(1 for item in results if item['status'] == 'running')}")
    print(f"Stopped:          {sum(1 for item in results if item['status'] != 'running')}")
    print(f"Active:           {sum(1 for item in results if item['activity'] == 'ACTIVE')}")
    print(f"Inactive:         {sum(1 for item in results if item['activity'] == 'INACTIVE')}")

    print("\n" + "-" * 85)
    print(
        f"{'NAME':<20}"
        f"{'STATUS':<15}"
        f"{'ACTIVITY':<15}"
        f"{'CONNECTIONS':<15}"
        f"{'IDLE (SEC)':<15}"
    )
    print("-" * 85)

    for item in results:
        connections_count = item.get("connections_count")
        connections_display = (
            str(connections_count)
            if connections_count is not None
            else "-"
        )

        idle_seconds = item.get("idle_seconds")
        idle_display = (
            f"{idle_seconds:.1f}"
            if idle_seconds is not None
            else "-"
        )

        print(
            f"{item['name']:<20}"
            f"{item['status']:<15}"
            f"{item['activity']:<15}"
            f"{connections_display:<15}"
            f"{idle_display:<15}"
        )

    print("-" * 85)
