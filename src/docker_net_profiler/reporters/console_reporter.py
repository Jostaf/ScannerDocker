
def print_report(results):

    total = len(results)

    running = sum(
        1 for item in results
        if item["status"] == "running"
    )

    stopped = total - running

    active = sum(
        1 for item in results
        if item["activity"] == "ACTIVE"
    )

    inactive = sum(
        1 for item in results
        if item["activity"] == "INACTIVE"
    )

    print("\n" + "=" * 85)
    print("                         DOCKER MONITOR")
    print("=" * 85)

    print(f"Total containers: {total}")
    print(f"Running:          {running}")
    print(f"Stopped:          {stopped}")
    print(f"Active:           {active}")
    print(f"Inactive:         {inactive}")

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

        idle = item["idle_seconds"]

        idle_text = str(idle) if idle is not None else "-"

        print(
            f"{item['name']:<20}"
            f"{item['status']:<15}"
            f"{item['activity']:<15}"
            f"{item.get('connections_count', 0):<15}"
            f"{idle_text:<15}"
        )

    print("=" * 85)
